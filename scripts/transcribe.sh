#!/usr/bin/env bash
# Transcribe source/audio/*.mp3 with MLX Whisper (large-v3-turbo, word timestamps)
# into transcripts/<episode>.{txt,srt,json}. Needs uv and the cached Hugging Face model.
#
# Usage: scripts/transcribe.sh [episode-name-substring]
set -euo pipefail

cd "$(dirname "$0")/.."

FILTER="${1:-}"
PROMPT="Doing and Feeling podcast on intelligence and consciousness. Blaise Agüera y Arcas, Anil Seth, Chalmers, Nagel, Dennett, Frankish, Tononi, Dehaene, Koch, Graziano, Friston, Cogitate, IIT, global workspace, panpsychism, illusionism, octopus, Godfrey-Smith, Chollet, ARC-AGI, Butlin, Shevlin, Schwitzgebel, Metzinger, Blindsight."

mkdir -p transcripts work/transcribe

for audio in source/audio/*.mp3; do
    name="$(basename "$audio" .mp3)"
    if [[ -n "$FILTER" && "$name" != *"$FILTER"* ]]; then
        continue
    fi
    echo "==> $name"
    uvx --from mlx-whisper mlx_whisper "$audio" \
        --model mlx-community/whisper-large-v3-turbo \
        --language en \
        --initial-prompt "$PROMPT" \
        --condition-on-previous-text False \
        --temperature 0 \
        --word-timestamps True \
        --hallucination-silence-threshold 2 \
        --output-format all \
        --output-dir work/transcribe \
        --output-name "$name" \
        --verbose False
    for ext in txt srt json; do
        cp "work/transcribe/$name.$ext" "transcripts/$name.$ext"
    done
done
