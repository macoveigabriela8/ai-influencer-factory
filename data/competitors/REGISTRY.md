# REGISTRY — every known monk/spiritual account + every engine verdict

Injected into every session via the SessionStart hook. Update the moment a new
account is found or an engine is tested. Full detail: `COMPETITORS.md`.

## Accounts (as of 2026-08-08)

| account | platform/lang | followers | top outlier | note |
|---|---|---|---|---|
| @monkcheen | IG en | ? | **4.05M** (glass of water) | THE source. 271 posts scraped, 62 transcripts. We reproduce his catalogue. |
| @yangmunus | IG en | **2.53M** | 1.25M (same glass script) | Model account. Median 159k/post. Runs monkcheen's scripts. YT: @Yangmunv2. Product: 30-Day Monk's Mind Reset |
| @mingsanhealing | TT en | 397k | **2.2M** | Salt/remedy rituals. Sells Beravia beetroot (white-label Shopify) |
| @monk.chen1 | TT en | ? | ? | monkcheen's own TikTok, not yet scraped |
| @yangzhion | TT en(+es tags) | 94k | 454k | Younger clone; prayer video = 3.9% c-rate record |
| @calugarul.wang | TT ro | 71k | 105k | RO proof #1. Mono-topic digestive journal via stan.store |
| @maestrul.tenzin1 | TT ro | 13k | **745k in 10 videos** | RO proof #2. "Pergament" funnel |
| @esenciabudista | TT es | 46k | 579k | ES demand proof — Buddhist stories, NO avatar, no real funnel |
| @auroramiagnosis | TT es | 10k | **1.3M** | ES demand proof #2 |
| @edencarllos | TT pt | 91k | 710k | PT natural-living community funnel |
| @find.your.zen | TT en | 17k | 555k | Zen wisdom, sells best-seller book |
| @shihengyi.online | TT en | 255k | 251k | Real Shaolin monk (authentic, not AI) |
| **@monjechen** | TT **es** | **1.3M** | **4.0M** | "Yan Chen \| Sabiduría sanadora" — monkcheen's Spanish sister/franchise. 423 videos, same hashtag-only captions (#calma #medicinachina). Recent median only ~55k — past its outlier phase |
| **@monge.yang** | TT **pt/es** | 394k | **8.3M** | "O Monge Yang" = yangmunus localized. Sells "Jornada de Cura de 30 dias" + livros. Glass-of-water at 2.9M, house-salt ritual 3.5M |
| @yonchenhealing | TT en→DACH | 31k | 926k | Runs monkcheen scripts verbatim in English; one 253k outlier, rest <3k — proof the script alone isn't enough |
| @ilmonacosilenzioso | TT **it** | 3.4k | 155k | Yang Mun clone in Italian, just starting, book funnel "L'arte di guarire". IT niche nearly open |
| @grandpa.emmanuel | TT de | 92k | 1.9M | Elderly-sage adjacent (not monk) |
| @germangracianojaraba | TT es | 394k | 747k | Morning-prayer hooks ("NUNCA EMPIECES TU DÍA...") |
| @alejandraenergiaslz | TT es | 640k | 4.0M | ES esoteric giant w/ store; runs glass-of-water ritual |
| @secretodebruja | TT es | **7.5M** | 2.7M | ES witchcraft mega-account — ritual demand ceiling proof |
| @alinelaine.ofc | TT es/pt | 1.4M | 2.6M | Esoteric rituals |
| @carlosherranoficiall | TT es | 180k | 4.0M | Ritual outliers |
| @maitre.al.adawiyya01 | TT fr | 151k | 307k | FR spiritual — no monk-avatar clone found in FR |

Sweep verdicts:
- 2026-08-08 hashtag sweep (`lang_sweep_raw.json`): found nothing outside EN/RO — **method was wrong**.
- 2026-08-08 **hook-fingerprint sweep** (`hook_sweep_raw.json` — search TRANSLATED proven hooks, e.g. "vaso de agua junto a tu cama"): **REVERSES the above.** Spanish and Portuguese monk-avatar clones exist AT SCALE (@monjechen 1.3M, @monge.yang 394k) and are run by the same operators as the EN originals. **ES/PT = proven demand but occupied. IT and FR are the near-open niches** (only @ilmonacosilenzioso at 3.4k in IT, nothing in FR). DE has no monk clone; @yonchenhealing serves it in English.
- Lesson (user-taught): discovery = search translated proven hooks, never hashtags.

## What WE have reproduced (ledger is authoritative: output/PRODUCTION_LEDGER.md)

19 reels built (B, 2–21 minus held). Sources used: see ledger `sources used`
line at session start. Cross-proven scripts prioritized (proof on 2+ accounts
beats single-account comment rate).

## Engine verdicts (every model we have actually tested)

| engine | $/s | verdict |
|---|---|---|
| kling/ai-avatar-pro (kie) | $0.0748 measured | **CURRENT.** 44/44 QC pass. Weaknesses: soft image, waxy skin (de-plastic pass fixes), face resets at clip joins, 4/37 clips got burned-in fake subtitles (SUBTITLE GATE catches) |
| kling/ai-avatar-standard (kie) | **$0.0383 measured** (288cr/37.6s) | **WINNER 2026-08-08.** Reel 16 single 37.6s take: transcript verbatim 1.000 incl. link line, subtitle gate clean, face sharp + identity stable. 720x1264 native (vs pro 1080p) — upscaled master looks fine. Single-take = NO clip joins = face-reset defect gone. 49% cheaper than pro |
| Seedance 2.0 (kie) | $0.205 measured | EXCLUDED: re-performs audio (can't mux), strips social CTAs, Japanese language drift, <12s filler floor, ~75% yield |
| OmniHuman 1.5 (fal + kie) | $0.0825–0.12 | EXCLUDED: hand smear whenever hands touch/interlace; 4 prompt strategies failed (see scripts/fal_avatar.py header). fal account locked on exhausted balance |
| Higgsfield unlimited | "free" | EXCLUDED: unlim tier caps at 5s/fast/720p; 5s ref audio → filler at sim 0.10 |
| Wan 2.2 S2V (WaveSpeed) | $0.03–0.06 listed | UNTESTED — needs WaveSpeed account. Cheapest candidate |
| InfiniteTalk (WaveSpeed) | $0.06 listed | UNTESTED — unlimited take length would kill joins entirely |

## Funnels known

- monkchen.com: Shopify PDF $29.99→$14.95, fake scarcity, 3 bonuses
- yangmunus: 30-day e-book (niche convention = 30-day guide)
- mingsanhealing: white-label supplement (Beravia)
- calugarul.wang: stan.store PDF; tenzin: "pergament"
- **OURS (live): masterkaion.gumroad.com/l/quiet — $14.95 PDF / $24.95 +audiobook**
