# Virality Scoring Rubric v1.0

## What this measures — and what it does not

This rubric scores **how completely a script implements the patterns that separate Monk Chen's hits from his flops.** Every criterion and its weight is derived from the measured contrast in `VIRALITY_ANALYSIS.md`, not from intuition.

**It is a process score, not a prediction.** A 95 does not mean "this will get 4M views." His top 3 are the 99th-percentile tail of 271 attempts, and a large share of their reach came from a cold-start boost that no script can manufacture. What the rubric does is raise the probability of a tail event and eliminate the failure modes that guarantee a flop.

### v2.0 — what changed and why

**v1.0 gave diagnostic branching the single largest sub-weight (10 pts) on the basis of a "64% of hits, 0% of flops" split. That finding did not replicate.** Re-tested across 61 transcripts with one consistent measure, branching shows `r = −0.066` against log plays and runs slightly the *wrong* way in the hits-vs-flops comparison. The weight has been cut from 10 to 6, and it is now justified as **craft** (it demonstrably structures retention) rather than as a measured predictor.

Those 4 points moved to **D2, topic stakes**, which absorbs the best-supported qualitative finding in the dataset: his hits are identity content (death, grief, family, destiny) and his flops are commodity health recipes.

**Be clear-eyed about what this rubric now is.** The honest result of the analysis is that *within his catalogue, script mechanics barely predict performance — timing dominates* (`r = −0.559` for date, an order of magnitude stronger than any script feature). This is a **craft rubric grounded in a structural reading of his top performers**, not a fitted predictive model. It is still worth applying, because it enforces a consistent floor and eliminates known failure modes. It is not evidence that a 91 will outperform an 83.

---

## The rubric — 100 points

### A. HOOK POWER — 30 pts
*Decides whether anyone sees beat 2.*

| # | Criterion | Pts | Full marks means |
|---|---|---|---|
| A1 | **First-3-second clarity** | 10 | Understandable with zero context, muted, mid-scroll. Concrete noun in the first sentence. |
| A2 | **Self-relevance trigger** | 10 | Viewer thinks *"this is about me"* — universal experience, identity marker, or demographic call-out. |
| A3 | **Curiosity gap / delayed payoff** | 10 | Explicitly promises a reveal that has not yet arrived ("tomorrow you will understand why"). No answer given up front. |

### B. RETENTION ARCHITECTURE — 21 pts
*Decides whether they reach 150 seconds.*

| # | Criterion | Pts | Full marks means |
|---|---|---|---|
| B1 | **Enumerated structure** | 10 | Labelled, countable segments (five mornings, three things, seven nights) so the viewer always knows where they are. |
| B2 | **Diagnostic branching** | 6 | 3–4 "if X → it means A" branches. Every viewer lands in exactly one. *(Was 10 in v1.0; cut after the supporting finding failed to replicate. Retained on craft grounds.)* |
| B3 | **No dead air** | 5 | Every 10s window carries a new concrete detail. No filler, no repetition. |

### C. ENGAGEMENT ENGINEERING — 20 pts
*Converts watch-time into algorithmic signal.*

| # | Criterion | Pts | Full marks means |
|---|---|---|---|
| C1 | **Scripted comment CTA** | 8 | The exact words to type are supplied. Low friction, emotionally motivated. |
| C2 | **Return-visit mechanic** | 7 | Asks for a second session ("come back tomorrow and tell me"). A second session is a very strong signal. |
| C3 | **Share trigger** | 5 | Names a specific person to send it to. (Note: "save this" earns 0 — it is inversely correlated.) |

### D. EMOTIONAL PAYLOAD & TOPIC STAKES — 19 pts
*Drives likes, shares, and the felt sense of being understood.*

| # | Criterion | Pts | Full marks means |
|---|---|---|---|
| D1 | **Absolution / blame reframe** | 8 | Explicitly relieves self-blame: your problem is real, external, and not your fault. |
| D2 | **Topic stakes — identity vs. commodity** | 11 | 11 = death, grief, the dead. 8 = family, destiny, ritual, invisible burden. 4 = general wellness. 0 = a recipe anyone could post. *(Raised from 7; absorbs the 4 points cut from B2. This is the clearest structural difference between his hits and his flops.)* |

### E. MONETISATION BRIDGE — 10 pts

| # | Criterion | Pts | Full marks means |
|---|---|---|---|
| E1 | **Root-cause pivot** | 5 | Pivots from the free tactic to the underlying cause the product addresses. |
| E2 | **Authority + product + CTA** | 5 | Years-in-silence credential → named product → "link in my profile." |

### Grading bands
| Score | Meaning |
|---|---|
| 90–100 | Cold-start tier. Reserve for the first 10 posts. |
| 85–89 | Publish. |
| 75–84 | Fixable — identify the missing beat and rewrite. |
| <75 | Do not post. |

---

## Scores — his top 3 vs. mine

### Monk Chen's top 3 (actual performance in brackets)

