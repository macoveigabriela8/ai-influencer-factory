#!/usr/bin/env python3
"""
Generate Master Kaion character-reference candidates.

    python3 scripts/character.py           # render all variants
    python3 scripts/character.py v2        # render one

Design notes, all derived from measurement of his top 3 reels rather than taste:

  * ZERO scene cuts across 151-161s, and a contact sheet of the hands at 8 points
    across 145s shows them interlaced in the identical position every time. So the
    reference image must be a composition that survives being held motionless for
    2.5 minutes -- hands clasped and locked, forearms down, nothing to animate.

  * His backdrop carries the authority: temple facade, prayer wheels, stupa, prayer
    flags, mountains. A generic interior reads as a man in a bathrobe. The setting
    is credibility, not decoration.

  * Realism comes from photographic specificity (lens, light, skin detail), not
    from adding "realistic" as an adjective. Diffusion models respond to camera
    language far more than to quality words.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie  # noqa: E402

ART = os.path.join(kie.ROOT, "output", "assets", "candidates")

# Shared photographic grammar -- this is the part that buys realism.
CAMERA = (
    "Shot on a full-frame DSLR with an 85mm lens at f/2.8, eye-level, locked-off "
    "tripod, chest-up medium close-up, subject centred and facing the lens directly. "
    "Overcast diffused daylight, no harsh shadows. Photojournalistic documentary "
    "photograph, natural colour, subtle film grain. "
)

# Realism lives in imperfections. Naming them explicitly stops the model from
# producing the airbrushed 'AI face' that reads as fake instantly.
FACE = (
    "An 74-year-old Tibetan Buddhist monk. Shaved head with faint grey stubble. "
    "Deeply weathered sun-aged skin with visible pores, fine crosshatched wrinkles "
    "around the eyes, deep nasolabial folds, slightly uneven skin tone, faint age "
    "spots on the temples and scalp, thin sparse grey eyebrows. Small dark brown "
    "eyes with heavy hooded lids and slight moisture. Ears slightly large with long "
    "lobes. Thin lips, mouth closed in a calm neutral expression. Warm, kind, "
    "grandfatherly, entirely serene. Asymmetric natural face, not a symmetrical "
    "idealised face. "
)

# Frame-grid across his range (BIG01 4.0M / TOP01 1.2M / LOW01 2.7k) shows the
# open sutra book and the pointing hand in ALL of them -- his best AND his worst.
# So the book does not predict performance. It earns its place for a different
# reason: it gives the hands a target. Gesturing at a specific object reads as
# teaching; gesturing at nothing reads as the jittery-avatar failure mode.
POSE_BOOK = (
    "He sits upright behind a low weathered wooden table. An old open sutra book "
    "with hand-written script lies flat on the table in front of him. His left hand "
    "rests on the table beside the book; his right hand is raised slightly, index "
    "finger extended, pointing calmly down toward the open page. Unhurried, "
    "deliberate, teaching. "
)

POSE = (
    "He sits upright behind a low weathered wooden table, both forearms resting flat "
    "on the tabletop, hands clasped together with fingers interlaced in front of him, "
    "completely still and relaxed. "
)

ROBE = (
    "Wearing a traditional deep maroon Tibetan monastic robe over a saffron-yellow "
    "under-shirt, heavy natural cotton with visible weave and soft folds. "
)

NEG = (
    "No text, no watermark, no logo, no subtitles, no plastic skin, no airbrushing, "
    "no beauty filter, no cgi look, no extra fingers, no distorted hands."
)

# v2-v4 all rendered a man reading ~62-65. His monk reads ~75: heavier jowls,
# hollower temples, denser age spots. Age is authority in this niche, so v5
# overrides the shared FACE block with a harder-aged description.
FACE_OLDER = (
    "An 78-year-old Tibetan Buddhist monk, visibly elderly and frail. Shaved head "
    "with white stubble at the temples. Heavily weathered leathery sun-damaged skin, "
    "deep creases across the forehead, hollow temples, sunken cheeks, loose skin and "
    "soft jowls along the jaw, prominent tendons in the neck, many dark age spots "
    "across the scalp, temples and hands. Sparse white eyebrows. Small dark eyes set "
    "deep under heavy drooping lids, slightly watery. Thin pale lips, mouth closed, "
    "calm neutral expression. Hands are bony and veined with prominent knuckles and "
    "thin skin. Warm, kind, grandfatherly, entirely serene. Asymmetric natural face, "
    "not symmetrical or idealised. "
)

VARIANTS = {
    "v2_temple": (
        "Behind him, an old Himalayan Buddhist temple courtyard: an ornate painted "
        "temple facade with red columns and gold trim, a row of copper prayer wheels "
        "along the wall on the left, a white stone stupa and colourful prayer flags "
        "on the right, green mountain slopes rising in the far background. Stone "
        "flagstone courtyard floor. Background softly out of focus. "
    ),
    "v3_monastery_wall": (
        "Behind him, the whitewashed stone wall of a Himalayan monastery with a "
        "carved dark-wood window frame, a row of copper prayer wheels running along "
        "the wall, faded prayer flags strung overhead, and misty mountain ridges "
        "visible beyond. Background softly out of focus. "
    ),
    # Same backdrop as v2 so the only variable is the face age.
    "v5_temple_older": (
        "Behind him, an old Himalayan Buddhist temple courtyard: an ornate painted "
        "temple facade with red columns and gold trim, a row of copper prayer wheels "
        "along the wall on the left, a white stone stupa and colourful prayer flags "
        "on the right, green mountain slopes rising in the far background. Stone "
        "flagstone courtyard floor. Background softly out of focus. "
    ),
    # Same face + backdrop as v5; the only change is the book and pointing hand.
    "v6_temple_book": (
        "Behind him, an old Himalayan Buddhist temple courtyard: an ornate painted "
        "temple facade with red columns and gold trim, a row of copper prayer wheels "
        "along the wall on the left, a white stone stupa and colourful prayer flags "
        "on the right, green mountain slopes rising in the far background. Stone "
        "flagstone courtyard floor. Background softly out of focus. "
    ),
    "v4_courtyard_rain": (
        "Behind him, a Himalayan monastery courtyard in light rain: wet stone "
        "flagstones, a painted temple entrance with red columns, copper prayer wheels, "
        "prayer flags heavy with damp, low cloud sitting on the green mountainside. "
        "Cool soft grey light. Background softly out of focus. "
    ),
}


def build(key):
    face = FACE_OLDER if key[:2] in ("v5", "v6") else FACE
    pose = POSE_BOOK if key.startswith("v6") else POSE
    return CAMERA + face + pose + ROBE + VARIANTS[key] + NEG


def render(key):
    os.makedirs(ART, exist_ok=True)
    d = kie.run_task("google/nano-banana",
                     {"prompt": build(key), "output_format": "png", "image_size": "9:16"},
                     key, poll=6, limit=40)
    urls = kie.urls_from(d)
    if not urls:
        print("  no url for", key)
        return
    path = os.path.join(ART, f"{key}.png")
    kie.fetch(urls[0], path)
    open(os.path.join(ART, f"{key}.url"), "w").write(urls[0])
    print("  ->", os.path.relpath(path, kie.ROOT))


if __name__ == "__main__":
    keys = sys.argv[1:] or list(VARIANTS)
    for k in keys:
        match = [x for x in VARIANTS if x.startswith(k)]
        render(match[0] if match else k)
