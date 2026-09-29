#!/usr/bin/env python3
"""Pre-flight an anchor still BEFORE spending video credits on it.

    python3 scripts/anchor_check.py a19_hall_altar_step [a17_hall_floor_lamp ...]

WHY THIS EXISTS. On 2026-08-11 reel 24 failed twice — ~880 credits — with
gibberish subtitles burned into the pixels, while reel 25 rendered clean on the
first roll in the same session with the same engine, prompt and settings. The
only variable was the anchor:

    a17  bare lap over an empty floor in the lower third   FAILED 2/2
    a18b wooden table, open book, candle in the same band  PASSED 1/1

Both failures put the text at the same baseline and the same left margin, and a
fresh TTS waveform (the previously documented remedy) changed only the glyphs,
never the placement. The prior that survives every observation: an EMPTY,
LOW-DETAIL lower third is read by the model as the place where subtitles belong,
because that is what it saw in millions of subtitled training videos.

So the guard is composition, checked on the 4-credit still rather than on the
~440-credit video: measure how occupied the subtitle band is, and refuse an
anchor whose band is a flat expanse.

Thresholds are calibrated on the three anchors above; run this on any new
anchor and on any anchor that has already failed, and keep the numbers.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANC = os.path.join(ROOT, "output", "assets", "anchors")

# The band kling puts subtitles in, as a fraction of frame height. Matches the
# y1150-1650 window qc_gate.py scans on the assembled 1080x1920 master.
BAND_TOP, BAND_BOT = 0.60, 0.86

# An anchor must clear BOTH. Detail = edges (props, carving, folds, text-free
# structure). Spread = luminance variance (a lit lamp against dark wood scores
# high; an evenly lit robe scores low). Calibration in the module docstring.
# CALIBRATION IS TWO POINTS ONLY — one confirmed failure and one confirmed
# pass, both from 2026-08-11. Treat the thresholds as a tripwire, not a proof:
#     a17  detail 0.0102  spread 20.9   burned text 2/2
#     a18b detail 0.0280  spread 28.6   clean 1/1
#     a19  detail 0.0322  spread 29.3   built to clear it, unrendered as of now
# Every new render should be appended to this table so the numbers earn their
# authority. A RISK verdict means "do not spend without a second look", not
# "this will certainly fail".
MIN_DETAIL = 0.038   # 0.024 -> 0.040 -> (0.050 reverted) -> 0.038

# CALIBRATION — every row is a real render, not a guess.
#
#   anchor            band detail   outcome
#   a17                   0.0102     burned text, 2 of 2 renders  (~880 cr)
#   a18b                  0.0280     clean
#   a23b                  0.0293     BURNED TEXT  (reel 28, 616 cr wasted)
#   a19                   0.0322     clean
#   a21c                  0.0419     clean  (reel 26)
#   a22                   0.0501     clean  (reel 27)
#   a25                   0.0420     (reel 29)
#   a20b                  0.0475     clean, 2 of 2
#   his source reel       0.0671     clean
#
# 0.024 was set from a18b/a19 and let a23b through at 0.0293, which burned text
# across the whole take.
#
# I then raised it to 0.050 reasoning from the anchor->render detail loss, and
# it immediately REJECTED a21c (0.0419) and a24 (0.0462) — the two anchors that
# had actually rendered clean. A floor that fails known-good inputs is
# miscalibrated, which is the exact rule written earlier the same day. Reverted
# to 0.038: comfortably above the only observed failure (0.0293) and below every
# observed pass. Move it again only when a real render contradicts it, never
# from reasoning alone.
#
# The render-loss measurement is still worth keeping, as context rather than as
# a threshold: kling loses ~28% of lower-third detail between still and video
# (a24 anchor 0.0462 -> rendered 0.0327-0.0369 across the whole take), so the
# anchor figure is optimistic by about a quarter. That explains WHY 0.0293 burns
# — it renders near 0.022 — without justifying a floor above the known passes.
MIN_SPREAD = 24.0


# ⚠️ NO AUTOMATED FACE-SIZE CHECK EXISTS. One was attempted 2026-08-15
# (skin-tone row detection) and REMOVED the same hour: it scored 0.808-0.862
# across anchors that differ visibly, because it catches arms and neck as well
# as the head. It could not separate a24 (tight, best mouth motion) from a25
# (wide, the operator noticed immediately). A check that cannot tell known-good
# from known-bad is worse than no check — it launders a guess as a measurement.
#
# Until something better exists, FACE SIZE IS A HUMAN JUDGEMENT: look at the
# 4-credit anchor next to the source frame before rendering. Reel 24 at ~8% of
# frame height read mushy; reels 26-28 at ~14-20% read clean. The `courtyard`
# setting pulls the camera back further than `veranda` or `gateway` — prefer
# those two for talking takes.

def measure(png):
    """(edge density, luminance stddev) inside the subtitle band."""
    import numpy as np
    from PIL import Image

    im = Image.open(png).convert("L")
    w, h = im.size
    band = im.crop((0, int(h * BAND_TOP), w, int(h * BAND_BOT)))
    a = np.asarray(band, dtype=float)
    # Sobel-free gradient magnitude: cheap, and we only need a relative score.
    gy, gx = np.gradient(a)
    mag = np.hypot(gx, gy)
    # Density = fraction of pixels sitting on a real edge, not sensor noise.
    detail = float((mag > 18).mean())
    spread = float(a.std())
    return detail, spread


def main():
    names = sys.argv[1:]
    if not names:
        sys.exit(__doc__.strip().splitlines()[2])
    bad = 0
    for n in names:
        png = n if os.path.exists(n) else os.path.join(ANC, n + ".png")
        if not os.path.exists(png):
            print(f"{n:28s} MISSING")
            bad += 1
            continue
        detail, spread = measure(png)
        ok = detail >= MIN_DETAIL and spread >= MIN_SPREAD
        flag = "OK  " if ok else "RISK"
        print(f"{os.path.basename(png):32s} detail {detail:.4f} "
              f"spread {spread:5.1f}  {flag}")
        if not ok:
            bad += 1
            print("     -> the subtitle band is close to empty. Put a surface, "
                  "prop or light source in the lower third before rendering.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
