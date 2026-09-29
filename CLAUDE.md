# influencer — Monk Chen teardown → `@master.kaion` reel factory

**Goal:** learn what makes @monkcheen's reels go viral, and produce reels for a new
account (`@master.kaion`) selling an equivalent product.

## Read before doing anything

0. **`output/SESSION_LESSONS_2026-08-15b.md`** — seven lessons from the reels
   32-33 session, each paid for once: the DM funnel's dead `postId: null`, the
   47 near-duplicate source clusters, anchor identity drift, proof that the
   burned text CANNOT be prompted away, how to actually detect it, and how to
   size the caption pill. Read it before scripting, spending or "fixing" a gate.


1. **`output/PRODUCTION_LEDGER.md`** — ⚠️ **THE SINGLE SOURCE OF TRUTH for what
   already exists.** One row per reel: his source shortcode, when we generated
   it, and whether it is built / scheduled / published. A source shortcode may
   NEVER appear twice — regenerating a topic we already made is the most
   expensive mistake available in this project.

   It is injected into **every session automatically** by the `SessionStart`
   hook in `.claude/settings.json`, so there is no excuse for not knowing.
   Commands:

   ```bash
   python3 scripts/ledger.py check <shortcode>   # exits 1 if already produced — RUN BEFORE ANY SPEND
   python3 scripts/ledger.py show                # full table
   python3 scripts/ledger.py add <reel> "<topic>" <shortcode> <plays>
   python3 scripts/ledger.py set <reel> status scheduled --when <ISO8601>
   python3 scripts/ledger.py set <reel> status published --url <post url>
   ```

   `add` REFUSES a shortcode that is already in the ledger. Update the row the
   moment a reel is built, scheduled, or published.
2. **`sop/SOP.md`** — the system. Parts 0/3 carry hard-won measurements; Part 3 in
   particular cost ~$80 of generations to establish. **Do not re-derive it.**
3. `analysis/VIRALITY_ANALYSIS.md` — where the correlations come from.

## Hard rules

- 🛑 **NEVER SCHEDULE OR PUBLISH ANYTHING WITHOUT EXPLICIT PER-REEL APPROVAL.**
  Building, assembling and reviewing are free and need no permission. Anything
  that puts a reel in front of the public — a Blotato schedule, a story, an
  immediate post — requires the user to see that specific reel and say yes to
  that specific reel. "Schedule the batch" approves only the reels named in
  that message. Show the file, wait for the yes, then schedule, then record it
  in the ledger. If a master is rebuilt after being scheduled, the queued copy
  is STALE — re-upload needs its own approval too.
- 🤖 **EVERY POST DISCLOSES THAT THE CHARACTER IS AI — VIA INSTAGRAM'S OWN
  TOGGLE, NOT THE CAPTION.** Platform rules require disclosure for
  photorealistic AI people. **Changed 2026-08-07 on user instruction: no
  disclosure TEXT in the caption.** Captions are hashtags only, exactly like
  the source account (`#monk #wisdom #health #usa`). The disclosure is
  Instagram's **"AI info"** label, switched on in the app (Advanced settings
  when posting, or edit after publish).

  ⚠️ Blotato's Instagram API exposes NO AI flag (`isAiGenerated` is
  TikTok-only, `containsSyntheticMedia` YouTube-only), so **nothing about the
  disclosure is settable programmatically** — the in-app toggle is a manual
  step the user must do on every feed post and every story. If we ever post to
  TikTok or YouTube, set the API flags too.
- **Never touch Instagram from the user's session.** All IG data comes via **Apify**
  — no cookies, no browser automation, no scraping from their account. Codex may be
  running scrapes in parallel; check for an existing Apify run before starting one.
- **The user creates the account and publishes.** We produce files, they post.
- **Never quote a price that has not been empirically verified.** Read the billing
  delta from `kie.credits()` before and after. Price estimates in this project have
  been wrong four times.
- **Open media with `open -a "QuickTime Player"`** — bare `open` sends audio to
  Apple Music, which the user does not pay for. **Every finished master opens
  in QuickTime AUTOMATICALLY the moment it is built** (user instruction
  2026-08-15) — `finish_reel.py` calls `show()` on both the dry and music
  paths so it never depends on anyone remembering. Any new assembly path
  must do the same.

## 💸 Spend discipline — four rules, all bought with real credits

Read these before submitting anything paid. The pattern across this project is
that credits are almost never lost to an engine misbehaving; they are lost to
spending before a question was settled, or to spending in a way that cannot
answer the question the spend was meant to answer.

1. **Record the taskId before polling.** Every paid render goes through
   `scripts/render_avatar.py` (writes `data/kie_tasks.json` first, `--resume
   <reel>` refetches free) and runs in the BACKGROUND. kie has **no
   task-history endpoint** — a taskId that exists only in stdout is money gone.
   Cost of learning: ~440cr, 2026-08-10.
2. **Never spend until the script text is locked** — including, for a
   recreation, the verbatim hook. Cost: ~440cr, 2026-08-11, on a render thrown
   away when the hook changed.
3. **One variable per paid render.** Reel 24 changed anchor AND motion prompt in
   one submission; it came apart only by luck. Confounded renders are how the
   wrong "seed follows the audio" rule got written in the first place.
4. **Answer every question on the cheap artifact.** An anchor still is 4cr; the
   video it anchors is ~440. Framing, expression, realism and subtitle-band
   composition are all still-image questions. `anchor_check.py` runs inside the
   render path for this reason.

### 🛑 CALIBRATE EVERY GATE ON A KNOWN-GOOD INPUT BEFORE TRUSTING A FAILURE

Full RCA of seven defects: **`output/RCA_GATES_2026-08-15.md`**. One rule
prevents the expensive half of them:

> **A gate that has never returned PASS on a verified-good input is not a gate,
> it is an untested function.** Run it on known-good (must PASS), then on
> known-bad (must FAIL), and only then on the unknown.

Three gates were wrong on 2026-08-15 and every one would have been caught in
seconds by that check:
- `gate0_tts` scored sentences against a window 1.4x their length and divided by
  the longer side, so a PERFECT match capped at 1/1.4 = 0.714 — 13 of 14 clean
  sentences "failed".
- After that fix, `difflib`'s **autojunk** (drops any element in >1% of a
  sequence over 200 long) zeroed the scores. Compare WORDS, not characters, and
  pass `autojunk=False`.
- `qc_gate`'s subtitle band was hardcoded `crop=1080:500:0:1150` — out of bounds
  on kling-standard's 720x1264, so it had been ERRORING, not passing, since the
  engine default changed at reel 16.

**Derive every geometric or numeric constant FROM the artifact** (probe width,
height, duration, loudness); never write the literal. And **assert the invariant
after the operation** — that is how `build_audiobook_pt.py` catches duration
drift, and it is what nobody did for loudness (below).

### 🔊 MASTER EVERY REEL TO -14 LUFS — measured, not assumed

His source is **-14.1 LUFS**. Ours were **-24.7 dry and -30.8 with music**, i.e.
16.7 dB quieter, because `amix=inputs=2` normalises by input count — so adding
the bed made every music master 6 dB QUIETER than its dry twin. Nobody had ever
measured the output. Final step of assembly is now:

```bash
ffmpeg -i in.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k out.mp4
```

Verify with `ffmpeg -i f.mp4 -af ebur128 -f null -` and read Integrated.

⚠️ **AND PIN THE SAMPLE RATE — `loudnorm` silently makes it 96 kHz.** Found by
QA on reel 35, 2026-08-15. The filter resamples to 192 kHz internally and AAC
caps at 96, so **every master built since the loudness fix shipped at 96 kHz**
while `make_story.py` goes out of its way to conform stories to 48 kHz. Nothing
measured it. `finish_reel.master()` now appends `,aresample=48000` and passes
`-ar 48000`; assert it with:

```bash
ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of csv=p=0 f.mp4
```

Same lesson as the loudness bug itself: **the operation you did not assert is
the one that drifted.**

### ⚠️ THE SUBTITLE GATE AND THE ANCHOR RULE NOW FIGHT EACH OTHER

We fill the lower third (table, open book, candle) so kling does not burn fake
subtitles into an empty band. **An open book is printed text**, so it saturates
the text-density detector: reel 26 flagged 34/34 samples and was completely
clean on inspection. For this anchor family the gate can only be cleared BY EYE.
**Do not raise the threshold to make it green** — that blinds it to real burned
text. Read the contact sheet.

### ⚠️ KLING FREEZES EVERYTHING THAT IS NOT THE FACE

