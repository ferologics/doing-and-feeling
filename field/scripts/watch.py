#!/usr/bin/env python3
"""Digest of new work by the researchers on the map.

Fetches works published since the last run (field/watch-state.json; first run: the last DEFAULT_DAYS days) for every
resolved author, merges works co-authored by several people on the map, checks each link, and writes
field/digests/<today>.md.

Link check: ✓ opens; ⛔ the publisher blocks scripted requests (401/403/406/429, usually fine in a browser);
✗ broken (404/410/5xx or no response).

Usage: field/scripts/watch.py [--since YYYY-MM-DD] [--dry-run]   (--dry-run leaves watch-state.json untouched)
"""

import argparse
import collections
import concurrent.futures
import datetime
import json
import urllib.error
import urllib.request

from openalex import FIELD, authors, people, short_id, works

DEFAULT_DAYS = 30
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
STATE = FIELD / "watch-state.json"
SELECT = "id,doi,title,publication_date,type,primary_location,authorships"


def check(url):
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    try:
        with urllib.request.urlopen(request, timeout=25):
            return "✓"
    except urllib.error.HTTPError as error:
        return "⛔" if error.code in (401, 403, 406, 429) else "✗"
    except Exception:
        return "✗"


def link(work):
    location = work.get("primary_location") or {}
    return work.get("doi") or location.get("landing_page_url") or work["id"]


def venue(work):
    source = (work.get("primary_location") or {}).get("source") or {}
    return source.get("display_name") or ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = datetime.date.today()
    if args.since:
        since = args.since
    elif STATE.exists():
        since = json.loads(STATE.read_text())["last_run"]
    else:
        since = (today - datetime.timedelta(days=DEFAULT_DAYS)).isoformat()

    camps = {p["name"]: (p.get("camps") or ["–"])[0] for p in people()}
    resolved = {name: a for name, a in authors().items() if a.get("openalex")}
    id_to_name = {a["openalex"]: name for name, a in resolved.items()}

    found = {}
    on_map = collections.defaultdict(set)
    for name, author in resolved.items():
        for work in works(author["openalex"], since, cache=False, select=SELECT):
            if (work.get("publication_date") or "") > today.isoformat():
                continue  # OpenAlex sometimes carries future-dated records; they show up once they are due
            found[work["id"]] = work
            for authorship in work["authorships"]:
                author_id = authorship["author"].get("id")
                if author_id and short_id(author_id) in id_to_name:
                    on_map[work["id"]].add(id_to_name[short_id(author_id)])

    ordered = sorted(found.values(), key=lambda w: (w.get("publication_date") or "", w.get("title") or ""), reverse=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        status = dict(zip((w["id"] for w in ordered), pool.map(lambda w: check(link(w)), ordered)))

    per_person = collections.Counter(n for names in on_map.values() for n in names)
    lines = [
        f"# Watch: {since} to {today.isoformat()}",
        "",
        f"{len(ordered)} new works by {len(per_person)} people on the map (OpenAlex, by publication date). "
        "Links: ✓ opens, ⛔ publisher blocks scripts (usually fine in a browser), ✗ broken.",
        "",
        "Most active: " + ", ".join(f"{n} ({c})" for n, c in per_person.most_common(12)),
        "",
    ]
    for work in ordered:
        names = sorted(on_map[work["id"]])
        others = len(work["authorships"]) - len(names)
        people_line = ", ".join(f"{n} ({camps.get(n, '–')})" for n in names) + (f" + {others} more" if others > 0 else "")
        meta = " · ".join(x for x in (work.get("publication_date"), work.get("type"), venue(work)) if x)
        lines += [f"## {work.get('title') or '(untitled)'}", "", f"- {people_line}", f"- {meta}",
                  f"- {status[work['id']]} {link(work)}", ""]

    out = FIELD / "digests" / f"{today.isoformat()}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    if not args.dry_run:
        STATE.write_text(json.dumps({"last_run": today.isoformat()}) + "\n")
    broken = sum(1 for s in status.values() if s == "✗")
    print(f"{len(ordered)} works → {out.relative_to(FIELD.parent)} ({broken} broken links)")


if __name__ == "__main__":
    main()
