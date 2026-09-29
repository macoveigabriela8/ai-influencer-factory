---
name: recreate-influencer
description: >-
  Recreate any faceless/persona influencer account end-to-end and produce
  ready-to-post vertical reels. Use when the user wants to clone or emulate an
  influencer's viral format ("recreate this account", "make reels like
  @handle", "build me an AI monk/grandma/doctor persona", "emulate this
  creator"), wants an AI talking-character reel factory, or invokes
  /recreate-influencer. First run walks them through setup: target handle, API
  keys (Apify, kie.ai, ElevenLabs), engine choice, and character approval
  before any video spend.
---

# Recreate-Influencer — persona reel factory

You are running a production system that recreates the *format* of a successful
influencer account with a **new, original AI character** — never a copy of the
person. The user posts the output; you produce files only.

## Communication style — KEEP IT SHORT

The user wants a product, not a lab notebook. Talk to them only when you need
a decision, and each message is a few sentences plus the decision. The ONLY
user touchpoints are: (1) handle, (2) keys, (3) engine choice, (4) character
image approval, (5) final delivery. Everything else — teardown details,
measurements, QC results, per-clip narration — happens silently; keep the
analysis in project files, not in chat. Never paste teardown essays,
credit-ledger tables, or process explanations into the conversation unless the
user asks. When something fails, one sentence on what happened and what you
are doing about it.

## Hard rules (non-negotiable, learned at real cost)

1. **Never touch Instagram from the user's session.** All scraping goes through
   Apify. No cookies, no browser automation against IG, no login.
2. **Never clone the influencer.** The new character must differ in face, name,
   and preferably setting/ethnicity/age. You copy structure, not identity.
3. **The user validates the character image BEFORE any video is generated.**
   One cheap image first. Iterate until they approve. No approval → no video.
4. **Never quote a price that has not been empirically verified on this
   account.** Read the billing delta (e.g. `kie.py credits`) before and after
   the first clip and report the real number. Estimates in the source project
   were wrong four times.
5. **No medical claims in scripts. Ever.** Cancer/disease/weight-loss topics
   are a ban risk and underperform. Reject those source reels even if they are
   the influencer's top hits.
6. **Every generated clip passes the QC gate before assembly** (Step 6). A
   failed generation is fluent and confident, not obviously broken — it ships
   silently if unchecked.
7. **The user creates the account and publishes.** You produce files.
8. **NEVER submit a generation job as a price/feasibility probe.** kie has no
   dry-run: any accepted submission bills in full. A "probe" with prompt
   "test" once burned 1,286 credits (~$6.40) in junk renders. Ask the model's
   cost endpoint if one exists; otherwise the FIRST submission is already the
   real one: full motion prompt, duration = audio length rounded UP (+1s).
9. **Every video submission carries the full motion prompt.** Without it,
   Seedance invents a dramatic camera push-in AND beds its own music
   (measured on a promptless clip: 45.9 frame-diff vs <8 static, and a 95×
   harmonic stack at 393Hz). "Static locked-off camera, one continuous shot"
   + "only his voice, quiet ambience" — on every job, no exceptions.
10. **Record every task id immediately** to a file before polling. A lost id
    on a billed job is unrecoverable.

## First-run setup (do this conversationally, one thing at a time)

1. **Target**: ask ONE question — "Which Instagram account do you want to
   recreate? Paste the handle or profile URL." Instagram only for now; do not
   ask which platform. Any niche works — the method is format-teardown, not
   monk-specific.
2. **Keys — make this effortless.** NEVER go hunting for keys in other
   projects' `.env` files (it reads as snooping and permission systems block
   it). Instead:
   a. Immediately CREATE the project `.env` with placeholders and OPEN it in
      their editor so they can paste keys straight in:
      ```
      APIFY_TOKEN=paste_here
      KIE_API_KEY=paste_here
      ELEVENLABS_API_KEY=paste_here
      ```
      (`open -t .env` on macOS, or the editor they use.)
   b. Then guide them to each key IN CHAT, one at a time, with the exact
      click-path and clickable URLs:
      - **Apify** → https://console.apify.com/settings/integrations → sign up
        free → copy "Personal API token". Free tier covers the scrape.
      - **kie.ai** → https://kie.ai/api-key → sign in → create key. This
        bills the character image (~$0.02) and video clips, so they should
        also top up a few dollars while there.
      - **ElevenLabs** → https://elevenlabs.io → profile icon → "API Keys" →
        create. Free tier covers roughly one reel of narration; starter plan
        (~$5) is safer.
   c. Tell them to save the file and say "done". Verify each key with a
      cheap authenticated call (Apify user info, kie credits, ElevenLabs
      voices) and report which ones work — never echo the key values back.
