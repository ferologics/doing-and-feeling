default:
    @just --list

# Print YouTube chapters for an episode, e.g. `just chapters 2-Feeling`
chapters episode:
    scripts/chapters.py Doing-and-Feeling-{{episode}}

# Validate the upload kit (titles, descriptions, tags, chapters, video durations)
check:
    scripts/check.py

# Render videos + thumbnails into out/ (optional episode substring filter)
render filter="":
    scripts/render-videos.sh {{filter}}

# Re-run Whisper on source/audio into transcripts/ (optional episode substring filter)
transcribe filter="":
    scripts/transcribe.sh {{filter}}
