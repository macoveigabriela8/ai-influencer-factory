#!/usr/bin/env python3
"""Verification-based TikTok queue for KAION. Never assumes, never duplicates.

    python3 scripts/tiktok_rotate.py            # verify + advance if posted
    python3 scripts/tiktok_rotate.py confirm    # manual "I posted it" advance

Model:
  * The folder root always holds exactly ONE video: the next UNPOSTED one.
    It stays there for days if the user forgets — it never silently rotates.
  * Advance happens ONLY when the current video is confirmed posted:
      - automatically: Apify scrape of the public TikTok profile (read-only,
        no login, no Blotato connection — cannot endanger the account),
        matching by video duration within 1.5s;
      - or manually: `confirm` argument.
  * data/tiktok_state.json records every advance with date + match evidence.
  * If it is past 17:00 local and today's video is still unposted, fire a
    reminder notification.

⚠️ Photos files an imported video under the FILE's creation date, not the
import date, so a freshly pushed reel does not appear at the top of Recents
(a master built on Aug 4 lands on Aug 4). Always look in the album itself.
The user reported a video 'missing' for this reason on 2026-08-13.

TIKTOK_HANDLE comes from .env (TIKTOK_HANDLE=master.kaion). Until it is set,
only manual confirm advances the queue.
"""

import json
import os
import shutil
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = "/Users/m/Library/Mobile Documents/com~apple~CloudDocs/KAION_TIKTOK"
Q, P = os.path.join(D, "_queue"), os.path.join(D, "_posted")
STATE = os.path.join(ROOT, "data", "tiktok_state.json")


def env(key):
    try:
        for l in open(os.path.join(ROOT, ".env")):
            if l.startswith(key + "="):
                return l.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def import_to_photos(path):
    """Put the day's video in the Photos library so the TikTok app can see it.

    The Files app is invisible to TikTok's gallery picker; Photos is the only
    surface it reads. Album 'KAION TIKTOK' holds the current video. Apple gives
    no API to delete from Photos, so posted videos are removed by the user with
    a swipe; only one ~50MB video is current at a time.
    """
    script = f'''
    set v to POSIX file "{path}"
    tell application "Photos"
        set al to missing value
        try
            set al to album "KAION TIKTOK"
        on error
            set al to make new album named "KAION TIKTOK"
        end try
        import {{v}} into al skip check duplicates yes
    end tell'''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True,
                       timeout=120)
        print("  imported to Photos album KAION TIKTOK")
    except Exception as e:
        print("  Photos import failed:", e)


def notify(msg, sound="Sosumi"):
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "KAION TIKTOK" '
                    f'sound name "{sound}"'])


def current():
    vids = [f for f in os.listdir(D) if f.endswith(".mp4")]
    return os.path.join(D, vids[0]) if vids else None


def scrape_durations(handle):
    """Durations+captions of the account's recent public posts via Apify."""
    tok = env("APIFY_TOKEN")
    if not tok:
        return None
    body = json.dumps({"profiles": [handle], "resultsPerPage": 15}).encode()
    u = ("https://api.apify.com/v2/acts/clockworks~tiktok-scraper/"
         "run-sync-get-dataset-items?token=" + tok)
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            u, body, {"Content-Type": "application/json"}), timeout=600)
        d = json.load(r)
        return [((v.get("videoMeta") or {}).get("duration") or 0,
                 (v.get("text") or "")[:80], v.get("webVideoUrl"))
                for v in d]
    except Exception as e:
        print("scrape failed:", e)
        return None


def advance(reason):
    cur = current()
    cap = os.path.join(D, "CAPTION.txt")
    stamp = time.strftime("%Y-%m-%d")
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"posted": []}
    if cur:
        st["posted"].append({"date": stamp, "file": os.path.basename(cur),
                             "evidence": reason})
        shutil.move(cur, os.path.join(P, f"{stamp}_{os.path.basename(cur)}"))
        if os.path.exists(cap):
            shutil.move(cap, os.path.join(P, f"{stamp}_caption.txt"))
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w"), indent=1)

    vids = sorted(f for f in os.listdir(Q) if f.endswith(".mp4"))
    if not vids:
        open(os.path.join(D, "NEEDS_REFILL.txt"), "w").write(
            "Queue empty — ask Claude to refill.\n")
        notify("Queue EMPTY — ask Claude to refill")
        return
    nxt = vids[0]
    txt = os.path.join(Q, nxt.replace(".mp4", ".txt"))
    name = "monk-wisdom"
    if os.path.exists(txt):
        words = re.findall(r"[A-Za-z']+",
                           open(txt).read().split("#")[0].lower())
        keep = [w for w in words if len(w) > 3 and w not in
                ("your", "this", "that", "with", "does", "even", "these",
                 "without", "things", "watch", "what", "happens", "from")]
        name = "-".join(keep[:6]) or name
    shutil.move(os.path.join(Q, nxt), os.path.join(D, name + ".mp4"))
    import_to_photos(os.path.join(D, name + ".mp4"))
    if os.path.exists(txt):
        shutil.move(txt, os.path.join(D, "CAPTION.txt"))
    left = len([f for f in os.listdir(Q) if f.endswith(".mp4")])
    print(f"advanced ({reason}) -> {name}.mp4 · {left} left in queue")
    if left <= 1:
        notify(f"Queue nearly empty ({left} left)", "Purr")


def main():
    cur = current()
    if not cur:
        advance("bootstrap")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "confirm":
        advance("manual confirm")
        return 0

    handle = env("TIKTOK_HANDLE")
    if handle:
        posted = scrape_durations(handle)
        want = dur(cur)
        if posted is not None and want:
            hit = [p for p in posted if p[0] and abs(p[0] - want) <= 1.5]
            if hit:
                advance(f"verified on @{handle}: {hit[0][2]}")
                return 0
            print(f"current video ({want:.0f}s) not found on @{handle} — "
                  "leaving in place")
    else:
        print("TIKTOK_HANDLE not set — only manual confirm advances")

    # afternoon reminder if still unposted
    if time.localtime().tm_hour >= 17:
        notify("Today's TikTok is still waiting in KAION_TIKTOK", "Purr")
    return 0


if __name__ == "__main__":
    sys.exit(main())
