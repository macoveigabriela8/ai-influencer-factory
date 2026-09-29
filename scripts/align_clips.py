#!/usr/bin/env python3
"""Remove the framing step between clips.

    REEL=2 python3 scripts/align_clips.py 1 2 3 4     -> sd2_NN_aligned.mp4

THE PROBLEM. Every clip is an independent Seedance generation anchored on the
same reference image, so each one interprets the framing slightly differently.
Measured on reel 2 (ORB features + RANSAC similarity fit, against clip 1):

    clip 1  scale 1.0000  rot  0.000deg  dy   0.0px
    clip 2  scale 1.0098  rot -0.157deg  dy -10.6px
    clip 3  scale 1.0214  rot -0.035deg  dy -13.2px
    clip 4  scale 1.0413  rot -0.283deg  dy -27.1px

Two things matter about that table. First, the drift is entirely BETWEEN clips
-- within any single clip the camera is locked to 4 decimal places, so this is
not shake and a stabiliser is the wrong tool. Second, it is MONOTONIC: the
framing pulls back ~1.4% per clip, so it reads as a slow creep across the reel
rather than as random jitter, which is exactly why it is noticeable at all.

THE FIX. Warp every clip into clip 1's frame. Clip 1 is the TIGHTEST framing, so
every correction is a zoom-IN and no clip is ever asked to invent pixels outside
its own edge. A uniform SAFETY_ZOOM is then applied to all clips equally --
including clip 1 -- to swallow the sliver that rotation and translation can
still expose at the border. Applying it to every clip is what keeps the
correction invisible: a zoom applied uniformly changes the composition slightly
but changes the RELATIVE framing not at all.

WHY FULL AFFINE AND NOT ffmpeg scale+crop. A pure scale+translate could be done
with `scale=...,crop=...` and no OpenCV. But the measured rotation reaches
0.283deg, which is ~9px of displacement at the corner of a 1920px frame -- above
the threshold that made this visible in the first place. Correcting scale while
leaving rotation would fix the part that was measured and leave the part that
was not.

Audio is remuxed untouched from the source clip. This step must never alter it:
the clips have already passed the QC gate on their audio, and re-encoding it
would invalidate that.
"""

import json
import os
import subprocess
import sys

import cv2
import numpy as np

ART = "output/assets"
STEM = {"B": "seedance", "2": "sd2", "3": "sd3", "4": "sd4", "5": "sd5", "6": "sd6",
        "7": "sd7", "8": "sd8", "9": "sd9", "10": "sd10", "11": "sd11"}
# 2% of frame, applied to every clip identically. Sized to cover the worst
# measured corner displacement (clip 4: 0.283deg rotation + 27px translation)
# with margin, without visibly cropping the composition.
SAFETY_ZOOM = 1.02
SAMPLES = 9          # frames per clip to median together for feature matching


def median_gray(path, k=SAMPLES):
    """A median over evenly-spaced frames: the monk moves, the courtyard does not.

    Matching on a single frame would let his head and hands contribute features
    that mean nothing about camera framing. Taking the per-pixel median across
    the clip suppresses whatever moves and keeps the static set, which is the
    only thing the transform should be fitted to.
    """
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ims = []
    for i in np.linspace(0, n - 1, k).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, im = cap.read()
        if ok:
            ims.append(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
    cap.release()
    return np.median(ims, axis=0).astype(np.uint8)


def fit(ref, img):
    """Similarity transform mapping `img` coordinates onto `ref` coordinates."""
    orb = cv2.ORB_create(4000)
    ka, da = orb.detectAndCompute(ref, None)
    kb, db = orb.detectAndCompute(img, None)
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(db, da)
    matches = sorted(matches, key=lambda x: x.distance)[:300]
    src = np.float32([kb[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([ka[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    M, inliers = cv2.estimateAffinePartial2D(
        src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5)
    return M, int(inliers.sum())


def zoom_about_centre(M, w, h, z):
    """Compose M with a zoom of z about the frame centre."""
    cx, cy = w / 2.0, h / 2.0
    Z = np.array([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)], [0, 0, 1]])
    M3 = np.vstack([M, [0, 0, 1]])
    return (Z @ M3)[:2]


def main(ns):
    reel = os.environ.get("REEL", "2")
    stem = STEM[reel]
    paths = [os.path.join(ART, f"{stem}_{n:02d}.mp4") for n in ns]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        sys.exit("missing: " + ", ".join(missing))

    ref = median_gray(paths[0])
    report = {}
    for n, path in zip(ns, paths):
        M, inl = fit(ref, median_gray(path))
        s = float(np.hypot(M[0, 0], M[0, 1]))
        rot = float(np.degrees(np.arctan2(M[0, 1], M[0, 0])))

        cap = cv2.VideoCapture(path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        Mz = zoom_about_centre(M, w, h, SAFETY_ZOOM)

        tmp = os.path.join(ART, f".{stem}_{n:02d}_aligned_v.mp4")
        out = os.path.join(ART, f"{stem}_{n:02d}_aligned.mp4")
        vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # BORDER_REPLICATE, not a black fill: if the safety zoom is ever a
            # hair short, a smeared edge pixel is invisible at scroll speed and
            # a black wedge is not.
            vw.write(cv2.warpAffine(frame, Mz, (w, h), flags=cv2.INTER_LANCZOS4,
                                    borderMode=cv2.BORDER_REPLICATE))
        cap.release()
        vw.release()

        # Remux: aligned video + ORIGINAL audio stream, copied not re-encoded.
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", path,
                        "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", out], check=True)
        os.remove(tmp)
        report[os.path.basename(path)] = dict(scale=s, rot=rot, dx=float(M[0, 2]),
                                              dy=float(M[1, 2]), inliers=inl)
        print(f"  clip {n}: scale {s:.4f} rot {rot:+.3f}deg "
              f"dy {M[1,2]:+6.1f}px inliers {inl} -> {os.path.basename(out)}")

    json.dump(report, open(os.path.join(ART, f"align_reel{reel}.json"), "w"), indent=1)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [1, 2, 3, 4])
