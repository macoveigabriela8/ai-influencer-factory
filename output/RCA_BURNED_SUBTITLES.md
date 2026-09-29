# RCA — kling burns subtitles into the pixels (2026-08-11, reel 24)

Cost of this incident: **~880 credits (~$4.40)** in two dead renders, on top of
~880 credits lost the same day to two process errors of mine (a foreground shell
timeout, and submitting before the script was locked).

## What happened

Reel 24 was rendered twice on `kling/ai-avatar-standard`. Both takes came back
with text burned into the frame — fake-Chinese glyphs on roll 1, gibberish Latin
("Arang Tatirenre afrenoifia") on roll 2. Reel 25, same engine, same session,
same motion prompt, same settings, came back clean on the first roll.

## Evidence

| | reel 24 roll 1 | reel 24 roll 2 | reel 25 |
|---|---|---|---|
| anchor | a17_hall_floor_lamp | a17_hall_floor_lamp | a18b_low_table_v2 |
| audio | TTS render A | **TTS render B (fresh)** | its own |
| result | fake-Chinese | gibberish Latin | **clean** |
| text position | same baseline, same left margin | same baseline, same left margin | — |
| persistence | every frame | every frame | — |

Four measurements that constrain the cause:

1. **The two failures placed text at the identical baseline and left margin**,
   despite different glyph systems. New noise, same layout.
2. **A fresh TTS waveform did not fix it.** That was the documented remedy
   ("the seed follows the audio file"), applied correctly, and it failed.
3. **The anchor carries no latent text.** Verified on a brightened, stretched
   crop of a17's lower third — clean.
4. **The text was persistent, not intermittent** — unlike the 2026-08-07 batch,
   where it flickered. So a single-frame check would have caught this one, but
   the edge-density gate would not: persistent text reads as uniform density.

## Root cause (working hypothesis, consistent with all observations)

**An empty, low-detail lower third is read by the model as the region where
subtitles belong.** kling trained on enormous quantities of subtitled video, in
which that band is characteristically flat and dark. Given a matching input it
reproduces the pattern it learned, inventing glyphs to fill it.

- a17: a wide flat expanse of maroon robe over bare floor. Measured band detail
  **0.0102**. Failed 2/2.
- a18b: a wooden table with an open book and a lit candle occupying that band.
  Measured detail **0.0280**. Clean 1/1.

## Why the previous rule was wrong

The 2026-08-08 note concluded the seed follows the audio file. That inference
came from a batch in which the anchor and the audio co-varied — every re-roll of
a failing script reused both — so the two hypotheses were confounded and the
evidence could not separate them. Reel 24 broke the confound by holding the
anchor fixed and changing only the audio, and the failure survived.

**Lesson beyond this bug:** when a remedy is inferred from a batch, check
whether the variable it names was ever varied independently. If it wasn't, the
rule is a guess wearing the clothes of a measurement — and this project pays
~440 credits every time one of those is trusted.

## What is now in place

1. **`scripts/anchor_check.py`** — measures edge density and luminance spread in
   the subtitle band of an anchor **still** and refuses a flat one. Runs on the
   4-credit image, not the ~440-credit video. Calibrated on a17/a18b; every new
   render appends to the table in the file.
2. **Compose anchors so the lower third is occupied** — a table, an altar step,
   a prop, a light source. A bare lap over bare floor is high-risk by default.
3. **The lower-frame prompt line stays positive** ("a low altar step fills the
   bottom of the frame, carved wood, a butter lamp and a folded cloth on it").
   Negations get generated.
4. **Eyeball frames, always.** Persistent burned text defeats the density gate
   by looking uniform. The independent deep-QA agent reads contact sheets.
5. **Keep every failed take.** It is already billed and it is the only evidence
   of why it failed. Both reel-24 takes are retained.

## Test result — 2026-08-11, same day

Reel 24 was re-rendered on **a20b_bright_hall_neutral** (detail **0.0475**, the
busiest lower third we have built) with the identical script, engine and audio.
**Clean.** Independent deep-QA scanned 265 frames at 5fps over the whole frame:
lower-third edge density 0.1635-0.1744, a 1.0% spread across the entire take —
flat, which is the mandala texture, and contrast-stretched zooms at 3s/22s/48s
found no faint or latent glyphs. Top band 0.0000, no watermark.

Four data points now, one from outside our own pipeline:

| anchor | band detail | burned text |
|---|---|---|
| a17_hall_floor_lamp | 0.0102 | YES, 2/2 |
| a18b_low_table_v2 | 0.0280 | no |
| a20b_bright_hall_neutral | 0.0475 | no (2 independent renders) |
| yangmunus DVLvl_AgLb1 (his real reel, 228k) | 0.0671 | no |

The composition rule is confirmed to the extent four observations can confirm
anything: **treat it as a working rule, keep `anchor_check.py` in the render
path, and append every future render to this table.** It is not proof, and the
first clean render on a flat band would falsify it.

a19_hall_altar_step (detail 0.0322) was built as the first test candidate and
superseded by a20b before rendering; it remains unrendered and available.

## Unrelated defect found in the same render — see it as a separate lesson

The same take FAILED deep-QA on hand anatomy: 4.0-16.0s, the raised right hand
is a fused mitten with no separable fingers, no thumb and no wrist, sprouting
directly from the robe. Cause is not the anchor — it is the motion prompt,
rewritten that day to ask for occasional hand gestures after the user found the
previous reel too static. Both hands are clean for the other 37 seconds, exactly
where no gesture was commanded. **kling renders still hands correctly and
gestured hands badly; the liveliness has a price and this is it.** Recorded here
because the two changes shipped in one render and a later reader would otherwise
attribute the hand defect to the anchor change.
