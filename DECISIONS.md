# DECISIONS

The log of what was chosen, what beat it, and what would reopen it.

## 2026-10-04 — Build for a friend = a Japanese learner's practice partner

**Chose:** a conversation-practice partner for one friend learning Japanese.
**Rejected:** a second recipe/voice project — the sibling repo `kitchen-memoir`
already plans that one, and it needs `whisper.cpp`, which is not on this machine.
**Reopens when:** the friend stops being the person, or the learner wants reading
drills instead of scenes.

## 2026-10-04 — `llama.cpp` only, no Ollama

**Chose:** `llama-server` / `llama-cli` straight from the llama.cpp binaries.
**Rejected:** Ollama. The user's machine is already RAM- and GPU-bound by the
Strata server; Ollama adds a second runtime and a model registry to keep
current, and it hides the sampling parameters the coach needs.
**Note:** the user offered to download Ollama. Downloading llama.cpp's own
prebuilt binaries is the same download with one less layer, so that is what the
scripts fetch.
**Reopens when:** a user has no way to run a binary — then a remote OpenAI-compatible
endpoint is one config line away (`base_url`), and that is the honest escape hatch.

## 2026-10-04 — Two engine modes: resident server, one-shot CLI

**Chose:** `mode = "server"` (fast path) and `mode = "cli"` (nothing resident).
**Because:** the machine cannot hold Strata and a second resident model at once.
`llama-cli` reloads per call, so the session pays time instead of RAM.
**Rejected:** a persistent in-process engine — that is the server mode, and it
would have been the only mode on a machine with headroom.
**Reopens when:** measured `cli` cost per turn is unacceptable; then batch the
coach call into the partner call, or keep the server and close Strata.

## 2026-10-04 — Gemma-3-4B-it Q4_K_M

**Chose:** Gemma 3 4B, Q4_K_M (~2.6 GB), served locally.
**Rejected:** the Strata Qwen shards already on disk — they are a coding model,
and a coding model in a role-play loop is worse at register than any 4B instruct
model. Rejected a 12B Gemma: it does not fit next to Strata.
**Bonus:** Gemma is a featured prize category, and this is a legitimate use of it,
not a bolt-on.
**Reopens when:** the friend's language needs more than 4B to be understood at all
— then the config takes any GGUF and the measurement goes in `docs/research/`.

## 2026-10-04 — Two model calls per turn: partner and coach

**Chose:** one call plays the person, a second reads the learner and reports.
**Rejected:** one call that plays and corrects at once — the partner starts
correcting in-character, the friend stops being the conversation, and the whole
point of a patient partner is lost.
**Rejected:** a correction *model* — a grammar checker would be more accurate and
would not know this learner. The coach's prompt carries the watch list built from
this learner's own turns.
**Reopens when:** the coach's `kind` labels prove useless on 4B; then drop the
labels and keep the fix.

## 2026-10-04 — JSON-schema constrained output, not "answer in JSON"

**Chose:** llama.cpp's `response_format` grammar path, with a loose parser and a
hard error when the grammar is ignored.
**Rejected:** prompt-and-hope JSON. A partner line that fails to parse silently
becomes a wrong scene; a coach that fails to parse silently becomes a wrong
correction handed to a friend.
**Reopens when:** a build of llama.cpp ignores `response_format` — `parse_json_loose`
raises `EngineError` naming exactly that, and `doctor` reports it.

## 2026-10-04 — sqlite, not a vector store, not MongoDB

**Chose:** three sqlite tables: turns, cards, sessions.
**Rejected:** embeddings/vector memory — the memory here is *counts of what this
learner keeps doing*, which is a tally, not a similarity search. The sibling
`kitchen-memoir` plan reached the same conclusion for the same reason.
**Reopens when:** the deck grows past a few thousand cards and needs search.

## 2026-10-04 — SM-2 lite, not FSRS

**Chose:** the small SM-2 variant in `memory.grade` (ease capped at 1.3, four
ratings, lapse cap at half the interval).
**Rejected:** FSRS — it wants ~1000 reviews per card to fit its weights, and this
deck is one friend's dozen sessions. A fitted model on 40 data points is a
confabulation.
**Reopens when:** the deck has enough reviews to fit anything.

## 2026-10-04 — The friend's name is a placeholder

**Chose:** `config/learner.toml` ships `name = "REPLACE-WITH-FRIEND-NAME"`.
**Because:** inventing a name for a real person in a public post is a lie, and a
placeholder is honest. The README says to swap it before the post.
**Reopens when:** the real friend agrees to be named in public.

## 2026-10-04 — `data/` is gitignored