3. **Engine choice** — present this menu with honest trade-offs and let the
   user pick (verify current prices on their account at first render):

   | engine | quality | measured cost | notes |
   |---|---|---|---|
   | Seedance 2.0 (kie) | best image, hand gestures, re-performs speech | ~$0.205/s (~$18 per 90s reel) | ⚠️ strips social CTAs from speech; needs 12–15s chunks (shorter = filler); language drift if character reads as foreign — prompt "speaks in English" |
   | **Kling Avatar Pro (kie)** — recommended | exact lip-sync to your audio, softer image, no gestures | ~$0.075/s (~$6.70 per 90s reel) | 21/21 clips passed QC first roll in production; chunks can be 15–20s; spoken CTAs work |
   | Wan-S2V / InfiniteTalk (fal/kie) | budget; quality varies by face | ~$0.03–0.06/s (~$3–5 per reel) | test ONE clip before committing; InfiniteTalk does up to 10-min single takes |

## Phase 1 — Scrape & teardown

1. Apify: pull the account's reels (posts + play/like/comment counts) and
   download the top ~20 by plays. Transcribe them (whisper).
2. Extract, with numbers, into `analysis/SOP.md` for this project:
   - **Hook patterns** (first 2 sentences of every top reel, verbatim)
   - **Beat structure** (map 3–5 top transcripts onto a beat skeleton: hook →
     authority → instruction → branches/payoff → absolution → comment-CTA →
     product bridge; note which beats recur)
   - **Close formula**: check the last ~30s of every top transcript for a
     fixed tail (product name + "link in my profile" style) vs a fresh pivot.
     In the source project the tail was 7/7 verbatim and the pivot 7/7 unique
     — assume that shape until the data says otherwise.
   - **Comment CTA**: the literal words viewers are told to type, per reel.
   - **Pacing**: measured wpm from transcript length / duration.
   - **Caption style**: usually 3–4 hashtags doing zero work — confirm.
   - **Length distribution** and correlation with plays.
3. Save 2–3 reference frames of the influencer for *style* reference (framing,
   lighting, setting) — used to inform the new character's setting, never to
   reproduce the person.

## Phase 2 — Character (user approval gate)

1. Draft a character brief that is deliberately NOT the influencer: shift
   ethnicity/age/setting while keeping the archetype that makes the niche work
   (e.g. Monk Chen, Japanese monk in tatami room → "Master Kaion", Bhutanese
   monk in a mountain courtyard).
2. Write one detailed photoreal portrait prompt: **chest-up (selfie distance —
   NOT waist-up; the face must dominate the frame like the source account)**,
   centred, facing camera, eye-line to lens, hands resting flat and visible,
   soft daylight, natural skin texture, 9:16. Keep per-topic props (signs,
   boards, objects) OUT of the anchor — the anchor is identity, reused across
   every reel; props are added per-reel with a cheap image edit. **State positively what IS in frame — negated
   objects get generated** ("no tripod" produces tripods).
3. Generate ONE image (kie `google/nano-banana`, ~$0.02). **Show it to the
   user.** Iterate on their notes. Only an explicit "yes" unlocks Phase 3.
4. The approved image is the **anchor** — every clip references it. Save it
   and its URL; identity continuity across the whole account depends on it.
   Keep resolution as high as the generator allows.
5. Pick a voice with the user (ElevenLabs voice list; calm/character-matched;
   ~140–160 wpm at speed 0.88–0.92).

## Phase 3 — Script (per reel)

1. Recreate the target's best performer first, then work down the ranked list.
   Skip anything medical.
2. **Keep the hook verbatim** (or near-verbatim). Never rewrite a proven hook.
3. Write to the extracted beat skeleton, second person, short declarative
   sentences, no hedging, one term of endearment max, never explain mechanisms
   scientifically.
4. Close = fresh pivot naming this reel's tactic and its limit + the fixed
   tail: "Everything I know is inside <PRODUCT>. The link is in my profile."
5. CTA rule: **two drawn cards with DIFFERENT text** — top band = comment
   instruction with the literal words to type; closing card = the return visit
   or share ask. The same sentence twice reads as a rendering fault.
6. On Seedance, social imperatives ("Send this to…", "Write in the comments…")
   are silently deleted from speech — keep them drawn-only. On lip-sync
   engines (Kling avatar) spoken CTAs work.

## Phase 4 — Voice & chunking

1. ONE continuous ElevenLabs render per script (`/with-timestamps` for
   character-level alignment). Per-chunk renders drift in voice identity.
2. Tile the narration into chunks **on sentence boundaries** using the
   alignment timestamps:
   - Seedance: 12–14.9s hard (shorter → generic filler; longer → over the 15s
     cap). If the sentences don't tile, rebalance the script (add/trim a short
     sentence) and re-render — do not ship an 8s chunk.
   - Kling avatar: 15–20s, minimum ~12s for safety.
