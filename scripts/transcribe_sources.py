#!/usr/bin/env python3
"""Transcribe competitor source videos that are already on disk.

    python3 scripts/transcribe_sources.py            # every untranscribed local video
    python3 scripts/transcribe_sources.py DVEI18AgH7h

WHY ONLY THE LOCAL ONES (established 2026-08-15). We hold 271 monkcheen posts
and 200 yangmunus posts as JSON, but selection needs the SCRIPT, and monkcheen's
captions are hashtags only. 209 posts have never been transcribed, which is the
binding constraint on picking topics.

Both routes to fresh media are closed today:

  * every stored `videoUrl` is a signed CDN link and now returns 403 — checked
    across monkcheen_full, monkcheen_raw and yangmunus_posts, all dead;
  * Apify is at $29.035 of a $29.00 monthly cap, cycle resets 2026-08-28.

yt-dlp is NOT a workaround: Instagram returns an empty media response to an
anonymous fetch and asks for cookies. Passing the operator's cookies is exactly
what the project forbids ("never touch Instagram from the user's session"), and
that rule protects the account, so the 209 wait for Apify.

What IS free is data/competitors/videos/ — 19 files pulled during earlier
sweeps. This script mines them and nothing else.

Output matches the existing data/transcripts/ shape ({key, play, text,
segments}) so the vein sweep reads old and new files identically.
"""

import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VID = os.path.join(ROOT, "data", "competitors", "videos")
OUT = os.path.join(ROOT, "data", "transcripts")
MODEL = "mlx-community/whisper-small.en-mlx"   # same model as qc_gate.py

# An IG shortcode is 11 chars and always mixes letters in. The lookahead keeps
# the tail of a numeric TikTok id (…41300655368) from matching.
SHORTCODE = re.compile(r"(?![0-9]{11}\.)([A-Za-z0-9_\-]{11})\.mp4$")


def plays_index():
    """shortcode -> play count, from whichever corpus holds the post."""
    idx = {}
    for f in ["data/monkcheen_full.json",
              "data/competitors/yangmunus_posts.json"]:
        try:
            d = json.load(open(os.path.join(ROOT, f)))
        except Exception:
            continue
        for p in (d if isinstance(d, list) else d.get("items", [])):
            sc = p.get("shortCode")
            if sc:
                idx[sc] = p.get("videoPlayCount") or 0
    return idx


def already():
    """Shortcodes already transcribed. Split on the FIRST underscore only —
    a shortcode may itself contain one (DbbyfX_Phmq), and splitting on the
    last one silently truncates it to 'Phmq', which reads as untranscribed."""
    out = set()
    for f in glob.glob(os.path.join(OUT, "*.json")):
        stem = os.path.basename(f)[:-5]
        out.add(stem.split("_", 1)[1] if "_" in stem else stem)
    return out


def main():
    want = set(sys.argv[1:])
    import mlx_whisper

    plays, done = plays_index(), already()
    todo = []
    for v in sorted(os.listdir(VID)):
        m = SHORTCODE.search(v)
        if not m:
            continue                      # TikTok dumps use a numeric id, skip
        sc = m.group(1)
        if sc in done or (want and sc not in want):
            continue
        todo.append((sc, os.path.join(VID, v)))

    print(f"{len(todo)} to transcribe "
          f"({len(done)} already on disk, {len(os.listdir(VID))} videos held)\n")

    for i, (sc, path) in enumerate(todo, 1):
        wav = f"/tmp/tr_{sc}.wav"
        # Some sweep dumps are video-only. Report and move on rather than
        # aborting the batch on one bad file.
        r0 = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1",
                             "-ar", "16000", "-y", wav], capture_output=True)
        if r0.returncode or not os.path.exists(wav):
            print(f"[{i}/{len(todo)}] {sc}  SKIPPED — no audio stream\n")
            continue
        r = mlx_whisper.transcribe(wav, path_or_hf_repo=MODEL)
        os.remove(wav)
        text = (r.get("text") or "").strip()
        rec = {
            "key": f"SW_{sc}",            # SW = sweep, distinct from BIG/TOP/T60
            "play": plays.get(sc, 0),
            "text": text,
            "segments": [{"start": s["start"], "end": s["end"],
                          "text": s["text"]} for s in r.get("segments", [])],
        }
        json.dump(rec, open(os.path.join(OUT, f"SW_{sc}.json"), "w"),
                  ensure_ascii=False, indent=1)
        head = " ".join(text.split()[:18])
        print(f"[{i}/{len(todo)}] {sc}  {plays.get(sc,0):>9,} plays")
        print(f"    {head}\n")


if __name__ == "__main__":
    main()
