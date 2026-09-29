#!/usr/bin/env python3
"""Daily account health check for @master_kaion.

    python3 scripts/health_check.py           # scrape, evaluate, alert if bad

Pulls live numbers via Apify (never the user's session), appends a snapshot to
output/health_history.json, evaluates the three real shadowban signals, and on
any problem fires a macOS notification + spoken alert the user can hear.

The three signals (calibrated 2026-08-07, see CLAUDE.md):
  1. THREE consecutive posts near-zero (<50 plays after 24h) — the pattern the
     user's other account showed while flagged.
  2. A post stuck under 50 plays 48h after publishing.
  3. Account-wide day-over-day plays collapsing >80% while posting continued.
One quiet post is the normal lottery; the gate is patterns, not single points.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "output", "health_history.json")


def token():
    """Match the key EXACTLY. `startswith("APIFY_TOKEN")` also matched
    `APIFY_TOKEN_2=`, so which token you got depended on line order in .env --
    and line 13 held the token that died on 2026-08-16. Try the primary, fall
    back to the spare, and verify before returning either."""
    env = {}
    for l in open(os.path.join(ROOT, ".env")):
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1)
            env[k.strip()] = v.strip()
    for key in ("APIFY_TOKEN", "APIFY_TOKEN_2"):
        t = env.get(key)
        if not t:
            continue
        try:
            urllib.request.urlopen(
                "https://api.apify.com/v2/users/me?token=" + t, timeout=60)
            return t
        except Exception:
            continue
    sys.exit("no working APIFY_TOKEN (primary and APIFY_TOKEN_2 both failed)")


def scrape():
    body = json.dumps({"directUrls": ["https://www.instagram.com/master_kaion/"],
                       "resultsType": "posts", "resultsLimit": 20}).encode()
    u = ("https://api.apify.com/v2/acts/apify~instagram-scraper/"
         "run-sync-get-dataset-items?token=" + token())
    r = urllib.request.urlopen(urllib.request.Request(
        u, body, {"Content-Type": "application/json"}), timeout=600)
    posts = [p for p in json.load(r) if p.get("shortCode")]
    posts.sort(key=lambda p: p.get("timestamp") or "")
    return [{"sc": p["shortCode"], "ts": p.get("timestamp"),
             "plays": p.get("videoPlayCount") or p.get("videoViewCount") or 0,
             "likes": p.get("likesCount") or 0,
             "comments": p.get("commentsCount") or 0} for p in posts]


def alert(msg, spoken=None):
    """Visible + audible on the Mac.

    The NOTIFICATION carries the detail (ids, error text); the SPOKEN line is a
    short human sentence. Reading automation ids aloud every morning is noise
    the user cannot act on - it said "1455, 1454, 1453..." for two weeks
    (2026-09-12). Speak what is wrong, never the identifiers.
    """
    subprocess.run(["osascript", "-e",
                    'display notification "%s" with title "KAION HEALTH ALERT" '
                    'sound name "Sosumi"' % msg.replace('"', "'")[:240]])
    if spoken:
        subprocess.run(["say", "-v", "Samantha", "Kaion. " + spoken])


def speak_for(problems):
    """One short spoken sentence for the whole problem list, or None to stay quiet.

    Blindness is not worth waking the user for - it goes in the notification and
    the log. Only a broken money path gets a voice.
    """
    for p in problems:
        if "no link" in p:
            n = p.split()[0]
            return "%s d m automations are missing the shop link." % n
    return None


def main():
    problems = []

    # Funnel gate FIRST: it must not depend on the scrape surviving.
    # A dead Apify token silenced this whole check for 24 runs (2026-08-25).
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from fix_dm_links import unlinked
        dead = unlinked()
        if dead:
            problems.append("%d DM automation(s) promise a gift with no link: %s"
                            % (len(dead), ", ".join(i for i, _ in dead[:6])))
    except Exception as e:
        problems.append("DM link gate could not run: %s" % e)

    try:
        posts = scrape()
    except Exception as e:
        # Degrade, never die. A blind board must SAY it is blind.
        problems.append("Apify scrape failed (%s) - reach signals are BLIND." % e)
        print(json.dumps({"posts": [], "problems": problems}, indent=1))
        alert(" ".join(problems)[:200], speak_for(problems))
        return 1

    now = time.time()
    hist = json.load(open(HIST)) if os.path.exists(HIST) else []
    hist.append({"t": now, "posts": posts})
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    json.dump(hist[-90:], open(HIST, "w"), indent=1)

    def age_h(p):
        return (now - time.mktime(time.strptime(
            p["ts"][:19], "%Y-%m-%dT%H:%M:%S"))) / 3600 if p.get("ts") else 0

    mature = [p for p in posts if age_h(p) > 24]
    if len(mature) >= 3 and all(p["plays"] < 50 for p in mature[-3:]):
        problems.append("Last three mature posts are all under 50 plays. "
                        "This matches the flagged-account pattern. Pause posting.")
    for p in posts:
        if age_h(p) > 48 and p["plays"] < 50:
            problems.append("Post %s stuck at %d plays after 48 hours."
                            % (p["sc"], p["plays"]))
    if len(hist) >= 2:
        prev = {p["sc"]: p["plays"] for p in hist[-2]["posts"]}
        gained = sum(max(0, p["plays"] - prev.get(p["sc"], 0)) for p in posts
                     if p["sc"] in prev)
        prev_gain = None
        if len(hist) >= 3:
            pp = {p["sc"]: p["plays"] for p in hist[-3]["posts"]}
            prev_gain = sum(max(0, prev.get(sc, 0) - pp.get(sc, 0))
                            for sc in prev if sc in pp)
        if prev_gain and prev_gain > 200 and gained < prev_gain * 0.2:
            problems.append("Daily plays collapsed: %d yesterday vs %d today."
                            % (prev_gain, gained))

    print(json.dumps({"posts": posts, "problems": problems}, indent=1))
    if problems:
        alert(" ".join(problems)[:200], speak_for(problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
