#!/usr/bin/env python3
"""
Gesture re-test: same image, same audio, corrected prompt.

    python3 scripts/gesture_test.py

The first 33s render used a prompt that explicitly forbade gesturing:
"no gesturing. His hands stay resting on the table and do not move."
The model obeyed it exactly, producing 0.54 mean motion in the hands band
against his measured 4.9-7.4 -- roughly a tenth.

A 6-frame strip across the same 33.6s window shows what he actually does:
clasped at t=3/9/15, hands lifted and open at t=21, fingertips together at
t=27, back to clasped at t=32. The clasp is not his posture, it is his REST
STATE between gestures. So the prompt below describes that cycle -- rest,
lift on emphasis, return -- rather than either forbidding motion (run 1) or
requesting generic "natural gestures", which is what produces the fast
jittery hands seen in HeyGen avatars.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie  # noqa: E402

PROMPT = (
    "An elderly monk speaks calmly and slowly directly to the camera while seated "
    "behind a table. His default resting position is both hands clasped together on "
    "the table with fingers interlaced, and he returns to that exact resting position "
    "between gestures. Occasionally, only on an important word, he lifts his hands a "
    "short way off the table and makes one slow deliberate gesture - an open upturned "
    "palm, or fingertips touching - holds it briefly, then lowers his hands back to "
    "the clasped resting position. The gestures are slow, sparse, heavy and unhurried, "
    "like an old teacher who has said this many times. No fast hand movement, no "
    "fidgeting, no waving, no repetitive gesturing, no restless hands. Head stays "
    "mostly still, no head bobbing, no nodding. Serene, warm, grandfatherly. Static "
    "locked-off camera, no camera movement, no cuts."
)


def main():
    art = kie.ART
    img = open(os.path.join(art, "kaion_master.url")).read().strip()
    aud = kie.upload(os.path.join(art, "voice_B_open.mp3"))
    print(f"  audio {aud}")
    print(f"  {kie.credits():.0f} credits before")

    d = kie.run_task("kling/ai-avatar-standard",
                     {"image_url": img, "audio_url": aud, "prompt": PROMPT},
                     "gesture33s", poll=20, limit=90)
    urls = [u for u in kie.urls_from(d) if ".mp4" in u] or kie.urls_from(d)
    if not urls:
        sys.exit("no video url")
    out = os.path.join(art, "avatar_B_open_v2.mp4")
    kie.fetch(urls[0], out)
    print("  ->", os.path.relpath(out, kie.ROOT))


if __name__ == "__main__":
    main()
