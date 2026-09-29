#!/usr/bin/env python3
"""
OmniHuman 1.5 avatar rendering via fal.ai.

    python3 scripts/fal_avatar.py B            # full reel, auto-segmented
    python3 scripts/fal_avatar.py B --limit 34 # short test

Why this engine rather than kling/ai-avatar (see scripts/kie.py):

  Kling exposes ONE global prompt and no timeline, so gesture timing cannot be
  controlled. Measured against his reel, run 1 gave 0.56 mean hand motion
  (his 4.79) and run 2 gave 3.82 but with peak/median 4.0x against his 7.4x --
  continuous moderate motion instead of rest-punctuate-rest. OmniHuman drives
  gestures from audio prosody instead of from a prompt, which is the mechanism
  that produces the rest/emphasis rhythm.

OmniHuman caps at 60s of audio at 720p, so a 151s reel needs 3 segments. Two
details keep the joins invisible:

  * Splits land on sentence boundaries taken from the ElevenLabs alignment, so
    no word is ever cut in half.
  * Segment N+1 is seeded with the LAST FRAME of segment N rather than the
    original master image. Re-using the master would snap the monk back to his
    clasped starting pose at every join -- a visible reset every 50 seconds.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
SEG = os.path.join(ART, "segments")
MODEL = "fal-ai/bytedance/omnihuman/v1.5"
# fal enforces DIFFERENT duration caps per resolution -- 60s at 720p, 30s at
# 1080p, HTTP 422 past either. So resolution silently decides how many segments
# a 151s reel becomes, and therefore how many joins can drift:
#
#   720p   60s cap -> 3 segments, 2 joins
#   1080p  30s cap -> 6 segments, 5 joins
#
# Price is $0.16/s either way, so this is a stitch-risk decision, not a cost one.
# We take 1080p because it is Instagram's native reel spec and IG re-encodes
# hard -- starting above its target loses less than starting at it. Note his own
# catalogue does NOT support resolution mattering for reach: his 4.0M-view BIG01
# is 720x1280 and his 1.38M BIG02 is 1080x1920, i.e. his biggest is the smaller
# file. This is a quality-of-presentation choice, not a virality lever.
RESOLUTION = "720p"
CAPS = {"720p": 50.0, "1080p": 28.0}     # under each cap, with headroom
MAX_SEG = CAPS[RESOLUTION]
RATE = 0.16             # USD per second of audio, billed on duration


def key():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    k = os.environ.get("FAL_KEY", "").strip()
    if not k:
        sys.exit("FAL_KEY not set in .env  (get one at https://fal.ai/dashboard/keys)")
    return k


KEY = key()
HDR = {"Authorization": "Key " + KEY, "Content-Type": "application/json"}


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"fal {e.code}: {e.read().decode()[:500]}")


def get(url):
    # Read the body on failure: fal puts the validation detail there, and a bare
    # HTTPError ("422 Unprocessable Entity") says nothing about which field is wrong.
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"fal GET {e.code} on {url}\n{e.read().decode()[:1500]}")


def upload(path):
    """Prefer a hosted URL, fall back to a data URI.

    fal's docs say base64 data URIs are accepted, and they are -- for images. A
    ~500KB mp3 came back as `file_download_error` on audio_url, so audio must be
    hosted. kie.py's uploader already writes a sibling `.url` next to anything it
    has hosted, so reuse that rather than standing up a second storage path. The
    data URI still serves the chained last-frame JPEGs, which have no .url and
    are small enough to inline.
    """
    cache = os.path.splitext(path)[0] + ".url"
    if os.path.exists(cache):
        return open(cache).read().strip()
    import base64
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def sentence_splits(rid, seg_max=MAX_SEG):
    """Split points at sentence ends, each segment as long as fits under the cap."""
    d = json.load(open(os.path.join(ART, f"voice_{rid}.json")))
    a = d["alignment"]
    chars, ends = a["characters"], a["character_end_times_seconds"]
    stops = [ends[i] for i, c in enumerate(chars) if c in ".!?"]
    total = ends[-1]

    cuts, start = [], 0.0
    while total - start > seg_max:
        # The latest sentence end that still fits inside the cap.
        fit = [s for s in stops if start < s <= start + seg_max]
        if not fit:
            sys.exit(f"no sentence boundary within {seg_max}s after {start:.1f}s")
        cuts.append(fit[-1])
        start = fit[-1]
    bounds = [0.0] + cuts + [total]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def slice_audio(rid, i, s, e):
    os.makedirs(SEG, exist_ok=True)
    out = os.path.join(SEG, f"{rid}_{i:02d}.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                    os.path.join(ART, f"voice_{rid}.mp3"),
                    "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
                    "-c:a", "libmp3lame", "-b:a", "192k", out], check=True)
    host(out)          # fal will not accept audio as a data URI -- see upload()
    return out


def host(path):
    """Publish a local file and cache its URL, reusing kie.py's storage."""
    cache = os.path.splitext(path)[0] + ".url"
    if os.path.exists(cache):
        return open(cache).read().strip()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kie
    return kie.upload(path)


