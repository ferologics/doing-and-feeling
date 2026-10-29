#!/usr/bin/env python3
"""Digest of new work by the researchers on the map.

Fetches works published since the last run (field/watch-state.json; first run: the last DEFAULT_DAYS days) for every
resolved author and keeps the on-topic ones: title or OpenAlex topics must match TOPIC_KEYWORDS, or the narrower
CORE_KEYWORDS for people marked `watch = "core"` in people.toml (this also drops papers by namesakes that OpenAlex
merged into a profile). Datasets, peer reviews and corrections are skipped;
preprint and published versions of the same title are merged. Each link is checked, and the digest goes to
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
SELECT = "id,doi,title,publication_date,type,primary_location,authorships,topics"
SKIP_TYPES = {"dataset", "peer-review", "erratum", "paratext"}
SKIP_TITLES = ("data and results for", "data for:", "code for", "accompanying data", "supplementary")
CORE_KEYWORDS = (
    "conscious", "aware", "sentien", "qualia", "phenomenal", "phenomenolog", "subjective", "introspect", "experience", "mind",
    "moral status", "welfare", "feeling", "self-model",
)
TOPIC_KEYWORDS = (
    "conscious", "aware", "sentien", "qualia", "phenomenal", "phenomenolog", "subjective", "experience", "introspect", "metacognit",
    "attention", "percept", "self-model", "selfhood", "mind", "psychedel", "anesthe", "anaesthe", "sleep", "dream",
    "meditat", "welfare", "moral status", "agency", "free will", "emotion", "intelligen", "cognit", "theory of mind",
    "language model", "artificial intelligence", "agi", "turing", "global workspace", "integrated information",
    "predictive processing", "predictive coding", "active inference", "free energy", "illusion", "pain", "brain",
    "neural", "philosoph",
)


def check(url):
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    try:
        with urllib.request.urlopen(request, timeout=25):
            return "✓"
    except urllib.error.HTTPError as error:
        return "⛔" if error.code in (401, 403, 406, 429) else "✗"
    except Exception:
        return "✗"


def on_topic(work, core_only):
    text = " ".join([work.get("title") or ""] + [t["display_name"] for t in work.get("topics") or []]).lower()
    return any(keyword in text for keyword in (CORE_KEYWORDS if core_only else TOPIC_KEYWORDS))


def title_key(work):
    return "".join(ch for ch in (work.get("title") or "").lower() if ch.isalnum())[:120]


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
    core_only = {p["name"] for p in people() if p.get("watch") == "core"}
    resolved = {name: a for name, a in authors().items() if a.get("openalex")}
    id_to_name = {a["openalex"]: name for name, a in resolved.items()}

    found, off_topic = {}, set()
    on_map = collections.defaultdict(set)
    for name, author in resolved.items():
        for work in works(author["openalex"], since, cache=False, select=SELECT):
            if (work.get("publication_date") or "") > today.isoformat():
                continue  # OpenAlex sometimes carries future-dated records; they show up once they are due
            title = (work.get("title") or "").lower()
            if work.get("type") in SKIP_TYPES or not title or any(marker in title for marker in SKIP_TITLES):
                continue
            if not on_topic(work, name in core_only):
                off_topic.add(work["id"])
                continue
            found[work["id"]] = work
            for authorship in work["authorships"]:
                author_id = authorship["author"].get("id")
                if author_id and short_id(author_id) in id_to_name:
                    on_map[work["id"]].add(id_to_name[short_id(author_id)])

    candidates = list(found.values())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        status = dict(zip((w["id"] for w in candidates), pool.map(lambda w: check(link(w)), candidates)))
    # Merge versions of the same title (preprint, published, repository copy): prefer a working link, then a DOI.
    versions = collections.defaultdict(list)
    for work in candidates:
        versions[title_key(work)].append(work)
    merged = []
    for group in versions.values():
        group.sort(key=lambda w: (status[w["id"]] != "✓", status[w["id"]] == "✗", not w.get("doi")))
        keep = group[0]
        for other in group[1:]:
            on_map[keep["id"]] |= on_map[other["id"]]
        merged.append(keep)
    ordered = sorted(merged, key=lambda w: (w.get("publication_date") or "", w.get("title") or ""), reverse=True)

    per_person = collections.Counter(n for w in ordered for n in on_map[w["id"]])
    lines = [
        f"# Watch: {since} to {today.isoformat()}",
        "",
        f"{len(ordered)} new works by {len(per_person)} people on the map (OpenAlex, by publication date; "
        f"{len(off_topic)} off-topic records skipped). "
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
    broken = sum(1 for w in ordered if status[w["id"]] == "✗")
    print(f"{len(ordered)} works → {out.relative_to(FIELD.parent)} ({broken} broken links)")


if __name__ == "__main__":
    main()
