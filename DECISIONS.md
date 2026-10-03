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
