# doing-and-feeling

Work on intelligence and consciousness: a published podcast series, and a map and watch of the research field.
Direction in `VISION.md`, open work in `TODO.md`.

| Folder | What |
|---|---|
| [`podcast/`](podcast/) | *Doing and Feeling*: a [4-episode overview](https://www.youtube.com/playlist?list=PLRaFm7tzS9Ew) and the [14-episode series](https://www.youtube.com/playlist?list=PLcBsjViogzvI), written by Claude, voiced by TTS, rendered and published by the scripts here |
| [`field/`](field/) | The researchers behind the questions: who they are, their camps, who works with whom, and what they publish |
| `notes/` | Shared research inputs: how the series started, checked sources, the deduplicated reading list from the @willdepue thread, thread data |
| `scripts/` | Shared tools: X thread capture (`x-thread-export.js`) and enrichment (`thread-enrich.py`) |

Each sub-project has its own `README.md`, `VISION.md` and `TODO.md`. Run sub-project recipes from the root with
`just podcast <recipe>` or `just field <recipe>` (`just` lists them all).

## Thread capture

Paste `scripts/x-thread-export.js` into the DevTools console on a logged-in X thread (and any sub-thread pages),
copy `~/Downloads/x-thread-export.json` to `notes/thread/`, then run `scripts/thread-enrich.py` to fetch full posts
via the FxTwitter API and regenerate `notes/thread/replies.md`.

## Credentials

Nothing secret is stored in the repo. Tools read credentials from 1Password at runtime:
- `op://Pi/YT_DESKTOP_CLIENT_OAUTH`: YouTube OAuth desktop client (podcast uploads; refresh token cached in the macOS Keychain)
- `op://Pi/OPENALEX_API_KEY/credential`: OpenAlex API key (field)

## License

Code: MIT (`LICENSE`). Notes, data, map, digests and podcast text and media: CC BY 4.0, except third-party material
(`LICENSE-CONTENT.md`).
