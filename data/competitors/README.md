# Where every scrape lives — read this before scraping anything

Built 2026-08-15. Supersedes the loose `*.json` dumps from 3–14 August.

## The live corpus (use this)

| path | what | size |
|---|---|---|
| `corpus/<shortcode>.json` | metadata + **full transcript** + vein, one file per post | 2.6 MB |
| `audio/<shortcode>.m4a` | 64 kbps audio — re-transcribe forever | 732 MB |
| `videos/<shortcode>.mp4` | full video, **recreation candidates only** (frame-gridding the source is mandatory before scripting) | 281 MB |
| `CORPUS.md` | the index a fresh session reads — ranked, with a `used` column cross-referenced against the production ledger | |

**669 posts · 598 transcribed · $1.81 of Apify.** Rebuild the index any time:
`python3 scripts/build_corpus.py --index`.

The SessionStart hook announces this corpus, so a fresh session finds it without
being told.

## The legacy dumps (metadata only — media is GONE)

`data/monkcheen_full.json`, `monkcheen_raw.json`, `monkcheen_posts.json`,
`competitors/yangmunus_posts.json`, `search_raw.json`, `clones_multilang.json`,
`tiktok_monks.json`, `profiles.json`, `calugarul_wang.json`,
`maestrul_tenzin.json`, `hook_sweep_raw.json`, `lang_sweep_raw.json`.

Keep them: they hold engagement history, TikTok accounts and multi-language
sweeps the new corpus does not cover. But **every `videoUrl` in them is a signed
CDN link and all now return 403** — verified 2026-08-15. That is why 209
monkcheen posts sat untranscribed for weeks while we "had" the data.

## The rule that follows from that

🛑 **A scrape is not saved until its MEDIA is on disk.** Storing the JSON stores
a pointer that expires. `build_corpus.py` pulls the audio during the run, in the
same loop, for exactly this reason. Never write a scraper that saves URLs and
downloads later.

## Do not re-scrape

The corpus covers both source accounts in full. Re-scraping costs money and
gains nothing unless you are adding a NEW account or refreshing play counts.
To add an account: append it to `ACCOUNTS` in `scripts/build_corpus.py` and run
`--scrape`; existing posts are updated in place and transcripts are preserved.
