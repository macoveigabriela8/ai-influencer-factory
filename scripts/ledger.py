#!/usr/bin/env python3
"""The production ledger: what exists, what it copies, where it is published.

    python3 scripts/ledger.py show                 # human table (also rewrites .md)
    python3 scripts/ledger.py brief                # 12-line summary for session start
    python3 scripts/ledger.py check DVZg8wAkYgk    # exit 1 if that source is used
    python3 scripts/ledger.py add 12 "Topic" DXxxxx 123456
    python3 scripts/ledger.py set 7 status scheduled --when 2026-08-08T09:14:00Z
    python3 scripts/ledger.py set 7 status published --url https://...

WHY THIS EXISTS. On 2026-08-04 the user asked whether a batch had regenerated
already-published reels. It had not, but proving it took file-timestamp
forensics because the only record was prose. At ~$6 of generation per reel a
duplicate is real money, and "is this new?" has to be answerable from a file in
one second, by a session that remembers nothing.

THE INVARIANT: a source shortcode appears at most once. `check` is the guard --
call it before writing a script and before submitting any generation job.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(ROOT, "output", "PRODUCTION_LEDGER.json")
MD = os.path.join(ROOT, "output", "PRODUCTION_LEDGER.md")

STATUSES = ("built", "scheduled", "published")


def load():
    return json.load(open(JSON)) if os.path.exists(JSON) else {}


def save(d):
    json.dump(d, open(JSON, "w"), indent=1)
    write_md(d)


def market(rid):
    """Market prefix of a reel id: 'ES1' -> 'ES', 'PT3' -> 'PT', '12'/'B' -> 'EN'."""
    m = ""
    for ch in rid:
        if ch.isalpha() and ch.isupper():
            m += ch
        else:
            break
    return m if m in ("ES", "PT", "RO") else "EN"


def dupes(d):
    """Duplicate = same source recreated twice WITHIN one market. The same
    source appearing in different markets is deliberate localization
    (architecture decision 2026-08-08, three-account expansion)."""
    seen = {}
    for rid, r in d.items():
        seen.setdefault((market(rid), r["src"]), []).append(rid)
    return {f"{m}:{s}": ids for (m, s), ids in seen.items() if len(ids) > 1}


def write_md(d):
    dup = dupes(d)
    rows = ["| reel | topic | copies (source) | his plays | generated | status | link |",
            "|---|---|---|---|---|---|---|"]
    for rid, r in sorted(d.items(), key=lambda kv: (len(kv[0]), kv[0])):
        st = r.get("status", "built")
        when = r.get("when", "")
        st_txt = {"built": "built — NOT posted",
                  "scheduled": f"SCHEDULED {when}",
                  "published": "PUBLISHED"}.get(st, st)
        rows.append(f"| {rid} | {r['topic']} | [{r['src']}]"
                    f"(https://www.instagram.com/p/{r['src']}/) | {r['plays']:,} | "
                    f"{r['gen']} | {st_txt} | {r.get('url','')} |")
    body = f"""# PRODUCTION LEDGER — single source of truth

⚠️ **READ THIS BEFORE WRITING A SCRIPT OR SPENDING A CREDIT.**
Every reel we have ever made is here, with the source reel it copies.

