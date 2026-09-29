#!/usr/bin/env python3
"""
Age the monk's hands and forearms in the source image, then re-sharpen.

    python3 scripts/age_hands.py

WHY. The v5 gate came back with a 70-year-old face on 40-year-old arms. Two
causes stack:

  1. The source photograph already has smooth, pale, untextured forearms. The
     face carries its age in LARGE features -- jowls, hollow cheeks, brow --
     while arms carry age purely in FINE texture: tendon ridges, raised veins,
     knuckle wrinkles, age spots, thin crepey skin.

  2. OmniHuman resamples internally and eats high-frequency detail. Measured:
     source detail 223, rendered output 912 against his 6172. Fine texture is
     exactly the band that gets destroyed -- so arm age is the first thing to
     go, and face age survives.

Which means "the arms look young" and "the arms look blurry" are ONE defect,
not two. The blur IS the youth.

THE STRATEGY IS PRE-COMPENSATION. If the model reliably removes a fixed amount
of high-frequency detail, then feeding it normally-aged arms yields young arms,
and feeding it EXAGGERATEDLY aged arms yields correctly aged ones. We
deliberately overshoot in the source so that what survives the smoothing lands
where we want it.

THE RISK, and how it is contained. This is a generative edit, and generative
edits are how interlaced fingers got introduced in the first place -- the whole
reason the hands broke. Since the v5 prompt no longer mentions hands at all,
this image is the ONLY control over finger geometry, so corrupting it corrupts
everything. Containment:

  * The prompt pins the pose explicitly and repeatedly -- same position, same
    separation, nothing touching -- and restricts the edit to SKIN TEXTURE.
  * The output is re-run through the crisp upscaler, because nano-banana emits
    around 1024px and would otherwise undo the detail work in fal_upscale.py.
  * The hands must be inspected by eye afterwards. Five countable fingers on
    each hand, still apart, still flat. No detail score can make that call.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie

ART = kie.ART

# Naming the aging markers individually rather than saying "make him look older".
# Vague age direction moves the FACE, which is already correct and which we do
# not want touched; naming the specific textures keeps the edit on the skin.
PROMPT = (
    "Keep this exact man, his face, his robe, the room, the lighting and the "
    "framing completely unchanged. Keep both hands in exactly the same position, "
    "flat and open on the table, wide apart, one on each side of the open book, "
    "with a clear gap between them and nothing touching. Change only the skin "
    "texture of his hands and forearms, so that it matches the age of his face: "
    "thin weathered elderly skin with visible raised veins along the back of the "
    "hands, prominent tendon ridges, deeply wrinkled knuckles, scattered brown "
    "age spots, loose crepey skin at the wrist and forearm, and dry papery "
    "texture. The hands of a man in his seventies. Photographic, highly detailed, "
    "sharp focus on the skin texture."
)


def detail(path):
    """Variance of the Laplacian at a fixed 512px width, so runs are comparable."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                          "scale=512:-1,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).astype(float).reshape(-1, 512)
    lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1]
           + a[1:-1, :-2] + a[1:-1, 2:])
    return lap.var()


def main():
    src = kie.upload(os.path.join(ART, "kaion_src.png"))
    d = kie.run_task("google/nano-banana", {
        "prompt": PROMPT,
        "image_urls": [src],
        "output_format": "png",
        "image_size": "9:16",
    }, "age hands")
    u = kie.urls_from(d)
    if not u:
        sys.exit("no image url returned")
    raw = kie.fetch(u[0], os.path.join(ART, "kaion_aged_raw.png"))
    print(f"  aged   detail {detail(raw):.0f}")

    # nano-banana returns ~1024px, well below the 2304px the crisp upscaler
    # produced, so re-sharpen and conform back to the render resolution.
    open(os.path.join(ART, "kaion_aged_raw.url"), "w").write(u[0])
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__),
                    "fal_upscale.py"), "kaion_aged_raw.png"], check=True)

    crisp = os.path.join(ART, "kaion_aged_raw_crisp.png")
    out = os.path.join(ART, "kaion_aged.png")
    subprocess.run(["ffmpeg", "-v", "error", "-i", crisp, "-vf",
                    "scale=720:1280:flags=lanczos", "-y", out], check=True)
    for p in (os.path.join(ART, "kaion_src.png"), out):
        print(f"  {os.path.basename(p):22} detail {detail(p):.0f}")
    print("  INSPECT THE HANDS BY EYE -- five fingers each, apart, flat.")


if __name__ == "__main__":
    main()
