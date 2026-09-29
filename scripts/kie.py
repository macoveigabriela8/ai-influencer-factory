#!/usr/bin/env python3
"""
Minimal kie.ai client + the Master Kaion production pipeline.

    python3 scripts/kie.py credits
    python3 scripts/kie.py image        # character reference (nano-banana)
    python3 scripts/kie.py voice B      # narration  (elevenlabs)
    python3 scripts/kie.py avatar B     # lip-synced talking head (kling)

Every call prints the credit delta so real per-reel cost is measured, not guessed.

Model IDs were found by probing the API, since kie.ai publishes no model-list
endpoint and the avatar model is absent from the docs' market index:
    google/nano-banana                    image
    elevenlabs/text-to-speech-turbo-2-5   voice
    kling/ai-avatar-pro                   audio-driven lip sync, <=5 min audio
"""

import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
BASE = "https://api.kie.ai/api/v1"


def load_env():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        sys.exit("KIE_API_KEY not set (put it in .env)")
    return key


KEY = load_env()
HDR = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}


def api(path, payload=None, method=None):
    url = BASE + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HDR,
                                 method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def credits():
    return float(api("/chat/credit").get("data") or 0)


def run_task(model, inp, label, poll=8, limit=180):
    """Create a task, poll to completion, return the result payload."""
    r = api("/jobs/createTask", {"model": model, "input": inp})
    if r.get("code") != 200:
        print(json.dumps(r, indent=1)[:600])
        sys.exit(f"createTask failed for {model}")
    tid = r["data"]["taskId"]
    print(f"  {label}: task {tid}")

    for i in range(limit):
        time.sleep(poll)
        s = api(f"/jobs/recordInfo?taskId={tid}")
        d = s.get("data") or {}
        state = d.get("state") or d.get("status") or "?"
        if state in ("success", "SUCCESS", "completed"):
            # The record reports its own cost — more reliable than a credit delta,
            # which races against any parallel job on the same account.
            print(f"  {label}: done in {d.get('costTime')}s · "
                  f"{float(d.get('creditsConsumed') or 0):.1f} credits")
            return d
        if state in ("fail", "failed", "FAIL", "error"):
            print(json.dumps(d, indent=1)[:700])
            sys.exit(f"{label} failed")
        if i % 5 == 0:
            print(f"    …{state} ({(i+1)*poll}s)")
    sys.exit(f"{label} timed out")


def urls_from(d):
    """kie.ai nests result URLs differently per model; dig them out."""
    out = []
    raw = d.get("resultJson") or d.get("result") or d
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return [raw] if raw.startswith("http") else []

    def walk(o):
        if isinstance(o, str) and o.startswith("http"):
            out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(raw)
    return out


