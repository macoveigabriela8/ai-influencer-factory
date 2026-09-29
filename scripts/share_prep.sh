#!/usr/bin/env bash
# Build a SANITISED copy of this project for handing to someone else.
#
#   scripts/share_prep.sh            # dry run: what would be excluded, final size
#   scripts/share_prep.sh --build    # write ../influencer_share/ and verify it is clean
#
# A zip does NOT honour .gitignore. Everything gitignore hides - the live keys
# in .env above all - lands in a zip unless it is excluded here explicitly.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="$SRC/../influencer_share"

EXCLUDE=(
  # --- secrets: never travel -------------------------------------------
  '.env'
  # --- your machine, not the project -----------------------------------
  '__pycache__/' '.git/' '.DS_Store' '*.log' 'output/health_history.json'
  'data/story_push_state.json' 'data/kie_tasks.json'
  # --- ~17 GB of renders/audio the recipient regenerates themselves ------
  # (anchor stills .png stay: they are the character and cost 4cr each)
  '*.mp4' '*.mov' '*.mp3' '*.wav' '*.m4a' '*.aac' '*.zip'
  'output/reels/.work/'
  # --- competitor media: downloaded, not ours to redistribute -----------
  'data/videos/' 'data/competitors/audio/' 'data/competitors/*.mp4'
)
ARGS=(); for e in "${EXCLUDE[@]}"; do ARGS+=(--exclude="$e"); done

if [[ "${1:-}" != "--build" ]]; then
  echo "DRY RUN - size of what WOULD be copied:"
  rsync -a -n --stats "${ARGS[@]}" "$SRC/" "$DST/" | grep -E "Total transferred|Number of regular files"
  echo; echo "re-run with --build to write $DST"; exit 0
fi

rm -rf "$DST"; rsync -a "${ARGS[@]}" "$SRC/" "$DST/"

# ---- scrub personal identifiers from the copy (never from the source) ---
# the email to scrub is read from .env, never written into this script
EMAIL="$(grep -E '^DRIVE_ACCOUNT=' "$SRC/.env" 2>/dev/null | cut -d= -f2-)"
[ -n "$EMAIL" ] || EMAIL='__none__'
grep -rIl "$EMAIL" "$DST" 2>/dev/null | while read -r f; do
  sed -i '' "s/$EMAIL/YOUR_EMAIL@example.com/g" "$f"
done

# ---- VERIFY: the copy must contain no key and no email -------------------
echo "verifying $DST ..."
bad=0
if [ -e "$DST/.env" ]; then echo "  !! .env present"; bad=1; fi
if grep -rIqE "(apify_api_|sk_[a-f0-9]{30}|xi-api|ghp_)[A-Za-z0-9_-]{16,}" "$DST" 2>/dev/null; then
  echo "  !! api-key shaped string found:"; grep -rIoE "(apify_api_|ghp_)[A-Za-z0-9_-]{16,}" "$DST" | head -3; bad=1; fi
if grep -rIq "$EMAIL" "$DST" 2>/dev/null; then echo "  !! personal email still present"; bad=1; fi
[ -e "$DST/.env.example" ] || { echo "  !! .env.example missing - recipient has no key template"; bad=1; }
[ -e "$DST/.claude/skills/recreate-influencer/SKILL.md" ] || { echo "  !! skill missing"; bad=1; }
if [ $bad = 0 ]; then
  echo "  CLEAN.  $(du -sh "$DST" | cut -f1)  ->  $DST"
  echo "  zip it:  cd $(dirname "$DST") && zip -rq influencer_share.zip influencer_share"
else
  echo "  NOT CLEAN - do not share."; exit 1
fi
