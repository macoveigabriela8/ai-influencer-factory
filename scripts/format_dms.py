#!/usr/bin/env python3
"""Normalise every Kaion DM automation: one tail, one button label.

The practice (the reel-specific part) is never touched - only the closing
offer, which had drifted into 5 different wordings and 4 button labels.

  python3 scripts/format_dms.py            # dry run
  python3 scripts/format_dms.py --apply
  python3 scripts/format_dms.py --check    # exits 1 if any active one is off-spec
"""
import json, re, sys, urllib.request, urllib.error

URL   = "https://masterkaion.gumroad.com/l/quiet/STILLNESS"
BTN   = "Your gift · 20% off"          # <= 20 chars, the label already on 29 of 37
TAIL  = ("The full thirty days are in my book. Your gift of twenty percent "
         "is already on it, with nothing to ask me for. \U0001f64f\n" + URL)
LIMIT = 640                             # measured: the API rejects longer

# every closing variant seen in the wild, longest first so partials cannot bite
TAILS = [
    r"The full thirty days are in my book\..*$",
    r"The full thirty days are inside The Quiet Between Thoughts\..*$",
    r"Everything I know is inside The Quiet Between Thoughts\..*$",
    r"The rest of what I know is inside The Quiet Between Thoughts\..*$",
    r"My friend, everything I teach is in one small book.*$",
    r"Here is the gift, my friend\..*$",
    r"The book, with your gift already on it:.*$",
    r"Your gift 20% off already on it:.*$",
    r"Thirty days, with your gift already on it:.*$",
]

URLBLOCK = re.compile(r"\n*[^\n]*(?:gift|book|Thirty days)[^\n]*:\s*\n?" 
                      + re.escape(URL) + r"\s*$", re.I)

def strip_tail(m):
    for pat in TAILS:
        m = re.sub(pat, "", m, flags=re.S | re.I)
    return m.rstrip().rstrip("\U0001f64f").rstrip()

def target(m):
    """Body + one canonical offer. NEVER returns a message without its body.

    Some automations ARE the offer (257 link-words, 258 yes-gift): their whole
    text matches a tail pattern, so stripping tails empties them. Caught on the
    dry run 2026-09-12 - both would have lost their own wording and become the
    generic close. When stripping leaves nothing, the message keeps its own
    words and only gains the link.
    """
    m = URLBLOCK.sub("", m).rstrip()          # drop any previously appended block
    body = strip_tail(m)
    if not body.strip():                      # offer-only automation
        return m.rstrip() + "\n" + URL
    return body + "\n\n" + TAIL

def key():
    for l in open(".env"):
        if l.startswith("BLOTATO_API_KEY"):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("no BLOTATO_API_KEY")

H = {"blotato-api-key": key(), "Content-Type": "application/json"}

def items():
    r = urllib.request.Request("https://backend.blotato.com/v2/dm-automations", headers=H)
    return json.loads(urllib.request.urlopen(r, timeout=90).read())["items"]

def main():
    apply_ = "--apply" in sys.argv
    todo = []
    for a in items():
        if not a.get("isActive"):
            continue
        m, new = a.get("dmMessage") or "", None
        new = target(a.get("dmMessage") or "")
        btn = a.get("buttons") or []
        need_btn = not (len(btn) == 1 and btn[0].get("title") == BTN
                        and btn[0].get("url") == URL)
        if m != new or need_btn:
            todo.append((a, new, need_btn, len(new) > LIMIT))

    for a, new, nb, over in todo:
        flag = "  !! OVER %d" % len(new) if over else ""
        print(f"{a['id']:>5}  {a.get('name','')[:40]:<40} {len(a['dmMessage']):>4}->{len(new):>4}c"
              f"{'  +btn' if nb else ''}{flag}")
    bad = [t for t in todo if t[3]]
    print(f"\n{len(todo)} to normalise, {len(bad)} would exceed {LIMIT}c")

    if "--check" in sys.argv:
        sys.exit(1 if todo else 0)
    if not apply_:
        print("\ndry run. re-run with --apply")
        return
    if bad:
        print("refusing to apply while any message would overflow")
        return
    for a, new, nb, _ in todo:
        patch = {"dmMessage": new}
        if nb:
            patch["buttons"] = [{"type": "url", "title": BTN, "url": URL}]
        try:
            rq = urllib.request.Request(
                f"https://backend.blotato.com/v2/dm-automations/{a['id']}",
                method="PATCH", headers=H, data=json.dumps({"patch": patch}).encode())
            urllib.request.urlopen(rq, timeout=60)
            print("normalised", a["id"])
        except urllib.error.HTTPError as e:
            print("FAILED", a["id"], e.code, e.read().decode()[:140])

if __name__ == "__main__":
    main()
