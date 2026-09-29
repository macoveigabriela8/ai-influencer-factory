"""Locate burned-glyph rows in a raw kling clip, in NORMALISED frame height.

Same signal finish_reel.measure_burn uses (temporal-median residual): kling
animates the face region of a still, so the per-pixel median over many frames
IS the clean plate, and whatever flickers against it in the lower band is the
burn. Reported as a fraction of frame height so it can be compared against the
caption card (0.760-0.839) regardless of the render's native resolution.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

def extent(path):
    p = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                        "-show_entries","stream=width,height","-of","csv=p=0",path],
                       capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(p[0]), int(p[1])
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",path,
                        "-vf","fps=2,format=gray",f"{td}/%03d.png"], check=True)
        fs = sorted(os.listdir(td))
        if len(fs) < 8:
            return None
        stack = np.stack([np.asarray(Image.open(os.path.join(td,f)),dtype=np.float32) for f in fs])
    med = np.median(stack, axis=0)
    res = np.abs(stack - med)                      # per-frame deviation from the clean plate
    lo, hi = int(H*0.55), int(H*0.95)              # lower band only; face sits above it
    band = res[:, lo:hi, :]
    # a burned row is bright ACROSS the row on at least one frame
    rowmax = band.max(axis=0).mean(axis=1)         # per-row mean residual, worst frame
    thr = rowmax.mean() + 3*rowmax.std()
    hot = np.where(rowmax > max(thr, 6.0))[0]
    frames_hot = int(((band.mean(axis=(1,2))) > (band.mean()+2*band.std())).sum())
    if len(hot) == 0:
        return (None, None, 0, len(fs), W, H)
    return ((lo+hot.min())/H, (lo+hot.max())/H, frames_hot, len(fs), W, H)

for f in sys.argv[1:]:
    r = extent(f)
    if r is None:
        print(f"{os.path.basename(f):<16} too few frames"); continue
    t,b,fh,n,W,H = r
    if t is None:
        print(f"{os.path.basename(f):<16} {W}x{H} {n}f  CLEAN (no hot rows)")
    else:
        print(f"{os.path.basename(f):<16} {W}x{H} {n}f  hot rows y {t:.3f}-{b:.3f}  ({int(t*1920)}-{int(b*1920)} @1080x1920)")
