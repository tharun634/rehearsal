# Rehearsal

A patient conversation-practice partner for **a friend who is learning Japanese**,
built on `llama.cpp` and nothing else. No API key, no server, no upload path.

The friend's problem: they can order at a counter, and they freeze anywhere the
counter stops being a script. Duolingo grades single sentences; it cannot hold a
two-minute scene, it cannot be told *"this person keeps mixing the politeness
levels, set that up for them"*, and every sentence they type into it goes to
someone's server.

Rehearsal runs a scene instead. A barista, a ticket clerk, a colleague on a call.
The model plays a **person** who never corrects them; a second call reads their
turn and writes the correction beside it. Their own mistakes become the deck, and
the deck becomes the watch list the next scene is built on.

```
$ python run.py practice --scenario cafe-aoi

Barista: Ah, good morning! Welcome to Café Aoi. What would you like today?
  · scene: greet
you> Ahara, sumisu no ogi, sato please.
  ✓ they got across
  - sato → satoh  [pronunciation]
    Final -s in a loanword needs the long vowel: satoo/satoh.
  say instead: Ahara, sumisu no ogi, satoh, please.
  · scene: choose

Barista: The ham sandwich is sold out this morning — anything else?
you> ...
```

## What it does

| verb | what happens |
|---|---|
| `doctor` | is llama.cpp reachable, and does it emit schema-valid JSON? |
| `practice --scenario cafe-aoi` | run a scene: partner + coach + memory |
| `review` | drill **this learner's** own sentences (SM-2 scheduling) |
| `report --out docs/handout.html` | the printable sheet you actually hand over |
| `stats` | what the memory holds |
| `scenarios` | the scenes |
| `profile --name ... --language ... --level ...` | set the friend |

Four scenes ship: `cafe-aoi`, `station-ticket`, `work-intro`, `pharmacy`. Each has
tasks and a goal, so a session can *fail*, which is the point: the friend has to
be understood, not just be grammatical.

## Quickstart

```
python -m venv .venv && .venv/Scripts/activate      # optional: the core is stdlib-only
python run.py doctor --engine mock                  # proves the pipeline, no model needed
python tools/get_llama.py                           # prebuilt llama.cpp binaries
python tools/get_model.py                           # Gemma-3-4b-it Q4_K_M (or --model gemma-3-1b for a tight laptop)
python run.py doctor                                  # now against the real model
python run.py practice --scenario cafe-aoi
```

Set `mode` in `config/engine.toml` first:

- `mode = "server"` — `llama-server` resident, fast, ~2.6 GB for Gemma-3-4B Q4_K_M.
- `mode = "cli"` — `llama-cli` one-shot per call, **nothing resident**. Use this when
  something else on the machine already owns the GPU; you pay the reload instead of the RAM.
- `mode = "mock"` — canned, tests only.

## Why open innovation matters here

| claim | what makes it possible |
|---|---|
| runs with no internet | `llama-server`/`llama-cli` are local binaries; the repo has no request to any host except the local one — `grep -rn http src/` returns `127.0.0.1` |
| the friend's data never leaves the machine | there is no upload path to not-use; turns go to sqlite on disk |
| swap and fine-tune | GGUF swap at runtime; the coach is a schema, so a fine-tuned correction model drops in without touching the loop |
| costs nothing | zero API calls; the cost is tokens/second, measured in `docs/research/` |
| inspectable | every correction carries the schema field it came from; every card points at the turn it came from |

A closed API gets the first two rows wrong outright. It gets the third expensively.
Where open **lost** is written up in `docs/research/` too — a 4B model mis-merges
long sentences, and a bigger closed model would have got those right while shipping
the friend's turns to a server.

## Layout

```
run.py                 entry point, no pip install needed
src/rehearsal/
  engine.py            llama.cpp adapter: server | cli | mock, JSON-schema constrained
  prompts.py           the partner prompt (a person) and the coach prompt (a reader)
  session.py           the loop: partner turn → learner turn → coach report → memory
  memory.py            sqlite: turns, cards, sessions, and the watch list
  srs.py               drilling the learner's own sentences
  report.py            the printable hand-over sheet
  cli.py               the verbs
config/
  learner.toml         the friend: name, language, level
  engine.toml          how to reach llama.cpp
  scenarios/*.toml     scenes: role, register, goal, tasks
tests/test_pipeline.py end-to-end with the mock engine
docs/                  DEV post draft, measurements, user guide
tools/                 get_llama.py, get_model.py
data/                  the friend's memory — gitignored, never uploaded
```

## Privacy

`data/` is gitignored and holds the friend's turns: who they work with, where they
go, what they are doing. Nothing in this repo can send it anywhere. If you fork
this for a real person, that directory is the one thing you must not commit.

## Honesty

The model is not a language teacher. It is a 4-billion-parameter guess machine
wearing a schema. Corrections are checked against the friend's own usage, not
against a grammar. Anything the friend intends to *act* on — a fare, a medicine,
a deadline — gets confirmed with a human, not with the coach.
