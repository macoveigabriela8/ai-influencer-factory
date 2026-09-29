#!/usr/bin/env python3
"""Build the two bonus PDFs that turn the book into a bundle.

    python3 scripts/build_bonuses.py

Bonus 1 — THE PRACTICE CARDS. One page per practice, drawn from the DM bodies
already written in data/dm_registry.json. Those were written one at a time as
each reel shipped, in Kaion's voice, each a single concrete physical act. They
have never existed as an artifact the buyer can hold, which is the only thing
missing to make them a bonus.

Bonus 2 — THE 30-DAY TRACKER. A printable one-pager: thirty boxes, the week
titles from the manuscript, and a line for the one sentence that matters.

Design deliberately copies output/book/book.html — same 6x9 page, same Georgia,
same paper and ink colours — so the bonuses read as part of the book rather than
as bolted-on lead magnets. Competitor evidence (monkchen.com, fetched
2026-08-07): a $14.95 PDF sells with THREE bonuses, an anchor price and a
guarantee. We had the better product and none of the packaging.

Chrome headless does the HTML->PDF step; weasyprint is not installed here.
"""

import html
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "output", "book")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: 6in 9in; margin: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: #2b2620;
       background: #faf6ee; margin: 0; }
.page { width: 6in; height: 9in; padding: 0.85in 0.8in; box-sizing: border-box;
        page-break-after: always; position: relative; background: #faf6ee;
        overflow: hidden; }
