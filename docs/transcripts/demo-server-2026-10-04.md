# Café Aoi, morning rush — session transcript

| scene | engine | model | turns | corrections | scene cleared | wall clock | tokens (prompt/completion) |
|---|---|---|---|---|---|---|---|
| `cafe-aoi` | server | models/gemma-3-4b-it-Q4_K_M.gguf | 5 | 15 | no | 22.3 s | 4749 / 1937 |

## Turn 1
**Barista:** Konnichiwa! Welcome to the café. What can I get for you today?
**learner:** Konnichiwa, sumisu no ogi, mado.

**coach:** they got across
- `Konnichiwa, sumisu no ogi, mado.` → `You said 'Konnichiwa, sumisu no ogi, mado.'` (word_order) — The phrase is correct, but the order of the elements is slightly off; it should be 'Sumisu no ogi o, mado onegaishimasu.'
- `Konnichiwa, sumisu no ogi, mado.` → `You said 'Konnichiwa, sumisu no ogi, mado.'` (particle) — The word 'o' is missing after 'sumisu no ogi', which is necessary to indicate that you are ordering it.
- `Konnichiwa, sumisu no ogi, mado.` → `You said 'Konnichiwa, sumisu no ogi, mado.'` (grammar) — Adding 'onegaishimasu' at the end would make the request more polite.
**say instead:** Sumisu no ogi o, mado onegaishimasu.
**coach nudge:** Could you please tell me what kind of coffee you'd like?
*scene moved on: greet*

## Turn 2
**Barista:** Otsukaresama desu.  Would you like a matcha latte and a melonpan?
**learner:** Katsu-men, please. Ah, one size large.

**coach:** they got across
- `Katsu-men, please. Ah, one size large.` → `You should specify the type of katsu-men you want, like 'tonkatsu-men' or 'katsudon-men'.` (vocabulary) — The learner used 'katsu-men' without specifying the type, which is a common mistake when ordering.
- `Ah, one size large.` → `It's better to say 'one size large, onegaishimasu' to be polite.` (grammar) — Adding 'onegaishimasu' makes the request more polite and standard for ordering food.
- `Ah, one size large.` → `You could also say 'one size large, onegaishimasu' for a more natural phrasing.` (grammar) — (seen) Adding 'onegaishimasu' is a good habit to form when requesting things.
**say instead:** Katsu-men, tonkatsu-men, onegaishimasu. One size large, onegaishimasu.
**coach nudge:** Please tell me what kind of katsu-men you would like to order.
*scene moved on: choose*

## Turn 3
**Barista:** Sumimasen, matcha latte wa oshimai desu. Ganbarimashita!
**learner:** Sato, mado.

**coach:** they got across
- `Sato, mado.` → `You need to use the correct phrase to request a receipt.` (grammar) — The phrase 'Sato, mado' doesn't convey the request for a receipt; you should use 'Katte, mado' instead.
- `Sato, mado.` → `You should use the polite form of 'please'.` (grammar) — Adding 'onegai shimasu' to the end of the phrase would make it more polite.
- `Sato, mado.` → `It's better to use 'onegai shimasu' after the item.` (grammar) — Placing 'onegai shimasu' after the item is more natural and grammatically correct.
**say instead:** Katte, mado, onegai shimasu.
**coach nudge:** Could you please tell me what you want to do with the receipt after you pay?
*scene moved on: size*

## Turn 4
**Barista:** Kore, matcha latte wa, mizu no kura, onegi shimasu ka?
**learner:** Um, big size? Or "large"?

**coach:** they got across
- `Um, big size? Or "large"?` → `You need to specify the size of the item you are ordering.` (vocabulary) — The learner used 'big size' which is not a standard way to request a size in Japanese; they should use 'onegi shimasu' with the size.
- `Um, big size? Or "large"?` → `It's better to use 'onegi shimasu' for requesting a size.` (grammar) — The learner is still struggling with the correct phrase structure for requesting a size.
- `Um, big size? Or "large"?` → `You could say 'onegi shimasu, onegai shimasu' for politeness.` (grammar) — (seen) Adding 'onegai shimasu' makes the request more polite.
**say instead:** Onegi shimasu, ichiban ookii onegai shimasu.
**coach nudge:** Could you please tell me what size you would like for the matcha latte?
*scene moved on: modify*

## Turn 5
**Barista:** Chotto, chotto.
**learner:** Arigatsumikabushi!

**coach:** they got across
- `Arigatsumikabushi!` → `Thank you very much!` (register) — The learner used an overly formal expression ('Arigatsumikabushi!') which isn't appropriate in this casual café setting; a simpler 'Arigato gozaimasu' would be better.
- `Arigatsumikabushi!` → `Thank you very much!` (word_order) — The learner repeated 'Arigatsumikabushi!' unnecessarily, adding extra formality.
- `Arigatsumikabushi!` → `Thank you very much!` (register) — The learner used 'Arigatsumikabushi!' which is a very polite and formal way to say thank you, and is not needed here.
**say instead:** Arigato gozaimasu!
**coach nudge:** Could you please tell me what you'd like to order next, or would you like me to repeat the options?
