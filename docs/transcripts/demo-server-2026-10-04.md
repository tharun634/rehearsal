# Café Aoi, morning rush — session transcript

| scene | engine | model | turns | corrections | scene cleared | wall clock | tokens (prompt/completion) |
|---|---|---|---|---|---|---|---|
| `cafe-aoi` | server | models/gemma-3-4b-it-Q4_K_M.gguf | 4 | 2 | no | 970.0 s | 2958 / 569 |

## Turn 1
**Barista:** Konnichiwa! Welcome to The Corner Cafe. What can I get for you today?
**learner:** Konnichiwa, sumisu no ogi, mado.

**coach:** they got across
- `Konnichiwa, sumisu no ogi, mado.` → `You said 'Konnichiwa, sumisu no ogi, mado.'` (word_order) — The word order is slightly off; it should be 'Sumisu no ogi, mado kudasai.'
**say instead:** Sumisu no ogi, mado kudasai.
**coach nudge:** Try rephrasing your request to include a polite request for the order.
*scene moved on: greet*

## Turn 2
**Barista:** Ah, a matcha latte! That's a good choice. We're actually out of the Hokkaido melon bread right now, sorry about that.
**learner:** Katsu-men, please. Ah, one size large.

**coach:** they did not get across
*scene moved on: choose*

## Turn 3
**Barista:** Okay, so just a large matcha latte and a katsu-men. Anything else for you today?
**learner:** Sato, mado.

**coach:** they got across
- `Sato, mado.` → `You need to use the correct particle for requests, 'o' instead of 'wo'.` (particle) — The particle 'wo' is used for stating something, not making a request.
**say instead:** Sato o onegaishimasu, mado.
**coach nudge:** Try requesting the item again, using the appropriate particle to indicate you want it.
*scene moved on: size*

## Turn 4
**Barista:** Hai, one more thing. Could I get a small side of miso soup, please?
**learner:** Um, big size? Or "large"?

**coach:** they did not get across