.cover { padding: 1.6in 0.9in; background: #12100d; color: #efe7d6; }
.cover h1 { font-size: 34px; line-height: 1.15; margin: 0 0 0.25in 0; }
.cover .sub { font-size: 12.5px; letter-spacing: 0.18em; text-transform: uppercase;
              color: #c9b286; }
.cover .rule { width: 1in; height: 1px; background: #8a6d3f; margin: 0.3in 0; }
h2.kicker { font-size: 13px; letter-spacing: 0.28em; text-transform: uppercase;
            color: #8a6d3f; text-align: center; margin: 0 0 0.12in 0; }
.num { font-size: 58px; color: #d9c9a6; text-align: center; line-height: 1;
       margin: 0.05in 0 0.1in 0; }
h3 { font-size: 19px; text-align: center; margin: 0 0 0.28in 0; font-weight: normal; }
p { font-size: 13.5px; line-height: 1.62; margin: 0 0 0.16in 0; }
p.first::first-letter { font-size: 30px; float: left; line-height: 0.9;
                        padding-right: 6px; color: #8a6d3f; }
.label { font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
         color: #8a6d3f; margin-bottom: 0.08in; }
.rule { border-top: 1px solid #e2d6bd; margin: 0.26in 0; }
.folio { position: absolute; bottom: 0.38in; left: 0; right: 0; text-align: center;
         font-size: 10px; color: #a4906a; letter-spacing: 0.2em; }
table.grid { border-collapse: collapse; width: 100%; margin-top: 0.12in; }
table.grid td { border: 1px solid #ddd0b4; height: 0.52in; width: 20%;
                vertical-align: top; padding: 4px 6px; font-size: 10px;
                color: #a4906a; }
.weekline { font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase;
            color: #8a6d3f; margin: 0.2in 0 0.04in 0; }
.line { border-bottom: 1px solid #e2d6bd; height: 0.28in; }
.note { font-style: italic; color: #6f6353; font-size: 12px; }
"""


def page(inner, folio=""):
    f = f'<div class="folio">{html.escape(folio)}</div>' if folio else ""
    return f'<div class="page">{inner}{f}</div>'


def render(title, pages, out_html, out_pdf):
    doc = (f"<html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
           f"<style>{CSS}</style></head><body>{''.join(pages)}</body></html>")
    open(out_html, "w").write(doc)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out_pdf}", "file://" + out_html],
                   check=True, capture_output=True, timeout=180)
    print(f"  {os.path.relpath(out_pdf, ROOT)}  ({len(pages)} pages)")


def clean_practice(t):
    """Strip the DM's funnel tail. The practice is the part that is a practice."""
    for cut in ["The full thirty days are in my book below",
                "Everything else I know is inside",
                "The full thirty days are inside"]:
        if cut in t:
            t = t.split(cut)[0]
    return t.replace("🙏", "").strip()


def practice_cards():
    reg = json.load(open(os.path.join(ROOT, "data", "dm_registry.json")))
    seen, cards = set(), []
    for a in reg["automations"]:
        body = clean_practice(a.get("dmMessage") or "")
        # Skip the follow-up/gift automations: they sell, they do not teach.
        if not body or len(body) < 80 or "here is the gift" in body.lower():
            continue
        key = body[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        kws = a.get("keywords") or []
        cards.append((kws[0] if kws else "", body))

    pages = [page(
        '<div class="cover">'
        '<div class="sub">A companion to</div>'
        '<h1>The Practice Cards</h1>'
        '<div class="rule"></div>'
        '<div class="sub">The Quiet Between Thoughts<br>Master Kaion</div>'
        '</div>')]
    pages.append(page(
        '<h2 class="kicker">How to use these</h2>'
        '<h3>One page. One act. One night.</h3>'
        '<p class="first">These are the practices I have given away one at a time, '
        'to the people who asked for them. Each one is a single act, done with the '
        'body, at a stated time. Not an idea to agree with. An act.</p>'
        '<p>Do not read them all tonight. Open one page, do what it says, and close '
        'the book. A practice you performed once is worth more than thirty you '
        'understood.</p>'
        '<p class="note">The thirty days in the main book build on these. These stand '
        'alone if you have only tonight.</p>', "THE PRACTICE CARDS"))

    for i, (kw, body) in enumerate(cards, 1):
        # First sentence as its own drop-cap paragraph, the rest beneath it.
        bits = body.split(". ")
        chunks = [bits[0] + ("." if not bits[0].endswith(".") else ""),
                  ". ".join(bits[1:])]
        paras = ""
        for j, chunk in enumerate(c for c in chunks if c.strip()):
            cls = ' class="first"' if j == 0 else ""
            paras += "<p%s>%s</p>" % (cls, html.escape(chunk.strip()))
        kicker = f'<h2 class="kicker">Practice {i:02d}</h2>'
        title = f'<h3>{html.escape(kw.title())}</h3>' if kw else ""
        pages.append(page(kicker + title + '<div class="rule"></div>' + paras,
                          "THE PRACTICE CARDS"))
    render("The Practice Cards", pages,
           os.path.join(BOOK, "bonus_practice_cards.html"),
           os.path.join(BOOK, "TQBT_bonus_practice_cards.pdf"))
    return len(cards)


def tracker():
    m = json.load(open(os.path.join(BOOK, "manuscript.json")))
    weeks = m.get("weeks") or []
    days = m.get("days") or []

    def week_title(i):
        """manuscript.json uses short keys: n = "Week One", t = "The Morning"."""
        if i >= len(weeks):
            return ""
        w = weeks[i]
        if isinstance(w, dict):
            return " · ".join(x for x in (w.get("n"), w.get("t")) if x)
        return str(w)

    def fit(t, n=26):
        """Truncate on a word boundary. Cutting mid-word reads as a bug."""
        t = (t or "").strip()
        if len(t) <= n:
            return t
        cut = t[:n].rsplit(" ", 1)[0]
        return cut + "\u2026"

    cells = []
    for d in range(1, 31):
        label = ""
        if d - 1 < len(days):
            dd = days[d - 1]
            if isinstance(dd, dict):
                label = fit(dd.get("title"))
        cells.append(f"<td><b style='font-size:13px;color:#2b2620'>{d}</b>"
                     f"<div>{html.escape(label)}</div></td>")
    rows = ""
    for r in range(6):
        rows += "<tr>" + "".join(cells[r * 5:(r + 1) * 5]) + "</tr>"

    wk = ('<div class="weekline">' +
          " &nbsp;·&nbsp; ".join(html.escape(week_title(i))
                                for i in range(min(4, len(weeks)))) +
          "</div>")

    pages = [page(
        '<div class="cover">'
        '<div class="sub">A companion to</div>'
        '<h1>The Thirty Day Tracker</h1>'
        '<div class="rule"></div>'
        '<div class="sub">The Quiet Between Thoughts<br>Master Kaion</div>'
        '</div>'),
        page('<h2 class="kicker">Print this page</h2>'
             '<h3>Thirty boxes. Mark the day you did it.</h3>'
             '<p class="first">Put this where you will see it before you sleep. Mark '
             'the box only when the act is done, not when you meant to do it. A '
             'missed day is not a failure, it is a day. Begin again on the next box.</p>'
             + wk +
             f'<table class="grid">{rows}</table>'
             '<div class="weekline">The one sentence I want to remember</div>'
             '<div class="line"></div><div class="line"></div>',
             "THE THIRTY DAY TRACKER")]
    render("The Thirty Day Tracker", pages,
           os.path.join(BOOK, "bonus_30_day_tracker.html"),
           os.path.join(BOOK, "TQBT_bonus_30_day_tracker.pdf"))


if __name__ == "__main__":
    n = practice_cards()
    tracker()
    print(f"\n{n} practices formatted. Both bonuses in output/book/.")
