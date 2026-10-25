#!/usr/bin/env python3
"""Render "Doing and Feeling: The Long Version" as chapter-card videos.

Reads source/long/kit/Doing-and-Feeling-Long-manifest.json and, per episode:
  out/long/cards/<episode>/NN.png   3840x2160 card per chapter: the episode cover on the left, the
                                    chapter list on the right with the current chapter highlighted
  out/long/videos/<episode>.mp4     cards switched at chapter starts + a progress bar, H.264 + AAC
  out/long/thumbnails/<episode>.png 1280x720 custom thumbnail: the cover centered on the background
Cards are HTML screenshotted by headless Chrome (set CHROME to override the binary path).

Usage: scripts/render-long.py [EPISODE_NUMBER ...] [--cards-only] [--seconds N]
       --seconds N renders only the first N seconds (preview).
"""

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "long"
OUT = ROOT / "out" / "long"
MANIFEST = SRC / "kit" / "Doing-and-Feeling-Long-manifest.json"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

WIDTH, HEIGHT = 3840, 2160
BG, TEXT, ORANGE = "#111319", "#f0eee8", "#e8b04b"
BAR_HEIGHT = 14

CARD_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {width}px; height: {height}px; background: {bg}; overflow: hidden; }}
body {{ display: flex; font-family: "SF Pro Display", "SF Pro", -apple-system, system-ui, sans-serif; color: {text}; }}
img {{ width: {height}px; height: {height}px; flex: none; }}
.panel {{ flex: 1; display: flex; flex-direction: column; justify-content: center; padding: 0 220px 0 40px; }}
.label {{ font-size: 46px; letter-spacing: 0.18em; text-transform: uppercase; color: #6f737d; margin-bottom: 56px; }}
ol {{ list-style: none; display: flex; flex-direction: column; gap: 0.62em; font-size: var(--size, 68px); line-height: 1.18; }}
li {{ display: flex; gap: 0.75em; color: #a3a7b0; }}
li .n {{ flex: none; width: 1.6em; font-variant-numeric: tabular-nums; color: #5b5f69; }}
li.past {{ color: #474b54; }}
li.past .n {{ color: #363940; }}
li.now {{ color: {text}; font-weight: 600; }}
li.now .n {{ color: {orange}; }}
.track {{ position: fixed; left: 0; right: 0; bottom: 0; height: {bar}px; background: #1d2029; }}
</style></head><body>
<img src="{cover}">
<div class="panel">
  <div class="label">{label}</div>
  <ol>{items}</ol>
</div>
<div class="track"></div>
<script>
  // Shrink the list until it fits vertically (long chapter lists, wrapped titles).
  const list = document.querySelector("ol");
  let size = 68;
  while (list.getBoundingClientRect().height > {height} - 520 && size > 34) {{
    size -= 2;
    list.style.setProperty("--size", size + "px");
  }}
</script>
</body></html>
"""


def episode_name(episode):
    return Path(episode["mp3"]).stem


def render_cards(episode, cards_dir):
    cards_dir.mkdir(parents=True, exist_ok=True)
    cover = (SRC / "covers" / episode["cover_4k"]).as_uri()
    part = episode.get("part", "").replace("I ", "I · ", 1) if episode.get("part") else ""
    label = html.escape(f"Chapters · Part {part}" if part else "Chapters")
    chapters = episode["chapters"]
    paths = []
    with tempfile.TemporaryDirectory() as tmp:
        for current in range(len(chapters)):
            items = "".join(
                f'<li class="{"past" if i < current else "now" if i == current else ""}">'
                f'<span class="n">{i + 1:02d}</span><span>{html.escape(ch["title"])}</span></li>'
                for i, ch in enumerate(chapters)
            )
            page = Path(tmp) / f"{current + 1:02d}.html"
            page.write_text(
                CARD_HTML.format(
                    width=WIDTH, height=HEIGHT, bg=BG, text=TEXT, orange=ORANGE, bar=BAR_HEIGHT,
                    cover=cover, label=label, items=items,
                )
            )
            png = cards_dir / f"{current + 1:02d}.png"
            subprocess.run(
                [
                    CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={WIDTH},{HEIGHT}", "--force-device-scale-factor=1",
                    "--virtual-time-budget=2000", f"--screenshot={png}", page.as_uri(),
                ],
                check=True,
                capture_output=True,
            )
            paths.append(png)
    return paths


def render_thumbnail(episode, thumbnail):
    thumbnail.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-i", str(SRC / "covers" / episode["cover_4k"]),
            "-vf", f"scale=720:720:flags=lanczos,pad=1280:720:(ow-iw)/2:0:color={BG.replace('#', '0x')}",
            str(thumbnail),
        ],
        check=True,
    )


def render_video(episode, cards, video, seconds=None):
    audio = SRC / "audio" / episode["mp3"]
    duration = float(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(audio)],
            check=True, capture_output=True, text=True,
        ).stdout
    )
    length = min(duration, seconds) if seconds else duration
    starts = [ch["start"] for ch in episode["chapters"]] + [duration]

    video.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ffconcat", delete=False) as listing:
        listing.write("ffconcat version 1.0\n")
        for card, start, end in zip(cards, starts, starts[1:]):
            listing.write(f"file '{card}'\nduration {end - start:.3f}\n")
        listing.write(f"file '{cards[-1]}'\n")  # concat demuxer needs the last file twice

    # Cards are decoded at 2 fps (chapter switches land within 0.5 s), the progress bar slides in
    # from the left over the full episode, and frames are duplicated to 24 fps after conversion.
    graph = (
        f"[0:v]fps=2[cards];"
        f"color=c={ORANGE.replace('#', '0x')}:s={WIDTH}x{BAR_HEIGHT}:r=2[bar];"
        f"[cards][bar]overlay=x='-w+w*t/{duration:.3f}':y=H-h:eval=frame:shortest=1,"
        f"format=yuv420p,fps=24[v]"
    )
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-stats", "-y",
            "-f", "concat", "-safe", "0", "-i", listing.name,
            "-i", str(audio),
            "-filter_complex", graph, "-map", "[v]", "-map", "1:a", "-t", f"{length:.3f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-crf", "16", "-g", "240",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-af", "pan=stereo|c0=c0|c1=c0", "-c:a", "aac", "-b:a", "192k",
            "-map_metadata", "1", "-movflags", "+faststart", str(video),
        ],
        check=True,
    )
    Path(listing.name).unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episodes", nargs="*", type=int)
    parser.add_argument("--cards-only", action="store_true")
    parser.add_argument("--seconds", type=float)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    for episode in manifest["episodes"]:
        if args.episodes and episode["episode"] not in args.episodes:
            continue
        name = episode_name(episode)
        print(f"==> {name}")
        cards = render_cards(episode, OUT / "cards" / name)
        render_thumbnail(episode, OUT / "thumbnails" / f"{name}.png")
        if not args.cards_only:
            suffix = f"-preview-{int(args.seconds)}s" if args.seconds else ""
            render_video(episode, cards, OUT / "videos" / f"{name}{suffix}.mp4", args.seconds)


if __name__ == "__main__":
    main()
