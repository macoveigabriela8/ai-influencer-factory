#!/usr/bin/env python3
"""Find audience comments that SHOULD have triggered a DM but did not.

    python3 scripts/keyword_gap.py            # last 7 days
    python3 scripts/keyword_gap.py --days 30

Cross-references every audience comment against every DM-automation run log. A
comment with no run behind it is a miss; a miss that looks like one of our
keywords is almost certainly a typo we can register.

WHY. Measured 2026-08-12 from the run logs: Blotato matches
contains(comment, keyword), case-insensitive — so punctuation, emoji, capitals
and surrounding words are all harmless. `Amen!🙏` fires, `My Daughter` fires.
The ONLY real failure mode is a misspelling: `Aman` and `My daugther` both
missed, ~5% of that week's comments. Every miss is a person who asked for the
freebie, got nothing, and will not ask twice.

Each suggestion is COLLISION-CHECKED before it is offered. A stem that fires on
an unrelated word is worse than a miss: `chos` matches "chosen", `amin` matches
"vitamin". A false DM goes to someone who never asked, which is the behaviour
that gets an account reported.

NOTHING IS CHANGED AUTOMATICALLY. This prints candidates for a human to approve,
because widening a keyword changes who gets messaged.
"""

import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT = "63585"          # @master_kaion instagram
# Words common enough that a stem colliding with them would fire on ordinary
# comments. Not exhaustive — it is a tripwire, and the human still reads it.
# 2026-08-21: the list below missed `hope`, `rest` and `like`, and the run
# that morning offered all three as "safe to add". Each would have fired on
# ordinary conversation ("I hope not", "the rest of it", "I like this") and
# sent a freebie DM to someone who never asked — the exact behaviour this
# tripwire exists to stop. Everyday English is added here; a word that is
# already a live keyword must NOT be, or real candidates read as collisions.
COMMON = """chosen choose chose vitamin examining reaming amnesia streaming
    beautiful blessing blessed thank thanks thankyou please prayer praying
    peace amazing morning mother father family friend heart soul life love
    truth wisdom master monk video reel words true
    hope hoping like likes liked rest resting there their this that these
    those here first need needs good great right time times today tonight
    think thinking know knowing thing things real really best better very
    sorry help helping nice lovely everything something someone""".split()


def env(k):
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip()
    sys.exit(f"{k} missing from .env")


def api(path, tries=5):
    """Retry transient transport failures.

    2026-09-09: this check had been dying on EVERY run and printing a
    traceback instead of a result. A single run walks ~36 automations x up to
    600 log pages, and somewhere in that sequence Blotato drops the socket
    (measured: ConnectionResetError, read timeout and SSL EOF on three
    consecutive runs). The endpoint itself is healthy -- 10/10 direct probes
    succeeded in ~1.6s -- so the failure was purely the missing retry. A gate
    that cannot finish reports nothing, which reads as 'no gaps found'."""
    req = urllib.request.Request("https://backend.blotato.com/v2" + path, None,
                                 {"blotato-api-key": env("BLOTATO_API_KEY")})
    for n in range(tries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except urllib.error.HTTPError:
            raise                      # a real 4xx/5xx is not transient
        except Exception:
            if n == tries - 1:
                raise
            time.sleep(2 ** n)


def paged(path, cap=1000):
    """Follow the cursor. NOTE: this API returns `items`, never `logs` —
    reading the wrong key once produced a confident, wrong 'nothing fired'."""
    out, cur = [], None
    while len(out) < cap:
        d = api(path + (f"&cursor={cur}" if cur else ""))
        out += d.get("items", [])
        cur = d.get("cursor")
        if not cur:
            break
    return out


def norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t.lower())).strip()


def main():
    days = 7
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                          time.gmtime(time.time() - days * 86400))

    autos = [a for a in paged("/dm-automations?limit=250")
             if a.get("accountId") == ACCOUNT and a.get("isActive")]
    keywords = {}
    for a in autos:
        for k in (a.get("trigger") or {}).get("keywords") or []:
            keywords[k.lower()] = a["id"]

    fired = set()
    for a in autos:
        for line in paged(f"/dm-automations/{a['id']}/logs?limit=250", cap=600):
            c = (line.get("context") or {}).get("comment")
            if c:
                fired.add(c["id"])

    comments = [c for c in paged(f"/comments?accountId={ACCOUNT}&limit=250")
                if not c["isAuthor"] and c["createdAt"] >= since]

    misses = [c for c in comments if c["id"] not in fired]
    print(f"{len(comments)} audience comments in {days}d · "
          f"{len(comments)-len(misses)} triggered a DM · {len(misses)} did not")
    if not keywords:
        sys.exit("no active keywords found — check the account id")

    # A miss is INTERESTING when it nearly matches a keyword: a likely typo.
    print("\nLIKELY TYPOS (a miss that closely resembles a live keyword):")
    hits = 0
    for c in misses:
        text = norm(c["text"])
        if not text:
            continue
        for word in text.split():
            for kw in keywords:
                if kw in text or len(kw.split()) > 1:
                    continue
                r = difflib.SequenceMatcher(a=word, b=kw).ratio()
                if r >= 0.75 and word != kw:
                    collide = [w for w in COMMON if word in w]
                    verdict = (f"COLLIDES with {collide[:3]} — do not add"
                               if collide else "safe to add")
                    print(f"  {c['text'][:44]!r:48s} '{word}' ~ '{kw}' "
                          f"({r:.2f}, automation {keywords[kw]}) — {verdict}")
                    hits += 1
                    break
    if not hits:
        print("  none — every miss was an ordinary comment, not a typo")

    print("\nOTHER MISSES (read these: a new phrase people use is a new "
          "keyword worth registering):")
    for c in misses[:40]:
        print("  ", c["text"].replace("\n", " ")[:70])


if __name__ == "__main__":
    main()
