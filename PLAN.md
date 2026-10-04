# PLAN

**What this is.** A conversation-practice partner for one friend learning Japanese.
It runs a *scene* — a barista, a ticket clerk, a colleague — with a local model
playing a person who never corrects the learner. A second model call reads the
learner's turn and writes the correction beside it. The learner's own mistakes
become the deck; the deck becomes the watch list the next scene is built on.

**Why it exists.** Duolingo grades single sentences. It cannot hold a two-minute
scene, cannot be told *"this person keeps mixing politeness levels, set that up
for them"*, and every sentence typed into it goes to someone's server. The friend
can order at a counter and freezes the moment the counter stops being a script.

**Stack.** `llama.cpp` (server or one-shot CLI) + Gemma-3-4B-it Q4_K_M + Python
stdlib only. sqlite for the memory. No framework, no API, no upload path.

## Milestones

- [x] **M0 — plan.** This file, plus DECISIONS.md and AGENTS.md before code.
- [x] **M1 — pipeline.** engine adapter (server/cli/mock) + JSON-schema constraint
  + scene loop + sqlite memory + SRS + report + CLI. `python run.py doctor --engine mock`
  and `python -m unittest tests.test_pipeline` green.
- [x] **M2 — real engine.** `tools/get_llama.py` + `tools/get_model.py` fetched
  llama.cpp b11379 (Vulkan build) and Gemma-3-4B-it-Q4_K_M; `doctor` passes in
  server AND cli mode; measured numbers in `docs/research/2026-10-04-record.md`
  (101–115 tok/s with the GPU while RAM was free, 1.9 tok/s while it was not).
- [x] **M3 — the friend.** A scripted session played end-to-end against the real
  model, twice: the starved-machine run (`docs/transcripts/demo-server-2026-10-04.md`
  before the retry fix: 5 turns, 12 corrections, 829.7 s, 4798/1566 tokens) and the
  clean one after it (`docs/transcripts/both-server-2026-10-04.md`: 5 turns, 15
  corrections, **21.9 s**, 4784/1858 tokens ≈ 85 tok/s wall). Same session in
  `mode = "cli"` (`docs/transcripts/both-cli-2026-10-04.md`): 5 turns, 9 corrections,
  **40.9 s**, tokens 0/0 because cli reports no usage.
- [x] **M4 — hand-over.** DONE: handed to Arjun, sheet at `docs/handout.html`, and
  his reply is quoted verbatim in `docs/DEV_POST.md` ("Handing it over"). He ran the
  café scene himself and called the coach out — the post keeps his words and the
  invented `tonkatsu-men` rather than sanding both off.
- [x] **M5 — post.** DONE: DEV article 4794935 is **live** at
  https://dev.to/tharun634/rehearsal-an-offline-japanese-practice-partner-for-a-friend-built-on-llamacpp-5bme
  with the three challenge tags, and agent session 435 is published, so
  `{% agent_session 435 %}` renders as a real embed. The repo link renders as DEV's
  GitHub embed (a bare URL on its own line — an `<iframe>` gets stripped).
  Verified against the live HTML: the numbers table's last row survived (no `|` inside
  a code span) and the demo blockquote's `say instead` / `coach nudge` / `scene moved
  on` lines are separate paragraphs.

## What has to be true before I call this done

1. `doctor` passes against the real model: the schema is honoured, not suggested.
2. A scene runs to a **goal**, and can fail. Grammar alone is not a pass.
3. Every card in the deck traces to a turn the learner actually typed.
4. `grep -rn http src/` shows only `127.0.0.1`. No path exists to send the friend's turns.
5. Numbers in the README are measured on this machine, not copied from a model card.
6. The hand-over sheet exists as a file, and the friend has seen it.

## Open questions — answered by measurement

- **Does the coach's `kind` classification survive on a 4B model?** Partly, and it
  improved once the retry fix landed. The clean 15-correction run returned
  `grammar` 8, `vocabulary` 4, `word_order` 1, `particle` 2 — and the earlier run
  had only `grammar`/`vocabulary`. `register` appeared twice in the other run.
  `pronunciation` and `comprehension` still never appear from the real model (the
  mock test emits `pronunciation`, which is how that label got into the counts).
  What did NOT survive is the content: `said` is still the learner's whole turn,
  not the shortest span, and the `why` text still invents — it offered the barista
  "Could you tell me what kind of bread you'd like?" as a nudge and invented the
  menu words `tonkatsu-men`/`katsudon-men`. The deck uses the *span* the learner
  typed, not the kind, so the cards still work; the kind labels are cosmetic and
  the hand-over sheet says "practise this", never "this rule". See DECISIONS.md,
  "The coach is a nudge, not a teacher".
- **Does `mode = "cli"` survive a reload per call?** Yes, and with the machine
  roomy a whole 5-turn cli session costs **40.9 s** (10 calls ≈ 4 s each) against
  the server's 21.9 s — so the reload is about 2× the session, not a disaster.
  The starved-machine numbers are the ones that matter: one `doctor` call was
  **17.8 s wall** and llama-cli's own line read `[ Prompt: 4.0 t/s | Generation:
  0.8 t/s ]`. cli exists so the session can coexist with another resident model,
  not to be fast.
- **Long-vowel pronunciation feedback from a text model is a guess, not audio.**
  Left as a guess and labelled that way in the README; no clip bank yet. This is
  the one open gap worth naming before the post.
