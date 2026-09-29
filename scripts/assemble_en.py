#!/usr/bin/env python3
"""EN master assembly: single kling clip -> subtitled dry 1080x1920 master.

    python3 scripts/assemble_en.py 25 [24 ...]

Same machinery as assemble_pt.py, pointed at the EN lane: source clip is
output/assets/avatar_<id>.mp4, script text comes from scripts/reels.json
(beats -> lines), whisper runs in English, master lands in output/reels/.
No music baked in — the user picks trending audio in the app.

Design copied from monge.yang's own frames (2026-08-08): centered white
subtitles with a soft black box, mid-lower band, no CTA cards, no baked
music (TikTok sound is added in-app; IG version gets a bed later).
Whisper multilingual gives the timings; cues are word-grouped to stay short.
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
REELS = os.path.join(ROOT, "output", "reels")
MODEL = "mlx-community/whisper-large-v3-turbo"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_SIZE = 60          # FIXED for the whole reel — size never varies per card
SAFE_W = 940            # max box width incl padding
LINE_W = SAFE_W - 56    # max measured text width per line
from PIL import ImageFont as _IF
_FONT = _IF.truetype(FONT_PATH, FONT_SIZE)
from PIL import ImageDraw as _ID, Image as _IM
_MEAS = _ID.Draw(_IM.new("RGB", (8, 8)))


def text_w(t):
    return _MEAS.textlength(t, font=_FONT)


def wrap_px(text):
    """Wrap into lines that each measure <= LINE_W at the fixed font size."""
    lines, line = [], ""
    for w in text.split():
        cand = (line + " " + w).strip()
        if line and text_w(cand) > LINE_W:
            lines.append(line)
            line = w
        else:
            line = cand
    if line:
        lines.append(line)
    return lines


def ts(t):
    h, m = divmod(t, 3600)
    m, s = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def junk(t):
    """Whisper artifacts that must never reach a caption card: breath/hum
    transcribed as a repeated letter, or tokens with no letters at all."""
    bare = re.sub(r"[^\wÀ-ÿ]", "", t)
    if not bare:
        return True
    if len(bare) >= 4 and len(set(bare.lower())) == 1:
        return True
    return False


def align_to_script(words, script):
    """Replace whisper's spelling with the script's own words, matched by
    position via difflib. Whisper keeps only the timing role. Unmatched
    whisper words (insertions) are dropped; unmatched script words ride
    along with the previous matched word so no text is lost."""
    import difflib
    wt = [re.sub(r"[^\wÀ-ÿ]", "", w["word"]).lower() for w in words]
    st_tokens = script.split()
    st = [re.sub(r"[^\wÀ-ÿ]", "", t).lower() for t in st_tokens]
    sm = difflib.SequenceMatcher(a=wt, b=st, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append({"word": st_tokens[j1 + k],
                            "start": words[i1 + k]["start"],
                            "end": words[i1 + k]["end"]})
        elif tag == "replace":
            span = words[i1:i2]
            toks = st_tokens[j1:j2]
            for k, t in enumerate(toks):
                w = span[min(k, len(span) - 1)]
                out.append({"word": t, "start": w["start"], "end": w["end"]})
        elif tag == "insert" and out:
            for t in st_tokens[j1:j2]:
                out.append({"word": t, "start": out[-1]["start"],
                            "end": out[-1]["end"]})
        # tag == "delete": whisper hallucination (breaths, "hhhh") -> dropped
    return out


def cues_from_words(words):
    """Group words into cues that break at CLAUSE boundaries, not pixel limits.

    The old builder appended words until the text needed a third line, then cut
    wherever that happened to land. QA 2026-08-15 found the results on reels 36
    and 37: "...when no" / "one was watching.", "...the body" / "is tired",
    "you learned to read" / "a room". Each card reads as a finished sentence
    that says something the script never said.

    Pushing the trailing word forward afterwards could not fix it — at the width
    limit the next card has no room, so the move was usually declined. The break
    point has to be chosen properly in the first place:

        1. a sentence end is always a break
        2. otherwise the LAST COMMA that still fits
        3. otherwise the last word that can plausibly end a card (not an
           article, conjunction, preposition, auxiliary or bare verb stem)
        4. only then, the width limit
    """
    toks = []
    for w in words:
        t = w["word"].strip()
        if t in ("—", "–", "--"):
            toks.append(("__BREAK__", w["start"], w["end"]))
            continue
        if junk(t):
            continue
        toks.append((t, w["start"], w["end"]))

    WEAK_END = {"a", "an", "the", "and", "or", "but", "so", "if", "when", "that",
                "to", "of", "in", "on", "at", "for", "with", "as", "is", "was",
                "are", "were", "be", "been", "no", "not", "your", "my", "his",
                "her", "their", "its", "this", "these", "those", "you", "it",
                "than", "then", "into", "from", "by", "who", "what", "how",
                # subordinators — a card ending "...to read a face before" is
                # as broken as one ending "the", and without these the walk-back
                # stops on them (reel 37).
                "before", "after", "because", "while", "until", "since",
                "although", "though", "unless", "whether", "where", "whose",
                "which", "will", "would", "can", "could", "should", "must",
                "has", "have", "had", "do", "does", "did"}

    def ok_end(word):
        return re.sub(r"[^\w']", "", word).lower() not in WEAK_END

    cues, i = [], 0
    while i < len(toks):
        if toks[i][0] == "__BREAK__":
            i += 1
            continue
        j, best = i, None
        while j < len(toks) and toks[j][0] != "__BREAK__":
            text = " ".join(t for t, _, _ in toks[i:j + 1])
            if len(wrap_px(text)) > 2:
                break
            if re.search(r"[.!?:]$", toks[j][0]):        # rule 1
                best = j
                break
            if toks[j][0].endswith(","):                 # rule 2
                best = j
            elif best is None or not toks[j][0].endswith(","):
                if ok_end(toks[j][0]):                   # rule 3
                    best = best if (best is not None and
                                    toks[best][0].endswith(",")) else j
            j += 1
        if best is None:                                 # rule 4
            best = max(i, j - 1)

        # LOOK AHEAD before committing. A break is mid-phrase whenever the NEXT
        # word opens a phrase — a determiner, preposition or auxiliary. That is
        # what left "...whose emotions ruled" / "the house", "learned to read" /
        # "a face" and "...when the body" / "is tired" on screen (QA, reels
        # 36/37): the card ends on a verb and its object lands on the next card,
        # so the first card reads as a complete, wrong sentence.
        # Walk back to the previous comma, or failing that one word, as long as
        # the cue keeps at least three words.
        OPENERS = {"a", "an", "the", "his", "her", "its", "their", "this",
                   "that", "these", "those", "my", "your", "our", "to", "of",
                   "in", "on", "at", "for", "with", "from", "by", "into",
                   "is", "was", "are", "were", "be", "been", "will", "would",
                   "can", "could", "should", "has", "have", "had", "and",
                   # relative pronouns open a clause too, so a break just before
                   # one splits the noun from the clause describing it
                   # ("...a mother whose emotions" / "ruled the house"), and
                   # "than" always belongs with the comparison before it.
                   "who", "whose", "which", "than",
                   # subject pronouns. "it" MUST be here: it was in the twin set
                   # inside merge_orphans but not in this one, so the walk-back
                   # never fired on "...the way you remember" / "it.", and the
                   # stranded one-word "it." was then force-merged onto the head
                   # of the NEXT card ("it. And yet this is...") — the exact
                   # blocker QA raised on reel 35. Two sets that must agree are
                   # a set that will disagree; they are cross-referenced here.
                   "you", "they", "we", "he", "she", "it", "there"}
    # NOT "when"/"where": they open a subordinate clause that reads fine as its
    # own card, and treating them as openers pushed "Luck does not choose
    # patience" back to "Luck does not choose" — worse than the break it
    # replaced. Measured on reel 36, not assumed.
        # Walk back until the break is good on BOTH sides: the word we stop on
        # can end a card, and the word after it does not open a phrase. Stepping
        # back only on the look-ahead test is not enough — on reel 37 it stopped
        # on "to" ("...before you learned to"), which the push pass in
        # merge_orphans then moved forward, landing straight back on the
        # boundary this was meant to prevent.
        def bad_break(k):
            if re.search(r"[,.!?;:]$", toks[k][0]):     # punctuation ends it
                return False
            if not ok_end(toks[k][0]):
                return True
            nxt = k + 1
            return (nxt < len(toks)
                    and re.sub(r"[^\w']", "", toks[nxt][0]).lower() in OPENERS)

        while best - i >= 3 and bad_break(best):
            commas = [k for k in range(i, best)
                      if toks[k][0].endswith(",")]
            best = commas[-1] if commas else best - 1
        cues.append((toks[i][1], toks[best][2],
                     " ".join(t for t, _, _ in toks[i:best + 1])))
        i = best + 1
    return merge_orphans(cues)


def _legacy_cues(words):
    cues, cur, start = [], "", None
    for w in words:
        t = w["word"].strip()
        # AN EM DASH IS A HARD CUE BOUNDARY, and the dash itself is never drawn.
        # ⚠️ THIS MUST COME BEFORE junk(). A dash has no word characters, so
        # junk() classifies it as a Whisper artifact and `continue`s past it —
        # which is why the first two attempts at this fix did nothing and
        # "your voice that is a quiet miracle" ran on for 4.6s (QA, reel 34).
        if t in ("—", "–", "--"):
            if cur:
                cues.append((start, w["start"], cur))
            cur, start = "", None
            continue
        if junk(t):
            continue
        if start is None:
            start = w["start"]
        cand = (cur + " " + t).strip()
        if len(wrap_px(cand)) > 2 or (cur and re.search(r"[.!?:]$", cur)):
            cues.append((start, w["start"], cur))
            cur, start = t, w["start"]
        else:
            cur = cand
        end = w["end"]
    if cur:
        cues.append((start, end, cur))
    return merge_orphans(cues)


def merge_orphans(cues):
    """Fold a one-or-two-word card back into its neighbour.

    The splitter closes a cue at the measured 2-line limit without looking for a
    clause boundary, which strands fragments — QA 2026-08-15 found `watching.`,
    `yourself.` and `old patterns.` each alone in a full-width white pill. Merge
    backwards when the result still fits on two lines, otherwise forwards.
    """
    # A trailing fragment has nowhere to go forwards, so it MUST merge back even
    # if the result needs a third line — the wrapper will trim, and a slightly
    # tall card beats "part." alone in a pill for 1.5s (QA, reel 34).
    out = []
    for i, (a, b, t) in enumerate(cues):
        if out and len(t.split()) <= 2:
            pa, pb, pt = out[-1]
            last = (i == len(cues) - 1)
            if last or len(wrap_px(f"{pt} {t}")) <= 2:
                out[-1] = (pa, b, f"{pt} {t}")
                continue
        out.append((a, b, t))
    merged = []
    for i, (a, b, t) in enumerate(out):
        if len(t.split()) <= 2 and i + 1 < len(out):
            na, nb, nt = out[i + 1]
            if len(wrap_px(f"{t} {nt}")) <= 2:
                out[i + 1] = (a, nb, f"{t} {nt}")
                continue
        merged.append((a, b, t))

    # REBALANCE what could not be merged. "part." stayed stranded because
    # joining it either way overflowed two lines — merging is not always
    # available, but moving a word across the boundary always is. Pull words
    # back from the previous cue until the fragment is a readable phrase.
    # (Merging would have had to drop text to fit; rebalancing never does.)
    for i in range(1, len(merged)):
        pa, pb, pt = merged[i - 1]
        a, b, t = merged[i]
        while len(t.split()) <= 2 and len(pt.split()) >= 4:
            words_ = pt.split()
            cand_prev, cand_cur = " ".join(words_[:-1]), f"{words_[-1]} {t}"
            if len(wrap_px(cand_cur)) > 2:
                break
            pt, t = cand_prev, cand_cur
        merged[i - 1] = (pa, pb, pt)
        merged[i] = (a, b, t)

    # NEVER END A CARD ON A WEAK WORD. The splitter breaks at the pixel limit,
    # which lands mid-clause and leaves cards like "...light up your phone, that"
    # followed by "is not ordinary." (QA, reel 34). A viewer reads the card as a
    # sentence, so the last word should be able to end one. Push a trailing
    # conjunction/article/pronoun onto the next card when it fits.
    WEAK = {"that", "and", "but", "or", "the", "a", "an", "to", "of", "in",
            "is", "was", "if", "when", "your", "my", "their", "his", "her",
            "for", "with", "as", "so", "it", "this", "these", "not",
            # auxiliaries — "...so the house would" / "stay calm." reads as a
            # finished sentence and is not one (QA, reel 36).
            "will", "would", "can", "could", "should", "must", "may",
            "are", "were", "be", "been", "has", "have", "had",
            "do", "does", "did", "who", "what", "how", "both", "very", "too", "than", "then",
            "from", "by", "into", "on", "at", "its", "those", "no"}

    # A break is ALSO mid-phrase when the NEXT card opens a phrase — the card
    # ends on a verb and its object lands on the following card ("...you
    # learned" / "to read a room", "Naming it loosens" / "it."). The last word
    # is a perfectly good English word, so WEAK alone never catches it; the
    # signal is on the other side of the boundary. Never push across a sentence
    # end — "It was not luck." / "It was you," is a correct break even though
    # the next card starts with a pronoun.
    OPENERS = {"a", "an", "the", "to", "of", "in", "on", "at", "for", "with",
               "from", "by", "into", "is", "was", "are", "were", "be", "been",
               "it", "its", "his", "her", "their", "this", "that", "these",
               "those", "my", "your", "our", "and"}

    def midphrase(last, nxt):
        # PUNCTUATION WINS. A word carrying a comma or a full stop already IS a
        # clause boundary, so the card ends correctly no matter what follows.
        # Without this guard the first attempt pushed "house," and "tone,"
        # forward and stranded "ruled the" and "A wrong" — strictly worse than
        # the defect it was fixing.
        if re.search(r"[,.!?;:]$", last):
            return False
        return nxt.split()[0].strip(",.;:").lower() in OPENERS

    for i in range(len(merged) - 1):
        a, b, t = merged[i]
        na, nb, nt = merged[i + 1]
        words_ = t.split()
        while (len(words_) > 3
               and not re.search(r"[,.!?;:]$", words_[-1])
               and (words_[-1].strip(",.;:").lower() in WEAK
                    or midphrase(words_[-1], nt))
               and len(wrap_px(f"{words_[-1]} {nt}")) <= 2):
            nt = f"{words_[-1]} {nt}"
            words_ = words_[:-1]
        merged[i] = (a, b, " ".join(words_))
        merged[i + 1] = (na, nb, nt)
    return merged


def silences(src, thresh="-45dB", dur=0.5):
    """[(start, end)] of silent windows in the take, via ffmpeg silencedetect."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src,
                        "-af", f"silencedetect=noise={thresh}:d={dur}",
                        "-f", "null", "-"], capture_output=True, text=True)
    out, start = [], None
    for m in re.finditer(r"silence_(start|end): ([\d.]+)", r.stderr):
        if m.group(1) == "start":
            start = float(m.group(2))
        elif start is not None:
            out.append((start, float(m.group(2))))
            start = None
    return out


