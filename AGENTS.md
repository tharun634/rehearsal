# AGENTS.md

Working notes for anyone continuing this repo — agent or human.

## The one-sentence invariant

**Nothing in `src/` may reach a host that is not local.** The friend's turns are
the most sensitive thing in the repo. `grep -rn http src/` must return only
`127.0.0.1`. If a change adds a remote endpoint, it goes in `config/engine.toml`
as an explicit, documented escape hatch — never as a default, and never silently.

## Commands

```
python run.py doctor --engine mock          # pipeline proof, no weights needed
python -m unittest tests.test_pipeline -v   # the four pipeline invariants
python run.py practice --scenario cafe-aoi  # needs a real engine
python run.py report --out docs/handout.html
```

`run.py` exists so the repo needs no `pip install` and no packaging: it puts
`src/` on `sys.path` and calls `rehearsal.cli.main`. Do not "fix" this into a
`pip install -e .` package without saying why — the zero-install property is a
feature, not laziness.

## Layout rules

- `src/rehearsal/*` — stdlib only. No numpy, no requests, no pydantic. `urllib`
  for the local server call, `sqlite3` for memory, `tomllib` for config.
- `config/` is data, not code. A new scene is a `.toml` file, not a new module.
- `data/` is gitignored and holds the friend's real turns. **Never commit it,
  never paste it into a post, never use it as a test fixture.**
- `docs/research/` holds measurements taken on this machine. A number in the
  README that is not in `docs/research/` is an unverified claim and must be
  marked as such.

## Things that are deliberately not here

- No ASR. There is no `whisper.cpp` on this machine, and the friend types. If
  voice input is added, it is local-only and it is a separate decision.
- No web UI. The hand-over artifact is a printable HTML sheet, because the thing
  a friend keeps is paper.
- No cloud fallback path. If llama.cpp is unreachable, `doctor` fails and says so.
  A silent remote fallback would be the worst feature in this repo.

## Known Windows traps (already handled — do not regress)

- `console.utf8_console()` must run before any `print`. cp1252 crashes on ✓ and
  on Japanese.
- `memory.connect` caches one handle per db path. Two open handles to the same
  sqlite file raise `database is locked` on Windows.
- Paths in this repo are written with `/` and passed through `pathlib`; do not
  hand-concatenate with `\` in a shell string.

## Where the next work is

`PLAN.md` lists milestones; M2 (real engine + measured numbers) is the next
incomplete one. `DECISIONS.md` records why each choice was made and what would
reopen it — read it before changing a stack choice.
