#!/usr/bin/env python3
"""Deliver DMs that the cloud automations could not send (plan §4, 2026-08-08).

Root cause found 2026-08-08: comments on posts published under the OLD Blotato
account record (62904, wiped on re-add) still log under 62904, where no
automations exist. The live automations sit on 63585 with postId=null, but
Blotato routes comment events by account record, so those comments never fire
a run. Same IG account, so a one-time PRIVATE REPLY to the comment (allowed
within 7 days) can still deliver the promised DM through 63585.

    python3 scripts/dm_backfill.py            # scan + send missed DMs
    python3 scripts/dm_backfill.py --dry      # report only

Keyword -> message map comes from the LIVE automations (GET /dm-automations),
so the copy always matches what the cloud would have sent. State in
data/dm_backfill_state.json (sent + failed comment ids); the API also enforces
once-per-comment. comment_sweep.py may only 'Sent, my friend' a 62904 comment
once its id is in this state file's sent list.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "dm_backfill_state.json")
BASE = "https://backend.blotato.com/v2"
LIVE_ACCOUNT = "63585"        # the connected @master_kaion record
STALE_ACCOUNTS = ["62904"]    # old records whose posts still receive comments
MAX_AGE_DAYS = 7              # IG private-reply window


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


def keyword_map(post_id=None):
    """keyword -> (dmMessage, buttons) for automations that serve `post_id`.

    An automation scoped to a postId serves ONLY that post; an unscoped one is
    considered global. Before 2026-08-15 this function skipped every scoped
    automation, on the reasoning that "per-post catch-alls don't generalize".
    That was right for a keyword-less catch-all and wrong for everything else,
    and it became load-bearing the day we learned that `postId: null` never
    fires (see bind_automations.py) — every real automation now carries a
    postId, so the old rule would have hidden all of them from the backfill and
    silently emptied it.
    """
    out = {}
    r = api("/dm-automations")
    autos = r.get("items") or r.get("automations") or []
    for a in autos:
        trig = a.get("trigger") or {}
        if not a.get("isActive") or trig.get("type") != "comment-received":
            continue
        pid = trig.get("postId")
        if pid and str(pid) != str(post_id):
            continue                  # scoped to a different post
        for kw in trig.get("keywords") or []:
            out[kw.lower()] = (a["dmMessage"], a.get("buttons") or [])
    return out


def run_contacts():
    """automation keyword -> set of contactIds that already got a run (63585).
    A comment on the LIVE account is only 'missed' if no run covers its author
    (happens when the comment predates the automation's creation)."""
    contacts = {}
    r = api("/dm-automations")
    for a in (r.get("items") or []):
        trig = a.get("trigger") or {}
        if trig.get("type") != "comment-received":
            continue
        try:
            runs = api(f"/dm-automations/{a['id']}/runs").get("items") or []
        except Exception:
            runs = []
        ids = {str(x.get("contactId")) for x in runs}
        for kw in trig.get("keywords") or []:
            contacts.setdefault(kw.lower(), set()).update(ids)
    return contacts


def matches(text, kws):
    t = text.lower()
    words = t.split()
    return [k for k in kws if (k in words if " " not in k else k in t)]


def main():
    dry = "--dry" in sys.argv
    st = json.load(open(STATE)) if os.path.exists(STATE) else {
        "sent": [], "failed": {}}
    print(f"{len(keyword_map())} global keywords (scoped ones resolve per post)")
    covered = run_contacts()
    served_any = set().union(*covered.values()) if covered else set()
    if not served_any:
        sys.exit("run coverage came back EMPTY — that means either no automation "
                 "has ever fired or the /runs endpoint failed. Refusing to send, "
                 "because an empty guard would re-DM everyone.")
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    sent = 0
    for acct in STALE_ACCOUNTS + [LIVE_ACCOUNT]:
        cursor = None
        while True:
            params = {"platform": "instagram", "accountId": acct, "limit": 50}
            if cursor:
                params["cursor"] = cursor
            page = api("/comments", params=params)
            items = page.get("items") or []
            for c in items:
                cid = str(c["id"])
                if c.get("isAuthor") or c.get("parentCommentId"):
                    continue
                if cid in st["sent"] or cid in st["failed"]:
                    continue
                ts = time.mktime(time.strptime(
                    c["createdAt"][:19], "%Y-%m-%dT%H:%M:%S"))
                if ts < cutoff:
                    continue
                kws = keyword_map(c.get("postId"))
                hit = matches(c.get("text") or "", kws)
                if not hit:
                    continue
                # Skip anyone an automation has EVER served, under any keyword —
                # not just the keyword that matched here. Checking only `hit`
                # let a contact through who had already been DMed under a
                # different keyword (caught 2026-08-15 before sending). Meta
                # allows one private reply per COMMENT, so a resend would be
                # legal and still wrong: same person, second unsolicited DM.
                if acct == LIVE_ACCOUNT and str(c["authorId"]) in served_any:
                    continue
                msg, buttons = kws[hit[0]]
                print(f"missed DM: comment {cid} ({c['createdAt'][:16]}) "
                      f"'{(c.get('text') or '')[:40]}' -> keyword '{hit[0]}'")
                if dry:
                    continue
                payload = {"accountId": LIVE_ACCOUNT, "platform": "instagram",
                           "target": {"targetType": "instagram"},
                           "recipientId": c["authorId"], "commentId": cid,
                           "text": msg}
                if buttons:
                    payload["buttons"] = [
                        {"type": "web_url", "title": b["title"], "url": b["url"]}
                        for b in buttons if b.get("type") == "url"][:3]
                try:
                    api("/messages", payload=payload)
                    st["sent"].append(cid)
                    sent += 1
                    print(f"  sent via private reply")
                except Exception as e:
                    err = getattr(e, "read", lambda: b"")().decode()[:200] \
                        if hasattr(e, "read") else str(e)
                    st["failed"][cid] = err
                    print(f"  FAILED: {err}")
            cursor = page.get("cursor")
            if not cursor or not items:
                break
    if not dry:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(st, open(STATE, "w"), indent=1)
    print(f"backfill done: {sent} sent, {len(st['failed'])} failed")


if __name__ == "__main__":
    main()
