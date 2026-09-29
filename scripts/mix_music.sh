#!/usr/bin/env bash
# Mix a soft piano bed under narration, matching Monk Chen's measured levels.
#
#   ./mix_music.sh voice.wav piano.mp3 out.wav
#
# Measured target (from his #1 reel, 4,047,769 plays):
#   music in speech gaps == ~20% of speech RMS  (approx -14 dB under the voice)
#
# The gain is computed RELATIVE TO THE PROCESSED VOICE, not to absolute dBFS.
# That matters: loudness-normalising the voice changes its level, so a fixed
# -14 dBFS bed would land at the wrong ratio for every different input file.
#
# Sidechain ducking then pulls the piano down further *while* he speaks and
# lets it return in the gaps -- which is what makes the pauses feel deliberate
# rather than empty.

set -euo pipefail
VOICE="${1:?usage: mix_music.sh voice.(wav|mp3) piano.(wav|mp3) out.wav}"
MUSIC="${2:?missing music file}"
OUT="${3:-mixed.wav}"
# Music RMS as a fraction of voice RMS, BEFORE ducking. Ducking costs roughly
# half, so 0.40 in lands at ~18-20% in the gaps -- his measured target.
# The script reports the achieved ratio; nudge this if you land outside 12-30%.
RATIO="${MUSIC_RATIO:-0.40}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Process the voice exactly as it will appear in the final mix, then measure it.
ffmpeg -y -loglevel error -i "$VOICE" \
  -af "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,dynaudnorm=f=200:g=5" \
  "$TMP/voice_proc.wav"

# 2. Compute the gain that puts the music at RATIO x voice RMS.
GAIN=$(python3 - "$TMP/voice_proc.wav" "$MUSIC" "$RATIO" <<'PY'
import sys, subprocess, wave, numpy as np
def rms(path):
    out = f"/tmp/_rms_{abs(hash(path))}.wav"
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',path,'-ar','22050','-ac','1',out],check=True)
    w = wave.open(out)
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)/32768
    return float(np.sqrt(np.mean(x**2))) or 1e-6
v, m, ratio = rms(sys.argv[1]), rms(sys.argv[2]), float(sys.argv[3])
print(f"{(v*ratio)/m:.6f}")
PY
)
echo "voice-relative music gain: ${GAIN}x"

# 3. Mix. Sidechain key is the RAW voice -- feeding it the normalised voice
#    would keep the compressor triggered through the quiet passages.
ffmpeg -y -loglevel error \
  -i "$TMP/voice_proc.wav" -stream_loop -1 -i "$MUSIC" \
  -filter_complex "\
    [0:a]asplit=2[voice][sc]; \
    [1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo, \
         volume=${GAIN}, highpass=f=90, lowpass=f=6000 [music]; \
    [music][sc]sidechaincompress=threshold=0.10:ratio=2.5:attack=40:release=250 [ducked]; \
    [voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0, \
    afade=t=in:st=0:d=1.5, alimiter=limit=0.95 [out]" \
  -map "[out]" -ar 44100 -ac 2 "$OUT"

echo "wrote $OUT"

# 4. Verify against the measured target.
python3 - "$OUT" <<'PY'
import sys, subprocess, wave, numpy as np
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',sys.argv[1],
                '-ar','22050','-ac','1','/tmp/_chk.wav'],check=True)
w = wave.open('/tmp/_chk.wav'); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)/32768
win = int(0.25*sr)
r = np.array([np.sqrt(np.mean(x[i:i+win]**2)) for i in range(0, len(x)-win, win)])
r = r[r > 1e-5]
if len(r):
    loud, quiet = np.percentile(r, 80), np.percentile(r, 10)
    pct = quiet/loud*100
    flag = "OK" if 12 <= pct <= 30 else "OUT OF RANGE - adjust MUSIC_RATIO"
    print(f"speech {loud:.4f} | gaps {quiet:.4f} | ratio {pct:.1f}%  (target ~20%)  {flag}")
PY
