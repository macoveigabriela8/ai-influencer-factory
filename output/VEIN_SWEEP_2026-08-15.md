# VEIN SWEEP — what to produce next, and why not by play count

**Run 2026-08-15.** Selection input for the reels between now and the Sep 7 gate.
Method and caveats are in here on purpose: the last two selection rules this
project trusted both turned out to be artifacts.

## The question the operator asked

> "we need to find their top videos right? so pick from best performant ones?"

**No — and this is the belief the council already invalidated.** Ranking sources
by play count is ANTI-correlated with our results: monkcheen's 718,914-play "My
Story" became our reel 13 and returned 222 views. Our single hit (reel 7,
**55,800 views**) came from a source with 580,071 plays but an unremarkable
**0.121% comment rate**.

Play count measures how well the ALGORITHM served the original account. It
carries no information about whether the script works when a 605-follower
account says it.

## What the corpus can actually support

| corpus | posts | usable topic signal |
|---|---|---|
| monkcheen | 271 | **62 transcribed** (23%) — captions are hashtags only |
| yangmunus | 200 | **183 have real captions** (92%) — topic readable without transcription |

Vein split across the 62 monkcheen transcripts we hold:

    health 43  ·  family 6  ·  ritual 4

**The family/identity vein is effectively exhausted on the monkcheen side** —
6 posts, 3 already produced, and one of the remaining 3 is a keyword
misclassification (a potato-under-the-bed ritual that merely mentions a sick
relative). We cannot select well from monkcheen because **209 of 271 posts have
no transcript**. That is now the binding constraint on selection, not taste.

**So this sweep ran on yangmunus captions instead.** 64 posts above 20k plays
carry a real caption; 8 are family/identity and unused.

## Ranked by COMMENT RATE, not plays

| c-rate | plays | comments | shortcode | topic |
|---|---|---|---|---|
| **1.534%** | 957,803 | 14,692 | `DVEI18AgH7h` | Never start your morning without saying these four things to yourself |
| **0.913%** | 430,140 | 3,927 | `DVOYptXAOH3` | Never end your night without saying these 4 things — "comment *peace*" |
| **0.893%** | 325,458 | 2,905 | `DVoddAyEZMc` | "write the word *truth* in the comments" |
| 0.421% | 118,956 | 501 | `DVTjXxgAL6R` | When you are building something sacred, silence becomes your shield |
| 0.079% | 130,017 | 103 | `DWZS_NVAO7J` | If you are in your 40s, 50s or 60s and you don't feel like yourself |
| 0.073% | 200,527 | 147 | `DUOfzG7D0H1` | If you don't force yourself to improve, nothing in your life will |

All five checked against the ledger: **every one is FREE.**

Ranking the same list by plays reorders it materially — `DUOfzG7D0H1` is 3rd by
plays and 6th by engagement, a 12× difference in comment rate. That gap is the
whole argument for the change of metric.

## Why the top three are the pick

They are not merely high-engagement. **They are comment-instruction posts** —
the script itself says "comment *peace*", "write the word *truth*". The high
comment rate is the CTA mechanic working, not an accident of topic.

For a funnel measuring **0 sales against 62 DMs**, a script whose native
behaviour is to generate keyword comments feeds the exact machinery that is
currently starved. It is the only vein in the corpus that improves the funnel
and the reach at the same time.

Nos. 1 and 2 are a **matched pair** (morning / night, four things each), which
gives a series rather than two unrelated posts.

## ⚠️ A finding worth recording on its own

`DVEI18AgH7h` (957k plays, 14,692 comments) is **the same script as our reel
12**, which we built from monkcheen's `DVpPFVSDIPj` — **27,450 plays**.

The identical topic exists on both accounts with a 35× spread, and we picked the
weak one. This is what "cross-account proof beats single-account plays" means in
practice, and it is the first concrete instance we have measured. When a script
appears on two accounts, produce the version that carries the engagement, and
check both before choosing.

## Honest limits of this sweep

1. **c-rate is better-motivated than plays, but it is not validated on our own
   outcomes either.** Our n of hits is 1, and reel 7's source scored 0.121% —
   this ranking would not have picked it. Treat the top three as the best
   available hypothesis, not a proven rule.
2. **Caption text is not the script.** yangmunus captions state the hook but not
   the body; each pick still needs its source video watched frame-by-frame
   before scripting (CLAUDE.md mandatory rule).
