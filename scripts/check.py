#!/usr/bin/env python3
"""Validate the YouTube upload kits in short/youtube/ and long/youtube/.

For every episode .md:
- title <= 100 chars, description <= 5000 chars, tags <= 500 chars, no < or > (YouTube rejects them)
- CHAPTERS block follows YouTube's rules: starts at 0:00, at least 3 chapters, ascending, each >= 10 s
- short only: the CHAPTERS block matches scripts/chapters.py output (computed from the transcript)
- if the rendered video exists, its duration matches the source MP3 within 0.1 s
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES = [
    # (markdown glob, audio dir, video dir, compare chapters with scripts/chapters.py)
    (ROOT / "short" / "youtube", "Doing-and-Feeling-*.md", ROOT / "short" / "audio", ROOT / "short" / "out" / "videos", True),
    (ROOT / "long" / "youtube", "*.md", ROOT / "long" / "audio", ROOT / "long" / "out" / "videos", False),
]


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def seconds(stamp):
    total = 0
    for part in stamp.split(":"):
        total = total * 60 + int(part)
    return total


def chapter_errors(chapters, duration):
    starts = []
    for line in chapters.splitlines():
        match = re.match(r"^(\d+(?::\d\d){1,2}) \S", line)
        if not match:
            return [f"bad chapter line: {line!r}"]
        starts.append(seconds(match.group(1)))
    errors = []
    if starts[0] != 0:
        errors.append("first chapter does not start at 0:00")
    if len(starts) < 3:
        errors.append("fewer than 3 chapters")
    ends = starts[1:] + ([duration] if duration else [])
    if any(end - start < 10 for start, end in zip(starts, ends)):
        errors.append("a chapter is shorter than 10 s or out of order")
    return errors


def main():
    errors = []
    for directory, pattern, audio_dir, video_dir, compare_with_transcript in SERIES:
        for md in sorted(directory.glob(pattern)):
            episode = md.stem
            blocks = re.findall(r"```\n(.*?)```", md.read_text(), re.S)
            title, description, tags = (block.strip() for block in blocks[:3])
            audio = audio_dir / f"{episode}.mp3"
            duration = probe_duration(audio) if audio.exists() else None

            problems = []
            if len(title) > 100:
                problems.append(f"title is {len(title)} chars (max 100)")
            if len(description) > 5000:
                problems.append(f"description is {len(description)} chars (max 5000)")
            if len(tags) > 500:
                problems.append(f"tags are {len(tags)} chars (max 500)")
            if re.search(r"[<>]", title + description):
                problems.append("title/description contains < or >")

            chapters = re.search(r"CHAPTERS\n(.*?)(?:\n\n|$)", description, re.S).group(1).strip()
            problems += chapter_errors(chapters, duration)
            if compare_with_transcript:
                expected = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "chapters.py"), episode],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                if chapters != expected:
                    problems.append("description chapters differ from scripts/chapters.py output")

            video = video_dir / f"{episode}.mp4"
            if video.exists() and duration:
                delta = abs(probe_duration(video) - duration)
                if delta > 0.1:
                    problems.append(f"video duration differs from audio by {delta:.2f}s")

            errors += [f"{episode}: {p}" for p in problems]
            print(f"{episode}: title {len(title)}, description {len(description)}, tags {len(tags)}"
                  + ("" if problems else " ✓"))

    if errors:
        print("\n".join(["", "FAILED:"] + errors))
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