def snap_out_of_silence(cues, src):
    """Push a cue that opens inside a silent window forward to where the voice
    actually starts.

    Whisper hands a word's start to the breath before it, so a card can appear
    a second ahead of its own audio — the deep-QA gate caught reel 25's closing
    line drawn 1.26s early, sitting over pure silence. Only the START moves; the
    card still runs until the next cue, so nothing is lost, and a cue is never
    pushed past its own end.
    """
    sil = silences(src)
    fixed = []
    for a, b, t in cues:
        for s0, s1 in sil:
            # 0.35s of slack in front: whisper hands the word start to the
            # breath, so the cue opens just BEFORE the silence, not inside it.
            if s0 - 0.35 <= a < s1 and s1 < b:
                a = s1
                break
        fixed.append((a, b, t))
    return fixed


def two_lines(text):
    return "\\N".join(wrap_px(text)[:2])


def assemble(rid):
    src = os.path.join(ART, f"avatar_{rid}.mp4")
    import mlx_whisper
    r = mlx_whisper.transcribe(src, path_or_hf_repo=MODEL,
                               word_timestamps=True, language="en")
    words = [w for seg in r["segments"] for w in seg.get("words", [])]
    sj = json.load(open(os.path.join(ROOT, "scripts", "reels.json")))
    reel = next(it for it in sj if str(it["id"]) == rid)
    script = " ".join(l for b in reel["beats"] for l in b["lines"])
    words = align_to_script(words, script)
    cues = snap_out_of_silence(cues_from_words(words), src)
    with open(os.path.join(ART, f"cues_{rid}.txt"), "w") as f:
        for a, b, t in cues:
            f.write(f"{a:7.2f} {t}\n")
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", src],
        capture_output=True, text=True).stdout.strip())

    from PIL import Image, ImageDraw
    W, H = 1080, 1920
    font = _FONT
    fdir = os.path.join(ART, f".cards_{rid}")
    os.makedirs(fdir, exist_ok=True)

    def draw(text, path):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if text:
            lines = two_lines(text).split("\\N")
            f = font
            wmax = max(d.textlength(l, font=f) for l in lines)
            lh = FONT_SIZE + 14
            bh = len(lines) * lh + 36
            # CAPTION BAND POSITION IS LOAD-BEARING, not aesthetic.
            # Measured 2026-08-15 across two different burned renders (reel 28
            # take 1 on anchor a23b, reel 30 on a26c — different anchors, poses
            # and settings): kling burns its fake subtitles into the SAME
            # horizontal band every time, y 961-1036 of a 720x1264 clip, i.e.
            # 0.76-0.82 of frame height = y 1459-1574 at 1080x1920. The old
            # card centred at 1470 stopped just short of it, which is exactly
            # why the gibberish showed as a "second line" under our caption.
            # The card now extends to BURN_BOTTOM so it covers that band
            # whatever the line count. This does not stop the burn; it makes it
            # invisible. Keep the render-time subtitle gate regardless.
            # CARD COLOURS — switched to a WHITE pill 2026-08-15 (operator: it
            # contrasts better against the maroon robe than black did). This
            # reverses the 2026-08-08 choice of a black box; the reasoning then
            # was contrast against a DARK interior, and every anchor is now a
            # bright daylight exterior, so the ground changed under it.
            # ⚠️ FILL MUST STAY FULLY OPAQUE (alpha 255) whatever the colour —
            # it is what hides kling's burned-in text. At alpha 230 the glyphs
            # showed straight through.
            CARD_FILL = (255, 255, 255, 255)
            TEXT_FILL = (17, 17, 17, 255)
            STROKE_FILL = (255, 255, 255, 255)
            # ⚠️ BURN_TOP RAISED 1460 -> 1300 on 2026-08-15 (reel 32).
            # The band is NOT the constant this file used to claim. Reel 32
            # burned at 0.681-0.819 of frame height, measured over 14 samples,
            # against the 0.76-0.82 seen on reels 28 and 30. The card covered
            # 0.760-0.839, so the rows at 0.681-0.737 — present in EVERY sample
            # — sat above it in plain sight.
            # 1300/1920 = 0.677, just above the highest burn row observed.
            # If a future render burns higher still, RAISE THIS AGAIN rather
            # than shipping it: measure the extent, do not assume the cover.
            # DERIVED FROM THE ARTIFACT, not a literal. finish_reel.py measures
            # THIS render's actual burn box and passes it in; the card is then
            # only as tall as this reel needs.
            #
            # Why: on reel 32 a crude edge detector put the burn top at y861 raw
            # (it was also catching the table's lit edge), so the card was built
            # from 1300 — about 100px taller than the evidence required, and the
            # operator's complaint was that the caption looked bad. The QA pass
            # isolated the real glyphs by temporal-median residual at y940-1010
            # raw = y1422-1527 in the master.
            #
            # A literal cannot be right here anyway: measured burn tops are
            # 0.744 (reel 32), 0.760 and 0.76 (reels 28, 30). It moves.
            # THE PILL IS SIZED BY THE TEXT AND POSITIONED OVER THE BURN.
            #
            # It used to be STRETCHED to the burn's bounds, so a one-line
            # caption sat in a 147px box surrounded by white — "huge empty white
            # space looks horrible" (operator, 2026-08-15). Wrong way round: an
            # ordinary snug pill is already ~90px for one row and ~150px for
            # two, and kling's burn is a single line only ~15px tall. Centring a
            # normal pill on it covers it without any inflation at all.
            #
            # Only if the burn genuinely would not fit inside a snug pill do we
            # grow it, and then by the minimum needed.
            # ASYMMETRIC PADDING — more headroom ABOVE than below.
            # QA 2026-08-15 measured only 14px between the one-line pill's top
            # edge and the burn's top edge, against 73px below. The cover was
            # airtight on that reel but had almost no margin on the tight side,
            # and any shorter pill or slightly higher burn would expose it.
            PADY = 18
            PADY_TOP = 46
            BURN_TOP = int(os.environ.get("BURN_TOP", 0))
            BURN_BOTTOM = int(os.environ.get("BURN_BOTTOM", 0))
            centre = ((BURN_TOP + BURN_BOTTOM) // 2) if BURN_BOTTOM else 1460
            card_top = centre - bh // 2 - PADY_TOP
            card_bot = centre + bh // 2 + PADY
            if BURN_BOTTOM:                       # grow ONLY if it truly sticks out
                card_top = min(card_top, BURN_TOP - 6)
                card_bot = max(card_bot, BURN_BOTTOM + 6)
            # WIDTH: hug the text unless we are covering a burn.
            #
            # This used to be max(wmax + 56, 940) unconditionally, so a short
            # caption like "is not ordinary." sat in a 940px pill with a slab of
            # white either side — the operator's note "can we reduce the white
            # space pill". The 940 floor exists ONLY because kling's burn runs
            # the full width of the frame and a narrower card let it peek past
            # the right edge (reel 30). On a clean render there is nothing to
            # peek, so the pill should fit the words like any normal caption.
            # WIDTH: hug the text, widening only as far as THIS render's burn
            # actually reaches. 940 was a guess that assumed a full-width burn;
            # measured, the glyphs span 387-514px, so the rest was empty white.
            burn_w = int(os.environ.get("BURN_W", 0))
            box_w = min(max(wmax + 56, burn_w), SAFE_W)
            d.rounded_rectangle([(W - box_w) / 2, card_top,
                                 (W + box_w) / 2, card_bot],
                                18, fill=CARD_FILL)
            # Text is centred in the CARD, not pinned to its top — otherwise a
            # tall cover card leaves the caption stranded against its top edge
            # with a slab of empty white beneath it.
            ty = (card_top + card_bot) / 2 - bh / 2
            for i, l in enumerate(lines):
                lw = d.textlength(l, font=f)
                d.text(((W - lw) / 2, ty + i * lh), l, font=f,
                       fill=TEXT_FILL,
                       stroke_width=2, stroke_fill=STROKE_FILL)
        img.save(path)

    blank = os.path.join(fdir, "blank.png")
    draw("", blank)
    entries, cursor = [], 0.0
    for i, (a, b, t) in enumerate(cues):
        if a - cursor > 0.02:
            entries.append((blank, a - cursor))
        nxt = cues[i + 1][0] if i + 1 < len(cues) else total
        p = os.path.join(fdir, f"c{i:03d}.png")
        draw(t, p)
        entries.append((p, max(0.10, nxt - a)))
        cursor = nxt
    if total - cursor > 0.02:
        entries.append((blank, total - cursor))
    lst = os.path.join(fdir, "cards.txt")
    with open(lst, "w") as f:
        for p, d_ in entries:
            f.write(f"file '{p}'\nduration {d_:.3f}\n")
        f.write(f"file '{entries[-1][0]}'\n")

    out = os.path.join(REELS, f"reel_{rid}_dry.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
        "-f", "concat", "-safe", "0", "-i", lst,
        "-filter_complex",
        "[0:v]scale=-2:1920,crop=1080:1920,unsharp=5:5:0.6:5:5:0.0,"
        "noise=alls=6:allf=t[bg];[bg][1:v]overlay=0:0:format=auto[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "22", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", out], check=True)
    print(out, f"({len(cues)} cues)")


if __name__ == "__main__":
    os.makedirs(REELS, exist_ok=True)
    for rid in sys.argv[1:]:
        assemble(rid)
