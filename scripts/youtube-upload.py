#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-api-python-client", "google-auth-oauthlib", "keyring"]
# ///
"""Upload the long version to YouTube with the Data API: videos, thumbnails, captions, playlist.

Per episode, in order (stops at the first failure so playlist order stays correct):
  1. videos.insert   long/out/videos/<ep>.mp4, Unlisted, title/description/tags from long/youtube/<ep>.md,
                     Education, not made for kids, AI disclosure (containsSyntheticMedia), English
  2. thumbnails.set  long/out/thumbnails/<ep>.png
  3. captions.insert long/captions/<ep>.srt (English)
  4. playlistItems   appended to "Doing and Feeling: The Long Version" (created Unlisted on first use)
Progress is recorded in long/youtube/uploads.json; reruns skip finished steps.

--publish switches every uploaded video and the playlist to Public.
--update-text pushes title, description and tags from long/youtube/*.md (and the playlist's title and
description from long/youtube/playlist.md) to the already uploaded videos and playlist.

Credentials: the OAuth desktop client is read from 1Password (op://Pi/YT_DESKTOP_CLIENT_OAUTH,
username = client ID, credential = client secret). The refresh token is cached in the macOS Keychain
(service "yt-desktop-client-oauth", reusable by other YouTube scripts); the browser consent only appears
when there is no cached token or it has expired (7 days while the Google project is in Testing mode).

Usage: scripts/youtube-upload.py [--only N ...] [--publish | --update-text] [--dry-run]
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LONG = ROOT / "long"
STATE = LONG / "youtube" / "uploads.json"
OP_ITEM = "op://Pi/YT_DESKTOP_CLIENT_OAUTH"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/youtube.upload"]
KEYCHAIN_SERVICE = "yt-desktop-client-oauth"
KEYCHAIN_ACCOUNT = "refresh-token"
TOKEN_URI = "https://oauth2.googleapis.com/token"
CATEGORY_EDUCATION = "27"


def code_blocks(path):
    return [block.strip() for block in re.findall(r"```\n(.*?)```", path.read_text(), re.S)]


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"playlist_id": None, "episodes": {}}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def youtube_client():
    import keyring
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    def op_read(field):
        return subprocess.run(["op", "read", f"{OP_ITEM}/{field}"], check=True, capture_output=True, text=True).stdout.strip()

    client_id, client_secret = op_read("username"), op_read("credential")
    refresh_token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
    if refresh_token:
        credentials = Credentials(
            None, refresh_token=refresh_token, token_uri=TOKEN_URI,
            client_id=client_id, client_secret=client_secret, scopes=SCOPES,
        )
        try:
            credentials.refresh(Request())
            return build("youtube", "v3", credentials=credentials)
        except RefreshError:
            print("Cached YouTube token expired or was revoked; asking for consent again.")

    config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(config, SCOPES)
    print("Opening the browser for YouTube consent (pick the channel to upload to)…")
    credentials = flow.run_local_server(port=0, open_browser=True, prompt="consent", access_type="offline")
    keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, credentials.refresh_token)
    return build("youtube", "v3", credentials=credentials)


def execute(request, what):
    """Run a non-upload request with retries on transient errors."""
    from googleapiclient.errors import HttpError

    for attempt in range(5):
        try:
            return request.execute()
        except HttpError as error:
            if error.resp.status in (500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt * 5)
                continue
            sys.exit(f"{what} failed: {error}")


def upload_video(youtube, path, title, description, tags):
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": CATEGORY_EDUCATION,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
            "embeddable": True,
            "license": "youtube",
        },
    }
    media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=32 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response, retries = None, 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"    uploading {status.progress():.0%}", end="\r", flush=True)
        except HttpError as error:
            if error.resp.status in (500, 502, 503, 504) and retries < 8:
                retries += 1
                time.sleep(min(2 ** retries, 60))
                continue
            sys.exit(f"upload of {path.name} failed: {error}")
    print("    uploading 100%")
    return response["id"]


def ensure_playlist(youtube, state):
    if state["playlist_id"]:
        return state["playlist_id"]
    title, description = code_blocks(LONG / "youtube" / "playlist.md")[:2]
    playlist = execute(
        youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description, "defaultLanguage": "en"},
                "status": {"privacyStatus": "unlisted"},
            },
        ),
        "playlist creation",
    )
    state["playlist_id"] = playlist["id"]
    save_state(state)
    print(f"  playlist created: https://www.youtube.com/playlist?list={playlist['id']}")
    return playlist["id"]


def upload(youtube, episodes, state, dry_run):
    for number, name in episodes:
        done = state["episodes"].setdefault(name, {})
        md = LONG / "youtube" / f"{name}.md"
        title, description, tags = code_blocks(md)[:3]
        video = LONG / "out" / "videos" / f"{name}.mp4"
        thumbnail = LONG / "out" / "thumbnails" / f"{name}.png"
        captions = LONG / "captions" / f"{name}.srt"
        for path in (video, thumbnail, captions):
            if not path.exists():
                sys.exit(f"missing {path.relative_to(ROOT)}")
        print(f"==> {number:02d} {title}")
        if dry_run:
            print(f"    would upload {video.name} ({video.stat().st_size / 1e6:.0f} MB), {len(tags.split(','))} tags; "
                  f"steps done: {sorted(k for k, v in done.items() if v) or 'none'}")
            continue

        if not done.get("video_id"):
            done["video_id"] = upload_video(youtube, video, title, description, [t.strip() for t in tags.split(",")])
            save_state(state)
            status = execute(youtube.videos().list(part="status", id=done["video_id"]), "status check")["items"][0]["status"]
            print(f"    https://youtu.be/{done['video_id']} — privacy: {status['privacyStatus']}, upload: {status['uploadStatus']}")
        if not done.get("thumbnail"):
            from googleapiclient.http import MediaFileUpload

            execute(youtube.thumbnails().set(videoId=done["video_id"], media_body=MediaFileUpload(str(thumbnail), mimetype="image/png")), "thumbnail")
            done["thumbnail"] = True
            save_state(state)
            print("    thumbnail set")
        if not done.get("captions"):
            from googleapiclient.http import MediaFileUpload

            execute(
                youtube.captions().insert(
                    part="snippet",
                    body={"snippet": {"videoId": done["video_id"], "language": "en", "name": "English", "isDraft": False}},
                    media_body=MediaFileUpload(str(captions), mimetype="application/octet-stream"),
                ),
                "captions",
            )
            done["captions"] = True
            save_state(state)
            print("    captions uploaded")
        if not done.get("in_playlist"):
            playlist_id = ensure_playlist(youtube, state)
            execute(
                youtube.playlistItems().insert(
                    part="snippet",
                    body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": done["video_id"]}}},
                ),
                "playlist item",
            )
            done["in_playlist"] = True
            save_state(state)
            print("    added to playlist")


def snippet(title, description, tags):
    return {
        "title": title,
        "description": description,
        "tags": [t.strip() for t in tags.split(",")],
        "categoryId": CATEGORY_EDUCATION,
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en",
    }


def update_text(youtube, episodes, state):
    # Updating the snippet part replaces every snippet field, so send all of them.
    for number, name in episodes:
        video_id = state["episodes"].get(name, {}).get("video_id")
        if not video_id:
            sys.exit(f"episode {number} is not uploaded yet")
        title, description, tags = code_blocks(LONG / "youtube" / f"{name}.md")[:3]
        execute(
            youtube.videos().update(part="snippet", body={"id": video_id, "snippet": snippet(title, description, tags)}),
            f"updating episode {number}",
        )
        print(f"  {number:02d} text updated: https://youtu.be/{video_id}")
    if state["playlist_id"]:
        title, description = code_blocks(LONG / "youtube" / "playlist.md")[:2]
        execute(
            youtube.playlists().update(
                part="snippet",
                body={"id": state["playlist_id"], "snippet": {"title": title, "description": description, "defaultLanguage": "en"}},
            ),
            "updating the playlist",
        )
        print(f"  playlist text updated: https://www.youtube.com/playlist?list={state['playlist_id']}")


def publish(youtube, episodes, state):
    for number, name in episodes:
        video_id = state["episodes"].get(name, {}).get("video_id")
        if not video_id:
            sys.exit(f"episode {number} is not uploaded yet")
        # Updating the status part resets omitted mutable fields, so send all of them.
        execute(
            youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                        "containsSyntheticMedia": True,
                        "embeddable": True,
                        "license": "youtube",
                        "publicStatsViewable": True,
                    },
                },
            ),
            f"publishing episode {number}",
        )
        print(f"  {number:02d} public: https://youtu.be/{video_id}")
    if state["playlist_id"]:
        title, description = code_blocks(LONG / "youtube" / "playlist.md")[:2]
        execute(
            youtube.playlists().update(
                part="snippet,status",
                body={
                    "id": state["playlist_id"],
                    "snippet": {"title": title, "description": description, "defaultLanguage": "en"},
                    "status": {"privacyStatus": "public"},
                },
            ),
            "publishing the playlist",
        )
        print(f"  playlist public: https://www.youtube.com/playlist?list={state['playlist_id']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", type=int, help="episode numbers")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--update-text", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = json.loads((LONG / "kit" / "Doing-and-Feeling-Long-manifest.json").read_text())
    episodes = [
        (e["episode"], Path(e["mp3"]).stem)
        for e in manifest["episodes"]
        if not args.only or e["episode"] in args.only
    ]
    state = load_state()
    if args.dry_run:
        upload(None, episodes, state, dry_run=True)
        return
    youtube = youtube_client()
    if args.publish:
        publish(youtube, episodes, state)
    elif args.update_text:
        update_text(youtube, episodes, state)
    else:
        upload(youtube, episodes, state, dry_run=False)


if __name__ == "__main__":
    main()
