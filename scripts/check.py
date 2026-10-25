#!/usr/bin/env python3
"""Validate the YouTube upload kit.

For every youtube/<episode>.md:
- title <= 100 chars, description <= 5000 chars, tags <= 500 chars, no < or > (YouTube rejects them)
- the CHAPTERS block in the description matches scripts/chapters.py output
- if out/videos/<episode>.mp4 exists, its duration matches the source MP3 within 0.1 s
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def main():
    errors = []
    for md in sorted((ROOT / "youtube").glob("Doing-and-Feeling-*.md")):
        episode = md.stem
        blocks = re.findall(r"```\n(.*?)```", md.read_text(), re.S)
        title, description, tags = (block.strip() for block in blocks[:3])

        if len(title) > 100:
            errors.append(f"{episode}: title is {len(title)} chars (max 100)")
        if len(description) > 5000:
            errors.append(f"{episode}: description is {len(description)} chars (max 5000)")
        if len(tags) > 500:
            errors.append(f"{episode}: tags are {len(tags)} chars (max 500)")
        if re.search(r"[<>]", title + description):
            errors.append(f"{episode}: title/description contains < or >")

        chapters = re.search(r"CHAPTERS\n(.*?)\n\n", description, re.S).group(1).strip()
        expected = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "chapters.py"), episode],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if chapters != expected:
            errors.append(f"{episode}: description chapters differ from scripts/chapters.py output")

        video = ROOT / "out" / "videos" / f"{episode}.mp4"
        if video.exists():
            audio = ROOT / "source" / "audio" / f"{episode}.mp3"
            delta = abs(probe_duration(video) - probe_duration(audio))
            if delta > 0.1:
                errors.append(f"{episode}: video duration differs from audio by {delta:.2f}s")

        print(f"{episode}: title {len(title)}, description {len(description)}, tags {len(tags)}")

    if errors:
        print("\n".join(["", "FAILED:"] + errors))
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