def upload(path):
    """Upload a local file, return its public URL (cached in a sibling .url)."""
    cache = os.path.splitext(path)[0] + ".url"
    # A .url older than its file is STALE — re-rendered audio must re-upload.
    # (Rounds 6-7 of PT2 re-rolled a garbled round-4 upload through this cache:
    # 1,280 credits of clean local audio never reached the engine, 2026-08-08.)
    # ...AND the cached URL must still RESOLVE. These are signed CDN links and
    # they expire: on 2026-08-15 a32d_cloister's stored url 403'd, the cache
    # handed the dead link straight back because the local png had not changed,
    # and the render failed with an unhelpful "internal error". The mtime check
    # answers "is the file newer than the upload"; it cannot answer "is the
    # upload still there". Both have to be true. Every dead scrape URL in this
    # project comes from the same assumption — see data/competitors/README.md.
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(path):
        cached = open(cache).read().strip()
        try:
            urllib.request.urlopen(urllib.request.Request(
                cached, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
            return cached
        except Exception as e:
            print(f"  cached url is dead ({type(e).__name__}) — re-uploading "
                  f"{os.path.basename(path)}")
    import base64
    payload = {
        "base64Data": "data:application/octet-stream;base64," +
                      base64.b64encode(open(path, "rb").read()).decode(),
        "uploadPath": "influencer",
        "fileName": os.path.basename(path),
    }
    # This host sits behind Cloudflare and answers `error code: 1010` to
    # urllib's default User-Agent -- which reads exactly like a missing route.
    req = urllib.request.Request(
        "https://kieai.redpandaai.co/api/file-base64-upload",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.loads(r.read())
    url = ((body.get("data") or {}).get("downloadUrl")
           or (body.get("data") or {}).get("fileUrl"))
    if not url:
        sys.exit(f"upload failed: {json.dumps(body)[:400]}")
    open(cache, "w").write(url)
    return url


def fetch(url, path):
    # The tempfile.aiquickdraw.com CDN 403s urllib's default User-Agent.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


# --------------------------------------------------------------------------
# User-supplied realism keywords (2026-08-08) — append to EVERY anchor image
# prompt and weave into video prompts. Three groups: say "real", talk like a
# photographer (85mm = faces), name real lighting.
REALISM = (
    "85mm lens, DSLR photography, documentary style, real-world photography, "
    "lifelike details, natural imperfections, realistic skin, realistic "
    "materials, natural light, realistic shadows, shallow depth of field."
)

CHARACTER = (
    "Photorealistic portrait photograph of an elderly Japanese Zen monk, 74 years old, "
    "shaved head, deeply lined kind face, small dark eyes with heavy lids, thin grey "
    "eyebrows, calm neutral expression, mouth closed. Wearing a plain indigo-grey cotton "
    "monastic robe with a simple charcoal kesa over one shoulder. Seated upright behind a "
    "low plain cedar table, both hands resting flat on the table. Chest-up framing, centred, "
    "facing the camera, looking directly into the lens. Soft overcast daylight through paper "
    "shoji screens, cool grey-green tones, tatami room, rain visible outside the window. "
    "Shallow depth of field, natural skin texture, no text, no watermark."
)


def cmd_image():
    os.makedirs(ART, exist_ok=True)
    d = run_task("google/nano-banana",
                 {"prompt": CHARACTER, "output_format": "png", "image_size": "9:16"},
                 "character image")
    u = urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no image url")
    p = fetch(u[0], os.path.join(ART, "kaion_master.png"))
    meta = os.path.join(ART, "kaion_master.url")
    open(meta, "w").write(u[0])
    print(f"  saved {os.path.relpath(p, ROOT)}\n  url {u[0]}")


def script_text(rid):
    reels = json.load(open(os.path.join(ROOT, "scripts", "reels.json")))
    reel = next(r for r in reels if r["id"] == rid.upper())
    parts = []
    for b in reel["beats"]:
        parts.append(" ".join(b["lines"]))
    return reel, "\n\n".join(parts)


def cmd_voice(rid):
    os.makedirs(ART, exist_ok=True)
    reel, text = script_text(rid)
    print(f"  {len(text.split())} words")
    d = run_task("elevenlabs/text-to-speech-turbo-2-5",
                 {"text": text, "voice_id": os.environ.get("EL_VOICE", "JBFqnCBsd6RMkjVDRZzb"),
                  "stability": 0.55, "similarity_boost": 0.75,
                  "speed": float(os.environ.get("EL_SPEED", "0.82"))},
                 f"voice {reel['id']}")
    u = [x for x in urls_from(d) if any(x.endswith(e) for e in (".mp3", ".wav", ".m4a"))] or urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no audio url")
    p = fetch(u[0], os.path.join(ART, f"voice_{reel['id']}.mp3"))
    open(os.path.join(ART, f"voice_{reel['id']}.url"), "w").write(u[0])
    print(f"  saved {os.path.relpath(p, ROOT)}\n  url {u[0]}")


def cmd_avatar(rid, secs=None):
    """`secs` renders only the opening N seconds -- a cheap gate on hand quality
    before committing to a full 150s reel."""
    rid = rid.upper()
    # kaion_rest, not kaion_master: the master has the fingers INTERLACED, and
    # interlaced fingers are what smear. Every Kling run before this one was
    # seeded with that pose, so its "stiff hands" verdict was measured against a
    # source image that was itself the failure case.
    #
    # ANCHOR=a3_dusk_stupa_nohands overrides the anchor with a variant from
    # output/assets/anchors/ (six generated 2026-08-07, user-approved). One
    # variant per reel is what fixes the grid: five identical cover frames
    # measured 7.3 mean pixel-difference vs 59.1 on his grid. Four of the six
    # keep the hands out of frame entirely — kling's weakest feature removed
    # at the source.
    if os.environ.get("ANCHOR"):
        img = os.path.join(ROOT, "output", "assets", "anchors",
                           os.environ["ANCHOR"] + ".url")
    else:
        img = os.path.join(ART, "kaion_rest.url")
    if secs:
        import subprocess
        cut = os.path.join(ART, f"voice_{rid}_test{int(secs)}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", os.path.join(ART, f"voice_{rid}.mp3"),
                        "-t", str(secs), "-c:a", "libmp3lame", "-b:a", "192k", cut],
                       check=True)
        aud = upload(cut) and os.path.splitext(cut)[0] + ".url"
        rid = f"{rid}_test{int(secs)}"
    else:
        aud = os.path.join(ART, f"voice_{rid}.url")
    for f in (img, aud):
        if not os.path.exists(f):
            sys.exit(f"missing {f} — run the earlier step first")
    d = run_task("kling/ai-avatar-pro", {
        "image_url": open(img).read().strip(),
        "audio_url": open(aud).read().strip(),
        # Run 1 stacked four negations at hand motion ("no gesturing", "hands do
        # not move"). The hands lifted anyway and rendered as a ghosted smear --
        # the model half-committing to a motion it had been forbidden. Suppressing
        # a motion the model wants to make is what produces the blur; shaping it
        # does not.
        #
        # That prompt rested on a comment claiming his reels are "motionless the
        # entire time". Measured on BIG02, lower third of frame: mean 10.43,
        # peak/median 4.4x, near-still only 50% of the time. He moves constantly
        # at a moderate level with periodic emphasis. The premise was false.
        #
        # So: describe the CYCLE (rest -> small lift on an emphasised word ->
        # settle back), and anchor the hands in physical contact with the table.
        # Contact is a constraint the model can satisfy geometrically, unlike a
        # prohibition it has to resist.
        "prompt": OMNI_PROMPT,
    }, f"avatar {rid}", poll=15, limit=120)
    u = [x for x in urls_from(d) if ".mp4" in x] or urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no video url")
    p = fetch(u[0], os.path.join(ART, f"avatar_{rid}.mp4"))
    print(f"  saved {os.path.relpath(p, ROOT)}")


# --------------------------------------------------------------------------
# Seedance route.
#
# Seedance 2.0 is text/image-to-video with its own audio, NOT audio-driven, and
# `duration` is capped at 15s (min 4, max 15 -- read off the slider on kie.ai,
# not off the marketing copy, which says nothing about it). A 151s reel is
# therefore ~11 generations. That is the same shape as the Flow failure, with
# one decisive difference: Flow carried continuity in PROSE, so every segment
# re-imagined the table and the camera. Seedance carries it in PIXELS via
# first_frame_url / last_frame_url.
#
# The anchoring trick: give EVERY clip the same image as both its first and its
# last frame. Then the frame on either side of every stitch is literally
# identical, and clip 3 cannot have drifted from clip 1 -- whereas chaining
# each clip's real last frame forward lets error accumulate across generations.
# The cost is that he returns to the rest pose every 15s, which is a rhythm his
# own reels already have.
#
# Audio is NOT generated here (`generate_audio: false`). Three independent
# generations give three slightly different voices and sentences chopped at the
# boundaries; no reference sample fixes that. The only way to get seamless
# audio is for there to be exactly one audio file, so the ElevenLabs narration
# goes on afterwards via LIPSYNC below, which re-drives the mouth to match it.
SEEDANCE = "bytedance/seedance-2"
LIPSYNC = "volcengine/video-to-video-lip-sync"

REST_POSE = (
    "Both hands rest flat and open on the table, palms down, one on each side of "
    "the open sutra, with a clear gap between them. Arms relaxed, shoulders down."
)

SEEDANCE_PROMPT = (
    "An elderly monk sits behind a low wooden table, speaking to the camera. "
    # SPEAKS IN ENGLISH -- load-bearing, added 2026-07-25 after reel 2 clip 2
    # came back entirely in Japanese: a faithful TRANSLATION of our reference
    # audio, not a misfire. Reel 2 clip 1's "garbled" speech was the same
    # effect part-way -- English pulled toward Japanese phonetics, which is why
    # it sounded like almost-words rather than noise.
    #
    # Cause: CHARACTER (above) describes "an elderly JAPANESE Zen monk ...
    # tatami room ... shoji screens", and that prompt generated kaion_rest.png,
    # the anchor image every clip passes as reference_image_urls. The model
    # reads the character as Japanese and voices him accordingly. Nothing in
    # this prompt ever asserted otherwise.
    #
    # Stated positively on purpose: negated objects get generated in these
    # models ("no tripod" produces tripods), so "not Japanese" is the wrong
    # shape. Name the language that IS spoken.
    "He speaks in English, in a calm measured voice. "
    + REST_POSE +
    " He speaks steadily, with small natural head movement. Occasionally he lifts "
    "one hand off the table, points toward the camera, holds it, and lays that hand "
    "back down flat. One hand at a time. Hands sharply defined and in focus "
    "throughout. Static locked-off camera, one continuous shot, no cuts."
)


def cmd_restpose():
    """Kaion's face and room, re-posed into the hands-flat-and-apart composition.

    This image is load-bearing: it is BOTH endpoints of all three clips, so it is
    the pose the whole 45s returns to. Generated by editing the existing master
    rather than from scratch, so identity and lighting carry over.
    """
    src = open(os.path.join(ART, "kaion_master.url")).read().strip()
    d = run_task("google/nano-banana", {
        "prompt": ("Keep this exact man, room, robe, lighting and framing unchanged. "
                   "Change only his hands and arms: " + REST_POSE +
                   " An open sutra lies on the table between his hands."),
        "image_urls": [src], "output_format": "png", "image_size": "9:16",
    }, "rest pose")
    u = urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no image url")
    p = fetch(u[0], os.path.join(ART, "kaion_rest.png"))
    open(os.path.join(ART, "kaion_rest.url"), "w").write(u[0])
    print(f"  saved {os.path.relpath(p, ROOT)}")


def cmd_seedance(n=1, secs=15, audio=None):
    """Render clip `n` of the chain. Clip 1 doubles as the cost probe.

    `audio` is a URL to a <=15s ElevenLabs chunk, passed as reference_audio_urls.
    When present, Seedance drives the mouth FROM that waveform, which replaces
    the separate lip-sync pass entirely -- kie's volcengine lip-sync model sits
    in "waiting" forever and never picks jobs up, so a post-hoc sync is not
    available to us at all.

    ⚠️ This docstring previously claimed we could throw away Seedance's audio
    and mux the ORIGINAL ElevenLabs mp3 back in, "and it still lines up".
    THAT IS FALSE and was disproved in the reel B run (SOP Part 3, constraint
    2): Seedance does not reproduce our waveform, it RE-PERFORMS the line at
    its own pace -- correlation 0.148 at -660ms offset. Muxing the source mp3
    back over the video desyncs within a sentence.

    So we keep Seedance's own audio track, and voice identity comes instead
    from every chunk being a slice of ONE continuous ElevenLabs recording with
    a pinned voice_id. Caption timing must likewise come from Whisper run on
    the RENDERED audio, never from the script or the ElevenLabs alignment.

    NOTE the 15s reference-audio cap is per REQUEST, not per file, and it
    matches the 15s duration cap exactly. So one clip = one audio chunk, and
    the reel's segmentation is decided by the audio, not the video.
    """
    anchor = os.path.join(ART, "kaion_rest.url")
    if not os.path.exists(anchor):
        sys.exit("run `kie.py restpose` first — every clip is anchored to it")
    anchor = open(anchor).read().strip()
    inp = {
        "prompt": SEEDANCE_PROMPT,
        "duration": secs,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        # generate_audio must be TRUE when reference audio is supplied -- the
        # speech is the thing being generated, and false would give us back the
        # silent plate we already have.
        "generate_audio": bool(audio),
    }
    if audio:
        # HTTP 422: "The reference audio and the first and last frames are
        # mutually exclusive, and only one scene can be selected". So the two
        # continuity mechanisms cannot be combined, and we must give up the
        # anchoring trick to get lip-sync.
        #
        # reference_image_urls is the weaker substitute: it carries WHO and
        # WHERE (face, robe, courtyard, framing) but not the exact pixel the
        # clip starts and ends on, so consecutive clips can drift in pose. Two
        # things contain that. The shot is locked-off, so there is little for
        # the camera to drift in; and the prompt returns him to the same rest
        # pose, so the drift is bounded by the pose description rather than
        # accumulating. Cuts will be visible as cuts -- which his own reels
        # also have -- rather than as a different man in a different place.
        inp["reference_image_urls"] = [anchor]
        inp["reference_audio_urls"] = [audio]
    else:
        inp["first_frame_url"] = anchor
        inp["last_frame_url"] = anchor
    d = run_task(SEEDANCE, inp, f"seedance clip{n}", poll=10, limit=120)
    u = [x for x in urls_from(d) if ".mp4" in x] or urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no video url")
    # Namespace the output per reel. Clip numbers restart at 1 for every reel,
    # so without this, rendering reel 2 clip 1 silently overwrites reel B's
    # seedance_01.mp4 -- which is exactly what happened on 2026-07-25 (the
    # casualty was an unused spare; reel B's master uses sd_v01.mp4, so nothing
    # published was lost, but clips 2-7 were one command away from the same
    # fate). Reel B keeps the bare `seedance_` prefix so its existing files and
    # the assemble_reel.py invocations in CLAUDE.md still resolve.
    reel = os.environ.get("REEL", "B")
    stem = "seedance" if reel == "B" else f"sd{reel}"
    p = fetch(u[0], os.path.join(ART, f"{stem}_{n:02d}.mp4"))
    print(f"  saved {os.path.relpath(p, ROOT)}")


def cmd_lipsync(video, audio, out, mode="basic"):
    """Re-drive an existing clip's mouth from a separate audio track.

    This is the join between the two halves of the architecture. Seedance gives
    us a silent plate whose skin texture holds (measured 8.3 -> 8.3 across 15s,
    where OmniHuman fell 9.0 -> 4.1); ElevenLabs gives us one continuous voice
    across the whole reel. Neither alone is a reel. Laying the audio on top
    WITHOUT this step is a dub -- the mouth is already moving to nothing, so it
    argues with the voice frame for frame, which is the single most reliable
    tell that a video is synthetic.

    Field names are documented (docs.kie.ai/market/volcengine/video-to-video-lip-sync)
    rather than probed, which matters here: the earlier attempt at this model
    returned no output, and a silently-ignored wrong field name is the likeliest
    explanation. `mode` is REQUIRED and has no default -- omit it and the task
    is malformed.

    `basic` over `lite` because basic is the tier that does scene segmentation
    and speaker identification. We have one speaker in one locked-off shot, so
    we need neither -- but basic is also the higher-fidelity mouth model, and
    this test exists to answer "is the lip-sync good enough to build on", which
    should be asked of the better tier. If basic works we can price-shop down to
    lite afterwards; if lite failed we would have learned nothing.
    """
    v = video if video.startswith("http") else upload(os.path.join(ART, video))
    a = audio if audio.startswith("http") else upload(os.path.join(ART, audio))
    before = credits()
    d = run_task(LIPSYNC, {
        "mode": mode,
        "video_url": v,
        "audio_url": a,
        # The plate has no voice on it at all, so there is nothing to separate
        # and nothing to detect a scene cut across. Both default false; stated
        # explicitly so a future reader knows they were considered, not missed.
        "separate_vocal": False,
        "open_scenedet": False,
    }, f"lipsync {mode}", poll=10, limit=120)
    u = [x for x in urls_from(d) if ".mp4" in x] or urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:1200]); sys.exit("no video url")
    p = fetch(u[0], os.path.join(ART, out))
    after = credits()
    print(f"  saved {os.path.relpath(p, ROOT)}")
    print(f"  billed {before - after:.1f} credits  ({after:.1f} left)")


