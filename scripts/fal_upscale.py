#!/usr/bin/env python3
"""
Sharpen the OmniHuman source image.

    python3 scripts/fal_upscale.py kaion_hands.png

Why this exists at all. OmniHuman treats the source image as near-inviolable:
it is the pose, the identity and the texture that the whole runtime returns to,
and the model cannot render a hand sharper than the hand it was shown. Measured
at 512px wide, variance of the Laplacian:

    kaion_rest.png      188
    kaion_master.png    153
    hands_apart.png     134     <- best POSE, worst PIXELS

hands_apart has the pose that fixed the hand smearing (both hands flat, wide
apart, sutra between them, nothing touching), so we want to keep it. But every
render we have made sits ~3x below his reference footage on detail, and feeding
the softest source available makes that worse. Improving the source is a fixed
cost paid once, ahead of every future render including reels C and D.

THE RISK, and why this script runs more than one model. Upscalers add detail by
INVENTING it, and fingers are precisely where invention shows up as an extra
knuckle or a fused pair. So the detail number going up is not sufficient
evidence -- the hands have to be inspected by eye afterwards. The two models
here fail differently on purpose:

    recraft/upscale/crisp   non-generative. Sharpens what is there. Cannot
                            invent a sixth finger because it is not generating.
                            Lower ceiling on detail gain.
    topaz/upscale/image     generative, much stronger detail recovery, and the
                            one that can rewrite a hand. Run with the lowest
                            creativity the endpoint allows.

Pick the winner on hands first, detail second. A soft correct hand beats a
sharp malformed one -- softness is uniform across the frame and reads as
camera; a bad finger reads as AI instantly.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fal_avatar as fa

ART = fa.ART

MODELS = {
    "crisp": ("fal-ai/recraft/upscale/crisp", {}),
    "topaz": ("fal-ai/topaz/upscale/image", {"upscale_factor": 2}),
}


def run(model, extra, image_url, label):
    r = fa.post(f"https://queue.fal.run/{model}", {"image_url": image_url, **extra})
    status_url, resp_url = r.get("status_url"), r.get("response_url")
    print(f"  {label}: queued")
    import time
    for i in range(120):
        time.sleep(5)
        st = fa.get(status_url).get("status")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR"):
            print(f"  {label} FAILED: {fa.get(resp_url)}")
            return None
        if i % 12 == 0:
            print(f"    …{st} ({(i+1)*5}s)")
    else:
        print(f"  {label} timed out")
        return None
    out = fa.get(resp_url)
    return (out.get("image") or {}).get("url")


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "kaion_hands.png"
    src = os.path.join(ART, name)
    url = fa.host(src)
    stem = os.path.splitext(name)[0]
    for key, (model, extra) in MODELS.items():
        u = run(model, extra, url, key)
        if not u:
            continue
        p = fa.fetch(u, os.path.join(ART, f"{stem}_{key}.png"))
        print(f"    -> {os.path.relpath(p, fa.ROOT)}")


if __name__ == "__main__":
    main()
