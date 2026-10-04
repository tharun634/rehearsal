# Café Aoi, morning rush — session transcript

| scene | engine | model | turns | corrections | scene cleared | wall clock | tokens (prompt/completion) |
|---|---|---|---|---|---|---|---|
| `cafe-aoi` | server | models/gemma-3-4b-it-Q4_K_M.gguf | 5 | 15 | no | 21.9 s | 4784 / 1858 |

## Turn 1
**Barista:** いらっしゃいませ！ 何かご注文されますか？
**learner:** Konnichiwa, sumisu no ogi, mado.

**coach:** they got across
- `Konnichiwa, sumisu no ogi, mado.` → `You used ‘sumisu’ instead of ‘suki’ for ‘like’.` (vocabulary) — The learner needs to remember the correct word for ‘like’ in this context.
- `Konnichiwa, sumisu no ogi, mado.` → `The word order is slightly off; it should be ‘sumisu no ogi o mado.’` (grammar) — The learner needs to correctly form the request for ‘a drink’ using the object marker ‘o’.
- `Konnichiwa, sumisu no ogi, mado.` → `It’s better to say ‘sumisu no ogi o onegaishimasu’ for a polite request.` (grammar) — Adding ‘onegaishimasu’ makes the request more polite and appropriate for a café setting.
**say instead:** Sumisu no ogi o onegaishimasu.
**coach nudge:** Could you please tell me what kind of drink you would like?
*scene moved on: greet*

## Turn 2
**Barista:** Sumimasen, omocha wa nan ka? (Excuse me, what kind of snacks do you have?)
**learner:** Katsu-men, please. Ah, one size large.

**coach:** they got across
- `Katsu-men, please. Ah, one size large.` → `You should specify the type of katsu-men you want, like 'tonkatsu-men' or 'katsudon-men'.` (vocabulary) — The learner didn't indicate the specific type of katsu-men, which is necessary for the order.
- `Ah, one size large.` → `It's better to say 'onegai shimasu' (please) before specifying the size.` (grammar) — Adding 'please' makes the request more polite and natural.
- `Ah, one size large.` → `Consider adding 'kudasai' (please) after the size to make it a complete request.` (grammar) — The phrase is incomplete and lacks a polite request particle.
**say instead:** Katsudon, onegai shimasu, one size large.
**coach nudge:** Could you tell me what kind of katsu-men you'd like to order?

## Turn 3
**Barista:** Kohi wa oishii desu ka? Matcha mo arimasu.
**learner:** Sato, mado.

**coach:** they got across
- `Sato, mado.` → `You need to use the correct particle for the object.` (particle) — The particle 'wa' is used for subjects, not objects, and 'mado' is the object of the sentence.
- `Sato, mado.` → `It's better to use 'o' before the noun.` (particle) — Using 'o' before the noun indicates that it is the object of the sentence.
- `Sato, mado.` → `Consider adding 'kudasai' to make it a polite request.` (grammar) — Adding 'kudasai' makes the request more polite and appropriate for ordering.
**say instead:** Sato o kudasai.
**coach nudge:** Try ordering your drink and food again, using the correct particles and a polite request.
*scene moved on: choose*

## Turn 4
**Barista:** Sumimasen, kofēi wa setto ga okurete imasu. Matcha wa ii desu ne? (Excuse me, we're out of espresso. Matcha is good, right?)
**learner:** Um, big size? Or "large"?

**coach:** they got across
- `Um, big size? Or "large"?` → `You should clarify the size you want, using the correct Japanese word for 'large'.` (vocabulary) — The learner is repeating a phrase and not using the appropriate size descriptor.
- `Um, big size?` → `It's better to use 'おおきい' (ookii) for 'large' instead of 'big size'.` (grammar) — The learner is mixing English and Japanese phrasing, and 'big size' isn't a natural way to express size in Japanese.
- `Or "large"` → `It's better to say 'おおきい' (ookii) for 'large' instead of using the English word in quotation marks.` (vocabulary) — (seen) This is a repetition of the previous error.
**say instead:** おおきい、お願いします。
**coach nudge:** Please specify the size you would like, for example, 'おおきいコーヒー、お願いします' (ookii ko-hi, onegaishimasu - large coffee, please).
*scene moved on: modify*

## Turn 5
**Barista:** Chotto matte, ōkii desu ka? 大きいですか？
**learner:** Arigatsumikabushi!

**coach:** they got across
- `Arigatsumikabushi!` → `Thank you very much!` (grammar) — The phrase 'Arigatsumikabushi' is a more formal and slightly redundant way to say 'thank you' in Japanese; a simpler 'Arigato' would be more natural here.
- `Arigatsumikabushi!` → `Thank you very much!` (word_order) — The word order is slightly off for a polite response; it should be 'Arigato gozaimasu'.
- `Arigatsumikabushi!` → `Thank you very much!` (grammar) — Adding 'gozaimasu' would make the expression more polite, which is appropriate for a café setting.
**say instead:** Arigato gozaimasu!
**coach nudge:** Could you please repeat your order, just to confirm everything is correct?
*scene moved on: size*
