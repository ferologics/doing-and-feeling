#!/usr/bin/env python3
"""Print YouTube chapter lines for an episode.

For the short series (v1). Each line of short/youtube/chapters/<episode>.txt is `<phrase> | <chapter title>`. The phrase is
located in the word-level Whisper transcript (short/whisper/<episode>.json) and the chapter
starts just before its first word. A first line with an empty phrase is pinned to 00:00.

Usage: scripts/chapters.py Doing-and-Feeling-1-Doing
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEAD_SECONDS = 0.3
MIN_CHAPTER_SECONDS = 10  # YouTube rejects chapter lists with shorter chapters


def norm(word):
    return re.sub(r"[^a-z0-9]", "", word.lower())


def load_words(episode):
    data = json.loads((ROOT / "short" / "whisper" / f"{episode}.json").read_text())
    words = []
    for segment in data["segments"]:
        for word in segment.get("words", []):
            # Whisper sometimes emits "split -brain" as two tokens; split on hyphens too.
            for part in re.split(r"[-\s]+", word["word"]):
                if norm(part):
                    words.append((norm(part), word["start"]))
    return words


def find(words, phrase):
    target = [norm(p) for p in re.split(r"[-\s]+", phrase) if norm(p)]
    for i in range(len(words) - len(target) + 1):
        if all(words[i + j][0] == target[j] for j in range(len(target))):
            return words[i][1]
    raise SystemExit(f"phrase not found in transcript: {phrase!r}")


def stamp(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    episode = sys.argv[1]
    words = load_words(episode)
    spec = (ROOT / "short" / "youtube" / "chapters" / f"{episode}.txt").read_text().splitlines()

    starts = []
    for line in spec:
        if not line.strip():
            continue
        phrase, title = (part.strip() for part in line.split("|", 1))
        start = 0.0 if not phrase else max(0.0, find(words, phrase) - LEAD_SECONDS)
        starts.append((start, title))

    for (start, title), (next_start, _) in zip(starts, starts[1:]):
        if next_start - start < MIN_CHAPTER_SECONDS:
            raise SystemExit(f"chapter shorter than {MIN_CHAPTER_SECONDS}s: {title!r}")
        if next_start <= start:
            raise SystemExit(f"chapters out of order at: {title!r}")

    for start, title in starts:
        print(f"{stamp(start)} {title}")


if __name__ == "__main__":
    main()
