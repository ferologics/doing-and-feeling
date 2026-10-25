# intelligence-pod

**Doing and Feeling**: a four-episode, ~62-minute podcast on intelligence and consciousness, written by Claude
and voiced with synthetic TTS. This repo turns the episodes into YouTube uploads and records how
they were made, so an expanded version can build on them.

## Layout

```
source/audio/                 Original episode MP3s (masters, from Claude)
source/covers/                3840×3840 cover art per episode
source/reference-screenshots/ Thread screenshots that were attached to the original prompt
transcripts/                  Whisper transcripts (txt, srt, word-level json) of the MP3s
notes/origin.md               The prompt, the Claude conversation, production details, screenshot index
notes/sources.md              Checked source list per episode + claims not yet checked
notes/claude-final-response.md, notes/grok-thread-summary.md, notes/claude-share.txt   Raw inputs
notes/reading-list.md         Final deduplicated list of every recommendation in the @willdepue thread
                              (handoff for the expanded version; includes corrections to Grok's summary)
notes/thread/                 Raw thread data: browser export, posts.json, replies.md (every post, threaded)
youtube/<episode>.md          Paste-ready title, description (with chapters) and tags
youtube/chapters/<episode>.txt  Chapter spec: `<phrase in transcript> | <chapter title>`
youtube/playlist.md           Playlist title and description
scripts/                      render-videos.sh, chapters.py, check.py, transcribe.sh,
                              x-thread-export.js (browser console), thread-enrich.py
out/                          Rendered videos, frames, thumbnails (gitignored)
work/                         Scratch space (gitignored)
```

## Commands

```bash
just render            # all episodes → out/videos/*.mp4 + out/thumbnails/*.png (~1–2 min each)
just render Feeling    # one episode (substring match)
just chapters 2-Feeling  # print YouTube chapters from the transcript
just check             # validate titles/descriptions/tags/chapters and video durations
just transcribe        # re-run Whisper on source/audio → transcripts/
```

Thread capture: paste `scripts/x-thread-export.js` into the DevTools console on the logged-in X thread
(and any sub-thread pages), copy `~/Downloads/x-thread-export.json` to `notes/thread/`, then run
`scripts/thread-enrich.py` to fetch full posts via the FxTwitter API and regenerate `notes/thread/replies.md`.

Requires `ffmpeg`/`ffprobe` and `python3`; `just transcribe` also needs `uv` and the cached
`mlx-community/whisper-large-v3-turbo` model (Apple Silicon).

## Video format

- 3840×2160, 24 fps, H.264 (`-tune stillimage`), yuv420p, BT.709. The square cover is scaled to
  2160×2160, centered, padded with the cover background colour `#111319`.
- AAC-LC 192 kbps, 44.1 kHz stereo: the mono MP3 copied to both channels at full level.
- Video length equals audio length (within one frame).
- Thumbnails: 1280×720 PNG of the same frame.

## Uploading

Per episode, in YouTube Studio:

1. Upload `out/videos/<episode>.mp4` as **Unlisted** first; 4K processing can take hours, so wait
   for the HD/4K versions before going public.
2. Paste the title, description and tags from `youtube/<episode>.md`. Chapters come from the
   timestamps in the description.
3. Custom thumbnail: `out/thumbnails/<episode>.png` (needs a phone-verified channel).
4. Category: Education. Audience: not made for kids. Language: English.
5. **AI use / altered or synthetic content: Yes** (recommended). YouTube requires disclosure for
   realistic AI-generated content; the voices are realistic synthetic speech, and the description
   says so anyway. Disclosure alone does not limit reach or monetization:
   https://support.google.com/youtube/answer/14328491
6. Add to the playlist from `youtube/playlist.md`, in episode order.
7. Captions: leave YouTube's auto-captions for now. `transcripts/*.srt` are raw Whisper output
   with mis-heard names and need proofreading before upload.

After all four are up, add the playlist link to each description's THE SERIES block.
