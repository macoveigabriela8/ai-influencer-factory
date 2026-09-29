#!/usr/bin/env python3
"""Put the Gumroad URL in the DM TEXT.

Blotato sends `text` + a malformed `attachment.buttons` in one message; Instagram
renders the text and silently drops the button, so every DM has promised a gift
with no way to reach it. A bare URL in the text is tappable on every IG surface
and involves no template rendering, so it cannot fail the same way.

Usage:  python3 scripts/fix_dm_links.py            # dry run, prints the diff
        python3 scripts/fix_dm_links.py --apply    # patch live
        python3 scripts/fix_dm_links.py --apply --only 1455
"""
import json, os, sys, urllib.request

URL = "https://masterkaion.gumroad.com/l/quiet/STILLNESS"
TAIL = "\n\nThe book, with your gift already on it:\n" + URL
API = "https://backend.blotato.com/v2"
IG_DM_LIMIT = 640   # measured: API rejects >640 (not the 1000 IG allows)

key = None
for line in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
    if line.startswith("BLOTATO_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
H = {"blotato-api-key": key, "Content-Type": "application/json"}


def req(method, path, body=None):
    r = urllib.request.Request(
        API + path, method=method, headers=H,
        data=json.dumps(body).encode() if body else None)
    with urllib.request.urlopen(r) as f:
        return json.loads(f.read())


def patched(msg):
    """Append the URL; make the 'below' references literally true."""
    if URL in msg:
        return None                      # already carries the link
    return msg.rstrip() + TAIL


def unlinked():
    """Active automations whose DM promises a gift with no reachable link.

    The button attachment blotato sends alongside the text is dropped by
    Instagram, so the URL must be in the TEXT. Verified against a real
    delivered DM 2026-08-25 - config alone is not evidence of delivery.
    """
    out = []
    for a in req("GET", "/dm-automations")["items"]:
        if a.get("isActive") and URL not in a.get("dmMessage", ""):
            out.append((a["id"], a.get("name", "")))
    return out


def main():
    apply_ = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    autos = req("GET", "/dm-automations")["items"]
    todo, skipped = [], []
    for a in autos:
        if not a.get("isActive"):
            skipped.append((a["id"], "inactive"))
            continue
        if only and str(a["id"]) != only:
            continue
        new = patched(a.get("dmMessage", ""))
        if new is None:
            skipped.append((a["id"], "already has url"))
            continue
        if len(new) > IG_DM_LIMIT:
            skipped.append((a["id"], f"WOULD OVERFLOW {len(new)}c"))
            continue
        todo.append((a, new))

    for a, new in todo:
        print(f"{a['id']:>5}  {a['name'][:44]:<44} {len(a['dmMessage']):>4}c -> {len(new):>4}c")
    for i, why in skipped:
        print(f"{i:>5}  -- skipped: {why}")
    print(f"\n{len(todo)} to patch, {len(skipped)} skipped")

    if "--check" in sys.argv:
        # gate: any active automation whose DM promises a gift with no reachable
        # link is a dead funnel. Calibrated 2026-08-25 on a known-bad set of 36.
        if todo:
            print(f"FAIL: {len(todo)} active automation(s) have no gumroad url in the DM TEXT")
            sys.exit(1)
        print(f"OK: all {len(autos)} automations carry the url in the text")
        sys.exit(0)

    if not apply_:
        print("\ndry run. re-run with --apply")
        return

    for a, new in todo:
        req("PATCH", f"/dm-automations/{a['id']}", {"patch": {"dmMessage": new}})
        print(f"patched {a['id']}")




if __name__ == "__main__":
    main()
