#!/usr/bin/env python3
"""
Score and stack renders against his reference footage.

    python3 scripts/compare.py out.mp4 \
        "His 1.38M"=data/videos/BIG02_DVkABsmDCWy.mp4 \
        "Kling"=output/assets/avatar_B_test34.mp4

Prints a metrics table, then writes a labelled side-by-side video.

All measurements are on the LOWER THIRD of frame, where the hands are, at 8fps.

READ THE COLUMNS IN THIS ORDER -- the first two carried all the signal, and the
third was a hypothesis that failed:

  motion       mean frame-to-frame difference. His BIG02 = 9.75. The first Kling
               render scored 0.94 -- ten times too still. That render's prompt
               stacked four negations at hand motion, and it worked: the hands
               barely moved. Being far BELOW his number is a defect, not safety.

  sharp@still  variance of the Laplacian = fine detail. His BIG02 = 3588, our
               renders ~900, at the SAME 720p resolution (his 720x1280, ours
               720x1264). A 4x detail gap present in every frame, moving or not.
               This is the largest measured difference between his footage and
               ours and is probably what reads as "AI" to a viewer.

  ratio        focus(moving)/focus(still). INTENDED to catch ghosting -- hands
               crisp at rest, smeared when lifted. IT DOES NOT WORK. The visibly
               ghosting render scored 0.99, better than his 0.96. The reason is
               that ghosting happens only in the handful of frames where the
               hands actually lift, and a conditional average over 33 seconds
               washes those frames out. Kept only so nobody re-derives it and
               believes it. To catch ghosting, inspect the peak-motion frames
               directly rather than averaging over them.
"""

import os
import subprocess
import sys

import numpy as np

W, H = 128, 72          # analysis resolution -- small is fine, we want gradients
FPS = 8


def frames(path, secs=None):
    """Lower TWO THIRDS of frame, greyscale, decimated.

    This was the lower third on the theory that the hands live there, because
    they rest on the table. That crop scored a Seedance clip at 2.66 motion --
    "barely moves" -- while it was in fact raising a hand and pointing at the
    camera the whole time. The gesture happens UP NEAR THE FACE, which the crop
    excluded, so the metric reported the exact opposite of what was on screen.

    The hands are only in the lower third when they are DOING NOTHING. Any crop
    tight enough to isolate resting hands is by construction blind to the
    gesture, which is the thing worth measuring. So: lower two thirds, which
    covers the table, the chest and the raised-hand zone, and excludes only the
    top of the head.
    """
    cmd = ["ffmpeg", "-v", "error"]
    if secs:
        cmd += ["-t", str(secs)]
    cmd += ["-i", path, "-vf",
            f"crop=iw:ih*2/3:0:ih/3,scale={W}:{H},format=gray,fps={FPS}",
            "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)


def laplacian(f):
    """4-neighbour Laplacian; its variance is the standard focus measure."""
    return (-4 * f[1:-1, 1:-1] + f[:-2, 1:-1] + f[2:, 1:-1]
            + f[1:-1, :-2] + f[1:-1, 2:])


def score(path, secs=None):
    f = frames(path, secs)
    if len(f) < 20:
        return None
    motion = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    focus = np.array([laplacian(x).var() for x in f[1:]])

    hi = motion >= np.percentile(motion, 90)      # hands actively moving
    lo = motion <= np.percentile(motion, 50)      # hands at rest
    return {
        "frames": len(f),
        "motion_mean": motion.mean(),
        "peak_median": motion.max() / max(np.median(motion), 1e-6),
        "focus_still": focus[lo].mean(),
        "focus_moving": focus[hi].mean(),
        # <1 means the hands lose definition exactly when they move: ghosting.
        "sharpness_ratio": focus[hi].mean() / max(focus[lo].mean(), 1e-6),
    }


def has_drawtext():
    r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                       capture_output=True, text=True)
    return " drawtext " in r.stdout


def stack(pairs, out, secs):
    """Lay the clips side by side at a common height, labelled if we can.

    Homebrew's default ffmpeg ships without drawtext (it needs libfreetype), so
    fall back to a coloured marker bar and print the left-to-right order instead
    of failing the whole comparison over a caption.
    """
    text = has_drawtext()
    bars = ["red", "lime", "cyan", "yellow", "magenta"]
    ins, filt, names = [], [], []
    for i, (label, path) in enumerate(pairs):
        ins += ["-t", str(secs), "-i", path]
        safe = label.replace("'", "").replace(":", " ")
        tag = (f"drawbox=y=0:h=64:color=black@0.65:t=fill,"
               f"drawtext=text='{safe}':x=20:y=16:fontsize=34:fontcolor=white"
               if text else
               f"drawbox=y=0:h=24:color={bars[i % len(bars)]}@0.9:t=fill")
        filt.append(f"[{i}:v]scale=-2:960,crop=540:960,{tag}[v{i}]")
        names.append(f"[v{i}]")
    if not text:
        print("  (ffmpeg has no drawtext -- labelling with colour bars instead)")
        for i, (label, _) in enumerate(pairs):
            print(f"    {bars[i % len(bars)]:<8} {label}")
    filt.append("".join(names) + f"hstack=inputs={len(pairs)}[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins,
                    "-filter_complex", ";".join(filt), "-map", "[v]",
                    "-map", "0:a?", "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-shortest", out], check=True)
    return out


def main():
    out = sys.argv[1]
    pairs = []
    for arg in sys.argv[2:]:
        label, _, path = arg.partition("=")
        if not os.path.exists(path):
            print(f"  SKIP (missing) {label}: {path}")
            continue
        pairs.append((label, path))
    if not pairs:
        sys.exit("nothing to compare")

    secs = min(float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
        for _, p in pairs)
    print(f"  comparing first {secs:.1f}s of {len(pairs)} clips\n")

    print(f"  {'clip':<22}{'motion':>8}{'pk/med':>8}{'sharp@still':>13}"
          f"{'sharp@move':>12}{'ratio':>8}")
    for label, path in pairs:
        s = score(path, secs)
        if not s:
            print(f"  {label:<22}  too short to score")
            continue
        print(f"  {label:<22}{s['motion_mean']:8.2f}{s['peak_median']:8.1f}"
              f"{s['focus_still']:13.1f}{s['focus_moving']:12.1f}"
              f"{s['sharpness_ratio']:8.2f}")
    print("\n  motion:      match his, do not undershoot -- too still is a defect too."
          "\n  sharp@still: fine detail. Ours has run ~4x below his at equal resolution."
          "\n  ratio:       does NOT detect ghosting (see docstring). Ignore it.\n")

    stack(pairs, out, secs)
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
