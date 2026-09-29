#!/usr/bin/env python3
"""Music-bed detector -- the second half of the QC gate (SOP Part 3 Step 5b).

    python3 scripts/drone_check.py output/assets/sd2_*.mp4

Seedance beds a synth drone under SOME generations -- confirmed on seedance_08,
1 clip in 8. It is per-generation, not global, so every clip must be checked.

WHY A NAIVE TEST FAILS, AND WHY THREE OF MY OWN ATTEMPTS DID.

  1. NOISE FLOOR. Does not work. seedance_08's quiet frames sit at 6.7% of its
     loudest frame -- QUIETER in relative terms than six clean clips (up to 30%).
     A soft drone and soft room tone are indistinguishable on amplitude.

  2. PEAK PROMINENCE WITH A FIXED THRESHOLD. Does not work, and this is the
     trap. Calibrated by injecting a synthetic A2+A3+D4 chord into a known-clean
     clip: an audible bed at -40 dBFS lifts the target bins to only 2.0-3.5x the
     local broadband floor. At -50 dBFS it is already invisible. So any "peak
     must exceed 4x" rule rejects real drones, and a low threshold drips false
     positives -- clean seedance_03 reads 3.50x at A2 all by itself.

  3. LOW FFT RESOLUTION. N=2048 at 16kHz is 7.8Hz per bin, which cannot tell
     A2 (109.8Hz) from generic 100-120Hz male vocal rumble. Every clip looks
     tonal down there because every clip has a voice in it.

WHAT ACTUALLY DISCRIMINATES: COHERENCE ACROSS THE NOTE SET.

A chord puts energy on ALL its partials at once. Vocal rumble and room noise
put energy on whatever they happen to land on. So the statistic is the MINIMUM
ratio across the three notes, not the maximum or the mean -- one lone hot bin
proves nothing, three simultaneously-hot bins is a chord.

Measured separation on the 10 clips rendered so far:

    seedance_08 (bedded)   min 1.95        <-- the SOP's positive control
    every other clip       min 0.57-1.21
    synthetic -40dB chord  min 2.05        <-- calibration

Threshold 1.7 sits in the empty band between 1.21 and 1.95. That is a gap of
measurement, not of theory: with n=10 it is a usable gate, not a proven
constant. Re-check the margin as clips accumulate.

DETECTION IS NOT A FIX. Do not prompt "no music" -- negated objects get
generated in these models ("no tripod" produces tripods). Re-roll the clip, and
if it recurs, describe what IS there: "only his voice, quiet courtyard ambience".
"""

import os
import subprocess
import sys

import numpy as np

SR = 44100
# 32768 samples = 1.35Hz per bin. Enough to resolve 109.8Hz as distinct from
# the 100-120Hz vocal-fundamental smear that sits on top of it in every clip.
N = 32768
NOTES = {"A2": 109.8, "A3": 220.0, "D4": 293.8}
THRESHOLD = 1.7


def ratios(path):
    """Tonal-peak-to-broadband-floor ratio at each note, over quiet frames only."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    frames = [a[i:i + N] for i in range(0, len(a) - N, N // 2)]
    if len(frames) < 4:
        return None
    # Analyse only the quietest 25% of frames. Speech is broadband and 30dB
    # louder than the bed; averaging it in buries the drone entirely.
    rms = np.array([np.sqrt((f ** 2).mean()) for f in frames])
    quiet = np.argsort(rms)[:max(1, len(frames) // 4)]
    spec = np.mean([np.abs(np.fft.rfft(frames[i] * np.hanning(N))) for i in quiet], axis=0)
    freq = np.fft.rfftfreq(N, 1 / SR)
    width = int(40 / (freq[1] - freq[0]))  # +/-40Hz local neighbourhood
    out = {}
    for name, target in NOTES.items():
        b = np.argmin(np.abs(freq - target))
        peak = spec[b - 2:b + 3].max()          # +/-2 bins, for generation pitch drift
        floor = np.median(np.concatenate([spec[b - width:b - 6], spec[b + 7:b + width]]))
        out[name] = peak / floor
    return out


def main(paths):
    print(f"{'clip':24s}" + "".join(f"{n:>7s}" for n in NOTES) + f"{'MIN':>8s}   verdict")
    bad = []
    for p in paths:
        r = ratios(p)
        if r is None:
            print(f"{os.path.basename(p):24s}  too short to analyse")
            continue
        m = min(r.values())
        if m > THRESHOLD:
            bad.append(p)
        print(f"{os.path.basename(p):24s}" + "".join(f"{r[n]:7.2f}" for n in NOTES)
              + f"{m:8.2f}   {'BEDDED - re-roll' if m > THRESHOLD else 'clean'}")
    if bad:
        print(f"\n{len(bad)} clip(s) bedded: " + ", ".join(os.path.basename(p) for p in bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
