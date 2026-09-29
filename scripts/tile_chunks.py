#!/usr/bin/env python3
"""Tile a reel's narration into kling-sized chunks on sentence boundaries.

    python3 scripts/tile_chunks.py 12 [13 ...]   # writes chunks_reel<N>.json

Uses the ElevenLabs character alignment (voice_<N>.json from eleven.py), so cut
points are exact sample times, not estimates.

Rules, all measured on earlier reels:
  * chunks 15-20s (kling has no 15s cap; fewer joins = less identity drift)
  * never open a chunk with a fragment under MIN_OPEN_WORDS words -- reel 6's
    "Not even love" pause came from exactly that
  * last chunk may run to 24s rather than strand a short tail
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")

MIN_S, MAX_S, TAIL_MAX = 13.0, 20.0, 24.0
MIN_OPEN_WORDS = 5


def sentences(align):
    """(text, start, end) per sentence from character alignment."""
    if "alignment" in align:
        align = align["alignment"]
    chars = align.get("chars") or align.get("characters")
    s = align.get("char_starts") or align.get("character_start_times_seconds")
    e = align.get("char_ends") or align.get("character_end_times_seconds")
    text = "".join(chars)
    out = []
    start = 0
    for m in re.finditer(r"[.!?]+(?=\s|$)", text):
        end = m.end()
        seg = text[start:end].strip()
        if seg:
            out.append((seg, s[start], e[end - 1]))
        start = end
    return out


def tile(sents):
    """Greedy forward tiling with a look-ahead against short openers."""
    chunks, cur = [], []
    for i, (txt, s0, e0) in enumerate(sents):
        if not cur:
            cur = [(txt, s0, e0)]
            continue
        dur = e0 - cur[0][1]
        cur_dur = cur[-1][2] - cur[0][1]
        nxt_short = len(txt.split()) < MIN_OPEN_WORDS
        # close the chunk when adding would blow MAX -- unless the incoming
        # sentence is a short fragment, which must never open the next chunk
        if dur > MAX_S and cur_dur >= MIN_S and not nxt_short:
            chunks.append(cur)
            cur = [(txt, s0, e0)]
        else:
            cur.append((txt, s0, e0))
    if cur:
        if chunks and cur[-1][2] - cur[0][1] < MIN_S:
            # fold a short tail into the previous chunk if it stays <= TAIL_MAX
            merged = chunks[-1] + cur
            if merged[-1][2] - merged[0][1] <= TAIL_MAX:
                chunks[-1] = merged
            else:
                chunks.append(cur)
        else:
            chunks.append(cur)
    return chunks


def main(rid):
    align = json.load(open(os.path.join(ART, f"voice_{rid}.json")))
    sents = sentences(align)
    chunks = tile(sents)
    plan = []
    for n, ch in enumerate(chunks, 1):
        s0, e0 = ch[0][1], ch[-1][2]
        plan.append({"n": n, "s": round(s0, 3), "e": round(e0, 3),
                     "dur": round(e0 - s0, 3),
                     "text": " ".join(t for t, _, _ in ch)})
    out = os.path.join(ART, f"chunks_reel{rid}.json")
    json.dump(plan, open(out, "w"), indent=1)
    durs = ", ".join(f"{p['dur']:.1f}" for p in plan)
    print(f"reel {rid}: {len(plan)} chunks [{durs}]")
    for p in plan:
        opener = p["text"].split(".")[0]
        if len(opener.split()) < MIN_OPEN_WORDS:
            print(f"  !! chunk {p['n']} opens short: {opener!r}")


if __name__ == "__main__":
    for rid in sys.argv[1:]:
        main(rid)
