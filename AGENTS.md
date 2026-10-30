# AGENTS.md

Context for AI assistants working in this repo. Human overview: `README.md`; direction: `VISION.md`.

## Layout

- Monorepo of sub-projects (`podcast/`, `field/`), each with `README.md`, `VISION.md`, `TODO.md` and a `justfile`
  loaded as a module by the root `justfile` (`just podcast check`, `just field map`).
- Sub-project scripts resolve paths relative to their own sub-project folder (`Path(__file__).parent.parent`), so
  they run from anywhere.
- Shared inputs live at the root: `notes/` (research notes, thread data) and `scripts/` (thread tools).
- Generated artefacts that are worth reading are committed (`field/map.md`, `field/digests/`, `podcast/*/youtube/`);
  caches, renders and large media are gitignored (`*/out/`, `field/cache/`, `podcast/long/audio/`, `work/`).

## Working rules

- **Check, don't trust.** Open every link and source before it goes into anything published. LLM summaries
  (Grok, Claude conversations) are leads; v1 of the podcast inherited a made-up claim from one.
- **Position tags need sources.** In `field/people.toml`, `crux` requires `crux_source`; camp tags are first-pass
  until reviewed.
- **Credentials** come from 1Password at runtime (`op read op://Pi/...`); never write keys or tokens to files.
  The YouTube refresh token lives in the macOS Keychain (`yt-desktop-client-oauth`).
- **YouTube quota:** 10,000 units/day (resets at midnight Pacific); uploads have their own 100/day bucket.
  Captions cost 400 units each. `podcast/scripts/youtube-upload.py` records progress in
  `podcast/long/youtube/uploads.json` and resumes after a quota stop.
- **OpenAlex** needs `OPENALEX_API_KEY` ($1/day budget); `field/scripts/openalex.py` caches responses in
  `field/cache/`. Agent bash has the key stripped (pi-env-guard); run field scripts with
  `OPENALEX_API_KEY="$(launchctl getenv OPENALEX_API_KEY)"` and never print it.
- Python scripts use the standard library where possible; scripts with dependencies declare them inline for
  `uv run --script`.