# --------------------------------------------------------------------------
# OmniHuman 1.5 on kie, which is the same model fal serves -- but billed against
# the kie balance, which matters because the fal account is locked on an
# exhausted balance. Measured 247.5 credits for 15s = 16.5 cr/s, against
# Seedance's 41 cr/s for the same second of footage.
#
# Field names are `image` and `audio` (NOT image_url/audio_url, which every
# other model here uses). Discovered by probing; kie publishes no doc page for
# this model. Probing cost 247.5 credits because a well-formed probe creates a
# REAL task -- use a dummy audio URL when probing anything billable.
OMNIHUMAN = "bytedance/omni-human"

# See fal_avatar.PROMPT for the full derivation. Short version: the smear tracks
# whether the hands TOUCH EACH OTHER, not how much they move, so the hands are
# kept on separate sides of the table and the source image is the flat-and-apart
# rest pose rather than the interlaced master.
OMNI_PROMPT = (
    "Static locked-off camera, medium shot, one continuous take. Warm, unhurried, "
    "grandfatherly. An elderly Tibetan monk sits behind a low wooden table and "
    "speaks directly to the camera throughout. His two hands stay well apart from "
    "each other at all times, one on the left side of the table and one on the "
    "right, with a clear gap of open space between them. Each hand rests flat and "
    "open, palm down, fingers relaxed and slightly spread. First he speaks with "
    "both hands resting flat. Then, on an emphasised word, he raises one hand a "
    "little off the table with the palm open and turned upward, holds it there "
    "briefly, and lays it back down flat on its own side of the table. Only one "
    "hand moves at a time and it always stays on its own side. Each hand is "
    "sharply defined, fully in focus, and separate from the other. Minimal "
    "gestures, subtle micro-expressions, calm restrained delivery."
)


