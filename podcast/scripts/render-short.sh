#!/usr/bin/env bash
# Render the short series (v1) as YouTube-ready videos (static cover + episode audio) and thumbnails.
#
# For each episode in short/audio/*.mp3 with a matching short/covers/<name>-cover-4K.png:
#   short/out/frames/<name>.png      3840x2160 frame: square cover scaled to 2160x2160, centered,
#                              padded with the cover background colour (#111319)
#   short/out/thumbnails/<name>.png  1280x720 custom thumbnail (same frame, downscaled)
#   short/out/videos/<name>.mp4      H.264 4K24 + AAC-LC 192k stereo, duration = audio duration.
#                              The mono MP3 is copied to both channels at full level (ffmpeg's
#                              default -ac 2 upmix would drop each channel by 3 dB).
#
# Usage: scripts/render-short.sh [episode-name-substring]
set -euo pipefail

cd "$(dirname "$0")/../short"

BG_COLOR="0x111319"
FILTER="${1:-}"

mkdir -p out/frames out/thumbnails out/videos

for audio in audio/*.mp3; do
    name="$(basename "$audio" .mp3)"
    if [[ -n "$FILTER" && "$name" != *"$FILTER"* ]]; then
        continue
    fi

    cover="covers/${name}-cover-4K.png"
    frame="out/frames/${name}.png"
    thumb="out/thumbnails/${name}.png"
    video="out/videos/${name}.mp4"

    if [[ ! -f "$cover" ]]; then
        echo "missing cover for $name: $cover" >&2
        exit 1
    fi

    echo "==> $name"

    ffmpeg -v error -y -i "$cover" \
        -vf "scale=2160:2160:flags=lanczos,pad=3840:2160:(ow-iw)/2:0:color=${BG_COLOR}" \
        "$frame"

    ffmpeg -v error -y -i "$frame" -vf "scale=1280:720:flags=lanczos" "$thumb"

    duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$audio")"

    # Input the still at 1 fps and duplicate to 24 fps after format conversion: the RGB->YUV
    # conversion runs once per second instead of per frame. -t pins the output to the audio
    # length; the in-graph fps filter keeps the video stream within one frame of it.
    ffmpeg -v error -stats -y \
        -loop 1 -framerate 1 -i "$frame" \
        -i "$audio" \
        -map 0:v -map 1:a -t "$duration" \
        -vf "format=yuv420p,fps=24" \
        -c:v libx264 -preset ultrafast -tune stillimage -crf 16 -g 240 \
        -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
        -af "pan=stereo|c0=c0|c1=c0" -c:a aac -b:a 192k \
        -map_metadata 1 \
        -movflags +faststart \
        "$video"
done

echo
echo "Rendered:"
for f in out/videos/*.mp4; do
    printf '%s  ' "$f"
    ffprobe -v error -show_entries format=duration,size -of compact=p=0:nk=1 "$f"
done