Measured on reel 26: candle flame ~1.0 mean frame-diff (compression noise) vs
~14 for the mouth. No model tier changes this — it animates the face region of a
still. **Prop choice is the fix:** put things in the lower third that have no
business moving (prayer beads, a stone bowl, folded cloth, an unlit lamp).
Never a flame, running water, or smoke — the frozen motion is a dead giveaway
and the operator spotted it unprompted on reels 24 and 26.

### 🛑 THE MOTION PROMPT MUST DESCRIBE THE ANCHOR YOU ARE ACTUALLY SENDING

Found 2026-08-15 after the operator said "he is still very stiff with shoulders".
`render_avatar.MOTION` still described reel 24's WIDE shot — "cross-legged on the
floor", "hands folded in his lap", "the patterned stone floor fills the lower
part of the frame" — months after the anchors became CHEST-UP portraits behind a
table with **no legs, lap, hands or floor in frame**. kling was handed a picture
of a torso plus instructions about crossed legs, and THREE separate commands to
hold still aimed at body parts it could not see.

**Whenever the anchor composition changes, re-read MOTION in the same commit.**
Rules for that text:
- describe ONLY what the anchor actually shows;
- name what MOVES before what stays still — a prompt that is mostly stillness
  language produces a photograph that happens to talk;
- 20-40 words of motion, all positive phrasing;
- **never delete** "he speaks in English, in a calm measured voice" (the language
  guard that stopped Seedance drifting to Japanese) or "only his voice and quiet
  temple ambience" (the guard against the engine bedding its own music).

**Diagnose the prompt before buying a bigger model.** Doubling to ai-avatar-pro
would have cost 2x and taught nothing, because prompt and engine would have
changed together — the same confounding that produced the wrong "seed follows
the audio" rule at ~880cr.

### ✅ THE CAPTION BAND COVERS THE BURN BAND — burns are now cosmetically moot

🛑 **FALSIFIED 2026-08-15 BY A THIRD DATA POINT — THE BAND IS NOT CONSTANT, AND
THE CARD DOES NOT ALWAYS COVER IT.** Reel 32 (anchor a32d) burned at **0.681 -
0.819** of frame height, measured across 14 samples. The card covers 0.760 -
0.839, so the top ~40% of the burn — the rows at 0.681-0.737, present in EVERY
sample — sat completely uncovered. A reel in this state cannot ship.

Do not assume the cover works. **Measure the burn's vertical extent whenever the
gate flags, and compare it against the card** before deciding a reel is
salvageable. The original two-render measurement is kept below for the record.

**Measured on two burned renders** with different anchors, poses and settings
(reel 28 take 1 on a23b; reel 30 on a26c): y 961-1036 of a 720x1264 clip =
**0.76-0.82 of frame height** = y 1459-1574 at 1080x1920. The old caption card
centred at 1470 stopped just short, which is exactly why the gibberish read as a
"second line" under our text.

`assemble_en.py` now draws the card from `1460 - bh//2` down to **1610**, at
**940 px wide** and **fully opaque (alpha 255)**. All three matter:
- too narrow (760) and the burn peeks past the right edge;
- at alpha 230 the bright glyphs show straight THROUGH the card.

This salvaged reel 30 (632 cr) and makes the defect invisible going forward.
**It is a cover, not a cure — keep the render-time gate** so we still know the
burn rate, and never let the card drift back up or lose opacity.

⚠️ **The "keep the proven foreground" theory is now WEAK too.** It held that the
four clean anchors shared one foreground (low table, open book, beads, daylight)
and both burns were departures from it. Reel 32's a32d used **exactly that
foreground**, in daylight, passed the band check at 0.0382 — and burned anyway.
So composition family does not protect a render either. Burning is currently
UNPREDICTED by anything we can measure before spending.

⚠️ **No anchor-side screen predicts burning.** Two were tested and both failed:
mean band detail (a26c burned at 0.0676, the HIGHEST ever recorded) and widest
quiet strip (a26c 0.425, identical to the clean set). Do not invent a third and
spend a render proving it. `anchor_check`'s floor still catches the gross cases
(a17 0.0102, a23b 0.0293) so keep it, but do not trust it as sufficient.

### 🛑 MEASURED 2026-08-15: YOU CANNOT PROMPT THE BURN AWAY, AND PRO DOES NOT FIX IT

Two 15s single-variable tests on the same anchor (a32d) and the same audio,
against reel 32's 38% baseline. 360 cr, ~$1.80:

| render | burn |
|---|---|
| standard + base prompt (reel 32) | 38% of frames, intermittent, ONE line |
| **standard + "no subtitles, no captions, no text" clause** | **~100% of frames, PERSISTENT, TWO lines — WORSE** |
| **kling/ai-avatar-PRO + base prompt** | **16.7%, intermittent, fainter — better, but 2x price** |

**The negation rule held.** Asking for "no text" produced more text, exactly as
"no tripod" produces tripods. Never add an anti-text clause to the motion
prompt. Pro roughly halves the rate and is not a cure at double cost.

⚠️ **AND THE PERSISTENT CASE BROKE THE DETECTOR.** `measure_burn`'s temporal
residual reported the two-line render **0/30 CLEAN**: constant text sits in the
median frame, so it deviates from nothing. `finish_reel` now also compares band
detail against the ANCHOR still (a known-clean plate of the same scene), which
separates the cases cleanly — clean 0.94-0.97x, persistent burn 1.40x, threshold
1.15. Intermittent burns do not move that signal; the temporal test catches
those. **Two signals, because each is blind to what the other sees.**

### 🔬 ENGINE RESEARCH 2026-08-15 — what a real fix would take

- The commonly cited fix ("use audio upload instead of TTS mode") **does not
  apply to us** — we already pass `audio_url`, not text.
- **kie exposes no subtitle or negative_prompt parameter.** `kling/ai-avatar-*`
  takes `image_url`, `audio_url`, `prompt` and nothing else, so there is no flag
  to switch the behaviour off.
- Probed kie for alternatives: `infinitetalk`, `wavespeed-ai/infinitetalk`,
  `wan/wan-2.2-s2v` all return 422 "model name not supported". **A different
  engine means a different vendor account** (WaveSpeedAI), not a config change.
- Listed, UNVERIFIED vendor pricing: InfiniteTalk 720p ~$0.06/s, Wan-2.2-S2V
  480p ~$0.03/s. Never quote these as fact — measure a real billing delta first.

### 🛑 SUBTITLE GATE IS CODE NOW — a manual QA step in a batch WILL get skipped

Reel 28 shipped with kling's gibberish burned under every caption (616 cr). The
gate was not broken and the anchor guard was not bypassed — **the check was
simply not run.** It was run on reels 26 and 27, and on 28 a motion measurement
was substituted for it. That is the whole failure: a manual step inside a batch
is a step that eventually does not happen.

It now lives in `finish_reel.py`, runs BEFORE assembly, writes a contact sheet
and **exits non-zero** unless `BAND_OK=1` confirms a human read the sheet. Never
re-add it as a manual step, and never pass BAND_OK without looking.

