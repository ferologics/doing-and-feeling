#!/usr/bin/env python3
"""Match every person in people.toml to an OpenAlex author and write authors.json.

Candidates come from OpenAlex author search. Each is scored by how many of its research topics relate to mind,
brain, cognition or AI, weighted by output; a `hint` in people.toml must match the candidate's institutions or
topics. A match is marked "check" when the best candidate is weak or a second plausible candidate exists. Set
`openalex = "A…"` in people.toml to override a match by hand.

Usage: field/scripts/resolve.py
"""

import json
import math
import sys

from openalex import FIELD, get, people, short_id

RELEVANT = (
    "conscious", "cognit", "neuro", "brain", "philosoph", "mind", "percept", "attention", "sleep", "anesthe",
    "artificial intelligence", "machine learning", "neural network", "memory", "metacognit", "embodied",
    "free energy", "decision", "emotion", "evolution", "animal", "language model", "reinforcement", "ethic",
)


def describe(author):
    institutions = [i.get("display_name", "") for i in author.get("last_known_institutions") or []]
    topics = [t["display_name"] for t in author.get("topics") or []]
    return institutions, topics


def relevance(author):
    _, topics = describe(author)
    top = topics[:10]
    if not top:
        return 0.0
    hits = sum(1 for t in top if any(k in t.lower() for k in RELEVANT))
    return hits / len(top) * math.log10(author.get("works_count", 0) + 10)


def matches_hint(author, hint):
    institutions, topics = describe(author)
    return any(hint.lower() in text.lower() for text in institutions + topics)


def resolve(person):
    if person.get("openalex") == "none":
        return None, "none", []
    if person.get("openalex"):
        author = get(f"authors/{person['openalex']}")
        return author, "manual", []
    candidates = get("authors", {"search": person["name"], "per-page": 10})["results"]
    if person.get("hint"):
        hinted = [c for c in candidates if matches_hint(c, person["hint"])]
        if not hinted:
            ranked = sorted(candidates, key=relevance, reverse=True)
            return (ranked[0] if ranked else None), "check", ranked[1:3]
        candidates = hinted
    ranked = sorted(candidates, key=relevance, reverse=True)
    if not ranked:
        return None, "missing", []
    best, rest = ranked[0], ranked[1:]
    plausible_rest = [c for c in rest if relevance(c) >= 0.5 * relevance(best) and relevance(c) > 0.5]
    confidence = "ok" if relevance(best) >= 1.0 and not plausible_rest else "check"
    return best, confidence, plausible_rest[:2]


def main():
    resolved, report = [], []
    for person in people():
        author, confidence, alternatives = resolve(person)
        if author is None:
            if confidence == "none":
                resolved.append({"name": person["name"], "openalex": None, "confidence": "none"})
            else:
                report.append(f"MISSING  {person['name']}")
            continue
        institutions, topics = describe(author)
        resolved.append({
            "name": person["name"],
            "openalex": short_id(author["id"]),
            "display_name": author["display_name"],
            "works_count": author.get("works_count", 0),
            "institution": institutions[0] if institutions else None,
            "topics": topics[:5],
            "confidence": confidence,
            "alternatives": [
                {"openalex": short_id(a["id"]), "display_name": a["display_name"], "works_count": a.get("works_count", 0),
                 "institution": (describe(a)[0] or [None])[0], "topics": describe(a)[1][:3]}
                for a in alternatives
            ],
        })
        if confidence == "check":
            report.append(
                f"{confidence.upper():8} {person['name']} -> {author['display_name']} ({short_id(author['id'])}, "
                f"{author.get('works_count', 0)} works, {institutions[:1]}, {topics[:3]})"
            )
    (FIELD / "authors.json").write_text(json.dumps(resolved, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(resolved)} of {len(people())} people resolved; {len(report)} need a look:")
    print("\n".join(report))
    return 0 if resolved else 1


if __name__ == "__main__":
    sys.exit(main())
