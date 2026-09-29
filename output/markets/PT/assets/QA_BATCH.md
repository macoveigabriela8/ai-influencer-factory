# QA — sdPT2–sdPT10 batch (2026-08-08)

Method identical to `QA_PT1.md`: mlx_whisper `mlx-community/whisper-large-v3-turbo` (multilingual),
difflib similarity vs `source/scripts_PT.json` (normalized), subtitle band scan (frame every 2s,
crop 720x329 @ y=757, FIND_EDGES, threshold 60), 4-frame visual pass, ffmpeg volumedetect.

## Verdict table

| id | dur (s) | similarity | lang | subtitle scan | visual | audio mean/max (dB) | verdict |
|---|---|---|---|---|---|---|---|
| PT2 | 80.8 | 0.978 | pt | densities uniform 0.041–0.045 (masked) — **burned fake-Chinese text visible in 3/4 frames** | glasses+beard OK, hands OK — but burned text on screen | -22.8 / -3.8 | **FAIL** |
| PT3 | 79.5 | 0.981 | pt | 0.016–0.019 uniform, clean | clean (garden, full body) | -22.6 / -4.1 | PASS |
| PT4 | 79.5 | 0.991 | pt | 0.005–0.007 uniform, clean | clean (tea table) | -23.5 / -3.9 | PASS |
| PT5 | 76.0 | 0.980 | pt | 0.013–0.029 uniform (shawl/stone texture), clean | clean (fog forest, grey shawl) | -23.0 / -4.1 | PASS |
| PT6 | 70.9 | 0.989 | pt | drift 0.010→0.047 = grass/path texture, no text in inspected bands | clean (field path, mala beads); feet normal | -22.8 / -4.9 | PASS |
| PT7 | 75.2 | 0.999 | pt | 0.001–0.004 uniform, clean | clean (candle, dark room) | -23.1 / -4.7 | PASS |
| PT8 | 78.7 | 0.985 | pt | **intermittent spikes 0.046–0.050 vs 0.031 baseline at frames 11–12, 14–15, 32–33 — burned fake-Chinese subtitles confirmed on frame inspection** | glasses+beard OK otherwise | -23.8 / -4.7 | **FAIL** |
| PT9 | 78.7 | 0.999 | pt | densities 0.023–0.043, near-persistent — **TWO-LINE burned text (fake-Chinese + gibberish Latin "Houhna IdoHos lo 4 Ims") in 3/4 frames** | glasses+beard OK otherwise | -23.8 / -4.1 | **FAIL** |
| PT10 | 84.8 | 0.993 | pt | 0.005–0.006 uniform, clean | clean (tea table) | -23.3 / -5.2 | PASS |

## 1. Transcripts

All nine detected as **pt** throughout — no English/Japanese/other drift, no dropped or altered
sentences, no CTA stripping. Every diff is a Whisper measurement artifact, not a defect:

- `kaion → kayon / caion` (all nine) — proper-name spelling.
- `catorze → 14` (PT8 ×3), `um/dois/três → 1/2/3` (PT10) — digit normalization.
- PT2 `casa → sabiracasa` — Whisper word-merge of "sabia? … casa"; audio correct.
- PT3 `de → e`, PT6 `a → da` — single-function-word transcription slips at 0.98+ similarity.
- PT4 and PT6: trailing `tchau para mais` segments start AT/after audio end (86.8s vs 79.5s file;
  78.5s vs 70.9s file) — classic end-of-audio hallucination. The real "Siga para mais." close is
  present in both.

## 2. Burned subtitles — 3 FAILURES, and a lesson

PT8 shows the calibrated intermittent-spike signature and was caught by the scan.
**PT2 and PT9 were NOT flagged by the density rule** — their burned text is near-persistent, so
the profile reads as "uniform elevated baseline", the pattern the rule classifies as scene
texture. They were caught only in the visual frame pass.

