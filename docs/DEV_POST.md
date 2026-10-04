# DEV post draft — publish after the friend has actually replied

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).*

## What I Built

**Rehearsal** — a conversation-practice partner for a friend of mine who is learning
Japanese. They have been studying grammar at a desk for a couple of years and they
freeze the moment a real person speaks to them: a café counter, a ticket machine,
introducing themselves at a new job. Nothing they practise at a desk prepares them
for the two seconds of panic in front of a stranger.

So I built the stranger. Not a tutor — a *person* who does not correct, does not
wait, and does not care about grammar. The scene has tasks (greet, choose, modify,
size, pay) and a goal, and it can **fail**. Being grammatical is not a pass; being
*understood* is. That is the whole design decision, and it is why the tool is not
Duolingo.

The friend's name is a placeholder in the repo (`config/learner.toml` says
`REPLACE-WITH-FRIEND-NAME`). I am not going to put a real person's name in a public
repo for a thing that holds their turns. Everything else about them — their level,
their first language, the scenes they practise — is theirs, and it lives on their
machine.

## Demo

The session below is real: llama.cpp b11379, Gemma-3-4B-it Q4_K_M, five turns,
12 corrections, 4798 prompt / 1566 completion tokens, in a café scene.

> **Barista:** おはようございます！ Welcome, what can I get for you today?
> **learner:** Konnichiwa, sumisu no ogi, mado.
>
> **coach:** they got across
> - `Konnichiwa, sumisu no ogi, mado.` → `Konnichiwa, sumisu no ogi o onegaishimasu.` (word_order) — the sentence structure is not quite natural for a request in Japanese.
> **say instead:** Konnichiwa, sumisu no ogi o onegaishimasu.
> **coach nudge:** Try rephrasing your request with a polite request particle.
> *scene moved on: greet*

**Disclosure, because it matters:** the five learner lines are *scripted*
(`docs/demos/script-cafe-aoi.txt`), not transcribed speech. I do not have whisper.cpp
on this machine and I was not going to record a real friend's Japanese and put it in
a public repo. The partner and the coach are the model's own output; the learner's
lines are mine, written to carry the kind of errors this friend actually makes.

## Code

<iframe src="https://gh-scm-snapshot.dev.to/gh-embed-tharun634-rehearsal"></iframe>

[github.com/tharun634/rehearsal](https://github.com/tharun634/rehearsal) — MIT, 33
tracked files, no pip install needed for the core.

## How I Built It

One adapter, three engines, and the loop never knows which one it is in:

```
src/rehearsal/
  engine.py     llama.cpp adapter: server | cli | mock, JSON-schema constrained
  prompts.py    the partner prompt (a person) and the coach prompt (a reader)
  session.py    partner turn → learner turn → coach report → memory
  memory.py     sqlite: turns, cards, sessions
  srs.py        SM-2 lite over the cards
  report.py     the hand-over sheet
```

- **Open-weight model, local inference.** llama.cpp's own prebuilt binaries
  (`tools/get_llama.py` pulls the release zip) and Gemma-3-4B-it Q4_K_M (2.49 GB)
  from a HF GGUF mirror (`tools/get_model.py`). No Ollama — the machine has llama.cpp
  and I would rather download one thing than two.
- **Two engine modes, because of the machine, not the design.** `server` keeps the
  model resident and is fast. `cli` runs `llama-cli` one-shot per call and keeps
  **nothing** resident. My friend's machine is my machine, and it already runs a
  bigger llama.cpp server for coding. Two resident models on 32 GB with 252 MB free
  is not a configuration, it is a page-fault storm.
- **JSON-schema constrained, not prompt-and-hope.** In server mode the schema goes
  into `response_format`, which llama.cpp turns into a GBNF grammar — the model
  cannot leave the shape. In cli mode that grammar sampler is broken on this build
  (`common_sampler_init: error initializing grammar sampler ... Unexpected empty
  grammar stack after accepting piece: <start_of_turn>`), so the cli path sends a
  shape *hint* and `parse_json_loose` recovers from fences and prose. That bug is
  in the repo, not hidden in a footnote.
- **Memory is a tally, not a vector store.** Three sqlite tables. The deck is
  spaced-repetition (SM-2 lite) over *the sentences the learner actually typed* —
  every card's front is something they wrote, which is the invariant that keeps the
  SRS honest.

## Why Does Open Innovation Matter?

**It runs on a laptop with no internet.** `grep -rn http src/` returns exactly one
line: `cfg.setdefault("base_url", "http://127.0.0.1:8082")`. There is no upload path
to not-use.

**It keeps someone's data off a server they don't control.** This is the reason the
open version is the *only* acceptable version here. The thing being stored is a
person's language mistakes — the record of a person being wrong in public. A closed
API would ship that to a server for a friend who never agreed to it. Deleting
`data/learner.sqlite3` deletes the memory, and you can read that whole privacy model
in twelve lines.

**It lets you swap the model and change how the agent behaves.** The friend is at
A2 and will be at B1 next year. `config/learner.toml` is theirs; the coach is a
schema and a prompt, so a fine-tuned correction model drops in without touching the
loop. A closed model is a subscription I cannot make say "be patient, never correct
the partner".

**It costs nothing to run.** Zero API calls. The cost is tokens/second, and I measured
it instead of quoting a model card.

**Where open lost, honestly.** A 4B model is a bad teacher. In the real run the coach
called `mado` "a type of bread" and told the learner `Sato` was English instead of
Japanese. A bigger closed model would have got those two facts right — while sending
the friend's turns to a server. So the coach is a *nudge*, and the deck uses the span
the learner typed, not the coach's claim. That trade is written up in
`docs/research/` and in DECISIONS.md ("The coach is a nudge, not a teacher").

## The numbers, both of them

Same model, same box, same day, 60× apart:

| condition | speed |
|---|---|
| GPU free, RAM free | **101–115 tok/s** generation, 71 tok/s prompt eval |
| another model holding the RAM (paging against `C:\pagefile.sys`) | **1.9 tok/s** — 5 turns, 1566 completion tokens, 829.7 s |
| `mode = "cli"`, RAM starved | one `doctor` call = **17.8 s** wall, `[ Prompt: 4.0 t/s | Generation: 0.8 t/s ]` |

The spread is not the model, it is the machine. A 2.49 GB model on a 32 GB box with
252 MB free pages, and paging is where the whole difference lives. Anyone who quotes
one of those numbers without the other is describing a different machine.

## My Agent Session

<!-- embed with the agent_session tag once DevRelay has uploaded it -->

## Prize Categories

- **Gemma — Best Use of Gemma** (featured): Gemma-3-4B-it Q4_K_M, run locally, swapped
  at runtime, `--model gemma-3-1b` for a tight laptop.
- **Entire — Best Use of Entire**: the agent sessions behind the build are shared
  through DevRelay above.

<!-- Thanks for participating! -->
