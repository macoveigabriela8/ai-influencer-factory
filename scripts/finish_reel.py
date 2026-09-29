#!/usr/bin/env python3
"""Assemble -> music bed -> MASTER TO -14 LUFS. One step, so nothing is skipped.

    python3 scripts/finish_reel.py 27

Replaces the hand-run sequence that shipped 25 reels at the wrong loudness.

WHY THE LOUDNESS STEP IS HERE AND NOT OPTIONAL (measured 2026-08-15):

    his source           -14.1 LUFS
    our dry master       -24.7 LUFS
    our music master     -30.8 LUFS   <- QUIETER than dry

`amix=inputs=2` normalises by input count, so adding the bed cost 6 dB, and
nobody had ever measured the output. Every reel before 26 went out roughly
16 dB below the accounts we are copying. On a feed where people scroll with
their volume fixed, that is a real handicap and it was invisible because
nothing asserted it.

The rule this came from: derive constants from the artifact and ASSERT THE
INVARIANT AFTER THE OPERATION. This script measures its own output and fails
loudly if the master is not within 1.5 dB of target.
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REELS = os.path.join(ROOT, "output", "reels")
MUSIC = os.path.join(ROOT, "output", "assets", "music", "chopin_prelude_28_6.mp3")
RATIO = 0.200                     # measured off his own mix; see CLAUDE.md
TARGET = -14.0


def run(c):
    subprocess.run(c, check=True, capture_output=True)


def lufs(path):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                        "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", o)
    return float(m[-1]) if m else None


def rms(path):
    o = subprocess.run(["ffmpeg", "-i", path, "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    for l in o.splitlines():
        if "mean_volume" in l:
            return 10 ** (float(l.split(":")[1].strip().split()[0]) / 20)
    return 0.1


def master(out):
    """Normalise to -14 LUFS and ASSERT it. The assert is the point: an
    unmeasured pipeline is how 25 reels shipped 16 dB below the competition."""
    # TWO-PASS loudnorm. Single pass is an estimate: QA 2026-08-15 measured the
    # result at -15.4 LUFS and -1.4 dBTP — inside tolerance, but 1.3 dB under
    # the source we are copying and 0.1 dB OVER the true-peak ceiling we asked
    # for. The measured pass removes both errors for one extra ffmpeg run.
    tmp = out + ".tmp.mp4"
    meas = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af",
         f"loudnorm=I={TARGET}:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True).stderr
    # TP=-1.7, not -1.5: loudnorm's limiter overshoots slightly, and QA measured
    # -1.4 then -1.3 dBTP against a -1.5 ceiling on two consecutive reels.
    # Asking for 0.2 dB more headroom lands the delivered peak inside spec.
    af = f"loudnorm=I={TARGET}:TP=-1.7:LRA=11"
    try:
        blob = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
        af += (f":measured_I={blob['input_i']}:measured_TP={blob['input_tp']}"
               f":measured_LRA={blob['input_lra']}"
               f":measured_thresh={blob['input_thresh']}"
               f":offset={blob['target_offset']}:linear=true")
    except Exception as e:
        print(f"  loudnorm measure pass unavailable ({e}) — single pass")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-c:v", "copy",
         # loudnorm resamples internally to 192 kHz and AAC caps at 96 kHz, so
         # WITHOUT this every master since the loudness fix shipped at 96 kHz —
         # non-standard for IG delivery, and the opposite of what make_story.py
         # goes out of its way to guarantee. Pin it back (QA, reel 35).
         "-af", af + ",aresample=48000", "-ar", "48000",
         "-c:a", "aac", "-b:a", "192k",
         # Trim the container to the SHORTER stream. QA found 0.467s of silent
         # video hanging past the end of the audio on reel 34 — kling ships
         # video slightly longer than the audio it was given.
         "-shortest", tmp])
    os.replace(tmp, out)
    got = lufs(out)
    ok = got is not None and abs(got - TARGET) <= 1.5
    print(f"  {os.path.basename(out)}  {got:+.1f} LUFS  {'ok' if ok else 'OUT OF SPEC'}")
    if not ok:
        sys.exit(f"master {out} is {got} LUFS, target {TARGET} — investigate")


def _band_excess_over_anchor(rid, H_):
    """Band detail of the RENDER divided by band detail of its ANCHOR.

    The anchor still is a known-clean plate of the same scene, so it is the
    natural reference. ~1.0 means the render's lower band looks like the
    composition we asked for; a large ratio means glyphs were added.

    Returns None when the anchor cannot be identified, so a missing file
    degrades to "no opinion" rather than a false PASS.
    """
    import numpy as np
    from PIL import Image, ImageFilter
    try:
        tasks_ = json.load(open(TASKS))
        anchor = tasks_[str(rid)]["anchor"]
    except Exception:
        return None
    png = os.path.join(ROOT, "output", "assets", "anchors", anchor + ".png")
    raw = os.path.join(ROOT, "output", "assets", f"avatar_{rid}.mp4")
    if not os.path.exists(png):
        return None

    def band_detail(im):
        w, h = im.size
        b = im.convert("L").crop((0, int(h * 0.60), w, int(h * 0.86)))
        b = b.resize((540, 250)).filter(ImageFilter.FIND_EDGES)
        px = list(b.getdata())
        return sum(1 for p in px if p > 60) / len(px)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "m.png")
        # the temporal MEDIAN frame: persistent text survives it, which is
        # exactly what we want to compare against the clean anchor
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-vf", "fps=1,tmix=frames=10:weights='1'",
                        "-frames:v", "1", f], check=True)
        if not os.path.exists(f):
            return None
        got = band_detail(Image.open(f))
    base = band_detail(Image.open(png))
    if base <= 0:
        return None
    return got / base


def measure_burn(rid):
    """Locate THIS render's burned glyphs and size the caption card to them.

    Isolates text by TEMPORAL-MEDIAN RESIDUAL: the scene is static (kling
    animates the face region only), so the per-pixel median over many frames is
    the clean plate, and anything that flickers against it is the burn. This is
    what the QA pass used, and it is far tighter than an edge detector — an edge
    detector also fires on the table's lit edge and the book, which is how reel
    32's card ended up ~100px taller than it needed to be.

    Returns (top, bottom) in 1080x1920 master coordinates, or None if clean.
    """
    import numpy as np
    from PIL import Image
    raw = os.path.join(ROOT, "output", "assets", f"avatar_{rid}.mp4")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", raw],
        capture_output=True, text=True).stdout.strip().split(",")
    W_, H_ = int(probe[0]), int(probe[1])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-vf", "fps=1,format=gray", f"{td}/%03d.png"], check=True)
        fs = sorted(os.listdir(td))
        if len(fs) < 8:
            return None
        stack = np.stack([np.asarray(Image.open(os.path.join(td, f)), dtype=np.float32)
                          for f in fs])
    # 🛑 TEMPORAL RESIDUAL ALONE IS BLIND TO PERSISTENT TEXT.
    # Found 2026-08-15: a test render carried TWO solid lines of gibberish in
    # nearly every frame, and this function reported 0/30 CLEAN. Constant text
    # sits in the median itself, so the residual against the median is ~zero.
    # It is the same blind spot the SOP already records for the density
    # heuristic ("persistent burned text reads as uniform density").
    #
    # The fix is a SECOND, anchor-referenced signal. The anchor still is a
    # known-clean plate of this exact scene, so band detail well above the
    # anchor's means something was added that was never in the composition.
    # Kept alongside the temporal test because each catches what the other
    # misses: temporal finds flickering text, anchor-diff finds constant text.
    # THRESHOLD 1.15, CALIBRATED ON KNOWN-GOOD *AND* KNOWN-BAD (2026-08-15).
    # My first guess was 1.6 and it would have missed the persistent-text render
    # this check exists to catch — which is precisely why the rule is to run a
    # new gate on verified inputs in BOTH directions before trusting it.
    #
    #   reel 26   0.97x  clean          reel 32   0.90x  burned, intermittent
    #   reel 27   0.94x  clean          test B    0.95x  burned, intermittent
    #                                   test A    1.40x  BURNED, PERSISTENT
    #
    # Clean tops out at 0.97 and persistent burn lands at 1.40, so 1.15 sits in
    # the gap with margin on both sides. Intermittent burns do not move this
    # signal at all — the temporal residual below is what catches those.
    anchor_excess = _band_excess_over_anchor(rid, H_)
    if anchor_excess is not None and anchor_excess > 1.15:
        print(f"  ⚠️  band detail is {anchor_excess:.2f}x the anchor's — "
              f"PERSISTENT burned text is likely. Read the contact sheet.")
    # OUTLINED-GLYPH TEST — locates the text without counting the book.
    #
    # Earlier attempts measured brightness or edges and could not tell kling's
    # glyphs from the open book's printed pages, which sit in the same band. On
    # reel 33 that produced a 386px card and the operator's note was "too much
    # white space in the caption pill". The distinguishing feature is that a
    # burned glyph is a PALE stroke with a DARK outline, so a very bright pixel
    # sits within a few px of a very dark one on the same row. Book pages are
    # bright but smooth and never satisfy it.
    #
    # Run over BOTH the median frame (persistent text survives it) and the max
    # frame (intermittent text survives that), because we have seen both.
    #
    # Calibrated 2026-08-15 on known-good AND known-bad:
    #   reel 26 clean -> NO GLYPHS      reel 33 persistent -> 1502-1530
    #   reel 27 clean -> NO GLYPHS      test A  two lines  -> 1463-1565
    #                                   reel 32            -> 1478 (single row)
    #
    # ⚠️ It is SPECIFIC but UNDER-READS the extent: on reel 32 it found one row
    # where the true span was 1422-1527. So it LOCATES the text and we expand by
    # PAD around it; never use the raw span as the card bounds.
    PAD = 25
    med = np.median(stack, axis=0)
    mx = stack.max(axis=0)
    glyph_rows = set()
    for frame in (med, mx):
        for y in range(int(H_ * 0.55), int(H_ * 0.95)):
            row = frame[y]
            n = 0
            for x in range(2, W_ - 2):
                if row[x] > 195 and row[x - 2:x + 3].min() < 95:
                    n += 1
            # THRESHOLD 8, RECALIBRATED 2026-08-15 ON SIX KNOWN RENDERS.
            # It was 18, tuned on reel 33 alone, and it MISSED reels 36 and 37 —
            # both visibly burned — because their glyphs are thinner and peak at
            # 15 and 12. They were handed a compact pill that did not cover the
            # text, and would have shipped that way if the contact sheet had not
            # been read. Tuning a threshold on ONE example is how you get a
            # number that fits that example and nothing else.
            #
            #   burned:  reel 33 -> 41    reel 36 -> 15    reel 37 -> 12
            #   clean:   reel 27 ->  5    reel 26 ->  3    reel 34 ->  2
            #
            # 8 sits in the gap with clear margin either side.
            if n > 8:
                glyph_rows.add(y)
    if glyph_rows:
        top = (min(glyph_rows) / H_ * 1920) - PAD
        bot = (max(glyph_rows) / H_ * 1920) + PAD
        # HORIZONTAL EXTENT TOO. The pill used to be forced to 940px wide on any
        # burned render, on the assumption the burn ran the full width. Measured
        # 2026-08-15 it does not — it spans 387-514px — so most of that width was
        # empty white ("minimize white empty space in the pill"). The burn is
        # NOT centred though (reel 36 sat at x450-856 of 1080), so a centred pill
        # must reach the farthest glyph from centre, not merely be as wide as
        # the glyphs.
        xs = []
        for frame in (med, mx):
            for y in glyph_rows:
                row = frame[y]
                for x in range(2, W_ - 2):
                    if row[x] > 195 and row[x - 2:x + 3].min() < 95:
                        xs.append(x)
        need_w = 0
        if xs:
            l, r = min(xs) / W_ * 1080, max(xs) / W_ * 1080
            need_w = int(2 * max(abs(l - 540), abs(r - 540)) + 100)
            print(f"  burn measure: glyphs x {l:.0f}-{r:.0f} of 1080 "
                  f"-> pill needs {need_w}px width (was hardcoded 940)")
        print(f"  burn measure: glyph rows {min(glyph_rows)}-{max(glyph_rows)} "
              f"of {H_} -> master y {top:.0f}-{bot:.0f} (incl. {PAD}px pad)")
        return int(top), int(bot), need_w
    print("  burn measure: no outlined glyphs found")
    return None

    resid = np.abs(stack - med).max(axis=0)          # brightest deviation per pixel
    peak = stack.max(axis=0)
    # Motion alone is NOT enough: the face and jaw are the biggest movers in the
    # frame, and a residual-only threshold reported y1056-1575 on reel 32 where
    # the true glyphs were y1422-1527. Burned glyphs are additionally PALE and
    # thin, so require brightness too and demand a substantial run of such
    # pixels across the row. Calibrated against the QA pass's ground truth.
    glyph = (resid > 55) & (peak > 165)
    rows = glyph.sum(axis=1)
    lo, hi = int(H_ * 0.60), int(H_ * 0.90)
    hits = [y for y in range(lo, hi) if rows[y] > 30]
    if not hits:
        print("  burn measure: no burned text detected")
        return None
    top = min(hits) / H_ * 1920
    bot = max(hits) / H_ * 1920
    print(f"  burn measure: raw y {min(hits)}-{max(hits)} of {H_} "
          f"-> master y {top:.0f}-{bot:.0f}")
    return int(top), int(bot)


def show(path):
    """Open the finished master for the operator. ALWAYS, automatically.

    Standing instruction 2026-08-15: every finished reel opens in QuickTime the
    moment it is built, without being asked.

    It must be `open -a "QuickTime Player"`, never a bare `open` — bare `open`
    hands audio to Apple Music, which the user does not pay for.
    """
    subprocess.run(["open", "-a", "QuickTime Player", path], check=False)
    print(f"  opened {os.path.basename(path)} in QuickTime Player")


def subtitle_gate(rid):
    """HARD GATE on the raw clip, before a single frame is assembled.

    Reel 28 shipped with kling's gibberish burned under every caption because
    this check was run on reels 26 and 27 and simply SKIPPED on 28 — it was a
    manual step, and a manual step in a batch is a step that eventually does not
    happen. 616 credits. It is now code, it runs first, and it exits non-zero.

    A flag is not proof of a defect: our own anchors put an open book in the
    band, which is printed text and saturates a text-density detector. So the
    gate does not decide alone — it writes a contact sheet and REFUSES to
    continue until a human has looked at it.
    """
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from qc_gate import burned_text_times
    raw = os.path.join(ROOT, "output", "assets", f"avatar_{rid}.mp4")
    hits = burned_text_times(raw)
    sheet = os.path.join(ROOT, "output", "assets", f"band_{rid}.png")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", raw],
        capture_output=True, text=True).stdout.strip().split(",")
    W_, H_ = int(probe[0]), int(probe[1])
    y0, y1 = int(H_ * 0.58), int(H_ * 0.90)     # wider than the metric band, so
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,   # nothing sits just
         "-vf", f"crop={W_}:{y1-y0}:0:{y0},fps=1/5,scale=520:-1,tile=2x6",
         "-frames:v", "1", sheet])              # outside the crop, as it did
    print(f"  subtitle gate: {len(hits)} flagged samples")
    print(f"  CONTACT SHEET -> {os.path.relpath(sheet, ROOT)}")
    print("  READ IT. Our own open book flags this gate; burned text is a "
          "SECOND line of pale gibberish, usually just under the caption.")
    if os.environ.get("BAND_OK") != "1":
        sys.exit("  refusing to assemble until the sheet is checked. "
                 "Re-run with BAND_OK=1 once you have read it.")


def main():
    rid = sys.argv[1]
    W = "/tmp/finish_%s" % rid
    os.makedirs(W, exist_ok=True)
    subtitle_gate(rid)

    # SMALLEST PILL THAT STILL COVERS ANY TEXT (operator instruction 2026-08-15:
    # "smallest caption pill, so it looks good and covers text if any").
    #
    #   burned -> the card stretches to exactly THIS render's glyphs plus margin
    #   clean  -> the card collapses to an ordinary caption pill wrapped to the
    #             text, because there is nothing to hide
    #
    # Previously a clean render still got the full-height cover, which is the
    # heavy look that was rejected. The sentinels (top huge, bottom zero) make
    # the min()/max() in assemble_en fall through to the text's own bounds.
    env = dict(os.environ)
    box = measure_burn(rid)
    if box:
        # NO extra margin here — measure_burn already adds its own PAD, and
        # stacking a second margin on top produced a 386px card and the note
        # "too much white space in the caption pill". One padding step, applied
        # where the measurement is made.
        env["BURN_TOP"] = str(max(1200, box[0]))
        env["BURN_BOTTOM"] = str(min(1700, box[1]))
        if len(box) > 2 and box[2]:
            env["BURN_W"] = str(box[2])
        print(f"  caption card -> y {env['BURN_TOP']}-{env['BURN_BOTTOM']} "
              f"({int(env['BURN_BOTTOM']) - int(env['BURN_TOP'])}px tall, "
              f"sized to this render's burn)")
    else:
        env["BURN_TOP"], env["BURN_BOTTOM"] = "99999", "0"
        print("  caption card -> compact pill (no burn detected, nothing to hide)")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                                                 "assemble_en.py"), rid],
                   check=True, env=env)
    dry = os.path.join(REELS, f"reel_{rid}_dry.mp4")

    # MUSIC IS OFF BY DEFAULT from reel 30 (operator, 2026-08-15) — the reel
    # ships dry so a trending sound can be chosen in the Instagram app, which is
    # the only place trending audio can be attached. Pass --music to bake the
    # Chopin bed back in for a specific reel.
    if "--music" not in sys.argv:
        master(dry)
        show(dry)
        return

    total = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", dry], capture_output=True, text=True).stdout)

    voice, bed, mixed = f"{W}/v.wav", f"{W}/m.wav", f"{W}/mix.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", dry, "-vn",
         "-ac", "2", "-ar", "44100", voice])
    run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1",
         "-i", MUSIC, "-af",
         f"atrim=0:{total:.2f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2,"
         f"afade=t=out:st={max(0, total-3):.2f}:d=3",
         "-ac", "2", "-ar", "44100", bed])
    gain = (rms(voice) * RATIO) / rms(bed)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", bed,
         "-filter_complex",
         f"[1:a]volume={gain:.4f}[m];"
         f"[m][0:a]sidechaincompress=threshold=0.05:ratio=2.5:attack=20:"
         f"release=500[md];[0:a][md]amix=inputs=2:duration=first:weights=1 1[a]",
         "-map", "[a]", mixed])
    music_out = os.path.join(REELS, f"reel_{rid}_music.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", dry, "-i", mixed,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-shortest", music_out])

    for out in (dry, music_out):
        master(out)
    show(music_out)


if __name__ == "__main__":
    main()
