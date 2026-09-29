#!/usr/bin/env python3
"""Render Reel B as N Seedance clips, each driven by its own narration chunk.

    python3 scripts/render_reel.py 2 3 4        # render clips 2, 3 and 4

WHY THIS SHAPE. Seedance 2.0 caps at 15s per generation and its reference-audio
field caps at 15s too, so a 151s reel is necessarily ~11 generations. The
segmentation is decided by the AUDIO, not the video: each clip is exactly one
chunk of the ElevenLabs narration, cut on sentence boundaries so no clip opens
or closes mid-word.

WHY REFERENCE AUDIO RATHER THAN A LIP-SYNC PASS. kie's
volcengine/video-to-video-lip-sync never picks jobs up -- a well-formed task sat
in state "waiting" for 20 minutes and consumed 0 credits, which is also why an
earlier attempt returned nothing. There is no post-hoc sync available to us. So
the mouth has to be generated together with the audio, which is strictly better
anyway: lip-sync is exact by construction rather than repaired afterwards.

WHAT THE REFERENCE AUDIO ACTUALLY DOES. Measured, not assumed. Clip 1's output
transcribes to our script very nearly verbatim, so the chunk drives the WORDS.
But its waveform correlates with our chunk at only 0.148 -- Seedance re-PERFORMS
the line at its own pace rather than reproducing our recording. Two consequences:

  * We cannot mux the original ElevenLabs mp3 back over the video. The timing
    differs, so it would desync. We keep Seedance's own audio track.
  * Voice identity therefore has to come from the reference sample being the
    same voice in every chunk -- which it is, since all chunks are slices of one
    continuous ElevenLabs recording.

The 15s cap is on the reference audio too, so chunks are cut at 14.8s to leave
headroom against container-vs-stream duration rounding.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie

ART = kie.ART

# Per-reel file sets. Reel B and reel 2 have overlapping clip numbers, so the
# chunk mp3s MUST NOT share a prefix -- otherwise rendering reel 2 clip 1
# silently overwrites reel B's vB_c01.mp3 and the two reels quietly diverge
# from the audio they were verified against.
REELS = {
    "B": {"plan": "chunks.json",       "voice": "voice_B.mp3", "prefix": "vB_c"},
    "2": {"plan": "chunks_reel2.json", "voice": "voice_2.mp3", "prefix": "v2_c"},
}
REEL = REELS[os.environ.get("REEL", "B")]
PLAN = os.path.join(ART, REEL["plan"])


def chunk_audio(p):
    """Cut chunk `n` out of the full narration and upload it."""
    out = os.path.join(ART, f"{REEL['prefix']}{p['n']:02d}.mp3")
    # LOUDNESS-NORMALISE EVERY CHUNK. Measured across 8 generations: every chunk
    # below ~0.048 RMS came back as generic spiritual filler instead of our
    # script (clips 6, 8, 9 at 0.045/0.047/0.040), and every chunk above 0.050
    # came back verbatim (clips 2,3,4,5,7 at 0.050-0.071). The failing chunks
    # transcribe perfectly on our side, so the audio is not corrupt -- it is
    # merely quiet, and Seedance appears to fall back on its "elderly monk"
    # character prior when the reference signal is weak.
    #
    # This matters because the quiet passages are the TENDER ones -- the
    # absolution and the comment CTA -- i.e. exactly the beats the reel cannot
    # afford to lose. Normalising is free and lossless to meaning: it changes
    # level, not delivery, and the prosody the model reads for gesture and
    # emphasis is preserved.
    # DO NOT PAD THE OPENING CHUNK WITH LEAD-IN SILENCE. Tried on 2026-07-25
    # (adelay=400 when s == 0) on the theory that chunk 1 fails because it
    # opens on a hard attack while every reel B chunk was cut from mid-file.
    # It did not help -- the real cause was the Japanese character prompt (see
    # CLAUDE.md) -- and once that was fixed, chunk 1 WITH the padding still
    # failed, returning generic filler ("The mind is like a wild river...")
    # while unpadded chunk 2 scored 1.000. Leading silence appears to read as
    # a weak reference signal, the same condition that triggers the filler
    # fallback. Every chunk gets identical treatment: loudnorm and nothing else.
    voice = os.path.join(ART, REEL["voice"])
    # A chunk is normally one contiguous slice, but it may instead declare
    # `parts`: several slices of the SAME recording spliced together. That is how
    # a sentence gets dropped from the middle of a chunk without re-rendering the
    # narration -- needed because Seedance silently deletes social-action CTAs
    # ("Send this to...") from speech, so those sentences have to leave the
    # spoken script and be drawn on screen instead. Splicing keeps the voice
    # identity identical, since every part is cut from the one ElevenLabs take.
    if p.get("parts"):
        # A hard butt-splice between two sentences reads as a jump cut in the
        # audio. GAP restores the breath that the removed sentence used to
        # occupy, so the delivery still sounds like one continuous take.
        GAP = 0.3
        segs, filt = [], []
        for i, (s, e) in enumerate(p["parts"]):
            segs += ["-ss", str(s), "-to", str(e), "-i", voice]
            filt.append(f"[{i}:a]")
            if i < len(p["parts"]) - 1:
                filt.append(f"[sil{i}]")
        n_in = len(p["parts"])
        sil = "".join(f"aevalsrc=0:d={GAP}:s=44100[sil{i}];"
                      for i in range(n_in - 1))
        chain = (f"{sil}{''.join(filt)}concat=n={n_in * 2 - 1}:v=0:a=1[c];"
                 f"[c]loudnorm=I=-16:TP=-1.5:LRA=11[a]")
        subprocess.run(["ffmpeg", "-v", "error", *segs, "-filter_complex", chain,
                        "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "2",
                        "-y", out], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(p["s"]), "-to", str(p["e"]),
                        "-i", voice,
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-c:a", "libmp3lame", "-q:a", "2", "-y", out], check=True)
    return kie.upload(out)


def main(ns):
    plan = {p["n"]: p for p in json.load(open(PLAN))}
    before = kie.credits()
    for n in ns:
        p = plan[n]
        # Seedance's `duration` is an integer 4-15. Round UP so the clip is never
        # shorter than its own narration -- a video that ends before the sentence
        # does would clip the last word off the reel.
        secs = min(15, int(p["dur"]) + 1)
        print(f"clip{n}: {p['dur']:.2f}s audio -> {secs}s video | {p['text'][:60]}…")
        url = chunk_audio(p)
        kie.cmd_seedance(n, secs, url)
    after = kie.credits()
    print(f"\nwave billed {before - after:.1f} cr = ${(before - after) * 0.005:.2f}"
          f"   ({after:.1f} cr = ${after * 0.005:.2f} left)")


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [2])