**How to read the sheet:** our own anchors put an open book in the band, which
is printed text and flags the detector every time. Burned text is a **SECOND
line of pale gibberish, usually just under the caption** ("Te ãñeUrm eñ gia tne
bñīaa dhe hemlē"). Book pages = fine. A second line = re-roll.

**ANCHOR_CHECK FLOOR RAISED 0.024 -> 0.040** on this evidence:

| anchor | band detail | outcome |
|---|---|---|
| a17 | 0.0102 | burned, 2/2 (~880 cr) |
| a23b | **0.0293** | **BURNED (reel 28, 616 cr)** |
| a21c | 0.0419 | clean (reel 26) |
| a22 | 0.0501 | clean (reel 27) |
| his source | 0.0671 | clean |

0.024 was set from two marginal passes and let 0.0293 through. **A 4-credit
anchor re-roll is 150x cheaper than the render it protects** — when an anchor
lands between 0.030 and 0.040, re-roll it, do not argue with it.

### 🛑 ANCHOR IDENTITY DRIFT — EDIT FROM THE CANON, NEVER FROM THE LAST ANCHOR

Found by the operator 2026-08-15 ("u sure is same monk his face changed?").
nano-banana **re-renders the face on every edit**, so generating each anchor
from the previous one stacks the error:

    kaion_rest  ->  a21c/a25  ->  a32d  ->  a33b  ->  a33d
    visibly OLD      thinner     thinner   thinner   visibly YOUNGER + FULLER

Three generations of drift produced a different man, and `kaion_rest` is now
visibly older than every recent anchor — the drift had been running unnoticed
across many published reels and NOTHING checked it.

**Rule:** `make_anchor.py` now defaults `--from` to `CANON` (`a32d_cloister`),
so every anchor is exactly ONE generation from the reference and error cannot
accumulate. Passing `--from` explicitly prints a warning. `kaion_rest` is NOT
the canon — the audience has seen the newer face, so reverting is itself a
visible change.

**Gate:** every run writes `anchors/_identity_<name>.png` — the new face beside
the canon. READ IT. There is no face-embedding model here and a pixel metric is
meaningless across different crops and lighting, so this one is by eye. Same
man, or re-roll for 4 cr.

### 📐 ANCHOR COMPOSITION: props must be LARGE and CLOSE, or the band fails

`anchor_check` measures the 0.60-0.86 band. A small table low in frame leaves
that band filled with flat robe and fails (a23 v1: 0.0214). **No crop can
rescue it** — twelve crop variants were tried and all scored worse, because
tightening a 9:16 crop cuts the props off the sides. The wording that passes
puts the table's NEAR EDGE close to the lens and says it fills the bottom third
(a22 0.0501, a23b 0.0293). Re-roll for 4cr rather than fighting a crop.

### 🎯 FACE SIZE SETS LIP-SYNC QUALITY, NOT MODEL TIER

Reel 24's face was ~8% of frame height and read mushy; reel 26 at ~20% on the
SAME engine reads clean. Kling animates the face REGION, so a wide shot leaves
it a few dozen mouth pixels. Match the source: his is ~16-18%. Upgrading to
ai-avatar-pro at double the price buys a sharper WIDE shot with the same tiny
mouth — fix framing first, and treat the engine as a separate single variable.
Anchor prompts must state the CROP as a hard boundary BEFORE the pose: describing
a kneeling pose in detail made nano-banana pull the camera back to show it.

**And when a check starts failing everything, suspect the check.** Three false
alarms on 2026-08-10/11 (stories "misconfigured" — I read `draft.content`
instead of `draft.target`; "38 comments → 0 DMs" — I sampled automations whose
keywords nobody used; "PT YouTube task broken" — the video published after the
last run). The transcript-gate incident below is the same failure mode with a
60,460-character bill attached.

## 🧭 STRATEGY — council review 2026-08-12 (read before proposing changes)

Four seats reviewed the business end to end. Full record, including the beliefs
it INVALIDATED and the topics still open, is in **`output/COUNCIL_2026-08-12.md`**.
The live demand experiment it started is **`output/FUNNEL_TEST.md`** (baseline
2026-08-12, checkpoint 2026-08-22, reading pre-registered).

Headline: **the production line was never the bottleneck.** ~40,000 IG views
produced 0 page views because nothing we published on Instagram was clickable.
Every seat independently said redeploy existing assets rather than make more.

Five steering beliefs did NOT survive the review — do not act on them again:
1. "Hashtags cut views 31.7%" — unverifiable; our own data leans the other way.
2. "Rank sources by play count" — ANTI-correlated (718k source -> 222 views).
3. "TikTok needs a 10-14 day warm-up or bans you" — vendor marketing; TikTok
   penalises AUTOMATION, not newness. Manual-only stays; the rationale was wrong.
4. "TikTok is where our reach is" — under 5K followers it is the weakest surface
   (Shorts 15,160 · Reels 625 · TikTok 350). It is an outlier bet, not reach.
5. "30-60s is the target" — SOP measures 143s median, r=+0.113, and says the
   short choice was ECONOMIC for Seedance at $0.205/s. Kling is $0.0383/s, so a
   150s reel is ~$5.75 and the basis is gone. The 150s control is still UNRUN.

Selection rule now: rank by VEIN and cross-account proof, never by source plays.

⚠️ **CORRECTED 2026-08-15 (later, on n=598 not n=64): rank by VEIN FIRST, not by
comment rate.** The earlier "rank by comment rate" line was drawn from 64
captioned posts and does not survive the full corpus. Measured across 598
transcripts, per account, outlier rate = share of posts above 3x that account's
own median:

| vein | monkcheen (median 8,081) | yangmunus (median 222,318) |
|---|---|---|
| family | **38% outliers** | 10% |
| identity | **33%** | 8% |
| ritual | 29% | 8% |
| health | **9%** | 12% |

**Vein matters when the account is SMALL and stops mattering when it is big.**
monkcheen's distribution is content-driven; yangmunus at 2.53M followers gets
served everything regardless. We are small, so monkcheen's pattern is the one
that applies: family/identity are ~4x more likely to produce an outlier than
health, and HEALTH IS THE WORST BET despite being 53% of the corpus.

Comment rate and outlier rate point in DIFFERENT directions — ritual has the
highest median c-rate (0.347%) and family/identity the lowest (0.114/0.124%).
So: **pick the vein for reach, then use comment rate to choose within it**,
because the DM funnel needs comments. Never let c-rate override vein.

Source list: `data/competitors/CORPUS.md`. Storage map and the
"a scrape is not saved until its MEDIA is on disk" rule: `data/competitors/README.md`.
The same script exists on both accounts with a 35x spread — yangmunus
`DVEI18AgH7h` 957k plays / 14,692 comments vs monkcheen `DVpPFVSDIPj` 27,450,
and we built reel 12 from the weak one. Check BOTH accounts before choosing.
Selection is currently constrained by the corpus, not by taste: only 62 of 271
monkcheen posts are transcribed (43 health, 6 family, 4 ritual), so the
family vein is exhausted there. yangmunus captions (183/200 real) are the
usable corpus until the remaining ~209 transcripts exist.
The family/identity vein produced our only hit (reel 7, **55,800 views** per the
app on 2026-08-15 — the Apify scrape said 31,356 and undercounts); every
ritual/habit reel is under 2,700. Require a second-person instruction in the
first sentence.

## Pipeline

```bash
REEL=2 python3 scripts/render_reel.py 3 5 6      # generate clips from chunks_reel2.json
REEL=2 python3 scripts/qc_gate.py 1 2 3 4 5 6    # MANDATORY gate: text + drone
REEL=2 python3 scripts/align_clips.py 1 2 3 4    # framing drift -> *_aligned.mp4
REEL=2 python3 scripts/assemble_reel.py 1 2 3 4  # -> voice-only master

# with a bed (default track + level; see memory/reel-music-bed.md)
MUSIC=output/assets/music/chopin_prelude_28_6.mp3 MUSIC_RATIO=0.200 \
  REEL=2 python3 scripts/assemble_reel.py 1 2 3 4 --music
```

**`REEL=` is not optional.** Clip numbers restart at 1 for every reel, so
omitting it renders reel 2 into reel B's filenames. That is how reel B's
`seedance_01.mp4` was destroyed on 2026-07-25.

### Fixed conventions — same for every reel, only the wording changes

- **Captions never exceed 2 rows.** Caption cards split to get there; CTA cards
  shrink their font. A card one row taller makes the whole block jump.
- **The top CTA band and the closing CTA card must say DIFFERENT things** — top
  = the comment instruction with the literal words to type, close = the return
  visit. The same sentence in both reads as a rendering fault.
- **CTAs are drawn, never spoken** — Seedance refuses them (see below).
- **Align before assembling.** `assemble_reel.py` auto-prefers `*_aligned.mp4`.
- **Music: CC0 Chopin from `output/assets/music/`, ratio 0.200.** No attribution
  needed. The `0.95` ratio in the script is a synth-only correction — never
  apply it to a real recording.
  🎵 **Licence discipline — `output/assets/music/LICENCES.md` is the authority.**
  Verified 2026-08-13: the Musopen Chopin collection is **CC0 1.0 Universal**
  (commercial use permitted, attribution not required), and CC0 covers the
  RECORDING, which is the part still in copyright when the composition is not.
  Before adding any track: confirm the licence of the recording, accept only
  CC0/public domain, and record the source URL. **CC BY is unusable here** —
  captions are hashtags only, so there is nowhere to put a credit. Two Kevin
  MacLeod tracks (CC BY) were moved to `music/_do_not_use/` on 2026-08-13 for
  exactly that reason. Commercial releases are legal ONLY via a platform's
  in-app picker, never baked in with ffmpeg (this is why PT masters ship dry).

- `scripts/kie.py` — kie API: upload, credits, Seedance. `cmd_seedance(n, secs, audio)`.
- `scripts/render_reel.py` — chunks the narration, **loudnorms it** (load-bearing —
  see SOP Part 3), submits each clip.
- `scripts/assemble_reel.py` — concat → Whisper → PIL caption cards → master.

**Between generate and assemble there is a mandatory gate: transcribe every clip and
diff against the intended text.** A failed Seedance generation is fluent and
confident, not obviously broken — it will ship silently if unchecked.

## State (2026-07-25)

- **Reel B is done**: `output/reels/reel_B_MASTER_dry.mp4` — 96.5s, voice only,
  posted by the user as-is. `_music.mp4` variant rejected (synth bed unusable).
- Reels C and D not yet written. Next batch targets **30–60s** (SOP Part 0).
- ⚠️ **CORRECTED 2026-07-26 — the claim below is TOO BROAD. Seedance speaks the
  product bridge fine:** `output/assets/seedance_07.mp4` transcribes clean,
  including "The link is in my profile." What it actually strips is
  **second-person social imperatives** ("Send this to…", "Write in the
  comments…") — and it deletes them surgically rather than garbling, leaving the
  rest of the sentence intact (`sd2_05_DRIFT`: "**Send this to** the person who
  sleeps eight hours" → "**A** person who sleeps eight hours").
  Phonetic garble is a DIFFERENT bug (language — see below). Keep the bridge and
  link line spoken; draw only the comment/share asks.

- ⚠️ **CHUNKS UNDER ~12s COME BACK AS FILLER.** Established 2026-07-26 at a cost
  of **$4.87**: clips of 8s, 6s and 8s all returned the character prior ("The
  truth is not found in extremes…") at similarity 0.13–0.18, while every clip
  ≥12s has passed. Loudness was ruled out (RMS 0.148–0.157, mid-band). A short
  reference is a weak reference. **When re-cutting a chunk to drop a sentence,
  re-balance to 12–14.8s** — pad from a neighbour or rewrite the dropped
  sentence as a declarative. This also means a reusable standalone "tail" clip
  is impossible: the invariant tail is only ~7.5s alone.

- ⚠️ **Whisper mangles our own clean source.** It renders "the weight" as "to
  wait" and "Forty" as "40" on the ElevenLabs master itself. Never put those in
  `qc_gate.py`'s required phrases — an earlier run blamed Seedance for what was
  a measurement artifact.

  **Repeated 2026-08-08 on the PT audiobook at a cost of 60,460 ElevenLabs
  characters (~1.2 book passes).** The gate compared "Dia um" (our script)
  against "Dia 1" (Whisper), so every chapter naming a number "failed" and got
  re-rolled 3x. The audio was perfect the whole time. **Rules for any
  transcript gate, forever: (1) strip digits AND number-words from BOTH sides
  before comparing; (2) score similarity as the SUM of matching blocks, never
  the single longest match, so one differing word mid-sentence cannot fail a
  good line; (3) NEVER delete a failed take — it is already billed and it is
  the only evidence of why it failed; (4) before trusting a gate that starts
  failing everything, transcribe ONE file by hand and read it — a gate that
  fails 30/30 is a broken gate, not 30 broken generations.**

- ⚠️ **Superseded, kept for the reasoning: Seedance will not speak ANY CTA line.**
  Now **8 failed generations** across reels B and 2 — the comment CTA, the share
  trigger ("Send this to the person who…") and the link line ("The link is in my
  profile") all fail, returning either generic filler ("The mind is like a wild
  horse…") or phonetic garble.

  Everything else about those chunks checks out, so the CTA is the only variable
  left: reference audio transcribes at **1.000**, loudness sits mid-band
  (0.147–0.155 RMS, well above the 0.048 failure threshold), and length is not
  it either — a 14s non-CTA clip passed while a 13s CTA clip failed twice.

  **Do not burn credits re-rolling it blind.** Doing so cost ~$5.60 on
  2026-07-26 alone. Keep CTAs out of the spoken script; they go on screen. If a
  chunk must contain one, re-cut the chunk to exclude that sentence first —
  `voice_*.mp3` already holds every sentence, so no new ElevenLabs render is
  needed.
- kie balance was **$4.36** — a top-up is needed before the next batch.
- ⚠️ **`CHARACTER` in `scripts/kie.py:154` is not a cosmetic bug — it is a
  LANGUAGE bug.** It describes "an elderly **Japanese** Zen monk … tatami room
  … shoji screens", and that prompt generated `kaion_rest.png`, the anchor
  image every clip passes as `reference_image_urls`. **Seedance reads the
  character as Japanese and speaks the script in Japanese.**

  Confirmed 2026-07-25, reel 2 clip 2: came back as a faithful *translation* of
  our reference audio — 「心の中に重いものがあれば、静かに受け止め…」 — not a
  misfire. Reel 2 clip 1 failed twice with the same cause part-way: English
  pulled toward Japanese phonetics, which transcribes as almost-words ("The
  Acard Favourite Time Arrow Morve…") and reads as a garbled generation.

  **Fix, already applied:** `SEEDANCE_PROMPT` now asserts "He speaks in English,
  in a calm measured voice." Clip 2 re-rolled at similarity **1.000**.
  Stated positively on purpose — negated objects get generated, so "not
  Japanese" is the wrong shape.

  Cost of finding this: **$7.79** in failed generations. Two dead ends were
  chased first (loudness — ruled out, reference RMS 0.1497 sits inside the
  proven-good 0.05–0.15 band; lead-in silence — tested, made it worse).
  **Diagnose language before loudness when a clip comes back "garbled".**

  The character description is still wrong on wardrobe/setting too (actual
  character is Bhutanese/Tibetan in a courtyard) — fixing that means
  regenerating the anchor image and re-anchoring every clip, so it is deferred.

## Reel 2 — SHIPPED 2026-07-26 at 53.29s, no product bridge

`output/reels/reel_2_MUSIC_C_prelude.mp4` — clips 1–4 only. Posted by the user
as-is. It has the hook, the ritual, the three branches and the absolution, plus
his comment CTA drawn on screen. **It has no spoken close and no link line**, so
it earns reach and comments but sells nothing.

The close was attempted and abandoned after the ~12s-floor discovery cost $4.87.
If it is ever finished, the cheap route is:
- **clip 5 is already paid for** — `sd2_05_DRIFT.mp4`, 13.07s, usable. Seedance
  deleted "Send this to" but kept the rest. Two blemishes: it says "shows you
  the **way**" where the script says "**weight**", and the middle sentence is
  left grammatically orphaned.
- **only the closing clip needs generating** — chunk `63.843–77.136` (13.29s,
  contiguous, no new ElevenLabs render): "It cannot take it off you. Forty years
  taught me to live without it. Everything I know is inside The Quiet Between
  Thoughts. The link is in my profile." ≈$2.87.

## Reel 3 — BUILT 2026-07-30 on a NEW ENGINE (kling/ai-avatar-pro, not Seedance)

`output/reels/reel_3_seven_grains_of_rice_music.mp4` — 78.5s, 6 clips, Chopin bed
at 0.200. Recreates BIG06 (rice/wallet, 210k plays, his best comment rate).
Voice-only variant alongside. Awaiting user review/post.

- **Engine: kie `kling/ai-avatar-pro`** — `image_url` (kaion_rest) + `audio_url`
  (loudnormed chunk) + `prompt`. It lip-syncs the EXACT reference audio rather
  than re-performing it, which kills three Seedance bugs at once: CTA stripping,
  Japanese drift, and the ~12s filler floor. Spoken CTAs are possible again on
  this engine (reel 3 still draws them).
- **Measured cost $0.0748/s** (208cr/13.91s; whole reel 1,184cr = $5.92).
  6/6 clips passed QC first roll. Zero framing drift. vs Seedance $0.205/s at
  ~75% yield.
- Trade-off: softer image than Seedance (visibly), no hand gestures. User
  verdict: "decent, not as good but works".
- Reel 4 planned as engine comparison: fal Kling v2 std ($0.056/s) or
  Wan-2.2-S2V (~$0.03/s, untested face quality). InfiniteTalk ($0.06/s, 10-min
  takes) is the route back to his unbroken single-take format.
- Higgsfield 1-day-unlimited: tested, unusable for talking clips (unlim caps
  Seedance at 5s/fast; 5s ref audio → filler at sim 0.10).

## Reels 4–6 — BUILT 2026-07-30, same kling engine, 5×15–20s chunks each

All three assembled dry + music, in `output/reels/` and `REVIEW/`. Awaiting review.
**Measured $20.08 for the three** (4,016cr; ~$6.69/reel at 87s avg). 15/15 clips
passed QC first roll. kie balance after: **1,350cr ≈ $6.75** — top-up needed
before reels 7+.

- Reel 4 `reel_4_salt_wash` — BIG05 (salt hand-wash, 219k). CTA: date / return.
- Reel 5 `reel_5_old_key` — BIG03 (key under pillow). CTA: "My paths are
  opening" / return after night three.
- Reel 6 `reel_6_words_to_mother` — BIG07 (family vein). CTA: "I love you mom"
  / send-to-mother share.

Pipeline upgrades baked into `assemble_reel.py` on 2026-07-30 (apply to every
future reel):
- **Sample-accurate concat** — kling clips ship audio 0.2–0.3s shorter than
  video; naive concat accumulated 1.08s lip desync by clip 6. Fixed with
  per-clip `apad=whole_dur=<video dur>` inside one filtergraph (residual ≤28ms).
- **De-plastic pass** — `unsharp + noise` grain on video before captions
  (kling skin reads waxy; approved on A/B).
- Kling has no 15s cap → chunks are now 15–20s, 5 per reel (fewer joins).

`REVIEW/KAION_PROFILE_AND_HOOKS.md` holds the @master.kaion profile copy and an
18-hook bank (6 produced, 12 open) — 9 more reels reach the bank-15 launch bar.

## Publishing — @master_kaion, Blotato account id 62904 (cadence reset 2026-08-07)

**Cadence: 2 feed reels/day + exactly 1 story/day.** The story is NEVER that
day's reel — it re-surfaces an older or a not-yet-posted one, so the profile
always shows two different things. Times are random non-round minutes, UTC.

**Captions: hashtags only** (`#monk #wisdom #health #usa`). No disclosure text —
see the AI hard rule above.

Published: **B, 2, 3, 4, 5**. Remaining feed queue:

| day | feed reels (UTC) | story (UTC) |
|---|---|---|
| Aug 7 | 6 words-to-mother 07:52 · 7 19:14 | 13:26 → reel B |
| Aug 8 | 8 08:37 · 9 18:52 | 16:41 → reel 2 |
| Aug 9 | 10 07:41 · 11 19:23 | 12:08 → reel 3 |
| Aug 10–17 | — *(out of reels)* | 4, 5, 6, 7, 8, 9, 10, 11 |
| Aug 18–28 | — | 6, 7, 8, 9, 10, 11, B, 2, 3, 4, 5 |

⚠️ **The feed runs dry after Aug 9.** Every built reel is scheduled; holding
2/day past that needs new reels, which needs a kie top-up.

- 🛑 **STORIES ARE MANUAL, ALWAYS. NEVER SCHEDULE A STORY IN BLOTATO.**
  (User instruction, enforced 2026-08-14: six queued kaion stories were deleted.)
  A story is the ONLY Instagram surface that can carry a clickable link, via the
  link sticker — and the sticker must be added by hand at post time and cannot be
  added afterwards, so an API-posted story is a story with no link. Measured:
  ~40,000 IG reel views produced 0 page views because nothing was clickable.
  The daily file lands in Photos album "KAION STORY EN" via `scripts/story_push.py`
  (**06:00 cron**, user's choice 2026-08-14); the user posts it and attaches the
  sticker. The script now enforces ONE push per lane per day (`last_day` in
  `data/story_push_state.json`) — a manual run on a day the cron already fired
  prints "already pushed today" and does nothing, because two videos in the album
  for one day makes the user guess which to post (happened 2026-08-14). Use
  `--force` only when the Mac was asleep at 06:00 and a second push is deliberate.
- **IG stories cap at 60s**, so stories use 15s teaser cuts —
  **ALWAYS via `scripts/make_story.py`** (48kHz audio conform; the Aug-7 story
  played silent for the user despite a clean 44.1kHz upload — root-cause
  analysis 2026-08-08: file/upload verified byte-identical and audible, so the
  loss is IG-side; RESOLVED same day: it was the app's sticky story-mute
  toggle — user tapped 🔊 and heard sound. Keep the 48kHz conform anyway).
- Re-sharing your own reel to Stories is native IG behaviour and carries no
  penalty; repeating the same video as a NEW FEED post is what looks spammy.

### DM automations — LIVE 2026-08-08 (Blotato cloud, runs with laptop closed)

Every "comment the word X" promise MUST have a delivery behind it. Registry:
`data/dm_registry.json` — check it BEFORE scripting any reel with a comment
CTA; never reuse a keyword for a different freebie.

```bash
python3 scripts/keyword_check.py <keyword>   # exits 1 if taken — RUN BEFORE SCRIPTING, like ledger.py check
```

It checks the registry AND the live Blotato automations, so a stale registry
cannot fool it. A keyword overlap between two active automations would
double-DM every commenter — that is why this guard exists. Live automations (all
posts, comment-received, IG account **63585** — the account was re-added
2026-08-08 for messaging permissions, which wiped id 62904 plus its whole
queue; all rebuilt): 254 home / 255 step / 256 water / 257 link-words / 259
legacy phrases / 258 yes-gift / 263 reel-13 catch-all. Each DM carries the
freebie inline + a Gumroad button. ⚠️ Never delete/re-add a Blotato account:
new accountId, schedules wiped. Created via REST `POST /v2/dm-automations` (BLOTATO_API_KEY in .env;
body needs `target:{targetType:"instagram"}`).

The PUBLIC half ("Sent, my friend 🙏" under the comment) is
`scripts/comment_sweep.py` via macOS **crontab** (every 30 min 9-24 while the
Mac is awake; IG allows replies up to 7 days back, so it catches up after
downtime). Randomized replies, never twice on one comment. All pure-script
routines live in crontab (marked KAION-CRON: sweep, tiktok_rotate,
health_check) — Claude scheduled-task slots are reserved for jobs that need
Claude (only kaion-youtube-pin remains).

### 🛑 THE "YES, POST IT" CHECKLIST — runs automatically on every reel approval

When the user approves a reel, ALL of these happen, no exceptions, no asking:

1. Upload master → schedule via Blotato REST `POST /v2/posts` (accountId
   **63585**, firstComment = Gumroad line, unique hashtag caption, non-round
   UTC minute, max 2 feed reels/day — LIST existing posts first, the Aug-10
   collision happened by skipping this).
2. Create the DM automation for the reel's comment keyword BEFORE the post
   goes live, add it to `data/dm_registry.json`, and record the scheduled
   post's media url under `registry["media"][automationId]` so the binder in
   step 2b can find it.

   🛑 **READ THAT URL BACK FROM THE SCHEDULE, NEVER FROM THE UPLOAD RESPONSE.**
   Blotato **re-hosts** the file when the post is created, so the `publicUrl`
   the presigned upload handed you is NOT the url that ends up on the post.
   Recording the upload url leaves an automation that looks perfectly healthy,
   reports "not published yet" forever, and DMs nobody — the same dead funnel
   2b exists to prevent. Found 2026-08-15 on reels 35/36/37, all three wrong.
   `bind_automations.py` now flags such a mapping as `!! ORPHAN media url`
   instead of quietly queueing it (calibrated on known-bad AND known-good).

   And match a post to its automation on the keyword it DECLARES (`the word X`),
   never on any keyword appearing anywhere in the comment text — reel 37's
   "first practice" otherwise steals reel 33's `practice` mapping. Open-ended asks (name/date/place) get a per-post
   catch-all (keywords []) the same way.

   🛑 **2b. AN AUTOMATION WITH `postId: null` NEVER FIRES. It must be bound to
   the PUBLISHED post id, which does not exist until the post goes live.**
   `17 * * * *` cron runs `scripts/bind_automations.py --apply`, which joins
   scheduled to published on `mediaUrls` and patches the postId in. Do not
   hand-set a postId from `list_posts(status=scheduled)` — that is a SUBMISSION
   id in a different range (3.4M vs 6.1M) and is just as dead.

   Measured 2026-08-15, account 63585: all 9 comment automations carrying a
   published postId had fired (267 alone 28 times); 10 of 12 with `postId:
   null` had NEVER fired. Reel 24 was the proof — two "forgive" comments on
   post 6159515, automation active with a matching keyword, and
   `list_automation_logs(1005)` returned an EMPTY LIST: no failed run, no run
   at all. Automation 263, scoped to submission id `3250679`, is the second
   confirmation — scoped, and equally dead.

   ⚠️ This kills the CROSS-POST catch-alls by design (256 water, 257
   book/link/price/quiet, 264, 271, 272, 273). A keyword that must work on
   every post needs one automation PER post; there is no "any post" mode that
   actually delivers.
3. Ledger: `set <reel> status scheduled --when <ISO>`.
4. Story teaser (`scripts/make_story.py`) queued on a DIFFERENT week than the
   reel, 1 story/day cadence.
5. Remind the user: AI-info toggle in the IG app when it publishes.

**How to write a new freebie practice (the DM body):** the registry holds
every existing practice — read it first, never repeat one. Each practice is
2-4 sentences, one concrete physical act tied to THAT reel's topic (a thing
done with the body at a stated time: touch, write, breathe, place, say aloud),
in Kaion's voice: plain words, no contractions (he learned English late),
warm "my friend", no AI phrasing (writing-style skill applies). Always end
with the fixed tail: "The full thirty days are in my book below. Reply YES
and I will leave you a small gift. 🙏" — the YES funnels into automation 258
(20% code STILLNESS, auto-applied link).

### Measured facts about his CTA (all 62 transcripts)

- "the link is in my profile" close: **62/62 (100%)**
- comment CTA: 61/62 · save: 15/62 · share/send: 7/62

So both CTAs are mandatory in every script — ours already match.

### ⚠️ Kling BURNS ITS OWN SUBTITLES into some generations (found 2026-08-07)

4 of 37 clips in the reels 12–20 batch came back with fake-Chinese or
gibberish-Latin subtitles rendered INTO the pixels (pale serif, lower-middle
band, intermittent — not present in every frame). Discovered only after
assembly; pulled reels 15 and 17 from a batch the user had already approved.
`qc_gate.py` now has a SUBTITLE GATE (edge-density scan of y1150–1650 every 2s,
threshold 0.027, calibrated on this batch: clean 0.008–0.019, text 0.028+).
**It runs as part of the standard gate — a clip that fails it gets re-rolled,
never assembled.** One frame is not enough to clear a clip; the text flickers.
⚠️ QA blind spot found 2026-08-08 (PT batch, 3/9 failed): PERSISTENT burned
text also reads as "uniform density" — the uniform=texture heuristic only
clears a clip when frame INSPECTION confirms no text. Always eyeball frames.
🛑 **SUPERSEDED 2026-08-11 — the "seed follows the audio" rule below is WRONG as
stated, and trusting it cost ~880cr on reel 24.** Held the anchor fixed (a17)
and changed ONLY the audio: failed twice, with the burned text at the identical
baseline and left margin both times. Reel 25 on anchor a18b was clean first
roll, same engine/prompt/session. The anchor carries no latent text. **Real
cause: an EMPTY, LOW-DETAIL LOWER THIRD is read as the place subtitles belong.**
a17 = bare lap over bare floor, band detail 0.0102, failed 2/2. a18b = table +
open book + candle in that band, detail 0.0280, clean. Full write-up with the
methodology lesson (the old rule came from a batch where anchor and audio
co-varied — a confounded inference) in **`output/RCA_BURNED_SUBTITLES.md`**.

**GUARD, run on the 4-credit still and never skip it:**

```bash
python3 scripts/anchor_check.py <anchor_name>   # exits 1 on a flat subtitle band
```

Compose every anchor so the lower third is OCCUPIED — table, altar step, prop,
light source — and state it positively in the prompt. Re-rendering the TTS is
still cheap and harmless, but it is not the fix.

⚠️ ROOT CAUSE NAILED 2026-08-08 (PT rounds 3-4) — SEE ABOVE, THIS IS SUPERSEDED:
the burned-subtitle seed follows
the AUDIO FILE, not the anchor or prompt. The same mp3 reproduced identical
gibberish across 3 different anchors; a fresh ElevenLabs render of the same
script (new waveform) fixed 2 of 3 first try. **After a burned-subtitle fail,
re-render the TTS before re-rolling — never resubmit the same audio.** If it
still fails (PT9), swap the anchor too (outdoor/path scenes seem to pull
watermark priors; candle_dark cleared it).
⚠️ Threshold 0.027 is calibrated for CHEST-UP framing. Full-body shots put mat
weave/robe folds in the band and fail EVERY frame at a uniform density — that
signature (uniform ~0.05+ on all frames) is scene texture, not subtitles;
burned text is intermittent. Verify by eye before re-rolling a wide shot
(reel 23 V2, 2026-08-08).

### ⚠️ CLOSING SCREEN: the originals draw NOTHING (measured 2026-08-07)

Final frames of monkcheen BIG01, TOP10 and yangmunus's 1.25M-play reel all show
ONLY the live subtitle line at the close. The comment CTA is SPOKEN mid-reel
(and subtitled), never a persistent overlay card; nothing competes with the
subtitles at the end. Our top-band CTA + closing card + subtitle triple-stack
on reels ≤20 reads awkward — the user flagged it.
**From reel 21 on: no persistent CTA cards. The comment instruction goes in
the spoken script, like the sources. Reels ≤20 ship as built (user decision:
no re-renders).**

### 🛑 INDEPENDENT DEEP-QA GATE — a SECOND agent verifies every assembled master (2026-08-08)

User found 3 bugs in reel PT5 that clip-level QC missed; a blind adversarial QA
agent then found all 3 plus a 4th. **Rule: no assembled master is "done" until
a SEPARATE agent (not the one that built it) has run this checklist and passed
it. The agent is told defects exist and must rule each category out.
APPLIES TO EVERY MARKET AND EVERY CHARACTER — EN Kaion, PT Mestre, ES Maestro,
and any future account — every reel, every story teaser, every re-roll, no
exceptions (user confirmation 2026-08-08). The user only ever reviews files
that have already passed this gate.**

1. **Full-frame visual sweep** — fps=1 over the WHOLE frame (contact sheets,
   read them all): burned text/watermarks anywhere; anatomy (hands, fingers,
   glasses, teeth); wardrobe/prop morphing (PT5: a hand + stick morphed
   through a closed shawl at 6 timestamps); objects appearing/vanishing.
2. **Caption audit** — band crop at fps=1, read every card: spelling vs OUR
   script (never Whisper's), name "Kaion", junk/hallucinated cards (PT5
   shipped "E assim ficou?" — never spoken), overflow past box or frame,
   caption present during silence / missing during speech.
3. **Audio** — transcript similarity with word-level diff listed (not just a
   number); silencedetect for mid-speech gaps >1.5s; volumedetect; A/V stream
   duration mismatch; clean start/end.
4. **Lip sync** — face crops at ≥6 speaking moments + ≥3 silent ones.
5. **Timing** — no frozen first/last frames, no dead air, doesn't cut mid-word.
6. **Identity** — face/glasses/beard/wardrobe vs the anchor at start/mid/end.

**Gate 0 — QC the TTS BEFORE any video spend, SENTENCE-LEVEL:** ElevenLabs
itself can garble a word (PT2 spoke "transforma a Sabira-casa"; 4 video rolls
of bad audio before it was caught). Whole-file similarity is NOT enough —
0.9933 still contained the garble. Whisper-transcribe every fresh TTS mp3 and
require EVERY script sentence to align ≥0.85 individually; re-render on fail.
ElevenLabs can stumble REPRODUCIBLY on one phrase for one voice — PT2's
"transforma a casa" failed in EVERY render (rounds 4-6); reword the sentence
(meaning-preserving) after 2 fails, don't keep retrying. And the checker must
use EXACT cleaned-substring matching on the affected sentences — fuzzy ratios
(0.85 longest-match) passed a stumble twice because the garble sits at the
sentence tail. AND verify the upload is fresh: `kie.upload` caches URLs in
sibling `.url` files — a stale cache silently resubmitted round-4's garbled
audio through rounds 6-7 (1,280 cr wasted). Fixed with an mtime check
2026-08-08; if audio QC passes but the rendered video still carries an old
defect, suspect the upload cache first.

Closed-wardrobe anchors (shawl) invite hand-morph artifacts — prompt must
POSITIVELY place the hands ("both hands resting hidden beneath it") just like
the lower-frame line guards against burned subtitles.

### 🛑 CAPTION GATE — QA the ASSEMBLED master, not just the raw clip (2026-08-08)

QC on raw kling clips is not enough: a PT test render shipped with "hhhhh…"
drawn across the whole width because Whisper transcribed a breath and the
assembler drew it verbatim, and PT1's first master said "Mestre Kayon"
(Whisper's spelling). Rules, all baked into `assemble_pt.py` and owed to any
future assembler:
- **Caption text comes from OUR script, never from Whisper.** Whisper supplies
  timings only; words are difflib-aligned to the script (align_to_script), so
  spelling is guaranteed and hallucinated tokens drop out.
- **Safe zone:** caption box max 940px wide on 1080; font auto-shrinks. Never
  edge-to-edge text.
- **Contrast:** Arial Bold 60, black box at alpha 230, 2px black stroke on the
  text (user: "his are way more contrasting", 2026-08-08).
- **Font size is FIXED for the whole reel — never auto-shrink per card** (user
  flagged size jitter 2026-08-08). Fit is guaranteed the other way round: lines
  are wrapped by MEASURED pixel width at the fixed size (wrap_px), and the cue
  builder closes a cue rather than let it need a third line.
- **After EVERY assembly: extract the caption band (fps=1, crop 1080x400 at
  y1250), build a contact sheet, and READ it** — checking wording, spelling,
  overflow, junk. A master is not done until its contact sheet has been eyeballed.
- Cue text is also written to `assets/cues_<id>.txt` for a cheap text-level diff.

### Music for PT (TikTok-first)

"Moment Of Reflection" (Jhonatan Rodrigues/Piano Sky/Dee Piano) is a commercial
release, NOT royalty-free. Legal only via the in-app music pickers (TikTok/IG),
covered by the platforms' licenses. **Never bake it into a file with ffmpeg.**
Masters stay dry; sound is added per-post in the app.

### 🛑 MANDATORY before recreating any source video: WATCH IT, all frames

Transcripts lose the visual half of what made it work. Before scripting or
generating, download the source video and read a dense frame grid END TO END
(12+ frames spanning the full duration, not 2 screenshots), and note: posture,
framing (full-body vs chest-up), setting, light, wardrobe, watermark, subtitle
placement, what's on screen at the close. The 8.3M monge.yang reel turned out
to be FULL-BODY seated on a mat — every assumption from the transcript alone
had it wrong (established 2026-08-08, one ~300cr render half-wasted).

### 🛑 ONE render per script — never A/B two video generations of the same script

Composition questions are settled BEFORE spending video credits: frame-grid the
source, generate the 4-credit anchor still, judge it, THEN submit once. A
render found to be off-format mid-flight is finished and repurposed (story
teaser), never duplicated. Only QC failures justify a re-roll. (User rule
2026-08-08 after reel 23 was rendered twice, ~$1.50 wasted.)

### ⚠️ ANCHOR RULES from the PT batch review (user, 2026-08-08) — all monks

- **Anchor faces must be NEUTRAL, relaxed, mouth closed — NEVER smiling.**
  PT8's anchor (pt_a4_low_table) has a soft smile; kling keeps snapping back
  to the anchor expression between phrases, so the mouth oscillates into a
  full toothy grin mid-sentence every few seconds (confirmed at 25-32s on a
  5fps mouth-crop scan). Prompt was identical to the clean reels; the anchor
  expression was the only variable. Check every new anchor's mouth before
  accepting it (the 4cr still is where this is caught, not the 600cr video).
  **QA implication: expression defects are INVISIBLE at 1fps** — each frame
  alone looks like plausible speech. The deep-QA gate must include a 5fps
  MOUTH-CROP sweep (crop the mouth region, tile, read the sheets) looking for
  expression oscillation/grin spikes, not just per-frame anatomy.
- **No standing full-body anchors for talking takes.** PT6 (pt_a6_dirt_path,
  standing) produced a step-forward/step-back sway loop over 80s. Seated
  anchors never sway. If a standing shot is ever required, prompt feet
  POSITIVELY ("he stands perfectly still, feet planted, weight settled") and
  treat it as high-risk.
- Slight body motion is DESIRABLE (PT5-style statue-stillness reads uncanny
  too): keep "small natural head movements, subtle micro-expressions" and add
  "his shoulders rise gently as he breathes" — but never hands/steps.
- Reels ≤PT10 ship as reviewed (user decision: no re-renders).

### Motion-quality prompt lines (web research 2026-08-08 — use from next batch)

Distilled from Kling 3.0 / avatar prompting guides (fal.ai, veed.io) + our own
batch findings. The avatar prompt's MOTION portion should be **20–40 words**,
never redescribe what the anchor image already shows, and state BOTH what moves
and what stays still — all positive phrasing (negations get generated):

> He sits perfectly still, weight settled. His shoulders rise gently as he
> breathes. Small natural head movements, subtle micro-expressions, gentle
> blinking. His hands rest calmly [hidden beneath the shawl / folded in his
> lap]. As he finishes speaking, he settles into stillness.

- The closing "settles into stillness" line gives the clip a temporal end-state
  — guides against loop-like sway (fal: describe progression, not a pose).
- Anchor motion to the speech: "he speaks in English, in a calm measured
  voice, unhurried" stays in every prompt (also the language guard).
- Keep restrained: Kling handles minimal-movement performances best; more
  motion verbs = more artifacts. One render per script still applies — test
  this block on the next PAID batch's first anchor+clip, never a dedicated
  test render.

### Visual format of the originals (frame grids, 4 yangmunus reels, 2026-08-08)

- **One pose/setting per reel, held for the whole take — variety lives BETWEEN
  reels** (sofa at night, bridge, temple table, courtyard). So: rotate the
  anchor image per reel; never expect pose changes inside one.
- **Only the live subtitle bubble is ever on screen** — no top band, no cards.
- **Comment asks are ONE WORD** ("peace", "amen", "rest") + a delivery promise
  ("comment peace and I will send you something powerful"). Never multi-word.

### Engine: kling/ai-avatar-standard is the default from reel 16 on

$0.0383/s measured (288cr/37.6s) — 49% under pro. 720x1264 native, upscales
fine; single takes up to 37.6s+ proven; transcript 1.000; subtitle gate clean.
No joins = no face reset.

### Two defects observed on review, with the lessons

- **Reel 3 face/light drift between clips.** Kling regenerates the face from
  the anchor still on every clip, so identity and lighting reset at each join;
  alignment cannot fix it (framing was already perfect). Mitigations: fewer,
  longer clips (reels 4–6 at 5×17s look steadier than reel 3 at 6×13s), and a
  higher-resolution anchor. InfiniteTalk's 60–80s single takes would remove
  the joins entirely.
- **Reel 6's long pause before "Not even love".** The tiler opened a chunk
  with that short fragment, so ~0.6s of kling head-silence stacked on the
  natural sentence gap. **Rule: never start a chunk with a short punch-line
  fragment** — keep it glued to the sentence it completes.

## Reel 2 source brief (kept for reels C/D)

Recreate **BIG01** — https://www.instagram.com/p/DVZg8wAkYgk/ — 4,047,769 plays,
19,077 comments. His single best asset and topic vein #1.

**Keep the hook verbatim:** *"Place a glass of water beside your bed tonight.
Tomorrow morning you will understand why."*

Write to the **45s compression** in SOP Part 2 (cut beats 2 and 5, two branches
not four, never cut the absolution). ≈115–130 words.

### ⚠️ REVERSED 2026-07-25 — do NOT reuse the close. Write it every time.

An earlier version of this file said his closing beat was "boilerplate in all six
BIG transcripts" and concluded that `output/assets/seedance_07.mp4` could be
appended to every reel, saving ~$2.50 and a re-roll. **That reading was wrong.**
Measured across all 7 BIG transcripts:

| element | recurrence |
|---|---|
| "The link is in my profile." | **7/7 verbatim** |
| "everything I know is inside \<PRODUCT\>" | 6/7 |
| "over 20 years… in silence" | 6/7 (absent in BIG05) |
| **the pivot sentence before it** | **7/7 distinct** |

His close is a **fixed tail with a written head**. The pivot always names that
reel's own topic — BIG01 "tired of needing rituals every time something feels
heavy", BIG05 "a ritual cleans the path, but what truly opens it is the inner
work", BIG08 "go beyond a recipe… calm your body and mind from the root". He
even varies the product name: BIG07 sells "the path back to calm".

So the rule is:

- **Invariant, never vary:** "Everything I know is inside \<PRODUCT\>. The link
  is in my profile."
- **Write fresh every reel:** the pivot before it, naming the tactic the viewer
  just watched and its limit.
- The "over 40 years in silence" credential is optional — he drops it in 1 of 7,
  and at 45s it is the first thing to cut (same logic as cutting beat 2).

Appending `seedance_07.mp4` would also end two consecutive posts with the same
twelve seconds — identical words *and* identical picture, since it is one file
rather than a re-performance. Reel B is already published with it. Repeated
*copy* is survivable; a repeated *file* is a different defect.

There is no economy in it either: re-rolling the old close bills exactly what a
new one bills ($0.205/s — no discount for repetition). So a 45s cut is **4 clips
to generate, not 3**.

## ⚠️ RESOLVED — Seedance DOES bed some generations

**Confirmed 2026-07-25 on `seedance_08.mp4`** (heard at ~1:19 of the Reel B
master; clip 8 occupies 74–84s in clip order 1·2·3·4·5·8·7).

Its quiet frames carry **A2 (109.8Hz), A3 (220.0Hz) and D4 (293.8Hz)** — exact
note frequencies, an octave plus a perfect fourth. A chord. The control clip 3
shows energy only at 85–99Hz, which is male vocal fundamental and nothing above.

**So "voice on silence" is only sometimes true.** It is per-generation, not
global — 1 of 8 clips in this reel.

### Detect it by SPECTRUM, not by level

A noise-floor test does not find this: clip 8 measured 0.95% of peak, quiet
enough to look like room tone, and it was dismissed as exactly that. A soft
drone and soft hiss score almost identically on amplitude and completely
differently on spectrum. **Add to the QC gate (SOP Part 3 Step 5): FFT the
quietest ~25% of frames and check for sharp partials landing on note
frequencies.** Broadband = clean; a harmonic stack = bedded, re-roll it.

Do NOT prompt "no music" to fix it — negated objects get generated in these
models ("no tripod" produces tripods). Describe what IS there: "only his voice,
quiet courtyard ambience".

Do NOT prompt "no music" to fix it — negated objects get generated in these
models ("no tripod" produces tripods). Describe what IS there: "only his voice,
quiet courtyard ambience".

### Account-safety evidence base (researched 2026-08-08, user request)

All our automation rides Meta's official Graph API surface (via Blotato):
scheduled posts, comment replies, keyword-triggered DMs, and one-time private
replies to comments (Meta policy: max 1 per comment, within 7 days — exactly
what dm_backfill.py sends; official cap 750 private replies/hour, we send
single digits/day). Industry sources consistently attribute shadowbans to
UNOFFICIAL automation — browser bots, like/follow automation, engagement pods,
unapproved API tokens — not to API-partner scheduling or API DM flows, which
Instagram explicitly supports. Our stack has zero browser automation on the
accounts, Apify scrapes are public-data read-only (no login/cookies), TikTok
is manual forever. Residual honest risk: Blotato's Meta-partner status is not
independently verifiable in the partner directory; mitigations already in
place = the morning-board RED tripwire (pause Blotato, post manually 2 weeks)
and tiny volumes. NEVER add: follow-triggered DMs, mass DMs, engagement
automation, or any unofficial-API tool.

### Posting-channel policy (decided 2026-08-08, evidence-based)

IG feed+stories stay on Blotato: our own board proves distribution is healthy
under API scheduling (1,940/1,207/683 plays). The TikTok shadowban research
indicts TIKTOK's API + unlabeled AI, not IG scheduling. TikTok stays manual
forever. TRIPWIRE: if kaion IG goes red on the morning board (3+ of last 5
posts under 10% of account median), remediation step 1 = pause Blotato and
post manually for two weeks. Blotato's "warm up before connecting" warning
applies at connection time only — already behind us.

## Session 2026-08-08 — state snapshot (read this, it supersedes older tables)

- **Engine default: kling/ai-avatar-standard** ($0.0383/s measured, 720x1264,
  single takes, QC verbatim). kie balance ~9,400cr ≈ $47 after top-up.
- **Scheduled (all in ledger):** reels 16+22 → Aug 13, reel 23 → Aug 14
  (feed had a collision on Aug 10 from the 12-20 batch — always list Blotato
  posts before picking slots). Stories 23-v1 → Aug 20, 23-v2 teaser → Aug 21
  (mix-and-match rule: a reel's own story runs a different week).
- **Reels 22/23** recreate monge.yang's 3.5M house-blessing and 8.3M comfort-
  trap (hook verbatim, translated). Sources in ledger as TTym….
- **Anchor bank a1-a15** in output/assets/anchors/ — one anchor per reel,
  never consecutive repeats, match source camera distance, REALISM keyword
  constant in kie.py goes in every image/video prompt.
- **DM funnel LIVE end-to-end** — see the DM automations section above +
  data/dm_registry.json. Gumroad code STILLNESS (20%) created and verified.
- **Profile:** bio rewritten (name field "Master Kaion | Monk Wisdom &
  Healing"), 3 highlights posted by user (Begin Here / Wisdom / Rituals),
  highlight stills in iCloud KAION_HIGHLIGHTS + Photos album.
- **TikTok:** day's video auto-imports to Photos album "KAION TIKTOK"
  (tiktok_rotate.py); user swipes to delete after posting (no delete API).
- **Cron (KAION-CRON in crontab):** comment_sweep every 30min, tiktok_rotate
  12:07/18:07, health_check 09:05. Claude scheduled task: only
  kaion-youtube-pin remains.
- **Story audio "bug" resolved:** it was IG's sticky story-mute toggle.
  Stories now built via scripts/make_story.py (48kHz conform) anyway.
- **Money plan (user-approved direction):** 2 accounts × 2 reels/day × 60
  days ≈ $450-500 all-in. Second account = SPANISH (translate our proven
  catalogue, ~$1.53/reel re-render; RO rejected: 1/10th market). Kill gates:
  day-30 median <1k views AND no post >50k → change structure; day-60 no
  outlier >250k AND <5 sales → kill worse account. Break-even ≈ 9-10
  sales/mo/account ≈ 230k views/mo. Next actions pending user: Spanish
  account setup, daily manual TikTok posting.

## Kill gates — agreed 2026-08-08, day 0 = Aug 3. DO NOT move these.

- **Sep 7 (day 30):** continue as-is only if ≥1 of: a reel >50k · median >1k ·
  1,000 followers · 1 sale. Else force structural change (hooks/market/niche),
  not more of the same.
- **Oct 7 (day 60):** kill the account unless ≥1 of: outlier >250k · 5+ sales ·
  3k followers with rising weekly median.
- **Nov 3 (day 90):** model dead across ALL accounts if: no 250k outlier ever
  AND <10 lifetime sales AND no account >3k followers. Take the machinery to a
  new niche.
- Zero sales alone is NOT failure below ~500k cumulative views (funnel math:
  ~$6/10k). A single >250k outlier resets the 60-day clock.

## Still owed

Reels C and D · side-by-side of his top 3 vs ours · hook bank (15+) ·
transcribe the remaining ~205 of 266 videos · `@master.kaion` profile copy.

## PT product funnel — LIVE 2026-08-08

- **Product:** O Silêncio Entre Pensamentos: Um Retorno de 30 Dias à Quietude
- **URL:** https://mestrekaion.gumroad.com/l/silencio · gift code **QUIETUDE** (20%)
- Separate Gumroad storefront `mestrekaion` (same account/payout, own profile,
  PT bio and Mestre avatar) so PT buyers never see the EN monk.
- Tiers: Livro (PDF) $9.95 · Livro + Audiolivro $16.95. Priced under EN on
  purpose for the BR market (Gumroad no longer offers PPP discounts).
- Assets in `output/book/`: `O_Silencio_Entre_Pensamentos.pdf`,
  `O_Silencio_audiolivro.zip` (full 47min + 4 week files), `gumroad_cover_pt.png`,
  `cover_wide_pt.png`, `pt_days_*.json` (source of truth for BOTH pdf and audio).
  Build: `scripts/build_book_pt.py` + `scripts/build_audiobook_pt.py`.
- PT audiobook voice = `EL_VOICE_PT`, the same voice as the PT reels.
- ⚠️ PT reels PT1-PT10 have NO spoken product close (written before the page
  existed). New PT scripts get one; no re-renders of PT1-10.

### YouTube pinned comments — automated, both channels

`kaion-youtube-pin` scheduled task, **09:10 and 20:10 local, max 5 videos per
run**. YouTube's API can insert comments but has **NO pin method** (verified
2026-08-08 in Google's docs), so pinning is browser automation — twice a day
is the agreed ceiling to stay clearly inside normal use. The task looks back
**30 days**, not 24h, so a Mac that was closed for days catches up
automatically; `data/youtube_pins.json` is the authority on what is done and
prevents double-commenting. EN videos get the `/l/quiet` line, PT videos the
`/l/silencio` line, each in its own language.

## Product funnel — LIVE 2026-08-08

- **Product:** The Quiet Between Thoughts: A 30-Day Return to Stillness
- **URL (the bio link):** https://masterkaion.gumroad.com/l/quiet
- Tiers: The Book (PDF) $14.95 · Book + Audiobook (George, 41.1 min) $24.95
- Assets in `output/book/`: PDF, TQBT_audiobook.zip (full + 4 week MP3s),
  gumroad_cover.png (square thumb), cover_wide_1_main / 2_audiobook (page covers),
  manuscript.json (source of truth for the text), build via
  `scripts/build_book.py` + `scripts/build_audiobook.py`.
- ⚠️ **ffmpeg concat: the silence spacer must match the chapters' codec,
  sample rate and channel layout** (mp3/44100/mono here). A `.wav` spacer
  between mp3 chapters is SILENTLY DROPPED — the PT audiobook's first
  assembly came out 61s short with every chapter running into the next
  (2026-08-08). **Always assert total duration == sum(parts) + gaps after
  assembling**; `build_audiobook_pt.py` now fails the build on >2s drift.
- Audiobook recipe: eleven_multilingual_v2, George, one chunk per day
  (~180-280 words), previous_request_ids stitching, <break> tags in-chunk,
  ffmpeg concat with 1.8s gaps between days. Do NOT regenerate whole book for
  small fixes — re-roll the single day chunk and re-concat.
- The spoken close in every reel ("Everything I know is inside The Quiet
  Between Thoughts. The link is in my profile.") now points at a REAL page.
- User-side steps that complete the funnel: publish button on Gumroad, IG bio
  link, pinned comment on each YouTube video.
