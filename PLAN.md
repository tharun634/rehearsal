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
  model (`docs/transcripts/demo-server-2026-10-04.md`: 5 turns, 12 corrections,
  4798/1566 tokens), and the coach's error kinds were checked against what the
  learner actually typed rather than believed.
- [ ] **M4 — hand-over.** `report` printed and given to the friend; their reply
  quoted in the DEV post.
- [ ] **M5 — post.** `docs/DEV_POST.md` against the challenge template, with the
  session saved through DevRelay.

## What has to be true before I call this done

1. `doctor` passes against the real model: the schema is honoured, not suggested.
2. A scene runs to a **goal**, and can fail. Grammar alone is not a pass.
3. Every card in the deck traces to a turn the learner actually typed.
4. `grep -rn http src/` shows only `127.0.0.1`. No path exists to send the friend's turns.
5. Numbers in the README are measured on this machine, not copied from a model card.
6. The hand-over sheet exists as a file, and the friend has seen it.

## Open questions — answered by measurement

- **Does the coach's `kind` classification survive on a 4B model?** No. In the
  real cafe run the 12 corrections came back as `grammar`, `vocabulary` and one
  `word_order` — `particle`, `register` and `pronunciation` never appeared, and
  the `why` text invented facts (`mado` called "a type of bread", `Sato` called
  English). The deck uses the *span* the learner typed, not the kind, so the
  cards still work; the kind labels are cosmetic and the hand-over sheet says
  "practise this", never "this rule". See DECISIONS.md, "The coach is a nudge,
  not a teacher".
- **Does `mode = "cli"` survive a reload per call?** One `doctor` call in cli
  mode measured **17.8 s wall** on this box (model load + prompt eval + 8 tokens),
  and llama-cli's own line read `[ Prompt: 4.0 t/s | Generation: 0.8 t/s ]` while
  RAM was starved. Survivable for a 5-turn session (~10 calls ≈ 3 minutes of
  overhead) but not competitive with the resident server; cli exists so the
  session can coexist with another model, not to be fast.
- **Long-vowel pronunciation feedback from a text model is a guess, not audio.**
  Left as a guess and labelled that way in the README; no clip bank yet. This is
  the one open gap worth naming before the post.
