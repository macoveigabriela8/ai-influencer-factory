#!/usr/bin/env python3
"""
Direct ElevenLabs narration for Master Kaion.

    python3 scripts/eleven.py voices        # list voices on YOUR account
    python3 scripts/eleven.py say B         # render reel B narration

We call `/with-timestamps`, which returns the mp3 AND character-level alignment.
That alignment is what lets subtitles split on punctuation while still landing on
the exact millisecond the word is spoken -- previously the timings were inferred
from an assumed words-per-minute, which is what made cards break mid-phrase.

Output per reel:
    output/assets/voice_<ID>.mp3     audio for the Kling avatar
    output/assets/voice_<ID>.json    {chars, char_starts, char_ends} alignment
"""

import base64
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
API = "https://api.elevenlabs.io/v1"

# Grandpa Spuds Oxley -- supplied by the user from their own ElevenLabs library.
VOICE = os.environ.get("EL_VOICE", "NOpBlnGInO9m6vDvFkFC")
MODEL = os.environ.get("EL_MODEL", "eleven_multilingual_v2")


def key():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k:
        sys.exit("ELEVENLABS_API_KEY not set in .env")
    return k


KEY = key()


def call(path, payload=None):
    hdr = {"xi-api-key": KEY, "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:600]
        sys.exit(f"ElevenLabs {e.code}: {body}")


def cmd_voices():
    for v in call("/voices").get("voices", []):
        lab = v.get("labels") or {}
        print(f"  {v['voice_id']}  {v['name']:24s} "
              f"{lab.get('age','')} {lab.get('gender','')} {lab.get('accent','')}")


def reel_text(rid):
    reels = json.load(open(os.path.join(ROOT, "scripts", "reels.json")))
    reel = next(r for r in reels if r["id"] == rid.upper())
    # One blank line between beats: ElevenLabs reads that as a real pause,
    # which reproduces the measured ~0.55s beat gap in his delivery for free.
    return reel, "\n\n".join(" ".join(b["lines"]) for b in reel["beats"])


def cmd_say(rid):
    os.makedirs(ART, exist_ok=True)
    reel, text = reel_text(rid)
    print(f"  reel {reel['id']} · {len(text.split())} words · {len(text)} chars")

    r = call(f"/text-to-speech/{VOICE}/with-timestamps", {
        "text": text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": 0.55,          # some variation; fully stable reads robotic
            "similarity_boost": 0.75,
            "style": 0.15,
            "use_speaker_boost": True,
            "speed": float(os.environ.get("EL_SPEED", "0.88")),  # ~150 wpm, unhurried
        },
    })

    mp3 = os.path.join(ART, f"voice_{reel['id']}.mp3")
    with open(mp3, "wb") as f:
        f.write(base64.b64decode(r["audio_base64"]))

    al = r.get("alignment") or r.get("normalized_alignment") or {}
    with open(os.path.join(ART, f"voice_{reel['id']}.json"), "w") as f:
        json.dump({"text": text, "alignment": al}, f)

    ends = al.get("character_end_times_seconds") or []
    dur = ends[-1] if ends else 0
    wpm = len(text.split()) / dur * 60 if dur else 0
    print(f"  {os.path.relpath(mp3, ROOT)}  {dur:.1f}s  ~{wpm:.0f} wpm")
    print(f"  alignment: {len(al.get('characters') or [])} chars timed")


if __name__ == "__main__":
    a = sys.argv[1:] or ["voices"]
    if a[0] == "voices":
        cmd_voices()
    elif a[0] == "say":
        cmd_say(a[1])
    else:
        sys.exit(__doc__)
