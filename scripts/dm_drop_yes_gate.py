#!/usr/bin/env python3
"""Remove the "reply YES" gate from every live DM automation.

    python3 scripts/dm_drop_yes_gate.py --dry     # show every before/after
    python3 scripts/dm_drop_yes_gate.py           # apply to Blotato + registry

WHY (measured 2026-08-15). 62 DM conversations on @master_kaion, 6 with any
reply at all, 0 sales. Every practice DM ended:

    "The full thirty days are in my book below.
     Reply YES and I will leave you a small gift."

and the button pointed at the FULL-PRICE page. So the only reason to reply was
a gift the reader could not see, and the discount was invisible until after
they had replied. Five steps between a one-word commenter and a $14.95 sale.

The fix is to stop asking. The gift is stated in message one and the button
carries it pre-applied, so the DM is a complete offer on its own.

Verified empirically before writing this (never quote an unverified price):

    GET /l/quiet/STILLNESS -> discount_code {valid:true, percent 20, no expiry}
    GET /l/quiet           -> discount_code null
    price_cents 1495 -> $11.96 with the code

The YES-handler automations (258, 758) stay live and untouched. People will
still type "yes" out of habit and that path must keep working; it simply stops
being the only way to reach the discount.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "dm_registry.json")
BASE = "https://backend.blotato.com/v2"

GIFT_URL = "https://masterkaion.gumroad.com/l/quiet/STILLNESS"
BUTTON_TITLE = "Your gift · 20% off"      # Blotato caps button titles at 20 chars

# The new tail. Kaion's voice: no contractions, warm "my friend", plain words.
# It states the gift as ALREADY GIVEN, which is the whole point — nothing is
# withheld pending a reply.
TAIL = ("The full thirty days are in my book. I have already left your gift on "
        "it, twenty percent, with nothing to ask me for. \U0001f64f")

# Some bodies already name the book in the sentence before the tail ("...is
# inside The Quiet Between Thoughts", "It is below"). Appending the full tail
# there announces the book twice in two sentences, which reads as a rendering
# fault rather than a voice. Those get the short tail instead.
TAIL_SHORT = ("I have already left your gift on it, twenty percent, with "
              "nothing to ask me for. \U0001f64f")
NAMES_BOOK = re.compile(r"(The Quiet Between Thoughts|my book|It is below)",
                        re.I)

# Every tail shape that has shipped. Matched longest-first so a short pattern
# cannot eat half of a long one and leave a fragment behind.
OLD_TAILS = [
    r"Everything else I know is inside The Quiet Between Thoughts\.\s*\U0001f64f?\s*"
    r"When you are ready,? reply YES and I will leave you a small gift\.\s*\U0001f64f?",
    r"The full thirty days are in my book below\.\s*"
    r"Reply YES and I will leave you a small gift\.\s*\U0001f64f?",
    r"The full thirty days are inside my book below\.\s*"
    r"Reply YES and I will leave you a small gift\.\s*\U0001f64f?",
    # last-resort catch: any sentence that asks for YES
    r"(?:When you are ready,?\s*)?[Rr]eply YES[^.]*\.\s*\U0001f64f?",
]


def key():
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith("BLOTATO_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("BLOTATO_API_KEY missing from .env")


def api(path, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data,
        {"blotato-api-key": key(), "Content-Type": "application/json"},
        method=method)
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        # The bare status tells you nothing; the body names the offending field
        # (this is how the 20-char button cap was found).
        raise SystemExit(f"{e.code} on {method or 'GET'} {path}: "
                         f"{e.read().decode()[:400]}")


def rewrite(body):
    """Swap the YES tail for the gift tail. Returns None if nothing to do."""
    new = body
    for pat in OLD_TAILS:
        if re.search(pat, new):
            new = re.sub(pat, "", new).strip()
            break
    else:
        return None
    # Removing a tail that sat after a 🙏 leaves the 🙏 dangling mid-message;
    # strip a trailing one so the new tail supplies the only closing gesture.
    new = re.sub(r"\s*\U0001f64f\s*$", "", new)
    new = re.sub(r"\s{2,}", " ", new).strip()
    tail = TAIL_SHORT if NAMES_BOOK.search(new) else TAIL
    return (new + " " + tail).strip()


def main():
    dry = "--dry" in sys.argv
    autos = (api("/dm-automations").get("items")
             or api("/dm-automations").get("automations") or [])
    reg = json.load(open(REG))
    by_id = {str(a.get("id")): a for a in reg["automations"]}

    changed, skipped = [], []
    for a in autos:
        aid = str(a.get("id"))
        body = a.get("dmMessage") or ""
        new = rewrite(body)
        if not new:
            skipped.append((aid, a.get("name", "")))
            continue
        buttons = [{"title": BUTTON_TITLE, "type": "url", "url": GIFT_URL}]
        print(f"\n=== {aid}  {a.get('name','')}")
        print(f"  OLD: ...{body[-130:]}")
        print(f"  NEW: ...{new[-130:]}")
        print(f"  BTN: {BUTTON_TITLE} -> {GIFT_URL}")
        if not dry:
            # PATCH carries only what changes; trigger/target stay as published.
            # The changed fields must sit under a "patch" key — a bare
            # {dmMessage, buttons} body is rejected 400.
            api(f"/dm-automations/{aid}",
                {"patch": {"dmMessage": new, "buttons": buttons}},
                method="PATCH")
            if aid in by_id:
                by_id[aid]["dmMessage"] = new
                by_id[aid]["buttons"] = buttons
        changed.append(aid)

    if not dry:
        reg["gumroad_gift_url"] = GIFT_URL
        reg["note"] = (reg.get("note", "") +
                       " | 2026-08-15: YES gate removed from every practice DM; "
                       "the 20% code is pre-applied on the button instead.").strip(" |")
        json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)

    print(f"\n{'WOULD CHANGE' if dry else 'CHANGED'}: {len(changed)} -> {changed}")
    print(f"untouched ({len(skipped)}): "
          f"{[f'{i} {n[:28]}' for i, n in skipped]}")


if __name__ == "__main__":
    main()
