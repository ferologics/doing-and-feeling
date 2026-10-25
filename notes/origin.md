# Origin: how the podcast was made

## The ask

Prompt given to Claude (claude.ai), October 2026:

> https://www.youtube.com/watch?v=gs38tMxZseA
> https://whatisintelligence.antikythera.org/
>
> are these good resources? what should i know about intelligence? and the science of intelligence? science and theory of consciousness. are u able to compile all this info into a lecture / podcast i can listen to? how long would it be?
>
> see attached stuff grok gave me from the original twitter post (https://x.com/willdepue/status/2113823172336505051?s=20)

Attached to the prompt:

- 9 screenshots of replies in the @willdepue thread → `notes/reference-screenshots/` (index below)
- Grok's summary of the thread → `notes/grok-thread-summary.md`

## The two links

Both are Blaise Agüera y Arcas's *What Is Intelligence?* project (Antikythera / MIT Press):

- Book, free to read online: https://whatisintelligence.antikythera.org/
- Lecture: https://www.youtube.com/watch?v=gs38tMxZseA. YouTube metadata: "What is Intelligence? lecture by Blaise Agüera y Arcas", channel Antikythera, uploaded 2025-09-04, 1:28:07. (Claude called it "~80 minutes, recorded in London in 2024"; the recording date is from Claude, not checked here.)

## The Claude conversation

- Share link: https://claude.ai/share/74b0fff9-4946-4781-ac30-86969c0b9682
- Visible text of the share: `notes/claude-share.txt` (pulled with a headed browser; Cloudflare blocks headless fetches)
- Final response, verbatim: `notes/claude-final-response.md`
- The share hides files, so the **episode scripts and the TTS pipeline are not recoverable from it**. To iterate on the scripts, ask Claude in that conversation to export the four scripts as text.

Production details stated by Claude in that conversation (not independently checked):

- Two synthetic voices, Kokoro TTS. The MP3 tags say "Written by Claude; synthetic voices (Kokoro TTS)."
- Three research passes fact-checked the scripts (one covered intelligence facts, one consciousness science), then an independent reviewer read them.
- Corrections applied after the review: episode 2's map had implied the hard problem rules out AI consciousness (Chalmers thinks the right functional organization would be conscious); a red-blood-cell/mitochondria slip; a "1990" anachronism; episode 4 gave the functionalist side fewer replies.
- Pronunciation fixes: "Dennett", "bat", "perturbational", "acing"; negative-contraction questions ("Is not that just…") rephrased.
- Mastered to −17.2 LUFS integrated with about 2 dB of true-peak headroom.
- Claude's search budget ran out before it could read the October 2026 *Nature* comment by Seth, Block and Tononi. That piece has since been checked: see `notes/sources.md`.

## The audio files (verified here)

| Episode | File | Duration | MP3 title tag |
|---|---|---|---|
| 1 | `short/audio/Doing-and-Feeling-1-Doing.mp3` | 16:47 | Doing and Feeling 1/4 – Doing: what intelligence is |
| 2 | `short/audio/Doing-and-Feeling-2-Feeling.mp3` | 14:51 | Doing and Feeling 2/4 – Feeling: the hard problem, and a map of the positions |
| 3 | `short/audio/Doing-and-Feeling-3-Measuring.mp3` | 14:37 | Doing and Feeling 3/4 – Measuring: what the science of consciousness can show |
| 4 | `short/audio/Doing-and-Feeling-4-Machines.mp3` | 15:44 | Doing and Feeling 4/4 – Machines: could an AI feel anything? And where to read next |

All four: MP3, mono, 44.1 kHz, ~80 kbps, artist "Claude (AI-generated)", album "Doing and Feeling", 1400×1400 cover embedded. Episode 3 measures −17.2 LUFS integrated, −1.9 dBTP true peak (ffmpeg `ebur128`).

Covers: `short/covers/*-cover-4K.png`, 3840×3840 RGB, solid background `#111319`. Claude designed them (doing/feeling Venn diagram with a muted "?" in the overlap).

## Series outline (from the transcripts)

1. **Doing**: three traditions for defining intelligence (psychometrics/g, generality à la Legg–Hutter and Chollet/ARC, prediction/compression); Agüera y Arcas's thesis (life is computation, intelligence is prediction, functionalism, symbiogenesis, LLMs as an evolutionary transition); octopuses and Michael Levin's basal cognition; place/grid cells and the Tolman–Eichenbaum machine ↔ transformer link; what LLM interpretability shows; jaggedness and Moravec's paradox.
2. **Feeling**: Nagel's bat; Chalmers's hard problem, zombies; Mary's room; a map from functionalism → illusionism (Dennett, Frankish, Carlsmith, meta-problem, Wittgenstein) → strange loops/Metzinger/*Blindsight* → biological naturalism (Searle, Seth) → IIT → panpsychism (Goff vs. Carroll) → idealism/dualism/mysterianism → Orch OR; Schwitzgebel's "United States is conscious"; the single question that sorts all positions.
3. **Measuring**: NCC and contrastive method; masking, rivalry, inattentional blindness; blindsight, split brains; Libet and Schurger; covert awareness (Owen 2006, Bodien 2024); PCI "zap and zip"; theory families (GWT, higher-order, recurrent processing, IIT, predictive processing), front vs. back, no-report paradigms; the IIT pseudoscience letter; Solms, Friston, *A beautiful loop*; attention schema; unlimited associative learning; the Cogitate adversarial collaboration (Nature 2025).
4. **Machines**: indicator properties (Butlin, Long et al. 2023, updated 2025); Chalmers 2023; Anthropic's global-workspace and introspection work (flagged as a conflict of interest); recurrence in transformers; Seth's biological naturalism, carbon chauvinism, IIT on hardware; the functionalist reply; Birch's gaming problem; *Perceived AGI* and Suleyman's "seemingly conscious AI"; risks both ways (Schwitzgebel's full-rights dilemma, Birch's precaution, UK animal sentience law); expert survey, laws, lab positions; what would move the needle; reading path and what to skip.

Machine transcripts (Whisper large-v3-turbo, word timestamps) are in `short/whisper/`. They are **not** the original scripts and contain mis-hearings (e.g. "Aguera e Arcus", "Chalet" for Chollet, "Girdle, Escher, Bach"), plus a few dropped phrases.

## Reference screenshots

| File | What it shows |
|---|---|
| `01-thread.png` | @teortaxesTex: Koch's *The Feeling of Life Itself* as a challenge to computational functionalism ("I can't endorse IIT as constructed here"), plus Koch's *Confessions of a Romantic Reductionist* and *The Quest for Consciousness* |
| `02-thread.png` | Apple Podcasts page: Sean Carroll's Mindscape, "Philip Goff on Consciousness Everywhere" (Nov 4, 2019, 1h35m) |
| `03-thread.png` | "GEB is trash"; Peter Watts's *Blindsight*, inspired by *Being No One*; Nagel's bat essay ("16 pages long, 30 minute read. Must read") |
| `04-thread.png` | @beffjezos: *Active Inference* (Parr, Pezzulo, Friston); start of @planet_nerf's GEB reply |
| `05-thread.png` | @planet_nerf: GEB photo; @leothecurious's six-paper list (A beautiful loop; Why Is Anything Conscious?; Cogitate adversarial test; Hard Problem + FEP; Could an LLM be Conscious?; A global workspace in language models) |
| `06-thread.png` | @malikules: *Other Minds* ("easy classic") and Ginsburg & Jablonka ("most comprehensive textbook… takes a whole year"); "You're conscious! Just pay attention for a day"; Michael Timothy Bennett's "How to Build Conscious Machines" talk |
| `07-thread.png` | "Read Consciousness Explained by Dennett"; Gurdjieff/Maxwell image reply; Orch OR microtubules meme |
| `08-thread.png` | Schwitzgebel, "If Materialism Is True, the United States Is Probably Conscious"; Graziano's *Rethinking Consciousness*; start of the Michael Levin reply |
| `09-thread.png` | Michael Levin / @david_i_spivak; Fin Moorhouse's illusionism links (PhilPapers/Chalmers, Frankish, Dennett, Carlsmith, a YouTube playlist); "@dioscuri" (Henry Shevlin, per Claude); "Probably all you need." |
