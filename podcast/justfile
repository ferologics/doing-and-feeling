default:
    @just --list

# Print short-series chapters computed from the transcript, e.g. `just chapters 2-Feeling`
chapters episode:
    scripts/chapters.py Doing-and-Feeling-{{episode}}

# Validate both upload kits (titles, descriptions, tags, chapters, video durations)
check:
    scripts/check.py

# Long series: verify chapter times against the transcripts and write long/youtube/*.md
long-youtube:
    scripts/long-youtube.py

# Long series: chapter-card videos + thumbnails into long/out/ (optional episode numbers)
render-long *episodes:
    scripts/render-long.py {{episodes}}

# Short series: static-cover videos + thumbnails into short/out/ (optional episode substring)
render-short filter="":
    scripts/render-short.sh {{filter}}

# Re-run Whisper on <series>/audio into <series>/whisper (series: short or long)
transcribe series filter="":
    scripts/transcribe.sh {{series}} {{filter}}
