# intelligence-pod

**Doing and Feeling**: a podcast on intelligence and consciousness, written by Claude and voiced with
synthetic TTS, turned into YouTube uploads. It exists in two versions, each in its own folder:

| | Episodes | Length | Video style | Status |
|---|---|---|---|---|
| `short/` | 4 | 62 min | static cover | [uploaded](https://www.youtube.com/playlist?list=PLRaFm7tzS9Ew) |
| `long/` | 14 | 5h23m | chapter cards + progress bar | [uploaded, unlisted](https://www.youtube.com/playlist?list=PLcBsjViogzvI) |

Both started from one X thread (@willdepue asking for consciousness reading); `notes/` records how.

## Layout

Both series folders share one layout:

```
<series>/
  audio/       episode MP3s from Claude (masters)
  covers/      3840×3840 cover per episode
  whisper/     our Whisper transcripts (txt, srt, word-level json)
  youtube/     paste-ready title, description (with chapters) and tags per episode
  out/         rendered videos, thumbnails, frames/cards (gitignored)
```

Series-specific extras:

```
short/youtube/chapters/       chapter specs: `<phrase in transcript> | <chapter title>` (timestamps come from whisper/)
short/youtube/playlist.md     playlist title and description
long/captions/                English captions: Claude's script text timed with whisper/ (scripts/long-captions.py)
long/youtube/uploads.json     YouTube upload state: playlist ID, video IDs, finished steps
long/youtube/playlist.md      playlist title and description
long/kit/                     Claude's delivery: manifest (chapters, durations), script transcripts for
                              captions, YouTube text (source of long/youtube/*.md)
long/companion.md             Claude's companion doc (sources and further reading)
long/companion-public.md      the published copy: https://gist.github.com/ferologics/f23bb5a1b636be8b1ae10362df402790
                              (update with `gh gist edit f23bb5a1b636be8b1ae10362df402790 long/companion-public.md`)
```

Project-wide:

```
notes/origin.md               the original prompt, the Claude conversation, production details, screenshot index
notes/sources.md              checked sources for the short series + claims that were not checked
notes/reading-list.md         deduplicated list of every recommendation in the thread (the long version's input)
notes/thread/                 thread data: browser export, posts.json, replies.md (every post, threaded)
notes/reference-screenshots/  thread screenshots attached to the original prompt
notes/claude-final-response.md, notes/grok-thread-summary.md, notes/claude-share.txt   raw inputs
scripts/                      see Commands
work/                         scratch space (gitignored)
```

`long/audio/` (200 MB) is gitignored; remove it from `.gitignore` to track it.

## Commands

```bash
just check                    # validate both upload kits: limits, chapter rules, video lengths
just render-short [filter]    # short/out/videos/*.mp4 + thumbnails (~1 min per episode)
just chapters 2-Feeling       # short: print chapters computed from the transcript
just render-long [N ...]      # long/out/videos/*.mp4 + thumbnails + cards (~2 min per episode)
just long-youtube             # long: verify Claude's chapter times against whisper/, write long/youtube/*.md
just transcribe short|long    # re-run Whisper into <series>/whisper/
scripts/long-captions.py      # long: build long/captions/*.srt
scripts/youtube-upload.py     # long: upload videos, thumbnails, captions, playlist (resumable; --publish, --dry-run)
```

`scripts/render-long.py 9 --seconds 130` renders a 130-second preview of one episode.

Thread capture: paste `scripts/x-thread-export.js` into the DevTools console on the logged-in X thread
(and any sub-thread pages), copy `~/Downloads/x-thread-export.json` to `notes/thread/`, then run
`scripts/thread-enrich.py` to fetch full posts via the FxTwitter API and regenerate `notes/thread/replies.md`.

Requires `ffmpeg`/`ffprobe`, `python3` and Google Chrome (long-version cards are HTML screenshotted by
headless Chrome). `just transcribe` also needs `uv` and the cached `mlx-community/whisper-large-v3-turbo`
model (Apple Silicon).

## Video format

Both series:
- 3840×2160, 24 fps, H.264 (`-tune stillimage`), yuv420p, BT.709.
- AAC-LC 192 kbps, 44.1 kHz stereo: the mono MP3 copied to both channels at full level.
- Video length equals audio length (within one frame).
- Thumbnails: 1280×720 PNG, the cover centered on the background colour `#111319`.

Short: the square cover scaled to 2160×2160 and centered. Long: the cover on the left, the chapter list on
the right with the current chapter highlighted, and an orange progress bar along the bottom; cards switch
at each chapter start.

## Uploading

The long version is uploaded with `scripts/youtube-upload.py` (YouTube Data API v3). It reads the OAuth desktop
client from 1Password (`op://Pi/YT_DESKTOP_CLIENT_OAUTH`: username = client ID, credential = client secret) and
caches the refresh token in the macOS Keychain (service `yt-desktop-client-oauth`), so the browser consent only
appears when the token is missing or expired (7 days while the Google project is in Testing mode). Each episode
is uploaded Unlisted with its text, Education category, not made for kids, the AI disclosure, thumbnail and
captions, then appended to the playlist; `--publish` makes the videos and the playlist public.

The short version was uploaded by hand. Per episode, in YouTube Studio:

1. Upload `<series>/out/videos/<episode>.mp4` as **Unlisted** first; 4K processing can take hours, so
   wait for the HD/4K versions before going public.
2. Paste the title, description and tags from `<series>/youtube/<episode>.md`. Chapters come from the
   timestamps in the description.
3. Custom thumbnail: `<series>/out/thumbnails/<episode>.png` (needs a phone-verified channel).
4. Category: Education. Audience: not made for kids. Language: English.
5. **AI use / altered or synthetic content: Yes** (recommended). YouTube requires disclosure for
   realistic AI-generated content; the voices are realistic synthetic speech, and the description
   says so anyway. Disclosure alone does not limit reach or monetization:
   https://support.google.com/youtube/answer/14328491
6. Captions:
   - long: Subtitles → Add → Upload file → "Without timing", using `long/kit/<episode>.txt`
     (Claude's script text); YouTube aligns it to the audio.
   - short: auto-captions; `short/whisper/*.srt` are raw Whisper output with mis-heard names.
7. Add to the series playlist in episode order (short: `short/youtube/playlist.md`; long: "Doing and
   Feeling: The Long Version").
