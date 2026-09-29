#!/usr/bin/env python3
"""
Burn monkcheen-style subtitles onto a talking-head video.

    python3 scripts/subs.py B <avatar.mp4> <out.mp4>
    python3 scripts/subs.py B --preview        # 12s sample, no avatar needed

Timing comes from the ElevenLabs `/with-timestamps` alignment, so every card
lands on the millisecond the word is actually spoken. The previous renderer
guessed timings from an assumed words-per-minute, which is what made cards
break mid-phrase ("Not for luck. To see what the").

Card style is copied from a frame grab of his 1.38M-view reel:
  black text, white rounded box, <=3 short lines, centred, just below middle.

This ffmpeg build has 489 filters and ZERO text filters -- no drawtext, no
libass, no subtitles. So cards are composited in PIL and overlaid as a single
alpha video rather than drawn by ffmpeg.
"""

import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
W, H = 1080, 1920

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
SIZE = 58
MAX_CHARS = 26          # per line, measured off his frame
MAX_LINES = 3
PAD_X, PAD_Y = 26, 16
RADIUS = 16
LINE_GAP = 10
Y_CENTRE = 0.60         # box centre as a fraction of frame height

# A card ends at a hard stop, or when it would exceed MAX_LINES.
HARD = ".!?"
SOFT = ",;:"


def run(cmd):
    subprocess.run(cmd, check=True)


def load(rid):
    p = os.path.join(ART, f"voice_{rid.upper()}.json")
    d = json.load(open(p))
    a = d["alignment"]
    return (a["characters"],
            a["character_start_times_seconds"],
            a["character_end_times_seconds"])


def words(chars, starts, ends):
    """Collapse the character stream into timed words."""
    out, buf, t0 = [], "", None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if buf:
                out.append((buf, t0, e))
                buf, t0 = "", None
            continue
        if not buf:
            t0 = s
        buf += ch
    if buf:
        out.append((buf, t0, ends[-1]))
    return out


def wrap(ws):
    """Greedy-wrap a list of word strings into <=MAX_CHARS lines."""
    lines, cur = [], ""
    for w in ws:
        cand = f"{cur} {w}".strip()
        if len(cand) > MAX_CHARS and cur:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


# Words that must not end a card: breaking after them strands a phrase and the
# viewer reads a fragment that means nothing until the next card appears
# ("...has something it has not" / "finished saying").
DANGLING = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "from", "with", "by", "as", "that", "who", "what", "when", "is",
    "was", "are", "were", "be", "been", "has", "have", "had", "do", "does",
    "did", "will", "would", "can", "could", "not", "no", "your", "you", "my",
    "his", "her", "their", "it", "its", "this", "these", "those", "so",
}


def _split_at(buf):
    """Choose where to end an overflowing card. Returns an index into buf."""
    # Walk back from the end for a word that can legally close a card. Only a
    # few words back -- retreating far would leave the card near-empty.
    for i in range(len(buf) - 1, max(len(buf) - 5, 1), -1):
        w = buf[i - 1][0].rstrip(".,;:!?").lower()
        if w not in DANGLING:
            return i
    return len(buf)


def cards(timed):
    """Group timed words into subtitle cards, breaking on punctuation."""
    out, buf = [], []

    def emit(chunk):
        out.append((" ".join(x[0] for x in chunk), chunk[0][1], chunk[-1][2]))

    for w, s, e in timed:
        buf.append((w, s, e))
        text = " ".join(x[0] for x in buf)
        stop = w[-1] in HARD
        full = (len(wrap([x[0] for x in buf])) >= MAX_LINES
                and len(text) > MAX_CHARS * (MAX_LINES - 0.4))
        soft = w[-1] in SOFT and len(text) > MAX_CHARS * 1.6
        if stop or soft:
            emit(buf)
            buf = []
        elif full:
            # Punctuation didn't decide this break, length did -- so pick the
            # cut point rather than splitting wherever the overflow landed.
            i = _split_at(buf)
            emit(buf[:i])
            buf = buf[i:]
    if buf:
        emit(buf)
    return out


