# Handoff — state as of the Flow Agent Mode test run

## The blocking finding: Agent Mode cannot produce a continuous take

An 18-clip Agent Mode run was generated and inspected. The clips do not cut
together. Between segments: the background shifts, the camera distance changes
(the space under the desk is visible in some clips and not others), the framing
moves, and a few clips land in an entirely different room.

This is not a prompt defect. Flow/Veo is **text-to-video**: it re-imagines the
scene from the prose on every segment, and Agent Mode fans those segments out
independently. A written description cannot pin a camera to a fixed distance --
"medium close-up" spans every framing we saw. Sixteen generations from one
paragraph give sixteen plausible rooms.

Measured against the target: his reels have **zero scene cuts across ~150s** with
identical framing throughout. That is the signature of an **audio-driven avatar
engine** -- one still image plus the full audio, animating a single frame end to
end. The background cannot drift because it is never regenerated.

**Continuity must be enforced in pixels, not prose.** Two architectures do it:

  a) animate one still for the whole duration (the room is a constant)
  b) chain generations, seeding segment N+1 from the LAST FRAME of segment N

`scripts/fal_avatar.py:189` already implements (b). Agent Mode does neither.

### The three options, undecided

  1. **Extend-chaining inside Flow.** Use the `+` extend control so each 10s clip
     continues from the previous frame rather than from the prompt. Same credit
     cost, already paid for, but sequential and manual, and drift accumulates
     over 16 links. UNTESTED -- this is the cheapest next experiment.
  2. **Audio-driven avatar.** Correct by construction. OmniHuman 1.5 @720p was
     priced at EUR 21.19/reel, which is EUR 1,270/mo at 2/day -- not viable at
     the planned cadence. Kling ai-avatar standard was EUR 5.60/reel but was
     rejected on gesture quality (see the header comment in fal_avatar.py).
     Cheaper audio-driven engines have NOT been surveyed. That survey is
     probably the highest-value open task.
  3. **Accept cuts.** Rejected: the unbroken take is the measured format.

## Second finding: negated objects get generated

Roughly 5 of 18 clips contained a camera on a tripod, despite the Set block
saying "no camera, tripod or filming equipment anywhere in frame at any point."
Naming a forbidden object plants it. This is the third time suppression-overshoot
has bitten this project.

Fixed in `scripts/flow_prompt.py` by describing what IS present instead, so there
is no vacancy to fill:

    - The space between him and the camera is completely empty. The floor in
      front of the table is bare, plain and unfurnished, and nothing at all
      stands on it.
    - The only objects anywhere in the frame are the table, the sutra lying on
      it, and him.

UNVERIFIED -- regenerated into all three prompt files but not yet tested.

## Voice pace

The bound voice is NOT a clone: it is the Flow preset **Sadaltager** with a
"Customize Performance" free-text field, so pace is promptable. Earlier worry
about needing to re-clone is retracted.

The voice picker also exposes **Sample Dialogue + Preview**, which is a FREE test
rig -- pace can be iterated at zero credits before committing any.

Calibration sentence (22 words, 113 of the 120 allowed characters):

  "Place a glass of water beside your bed tonight, and in the morning you will
   understand exactly why I asked you to."

  7.3s = 180wpm | 8.2s = 162wpm (his pace, ship it) | 9.4s = 140 (retime 1.15x)
  11.0s = 120 (too slow) | >12.6s = beyond the 1.40x cap

`DELIVERY` in flow_prompt.py was rewritten to anchor on a checkable quantity
("each 10-second segment must contain about 27 words") rather than an
unfalsifiable wpm number, and its negations were changed to negate artifacts
(stretched vowels, trailing off) rather than qualities ("not slow"), which have
an opposite to overshoot into.

`assemble.py` MAX_STRETCH was raised 1.20 -> 1.40. The old cap was the threshold
for MUSIC; speech tolerates far more. What breaks first is the VIDEO -- setpts
speeds up blinks and gestures by the same factor, and a monk blinking 1.4x too
fast reads as nervous. A large retime is also a budget signal: Flow bills per 10s
segment, so a 26% slow read is a 26% credit overrun.

## Watermark

His reels are **clean** -- the bottom-right corner of his 4.0M-view reel was
sampled at 1s/40s/100s/145s and carries no visible mark. Flow output on the
current plan does carry one. Whether Ultra exports watermark-free is UNVERIFIED
and should be confirmed BEFORE subscribing, since it is a second independent
reason to be on that tier.

SynthID (the invisible mark) stays regardless. It is imperceptible and has no
effect on ranking; no attempt should be made to strip it.

## Flow settings

Agent settings must be: **9:16** (was 16:9 -- would have wasted the whole test),
**1x** variants for cheap tests, and **Confirm before generating: Always** (Agent
Mode fires 16 generations from one paste = 240 credits with no checkpoint).

The top model dropdown is the IMAGE model (Nano Banana 2); the bottom is the
VIDEO model (Omni Flash / Veo 3.1 Lite / Fast / Quality). Per-model credit costs
are UNKNOWN -- read the number on the confirmation dialog for the first segment.

## Character

Reference image `output/assets/candidates/v7_interior_skin.png` (4 kie credits,
768x1344). Character Info field is descriptive, not generative -- it is labelled
"Describe how your character acts..." and feeds the Agent. The uploaded portrait
survives it. The character still needs a name (was "Untitled Character").

## Still open from the original brief

  - Virality scoring rubric + `output/SCORING.md` -- never built
  - Side-by-side comparison of his top 3 vs ours
  - ~204 of 266 videos still untranscribed (the 11 hits vs 255 misses natural
    experiment)
  - Hook bank (15+) and script generator
  - Reel D from the #3 breakout (x61, 580k, "your first daughter is always going
    to be more like her father")
  - Whether a single bad segment can be regenerated for 15 credits or the whole
    reel re-runs for 225 -- a 2x swing on the entire launch budget
  - `@master.kaion` IG account -- the user must create this themselves

## Engines already ruled out (do not re-check)

| Engine | Verdict |
|---|---|
| Google Flow / Veo (any tier) | wrong architecture -- 10s cap, text-to-video, cannot hold continuity |
| OmniHuman 1.5 @720p (fal) | correct architecture, EUR 21.19/reel = EUR 1,270/mo at 2/day |
| Kling ai-avatar standard | correct architecture, EUR 5.60/reel, rejected on gesture quality |
| Arcads.ai | correct architecture, but **120s max length** (our reels are 143-159s, his median 143s, zero of 266 posts under 60s) AND ~$11/finished video = $660/mo AND custom actor from own headshot is gated to a top plan reported near $385/mo |

**Lesson from Arcads:** packaged UGC products bill per finished video because they
sell the workflow. We already own the workflow (kie.py, subs.py, assemble.py) and
only need inference. Search for RAW MODELS ON PER-SECOND APIs (fal.ai, kie.ai,
replicate), not packaged products.

**Target to beat:** under ~EUR 4/reel for ~150s of continuous image+audio avatar,
with acceptable hands. At 60 reels/mo that is ~EUR 240/mo; at the recommended
~1.5/day cadence (44 reels) it is ~EUR 175/mo. Break-even on his $14.95 product
is ~12-16 sales/month at that spend.
