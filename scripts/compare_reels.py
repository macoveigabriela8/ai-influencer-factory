#!/usr/bin/env python3
"""Side-by-side frame comparison: HIS reel vs OURS.

    python3 scripts/compare_reels.py <source> <ours> [-o out.jpg] [-n 8]

<source> may be a local mp4, an Instagram/TikTok URL, or a monkcheen shortcode
(resolved from data/monkcheen_posts.json, falling back to yt-dlp on the
permalink because Instagram CDN media urls expire within days).
<ours> may be a local mp4 or a reel number (2, 7, 22 ... -> output/FINAL_MASTERS).

Frames are sampled by PERCENTAGE of duration, not by absolute seconds, so a 45s
source lines up against our 78s master beat for beat. Top row is his, bottom row
is ours, same column = same point in the story.

Why this exists: transcripts carry the words and lose everything else. The 8.3M
monge.yang reel turned out to be FULL-BODY seated on a mat, and every assumption
taken from its transcript alone was wrong (CLAUDE.md, 2026-08-08). Framing,
posture, wardrobe, light, subtitle placement and what is on screen at the close
are all invisible in text and all copyable.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTERS = os.path.join(ROOT, "output", "FINAL_MASTERS")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def duration(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", path])
    return float(r.stdout.strip())


def resolve_source(arg, tmp):
    if os.path.exists(arg):
        return arg
    url = arg
    if "/" not in arg:                      # bare shortcode
        url = f"https://www.instagram.com/p/{arg}/"
        local = [f for f in os.listdir(os.path.join(ROOT, "data",
                 "competitors", "videos")) if arg in f] \
            if os.path.isdir(os.path.join(ROOT, "data", "competitors",
                                          "videos")) else []
        if local:
            return os.path.join(ROOT, "data", "competitors", "videos", local[0])
    out = os.path.join(tmp, "source.mp4")
    r = sh(["yt-dlp", "-o", out, "-f", "mp4/best", url])
    if not os.path.exists(out):
        raise SystemExit(
            f"could not fetch {url}\n{r.stderr.strip()[-400:]}\n"
            "Instagram CDN urls in the scrape expire — re-scrape via Apify or "
            "download the mp4 by hand into data/competitors/videos/.")
    return out


def resolve_ours(arg):
    if os.path.exists(arg):
        return arg
    key = arg.zfill(2) if arg.isdigit() else arg
    for f in sorted(os.listdir(MASTERS)):
        if f.startswith(f"reel_{key}_") or f.startswith(f"reel_{arg}_"):
            return os.path.join(MASTERS, f)
    raise SystemExit(f"no master for reel '{arg}' in {MASTERS}")


def strip(path, n, tmp, tag, label):
    """One horizontal strip of n frames sampled at even % of duration."""
    d = duration(path)
    shots = []
    for i in range(n):
        pct = (i + 0.5) / n
        t = d * pct
        f = os.path.join(tmp, f"{tag}_{i:02d}.jpg")
        sh(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
            "-vf", "scale=320:-2", f])
        if os.path.exists(f):
            shots.append((f, f"{int(pct*100)}%  {t:0.1f}s"))
    if not shots:
        raise SystemExit(f"no frames extracted from {path}")
    row = os.path.join(tmp, f"{tag}_row.jpg")
    # drawtext per tile, then hstack
    labelled = []
    for i, (f, cap) in enumerate(shots):
        o = os.path.join(tmp, f"{tag}_{i:02d}_l.jpg")
        sh(["ffmpeg", "-y", "-i", f, "-vf",
            "drawbox=x=0:y=0:w=iw:h=26:color=black@0.65:t=fill,"
            f"drawtext=text='{cap}':x=6:y=5:fontsize=15:fontcolor=white", o])
        labelled.append(o if os.path.exists(o) else f)
    inputs = []
    for f in labelled:
        inputs += ["-i", f]
    sh(["ffmpeg", "-y"] + inputs +
       ["-filter_complex", f"hstack=inputs={len(labelled)}", row])
    titled = os.path.join(tmp, f"{tag}_titled.jpg")
    sh(["ffmpeg", "-y", "-i", row, "-vf",
        f"pad=iw:ih+34:0:34:color=#111111,"
        f"drawtext=text='{label}':x=8:y=7:fontsize=22:fontcolor=#ffd479",
        titled])
    return titled if os.path.exists(titled) else row


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    if len(a) < 2:
        raise SystemExit(__doc__)
    n = 8
    out = os.path.join(ROOT, "output", "compare.jpg")
    for i, x in enumerate(sys.argv):
        if x == "-n":
            n = int(sys.argv[i + 1])
        if x == "-o":
            out = sys.argv[i + 1]
    with tempfile.TemporaryDirectory() as tmp:
        src = resolve_source(a[0], tmp)
        ours = resolve_ours(a[1])
        ds, do = duration(src), duration(ours)
        print(f"HIS  {os.path.basename(src)}  {ds:.1f}s")
        print(f"OURS {os.path.basename(ours)}  {do:.1f}s")
        top = strip(src, n, tmp, "his",
                    f"HIS  {os.path.basename(src)}  {ds:.0f}s")
        bot = strip(ours, n, tmp, "our",
                    f"OURS {os.path.basename(ours)}  {do:.0f}s")
        sh(["ffmpeg", "-y", "-i", top, "-i", bot, "-filter_complex",
            "[0][1]vstack=inputs=2", out])
    if not os.path.exists(out):
        raise SystemExit("stack failed")
    print(f"\n{out}")
    print(f"duration: his {ds:.0f}s vs ours {do:.0f}s  "
          f"({'ours is %.0f%% longer' % ((do/ds-1)*100) if do > ds else 'ours is shorter'})")


if __name__ == "__main__":
    main()