def last_frame(video, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.2",
                    "-i", video, "-update", "1", "-q:v", "2", out], check=True)
    return out


# Gesture choreography, fourth revision -- and the first one aimed at the real
# cause rather than at "how much" the hands move.
#
#   v1  "hands do not move, no gesturing" -> four negations. Smeared anyway.
#   v2  clasped -> fingertips separate -> re-clasp. Motion up, definition marginal.
#   v3  palms flat -> one hand lifts and points -> flat. Motion up again, still
#       smearing at rest.
#
# Frame-by-frame on the v3 output finally isolated it. The smear is not a
# function of HOW MUCH the hands move -- it tracks WHETHER THE HANDS ARE
# TOUCHING EACH OTHER:
#
#   0:02  fingers interlaced          -> ghosted
#   0:10  fingers interlaced          -> ghosted
#   0:05  two open palms, apart       -> sharp, clean, correct
#
# Interlaced fingers require the model to resolve finger-over-finger occlusion
# and decide a depth order at every joint. Two separate hands with air between
# them are two simple isolated shapes. So the constraint is not "move less" or
# "move more" -- it is NEVER LET THE HANDS TOUCH.
#
# The bigger error was upstream: kaion_master.png has his fingers interlaced, so
# the home pose we handed the model WAS the failure case, and it returned there
# every time it stopped gesturing. main() now seeds from kaion_rest.png (hands
# flat and apart, sutra between them) instead. That image change is likely worth
# more than every prompt revision above put together, and it costs nothing.
#
# Phrasing follows fal's documented OmniHuman order -- camera, mood, speaking
# state, then ordinal actions -- and names body parts explicitly, which their
# prompt guide and ByteDance's own demo prompts both do. Gestures are kept
# single-handed: the published counting test on this model is reliable for
# one-hand gestures and starts failing as soon as two hands must coordinate.
# v5 -- and the first version written from fal's own documentation rather than
# from our guesses. It is SHORTER THAN v1, and it does not contain the word
# "hand" at all. That is the point.
#
# What the research actually said:
#
#   * fal's official prompt guide (fal.ai/learn/devs/omnihuman-1-5-prompt-guide)
#     documents the formula [camera] + [emotion/mood] + [speaking state] +
#     [specific actions], and contains NO hand guidance whatsoever. Its only
#     mention of hands is a POSITIVE example, "gesturing".
#   * There is no negative_prompt field. Confirmed against the OpenAPI schema --
#     `prompt` and `mask_url` are the only text/spatial controls. So a
#     prohibition can only be phrased as a negation inside the prompt, and
#     ByteDance's own guide advises "minimal negation".
#   * The one substantive practitioner source recommends constraining motion
#     AMPLITUDE generally rather than describing hand positions, and warns that
#     pushing emotion hard makes the model compensate with bigger motion.
#
# v4 did the opposite of all of this: 245 words, ~120 of them minute hand
# choreography ("palm open and turned upward", "on its own side of the table").
# Every one of those words is attention spent on hands, and several were
# negations wearing a positive costume ("stay well apart", "separate from the
# other") -- which is the failure mode already recorded in memory, where
# naming a thing you do not want is what summons it.
#
# So the hands are now controlled ENTIRELY by the source image, which is the
# one lever with evidence behind it, and the prompt's only job is to keep the
# overall motion amplitude low so the model never reaches for a big gesture.
# "Calm", "still", "unhurried" are doing the work that a paragraph of finger
# blocking failed to do.
PROMPT = (
    "Static locked-off camera, medium shot. A calm, unhurried, grandfatherly "
    "elderly monk speaks softly and directly to the camera throughout, seated and "
    "still. Subtle micro-expressions, minimal gestures, restrained delivery."
)

