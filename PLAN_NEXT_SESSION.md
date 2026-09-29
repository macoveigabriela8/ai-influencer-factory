# PLAN — fresh session, written 2026-08-08 (read top to bottom, execute in order)

## ✅ EXECUTED 2026-08-08 (same day, later session)
§1 kit built (output/markets/PT/profile + Desktop + Drive), Gmail draft awaits
send OK. §2 Drive push live (scripts/pt_drive_push.py, cron 06:12; Drive is
mounted locally — no MCP needed). §3 verified impossible (no follow trigger,
Blotato + Meta docs) — dropped per plan. §4 root cause found: comments on old
account record 62904 never reach 63585's automations; scripts/dm_backfill.py
sends the missed DMs as private replies (7 misses healed), comment_sweep.py
fixed (was watching ONLY 62904), dashboard now has a DM-health section, cron
06:00 dashboard + hourly backfill. §5 motion prompt block added to CLAUDE.md.
§6/§7 are standing rules, nothing to execute. §8 still blocked on user.

User approved this plan verbally; per-item approvals still apply where marked.
Context: PT catalogue DONE — 10 masters certified in output/markets/PT/reels/,
user posts them manually, NO re-renders of PT1-PT10 ever.

## 0. Standing corrections already persisted (do not redo, just obey)
- CLAUDE.md: anchor rules (no smiling anchors, no standing anchors for talking
  takes), Gate 0 sentence-level TTS QC, upload-cache mtime fix in kie.py,
  independent deep-QA gate for ALL monks, caption gate, fixed font size.
- PT accounts (user created, new phone): IG mestrekaion · TikTok @mestre.kaion
  · YouTube channel UC8LvVqplv_XMhHsfhANyXbw. Email: masterkaionpt@gmail.com.

## 1. PT profile asset kit (build + deliver)
Build in output/markets/PT/profile/: profile photo (pt_face_v3 crop, 320x320
and 1000x1000), 3 highlight covers in the EN style (Comece Aqui / Sabedoria /
Rituais), YouTube banner 2560x1440 (safe area 1546x423), YouTube avatar
800x800, bio text PT (mirror EN bio: "40 anos em silêncio. Agora eu ensino." /
"Pequenas práticas para uma mente que não para." — no product line until the
PT book exists), TikTok bio (shorter), suggested handles/name fields
("Mestre Kaion | Sabedoria e Cura").
Then: (a) copy to a Finder folder ~/Desktop/MESTRE_KAION_ASSETS/ (or iCloud
MESTRE_PT/profile/), (b) EMAIL everything to masterkaionpt@gmail.com — Gmail
MCP tools exist in this workspace (create_draft, but SENDING needs the user's
per-action OK — draft it, show it, ask to send).

## 2. Android delivery of PT videos
Goal: each day's PT video + caption txt lands on the user's Android phone
automatically. Realistic options to implement/verify:
- Simplest: Google Drive folder "MESTRE KAION PT" synced by the Drive app on
  the phone. A Drive MCP server is connected in this workspace (search_files,
  create_file etc.) — verify write scope; if writable, push video + caption
  there daily via cron script (KAION-CRON pattern).
- "Photos + txt on desktop" as user asked is not directly scriptable from a
  Mac to Android; Drive (or Google Photos app auto-backup of the Drive folder)
  is the honest equivalent. Explain trade-off, get user OK on the Drive route.
- User mentioned giving "Google CLI connection" access — ask what they meant
  (likely OK to use their Google account via the connected MCP).

## 3. Welcome-DM on follow (ALL monks)
Requested copy: "Welcome, my friend. I am grateful you are here. May the
wisdom from our monastery bring you peace and healing. 🙏" (PT version for
Mestre: translate in Kaion voice, no contractions).
- Check Blotato: v2/dm-automations trigger types — we only know
  comment-received and message-received. VERIFY via API/docs whether a
  "new follower" trigger exists (list existing automations' schema, try
  targetType options, check Blotato docs). If not supported: say so plainly,
  fall back = none (IG official API does not expose follow events to third
  parties easily). Do NOT fake it with unofficial automation.
- If supported: create for EN 63585 now, PT when its account connects;
  register in data/dm_registry.json.

## 4. 6am automation health check (extend kaion-morning-board task)
Extend the existing 06:08 Claude scheduled task (kaion-youtube-pin is separate;
morning board = scripts/daily_dashboard.py) OR add a section to the dashboard
build: every morning pull last 24h comments (Blotato /comments) + DM automation
runs (GET /v2/dm-automations + list_automation_runs/logs endpoints — the MCP
now exposes blotato_list_automation_runs, blotato_list_automation_logs,
blotato_get_automation_analytics), cross-reference: every comment containing a
registered keyword must have a matching automation run. Mismatches → red row
on the HTML board with: problem, fix applied, proof (post-fix run id).
TODAY'S KNOWN BUG to verify first: user says comments came in but automation
did not trigger — reproduce, diagnose (account 63585 connected state? keyword
matching? automation active flag?), fix, and show proof on the board.
Board file: output/dashboard.html (built by scripts/daily_dashboard.py, cron
09:05 — move/add 06:00 run in crontab KAION-CRON).

## 5. Movement-quality research (web) before next batch
Search: prompting best practices for kling ai-avatar / talking-avatar motion
naturalness (avoid sway loops, natural breathing, shoulder motion), 2026
sources. Distill into CLAUDE.md as positive-phrasing prompt lines. Test the
improved motion prompt on ONE 4cr anchor + ONE clip only when the next batch
is already paid for — never a dedicated test render.

## 6. Cost discipline (user complaint: too many regens)
Root causes this session, all now guarded: upload-cache staleness (fixed in
kie.py), whole-file TTS QC too weak (Gate 0 now sentence-level exact match),
audio-seeded burned subtitles (fresh TTS after any burn fail), smiling/standing
anchors (anchor rules). Standing rule: ONE render per script; re-roll ONLY on
a specific diagnosed QC failure with an INPUT CHANGED; every re-roll names the
changed input in the ledger/batch state. kie balance after PT batch: 3,749 cr
(~$18.75) — top-up needed before ES batch (floor was 6,000 for ES; breached
with user awareness finishing PT).

## 7. Speed (user complaint: too slow)
Wall-clock is dominated by kling render time (~10-15 min/80s clip, external)
and QA transcription. Improvements for next batch: submit ALL clips in
parallel (rounds 4-8 of PT2 were sequential by necessity, but batch = parallel
like round-3 was), run deep-QA on each clip AS IT LANDS instead of after the
whole batch, keep whisper-small for pre-flight Gate 0 (turbo only for final
certification), and batch the caption-gate agent over all reels at once.
Token usage: prefer the cues_*.txt text diff before any frame reading; frame
grids at 2s not 1s for pre-checks (1s only for final certification).

## 8. Blocked on user
- Blotato: connect IG mestrekaion (once, never delete/re-add) → then create
  the 8 PT keyword automations (lar, água, clareza, pureza, cuidar, amém,
  aceito, sim) with unique PT practices, no product tail until PT book exists.
- kie top-up before ES monk.
- TikTok PT1 upload → tell us the suggested song (music direction).
- Link-in-bio: PT scripts intentionally have NO product close — there is no
  PT product yet. When the PT book/Gumroad page exists, closes get the product
  line (translate the EN invariant) in NEW scripts only.
