#!/usr/bin/env python3
"""
Render the three Master Kaion reels end-to-end, locally, with zero API keys.

    python3 scripts/build_reels.py            # all three
    python3 scripts/build_reels.py A          # just reel A

What this produces is a REAL 1080x1920 mp4 per reel: narrated, music-bedded,
with burned-in subtitles at the measured treatment. It is a proof of the whole
pipeline and a usable timing reference.

What it is NOT: the finished creative. Two layers are stand-ins, both clearly
labelled in the output --
  * voice  -- macOS `say` (Grandpa, en_GB). Swap for ElevenLabs when keyed.
  * visual -- a flat gradient plate. Swap for the avatar render when keyed.

The subtitle timings ARE final, because they are derived from the actual
narration audio rather than estimated. When the real voice lands, rerun and the
timings re-derive themselves.

Music bed: synthesised, not sampled -- two sustained sine partials at G3 (196 Hz)
and Bb3 (233 Hz), the interval measured off his #1 reel, run through tremolo and
reverb so it reads as a pad rather than a test tone. Royalty-free by construction.
"""

import json
import os
import subprocess
import sys
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "reels")
WORK = os.path.join(OUT, ".work")

VOICE = os.environ.get("KAION_VOICE", "Grandpa (English (UK))")
# `say -r` is not real wpm on this voice: measured 145->111wpm, 190->166wpm.
# 180 lands at ~150wpm, which is the measured centre of his delivery.
WPM = int(os.environ.get("KAION_WPM", "180"))
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
BEAT_GAP = 0.55           # silence at every beat boundary
CARD_GAP = 0.14           # micro-breath between subtitle cards
MUSIC_RATIO = 0.40        # music RMS as fraction of voice RMS, pre-duck

W, H = 1080, 1920


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def dur(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path])
    return float(r.stdout.strip())


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


# --------------------------------------------------------------------------
# Script data. Beats hold lines; lines are split into <=7-word subtitle cards.
# --------------------------------------------------------------------------
def load_reels():
    with open(os.path.join(ROOT, "scripts", "reels.json")) as f:
        return json.load(f)


def cards_for(beat):
    out = []
    for line in beat["lines"]:
        w = line.split()
        for i in range(0, len(w), 7):
            out.append(" ".join(w[i:i + 7]))
    return out


# --------------------------------------------------------------------------
def synth_music(seconds, path):
    """Two sustained partials, G3 + Bb3, tremolo + reverb-ish tail."""
    expr = (
        f"aevalsrc="
        f"0.34*sin(2*PI*196*t)+0.26*sin(2*PI*233*t)"
        f"+0.10*sin(2*PI*392*t)+0.07*sin(2*PI*466*t)"
        f":s=44100:d={seconds:.2f}"
    )
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", expr,
         "-af", ("tremolo=f=0.18:d=0.55,"
                 "aecho=0.8:0.9:600|1100:0.35|0.22,"
                 "lowpass=f=1400,highpass=f=120,"
                 "afade=t=in:st=0:d=4,"
                 f"afade=t=out:st={max(0, seconds-5):.2f}:d=5"),
         "-ac", "2", path])


def rms(path):
    tmp = path + ".rms.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
         "-ar", "22050", "-ac", "1", tmp])
    with wave.open(tmp) as w:
        raw = w.readframes(w.getnframes())
    os.remove(tmp)
    if not raw:
        return 1e-6
    import array
    a = array.array("h", raw)
    return (sum(float(x) ** 2 for x in a) / len(a)) ** 0.5 / 32768 or 1e-6


# --------------------------------------------------------------------------
# Frame compositing. Subtitle treatment is measured off his reels: white
# rounded card, black bold text, 5-8 words, centred at ~55% frame height.
# --------------------------------------------------------------------------
def make_plate():
    """Static stand-in for the avatar render: seated figure behind a table."""
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new("RGB", (W, H), (35, 42, 47))
    d = ImageDraw.Draw(img)
    for y in range(H):                                  # vertical falloff
        k = y / H
        d.line([(0, y), (W, y)],
               fill=(int(57 - 22 * k), int(66 - 24 * k), int(75 - 28 * k)))
    d.ellipse([int(W * 0.40), int(H * 0.30),            # head
               int(W * 0.60), int(H * 0.43)], fill=(110, 98, 90))
    d.rounded_rectangle([int(W * 0.26), int(H * 0.40),  # shoulders / robe
                         int(W * 0.74), int(H * 0.78)],
                        radius=int(W * 0.20), fill=(62, 71, 89))
    d.rectangle([0, int(H * 0.74), W, H], fill=(94, 72, 48))   # cedar table
    img = img.filter(ImageFilter.GaussianBlur(22))
    return img


