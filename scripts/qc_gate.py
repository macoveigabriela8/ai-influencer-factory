#!/usr/bin/env python3
"""The generate->assemble QC gate. Run on every clip before assembly.

    REEL=2 python3 scripts/qc_gate.py 1 2 3 4 5 6

Two independent checks, both mandatory (CLAUDE.md; SOP Part 3 Step 5):

  TEXT  -- transcribe the RENDERED audio and diff against the intended chunk.
           A failed Seedance generation is fluent and confident, not obviously
           broken. It ships silently if unchecked.
  DRONE -- see drone_check.py. Seedance beds a synth chord under some
           generations (1 in 8 measured).

WHY SIMILARITY ALONE IS NOT ENOUGH -- the clip 5 lesson, 2026-07-25.

Reel 2 clip 5 scored 0.833 word-level similarity, which reads as a near-miss and
would pass any threshold set at 0.8. It was not a near-miss. Two words moved:

    "SEND THIS TO the person who sleeps eight hours..."  ->  "A person who..."
    "a glass of water shows you the WEIGHT"              ->  "...the WAY"

The first deletes the share trigger outright (rubric C3, 5 pts). The second
inverts the product pivot (E1, 5 pts): "shows you the way" makes the glass
sufficient, which removes the reason to buy anything. ~10 rubric points lost,
and the similarity score barely moved, because similarity weights every word
equally and a script does not.

So: load-bearing lines are checked LITERALLY, not statistically. A clip fails if
any required phrase is absent, no matter how well it scores overall.
"""

import difflib
import json
import os
import re
import subprocess
import sys

ART = "output/assets"
PLAN = {"B": "chunks.json", **{str(n): f"chunks_reel{n}.json" for n in range(2, 22)}}
STEM = {"B": "seedance", **{str(n): f"sd{n}" for n in range(2, 22)}}

# Phrases that carry rubric points and must survive verbatim. Keyed by reel and
# clip. Matched on normalised text (lowercase, punctuation stripped), so casing
# and commas are free, but every word must be present in order.
REQUIRED = {
    "2": {
        1: ["place a glass of water beside your bed tonight",
            "tomorrow morning you will understand why"],   # hook -- never rewrite
        2: ["absorb what is heavy", "three things can happen"],  # incantation + B1 count
        3: ["first", "second"],                                  # enumeration ordinals
        4: ["you are not lazy", "you are not weak"],             # D1 absolution
        # Phrases here must survive WHISPER, not just Seedance. Checked against
        # our own clean ElevenLabs source: it renders "the weight" as "to wait"
        # and "Forty" as "40". Requiring either would fail a perfect clip, so
        # both are excluded -- an earlier run blamed Seedance for exactly that.
        5: ["you have been sleeping beside something",
            "a glass of water shows you"],                       # E1 pivot setup
        6: ["it cannot take it off you",
            "taught me to live without it"],                     # E1 limit + credential
        7: ["everything i know is inside",
            "the link is in my profile"],                        # invariant tail, 7/7
    }
}

SIM_FLOOR = 0.90


def norm(s):
    return re.sub(r"[^a-z ]", "", s.lower()).split()


