#!/usr/bin/env bash
# Transcribe $AUDIO_DIR/*.mp3 (default source/audio) with MLX Whisper (large-v3-turbo, word
# timestamps) into $OUT_DIR/<episode>.{txt,srt,json} (default transcripts). Needs uv and the cached
# Hugging Face model.
#
# Usage: [AUDIO_DIR=source/long/audio OUT_DIR=transcripts/long] scripts/transcribe.sh [episode-name-substring]
set -euo pipefail

cd "$(dirname "$0")/.."

FILTER="${1:-}"
AUDIO_DIR="${AUDIO_DIR:-source/audio}"
OUT_DIR="${OUT_DIR:-transcripts}"
PROMPT="Doing and Feeling podcast on intelligence and consciousness. Blaise Agüera y Arcas, Anil Seth, Chalmers, Nagel, Dennett, Frankish, Tononi, Dehaene, Koch, Graziano, Friston, Cogitate, IIT, global workspace, panpsychism, illusionism, octopus, Godfrey-Smith, Chollet, ARC-AGI, Butlin, Shevlin, Schwitzgebel, Metzinger, Blindsight."

mkdir -p "$OUT_DIR" work/transcribe

for audio in "$AUDIO_DIR"/*.mp3; do
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
        cp "work/transcribe/$name.$ext" "$OUT_DIR/$name.$ext"
    done
done
