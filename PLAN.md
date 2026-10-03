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
- [ ] **M2 — real engine.** `tools/get-llama.ps1`, `tools/get-model.ps1`, `doctor`
  against Gemma, and the first measured numbers (tokens/second, RAM, wall time per
  turn) in `docs/research/`.
- [ ] **M3 — the friend.** A scripted session played end-to-end against the real
  model, transcript in `docs/transcripts/`, and the coach's error kinds checked
  against the learner's own usage rather than believed.
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

## Open questions

- Does the coach's `kind` classification survive on a 4B model, or is it mostly
  `grammar`? Measured in M3, not assumed.
- `mode = "cli"` pays a model reload per call. Is that survivable, or does the
  session need to batch calls? Measured in M2.
- Long-vowel pronunciation feedback from a text model is a guess, not audio.
  Either drop that error kind or pair it with a clip bank.
