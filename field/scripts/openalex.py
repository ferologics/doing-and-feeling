"""Shared helpers for the field scripts: OpenAlex requests (with an on-disk cache) and the people list.

OpenAlex meters usage per API key ($1/day free). The key is read once per run from 1Password:
op://Pi/OPENALEX_API_KEY/credential.
"""

import functools
import hashlib
import subprocess
import json
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FIELD = Path(__file__).resolve().parent.parent
CACHE = FIELD / "cache"
API = "https://api.openalex.org"
OP_KEY = "op://Pi/OPENALEX_API_KEY/credential"
USER_AGENT = "doing-and-feeling-field/1.0"


def people():
    return tomllib.loads((FIELD / "people.toml").read_text())["person"]


def authors():
    """Resolved OpenAlex authors keyed by person name (written by resolve.py)."""
    return {a["name"]: a for a in json.loads((FIELD / "authors.json").read_text())}


@functools.cache
def api_key():
    result = subprocess.run(["op", "read", OP_KEY], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"OpenAlex API key not found at {OP_KEY} (free key: https://openalex.org/settings/api)")
    return result.stdout.strip()


def get(path, params=None, cache=True):
    """GET an OpenAlex endpoint and return the JSON, optionally cached on disk (the cache key excludes the API key)."""
    query = urllib.parse.urlencode(params or {})
    cached = CACHE / "api" / f"{hashlib.sha1(f'{path}?{query}'.encode()).hexdigest()}.json"
    if cache and cached.exists():
        return json.loads(cached.read_text())
    url = f"{API}/{path}?{query}&{urllib.parse.urlencode({'api_key': api_key()})}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read())
            break
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt * 2)
                continue
            raise
    if cache:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(data))
    return data


def works(author_id, since, cache=True, select=None):
    """All works by an OpenAlex author published on or after `since` (YYYY-MM-DD), following the cursor."""
    params = {
        "filter": f"author.id:{author_id},from_publication_date:{since}",
        "per-page": 200,
        "cursor": "*",
    }
    if select:
        params["select"] = select
    results = []
    while params["cursor"]:
        page = get("works", params, cache=cache)
        results += page["results"]
        params = dict(params, cursor=page["meta"].get("next_cursor"))
    return results


def short_id(openalex_url):
    return openalex_url.rsplit("/", 1)[-1]