- **Source account copied:** [@monkcheen](https://www.instagram.com/monkcheen/)
- **Our account:** [@master_kaion](https://www.instagram.com/master_kaion/)
- **Invariant:** a source shortcode may appear at most ONCE. Regenerating a
  topic we already produced costs ~$6 and is the most avoidable mistake here.
- **Guard:** `python3 scripts/ledger.py check <shortcode>` exits 1 if used.

{chr(10).join(rows)}

**{len(d)} reels · {len(set(r['src'] for r in d.values()))} distinct sources · duplicates: {dup or 'none'}**

Counts — published {sum(1 for r in d.values() if r.get('status')=='published')} ·
scheduled {sum(1 for r in d.values() if r.get('status')=='scheduled')} ·
built-not-posted {sum(1 for r in d.values() if r.get('status','built')=='built')}

Update a row the moment a reel is built, scheduled, or published:
`python3 scripts/ledger.py set <reel> status scheduled --when <ISO>`
"""
    open(MD, "w").write(body)


def cmd_show():
    d = load()
    write_md(d)
    print(open(MD).read())


def cmd_brief():
    """Compact enough to inject into every session's context."""
    d = load()
    if not d:
        print("PRODUCTION LEDGER: empty")
        return
    dup = dupes(d)
    pub = [k for k, r in d.items() if r.get("status") == "published"]
    sch = [k for k, r in d.items() if r.get("status") == "scheduled"]
    blt = [k for k, r in d.items() if r.get("status", "built") == "built"]
    print("PRODUCTION LEDGER (output/PRODUCTION_LEDGER.md) — copying @monkcheen -> @master_kaion")
    print(f"  {len(d)} reels made. NEVER recreate a source shortcode already listed.")
    print(f"  published: {', '.join(pub) or '-'}")
    print(f"  scheduled: {', '.join(sch) or '-'}")
    print(f"  built, not posted: {', '.join(blt) or '-'}")
    print("  sources used: " + " ".join(sorted(r["src"] for r in d.values())))
    if dup:
        print(f"  !! DUPLICATE SOURCES: {dup}")
    print("  guard before any spend: python3 scripts/ledger.py check <shortcode>")
    reg = os.path.join(ROOT, "data", "competitors", "REGISTRY.md")
    if os.path.exists(reg):
        print("  COMPETITOR & ENGINE REGISTRY: data/competitors/REGISTRY.md "
              "(all known monk accounts, outliers, engine verdicts — read "
              "before picking topics or engines)")

    # The corpus is the SOURCE-SELECTION authority. Without this line a fresh
    # session re-discovers "we only have 62 transcripts" and re-does a scrape
    # that has already been paid for.
    corp = os.path.join(ROOT, "data", "competitors", "CORPUS.md")
    if os.path.exists(corp):
        import json as _j
        cdir = os.path.join(ROOT, "data", "competitors", "corpus")
        n = len(os.listdir(cdir)) if os.path.isdir(cdir) else 0
        print(f"  SOURCE CORPUS: data/competitors/CORPUS.md — {n} competitor "
              f"posts, full transcripts, ranked by COMMENT RATE (never plays). "
              f"Pick every new reel from here; the `used` column is already "
              f"cross-referenced against this ledger. Audio is on disk at "
              f"data/competitors/audio/ so it can be re-transcribed forever — "
              f"do NOT re-scrape, the CDN urls in older *.json are all dead.")


def cmd_hook():
    """SessionStart hook form: emit the brief as injected context.

    Wrapped in the hook JSON envelope so the summary lands in the model's
    context at session start rather than only in the user's terminal. Failures
    must stay silent -- a broken hook must never block a session.
    """
    import io
    import contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            cmd_brief()
        text = buf.getvalue()
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext":
            "MANDATORY CHECK — reels already produced for this project. "
            "Never recreate a source shortcode listed here.\n" + text}}))


def cmd_check(src, mkt="EN"):
    d = load()
    hit = [rid for rid, r in d.items() if r["src"] == src and market(rid) == mkt]
    if hit:
        r = d[hit[0]]
        print(f"ALREADY MADE — reel {hit[0]} ({r['topic']}), generated {r['gen']}, "
              f"status {r.get('status','built')}. DO NOT regenerate.")
        sys.exit(1)
    print(f"{src} is unused — safe to produce.")


def cmd_add(rid, topic, src, plays):
    d = load()
    if rid in d:
        sys.exit(f"reel {rid} already in ledger: {d[rid]['topic']}")
    hit = [k for k, r in d.items() if r["src"] == src and market(k) == market(rid)]
    if hit:
        sys.exit(f"REFUSED: source {src} is already reel {hit[0]} ({d[hit[0]]['topic']}) in this market")
    gen = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
    d[rid] = dict(topic=topic, src=src, plays=int(plays), gen=gen, status="built")
    save(d)
    print(f"added reel {rid}: {topic} <- {src}")


def cmd_set(rid, field, value, when=None, url=None):
    d = load()
    if rid not in d:
        sys.exit(f"no reel {rid} in ledger")
    if field == "status" and value not in STATUSES:
        sys.exit(f"status must be one of {STATUSES}")
    d[rid][field] = value
    if when:
        d[rid]["when"] = when
    if url:
        d[rid]["url"] = url
    save(d)
    print(f"reel {rid}: {field} = {value}" + (f" ({when or url})" if (when or url) else ""))


if __name__ == "__main__":
    a = sys.argv[1:] or ["brief"]
    if a[0] == "show":
        cmd_show()
    elif a[0] == "brief":
        cmd_brief()
    elif a[0] == "hook":
        cmd_hook()
    elif a[0] == "check":
        cmd_check(a[1], a[2].upper() if len(a) > 2 else "EN")
    elif a[0] == "add":
        cmd_add(a[1], a[2], a[3], a[4])
    elif a[0] == "set":
        when = a[a.index("--when") + 1] if "--when" in a else None
        url = a[a.index("--url") + 1] if "--url" in a else None
        cmd_set(a[1], a[2], a[3], when, url)
    else:
        sys.exit(__doc__)
