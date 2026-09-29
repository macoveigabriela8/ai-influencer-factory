#!/usr/bin/env python3
"""Stitch the Seedance clips into a finished, postable reel.

    python3 scripts/assemble_reel.py 1 2 3 4 5 6 7

Concat -> transcribe -> caption -> music bed -> 1080x1920 master.

WHY THE CAPTIONS ARE TRANSCRIBED RATHER THAN TAKEN FROM THE SCRIPT. Seedance
re-performs each line at its own pace instead of reproducing our ElevenLabs
recording (measured: waveform correlation 0.148 against the reference chunk).
So the script says WHAT is spoken but not WHEN. Timing the cards off the script
would drift within the first sentence. Whisper word-timestamps on the ACTUAL
rendered audio is the only source of truth here -- and it has the useful side
effect of catching a bad generation, since a clip that speaks gibberish
produces gibberish cards rather than silently shipping.

WHY THE MUSIC IS SYNTHESISED. Two sustained partials at G3+Bb3 -- the interval
measured off his 4.0M-view reel -- through tremolo and a reverb tail. Royalty
free by construction, which matters for a commercial page: no library licence
to track, no Instagram audio claim, no third-party takedown risk on the asset
the whole account is being launched with.

LEVELS ARE MEASURED, NOT TASTE. The bed sits at 40% of voice RMS pre-duck and
is sidechain-ducked under the speech, so it recedes while he talks and returns
in the gaps. That ratio came off his own mix; the gap behaviour is what makes
his pauses read as deliberate rather than as dead air.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
OUT = os.path.join(ROOT, "output", "reels")

# PER-REEL CONFIG. Clip numbers restart at 1 for every reel, so the video stem,
# the work directory and the output name all have to be namespaced -- rendering
# reel 2 through a hardcoded reel-B path is how reel B's seedance_01.mp4 got
# destroyed on 2026-07-25.
REEL = os.environ.get("REEL", "B")
REELS = {
    "B": {
        "stem": "seedance",
        "out": "reel_B_dreams_of_the_dead_v2",
        # The comment CTA rides at the top from CTA_AFTER onward; CTA_CLOSE
        # drops into the caption band for the final CTA_SECS.
        "cta_top": "Write their name in the comments",
        "cta_close": "Just the name. Nothing else.",
    },
    "2": {
        "stem": "sd2",
        "out": "reel_2_glass_of_water",
        # Reel 2 carries MORE on screen than reel B did, because two of its
        # spoken beats could not be generated at all: Seedance refuses CTA
        # lines (8 failed generations across both reels -- see CLAUDE.md KNOWN
        # UNSOLVED). The share trigger and the link line are therefore drawn
        # rather than spoken, which is why the closing card here is doing real
        # work rather than reinforcing something already said aloud.
        # The two cards must ask for DIFFERENT things. First pass set the top
        # band to "I WILL DO IT TODAY" and the closing card to 'Write "I will do
        # it today" below', which is the same sentence twice on screen at once
        # -- it reads as a rendering fault rather than as emphasis. The top band
        # carries the comment instruction (supplying the literal words to type,
        # which is what removes the hesitation that stops people commenting) and
        # the closing card carries the RETURN VISIT, which is the separate,
        # higher-value ask and the one his own reels close on.
        # His wording, split across the two cards. Measured 6/7 of his reels
        # SPEAK this line; we draw it instead only because Seedance deletes
        # social-action imperatives from speech. Keep the phrase short and
        # literal -- his are "abundance", "health", "I love you mom".
        "cta_top": 'Write in the comments\n"I will do it today"',
        "cta_close": "Come back tomorrow and tell me what changed.",
    },
    "3": {
        "stem": "sd3",
        "out": "reel_3_seven_grains_of_rice",
        # Reel 3 clips come from kling/ai-avatar-pro (audio-driven lip-sync),
        # not Seedance -- the reference audio is spoken verbatim, so the link
        # line is safely in the SPOKEN close. The drawn cards keep the split
        # rule: top band = comment instruction with the literal word, closing
        # card = the return visit (his BIG06 word is "abundance").
        "cta_top": 'Write in the comments\n"Abundance"',
        "cta_close": "Come back on day 21. Tell me what changed.",
    },
    "4": {
        "stem": "sd4",
        "out": "reel_4_salt_wash",
        "cta_top": "Write in the comments the date you watch this",
        "cta_close": "Come back and tell me what changed.",
    },
    "5": {
        "stem": "sd5",
        "out": "reel_5_old_key",
        "cta_top": 'Write in the comments\n"My paths are opening"',
        "cta_close": "Come back after night three. Tell me what opened.",
    },
    "6": {
        "stem": "sd6",
        "out": "reel_6_words_to_mother",
        # BIG07's own pairing: comment word + share trigger. The share ask is
        # the closing card (drawn, not spoken -- kling could speak it, but the
        # drawn layout is the tested format).
        "cta_top": 'Write in the comments\n"I love you mom"',
        "cta_close": "Send this to your mother right now.",
    },
    "7": {
        "stem": "sd7",
        "out": "reel_7_first_daughter",
        "cta_top": 'Write in the comments\n"My daughter"',
        "cta_close": "Send this to her. She will understand.",
    },
    "8": {
        "stem": "sd8",
        "out": "reel_8_the_dark_around_you",
        "cta_top": 'Write in the comments\n"Amen"',
        "cta_close": "Come back after the third night.",
    },
    "9": {
        "stem": "sd9",
        "out": "reel_9_three_points",
        "cta_top": 'Write in the comments\n"I cleanse"',
        "cta_close": "Come back tomorrow. Tell me what you found.",
    },
    "10": {
        "stem": "sd10",
        "out": "reel_10_not_tired_exhausted",
        "cta_top": 'Write in the comments\n"Enough"',
        "cta_close": "Send this to someone who needs to read it.",
    },
    "11": {
        "stem": "sd11",
        "out": "reel_11_morning_seal",
        "cta_top": 'Write in the comments\n"My day is protected"',
        "cta_close": "Come back on day three. Tell me what changed.",
    },
    # Batch 12-20 (2026-08-07): top CTA = comment instruction with literal
    # words, close CTA = return visit / share. Never the same sentence.
    "12": {
        "stem": "sd12",
        "out": "reel_12_four_morning_things",
        "cta_top": 'Write in the comments\n"Peace"',
        "cta_close": "Say them tomorrow morning. Then come back.",
    },
    "13": {
        "stem": "sd13",
        "out": "reel_13_my_story",
        "cta_top": 'Write in the comments\nwhere you are watching from',
        "cta_close": "Follow me. This story is not finished.",
    },
    "14": {
        "stem": "sd14",
        "out": "reel_14_three_things_to_god",
        "cta_top": 'Write in the comments\n"Amen"',
        "cta_close": "Send this prayer to someone you love.",
    },
    "15": {
        "stem": "sd15",
        "out": "reel_15_forgive_or_go",
        "cta_top": 'Write in the comments\n"Peace over pain"',
        "cta_close": "Send this to someone standing at this door.",
    },
    "17": {
        "stem": "sd17",
        "out": "reel_17_phone_bedroom",
        "cta_top": 'Write in the comments\n"The morning is mine"',
        "cta_close": "Try one week. Come back and tell me.",
    },
    "18": {
        "stem": "sd18",
        "out": "reel_18_salt_stand",
        "cta_top": 'Write in the comments\n"Tonight"',
        "cta_close": "Come back after night one. Tell me how you slept.",
    },
    "19": {
        "stem": "sd19",
        "out": "reel_19_guardians",
        "cta_top": 'Write in the comments\n"My guardians"',
        "cta_close": "Send this to someone whose dog sleeps by their door.",
    },
    "22": {
        "stem": "sd22_std",
        "out": "reel_22_house_blessing",
        # First reel on the full source format: comment CTA is SPOKEN in the
        # script, so nothing is drawn — subtitles only, like the originals.
        "cta_top": "",
        "cta_close": "",
    },
    "23": {
        "stem": "sd23_std",
        "out": "reel_23_comfort_trap",
        "cta_top": "",
        "cta_close": "",
    },
    "16": {
        "stem": "sd16_std",
        "out": "reel_16_dogs_on_bed",
        "cta_top": 'Write in the comments\n"Tonight she guards me"',
        # Closing-screen rule (measured off BIG01/TOP10/YM): the originals draw
        # NOTHING at the close. Empty cta_close skips the closing card.
        "cta_close": "",
    },
    "20": {
        "stem": "sd20",
        "out": "reel_20_speak_gently",
        "cta_top": 'Write in the comments\n"I am learning"',
        "cta_close": "Save this for the day the old voice returns.",
    },
}
CFG = REELS[REEL]
WORK = os.path.join(OUT, f".work{REEL}")

W, H = 1080, 1920
# 0.40 was his measured ratio, but RMS-matching a synthesised bed to a real
# piano under-delivers badly: his bed is a struck string with broadband attack
# and inharmonic partials, ours is four sine tones. Equal RMS is nowhere near
# equal loudness, so the bed was barely audible. Raised by ear against the
# rendered master.
MUSIC_RATIO = 0.95
# ...but 0.95 is a SYNTH-ONLY correction. Four sine tones read far quieter than
# their RMS implies, because loudness perception tracks spectral spread and a
# real instrument has broadband attack and inharmonic partials that sines lack.
# A licensed recording needs no such compensation, so it goes back to 0.40 --
# the ratio actually measured off his own mix. Overridable with MUSIC_RATIO=.
MUSIC_RATIO_REAL = 0.40
MAX_WORDS = 7
# HARD RULE: no card is ever three rows tall. Caption cards reach this by being
# split across two cards; CTA cards, which cannot be split, reach it by having
# their font shrunk until they fit. A single taller card makes the whole text
# block jump vertically mid-reel, which is the most visible defect the layout
# can have.
MAX_ROWS = 2
MIN_FONT = 38
# INSTAGRAM SAFE ZONES on a 1080x1920 reel. Instagram draws its own chrome over
# the frame: caption/username/audio ticker across the bottom ~420px, the
# like/comment/share rail down the right ~200px, and ~220px of top inset. Text
# outside these bounds is text the viewer never reads.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 230, 430, 190
# Cards sit lower than the optical centre. Measured off his reels the band is
# ~0.55H; the user wants them 20% further down, which also clears his face at
# the framing Seedance gives us.
CAPTION_Y = 0.72
# The CTA rides at the TOP for the whole reel after the hook, so a viewer who
# arrives mid-scroll sees the ask without waiting for the close. It is drawn
# into the same PNG as the caption card rather than as a second overlay track,
# which keeps the filtergraph to a single overlay.
CTA_TOP_Y = 0.19
CTA_AFTER = 15.0
# The comment CTA never rendered as speech -- four generations, the last one a
# fluent monk platitude rather than our line, which reads as the character prior
# refusing a social-media instruction. It goes on screen instead. He runs the
# comment CTA before the link CTA, so this card lands over the product bridge.
CTA_TEXT = CFG["cta_top"]
# The closing card keeps the top band and puts DIFFERENT words below it -- the
# same text in both places reads as a rendering fault, not as emphasis. This
# line is also the more useful half: naming the exact scope of the ask ("just
# the name") is what removes the hesitation that stops people commenting. He
# does the same thing, supplying the literal words to type ("I will do it today").
CTA_CLOSE = CFG["cta_close"]
CTA_SECS = 4.5
WRAP = 24
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", p]).stdout.strip())


def clip_path(n):
    # Reel B's clip 1 lives under a different name: it was the pipeline probe,
    # rendered before the chunk plan existed. That special case is reel-B only
    # -- reel 2's clip 1 is a normal numbered clip, and routing it through
    # sd_v01.mp4 would silently splice reel B's opening onto reel 2.
    if REEL == "B" and n == 1:
        return os.path.join(ART, "sd_v01.mp4")
    # PREFER THE ALIGNED CLIP when align_clips.py has produced one. Each clip is
    # a separate generation and they disagree on framing by up to 4.1% scale and
    # 27px -- monotonically, so it reads as a slow creep rather than jitter and
    # is visible on playback. The aligned copy carries the SAME audio stream
    # (copied, not re-encoded), so a clip that passed the QC gate still passes.
    aligned = os.path.join(ART, f"{CFG['stem']}_{n:02d}_aligned.mp4")
    if os.path.exists(aligned):
        return aligned
    return os.path.join(ART, f"{CFG['stem']}_{n:02d}.mp4")


def concat(ns, out):
    """Join the clips, normalising to a common format first.

    Re-encoding rather than stream-copying: the clips come back from separate
    generations and a concat demuxer copy will desync audio if any of them
    differs in timebase or in how the AAC priming samples are counted. At seven
    clips a re-encode costs seconds and removes the whole class of problem.
    """
    # PAD EACH CLIP'S AUDIO TO ITS OWN VIDEO DURATION FIRST. kling/ai-avatar
    # clips (reel 3+) come back with the audio stream 0.18-0.31s SHORTER than
    # the video, and the concat demuxer joins streams independently -- so every
    # deficit pulls all later audio earlier. By clip 6 the voice ran 1.08s
    # ahead of the lips, which read as "lip sync drifts late in the video".
    # apad + -t <video dur> makes every clip's streams equal length, so the
    # joins stay locked. Seedance clips have matched streams; padding them by
    # 0ms is a no-op, so this is safe for every reel.
    # One filtergraph, one encode: per-clip apad(whole_dur=<video dur>) is
    # sample-accurate, so no per-file AAC/MP4 frame rounding survives into the
    # joins (padding per-file left a residual 23ms/clip = 0.14s by clip 6).
    # unsharp + fine grain in the same pass de-plastics the kling avatar skin
    # (Laplacian ~90 vs Seedance ~435); applied before caption compositing so
    # the text stays crisp. Approved on an A/B of reel 3 clip 2 (2026-07-30).
    srcs = [clip_path(n) for n in ns]
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    fg = []
    for i, src in enumerate(srcs):
        cmd += ["-i", src]
        vd = float(run(["ffprobe", "-v", "error", "-select_streams", "v",
                        "-show_entries", "stream=duration",
                        "-of", "default=nw=1:nk=1", src]).stdout.strip())
        fg.append(f"[{i}:v]fps=24,unsharp=5:5:0.6:5:5:0.0,"
                  f"noise=alls=6:allf=t+u,trim=duration={vd:.4f},setpts=PTS-STARTPTS[v{i}];"
                  f"[{i}:a]aresample=44100,apad=whole_dur={vd:.4f},"
                  f"atrim=duration={vd:.4f},asetpts=PTS-STARTPTS[a{i}]")
    fg.append("".join(f"[v{i}][a{i}]" for i in range(len(srcs))) +
              f"concat=n={len(srcs)}:v=1:a=1[v][a]")
    cmd += ["-filter_complex", ";".join(fg), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", out]
    run(cmd)
    return out


def transcribe(video):
    import mlx_whisper
    wav = os.path.join(WORK, "voice.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
         "-ac", "1", "-ar", "16000", wav])
    r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-small.en-mlx",
                               word_timestamps=True)
    words = [w for s in r["segments"] for w in s.get("words", [])]
    return [(w["word"].strip(), w["start"], w["end"]) for w in words if w["word"].strip()]


def cards(words):
    """Group words into <=7-word cards, breaking at punctuation.

    Breaking on sentence-final punctuation as well as on the word count keeps a
    card from straddling two thoughts, which is what makes his cards readable at
    scroll speed -- the eye gets one complete idea per card.
    """
    out, cur = [], []
    for w, a, b in words:
        cur.append((w, a, b))
        if len(cur) >= MAX_WORDS or w.endswith((".", "?", "!", ",", ";", ":")):
            out.append(cur); cur = []
    if cur:
        out.append(cur)

    # HARD CAP AT TWO ROWS. MAX_WORDS only approximates height -- seven short
    # words fit on one line, seven long ones spill to three -- and a card that
    # is one row taller than its neighbours makes the whole block jump vertically
    # mid-reel. Measuring and splitting is the only way to guarantee it. Splits
    # happen at a word boundary and each half keeps its own real timestamps, so
    # nothing drifts.
    from PIL import Image, ImageDraw, ImageFont
    d = ImageDraw.Draw(Image.new("RGBA", (W, H)))
    f = ImageFont.truetype(FONT_PATH, 64)

    def rows(ws):
        return len(wrap(" ".join(x[0] for x in ws), f, d).split("\n"))

    capped = []
    for c in out:
        while rows(c) > 2 and len(c) > 1:
            # Peel words off the end until the head fits two rows.
            k = len(c) - 1
            while k > 1 and rows(c[:k]) > 2:
                k -= 1
            capped.append(c[:k])
            c = c[k:]
        capped.append(c)
    return [(" ".join(x[0] for x in c), c[0][1], c[-1][2]) for c in capped]


def wrap(text, font, d):
    # Wrap by MEASURED pixel width, not character count. The usable width is the
    # frame minus twice the right-rail inset, since the cards are centred and a
    # card wide enough to reach the rail on the right also reaches it mirrored on
    # the left. Character counting cannot know this -- "Will" and "mmmm" are the
    # same four characters and very different widths.
    # An explicit \n in the text is a hard break -- used by CTA cards to keep
    # the quoted comment phrase ("I love you mom") whole on its own row instead
    # of splitting it mid-quote across rows.
    if "\n" in text:
        return "\n".join(wrap(part, font, d) for part in text.split("\n"))
    limit = W - 2 * SAFE_RIGHT - 56
    lines, cur = [], ""
    for w in text.split():
        probe = (cur + " " + w).strip()
        if d.textlength(probe, font=font) > limit and cur:
            lines.append(cur); cur = w
        else:
            cur = probe
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def card_track(cs, total):
    """Render the captions as a transparent overlay track.

    This ffmpeg build ships WITHOUT libass, libfreetype and drawtext -- checked,
    not assumed (`ffmpeg -filters` lists none of ass/subtitles/drawtext). So
    there is no way to burn text from inside a filtergraph at all, and the
    captions have to be drawn as RGBA images by PIL and composited. The existing
    build_reels.py reached the same conclusion, which is why it composites PNGs.

    Rather than emit one overlay filter per card (34+ chained overlays, which
    gets slow and fragile), every card becomes one PNG and the concat demuxer
    turns the sequence into a single alpha video with per-card durations. That
    is one overlay in the final graph regardless of card count.
    """
    from PIL import Image, ImageDraw, ImageFont
    fdir = os.path.join(WORK, "cards")
    os.makedirs(fdir, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 64)
    cta_font = ImageFont.truetype(FONT_PATH, 52)

    def fit(text, f, d):
        """Shrink the font until the text wraps to at most MAX_ROWS lines.

        The caption cards are held to two rows by SPLITTING them (see cards()),
        which works because a caption can be broken across two cards without
        losing anything. A CTA card cannot be split -- it is one instruction and
        both halves have to be readable at once -- so it is held to two rows by
        shrinking instead. Without this, 'Come back tomorrow and tell me.' wraps
        to three rows at 52px and the closing card grows a row taller than every
        other card in the reel, which reads as a layout fault.
        """
        size = f.size
        while size > MIN_FONT:
            ff = ImageFont.truetype(FONT_PATH, size)
            if len(wrap(text, ff, d).split("\n")) <= MAX_ROWS:
                return ff
            size -= 2
        return ImageFont.truetype(FONT_PATH, MIN_FONT)

    def band(d, text, cy, f, fill, fg):
        """Draw one centred rounded-rect text band, clamped into the safe area."""
        f = fit(text, f, d)
        lines = wrap(text, f, d).split("\n")
        lh = int(f.size * 1.28)
        bw = max(d.textlength(l, font=f) for l in lines) + 56
        bh = lh * len(lines) + 34
        y0 = min(max(cy - bh / 2, SAFE_TOP), H - SAFE_BOTTOM - bh)
        x0 = (W - bw) / 2
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18, fill=fill)
        for i, l in enumerate(lines):
            lw = d.textlength(l, font=f)
            d.text(((W - lw) / 2, y0 + 17 + i * lh), l, font=f, fill=fg)

    def draw(text, path, cta=False):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if text:
            band(d, text, H * CAPTION_Y, font, (255, 255, 255, 255), (0, 0, 0, 255))
        if cta:
            # Dark band, not white: it has to read as a persistent instruction
            # from the page rather than as another line of his speech.
            band(d, CTA_TEXT, H * CTA_TOP_Y, cta_font, (17, 17, 17, 232),
                 (255, 255, 255, 255))
        img.save(path)

    # Each card is HELD until the next one starts, rather than disappearing at
    # its own last word. Showing only the word span leaves the frame bare during
    # every inter-word gap, so the caption strobes on and off ~34 times a minute
    # -- visible as flicker and nothing like his reels, where text is on screen
    # continuously and simply swaps. The only real gap left is any lead-in
    # before the first word.
    blank = os.path.join(fdir, "blank.png")
    draw("", blank)
    blank_cta = os.path.join(fdir, "blank_cta.png")
    draw("", blank_cta, cta=True)

    entries, cursor = [], 0.0
    for i, (t, a, b) in enumerate(cs):
        on = a >= CTA_AFTER          # CTA rides along once the hook has landed
        if a - cursor > 0.02:
            entries.append((blank_cta if on else blank, a - cursor))
        nxt = cs[i + 1][1] if i + 1 < len(cs) else total
        p = os.path.join(fdir, f"c{i:03d}.png")
        draw(t, p, cta=on)
        entries.append((p, max(0.10, nxt - a)))
        cursor = max(b, nxt)
    # The comment CTA, held over the tail. He runs comment-CTA then link-CTA;
    # ours only ever rendered the link half as speech, so this restores the
    # first half as text over the closing lines.
    if total - cursor > 0.02:
        entries.append((blank, total - cursor))

    if CTA_TEXT and CTA_CLOSE:
        # Reclaim the final CTA_SECS from whatever is on screen -- the closing
        # narration card would otherwise hold there, and the CTA has to be the
        # last thing read before the loop restarts.
        need = CTA_SECS
        while need > 0.01 and entries:
            p, d_ = entries[-1]
            if d_ > need:
                entries[-1] = (p, d_ - need)
                need = 0
            else:
                entries.pop()
                need -= d_
        # Closing card: the CTA drops to the caption band too, so the last thing
        # on screen before the loop restarts says it twice.
        cta = os.path.join(fdir, "cta.png")
        draw(CTA_CLOSE, cta, cta=True)
        entries.append((cta, CTA_SECS))

    lst = os.path.join(WORK, "cards.txt")
    with open(lst, "w") as f:
        for p, d_ in entries:
            f.write(f"file '{p}'\nduration {d_:.3f}\n")
        f.write(f"file '{entries[-1][0]}'\n")     # demuxer drops the last duration
    print(f"  {len(cs)} cards drawn ({len(entries)} timeline entries)")
    return lst


def rms(p):
    import array, wave
    tmp = p + ".rms.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ar", "22050", "-ac", "1", tmp])
    with wave.open(tmp) as w:
        raw = w.readframes(w.getnframes())
    os.remove(tmp)
    a = array.array("h", raw)
    return (sum(float(x) ** 2 for x in a) / len(a)) ** 0.5 / 32768 or 1e-6


def synth_music(seconds, path):
    # SADDER than the reel-B bed. Same G-minor root measured off his 4.0M reel,
    # but three changes carry the grief: a G2 sub-octave drone underneath (98Hz)
    # so the chord sits heavy rather than airy; a minor SIXTH added on top (Eb4,
    # 311Hz) -- the interval that makes a minor triad ache rather than merely
    # sound minor; and a slower, deeper tremolo so it breathes at roughly the
    # pace of his pauses instead of shimmering.
    expr = (f"aevalsrc=0.20*sin(2*PI*98*t)+0.30*sin(2*PI*196*t)"
            f"+0.24*sin(2*PI*233*t)+0.14*sin(2*PI*311*t)"
            f"+0.06*sin(2*PI*392*t):s=44100:d={seconds:.2f}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", expr,
         "-af", ("tremolo=f=0.11:d=0.62,"
                 "aecho=0.8:0.9:800|1500:0.40|0.28,"
                 "lowpass=f=1100,highpass=f=70,"
                 "afade=t=in:st=0:d=4,"
                 f"afade=t=out:st={max(0, seconds-5):.2f}:d=5"),
         "-ac", "2", path])
    return path


def finish(raw, audio, cardlist, suffix=""):
    # The dry master and the music version are separate files, never overwriting
    # each other: the dry one is what goes to Instagram (in-app audio buys a
    # place on the track's audio page, which an uploaded bed forfeits), and the
    # music one is the fallback if the business-account catalogue is too thin.
    final = os.path.join(OUT, f"{CFG['out']}{suffix}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", audio,
         "-f", "concat", "-safe", "0", "-i", cardlist,
         "-filter_complex",
         f"[0:v]scale={W}:{H}:flags=lanczos[bg];[bg][2:v]overlay=0:0:format=auto[v]",
         "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", final])
    print(f"\n  -> {os.path.relpath(final, ROOT)}  {dur(final):.2f}s")
    return final


def main(ns, with_music=False):
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    raw = concat(ns, os.path.join(WORK, "raw.mp4"))
    total = dur(raw)
    print(f"  concat: {len(ns)} clips, {total:.2f}s")

    cs = cards(transcribe(raw))
    cardlist = card_track(cs, total)

    voice = os.path.join(WORK, "voice_only.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-vn",
         "-ac", "2", "-ar", "44100", voice])

    # DEFAULT: ship the narration alone. The user lays their own piano over the
    # master, and a baked-in bed cannot be removed -- it would fight whatever
    # they put on top. The synthesised bed stays available behind --music
    # because the levels below are measured off his own mix and are still the
    # right target if a bed is ever wanted.
    if not with_music:
        # BUG FIXED 2026-07-26: this branch used to fall through into the music
        # mix below, so `mixed` was immediately overwritten and the "voice only"
        # master silently shipped WITH a bed anyway. Reel B's dry master was
        # assembled before that regression, so it is unaffected -- but the
        # printed reassurance was not true for any later run.
        print("  voice only -- no music bed (add yours in post)")
        return finish(raw, voice, cardlist)

    # MUSIC=<path> swaps the synthesised bed for a real track. The synth bed was
    # rejected by the user on reel B ("synth bed unusable"), which is the whole
    # reason a licensed track is being sourced -- but the LEVEL logic below is
    # still the measured one and applies to either source.
    ext = os.environ.get("MUSIC")
    if ext:
        music = os.path.join(WORK, "music_ext.wav")
        # Trim/pad the track to the reel length and fade both ends, so a track
        # of any length drops in without clipping mid-phrase at the loop point.
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", ext,
             "-af", (f"atrim=0:{total:.2f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:st=0:d=2,"
                     f"afade=t=out:st={max(0, total - 3):.2f}:d=3"),
             "-ac", "2", "-ar", "44100", music])
        print(f"  music: {os.path.basename(ext)}")
    else:
        music = synth_music(total, os.path.join(WORK, "music.wav"))
        print("  music: synthesised bed")
    ratio = float(os.environ.get("MUSIC_RATIO",
                                 MUSIC_RATIO_REAL if ext else MUSIC_RATIO))
    gain = (rms(voice) * ratio) / rms(music)
    mixed = os.path.join(WORK, "mixed.wav")
    # sidechaincompress keyed off the voice pulls the bed down while he speaks
    # and lets it swell back in the gaps.
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music,
         "-filter_complex",
         f"[1:a]volume={gain:.4f}[m];"
         # Gentler duck than before (ratio 6 -> 2.5): at ratio 6 the bed was
         # crushed almost to nothing the moment he spoke, so it was only ever
         # audible in the gaps -- which read as "barely there" across a reel
         # that is 90% speech.
         f"[m][0:a]sidechaincompress=threshold=0.05:ratio=2.5:attack=20:release=500[md];"
         f"[0:a][md]amix=inputs=2:duration=first:weights=1 1[a]",
         "-map", "[a]", mixed])
    print(f"  bed at {ratio:.2f}x voice RMS · gain {gain:.3f}x · ducked under speech")
    return finish(raw, mixed, cardlist, "_music")


if __name__ == "__main__":
    a = sys.argv[1:]
    music = "--music" in a
    main([int(x) for x in a if x != "--music"] or [1, 2, 3, 4], music)
