#!/usr/bin/env python3
"""Bind every reel's DM automation to its PUBLISHED post id. Run on cron.

    python3 scripts/bind_automations.py            # report only
    python3 scripts/bind_automations.py --apply    # bind what it found

WHY THIS EXISTS — the silent funnel failure found 2026-08-15.

A comment automation whose trigger has `postId: null` is documented as "match
comments on any post". It does not. Measured across account 63585:

    postId set   254 255 263* 265 266 267 268 269 270   9 automations
    postId null  1005 1329 1333 1337 1341 1346 256 257 264 271 272 273

Every scoped automation has fired (267 alone 28 times). Ten of the twelve
unscoped ones have NEVER fired. The decisive case was reel 24: two people
commented "forgive" on post 6159515, the automation was active with a matching
keyword, and `list_automation_logs(1005)` returned an EMPTY LIST — not a failed
run, no run at all. The flow never started. Meanwhile automation 267, scoped to
a postId, started and completed normally on the same account the same hour. The
system was healthy; the event simply never reached the unscoped automation.

* 263 is the second, independent confirmation. It IS scoped — but to `3250679`,
  which is a SUBMISSION id, not a published post id. It has never fired either.
  Publishing mints a new id in a different range:

      scheduled submission id   3482308
      published post id         6159515

  So "has a postId" is not sufficient. It must be the PUBLISHED id, which does
  not exist until the post goes live — which is exactly why this has to be a
  scheduled job and cannot be done at scheduling time.

THE JOIN KEY IS `mediaUrls`. It is the one field that survives publication
unchanged, so it maps a scheduled entry to its published twin. Captions do not
work (several reels share a hashtag set) and post times drift.

The automation -> media mapping lives in data/dm_registry.json under
"media" — written by the scheduler when the reel is queued.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dm_drop_yes_gate import api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "dm_registry.json")


def published_by_media():
    """media url -> published post id, for the last 30 days."""
    out = {}
    cur = None
    while True:
        q = ("/posts?platform=instagram&status=published"
             "&since=2026-07-20T00:00:00Z&limit=100")
        if cur:
            q += "&cursor=" + cur
        r = api(q)
        for p in (r.get("items") or []):
            for m in (p.get("mediaUrls") or []):
                out[m] = p["id"]
        cur = r.get("cursor")
        if not cur:
            return out


def scheduled_media():
    """Every media url currently sitting on a scheduled post (any account)."""
    out = set()
    for s in (api("/schedules?limit=50").get("items") or []):
        for u in ((s.get("draft") or {}).get("content") or {}).get("mediaUrls") or []:
            out.add(u)
    return out


def main():
    apply = "--apply" in sys.argv
    reg = json.load(open(REG)) if os.path.exists(REG) else {}
    media_map = reg.get("media", {})          # automationId -> media url
    pub = published_by_media()
    sched_media = scheduled_media()     # computed once, not per automation

    autos = {a["id"]: a for a in (api("/dm-automations").get("items") or [])}
    todo, blocked = [], []

    for aid, murl in media_map.items():
        a = autos.get(aid)
        if not a:
            continue
        t = a.get("trigger") or {}
        if t.get("type") != "comment-received":
            continue
        want = pub.get(murl)
        if not want:
            # DISTINGUISH "waiting" FROM "will never join". Blotato RE-HOSTS the
            # file when a post is scheduled, so the upload's publicUrl is NOT
            # the url that ends up on the post. Recording the upload url leaves
            # an automation that looks fine, reports "not published yet"
            # forever, and silently DMs nobody — the same dead funnel this
            # script was written to fix. Found 2026-08-15 on reels 35/36/37.
            # A mapping that matches neither a scheduled nor a published post
            # is broken NOW and must be shouted about, not queued.
            where = "not published yet" if murl in sched_media else (
                "!! ORPHAN media url — matches no scheduled or published post. "
                "Re-read it from the SCHEDULE, not from the upload response.")
            blocked.append((aid, a["name"], where))
            continue
        if t.get("postId") == want:
            continue
        todo.append((aid, a["name"], t.get("postId"), want, t))

    for aid, name, old, want, t in todo:
        print(f"{aid} {name}\n    postId {old!r} -> {want}")
        if apply:
            api(f"/dm-automations/{aid}", {"patch": {"trigger": {
                "type": t["type"], "isActive": True,
                "keywords": t.get("keywords") or [], "postId": want}}},
                method="PATCH")
            print("    bound")
    for aid, name, why in blocked:
        print(f"{aid} {name}: {why}")

    if todo and not apply:
        print(f"\n{len(todo)} to bind — re-run with --apply")
    if not todo and not blocked:
        print("all mapped automations are bound to their published post")


if __name__ == "__main__":
    main()
