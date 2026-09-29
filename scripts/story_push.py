#!/usr/bin/env python3
"""Put today's story teasers into Photos so the user can post them in one tap.

    python3 scripts/story_push.py            # push today's EN + PT story
    python3 scripts/story_push.py --dry      # show what would be pushed

Why this exists: an Instagram story is the ONLY surface on Instagram that can
carry a clickable link (the link sticker, available at any follower count).
Reels and feed posts cannot. Measured 2026-08-10: 28,741 Instagram reel views
produced ZERO referrals to the Gumroad page, while YouTube and Facebook — where
the link sits inside the post — both produced clicks. The sticker has to be
added by hand at post time and cannot be added afterwards, so Blotato can never
do it. The automated story queue was cancelled on 2026-08-10 for this reason.

⚠️ Photos files an imported video under the FILE's creation date, not the
import date, so a freshly pushed reel does not appear at the top of Recents
(a master built on Aug 4 lands on Aug 4). Always look in the album itself.
The user reported a video 'missing' for this reason on 2026-08-13.

The Files app is invisible to Instagram's gallery picker; Photos is the only
surface it reads (same finding as tiktok_rotate.py). Apple exposes no delete
API, so the user removes posted stories with a swipe.

Rotation: least-recently-pushed first, never the same reel twice in a row, and
a full cycle before any repeat. State in data/story_push_state.json.
"""

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "story_push_state.json")

LANES = [
    {"name": "EN", "album": "KAION STORY EN",
     "dir": os.path.join(ROOT, "output", "reels", "stories")},
    # PT Instagram is in a manual warm-up and posts NOTHING before 2026-08-21
    # (user, 2026-08-10). Pushing PT teasers into Photos before then would pile
    # up eleven days of videos that cannot be posted. The lane stays dark until
    # the date passes, then rotates like EN.
    {"name": "PT", "album": "KAION STORY PT",
     "dir": os.path.join(ROOT, "output", "markets", "PT", "stories"),
     "not_before": "2026-08-21"},
]


def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"lanes": {}}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w"), indent=1)


def import_to_photos(path, album):
    script = f'''
    set v to POSIX file "{path}"
    tell application "Photos"
        set al to missing value
        try
            set al to album "{album}"
        on error
            set al to make new album named "{album}"
        end try
        import {{v}} into al skip check duplicates yes
    end tell'''
    r = subprocess.run(["osascript", "-e", script],
                       capture_output=True, text=True, timeout=180)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])


def notify(msg):
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "KAION STORY" '
                    f'sound name "Glass"'])


def pick(lane, st):
    """Least-recently-pushed file, never the one pushed last."""
    files = sorted(f for f in os.listdir(lane["dir"]) if f.endswith(".mp4"))
    if not files:
        return None
    hist = st["lanes"].setdefault(lane["name"], {"pushed": [], "last": None})
    order = {f: i for i, f in enumerate(hist["pushed"])}
    # never-pushed first (order -1), then oldest push
    cand = sorted(files, key=lambda f: order.get(f, -1))
    for f in cand:
        if f != hist["last"] or len(files) == 1:
            return f
    return cand[0]


def main():
    dry = "--dry" in sys.argv
    force = "--force" in sys.argv
    st = load()
    pushed = []
    today = time.strftime("%Y-%m-%d")
    for lane in LANES:
        # ONE story per lane per day. The 06:00 cron owns the daily push; a
        # manual run on top of it puts two videos in the album for one day and
        # the user has to guess which to post (happened 2026-08-14). --force
        # overrides, e.g. when the Mac was asleep at 06:00 and you want a
        # second, deliberate push.
        h0 = st["lanes"].get(lane["name"], {})
        if not force and not dry and h0.get("last_day") == today:
            print(f"{lane['name']}: already pushed today ({h0.get('last')}) "
                  f"— use --force to push another")
            continue
        nb = lane.get("not_before")
        if nb and today < nb:
            print(f"{lane['name']}: account in warm-up until {nb}, skipped")
            continue
        if not os.path.isdir(lane["dir"]):
            print(f"{lane['name']}: no story dir, skipped")
            continue
        f = pick(lane, st)
        if not f:
            print(f"{lane['name']}: no story files, skipped")
            continue
        path = os.path.join(lane["dir"], f)
        print(f"{lane['name']}: {f} -> Photos album '{lane['album']}'")
        if dry:
            continue
        try:
            import_to_photos(path, lane["album"])
        except Exception as e:
            print(f"  FAILED: {e}")
            continue
        h = st["lanes"][lane["name"]]
        if f in h["pushed"]:
            h["pushed"].remove(f)
        h["pushed"].append(f)
        h["last"] = f
        h["last_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        h["last_day"] = today
        pushed.append(f"{lane['name']}: {f}")
    if not dry:
        save(st)
        if pushed:
            notify("Today's stories are in Photos — post with a LINK STICKER")
    print("\n".join(pushed) if pushed else "nothing pushed")


if __name__ == "__main__":
    main()
