# Hand-over guide — how to use Rehearsal

This is the sheet that goes to the learner. It assumes the repo is already set up
(`.venv` optional — the core is stdlib-only Python).

## What you are actually doing

You are ordering coffee at a café that is not a café. The person behind the counter
is a model running on your own machine. Your job is to get across, in Japanese, the
thing you came to order. The scene has tasks — greet, choose, modify, size, pay —
and it can **fail**. Being grammatical is not a pass; being *understood* is.

Four scenes ship: `cafe-aoi` (morning rush), `station-ticket` (a ticket machine that
only speaks Japanese), `work-intro` (introducing yourself at a new job),
`pharmacy` (asking a counter clerk for something specific).

## The three commands you need

```
python run.py practice --scenario cafe-aoi            # type your own lines
python run.py review --n 10                           # practise your own weak spots
python run.py report --out docs/handout.html          # the sheet to print
```

`practice` prints the partner's line, you answer in romaji (or Japanese script),
the coach answers in your language. Nothing else.

## The one thing that will bite you on this machine

`mode = "server"` keeps a 2.6 GB model resident. If something else on the machine
already owns the RAM and the GPU, that model pages and everything drops from ~110
tok/s to ~2 tok/s. Two ways out:

- close the other model first, then run `practice` (fastest, and what the demo does);
- or set `mode = "cli"` in `config/engine.toml`: nothing stays resident, you pay a
  ~18 s reload per call instead of the RAM.

If a run dies mid-session, the model is still resident. `python tools/stop_llama.py`.

## What the coach is, and is not

The coach is a 4B model. It is good at one thing: noticing **where** you struggled,
and that is what the deck and the hand-over sheet use. It is bad at another: the
Japanese facts in its `why`. In a real run it called `mado` "a type of bread" and
told the learner `Sato` was English. Read the nudge as "practise this span", never
as "this is the rule". If you want rules, look them up — the tool never sends your
turn to a server, so it never looks anything up either.

## Where your data lives

`data/learner.sqlite3`, on your machine, gitignored, never uploaded. There is no
upload path in the code: `grep -rn http src/` returns one line, `127.0.0.1:8082`.
Delete the file and the deck and the memory are gone. That is the whole privacy
model, and you can read it in twelve lines of `src/rehearsal/memory.py`.