def render_frames(wd, seq, total):
    """One PNG per subtitle state, with its display duration."""
    from PIL import Image, ImageDraw, ImageFont
    fdir = os.path.join(wd, "frames")
    os.makedirs(fdir, exist_ok=True)
    plate = make_plate()

    font = ImageFont.truetype(FONT_BOLD, 66)
    tag = ImageFont.truetype(FONT_BOLD, 26)

    def compose(text, path):
        img = plate.copy()
        d = ImageDraw.Draw(img)
        d.text((44, 44), "PLACEHOLDER VISUAL + TTS", font=tag, fill=(255, 255, 255, 140))
        d.text((44, 82), "SUBTITLE TIMING IS FINAL", font=tag, fill=(255, 255, 255, 140))
        if text:
            words, lines, cur = text.split(), [], ""
            for w in words:                             # wrap at ~24 chars
                probe = (cur + " " + w).strip()
                if len(probe) > 24 and cur:
                    lines.append(cur); cur = w
                else:
                    cur = probe
            if cur:
                lines.append(cur)
            lh = 82
            bw = max(d.textlength(l, font=font) for l in lines) + 56
            bh = lh * len(lines) + 34
            x0, y0 = (W - bw) / 2, H * 0.55 - bh / 2
            d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18,
                                fill=(255, 255, 255))
            for i, l in enumerate(lines):
                lw = d.textlength(l, font=font)
                d.text(((W - lw) / 2, y0 + 17 + i * lh), l, font=font, fill=(0, 0, 0))
        img.save(path)

    blank = os.path.join(fdir, "blank.png")
    compose(None, blank)

    out, cursor = [], 0.0
    for i, c in enumerate(seq):
        if c["t0"] - cursor > 0.02:                     # silence before this card
            out.append((blank, c["t0"] - cursor))
        png = os.path.join(fdir, f"f{i:03d}.png")
        if not os.path.exists(png):
            compose(c["text"], png)
        show = c["t1"] + CARD_GAP - c["t0"]
        out.append((png, show))
        cursor = c["t1"] + CARD_GAP
    if total - cursor > 0.02:
        out.append((blank, total - cursor))
    print(f"  {len(out)} frames composited")
    return out


# --------------------------------------------------------------------------
def build(reel):
    rid = reel["id"]
    wd = os.path.join(WORK, rid)
    os.makedirs(wd, exist_ok=True)
    print(f"\n=== Reel {rid} — {reel['title']} ===")

    # 1. Narrate each card separately so subtitle timing is exact, not estimated.
    seq, t, idx = [], 0.0, 0
    for bi, beat in enumerate(reel["beats"]):
        if bi:
            t += BEAT_GAP
        for text in cards_for(beat):
            aiff = os.path.join(wd, f"c{idx:03d}.aiff")
            wav = os.path.join(wd, f"c{idx:03d}.wav")
            if not os.path.exists(wav):
                run(["say", "-v", VOICE, "-r", str(WPM), "-o", aiff, text])
                # `say` pads every clip with leading/trailing silence. Left in,
                # 78 clips accumulate ~60s of dead air and the reel overruns.
                trim = ("silenceremove=start_periods=1:start_silence=0.02:"
                        "start_threshold=-45dB:detection=peak,areverse,"
                        "silenceremove=start_periods=1:start_silence=0.02:"
                        "start_threshold=-45dB:detection=peak,areverse")
                run(["ffmpeg", "-y", "-loglevel", "error", "-i", aiff,
                     "-af", trim, "-ar", "44100", "-ac", "2", wav])
                os.remove(aiff)
            d = dur(wav)
            seq.append({"wav": wav, "t0": t, "t1": t + d,
                        "text": text, "beat": beat["label"]})
            t += d + CARD_GAP
            idx += 1
    total = t + 1.0
    print(f"  {len(seq)} subtitle cards · {total/60:.0f}:{total%60:04.1f} runtime")

    # 2. Lay the clips onto a silent bed at their exact offsets.
    silent = os.path.join(wd, "bed.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"anullsrc=r=44100:cl=stereo:d={total:.2f}", silent])
    inputs, filters, labels = ["-i", silent], [], ["[0:a]"]
    for i, c in enumerate(seq, start=1):
        inputs += ["-i", c["wav"]]
        filters.append(f"[{i}:a]adelay={int(c['t0']*1000)}|{int(c['t0']*1000)}[d{i}]")
        labels.append(f"[d{i}]")
    voice = os.path.join(wd, "voice.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
         ";".join(filters) + ";" + "".join(labels) +
         f"amix=inputs={len(seq)+1}:duration=first:normalize=0,"
         "dynaudnorm=f=200:g=5[o]",
         "-map", "[o]", voice])

    # 3. Music bed, gain-matched to the processed voice.
    music = os.path.join(wd, "music.wav")
    synth_music(total, music)
    gain = (rms(voice) * MUSIC_RATIO) / rms(music)
    mixed = os.path.join(wd, "mixed.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music,
         "-filter_complex",
         f"[0:a]asplit=2[v][sc];[1:a]volume={gain:.5f}[m];"
         "[m][sc]sidechaincompress=threshold=0.10:ratio=2.5:attack=40:release=250[duck];"
         "[v][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[o]",
         "-map", "[o]", mixed])
    print(f"  music bed synthesised · gain {gain:.3f}x")

    # 4. Frames. This ffmpeg build ships without libass AND without drawtext
    #    (489 filters, zero text filters), so subtitles are composited in PIL
    #    and fed to ffmpeg as a timed image sequence instead.
    frames = render_frames(wd, seq, total)

    # 5. Concat the timed frames against the mixed audio.
    final = os.path.join(OUT, f"reel_{rid}_{reel['slug']}.mp4")
    listfile = os.path.join(wd, "frames.txt")
    with open(listfile, "w") as f:
        for png, d in frames:
            f.write(f"file '{png}'\nduration {d:.3f}\n")
        f.write(f"file '{frames[-1][0]}'\n")   # concat demuxer needs the tail repeated
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", listfile, "-i", mixed,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
         "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", final])
    got = dur(final)
    if abs(got - total) > 1.5:
        print(f"  WARNING: video {got:.1f}s vs expected {total:.1f}s")

    size = os.path.getsize(final) / 1e6
    print(f"  -> {os.path.relpath(final, ROOT)}  ({dur(final):.1f}s, {size:.1f} MB)")
    return final


def main():
    os.makedirs(WORK, exist_ok=True)
    reels = load_reels()
    want = [a.upper() for a in sys.argv[1:]]
    todo = [r for r in reels if not want or r["id"] in want]
    made = [build(r) for r in todo]
    print("\nDone:")
    for m in made:
        print("  " + os.path.relpath(m, ROOT))


if __name__ == "__main__":
    main()