**Chose:** turns, cards and timings live in `data/`, ignored by git.
**Because:** those turns name who the friend works with, where they go, and what
they are doing. A public repo must not be able to carry them.
**Reopens when:** a user wants a published demo memory — then it is a fixture,
written by hand, not a real learner's turns.

## 2026-10-04 — Windows console is a first-class concern

**Chose:** `console.utf8_console()` called by every entry point.
**Because:** default Python on Windows writes cp1252; a Japanese turn or a ✓
crashed `print`. This is the friend's machine, so it is not a footnote.
**Rejected:** non-ASCII-only output with no guard — that is what broke the tests.

## 2026-10-04 — One sqlite handle per db path

**Chose:** `_HANDLES` cache in `memory.connect`.
**Because:** Windows raised `sqlite3.OperationalError: database is locked` when
two handles to the same file were open at once, and every verb here opens the
file.
**Rejected:** closing per command — the cache is one line and cannot leak a handle.

## 2026-10-04 — Tests run against the mock engine

**Chose:** `tests/test_pipeline.py` drives the whole loop with `mode = "mock"`.
**Because:** the test proves the *pipeline* — partner → learner → coach → memory →
deck → report — and must not need 2.6 GB of weights or a GPU to do it.
**Rejected:** no tests. A scene that records nothing looks identical to a scene
that recorded everything, and that is the whole bug surface here.
**Reopens when:** M3 adds a transcript fixture from the *real* model, so the mock
never becomes the only witness.

## 2026-10-04 — One retry at temp 0, then skip the turn

**Chose:** `session._call` asks the model twice, cold the second time, and if
that also fails the turn is saved without a grade instead of ending the run.
**Because:** measured on the real model — the coach call on turn 2 of the cafe
scene emitted 320 tokens of prose and `parse_json_loose` raised
`ENGINE: model did not return JSON`. A 4B model does not respect the shape
every time, and a session that dies on turn 2 records less than a session that
limps to turn 5.
**Rejected:** raising on the first failure — the demo recorder would have
written a tape with one turn in it and the post would have looked like a demo
of a working tool.

## 2026-10-04 — Coach budget 320 → 512 tokens

**Chose:** `max_tokens = 512` for the coach call, 160 for the partner.
**Because:** the coach payload is three errors plus `better` plus `nudge`, and
in Japanese with romaji glosses that overflows 320. The failing call above hit
the cap exactly (`n_gen = 320` in the server log).
**Rejected:** truncating the JSON — a half payload is what `parse_json_loose`
would then reject anyway, and the failure would look like a parse bug instead
of a budget bug.

## 2026-10-04 — Dedupe coach errors by the said-span

**Chose:** a `seen_spans` set in `practice` keyed on `said.strip().lower()`.
**Because:** the real run returned the same correction twice in one report
("`Arigatsumikabushi!` → Thank you very much!" and "`Arigatsumikabushi!` →
Thank you!"), and every one of those becomes a card in the deck. The SRS would
have shown the same card twice in one review.

## 2026-10-04 — RAM read from `systeminfo`, not ctypes

**Chose:** `record_demo.ram_mib()` shells out to `systeminfo` and parses the two
labelled lines; `--ram-total/--ram-free` override it.
**Because:** `ctypes` in this Python 3.13 build has no `windos…` handle
(`dir(ctypes)` → only `windll`), and `windll.ntdll.GetSystemInfo` raises
`function 'GetSystemInfo' not found`. A slow read that is right beats a fast
read that is missing, and the RAM number is the one number the whole speed
claim depends on.

## 2026-10-04 — Two speeds, one machine, both true

**Chose:** the evidence file prints the RAM at the moment of the run and says
what it does not prove.
**Because:** the same model on the same box measured **101–115 tok/s** with the
GPU while memory was free, and **1.9 tok/s** (829.7 s for a 5-turn session,
1566 completion tokens) while the Strata server was holding the RAM and llama
was paging against `C:\pagefile.sys`. Quoting either number alone would be a
lie about the machine.
**Rejected:** a clean-machine-only benchmark — the friend's machine is this
machine, and the honest claim is a range with the cause named.

## 2026-10-04 — The coach is a nudge, not a teacher

**Chose:** the coach's `why` is shown as a nudge and the cards are labelled as
the learner's own weak spots, not as corrections to study.
**Because:** the real run invented Japanese facts — it called `mado` "a type of
bread" and told the learner `'Sato'` was English instead of Japanese. A 4B
model is confident and wrong about the very thing it is supposed to be an
authority on. The one thing it gets right every time is *where* the learner
struggled, which is what the deck and the hand-over sheet actually use.
**Reopens when:** a bigger model or a lookup table (jisho/KanjiGo) backs the
`fix` field. Until then the sheet says "this is what to practise", never
"this is the rule".