⚠️ Lesson for `qc_gate.py`: uniform-high is NOT automatically scene texture. A uniform band
above ~0.03 needs one frame actually eyeballed (or an OCR/stroke-shape check) before clearing.

Failure detail:
- **PT2** (`sdPT2.mp4`): one line of pale fake-Chinese glyphs, lower band (~y 940–990), present
  most of the video (visible at 10%, 37%, 90% marks; absent at 63%).
- **PT8** (`sdPT8.mp4`): one line of fake-Chinese glyphs flickering in/out (~20–30s and ~62–66s).
- **PT9** (`sdPT9.mp4`): two stacked lines — fake-Chinese over gibberish-Latin — burned in for
  most of the runtime.

## 3. Visual

Glasses (round wire) + white chin beard present and consistent in all 36 sampled frames across
all nine videos. Hands normal (folded, teapot, mala beads) — no extra fingers or morphing. No
watermarks or logos. Scenes: PT2/PT9 window room, PT3 garden, PT4/PT10 tea table, PT5 fog
forest with grey shawl, PT6 field path, PT7 candle room, PT8 tatami room. Identity stable
within each video. Aside from the burned text on PT2/PT8/PT9, no visual defects.

## 4. Audio

All nine within spec: mean −22.6 to −23.8 dB (floor −30, ceiling −12), max −3.8 to −5.2 dB
(no clipping, ≥3.8 dB headroom). Full spectral FFT bed-check per SOP Part 3 Step 5 not run here —
run before final assembly.

## Action

Re-roll **PT2, PT8, PT9** (burned-subtitle defect, same class as the reels 12–20 kling batch).
PT3, PT4, PT5, PT6, PT7, PT10 are clean and ready for assembly.

## Rerolls (2026-08-08) — sdPT2 / sdPT8 / sdPT9, second generation

Same method: whisper-large-v3-turbo vs `scripts_PT.json`, density scan (frame/2s, 720x329 @ y=757,
FIND_EDGES>60), mandatory frame inspection (7–10 frames each, incl. all density spikes), volumedetect.

