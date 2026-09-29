#!/usr/bin/env python3
"""Build the PERMANENT competitor corpus — scrape once, usable forever.

    python3 scripts/build_corpus.py --scrape        # fetch metadata + audio
    python3 scripts/build_corpus.py --transcribe    # whisper the new audio
    python3 scripts/build_corpus.py --index         # rebuild CORPUS.md
    python3 scripts/build_corpus.py                 # all three, in order

WHY THIS EXISTS. Every previous scrape stored `videoUrl`, which is a SIGNED CDN
link. They all now return 403 — verified 2026-08-15 across monkcheen_full,
monkcheen_raw and yangmunus_posts. So we held 471 posts of metadata and could
not read a single script, and 209 monkcheen posts stayed untranscribed for
weeks. The corpus was never durable; it just looked durable.

The fix is to store what cannot expire:

    data/competitors/corpus/<shortcode>.json   metadata + FULL TRANSCRIPT
    data/competitors/audio/<shortcode>.m4a     ~1 MB, enough to re-transcribe
    data/competitors/videos/<shortcode>.mp4    only for recreation candidates,
                                               because frame-gridding the source
                                               is mandatory before scripting

Audio rather than video for the bulk: a 96s reel is ~25 MB of video and ~1 MB of
audio, and the transcript is what selection actually needs. 470 posts of audio
is under half a gigabyte; of video it would be twelve.

Measured cost 2026-08-15: **$0.0027 per post** (a 2-post run billed $0.0054), so
the whole 471-post corpus is well under $2 on a $5 free account. Do not upgrade
the plan for this.

`CORPUS.md` is regenerated at the end and is what a fresh session reads: one row
per post with plays, comment rate, vein, the hook, and whether the ledger has
already used that shortcode.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = os.path.join(ROOT, "data", "competitors")
CORPUS = os.path.join(COMP, "corpus")
AUDIO = os.path.join(COMP, "audio")
VIDEO = os.path.join(COMP, "videos")
INDEX = os.path.join(COMP, "CORPUS.md")

ACCOUNTS = ["monkcheen", "yangmunus"]
ACTOR = "apify~instagram-scraper"
LIMIT = 400                       # per account; both are under this today

FAM = ["daughter", "son", "mother", "father", "child", "children", "parent",
       "family", "husband", "wife", "sister", "brother", "grandchild", "mom",
       "dad", "partner"]
IDENT = ["you are", "who you", "becoming", "yourself", "you were", "excluded",
         "your name", "belong", "boundaries", "your truth", "you have never"]
RITUAL = ["tonight", "place a glass", "salt", "pillow", "candle", "before you "
          "sleep", "ritual", "bay leaf", "under your", "wash your", "three days"]
HEALTH = ["liver", "belly", "kidney", "sciatica", "meals", "shower", "food",
          "eat", "blood", "sugar", "legs", "doctor", "pain", "bloating"]


def token():
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith("APIFY_TOKEN_2="):
            return line.split("=", 1)[1].strip()
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith("APIFY_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no APIFY token in .env")


def vein(text):
    t = (text or "").lower()
    sc = {"family": sum(t.count(w) for w in FAM),
          "identity": sum(t.count(w) for w in IDENT),
          "ritual": sum(t.count(w) for w in RITUAL),
          "health": sum(t.count(w) for w in HEALTH)}
    top = max(sc, key=sc.get)
    return top if sc[top] else "other"


def used_shortcodes():
    out = set()
    p = os.path.join(ROOT, "output", "PRODUCTION_LEDGER.md")
    if os.path.exists(p):
        for line in open(p):
            out.update(re.findall(r"\[([A-Za-z0-9_\-]{8,})\]", line))
    return out


def scrape():
    tok = token()
    for d in (CORPUS, AUDIO, VIDEO):
        os.makedirs(d, exist_ok=True)
    for acct in ACCOUNTS:
        body = {"directUrls": [f"https://www.instagram.com/{acct}/"],
                "resultsType": "posts", "resultsLimit": LIMIT,
                "addParentData": False}
        u = f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={tok}"
        req = urllib.request.Request(u, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        rid = json.load(urllib.request.urlopen(req, timeout=120))["data"]["id"]
        print(f"{acct}: run {rid}")
        while True:
            time.sleep(10)
            s = json.load(urllib.request.urlopen(
                f"https://api.apify.com/v2/actor-runs/{rid}?token={tok}",
                timeout=60))["data"]
            if s["status"] not in ("RUNNING", "READY"):
                break
        items = json.load(urllib.request.urlopen(
            f"https://api.apify.com/v2/datasets/{s['defaultDatasetId']}"
            f"/items?token={tok}", timeout=300))
        print(f"  {s['status']} · ${s.get('usageTotalUsd') or 0:.4f} · "
              f"{len(items)} posts")

        for it in items:
            sc = it.get("shortCode")
            if not sc:
                continue
            rec = {
                "shortcode": sc, "account": acct,
                "url": it.get("url"), "type": it.get("type"),
                "plays": it.get("videoPlayCount") or it.get("videoViewCount") or 0,
                "likes": it.get("likesCount") or 0,
                "comments": it.get("commentsCount") or 0,
                "caption": (it.get("caption") or "").strip(),
                "timestamp": it.get("timestamp"),
                "duration": it.get("videoDuration"),
                "scraped": time.strftime("%Y-%m-%d"),
            }
            path = os.path.join(CORPUS, sc + ".json")
            if os.path.exists(path):                # keep any transcript we have
                rec["transcript"] = json.load(open(path)).get("transcript", "")
            json.dump(rec, open(path, "w"), ensure_ascii=False, indent=1)

            # AUDIO NOW, while the signed link is alive. This is the whole point.
            a = os.path.join(AUDIO, sc + ".m4a")
            if not os.path.exists(a) and it.get("videoUrl"):
                try:
                    r = subprocess.run(
                        ["ffmpeg", "-v", "error", "-y", "-i", it["videoUrl"],
                         "-vn", "-c:a", "aac", "-b:a", "64k", a],
                        capture_output=True, timeout=300)
                    if r.returncode:
                        print(f"    {sc}: no audio")
                except subprocess.TimeoutExpired:
                    print(f"    {sc}: audio timeout")


def transcribe():
    import mlx_whisper
    todo = [f for f in sorted(os.listdir(AUDIO)) if f.endswith(".m4a")
            and not json.load(open(os.path.join(CORPUS, f[:-4] + ".json"))
                              ).get("transcript")]
    print(f"{len(todo)} to transcribe")
    for i, f in enumerate(todo, 1):
        sc = f[:-4]
        wav = "/tmp/corpus.wav"
        if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i",
                           os.path.join(AUDIO, f), "-ac", "1", "-ar", "16000",
                           wav], capture_output=True).returncode:
            continue
        text = mlx_whisper.transcribe(
            wav, path_or_hf_repo="mlx-community/whisper-small.en-mlx")["text"].strip()
        p = os.path.join(CORPUS, sc + ".json")
        rec = json.load(open(p))
        rec["transcript"] = text
        rec["vein"] = vein(text)
        json.dump(rec, open(p, "w"), ensure_ascii=False, indent=1)
        if i % 10 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {sc}")


def cluster(rows):
    """Group near-identical scripts and mark the strongest instance of each.

    THE MISTAKE THIS PREVENTS (measured 2026-08-15). These accounts repost the
    same script many times, and the versions differ by up to 40x in plays:

        DSXucA2kT96  18,535,469   "Keep it private until it's permanent"
        DT5MoDUAL6D     461,871   "The fastest way to ruin a good thing"   <- we built reel 26 from THIS
        DVEI18AgH7h     958,440   "Never start your morning..."
        DVpPFVSDIPj      27,464   same script                              <- we built reel 12 from THIS

    47 such clusters exist in the corpus. The ledger blocks a repeated
    SHORTCODE, which does nothing here: these are different shortcodes
    carrying the same script. Two of the four clusters we have drawn from were
    entered through the weak twin, and using either twin burns the topic — so
    the 18.5M version is now unusable because reel 26 exists.

    Rule: pick `BEST` rows. A `dup` row is the same idea, already available in
    a stronger version; a `USED-CLUSTER` row means we have already made this
    topic under some other shortcode.
    """
    import difflib

    def words(r):
        return re.sub(r"[^a-z ]", "", (r.get("transcript") or "").lower()
                      ).split()[:120]

    seen, groups = set(), []
    for i, a in enumerate(rows):
        if a["shortcode"] in seen or not a.get("transcript"):
            continue
        grp = [a]
        seen.add(a["shortcode"])
        wa = words(a)
        for b in rows[i + 1:]:
            if b["shortcode"] in seen or not b.get("transcript"):
                continue
            if difflib.SequenceMatcher(None, wa, words(b),
                                       autojunk=False).ratio() > 0.55:
                grp.append(b)
                seen.add(b["shortcode"])
        groups.append(grp)

    for grp in groups:
        best = max(grp, key=lambda x: x.get("plays") or 0)
        burned = any(x["used"] for x in grp)
        for x in grp:
            x["cluster_used"] = burned
            x["best"] = (x is best)
            x["cluster_n"] = len(grp)


def index():
    used = used_shortcodes()
    rows = []
    for f in os.listdir(CORPUS):
        r = json.load(open(os.path.join(CORPUS, f)))
        t = r.get("transcript") or ""
        r["cr"] = (r["comments"] / r["plays"] * 100) if r.get("plays") else 0
        r["vein"] = r.get("vein") or vein(t)
        r["used"] = r["shortcode"] in used
        r["hook"] = " ".join(t.split()[:16])
        rows.append(r)
    cluster(rows)
    rows.sort(key=lambda x: -x["cr"])
    with open(INDEX, "w") as o:
        o.write("# COMPETITOR CORPUS — scraped once, permanent\n\n")
        o.write(f"{len(rows)} posts · "
                f"{sum(1 for r in rows if r.get('transcript'))} transcribed · "
                f"{sum(1 for r in rows if r['used'])} already produced\n\n")
        o.write("Ranked by COMMENT RATE, never by plays — play count is\n"
                "anti-correlated with our results (see CLAUDE.md). Rebuild with\n"
                "`python3 scripts/build_corpus.py --index`.\n\n")
        o.write("**PICK ONLY `BEST` ROWS.** These accounts repost the same "
                "script at up to 40x different play counts, and the ledger's "
                "shortcode guard cannot see it. `dup` = a stronger version of "
                "this exact script exists; `USED-CLUSTER` = we have already "
                "produced this topic under a different shortcode.\n\n")
        o.write("| pick | c-rate | plays | acct | shortcode | vein | used | hook |\n")
        o.write("|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            if not r.get("transcript"):
                continue
            pick = ("USED-CLUSTER" if r.get("cluster_used") and not r["used"]
                    else "BEST" if r.get("best") else "dup")
            o.write(f"| {pick} | {r['cr']:.3f}% | {r['plays']:,} | "
                    f"{r['account'][:4]} | "
                    f"`{r['shortcode']}` | {r['vein']} | "
                    f"{'YES' if r['used'] else ''} | {r['hook'][:70]} |\n")
    print(f"  {INDEX}: {len(rows)} posts")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "--scrape" in a:
        scrape()
    if not a or "--transcribe" in a:
        transcribe()
    if not a or "--index" in a:
        index()
