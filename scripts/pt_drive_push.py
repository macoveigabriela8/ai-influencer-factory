#!/usr/bin/env python3
"""Daily delivery for the PT account's manual posting (plan §2, revised
2026-08-08: user posts everything on IG manually for 2 weeks).

Every morning at 06:12 the Mac pushes to BOTH:
  * Google Drive  "MESTRE KAION PT/videos"  (backup / browsing)
  * Google Photos album "KAION PT" via rclone (the phone's zero-friction path)

Per day: the day's TWO reels + one PLAN CARD image that tells the user, in
Portuguese, exactly what to do: which reel is the morning post, which the
evening post, and which OLDER reel to re-share as the day's story (mix-and-
match rule: a story never re-surfaces that day's own reel).

The daily pairs mirror the YouTube schedule created 2026-08-08 so IG and YT
carry the same two reels on the same day:
  Aug 9: PT2+PT3 · Aug 10: PT4+PT5 · Aug 11: PT6+PT7 · Aug 12: PT8+PT9
  Aug 13: PT10.  (PT1 was posted manually on Aug 8.)

    python3 scripts/pt_drive_push.py          # push today's (idempotent)
    python3 scripts/pt_drive_push.py status
"""
import json
import os
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Your Google Drive folder. Set PT_DRIVE_DIR in .env; the default is the
# path Google Drive for desktop creates on macOS for the account in DRIVE_ACCOUNT.
DRIVE = os.path.expanduser(os.environ.get("PT_DRIVE_DIR") or (
    "~/Library/CloudStorage/GoogleDrive-%s/My Drive/MESTRE KAION PT/videos"
    % os.environ.get("DRIVE_ACCOUNT", "YOUR_GOOGLE_ACCOUNT")))
REELS = os.path.join(ROOT, "output/markets/PT/reels")
STATE = os.path.join(ROOT, "data/pt_drive_state.json")
RCLONE = "/opt/homebrew/bin/rclone"
ALBUM = "gphotos-pt:album/KAION PT"
CAPTION = "#monge #sabedoria #saude #brasil"

TOPICS = {
    "PT1": "A armadilha do conforto", "PT2": "Limpeza da casa nova",
    "PT3": "O copo de água ao lado da cama", "PT4": "A cadeira cheia de roupas",
    "PT5": "Água destampada à noite", "PT6": "Pare de se doar demais",
    "PT7": "Quatro palavras ao acordar", "PT8": "Catorze dias sem açúcar",
    "PT9": "A porta fechada ao dormir", "PT10": "Silêncio em três situações",
}
PAIRS = [["PT2", "PT3"], ["PT4", "PT5"], ["PT6", "PT7"], ["PT8", "PT9"],
         ["PT10"]]
GEORGIA_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"pushed": []}


def plan_card(path, day, pair, story_id):
    im = Image.new("RGB", (1080, 1920), (24, 20, 16))
    d = ImageDraw.Draw(im)
    f_h = ImageFont.truetype(GEORGIA_B, 72)
    f_b = ImageFont.truetype(GEORGIA, 46)
    f_s = ImageFont.truetype(GEORGIA, 36)
    d.text((80, 120), "PLANO DE HOJE", font=f_h, fill=(240, 230, 210))
    d.text((80, 230), day, font=f_b, fill=(170, 160, 150))
    y = 340
    slots = [("MANHÃ — 1º reel", pair[0])]
    if len(pair) > 1:
        slots.append(("FIM DE TARDE — 2º reel", pair[1]))
    for label, rid in slots:
        d.text((80, y), label, font=f_b, fill=(200, 170, 110))
        d.text((80, y + 70), f"{rid}: {TOPICS[rid]}", font=f_b,
               fill=(240, 230, 210))
        y += 210
    d.text((80, y), "STORY", font=f_b, fill=(200, 170, 110))
    d.text((80, y + 70), f"Reabra o reel {story_id} ({TOPICS[story_id]})",
           font=f_b, fill=(240, 230, 210))
    d.text((80, y + 140), "no perfil e compartilhe nos stories.", font=f_b,
           fill=(240, 230, 210))
    y += 300
    for line in ["Legenda dos reels (copiar):", CAPTION, "",
                 "Em cada post: Configurações avançadas,",
                 "ativar o selo de IA (AI info)."]:
        d.text((80, y), line, font=f_s, fill=(170, 160, 150))
        y += 56
    im.save(path)


def main():
    st = load()
    done = [p["id"] for p in st["pushed"]]
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print("pushed:", done)
        return 0
    today = time.strftime("%Y-%m-%d")
    if any(p["date"] == today for p in st["pushed"]):
        print("already pushed today")
        return 0
    pair = next((p for p in PAIRS if p[0] not in done), None)
    if not pair:
        print("queue empty — all PT reels delivered")
        return 0
    story_id = done[-1] if done else "PT1"
    os.makedirs(DRIVE, exist_ok=True)
    card = os.path.join(DRIVE, f"{today}_00_PLANO.png")
    plan_card(card, today, pair, story_id)
    to_photos = [card]
    for rid in pair:
        src = os.path.join(REELS, f"reel_{rid}_dry.mp4")
        if not os.path.exists(src):
            print("missing master:", src)
            return 1
        dst = os.path.join(DRIVE, f"{today}_{rid}.mp4")
        shutil.copy2(src, dst)
        to_photos.append(src)
    open(os.path.join(DRIVE, f"{today}_legenda.txt"), "w").write(CAPTION + "\n")
    for f in to_photos:
        r = subprocess.run([RCLONE, "copy", f, ALBUM],
                           capture_output=True, text=True, timeout=900)
        print(os.path.basename(f), "->photos",
              "ok" if r.returncode == 0 else r.stderr[-150:])
    for rid in pair:
        st["pushed"].append({"id": rid, "date": today})
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w"), indent=1)
    print(f"pushed {pair} (story suggestion: {story_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
