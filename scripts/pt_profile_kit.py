#!/usr/bin/env python3
"""Build the Mestre Kaion (PT) profile asset kit from existing anchors.

Everything is derived locally with PIL — no generation spend. Mirrors the EN
highlight-cover style: anchor photo, dark overlay, Georgia serif text.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

A = "output/markets/PT/anchors"
OUT = "output/markets/PT/profile"
os.makedirs(OUT, exist_ok=True)

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
GEORGIA_I = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"


def face_crop(path, size, y_center=0.315, zoom=0.50):
    """Square crop centered on the face. y_center/zoom tuned for the anchor set
    (face sits ~24% down the 768x1344 frame)."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = int(w * zoom)
    cx, cy = w // 2, int(h * y_center)
    box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
    return im.crop(box).resize((size, size), Image.LANCZOS)


def cover(path, w, h, y_bias=0.5):
    """Center-crop an anchor to w x h (cover fit). y_bias 0=top, 1=bottom."""
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    im = im.resize((int(iw * scale) + 1, int(ih * scale) + 1), Image.LANCZOS)
    iw, ih = im.size
    x = (iw - w) // 2
    y = int((ih - h) * y_bias)
    return im.crop((x, y, x + w, y + h))


def draw_centered(d, text, font, cx, y, fill=(255, 255, 255), shadow=2, max_w=None):
    """Draw word-wrapped centered text, return the y after the block."""
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if max_w and d.textlength(t, font=font) > max_w and cur:
            lines.append(cur); cur = wd
        else:
            cur = t
    lines.append(cur)
    lh = int(font.size * 1.35)
    for ln in lines:
        tw = d.textlength(ln, font=font)
        x = cx - tw / 2
        d.text((x + shadow, y + shadow), ln, font=font, fill=(0, 0, 0))
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def darken(im, factor=0.62):
    return ImageEnhance.Brightness(im).enhance(factor)


# ---- 1. profile photos (IG 320 + hi-res 1000) --------------------------------
for size, name in [(320, "profile_320.png"), (1000, "profile_1000.png")]:
    face_crop(f"{A}/pt_face_v3.png", size).save(f"{OUT}/{name}")

# ---- 2. highlight covers 1080x1920, EN style ---------------------------------
COVERS = [
    ("pt_a2_window_light.png", "Comece Aqui",
     "Pequenas práticas para uma mente que não para."),
    ("pt_a5_grey_shawl_mist.png", "Sabedoria",
     "A mente aquieta quando você deixa de alimentá-la."),
    ("pt_a7_candle_dark.png", "Rituais",
     "Não é o ritual que muda a casa. É a intenção que muda você."),
]
for src, title, sub in COVERS:
    im = darken(cover(f"{A}/{src}", 1080, 1920, y_bias=0.35))
    d = ImageDraw.Draw(im)
    f_title = ImageFont.truetype(GEORGIA_B, 110)
    f_sub = ImageFont.truetype(GEORGIA_I, 58)
    draw_centered(d, title, f_title, 540, 360, max_w=900)
    draw_centered(d, sub, f_sub, 540, 1560, max_w=860)
    slug = title.lower().replace(" ", "_").replace("ç", "c")
    im.save(f"{OUT}/highlight_{slug}.jpg", quality=92)

# ---- 3. YouTube banner 2560x1440 (safe area 1546x423 centered) ---------------
# The FACE must live inside the 423px-tall safe strip (mobile shows only that),
# with the text beside it — not stacked on top of it.
# y_bias=0 keeps the top of the source, which puts his face (~y560 after the
# 3.33x cover scale) inside the 508-931 safe strip.
im = darken(cover(f"{A}/pt_a6_dirt_path.png", 2560, 1440, y_bias=0.12), 0.70)
sy = (1440 - 423) // 2                            # safe strip top (y=508)
d = ImageDraw.Draw(im)
# safe area x-range is 507-2053; his face is centered ~x1280, so the text
# block must fit inside x 507-1080 (left of the face, inside the safe area)
f_name = ImageFont.truetype(GEORGIA_B, 78)
f_tag = ImageFont.truetype(GEORGIA_I, 38)
tx = 800                                          # text center, left of monk
draw_centered(d, "Mestre Kaion", f_name, tx, sy + 110, max_w=560)
draw_centered(d, "40 anos em silêncio. Agora eu ensino.", f_tag, tx, sy + 230,
              max_w=540)
im.save(f"{OUT}/youtube_banner_2560x1440.jpg", quality=92)

# ---- 4. YouTube avatar 800x800 ----------------------------------------------
face_crop(f"{A}/pt_face_v3.png", 800).save(f"{OUT}/youtube_avatar_800.png")

# ---- 5. bio texts ------------------------------------------------------------
BIO = """MESTRE KAION — textos de perfil (PT)
=====================================

Instagram (@mestrekaion)
  Nome (campo name): Mestre Kaion | Sabedoria e Cura
  Bio:
    40 anos em silêncio. Agora eu ensino.
    Pequenas práticas para uma mente que não para.
  (sem linha de produto até o livro PT existir)

TikTok (@mestre.kaion)
  Nome: Mestre Kaion
  Bio: 40 anos em silêncio. Agora eu ensino. 🙏

YouTube (UC8LvVqplv_XMhHsfhANyXbw)
  Nome do canal: Mestre Kaion | Sabedoria e Cura
  Descrição:
    40 anos em silêncio. Agora eu ensino.
    Pequenas práticas para uma mente que não para.
    Um vídeo por dia. Sente. Respire. Comece.

Destaques (highlights) — ordem no perfil:
  1. Comece Aqui   2. Sabedoria   3. Rituais
"""
open(f"{OUT}/BIO_PT.txt", "w").write(BIO)
print("done ->", OUT)
for f in sorted(os.listdir(OUT)):
    print("  ", f)
