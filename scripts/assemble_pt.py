#!/usr/bin/env python3
"""PT master assembly: single kling clip -> subtitled dry 1080x1920 master.

    python3 scripts/assemble_pt.py PT1 [PT2 ...]

Design copied from monge.yang's own frames (2026-08-08): centered white
subtitles with a soft black box, mid-lower band, no CTA cards, no baked
music (TikTok sound is added in-app; IG version gets a bed later).
Whisper multilingual gives the timings; cues are word-grouped to stay short.
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PT = os.path.join(ROOT, "output", "markets", "PT")
MODEL = "mlx-community/whisper-large-v3-turbo"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_SIZE = 60          # FIXED for the whole reel — size never varies per card
SAFE_W = 940            # max box width incl padding
LINE_W = SAFE_W - 56    # max measured text width per line
from PIL import ImageFont as _IF
_FONT = _IF.truetype(FONT_PATH, FONT_SIZE)
from PIL import ImageDraw as _ID, Image as _IM
_MEAS = _ID.Draw(_IM.new("RGB", (8, 8)))


def text_w(t):
    return _MEAS.textlength(t, font=_FONT)


def wrap_px(text):
    """Wrap into lines that each measure <= LINE_W at the fixed font size."""
    lines, line = [], ""
    for w in text.split():
        cand = (line + " " + w).strip()
        if line and text_w(cand) > LINE_W:
            lines.append(line)
            line = w
        else:
            line = cand
    if line:
        lines.append(line)
    return lines


def ts(t):
    h, m = divmod(t, 3600)
    m, s = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def junk(t):
    """Whisper artifacts that must never reach a caption card: breath/hum
    transcribed as a repeated letter, or tokens with no letters at all."""
    bare = re.sub(r"[^\wÀ-ÿ]", "", t)
    if not bare:
        return True
    if len(bare) >= 4 and len(set(bare.lower())) == 1:
        return True
    return False


def align_to_script(words, script):
    """Replace whisper's spelling with the script's own words, matched by
    position via difflib. Whisper keeps only the timing role. Unmatched
    whisper words (insertions) are dropped; unmatched script words ride
    along with the previous matched word so no text is lost."""
    import difflib
    wt = [re.sub(r"[^\wÀ-ÿ]", "", w["word"]).lower() for w in words]
    st_tokens = script.split()
    st = [re.sub(r"[^\wÀ-ÿ]", "", t).lower() for t in st_tokens]
    sm = difflib.SequenceMatcher(a=wt, b=st, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append({"word": st_tokens[j1 + k],
                            "start": words[i1 + k]["start"],
                            "end": words[i1 + k]["end"]})
        elif tag == "replace":
            span = words[i1:i2]
            toks = st_tokens[j1:j2]
            for k, t in enumerate(toks):
                w = span[min(k, len(span) - 1)]
                out.append({"word": t, "start": w["start"], "end": w["end"]})
        elif tag == "insert" and out:
            for t in st_tokens[j1:j2]:
                out.append({"word": t, "start": out[-1]["start"],
                            "end": out[-1]["end"]})
        # tag == "delete": whisper hallucination (breaths, "hhhh") -> dropped
    return out


def cues_from_words(words):
    """Group whisper words into short cues broken at punctuation/width."""
    cues, cur, start = [], "", None
    for w in words:
        t = w["word"].strip()
        if junk(t):
            continue
        if start is None:
            start = w["start"]
        cand = (cur + " " + t).strip()
        if len(wrap_px(cand)) > 2 or (cur and re.search(r"[.!?:]$", cur)):
            cues.append((start, w["start"], cur))
            cur, start = t, w["start"]
        else:
            cur = cand
        end = w["end"]
    if cur:
        cues.append((start, end, cur))
    return cues


def two_lines(text):
    return "\\N".join(wrap_px(text)[:2])


def assemble(rid):
    src = os.path.join(PT, "assets", f"sd{rid}.mp4")
    import mlx_whisper
    r = mlx_whisper.transcribe(src, path_or_hf_repo=MODEL,
                               word_timestamps=True, language="pt")
    words = [w for seg in r["segments"] for w in seg.get("words", [])]
    sj = json.load(open(os.path.join(PT, "source", "scripts_PT.json")))
    script = next(it["script"] for it in sj if it["id"] == rid)
    words = align_to_script(words, script)
    cues = cues_from_words(words)
    with open(os.path.join(PT, "assets", f"cues_{rid}.txt"), "w") as f:
        for a, b, t in cues:
            f.write(f"{a:7.2f} {t}\n")
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", src],
        capture_output=True, text=True).stdout.strip())

    from PIL import Image, ImageDraw
    W, H = 1080, 1920
    font = _FONT
    fdir = os.path.join(PT, "assets", f".cards_{rid}")
    os.makedirs(fdir, exist_ok=True)

    def draw(text, path):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if text:
            lines = two_lines(text).split("\\N")
            f = font
            wmax = max(d.textlength(l, font=f) for l in lines)
            lh = FONT_SIZE + 14
            bh = len(lines) * lh + 36
            y0 = 1470 - bh // 2
            x0 = (W - wmax) / 2 - 28
            d.rounded_rectangle([x0, y0, x0 + wmax + 56, y0 + bh], 18,
                                fill=(0, 0, 0, 230))
            for i, l in enumerate(lines):
                lw = d.textlength(l, font=f)
                d.text(((W - lw) / 2, y0 + 18 + i * lh), l, font=f,
                       fill=(255, 255, 255, 255),
                       stroke_width=2, stroke_fill=(0, 0, 0, 255))
        img.save(path)

    blank = os.path.join(fdir, "blank.png")
    draw("", blank)
    entries, cursor = [], 0.0
    for i, (a, b, t) in enumerate(cues):
        if a - cursor > 0.02:
            entries.append((blank, a - cursor))
        nxt = cues[i + 1][0] if i + 1 < len(cues) else total
        p = os.path.join(fdir, f"c{i:03d}.png")
        draw(t, p)
        entries.append((p, max(0.10, nxt - a)))
        cursor = nxt
    if total - cursor > 0.02:
        entries.append((blank, total - cursor))
    lst = os.path.join(fdir, "cards.txt")
    with open(lst, "w") as f:
        for p, d_ in entries:
            f.write(f"file '{p}'\nduration {d_:.3f}\n")
        f.write(f"file '{entries[-1][0]}'\n")

    out = os.path.join(PT, "reels", f"reel_{rid}_dry.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
        "-f", "concat", "-safe", "0", "-i", lst,
        "-filter_complex",
        "[0:v]scale=-2:1920,crop=1080:1920,unsharp=5:5:0.6:5:5:0.0,"
        "noise=alls=6:allf=t[bg];[bg][1:v]overlay=0:0:format=auto[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "22", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", out], check=True)
    print(out, f"({len(cues)} cues)")


if __name__ == "__main__":
    os.makedirs(os.path.join(PT, "reels"), exist_ok=True)
    for rid in sys.argv[1:]:
        assemble(rid.upper())
