#!/usr/bin/env python3
"""Build timed English captions for the long version: Claude's exact script text, timed with our Whisper words.

Inputs:  long/kit/<episode>.txt       script text as spoken (correct names, no transcription errors)
         long/whisper/<episode>.json  Whisper word timestamps
Output:  long/captions/<episode>.srt

Script words are aligned to Whisper words with difflib; unmatched words (spelled-out numbers, misheard
names) get times interpolated between their matched neighbours. Cues hold at most two lines of
MAX_LINE characters and break at sentence ends where possible. Fails if fewer than MIN_MATCH of the
script words align.

Usage: scripts/long-captions.py [EPISODE_NUMBER ...]
"""

import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LONG = ROOT / "long"
MAX_LINE = 42
MAX_CUE_SECONDS = 6.5
MIN_MATCH = 0.85


def norm(word):
    return re.sub(r"[^a-z0-9]", "", word.lower())


def whisper_words(name):
    data = json.loads((LONG / "whisper" / f"{name}.json").read_text())
    return [w for segment in data["segments"] for w in segment.get("words", []) if norm(w["word"])]


def align(script_tokens, words):
    """Return (start, end) per script token and the matched fraction."""
    a = [norm(t) for t in script_tokens]
    b = [norm(w["word"]) for w in words]
    times = [None] * len(script_tokens)
    matched = 0
    for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(block.size):
            w = words[block.b + k]
            times[block.a + k] = (w["start"], w["end"])
            matched += 1
    # Interpolate runs of unmatched tokens between the surrounding matched times.
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        left = times[i - 1][1] if i > 0 else 0.0
        right = times[j][0] if j < len(times) else (words[-1]["end"] if words else left)
        step = max(right - left, 0.0) / (j - i)
        for k in range(i, j):
            times[k] = (left + step * (k - i), left + step * (k - i + 1))
        i = j
    return times, matched / max(len(script_tokens), 1)


def wrap(words):
    """Split cue words into at most two balanced lines."""
    text = " ".join(words)
    if len(text) <= MAX_LINE:
        return text
    best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def cues(script_text, times):
    tokens = script_text.split()
    result, current = [], []
    for index, token in enumerate(tokens):
        current.append(index)
        text = " ".join(tokens[i] for i in current)
        duration = times[current[-1]][1] - times[current[0]][0]
        sentence_end = token.endswith((".", "?", "!", ":", ";")) or token.endswith(('."', '?"', '!"', ".’", "?’"))
        next_len = len(text) + 1 + len(tokens[index + 1]) if index + 1 < len(tokens) else 0
        if (
            index + 1 == len(tokens)
            or next_len > 2 * MAX_LINE
            or duration > MAX_CUE_SECONDS
            or (sentence_end and len(text) > MAX_LINE * 0.6)
        ):
            result.append(current)
            current = []
    return [(times[c[0]][0], times[c[-1]][1], wrap([tokens[i] for i in c])) for c in result]


def stamp(seconds):
    ms = int(round(seconds * 1000))
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    manifest = json.loads((LONG / "kit" / "Doing-and-Feeling-Long-manifest.json").read_text())
    wanted = {int(a) for a in sys.argv[1:]}
    out_dir = LONG / "captions"
    out_dir.mkdir(exist_ok=True)
    failures = []
    for episode in manifest["episodes"]:
        if wanted and episode["episode"] not in wanted:
            continue
        name = Path(episode["mp3"]).stem
        script = (LONG / "kit" / f"{name}.txt").read_text()
        times, ratio = align(script.split(), whisper_words(name))
        entries = cues(script, times)
        lines = []
        for n, (start, end, text) in enumerate(entries, 1):
            next_start = entries[n][0] if n < len(entries) else end + 2
            end = min(max(end, start + 1.0), next_start - 0.05)  # at least 1 s, never overlapping the next cue
            lines += [str(n), f"{stamp(start)} --> {stamp(end)}", text, ""]
        (out_dir / f"{name}.srt").write_text("\n".join(lines))
        print(f"{name}: {len(entries)} cues, {ratio:.1%} of script words aligned")
        if ratio < MIN_MATCH:
            failures.append(name)
    if failures:
        sys.exit(f"alignment below {MIN_MATCH:.0%}: {', '.join(failures)}")


if __name__ == "__main__":
    main()