def main(ns):
    reel = os.environ.get("REEL", "B")
    plan = {p["n"]: p for p in json.load(open(os.path.join(ART, PLAN[reel])))}
    req = REQUIRED.get(reel, {})
    import mlx_whisper

    failed = []
    for n in ns:
        video = os.path.join(ART, f"{STEM[reel]}_{n:02d}.mp4")
        if not os.path.exists(video):
            print(f"clip {n}: MISSING {video}")
            failed.append(n)
            continue
        wav = f"/tmp/qc_{reel}_{n}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1",
                        "-ar", "16000", "-y", wav], check=True)
        got = mlx_whisper.transcribe(
            wav, path_or_hf_repo="mlx-community/whisper-small.en-mlx")["text"].strip()
        want = plan[n]["text"]
        sim = difflib.SequenceMatcher(None, norm(want), norm(got)).ratio()
        flat = " ".join(norm(got))
        missing = [p for p in req.get(n, []) if " ".join(norm(p)) not in flat]

        ok = sim >= SIM_FLOOR and not missing
        print(f"clip {n}: similarity {sim:.3f}  {'PASS' if ok else 'FAIL'}")
        if missing:
            print("   MISSING REQUIRED: " + " | ".join(repr(p) for p in missing))
        if not ok:
            print(f"   WANT: {want}\n   GOT : {got}")
            failed.append(n)

    print()
    if failed:
        print(f"TEXT GATE: {len(failed)} clip(s) failed: {failed}")
    else:
        print(f"TEXT GATE: all {len(ns)} clips pass")

    # Burned-subtitle gate. Kling sometimes renders its OWN subtitles into the
    # pixels -- fake Chinese or gibberish Latin in a pale serif, lower-middle of
    # frame. Found 2026-08-07 on 4 of 37 clips (reels 15, 17) AFTER assembly;
    # cost of the miss was ~$5.45 of re-rolls plus two reels pulled from a
    # scheduled batch. Text is intermittent, so ONE frame is not enough:
    # sample every 2s and take the max. Calibration on the 37-clip batch:
    # clean frames scored 0.008-0.019 edge density, subtitled frames 0.028+.
    print()
    sub_failed = []
    for n in ns:
        v = os.path.join(ART, f"{STEM[reel]}_{n:02d}.mp4")
        if not os.path.exists(v):
            continue
        hit = burned_text_times(v)
        if hit:
            print(f"clip {n}: BURNED-IN TEXT at {hit}s — kling subtitled it. Re-roll.")
            sub_failed.append(n)
    if sub_failed:
        print(f"SUBTITLE GATE: {len(sub_failed)} clip(s) failed: {sub_failed}")
    else:
        print(f"SUBTITLE GATE: all clips clean")

    # Drone half -- delegated, so there is exactly one implementation of it.
    vids = [os.path.join(ART, f"{STEM[reel]}_{n:02d}.mp4") for n in ns]
    vids = [v for v in vids if os.path.exists(v)]
    print()
    rc = subprocess.run([sys.executable, "scripts/drone_check.py"] + vids).returncode
    return 1 if (failed or sub_failed or rc) else 0


def burned_text_times(video, band=None, thresh=0.027):
    """Seconds at which the lower-middle band shows text-like edge density.

    The band is a FRACTION of the frame, not fixed pixels. It was originally
    hardcoded to y1150-1650 of a 1080x1920 clip, which silently broke the day
    the default engine became kling/ai-avatar-standard — that renders 720x1264,
    so the crop fell outside the frame and ffmpeg errored rather than reporting
    a clean pass. 1150/1920 = 0.599 and 1650/1920 = 0.859, the same fractions
    anchor_check.py uses, so the calibration carries over unchanged. The crop is
    still scaled to 540x250 before measuring, which is what keeps the 0.027
    threshold comparable across resolutions.
    """
    import tempfile
    from PIL import Image, ImageFilter
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", video],
        capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(probe[0]), int(probe[1])
    y0 = int(H * (band[0] / 1920 if band else 0.599))
    y1 = int(H * (band[1] / 1920 if band else 0.859))
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip())
    hits = []
    with tempfile.TemporaryDirectory() as td:
        t = 1.0
        while t < dur - 0.5:
            png = os.path.join(td, "f.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t),
                            "-i", video, "-vf",
                            f"crop={W}:{y1-y0}:0:{y0},scale=540:250",
                            "-frames:v", "1", png], check=True)
            im = Image.open(png).convert("L").filter(ImageFilter.FIND_EDGES)
            px = list(im.getdata())
            if sum(1 for p in px if p > 60) / len(px) > thresh:
                hits.append(round(t))
            t += 2.0
    return hits


if __name__ == "__main__":
    sys.exit(main([int(x) for x in sys.argv[1:]]))