# The home pose the model returns to whenever it is not gesturing. This is the
# single highest-leverage input in the whole pipeline: it is every pixel of the
# hands for most of the runtime, and the model cannot invent a cleaner hand than
# the one it is shown. kaion_master.png has the fingers INTERLACED, which is the
# exact configuration that renders as a smear -- and worse, the model had to
# transition out of it, which is where malformed fingers appeared.
#
# kaion_hands.png is a user-supplied photograph, not one of our generations:
# both hands flat on the table, wide apart, palms down, an open sutra between
# them, nothing touching anything. It is the pose we spent four prompt
# revisions failing to describe. Since v5 above removed hand direction from the
# prompt entirely, this image is now the ONLY thing controlling the hands.
#
# Its one weakness is detail. Variance of the Laplacian at 512px wide:
#   kaion_rest 188, kaion_master 153, kaion_hands 134. Softest of the three,
# and our renders already run ~3x below his reference footage. Hence
# fal_upscale.py, which sharpens this file before it is used -- pose from the
# photograph, detail from the upscaler.
# kaion_hands.png put through fal_upscale.py (recraft crisp, the non-generative
# one) and conformed back to 720x1280 with lanczos. Detail at 512px wide:
# 134 raw -> 225 upscaled -> 223 after the downscale. The round trip is
# supersampling, not a wash: the upscaler reconstructs edges at 2304px and the
# downsample averages that reconstruction into the output pixels, so the gain
# survives. Hands verified by eye at each step -- five fingers, correct
# knuckles, nothing invented, which is the check the detail number cannot make.
SOURCE_IMAGE = "kaion_src.png"


def render(image_uri, audio_path, label):
    r = post(f"https://queue.fal.run/{MODEL}", {
        "image_url": image_uri,
        "audio_url": upload(audio_path),
        "prompt": PROMPT,
        "resolution": RESOLUTION,
    })
    status_url = r.get("status_url")
    resp_url = r.get("response_url")
    print(f"  {label}: queued")
    for i in range(200):
        time.sleep(10)
        st = get(status_url).get("status")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR"):
            sys.exit(f"{label} failed: {json.dumps(get(resp_url))[:400]}")
        if i % 6 == 0:
            print(f"    …{st} ({(i+1)*10}s)")
    else:
        sys.exit(f"{label} timed out")
    out = get(resp_url)
    url = (out.get("video") or {}).get("url")
    if not url:
        sys.exit(f"no video url: {json.dumps(out)[:400]}")
    return url


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def main():
    rid = sys.argv[1].upper()
    limit = None
    if "--limit" in sys.argv:
        limit = float(sys.argv[sys.argv.index("--limit") + 1])

    segs = sentence_splits(rid)
    if limit:
        segs = [(0.0, limit)]
    total = sum(e - s for s, e in segs)
    print(f"  {len(segs)} segment(s), {total:.1f}s  ≈ ${total * RATE:.2f}")
    for i, (s, e) in enumerate(segs):
        print(f"    {i}: {s:6.1f}-{e:6.1f}  ({e-s:.1f}s)")

    os.makedirs(SEG, exist_ok=True)
    image_uri = upload(os.path.join(ART, SOURCE_IMAGE))
    parts = []
    for i, (s, e) in enumerate(segs):
        aud = slice_audio(rid, i, s, e)
        url = render(image_uri, aud, f"seg{i}")
        mp4 = fetch(url, os.path.join(SEG, f"{rid}_{i:02d}.mp4"))
        parts.append(mp4)
        print(f"    -> {os.path.relpath(mp4, ROOT)}")
        if i + 1 < len(segs):
            # Seed the next segment from where this one ended, so the pose
            # carries over instead of resetting to the master image.
            image_uri = upload(last_frame(mp4, os.path.join(SEG, f"{rid}_{i:02d}_end.jpg")))

    out = os.path.join(ART, f"avatar_{rid}_omni.mp4")
    if len(parts) == 1:
        os.replace(parts[0], out)
    else:
        lst = os.path.join(SEG, f"{rid}_concat.txt")
        with open(lst, "w") as f:
            for p in parts:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print(f"  -> {os.path.relpath(out, ROOT)}   billed ≈ ${total * RATE:.2f}")


if __name__ == "__main__":
    main()
