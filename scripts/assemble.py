#!/usr/bin/env python3
"""
Turn a folder of Google Flow segments into a finished reel.

    python3 scripts/assemble.py A output/assets/flow_A/

    concat -> transcribe -> retime to his pace -> alignment for subs.py

Flow returns one file per 10s segment with no audio track we control, so pace
can't be dialled in at generation time -- it's whatever the model felt like.
This measures the assembled cut and retimes it to his 161.6 wpm.

setpts=PTS/N with atempo=N retimes video and audio by the identical factor, so
lip sync survives.

The cap was 1.20x on the theory that atempo becomes audible past it. That is the
threshold for MUSIC, where the artefacts land on transients and sustained tones.
Speech tolerates far more -- podcast apps run 1.5x as a default listening speed
and nobody describes it as processed. What DOES break first is not the audio at
all: it is the video. setpts speeds up blinks, breathing and hand gestures by the
same factor, and a monk who blinks 1.4x too fast reads as nervous rather than
serene, which is the one quality this character cannot lose. 1.40 is where that
starts to show, so that is the cap -- set by the face, not by the ear.

A retime this large is a symptom, not a fix. It also means the reel cost ~40%
more credits than budgeted, because Flow bills per 10s segment and a slow read
needs more of them. Tighten the delivery prompt rather than leaning on this.

The alignment is written in the ElevenLabs /with-timestamps schema even though
it comes from Whisper, so subs.py consumes it without knowing the difference.
"""

import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
TARGET_WPM = 161.6      # measured from his 4.0M reel
MAX_STRETCH = 1.40      # see note below


def sh(cmd, capture=False):
    r = subprocess.run(cmd, check=True, text=True,
                       stdout=subprocess.PIPE if capture else None)
    return r.stdout if capture else None


def concat(clips, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    # Re-encode rather than -c copy: Flow segments are separate encodes and a
    # stream copy across them yields broken timestamps at each join.
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", lst, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", out])
    return out


def duration(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", path], capture=True).strip())


def transcribe(video):
    import mlx_whisper
    wav = os.path.splitext(video)[0] + ".wav"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
        "-ac", "1", "-ar", "16000", wav])
    r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-small.en-mlx",
                               word_timestamps=True)
    words = [w for s in r["segments"] for w in s.get("words", [])]
    return words


def to_elevenlabs(words, path):
    """Whisper is word-level; subs.py wants characters. Interpolate within each word."""
    chars, starts, ends = [], [], []
    for i, w in enumerate(words):
        t = w["word"]
        s, e = float(w["start"]), float(w["end"])
        span = max(e - s, 1e-3) / max(len(t), 1)
        for j, ch in enumerate(t):
            chars.append(ch)
            starts.append(s + j * span)
            ends.append(s + (j + 1) * span)
        if i + 1 < len(words):                       # the gap between words
            chars.append(" ")
            starts.append(e)
            ends.append(float(words[i + 1]["start"]))
    json.dump({"alignment": {"characters": chars,
                             "character_start_times_seconds": starts,
                             "character_end_times_seconds": ends}}, open(path, "w"))
    return path


def retime(src, out, factor):
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex",
        f"[0:v]setpts=PTS/{factor:.6f}[v];[0:a]atempo={factor:.6f}[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out])
    return out


def main():
    rid = sys.argv[1].upper()
    folder = sys.argv[2]
    clips = sorted(glob.glob(os.path.join(folder, "*.mp4")))
    if not clips:
        sys.exit(f"no .mp4 files in {folder}")
    print(f"  {len(clips)} segments")

    raw = os.path.join(ART, f"flow_{rid}_raw.mp4")
    concat(clips, raw)
    print(f"  concat -> {os.path.relpath(raw, ROOT)}  {duration(raw):.1f}s")

    words = transcribe(raw)
    dur = duration(raw)
    wpm = len(words) / dur * 60
    factor = wpm and TARGET_WPM / wpm
    print(f"  {len(words)} words / {dur:.1f}s = {wpm:.1f} wpm   (his {TARGET_WPM})")
    print(f"  retime factor {factor:.3f}  -> {dur / factor:.1f}s")

    final = os.path.join(ART, f"flow_{rid}.mp4")
    if abs(factor - 1.0) < 0.02:
        print("  within 2% of his pace -- no retime")
        os.replace(raw, final)
    elif factor > MAX_STRETCH or factor < 1 / MAX_STRETCH:
        print(f"  REFUSING to retime by {factor:.2f}x -- past {MAX_STRETCH:.2f}x the "
              f"sped-up blinks and gestures read as nervous. Fix the delivery prompt.")
        print(f"  (a {factor:.2f}x correction also means this reel cost ~{factor:.0%} "
              f"of budget in credits -- the slow read bought extra 10s segments)")
        os.replace(raw, final)
    else:
        retime(raw, final, factor)
        # Re-transcribe: the cards must be timed against the video that ships,
        # not the one that was measured.
        words = transcribe(final)

    aln = to_elevenlabs(words, os.path.join(ART, f"voice_{rid}.json"))
    print(f"  alignment -> {os.path.relpath(aln, ROOT)}")
    print(f"  -> {os.path.relpath(final, ROOT)}  {duration(final):.1f}s\n")
    print(f"  next:  python3 scripts/subs.py {rid} {os.path.relpath(final, ROOT)} "
          f"output/REEL_{rid}_FINAL.mp4")


if __name__ == "__main__":
    main()