| id | dur (s) | similarity | lang | subtitle scan | visual | audio mean/max (dB) | verdict |
|---|---|---|---|---|---|---|---|
| PT2 (reroll) | 80.8 | 0.978 | pt | uniform 0.041–0.047 (masked) — **TWO lines of white fake-Chinese burned in ALL 7/7 inspected frames, persistent whole runtime** | glasses+beard OK, hands OK, no watermark | -22.8 / -3.8 | **FAIL** |
| PT8 (reroll) | 78.7 | 0.985 | pt | baseline 0.031–0.036 with spikes 0.046–0.056 at frames 6–7, 23–24, 29, 31–32 — **fake-Chinese line confirmed on every spike frame (~12–14s, 46–48s, 58s, 62–66s), varying text** | glasses+beard OK, hands OK, no watermark | -23.8 / -4.7 | **FAIL** |
| PT9 (reroll) | 78.7 | 0.999 | pt | near-uniform 0.039–0.044 (masked; brief dip 0.024 @ 46–48s) — **two stacked lines (fake-Chinese over gibberish Latin \"d to Hno IdoHos lo 4 Ims\") in 7/8 inspected frames** | glasses+beard OK, hands OK, no watermark | -23.8 / -4.1 | **FAIL** |

Transcripts: all three pt throughout, no dropped sentences, CTAs intact. Only known Whisper
artifacts (kaion→Kayon; catorze→14 in PT8; PT2 word-merge "sabiracasa" for "sabia?…casa").
Audio in bounds.

**All three rerolls FAIL on the same burned-subtitle defect as their first generations — 0/3
yield.** PT2 and PT9 are again "uniform elevated" profiles the density rule alone would clear;
the frame inspection caught them, confirming the earlier lesson. PT9's gibberish-Latin line is
near-identical in shape to its first generation ("Houhna IdoHos lo 4 Ims" vs "d to Hno IdoHos lo
4 Ims"), and PT2's text is persistent across the full runtime — the defect appears anchored to
these prompts/seeds, not random. **Do not re-roll blind a third time**: change something (new
seed/prompt phrasing describing a clean plain wall, different anchor crop, or negative-space
reframe) before spending again.

## Round 3 (2026-08-08) — sdPT2 / sdPT8 / sdPT9, third generation

Method: mlx_whisper large-v3-turbo (language=pt) vs `scripts_PT.json` (difflib, normalized);
frame extraction fps=0.5 (every 2s, full runtime), lower band crop 720x400 @ y=757, **every
extracted frame visually inspected** (40 + 39 + 39 frames = 118 total, no density shortcut).

| id | similarity | subtitle verdict | verdict |
|---|---|---|---|
| PT2 | 0.978 | **Burned two-line fake-Chinese text in 40/40 frames (t=0–78s, fully persistent), same layout as gen 1–2** | **FAIL** |
| PT8 | 0.985 | **Intermittent fake-Chinese lines at t≈12–14s, 46–48s, 58s, 62–64s (frames 7–8, 24–25, 30, 32–33); text varies per burst; other 32 frames clean — same timestamps as gen 2** | **FAIL** |
| PT9 | 0.999 | **Two stacked lines (fake-Chinese over gibberish Latin "d to Hno IdoHos lo 4 Ims") in 37/39 frames; absent only t≈46–48s — same Latin string as gens 1–2** | **FAIL** |

Transcripts all pass (pt throughout, only known Whisper artifacts: kaion→Kayon, catorze→14,
PT2 "sabiracasa" word-merge). The defect is exclusively the burned text.

**0/3 yield for the THIRD consecutive generation — 9 renders on these three scripts, 9 fails.**
The defect is provably deterministic: PT9's gibberish-Latin string is byte-for-byte the same
phrase across all three generations, and PT8's bursts land at the same timestamps. Re-rolling
with the same inputs is spending money on the same output. Before any further spend, change an
actual input: different anchor image (new crop/scene with clean negative space in the y≈757–1160
band), rephrased prompt describing the empty lower frame ("bare wooden floor fills the lower
third"), or a different engine for these three scripts. Consider also framing the anchor so the
subtitle band is floor-only — PT2/PT9's text sits over the robe, PT8's over the mat.

## Round 4 (2026-08-08, fresh TTS)

| clip | transcript sim | subtitle gate | verdict |
|---|---|---|---|
| sdPT2 | 0.9782 | clean — all 40 frames (0-80s), band shows only shawl/robe | PASS |
| sdPT8 | 0.9847 | clean — all 39 frames (0-78s), band shows table/teapot/hands | PASS |
| sdPT9 | 0.9990 | FAIL — persistent gibberish-Latin burned text ("S ənmsıtom", pale serif with drop shadow, Samsung-watermark-like) centered in band, present in EVERY frame from 0s to 78s | FAIL — re-roll |

Notes: PT9 text is PERSISTENT (uniform-density signature) — confirms the 2026-08-08
QA blind-spot rule: only frame inspection catches it, density heuristics read it as
texture. Whisper (mlx large-v3-turbo, pt) run in-process; similarity = SequenceMatcher
on lowercased, punctuation-stripped text.

## Round 5 (2026-08-08, PT9 candle_dark anchor)

- **sdPT9.mp4** — **PASS**
  - Transcript: similarity **0.999** (mlx whisper-large-v3-turbo, pt). Verbatim; only differences are punctuation/comma placement and "Kayon" for "Kaion" (name spelling, measurement artifact). Comment keyword "sim", "Mestre Kaion" and "Siga para mais" all present and spoken.
  - Burned subtitles: **CLEAN** — 39/39 frames inspected by eye (fps=0.5, full 78.7s, crop y757–1160, brightness +0.15 for the dark candle-lit scene). No text-like glyphs at any timestamp (0s–78s). Only hands, robe folds, floorboards and the candle in the band.

## Caption gate (2026-08-08, script-aligned rebuild)

Method: cue-file word diff vs scripts_PT.json (every cue word present in script, no repeated-letter junk, name spelling), then 1fps caption-band extraction (crop 1080x500 @ y=1200) and full contact-sheet read of every frame, all 10 reels.

| reel | cue diff | visual read | verdict |
|---|---|---|---|
| PT1 | clean | all cards match script, accents correct, 1-2 rows, inside box | PASS |
| PT2 | clean | clean end to end | PASS |
| PT3 | clean | clean end to end | PASS |
| PT4 | clean | clean; 3-row-looking cards are 2 rows, inside box | PASS |
| PT5 | clean | **all three prior defects fixed**: 49-55s "saude sao exatamente..." card fits box, no overflow; ~72s reads "Eu sou o Mestre Kaion." (not "Kayon"); no hallucinated "E assim ficou?" card at ~75s | PASS |
| PT6 | clean | clean end to end | PASS |
| PT7 | clean | clean end to end | PASS |
| PT8 | clean | clean; widest card ("corpo pede para lembrar quem ele e.") stays inside box | PASS |
| PT9 | clean | clean end to end | PASS |
| PT10 | clean | clean end to end | PASS |

Notes: "Kaion" spelled correctly in every closing card (10/10). No text touches frame edges or exceeds the black box anywhere. No junk/hallucinated cards. Batch: 10/10 PASS.

## FINAL CERTIFICATION (2026-08-08)

Adversarial 6-point gate on reel_PT1_dry..reel_PT10_dry. Full-frame fps=1 contact sheets read end to end for every reel; caption cards read on every card; mlx whisper-large-v3-turbo transcription vs scripts_PT.json with word-level diff; cue files diffed against scripts; silencedetect -35dB/1.5s; volumedetect; A/V stream duration compare; 6 face crops per reel (4 speech, 2 tail); anchors cross-checked vs anchors/BANK_SHEET.png (incl. overrides PT2/PT5=a5, PT8=a4, PT9=a7).

| reel | frames | captions | audio/transcript | lip/timing/identity | verdict |
|---|---|---|---|---|---|
| PT1 | clean | clean, cues 1.000 | sim 0.991 (Whisper "Kayon"+tail hallucination only) | clean | PASS |
| PT2 | clean (shawl closed all frames) | clean, cues 1.000 | **GARBLED WORD at ~69.1-69.9s: "transforma a casa" is spoken as "transforma a SABIRA-casa"** — reproduced in 3 independent Whisper decodes on 2 different slices; extra syllables are in the audio, not a transcription artifact | clean | **FAIL (audio)** |
| PT3 | clean | clean, cues 1.000 | sim 0.989 (de/e + Kayon = Whisper artifacts) | clean | PASS |
| PT4 | clean, props stable | clean, cues 1.000 | sim 0.983; trailing "obrigado x4" verified as Whisper hallucination (tail re-transcribes clean, tail RMS -43dB) | clean | PASS |
| PT5 | clean — NO shawl morph at 7/17/37/42/56/62s or anywhere; slow zoom-out drift only (cosmetic) | clean, cues 1.000 | 0.612 raw is tail-hallucination ("crushed" loop) — slice re-transcribes clean; real diff only Kayon | clean | PASS |
| PT6 | clean, mala beads stable | clean, cues 1.000 | sim 0.979 (da/a + Kayon + echo of close = artifacts) | clean | PASS |
| PT7 | clean; candle flame verified continuously lit (YMAX 234-249 every second — earlier "vanish" was a crop artifact) | clean, cues 1.000 | sim 0.995 | clean | PASS |
| PT8 | clean | clean, cues 1.000 | sim 0.978 ("14"=catorze, Whisper normalization) | clean | PASS |
| PT9 | clean | clean, cues 1.000 | sim 0.995 | clean | PASS |
| PT10 | clean | clean, cues 1.000 | sim 0.978 (digits = Whisper normalization) | clean | PASS |

Common measurements: A/V duration mismatch 0.024-0.197s (all under 0.35s); no silencedetect hits anywhere (no mid-speech gaps >1.5s, no dead air at head/tail); mean volume -22.7 to -24.3dB, max -3.8 to -5.2dB (consistent); speech ends 0.06-0.66s before video end, no mid-word cuts, all reels end on "Siga para mais."; caption font size consistent within every reel, 1-2 rows, no edge contact; "Kaion" correct in all cues and cards; identity/glasses/beard/wardrobe consistent within each reel and vs its anchor.

Defect evidence: qa scratchpad evidence/PT2_sabiracasa_67.3-70.8s.wav (slice; word occupies 7.14-7.88s of the slice = ~69.1-69.9s absolute).

Unconfirmed suspicions (not blocking): PT5 gradual zoom-out over the reel (kling drift, reads as slow push-out, user may or may not care); PT1 Whisper emitted a long "fsfs..." string on the final ~0.1s — tail audio is low-level room tone, judged hallucination.

**CERTIFIED: NO — 9/10 pass. PT2 fails on a spoken-audio garble ("Sabira" inserted before "casa" at ~69.5s). Fix path per house rules: fresh ElevenLabs render of the PT2 script (never resubmit the same audio), re-roll, re-gate. Everything else is ship-ready.**

## PT2 round 5 certification (2026-08-08)

Adversarial 6-point gate on `output/markets/PT/reels/reel_PT2_dry.mp4` (1080x1920, 80.83s).

| # | Category | Verdict | Evidence |
|---|---|---|---|
| 1 | Full-frame sweep (fps=1, 81 frames) | PASS | No burned fake-Chinese/gibberish subtitles anywhere, no watermarks. Hands remain under the closed shawl for the entire reel (no morphing through fabric). Wardrobe/setting stable, no freezes. |
| 2 | Captions | PASS | cues_PT2.txt diffs clean vs scripts_PT.json PT2 (verbatim, all accents correct: cômodo, purificação, intenção, séculos). All cards ≤2 rows, consistent font size, no edge contact, "Kaion" spelled right. Cards present throughout speech; last card "Siga para mais." holds to end; no orphan cards. |
| 3 | Audio / transcript | **FAIL** | whisper-large-v3-turbo similarity 0.989, but **the round-4 garble is STILL PRESENT at ~69.1s**: "Não é o ritual que transforma a **Sabiracasa**" instead of "…transforma a casa". Confirmed twice — full-file pass AND an independent re-transcription of an extracted 65–73s slice ("…que transforma a Sabiracasa, é a intenção…"). The re-rendered TTS did not make it into this master (or the fix was not applied). Only other diff: kaion→kayon (normal Whisper phonetics, not a defect). silencedetect -35dB/1.5s: zero events. mean -22.8 dB / max -3.8 dB. A/V duration delta 0.074s (<0.35s). Clean start, clean 0.7s tail. |
| 4 | Lip sync | PASS | Mouth strips at 10/30/50/70s show active, varied articulation matching speech; tail silence strip (79.9s+) settles to closed mouth. |
| 5 | Timing | PASS | No dead air >1.5s, no frozen ends (subtle motion through final second), no mid-word cuts; cue timeline continuous 0.00–80.1s. |
| 6 | Identity vs anchor | PASS | Frames ~0s/~33s/~67s vs pt_a5_grey_shawl_mist.png: same face, round wire glasses, short white chin beard, grey closed shawl, misty forest. Mild kling softening mid/end, identity intact. |

**OVERALL: FAIL — do not ship.** Single blocking defect: the ~69s garbled word persists ("transforma a Sabira-casa"). Per the burned-subtitle/garble SOP: verify the fresh ElevenLabs render actually replaced the chunk audio in the assembly inputs, then re-roll ONLY that clip with the new waveform and reassemble. Visuals and captions are certifiable as-is.

## PT2 round 6 certification (2026-08-08)

File: output/markets/PT/reels/reel_PT2_dry.mp4 (80.83s video / 80.76s audio, 1080x1920). Adversarial gate, work dir qa_pt2_r6.

| # | Category | Verdict | Evidence |
|---|---|---|---|
| 1 | Full-frame sweep (fps=1, 3 sheets, all 81 frames) | PASS | No burned fake-Chinese/gibberish subtitles anywhere; single white-on-black caption card only. Hands stay inside the closed grey shawl for the whole take, no morphing; wardrobe/setting stable; no freezes. |
| 2 | Captions | **FAIL** | Card at ~66.9s reads "Não é o ritual que **transforma** a casa." — the round-6 reword ("muda a casa") is NOT in the video, NOT in cues_PT2.txt, and NOT in scripts_PT.json (still "transforma"). All other cards clean: correct PT accents, "Kaion" spelled right, ≤2 rows, consistent font, no edge contact, cue coverage matches speech ("Siga para mais." card holds ~0.6s past last word — acceptable close). |
| 3 | Audio (mlx whisper large-v3-turbo, pt) | **FAIL** | The 65–72s garble is STILL PRESENT. Isolated 64–73s slice transcribes: "Não é o ritual que transforma a **Sabiracasa**, é a intenção que transforma o ambiente." Full-pass similarity 0.989 with the same single defect (casa→sabiracasa; "Kayon" is a Whisper spelling artifact, not a defect). silencedetect -35dB/1.5s: zero hits. volumedetect mean -22.8 / max -3.8 dB. A/V delta 0.074s (<0.35). Clean start (first word 0.00s) and end (last word ends 80.22s). |
| 4 | Lip sync (4 speech + 2 silence crops) | PASS | Mouth articulating on all speech crops (5/25/45/68s), consistent with audio; no dead-face-while-speaking. |
| 5 | Timing | PASS | No frozen tail (fps=4 last 1.5s shows normal micro-motion), no dead air ≥1.5s, no mid-word cuts. |
| 6 | Identity vs anchor (pt_a5_grey_shawl_mist, start/mid/end) | PASS | Same face, glasses, beard, shawl, framing and mist across anchor and all three probes. |

**OVERALL: FAIL — do not ship.** Root cause: stale rebuild. The session's reword to "Não é o ritual que muda a casa." never propagated — scripts_PT.json (mtime Aug 8 07:33) still carries "transforma a casa", the cue sidecar matches the old text, and the delivered master contains the same reproducible TTS stumble ("Sabiracasa") as round 5. Fix path: update scripts_PT.json PT2 sentence, fresh ElevenLabs render of that chunk (never resubmit the same waveform per the burned-subtitle/TTS rule), regenerate video for that span, rebuild captions from new cues, re-run this gate.

## PT2 round 7 certification (2026-08-08)

File: output/markets/PT/reels/reel_PT2_dry.mp4 (1080x1920, 30fps, 80.83s video / 80.76s audio, A/V delta 74ms).

| # | Check | Verdict |
|---|---|---|
| 1 | Full-frame sweep (fps=1, 81 frames, all sheets read) | **PASS** — no burned fake-Chinese/gibberish subtitles anywhere; no hands ever emerge (arms fully under the closed shawl all take, no morph possible); one pose, misty-forest anchor scene held throughout |
| 2 | Caption band audit | **PASS** — every card matches cues_PT2.txt verbatim, cues match scripts_PT.json PT2 verbatim (JSON confirmed to contain "Não é o ritual que muda a casa."); consistent font/size/position, max 2 rows, no stray cards |
| 3 | Audio (mlx_whisper large-v3-turbo pt, word_timestamps) | **FAIL** — 67.58–69.88s speaks "Não é o ritual que **transforma a sabiracasa**" instead of "muda a casa". Independent 63–74s slice re-transcription confirms "Sabiracasa" — the round-6 garble is STILL PRESENT. Everything else is a word-perfect match to the script. silencedetect -35dB/1.5s: zero events; volumedetect mean -22.8 dB / max -3.8 dB (healthy) |
| 3b | Caption/audio agreement on reworded line | **FAIL** — caption correctly shows "muda a casa" while audio says the garble; visible-vs-audible mismatch on screen at 66.9–69.9s |
| 4 | Lip-sync crops (6 speech points incl. 67.5/69.4s) | PASS — mouth articulating at all sampled speech times, incl. inside the garble window |
| 5 | Timing | PASS — captions land on whisper word times (e.g. "Não" cue 66.90 = whisper 66.90); no dead air, ends 78.8s + tail |
| 6 | Identity vs anchor pt_a5_grey_shawl_mist.png | PASS — bald, round wire glasses, short white chin beard, closed grey shawl over brown robe, cobbled misty path; stable across the whole take |

**OVERALL: FAIL.** Sole blocker is the audio: the reworded line was fixed in script/cues/captions but the underlying TTS/render still carries the old garbled pronunciation ("transforma a sabiracasa") at 67.6–69.9s. Per the burned-subtitle/garble SOP: re-render the TTS for that line (fresh ElevenLabs waveform), re-roll the clip, do not resubmit the same audio. Do not ship this build.

## PT2 round 8 certification (2026-08-08)

File: output/markets/PT/reels/reel_PT2_dry.mp4 — 1080x1920, 30fps, 78.17s video / 77.60s audio.

| # | Check | Result |
|---|---|---|
| 0 | CRITICAL 63–74s re-transcription (isolated extract, large-v3-turbo pt) | **PASS** — "…harmonia, prosperidade, paz, não é o ritual que muda a casa, é a intenção que transforma o ambiente. Se fez sentido, comente a palavra lar." Verbatim, zero trace of "sabira"/"saizir"/any garble. The round-7 blocker is gone. |
| 1 | Full-frame sweep fps=1 (78 frames, 4 contact sheets, all read) | PASS — no burned fake-Chinese/gibberish text anywhere, no anatomy faults, shawl stable (no morphing), no freezes (freezedetect n=0.001 d=1.5: 0 events) |
| 2 | Caption audit (every band card vs cues_PT2.txt + script) | PASS — all 25 cue lines rendered verbatim; "Kaion" spelled correctly on both closing cards; 1–2 rows throughout, consistent size, no edge contact; caption text and audio agree on the reworded 65.4–70.3s lines |
| 3 | Audio (large-v3-turbo pt, word_timestamps) | PASS — similarity 0.9945 vs scripts_PT.json id PT2; sole word diff "Kaion→Kayon" (Whisper phonetic spelling, not a defect). silencedetect -35dB/1.5s: none. mean −22.9 dB / max −4.0 dB. |
| 4 | Lip sync (4 speech points 10.5/30.0/49.0/66.5s + 2 stills 5.0/77.5s) | PASS — clear frame-to-frame articulation at all 4 speech points incl. the critical 66.5s line; mouth closed and still at 77.5s tail |
| 5 | Timing / A-V | PASS — whisper segment starts match cues within ±0.02s on all 22 lines (e.g. cue 65.42 = whisper 65.42); last word ends 77.04s, 1.1s clean tail; A/V duration delta 0.57s (video pad, no drift) |
| 6 | Identity vs anchor pt_a5_grey_shawl_mist.png | PASS — same bald elderly man, round wire glasses, short white chin beard, closed grey shawl over brown robe, misty forest cobbled path, same camera distance; identity stable across the whole take |

**OVERALL: PASS.** Round 8 clears the round-7 garble; fresh TTS + fresh upload confirmed effective. Certified ready for user review.