| Criterion | #1 Glass of Water<br>*[4,047,769]* | #2 Dreams of the Dead<br>*[1,384,721]* | #3 Morning Routine<br>*[1,205,999]* |
|---|:--:|:--:|:--:|
| A1 Clarity (10) | 10 | 9 | 10 |
| A2 Self-relevance (10) | 8 | 10 | 8 |
| A3 Curiosity gap (10) | 10 | 8 | 6 |
| **A subtotal (30)** | **28** | **27** | **24** |
| B1 Enumeration (10) | 7 | 6 | 10 |
| B2 Branching (6) | 6 | 5 | **0** |
| B3 No dead air (5) | 5 | 5 | 5 |
| **B subtotal (21)** | **18** | **16** | **15** |
| C1 Comment CTA (8) | 8 | 4 | 7 |
| C2 Return visit (7) | 7 | 2 | 4 |
| C3 Share trigger (5) | 1 | 1 | 4 |
| **C subtotal (20)** | **16** | **7** | **15** |
| D1 Absolution (8) | 8 | 7 | 8 |
| D2 Topic stakes (11) | 8 | 11 | 4 |
| **D subtotal (19)** | **16** | **18** | **12** |
| E1 Root-cause pivot (5) | 5 | 4 | 5 |
| E2 Authority+CTA (5) | 5 | 5 | 5 |
| **E subtotal (10)** | **10** | **9** | **10** |
| **TOTAL** | **88** | **77** | **76** |

**His top-3 average: 80.3**

Note how the reweighting redistributes rather than flatters: his #2 *gains* on topic stakes (grief and the dead — the maximum) while his #3 *loses* (a morning wellness routine is the commodity end of the scale). That is the rubric doing its job.

### The new scripts

| Criterion | A — Glass of Water | B — Dreams of the Dead | C — Morning Routine |
|---|:--:|:--:|:--:|
| A1 Clarity (10) | 10 | 9 | 10 |
| A2 Self-relevance (10) | 8 | 10 | 8 |
| A3 Curiosity gap (10) | 10 | 8 | 8 |
| **A subtotal (30)** | **28** | **27** | **26** |
| B1 Enumeration (10) | 7 | 6 | 10 |
| B2 Branching (6) | 6 | 6 | 5 |
| B3 No dead air (5) | 5 | 5 | 5 |
| **B subtotal (21)** | **18** | **17** | **20** |
| C1 Comment CTA (8) | 8 | 8 | 8 |
| C2 Return visit (7) | 7 | 6 | 4 |
| C3 Share trigger (5) | 4 | 3 | 5 |
| **C subtotal (20)** | **19** | **17** | **17** |
| D1 Absolution (8) | 8 | 8 | 8 |
| D2 Topic stakes (11) | 8 | 11 | 4 |
| **D subtotal (19)** | **16** | **19** | **12** |
| E1 Root-cause pivot (5) | 5 | 4 | 5 |
| E2 Authority+CTA (5) | 5 | 5 | 5 |
| **E subtotal (10)** | **10** | **9** | **10** |
| **TOTAL** | **91** | **89** | **85** |

**New average: 88.3** — **+8.0 over his top 3**, and every script clears the 85 publish threshold, though Reel C now clears it only exactly.

---

## Where the gains come from

| Reel | Gap closed | Points |
|---|---|---|
| **A vs his #1** (88→91) | Added a share trigger (he had none, scored 1/5) and 4 branches instead of 3, each keyed to a *social* cause rather than ambient energy. | +3 |
| **B vs his #2** (77→89) | His weakest area by far was engagement (7/20). *"Write their name in the comments. Just the name."* plus a return-visit request takes it to 17/20. | +12 |
| **C vs his #3** (76→85) | Branching added (he had none) on "which morning was hardest," which self-selects and yields a one-word comment. Topic stakes stay low for both — it is a wellness routine, and no amount of structure changes that. | +9 |

**Reel C is now the honest weak link, and the reweighting is what exposed it.** Under v1.0 it scored 91 and looked like the biggest win in the set. Under v2.0 it scores 85 — barely publishable — because topic stakes now carry 11 points and a morning routine earns 4 of them. That is the correct read: his #3 got 1.2M plays on timing and topic familiarity, not structure, and my version cannot borrow either. **I would not lead the launch with Reel C.** Reel B is the strongest asset in the set and should go first.

---

## Honest limitations

1. **These scores are unvalidated.** His carry 4M plays of evidence; mine carry none. The rubric measures pattern-adherence, and pattern-adherence is a *probability shift*, not an outcome.
2. **The rubric is a craft instrument, not a fitted model.** I tested its criteria against 61 transcripts and *most did not predict performance*. Branching failed outright (`r = −0.066`); so did medical claims once date was controlled. The only strong quantitative signal in the whole corpus is posting date (`r = −0.559`), which no script can influence. The weights encode a structural reading of what his hits do differently — a defensible basis for consistency, but not proof that a higher score earns more reach.
3. **I scored my own work.** I applied caps and withheld full marks where the device is present but not maximal, but self-scoring carries an optimism bias that no amount of care fully removes.
4. **The largest single variable is not in the rubric at all.** Cold-start boost drove his top 2, and a new account gets one. That helps you — but it is timing, not craft, and it cannot be scored.
5. **Reel C changes his content materially** by removing medical claims. If it underperforms his version, that is the most likely reason — pseudo-medical specificity ("activates thermogenesis") probably does drive some engagement. I consider that trade correct anyway: those claims are a ban risk and can cause real harm.