3. **The keyword vein classifier is crude** — it put a potato ritual in "family"
   because the transcript mentions a sick relative. Read the hook, do not trust
   the label.
4. **The real unlock is transcription.** 209 untranscribed monkcheen posts is
   where the unexploited family-vein material is, if it exists. Until that is
   done, selection is limited to what yangmunus happens to caption.

## Recommendation

Produce in this order, one variable at a time, ledger-checked before each spend:

1. `DVOYptXAOH3` — night version, pairs with our published reel 12, own keyword
2. `DVoddAyEZMc` — "truth" keyword, clean single-word comment ask
3. `DVEI18AgH7h` — the morning original, **only as a deliberate re-make** of
   reel 12's topic from the strong source; note the topic overlap in the ledger

Then re-read at the Aug 22 funnel checkpoint before committing further spend.

---

# ADDENDUM — transcription attempt, same day

## The 209 are BLOCKED, and not by anything we can decide

Asked to transcribe the remaining 209 monkcheen posts. Both media routes are
closed:

| route | state |
|---|---|
| stored `videoUrl` in our JSON | **403** — signed CDN links, expired. Verified dead across `monkcheen_full`, `monkcheen_raw` and `yangmunus_posts` |
| Apify | **$29.035 spent of a $29.00 cap.** Cycle resets **2026-08-28** |
| yt-dlp anonymous | Instagram returns an empty media response and demands cookies |

**yt-dlp with the operator's cookies is not an option and was not attempted.**
"Never touch Instagram from the user's session" exists to protect the account,
and a rule that only holds when it is convenient is not a rule. The 209 wait
for the Apify reset on **Aug 28** — which lands after the Aug 22 funnel
checkpoint, so it does not block the next decision.

## What was free: 14 local videos, now transcribed

`data/competitors/videos/` held 19 files from earlier sweeps. 14 transcribed
(2 have no audio stream, 3 were already done) via
`scripts/transcribe_sources.py`. **This is high-value precisely because these
posts carry hashtag-only captions — their topic was invisible until now.**

### Newly readable, NOT yet produced

| c-rate | plays | shortcode | vein | hook |
|---|---|---|---|---|
| **1.534%** | 957,803 | `DVEI18AgH7h` | ritual/self | Never start your morning without saying these four things to yourself |
| **0.264%** | 461,853 | `DT5MoDUAL6D` | identity | The fastest way to ruin a good thing is to talk about it too early |
| 0.226% | 1,253,259 | `DWTvDFEAJOg` | ritual | Place a glass of water beside your bed tonight |
| 0.210% | 546,802 | `DWtswbNAPLL` | health | That pain in your back and hips may not be sciatica — your kidneys |
| 0.099% | 463,656 | `DUGvah-D6fy` | identity | The next time you feel excluded, when people forget your name, let them |
| 0.086% | 647,575 | `DUgihUwj4MU` | identity | Staying home too long does not make you rest |
| 0.086% | 551,183 | `DT-rhe0AEEe` | identity | Be patient when you are becoming someone you have never been |
| 0.071% | 669,682 | `DYCp-ZaALOi` | health | We were never supposed to eat three meals a day |

### Two cross-account confirmations worth keeping

- **`DWTvDFEAJOg` is yangmunus's single biggest post (1.25M) and it is the
  glass-of-water script** — the same one monkcheen ran to 4.05M and we built as
  reel 2. Three accounts, three outliers, one script. That is the strongest
  cross-account signal in the corpus.
- **`DUgihUwj4MU` (647k) is the comfort-trap script** we already built as reel
  23 from monge.yang's 8.3M version. Third account carrying it.

Both shortcodes are ledger-FREE, but the **topics** are used. The ledger guards
shortcodes; it cannot guard topics. Check the topic by hand before scripting.

### Three genuinely new identity-vein candidates

`DT5MoDUAL6D`, `DUGvah-D6fy` and `DT-rhe0AEEe` were invisible to every previous
sweep because their captions are hashtags only. All three are second-person
identity statements with no ritual instruction — structurally the same shape as
reel 7, our only hit.

## Revised recommendation

The earlier top three stand, with `DT5MoDUAL6D` promoted into contention: at
0.264% it is the **best-engaging identity-vein script in the corpus that has no
comment instruction in it**, which means the c-rate is coming from the topic
rather than from a CTA. Adding our own comment ask to it should compound rather
than substitute.
