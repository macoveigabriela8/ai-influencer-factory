# FUNNEL TEST — the first honest measurement of demand

**Started 2026-08-12. First checkpoint 2026-08-22. Decision point 2026-08-26.**

## Why this test exists

Every Instagram view before today hit a path that could not be clicked:
links in IG captions and comments are plain text (verified 2026), and the
"link in bio" route is three taps. Measured result: **~40,000 Instagram views
produced 0 page views.** That was never a measurement of demand — it was a
measurement of broken plumbing. As of today two tappable paths exist for the
first time, so the next ten days produce the project's first real data.

⚠️ **Instagram's in-app insights are the authority, not our Apify scrape.**
On 2026-08-14 the scrape said 434 followers and a 31,356 best reel while the app
said **500** and **46,500**. The scrape lags and undercounts; always ask the
operator for the app figures before drawing a conclusion about the gates.

## Baseline at start (2026-08-12)

| metric | value |
|---|---|
| Gumroad page views, lifetime | **11** (5 operator's own laptop, 3 YouTube, 2 Facebook, **0 Instagram**) |
| Gumroad sales, lifetime | **0** |
| IG followers | 342 |
| IG views, last 10 posts | 40,244 (median 843, one outlier 31,356) |
| IG comment rate | ~0.11% (44 audience comments) |
| YouTube EN | 66 subs, 6 videos, median 875 |
| Click-to-page rate | **0.015%** (6 non-operator page views / ~40k views) |

## What changed, and what each path is being tested for

1. **Story link sticker** — posted by hand daily, the only tappable link on
   Instagram besides a DM button. First one posted 2026-08-12 (15s teaser,
   reel 10, sticker attached). Tests: does a one-tap offer convert attention?
2. **Comment keyword -> DM with a button** — every scheduled reel's pinned
   comment now asks for the reel's own keyword instead of printing a dead URL.
   Automations post-scoped, misspellings covered. Tests: does the DM funnel
   carry traffic at all? It never has.

## What to record at each checkpoint

Gumroad has no API key configured here, so the operator reads these from the
Gumroad dashboard:

| date | page views | sales | source split | IG followers | notes |
|---|---|---|---|---|---|
| 2026-08-12 | 11 | 0 | 5 direct / 3 YT / 2 FB / 0 IG | 342 | baseline; first story sticker posted |
| 2026-08-14 | ? | 0 | ? | **500** | operator's in-app figures: 64,100 total IG views, best reel **46,500** and still climbing, 500 followers. 2 stories posted with link stickers. First TikTok post live (reel 7). |
| 2026-08-22 | | | | | 10-day checkpoint |

## How to read the result — decide this BEFORE seeing the numbers

- **Page views rise clearly (>30 non-operator) and >=1 sale** — the funnel works.
  Next move is the $47 anchored bundle to raise revenue per buyer.
- **Page views rise, 0 sales** — traffic is fine, the OFFER is wrong. The $150
  paid-traffic test is then unnecessary; fix packaging and price instead.
- **Page views stay near zero** — the audience does not follow links at any
  volume we can reach organically. THEN the $150 paid test earns its place,
  because it asks a different question: will *intent* traffic buy?

Writing the interpretation down in advance is deliberate. This project has
repeatedly inferred rules after the fact from confounded evidence (see
`output/RCA_BURNED_SUBTITLES.md`), and a pre-registered reading is the cheapest
guard against doing it again.

## Not to be confused with the kill gates

The Sep 7 / Oct 7 / Nov 3 gates measure REACH. This test measures MONEY. They
can disagree: at 0.015% click-through even a 250k-view outlier yields ~37 page
views and 0-1 sales, so the account can pass a reach gate while earning nothing.
