#!/usr/bin/env python3
"""Guard against reusing a DM keyword (mirror of ledger.py check).

    python3 scripts/keyword_check.py <keyword...>   # exit 1 if ANY is taken
    python3 scripts/keyword_check.py --list         # show all taken keywords

Checks BOTH data/dm_registry.json and the LIVE Blotato automations, so it
cannot be fooled by a stale registry. RUN BEFORE scripting any reel with a
comment CTA.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from dm_backfill import api  # noqa: E402


def taken():
    kws = {}
    reg = json.load(open(os.path.join(ROOT, "data", "dm_registry.json")))
    for a in reg["automations"]:
        for k in a["keywords"]:
            kws.setdefault(k.lower(), []).append(f"registry #{a['id']}")
    try:
        for a in api("/dm-automations")["items"]:
            if not a.get("isActive"):
                continue
            for k in (a.get("trigger") or {}).get("keywords") or []:
                kws.setdefault(k.lower(), []).append(f"live #{a['id']}")
    except Exception as e:
        print(f"WARNING: live check failed ({e}) — registry only", file=sys.stderr)
    return kws


def main():
    kws = taken()
    if len(sys.argv) < 2 or sys.argv[1] == "--list":
        for k in sorted(kws):
            print(k)
        return 0
    bad = 0
    for want in sys.argv[1:]:
        w = want.lower().strip()
        if w in kws:
            print(f"TAKEN: '{want}' ({', '.join(set(kws[w]))})")
            bad = 1
        else:
            print(f"free:  '{want}'")
    return bad


if __name__ == "__main__":
    sys.exit(main())
