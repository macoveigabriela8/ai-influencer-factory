#!/usr/bin/env python3
"""Generate one anchor still, by EDITING an approved anchor so identity carries.

    python3 scripts/make_anchor.py a21_courtyard_table_closeup --from a18b_low_table_v2

4 credits. The still is where framing, expression, realism and the subtitle
band are decided — the video it seeds costs ~150x more (CLAUDE.md spend rule 4).

WHY EDIT RATHER THAN GENERATE FRESH. Kaion's face has to be the same man in
every reel. A from-scratch prompt re-rolls the identity; `image_urls` on
nano-banana keeps it and changes only what the prompt names. Same technique as
kie.cmd_restpose.

WHY THIS ANCHOR EXISTS (2026-08-15). The operator's note on reel 24 was that the
lip movement read wrong. Measured against the source we are copying:

    his face  ~18% of frame height   (chest-up, at a low table)
    reel 24   ~8%                    (wide shot, empty floor)

Kling animates the face REGION of the still, so a wide shot leaves it a few
dozen pixels of mouth to work with and the result reads mushy. This is a
FRAMING defect, not an engine defect — ai-avatar-pro would render a sharper
wide shot with the same tiny mouth, at double the price. Fix the framing on
the cheap artifact first; keep the engine as the next single variable if the
lips still read wrong (spend rule 3: one variable per paid render).

The prompt states the lower third POSITIVELY (table, open book, candle). An
empty low-detail band is what makes kling burn fake subtitles into the pixels
— see output/RCA_BURNED_SUBTITLES.md. anchor_check runs automatically below.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anchor_check
import kie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANC = os.path.join(ROOT, "output", "assets", "anchors")

# The ONE face every anchor is edited from. See the note in main().
CANON = "a32d_cloister"

# Composition read off a frame of the source at 62s (2026-08-15), not guessed.
# Everything is stated POSITIVELY — negated objects get generated ("no tripod"
# produces tripods), so "hands not visible" is phrased as arms resting low and
# hidden by the robe.
#
# Four things the first pass (a21) got wrong, all corrected here:
#   1. it smiled          -> kling oscillates into a grin (the PT8 defect)
#   2. candle cropped out -> his stands fully in frame in front of the book
#   3. dead-centre        -> his table sits to one side, angled; the shot is asymmetric
#   4. hands on the table -> his are out of frame entirely, which removes
#                            kling's weakest feature at the source
# ---------------------------------------------------------------- INVARIANTS
# Every clause below was bought with a real failure. Do not trim them.
#
#   FRAMING FIRST      a21b described the kneeling pose in detail and the model
#                      pulled the camera back to show it; face height fell to
#                      ~12% and lip-sync went mushy again. State the crop as a
#                      hard boundary BEFORE the pose, and keep the pose short.
#   FACE ~18-20%       reel 24 at ~8% read mushy, reel 26 at ~20% read clean on
#                      the SAME engine. Face size sets lip-sync, not model tier.
#   NEUTRAL MOUTH      PT8's anchor had a soft smile and kling snapped back to it
#                      between phrases, oscillating into a grin every few seconds.
#                      Invisible at 1fps; only a 5fps mouth crop catches it.
#   SEATED             standing anchors produce a step-forward/step-back sway loop.
#   HANDS OUT OF FRAME kling's weakest feature, removed at the source. The
#                      originals hide them behind the table anyway.
#   BUSY LOWER THIRD   an empty low-detail band makes kling burn fake subtitles
#                      into the pixels (output/RCA_BURNED_SUBTITLES.md).
#   NOTHING THAT MOVES kling animates the FACE REGION ONLY, so a candle flame is
#                      frozen for the whole take — measured on reel 26 at ~1.0
#                      mean frame-diff against ~14 for the mouth, and the operator
#                      spotted it unprompted twice. Fill the band with objects
#                      that have no business moving: books, beads, stone, cloth.
#   POSITIVE PHRASING  negated objects get generated ("no tripod" makes tripods),
#                      so "hands not visible" is written as arms resting low.

FRAMING = (
    "FRAMING, the most important instruction: this is a TIGHT CHEST-UP PORTRAIT, "
    "a close photograph of his head and chest only. "
    # EXPLICIT PROPORTION, added 2026-08-15. "His head is large and fills the
    # upper third" was too vague: QA measured reel 33's face at 14.7% of frame
    # height against the ~18-20% target, and face size — not model tier — is
    # what sets lip-sync legibility. Give the model a number it can aim at.
    "HIS HEAD MUST BE BIG IN THE PICTURE: from the top of his skull to the point "
    "of his chin should span about one fifth of the whole height of the image. "
    "This is a close portrait, shot as if from about one metre away with an 85mm "
    "lens, not a room photograph with a person in it. "
    "The bottom edge of the picture cuts across "
    "the middle of his chest, so his lap, knees and legs are entirely outside "
    "the frame. His arms rest low and out of shot. Fill the frame with him. "
)

# POSE VARIANTS. Operator note 2026-08-15: "not all reels in same pose". Every
# anchor to that point was seated-behind-a-low-table with an open book, which
# reads as one shot restaged. Each variant below still satisfies the invariants
# — seated (standing sways), hands out of frame, a lower third full of STATIC
# objects — but changes the body, the camera axis and the furniture.
POSES = {
    "table": (
        "POSE: he is seated upright behind a low table, his body turned "
        "slightly, his face square to the camera. He looks directly into the "
        "lens, holding the viewer's eye. "),
    "step": (
        "POSE: he is sitting on a broad stone step, leaning forward a little "
        "with his forearms out of frame, his upper body angled about thirty "
        "degrees away from the camera while his face turns back square to the "
        "lens. He looks directly into the lens, holding the viewer's eye. "),
    "ledge": (
        "POSE: he is seated behind a low stone balustrade, upright and square "
        "to the camera, photographed from very slightly below his eye level so "
        "he reads a little taller. He looks directly into the lens. "),
    "mat": (
        "POSE: he is seated cross-legged on a woven mat on the ground, his back "
        "straight, his body turned a quarter to one side and his face square to "
        "the camera. He looks directly into the lens. "),
}

EXPRESSION = (
    "EXPRESSION: completely neutral and still. The mouth is closed, the lips "
    "gently together and level, the jaw relaxed. A calm, serious, unsmiling face "
    "at rest, as in a passport photograph. "
)

REALISM_BLOCK = (
    "REALISM: real weathered skin with visible pores, fine wrinkles, sun spots "
    "and small blemishes. Slightly asymmetric features. Fabric with genuine "
    "creases and wear. Natural light with soft directional shadows falling to "
    "one side. An unposed, candid documentary photograph, imperfect rather than "
    "polished. "
)

# ------------------------------------------------------------------ SETTINGS
# 🛑 THE FOREGROUND IS FIXED. Do not vary it (operator decision 2026-08-15,
# after reel 30 burned at the best band score we have ever measured).
#
# Six anchors, six renders:
#     a21c 0.0419 · a22 0.0501 · a24 0.0462 · a25 0.0420   all CLEAN
#     a23b 0.0293 (dark hall)                              BURNED
#     a26c 0.0676 (stone balustrade, no table, no book)    BURNED
#
# The four clean ones are the SAME foreground — low table close to the lens,
# large open book, prayer beads, bright daylight. Both burns were departures
# from it. Two anchor-side metrics were tested and BOTH failed to predict a26c:
# mean band detail (0.0676, the highest recorded) and widest quiet strip (0.425,
# identical to the clean set). So we cannot currently screen this from the
# still, and the only thing that fits all six points is the composition family.
#
# VARIETY THEREFORE COMES FROM THE BACKDROP, THE LIGHT AND THE CAMERA ANGLE —
# which is also what the source accounts actually do: one pose per reel, the
# ROOM changes between reels.

FOREGROUND = (
    "FOREGROUND, filling the bottom third of the frame: the near edge of a low "
    "weathered wooden table, very close to the camera and turned at an angle so "
    "one corner points toward the lens. A large old book lies open on it, its "
    "printed pages facing up and filling much of the width, with a string of "
    "dark wooden prayer beads coiled beside it. Both are large in frame and "
    "sharply detailed. "
)

BACKDROPS = {
    "courtyard":  "an open temple courtyard in bright afternoon light, carved "
                  "stone lanterns and clipped bonsai behind him, grey paving. ",
    "gateway":    "the gateway of a temple in soft daylight, tall red lacquered "
                  "pillars and a carved stone guardian lion behind him. ",
    "veranda":    "an open temple veranda in full daylight, pale timber posts "
                  "and a bright garden of clipped green shrubs behind him. ",
    "terrace":    "an open stone terrace in clear morning light, a tiled temple "
                  "roof and distant green hills far behind him. ",
    "wall":       "a sunlit monastery wall of weathered ochre plaster behind "
                  "him, a narrow shadow line falling across it. ",
    "garden":     "a temple garden at golden hour, a still pond and a stone "
                  "bridge softly out of focus behind him. ",
    "steps":      "the broad stone stairway of a temple in bright daylight, "
                  "carved balustrades and green trees behind him. ",
    "cloister":   "a shaded stone cloister opening onto bright daylight, a row "
                  "of pale arches receding behind him. ",
    # First INTERIOR backdrop (reel 32). Read off the source of DSXWL-FEZgI,
    # which is shot inside a temple hall — every backdrop above is outdoor
    # daylight, so the whole set had one look. The lanterns are described as
    # GLOWING rather than flickering: kling animates the face region only, so
    # anything that should move is frozen for the whole take. For the same
    # reason this deliberately drops the source's lit candle.
    # ⚠️ THE ONLY OTHER INTERIOR WE TRIED, a23b, BURNED (band detail 0.0293 —
    # reel 28, 616 cr). It was a DARK hall, and a dark lower third is what makes
    # kling burn subtitles into the band. So this one keeps the interior for
    # variety but puts bright daylight ON THE TABLE from a side opening: the
    # backdrop is warm and deep, the FOREGROUND is well lit. Do not reintroduce
    # "deep shadows" here — that phrase is what a23b's prompt said.
    # 🛑 DO NOT USE. INTERIORS DO NOT CLEAR THE SUBTITLE BAND — 4 for 4, and one
    # of them cost a 616 cr reel. Measured 2026-08-15, floor 0.038:
    #
    #   a23b  0.0293  dark hall                       -> BURNED (reel 28)
    #   a32   0.0174  hall, rich description, low angle  -> FAIL
    #   a32b  0.0258  hall, terse + defocused backdrop   -> FAIL
    #   a32c  0.0236  same, HIGH angle                   -> FAIL
    #
    # vs every outdoor daylight backdrop: 0.0419 - 0.0501, all clean.
    #
    # Two fixes were tried and both were falsified. Shortening the setting text
    # fixed the framing (a32 pulled back to a mid shot; a32b did not) but moved
    # the band only 0.0174 -> 0.0258. Raising the camera to bring the book's
    # pages up into the band made it slightly WORSE, 0.0236.
    #
    # The reason is the metric: it counts EDGE DENSITY, and an interior is dark,
    # so the band loses contrast no matter how the furniture is arranged. This
    # is a property of the lighting, not the composition, and it cannot be
    # prompted away while the room is indoors. Get scene variety from the
    # daylight backdrops above — that is also what the source accounts do.
    "hall":       "a temple hall indoors, a gilded Buddha statue and warm paper "
                  "lanterns far behind him, thrown completely out of focus. "
                  "Daylight from one side falls brightly across the table and "
                  "the open book. ",
}

ANGLES = {
    "straight": "The camera is square to him at his eye level. ",
    "left":     "The camera sits slightly to his left, so he is seen a little "
                "from the side while his face turns back to the lens. ",
    "right":    "The camera sits slightly to his right, so he is seen a little "
                "from the side while his face turns back to the lens. ",
    "low":      "The camera is a little below his eye level, looking slightly "
                "up at him. ",
    "high":     "The camera is a little above his eye level, looking slightly "
                "down at him. ",
}

# Robe colours. The FACE is the identity and must never change; the robe is
# wardrobe and can. Varying it is the cheapest real novelty available, because
# it changes the largest block of colour in frame — and the lower half of our
# composition is mostly robe.
ROBES = {
    "maroon":   "the same maroon and saffron monastic robe",
    "indigo":   "a deep indigo and dark slate-blue monastic robe",
    "charcoal": "a charcoal grey and off-white monastic robe",
    "ochre":    "a burnt ochre and pale gold monastic robe",
    "plum":     "a dark plum and dusty rose monastic robe",
}


def build(backdrop, angle="straight", pose="table", robe="maroon"):
    return ("Keep this exact man unchanged — the same face, the same age and "
            "lines, the same shaved head, the same identity. He is wearing "
            + ROBES[robe] + ". Change only the camera, the pose and the "
            "setting. The robe is EXACTLY the colour just described. "
            # ⚠️ This used to end "...the pose, the wardrobe COLOUR and the
            # setting", which contradicted the robe named one clause earlier —
            # it named a colour and then licensed changing it. nano-banana took
            # the licence: `--robe maroon` returned a GREEN robe (a38c,
            # 2026-08-15). Wardrobe variety comes from PASSING a different
            # --robe, never from leaving the model free to invent one.
            + FRAMING + POSES[pose] + ANGLES[angle] + EXPRESSION
            + FOREGROUND + "SETTING: " + BACKDROPS[backdrop] + REALISM_BLOCK
            # The crop is restated LAST as well as first. a32 proved that a
            # setting described near the end of the prompt overrides a framing
            # instruction given at the start: the model pulled back to a mid
            # shot to show the temple hall off, dropping the face to ~10% of
            # frame height and filling the subtitle band with flat robe.
            + "FINALLY, THE CROP AGAIN, WHICH OVERRIDES THE SETTING: this is a "
              "tight chest-up portrait. The table's near edge is close to the "
              "camera and the open book is large in the bottom third of the "
              "picture. His head is large in frame. The background is distant "
              "and out of focus. ")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    name = sys.argv[1]
    # 🛑 ALWAYS EDIT FROM THE CANONICAL FACE, NEVER FROM THE LAST ANCHOR.
    #
    # Identity drift is CUMULATIVE. nano-banana re-renders the face on every
    # edit, so chaining a33d <- a33b <- a32d <- a25 stacks three generations of
    # error and the man stops being the same man. Caught by the operator on
    # 2026-08-15: a33d is visibly younger and fuller-faced than the monk on the
    # published reels, and kaion_rest is visibly OLDER than all of them — proof
    # the drift had been running unnoticed for many anchors.
    #
    # Editing from a fixed canonical source keeps every anchor exactly ONE
    # generation from the reference, so error cannot accumulate.
    #
    # CANON is a32d_cloister: the face family the audience has actually seen on
    # the recent published reels. kaion_rest is deliberately NOT the canon —
    # reverting to it now would itself be a visible change of face.
    src = CANON
    if "--from" in sys.argv:
        src = sys.argv[sys.argv.index("--from") + 1]
        if src != CANON:
            print(f"  ⚠️  editing from {src}, not the canonical {CANON}. "
                  f"Each hop re-renders the face — only do this deliberately.")
    backdrop = "courtyard"
    if "--setting" in sys.argv:
        backdrop = sys.argv[sys.argv.index("--setting") + 1]
    angle = "straight"
    if "--angle" in sys.argv:
        angle = sys.argv[sys.argv.index("--angle") + 1]
    pose = "table"
    if "--pose" in sys.argv:
        pose = sys.argv[sys.argv.index("--pose") + 1]
    robe = "maroon"
    if "--robe" in sys.argv:
        robe = sys.argv[sys.argv.index("--robe") + 1]
    EDIT = build(backdrop, angle, pose, robe)

    src_url = os.path.join(ANC, src + ".url")
    if not os.path.exists(src_url):
        sys.exit(f"no {src_url} — the source anchor must have a stored url")

    before = kie.credits()
    d = kie.run_task("google/nano-banana", {
        "prompt": EDIT + kie.REALISM + " No text, no watermark, no subtitles.",
        "image_urls": [open(src_url).read().strip()],
        "output_format": "png", "image_size": "9:16",
    }, f"anchor {name}")
    u = kie.urls_from(d)
    if not u:
        sys.exit("no image url returned")

    png = kie.fetch(u[0], os.path.join(ANC, name + ".png"))
    open(os.path.join(ANC, name + ".url"), "w").write(u[0])
    # PROVENANCE — how many generations from the canonical face this anchor is.
    # render_avatar.py refuses to spend on an anchor that is more than one hop,
    # because that is how the face drifted into a different man unnoticed.
    prov_src = os.path.join(ANC, src + ".json")
    hops = 1
    if os.path.exists(prov_src):
        try:
            hops = json.load(open(prov_src)).get("hops_from_canon", 0) + 1
        except Exception:
            hops = 1
    if src == CANON:
        hops = 1
    json.dump({"from": src, "canon": CANON, "hops_from_canon": hops,
               "pose": pose, "robe": robe, "setting": backdrop, "angle": angle},
              open(os.path.join(ANC, name + ".json"), "w"), indent=1)
    print(f"  provenance: {hops} generation(s) from canon {CANON}")
    after = kie.credits()
    print(f"  saved {os.path.relpath(png, ROOT)}")
    print(f"  billed {before - after:.0f} cr  (balance {after:.0f})")

    # IDENTITY STRIP — the check that did not exist while the face drifted.
    # No face-embedding model here, and a crude pixel metric would be worse than
    # useless on different crops and lighting. So this writes the new face
    # beside the canonical one and makes the operator look. Cheap, and it is
    # exactly how the drift was eventually caught.
    try:
        from PIL import Image, ImageDraw
        cmp_path = os.path.join(ANC, f"_identity_{name}.png")
        pair = []
        for lbl, p in (("CANON " + CANON, os.path.join(ANC, CANON + ".png")),
                       ("NEW " + name, png)):
            im = Image.open(p)
            w, h = im.size
            pair.append((lbl, im.crop((int(w * .25), int(h * .10),
                                       int(w * .80), int(h * .55))).resize((380, 380))))
        strip = Image.new("RGB", (760, 404), "white")
        d = ImageDraw.Draw(strip)
        for i, (lbl, t) in enumerate(pair):
            strip.paste(t, (i * 380, 24))
            d.text((i * 380 + 6, 6), lbl, fill="black")
        strip.save(cmp_path)
        print(f"  IDENTITY STRIP -> {os.path.relpath(cmp_path, ROOT)}  "
              f"— compare the faces before rendering. Same man or re-roll.")
    except Exception as e:
        print(f"  identity strip failed: {e}")

    detail, spread = anchor_check.measure(png)
    ok = detail >= anchor_check.MIN_DETAIL and spread >= anchor_check.MIN_SPREAD
    print(f"  subtitle band: detail {detail:.4f} (floor {anchor_check.MIN_DETAIL}) "
          f"| spread {spread:.1f} (floor {anchor_check.MIN_SPREAD}) "
          f"-> {'PASS' if ok else 'FAIL — recompose, do not render'}")


if __name__ == "__main__":
    main()