def draw_card(text, font):
    """Render one card as a full-frame RGBA image."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(text.split())
    dims = [d.textbbox((0, 0), ln, font=font) for ln in lines]
    lw = [b[2] - b[0] for b in dims]
    lh = max(b[3] - b[1] for b in dims)
    box_w = max(lw) + PAD_X * 2
    box_h = len(lines) * lh + (len(lines) - 1) * LINE_GAP + PAD_Y * 2
    x0 = (W - box_w) // 2
    y0 = int(H * Y_CENTRE) - box_h // 2
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], RADIUS, fill=(255, 255, 255, 236))
    y = y0 + PAD_Y
    for ln, w_ in zip(lines, lw):
        d.text(((W - w_) // 2, y), ln, font=font, fill=(0, 0, 0, 255))
        y += lh + LINE_GAP
    return img


def build_overlay(rid, work, limit=None):
    """Render every card to disk and concat them into one alpha video."""
    # The concat demuxer resolves each `file` entry relative to the list file's
    # own directory, so a relative work dir silently doubles the path prefix.
    work = os.path.abspath(work)
    chars, starts, ends = load(rid)
    cs = cards(words(chars, starts, ends))
    if limit:
        cs = [c for c in cs if c[1] < limit]
    font = ImageFont.truetype(FONT, SIZE)
    os.makedirs(work, exist_ok=True)

    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    seq, t = [], 0.0
    for i, (text, s, e) in enumerate(cs):
        if s > t + 0.02:                       # gap between cards
            p = os.path.join(work, "blank.png")
            if not os.path.exists(p):
                blank.save(p)
            seq.append((p, s - t))
        p = os.path.join(work, f"c{i:04d}.png")
        draw_card(text, font).save(p)
        seq.append((p, max(e - s, 0.25)))
        t = max(e, s)

    listfile = os.path.join(work, "cards.txt")
    with open(listfile, "w") as f:
        for p, dur in seq:
            f.write(f"file '{p}'\nduration {dur:.3f}\n")
        f.write(f"file '{seq[-1][0]}'\n")

    ov = os.path.join(work, "overlay.mov")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listfile, "-c:v", "qtrle", "-r", "30", "-fps_mode", "cfr", ov])
    print(f"  {len(cs)} cards -> {os.path.relpath(ov, ROOT)}")
    return ov, cs, t


def main():
    rid = sys.argv[1].upper()
    work = os.path.join(ROOT, "output", "reels", ".work", f"subs_{rid}")

    if "--preview" in sys.argv:
        # No avatar yet: composite cards over the still master so timing and
        # styling can be judged before any money goes into a render.
        ov, cs, t = build_overlay(rid, work, limit=12.0)
        still = os.path.join(ART, "kaion_master.png")
        out = os.path.join(ROOT, "output", f"subs_preview_{rid}.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-loop", "1", "-i", still, "-i", ov,
             "-i", os.path.join(ART, f"voice_{rid}.mp3"),
             "-filter_complex",
             f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},setsar=1[bg];[bg][1:v]overlay=0:0[v]",
             "-map", "[v]", "-map", "2:a", "-t", "12",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", out])
        print(f"  preview -> {os.path.relpath(out, ROOT)}")
        for text, s, e in cs[:8]:
            print(f"    {s:6.2f}-{e:6.2f}  {text}")
        return

    avatar, out = sys.argv[2], sys.argv[3]
    ov, cs, t = build_overlay(rid, work)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", avatar, "-i", ov,
         "-filter_complex",
         f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
         f"crop={W}:{H},setsar=1[bg];[bg][1:v]overlay=0:0[v]",
         "-map", "[v]", "-map", "0:a?",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", out])
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
