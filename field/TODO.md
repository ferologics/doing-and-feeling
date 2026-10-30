# Field: TODO

## Map

- [x] Seed list of researchers (`people.toml`) from the series, the companion and the thread
- [x] Resolve each person to an OpenAlex author (`just field resolve`), with ambiguous matches flagged
- [x] Co-authorship map among the seed people (`just field map` → `map.md`, `map.html`); links count papers with ≤10
      authors, larger collective papers (letters, consensus pieces, adversarial collaborations) listed separately
- [ ] Review the first-pass camp tags and add a source for each; check two OpenAlex profiles that may be merged with
      namesakes (Michael Timothy Bennett: 134 works; Christof Koch: listed at IMEC)
- [ ] Argument edges: BBS target articles and their commentators, adversarial collaborations (Cogitate, INTREPID, ConTraSt)
- [ ] Lab and funding affiliations (Anthropic, Google DeepMind, Eleos, Rethink Priorities, CIFAR, Templeton)
- [ ] Grow the seed list from the map's own co-author network (who keeps appearing next to the seed people)

## Watch

- [x] Digest of new works by the seed people (`just field watch` → `digests/<date>.md`), links checked
- [ ] Add sources OpenAlex indexes late or not at all: arXiv listings, PhilPapers, PsyArXiv, bioRxiv
- [x] Topic filter (stricter `watch = "core"` for people who publish widely), merged versions, no datasets
- [ ] Rank and summarise: what's notable this period and why (with the checking discipline)
- [x] Run it on a schedule: pi-jobs job `consciousness-research-digest` (Mondays 08:30) commits and pushes the digest, notifies on notable papers

## Later

- [ ] Ledger: format, first credences once the series is finished
- [ ] Scorecard: the 14 indicators × current frontier models
- [ ] Dispatch episode format
