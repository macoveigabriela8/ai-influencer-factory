#!/usr/bin/env python3
"""Public 'sent' replies under keyword comments, in character, randomized.

    python3 scripts/comment_sweep.py          # one sweep pass

The DM itself is handled in Blotato's cloud (dm-automations 236-239, see
data/dm_registry.json) and fires with the laptop closed. This sweep adds the
PUBLIC half of the loop the big accounts run: a short reply under the comment,
which confirms the promise publicly and doubles the comment count. Instagram
allows replying to comments up to 7 days old, so this catches up after any
downtime -- it does not need to be running when the comment lands.

State in data/comment_sweep_state.json: replied comment ids (never reply
twice), last reply text per post (never repeat consecutively). Caps at
MAX_PER_RUN replies per pass so a viral post cannot make us spam-burst.
"""

import json
import os
import random
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "comment_sweep_state.json")
REG = os.path.join(ROOT, "data", "dm_registry.json")
BASE = "https://backend.blotato.com/v2"
MAX_PER_RUN = 20

REPLIES = [
    "Sent, my friend \U0001F64F",
    "It is in your messages \U0001F54A️",
    "Look in your inbox, my friend \U0001F64F",
    "Sent. Read it slowly \U0001F64F",
    "It is with you now \U0001F54A️",
    "Check your messages, my friend",
]


def key():
    for l in open(os.path.join(ROOT, ".env")):
        if l.startswith("BLOTATO_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("BLOTATO_API_KEY missing from .env")


def api(path, payload=None, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data,
        {"blotato-api-key": key(), "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def keywords():
    reg = json.load(open(REG))
    kws = set()
    for a in reg["automations"]:
        kws.update(k.lower() for k in a["keywords"])
    return kws


def main():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {
        "replied": [], "last_text": {}}
    kws = keywords()
    # 62904 = stale pre-re-add record: its comments get NO automation DM, so a
    # public "Sent" is a lie unless dm_backfill.py has delivered one (its state
    # holds the comment ids it sent). 63585 comments get the cloud DM directly.
    bf = os.path.join(ROOT, "data", "dm_backfill_state.json")
    backfilled = set(json.load(open(bf))["sent"]) if os.path.exists(bf) else set()
    done = 0
    # Comments we already replied to ANYWHERE (including manual in-session
    # replies) — live from the API, not just our state file. Found 2026-08-08:
    # 4 comments got a manual "take care" AND a sweep "Sent" (double-reply).
    already = set()
    for acct in ("63585", "62904"):
        cursor = None
        while True:
            params = {"platform": "instagram", "accountId": acct, "limit": 100}
            if cursor:
                params["cursor"] = cursor
            try:
                page = api("/comments", params=params)
            except Exception:
                break
            items = page.get("items") or []
            for c in items:
                if c.get("isAuthor") and c.get("parentCommentId"):
                    already.add(str(c["parentCommentId"]))
            cursor = page.get("cursor")
            if not cursor or not items:
                break
    for acct in ("63585", "62904"):
        if done >= MAX_PER_RUN:
            break
        cursor = None
        while done < MAX_PER_RUN:
            params = {"platform": "instagram", "accountId": acct, "limit": 50}
            if cursor:
                params["cursor"] = cursor
            try:
                page = api("/comments", params=params)
            except Exception as e:
                print("list failed:", e)
                return
            items = page.get("items") or []
            for c in items:
                cid = str(c.get("id"))
                text = (c.get("text") or "").lower()
                if cid in st["replied"] or cid in already \
                        or c.get("parentCommentId") or c.get("isAuthor"):
                    continue
                if not any((k in text.split() if " " not in k else k in text)
                           for k in kws):
                    continue
                if acct == "62904" and cid not in backfilled:
                    continue    # no DM was delivered — do not claim one
                post = str(c.get("postId"))
                pool = [r for r in REPLIES if r != st["last_text"].get(post)]
                reply = random.choice(pool)
                try:
                    api("/comments", payload={"postId": post,
                        "parentCommentId": cid, "text": reply})
                    st["replied"].append(cid)
                    st["last_text"][post] = reply
                    done += 1
                    print(f"replied {cid} on {post}: {reply}")
                except Exception as e:
                    print("reply failed", cid, e)
                if done >= MAX_PER_RUN:
                    break
            cursor = page.get("cursor")
            if not cursor or not items:
                break
    json.dump(st, open(STATE, "w"), indent=1)
    print(f"sweep done: {done} replies")


if __name__ == "__main__":
    main()
