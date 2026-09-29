#!/usr/bin/env python3
"""Side-by-side review: HIS reel on the left, OURS on the right.

    python3 scripts/sbs.py 3 4 5 6        # build for these reel ids
    python3 scripts/sbs.py all

Each output is 1080x960 (two 540x960 halves) and runs for as long as the
SHORTER of the two, which is always ours -- his are ~150s, ours ~90s.

Audio is OURS. The point of the comparison is to judge our render against his
picture, and two soundtracks at once is unlistenable. His delivery is already
known from the source files; what needs judging is whether our frame holds up
next to his.

Labels are burned as a PIL-drawn strip rather than drawtext: this ffmpeg build
has no libfreetype, which is the same constraint assemble_reel.py works around.
"""

import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VID = os.path.join(ROOT, "data", "videos")
OUT = os.path.join(ROOT, "output", "reels")
SBS = os.path.join(OUT, "SIDE_BY_SIDE")

# reel id -> (his source shortcode, our master basename, plays for the label)
PAIRS = {
    "2":  ("DVZg8wAkYgk", "reel_2_MUSIC_C_prelude",            "4,047,769"),
    "B":  ("DVkABsmDCWy", "reel_B_MASTER_dry",                 "1,384,721"),
    "3":  ("DV9w6UMDPgf", "reel_3_seven_grains_of_rice_music",   "210,148"),
    "4":  ("DVttJr1kdHh", "reel_4_salt_wash_music",              "219,253"),
    "5":  ("DWXDi_Ika9U", "reel_5_old_key_music",                "415,810"),
    "6":  ("DY9NBMXMW_2", "reel_6_words_to_mother_music",        "112,851"),
    "7":  ("DZDVB7zM5m1", "reel_7_first_daughter_music",         "580,071"),
    "8":  ("DYuiToNMJep", "reel_8_the_dark_around_you_music",     "33,897"),
    "9":  ("DV19AcBEVYV", "reel_9_three_points_music",            "52,230"),
    "10": ("DWm54pTDBCB", "reel_10_not_tired_exhausted_music",    "70,614"),
    "11": ("DYmxRyQsXw7", "reel_11_morning_seal_music",           "85,818"),
}

W, H = 540, 960          # each half
BAR = 64                 # label strip height


def find_source(code):
    for f in os.listdir(VID):
        if code in f and f.endswith(".mp4"):
            return os.path.join(VID, f)
    return None


def label_strip(left, right, path):
    im = Image.new("RGB", (W * 2, BAR), (16, 16, 16))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
    except OSError:
        f = ImageFont.load_default()
    for text, x0, colour in ((left, 0, (235, 235, 235)), (right, W, (150, 230, 150))):
        w = d.textlength(text, font=f)
        d.text((x0 + (W - w) / 2, (BAR - 34) / 2), text, font=f, fill=colour)
    im.save(path)
    return path


def build(rid):
    code, ours_name, plays = PAIRS[rid]
    his = find_source(code)
    ours = os.path.join(OUT, ours_name + ".mp4")
    if not his:
        return f"reel {rid}: SKIP - his source video not downloaded ({code})"
    if not os.path.exists(ours):
        return f"reel {rid}: SKIP - our master not built ({ours_name})"

    os.makedirs(SBS, exist_ok=True)
    strip = label_strip(f"HIS  {plays} plays", "OURS  @master_kaion",
                        os.path.join(SBS, f".label_{rid}.png"))
    out = os.path.join(SBS, f"sbs_reel_{rid}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", his, "-i", ours, "-i", strip,
        "-filter_complex",
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1[l];"
        f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1[r];"
        f"[l][r]hstack=2[v];[2:v][v]vstack=2[o]",
        "-map", "[o]", "-map", "1:a",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(strip)
    return f"reel {rid}: -> {os.path.relpath(out, ROOT)}"


if __name__ == "__main__":
    ids = sys.argv[1:] or ["all"]
    if ids == ["all"]:
        ids = list(PAIRS)
    for rid in ids:
        print(build(rid))
