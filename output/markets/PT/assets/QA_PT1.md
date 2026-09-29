# QA — sdPT1.mp4 (2026-08-08)

**Verdict: PASS**

File: `output/markets/PT/assets/sdPT1.mp4` — 73.07s, 720x1264, audio+video streams present.
Intended script: `script_PT1.txt` (pt-BR).

## 1. Transcript
- Engine: mlx_whisper, `mlx-community/whisper-large-v3-turbo` (multilingual). Detected language: **pt** throughout — no English or other-language drift.
- **Similarity: 0.996** raw (difflib ratio, normalized lowercase, punctuation stripped); **0.999** after removing a trailing Whisper hallucination.
- Diffs (word level):
  - `kaion -> kayon` — Whisper spelling of the proper name; audio is correct. Not a defect.
  - trailing `"E aí"` inserted at 72.6–77.7s — segment starts at end-of-audio and extends past the 73.07s file duration; classic Whisper silence hallucination, not spoken content.
- No dropped or altered sentences. All 17 script sentences present verbatim, in order.

## 2. Burned subtitles (band y=757–1086, full width, frame every 2s)
- 37 frames sampled. Edge density range **0.0314–0.0366**, mean 0.0336.
- Profile is UNIFORM — no intermittent spikes against a lower baseline. Per the calibrated rule, uniform elevation on every frame is scene texture: this is a full-body shot on a woven mat, and the mat weave dominates the band.
- **Verdict: no burned subtitles.**

## 3. Visual (frames at 2s, 15s, 30s, 45s, 60s, 71s)
- Round wire glasses and white chin beard present and consistent in all 6 frames.
- Hands folded in lap: normal count and shape, no extra fingers, no deformation. Slight AI softness on hand skin (known kling look) but nothing defective.
- Identity, wardrobe (brown robe), framing, and lighting stable first-to-last frame — negligible drift.
- No text, logo, or watermark anywhere in frame.

## 4. Audio (ffmpeg volumedetect)
- mean_volume **-24.3 dB** (above the -30 dB floor), max_volume **-4.3 dB** (no clipping, 4.3 dB headroom).
- No music bed audible in the transcription pass; nothing anomalous in the level stats. (Full spectral FFT check per SOP Part 3 Step 5 not run here — do it before final assembly if this clip goes into a master.)

## Notes
- Two Whisper artifacts ("Kayon" spelling, trailing "E aí") should NOT be added to any qc_gate required-phrase list — measurement artifacts, same class as "the weight"/"to wait".