def cmd_omni(rid, secs=None):
    """OmniHuman render. `secs` gates on a short slice before a full reel."""
    import subprocess
    rid = rid.upper()
    img = upload(os.path.join(ART, "kaion_rest.png"))
    src = os.path.join(ART, f"voice_{rid}.mp3")
    if secs:
        cut = os.path.join(ART, f"voice_{rid}_test{int(secs)}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                        "-t", str(secs), "-c:a", "libmp3lame", "-b:a", "192k", cut],
                       check=True)
        src, rid = cut, f"{rid}_omni{int(secs)}"
    d = run_task(OMNIHUMAN, {"image": img, "audio": upload(src),
                             "prompt": OMNI_PROMPT}, f"omnihuman {rid}",
                 poll=15, limit=120)
    u = [x for x in urls_from(d) if ".mp4" in x] or urls_from(d)
    if not u:
        print(json.dumps(d, indent=1)[:800]); sys.exit("no video url")
    p = fetch(u[0], os.path.join(ART, f"avatar_{rid}.mp4"))
    print(f"  saved {os.path.relpath(p, ROOT)}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["credits"]
    if a[0] == "credits":
        print(f"{credits():.1f} credits")
    elif a[0] == "image":
        cmd_image()
    elif a[0] == "voice":
        cmd_voice(a[1])
    elif a[0] == "avatar":
        cmd_avatar(a[1], float(a[2]) if len(a) > 2 else None)
    elif a[0] == "omni":
        cmd_omni(a[1], float(a[2]) if len(a) > 2 else None)
    elif a[0] == "restpose":
        cmd_restpose()
    elif a[0] == "lipsync":
        cmd_lipsync(a[1], a[2], a[3], a[4] if len(a) > 4 else "basic")
    elif a[0] == "seedance":
        cmd_seedance(int(a[1]) if len(a) > 1 else 1,
                     int(a[2]) if len(a) > 2 else 15,
                     a[3] if len(a) > 3 else None)
    else:
        sys.exit(__doc__)