3. **Loudnorm every chunk** (`loudnorm=I=-16:TP=-1.5:LRA=11`). Below ~0.048
   RMS reference audio returns filler instead of the script. This is free and
   load-bearing.

## Phase 5 — Generate

- Upload anchor image + each loudnormed chunk; submit one job per chunk with a
  motion prompt describing the static-camera talking shot ("speaks steadily,
  small natural head movement, static locked-off camera, one continuous shot",
  plus "He speaks in English" for Seedance, plus skin-texture words for Kling:
  "weathered aged skin, visible pores, natural skin texture").
- Report the measured billing delta after the first clip and after the batch.

## Phase 6 — QC GATE (mandatory, per clip)

1. **Text**: whisper-transcribe the output, diff against the chunk text.
   ≥0.9 similarity passes (whisper writes "seven"→"7" — don't count numeral
   artifacts as failures, and never put number-words in required phrases).
   Below that → re-roll (Seedance) or investigate (lip-sync engines should be
   ~1.0 by construction).
2. **Music bed**: FFT the quietest ~25% of audio frames; sharp partials on
   note frequencies = the engine bedded a drone → re-roll. A level check does
   NOT catch this. Never prompt "no music" — describe what IS there ("only his
   voice, quiet ambience").
3. **Sharpness**: Laplacian variance on a face/chest crop at start/mid/end. A
   collapse of ~50% across the clip (OmniHuman-style skin decay) fails the
   clip; a settle in the first second off the anchor still is normal.

## Phase 7 — Assemble

Use the bundled `assemble_reel.py` (config-driven). Critical behaviors it
implements — keep them if you modify it:
- **Caption timing from Whisper on the RENDERED audio, never the script**
  (engines re-perform at their own pace).
- **Sample-accurate concat**: pad each clip's audio to its exact video
  duration inside one filtergraph (`apad=whole_dur=…`). Kling clips ship audio
  0.2–0.3s short; naive concat accumulates ~1s of lip desync by clip 6.
- **De-plastic pass** on lip-sync engines: `unsharp + noise` grain before
  caption compositing.
- Captions: max 2 rows per card (split cards, never 3 rows), wrap by measured
  pixel width, hold each card until the next, respect IG safe zones (top
  ~230px, bottom ~430px, right ~190px on 1080×1920), band at 0.72H.
- CTA top band rides from ~15s onward; closing CTA card takes the final ~4.5s.
  Quoted comment phrases get a hard line break so the quote sits whole on its
  own row.
- Music: real royalty-free track (CC0 classical works well) mixed at ~0.20 of
  voice RMS, sidechain-ducked; never synthesize a sine-pad bed. Deliver both a
  dry and a music master; the user can also add music inside Instagram.

## Phase 7b — Deliver in ONE folder (always)

The final message to the user is SHORT: the two files per reel plus the
paste-ready caption. Open the folder for them (macOS: `open`); attach or show
the videos if the client supports it.

```
REVIEW/
  1_reel_<slug>_MUSIC_<len>s.mp4    <- post candidate: captions + our music
  1_reel_<slug>_DRY_<len>s.mp4      <- clean plate: no captions, no music
  ...
  SOURCE_NOTES.md                   <- per reel: hook, paste-ready caption,
                                       CTA card texts, source reel recreated
```

Exact spec of the two files:
- **DRY** = the pure video: static locked-off camera (no zooms, no edits,
  no punch-ins), the character performing like the source account, speaking
  the ElevenLabs-scripted narration, nothing burned in, no music. This is the
  clean plate the user can caption/soundtrack inside Instagram or TikTok.
- **MUSIC** = same video with burned captions (2-row cards, tested layout,
  CTA bands) and OUR royalty-free bed at the measured ratio — never
  engine-generated music (the QC gate re-rolls any clip that came back with
  its own bed).

Tell the user in one line: post the MUSIC file as-is, or take the DRY file
and add captions/any song in-app. Only re-render if they hand you a specific
track.

## Phase 8 — Launch guidance (tell the user, don't do it for them)

- Bank ~15 finished reels before posting one; post best-first, 1–2/day.
- Cold-start reach is a non-renewable window — first 10 posts must be the
  strongest material.
- Bio + product link live from post #1. Reply to every comment for 30 days.
- Caption = 3–4 niche hashtags. Label the account as AI (platform AI tag).

## Bundled scripts (`scripts/` in this plugin)

`kie.py` (kie client: credits, upload, image, engines), `eleven.py` (voice with
timestamps), `render_reel.py` (Seedance chunk submitter), `qc_gate.py`,
`align_clips.py` (framing drift), `assemble_reel.py` (concat→captions→master),
`drone_check.py`. They were extracted from a working production project and
carry monk-era constants — on first use in a new project, copy them into the
project, then parameterize the character prompt, product name, and reel
configs from this project's own files. Media playback on macOS: open files
with `open -a "QuickTime Player"`, never bare `open`.
