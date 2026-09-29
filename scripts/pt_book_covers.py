#!/usr/bin/env python3
"""PT book covers for O Silêncio Entre Pensamentos, mirroring the EN design:
photo of the Mestre + black band + Georgia caps. Uses PT anchors (brown-robed
Mestre), never the EN monk."""
import os
from PIL import Image, ImageDraw, ImageFont

A = "output/markets/PT/anchors"
OUT = "output/book"
G_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
G = "/System/Library/Fonts/Supplemental/Georgia.ttf"
CREAM = (238, 230, 214)
GOLD = (200, 176, 128)
BLACK = (18, 16, 13)


def cover_fit(path, w, h, y_bias=0.25):
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    s = max(w / iw, h / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    iw, ih = im.size
    x, y = (iw - w) // 2, int((ih - h) * y_bias)
    return im.crop((x, y, x + w, y + h))


def caps_centered(d, text, font, cx, y, fill, tracking=2):
    # simple letter-spaced caps
    text = text.upper()
    widths = [d.textlength(c, font=font) + tracking for c in text]
    total = sum(widths) - tracking
    x = cx - total / 2
    for c, wd in zip(text, widths):
        d.text((x, y), c, font=font, fill=fill)
        x += wd
    return total


# ---- square 1200x1200 (gumroad thumbnail) ----
im = Image.new("RGB", (1200, 1200), BLACK)
im.paste(cover_fit(f"{A}/pt_face_v3.png", 1200, 880, 0.18), (0, 0))
d = ImageDraw.Draw(im)
caps_centered(d, "O Silêncio Entre Pensamentos", ImageFont.truetype(G, 62), 600, 960, CREAM)
d.line([(560, 1060), (640, 1060)], fill=GOLD, width=2)
caps_centered(d, "Um retorno de 30 dias à quietude  ·  Mestre Kaion",
              ImageFont.truetype(G, 30), 600, 1090, GOLD)
im.save(f"{OUT}/gumroad_cover_pt.png")

# ---- wide 1600x900 (product page cover) ----
im = Image.new("RGB", (1600, 900), BLACK)
im.paste(cover_fit(f"{A}/pt_a2_window_light.png", 660, 900, 0.15), (0, 0))
d = ImageDraw.Draw(im)
f_t = ImageFont.truetype(G, 72)
d.text((760, 160), "O SILÊNCIO ENTRE", font=f_t, fill=CREAM)
d.text((760, 260), "PENSAMENTOS", font=f_t, fill=CREAM)
d.line([(764, 390), (940, 390)], fill=GOLD, width=3)
d.text((760, 430), "Um retorno de 30 dias à quietude",
       font=ImageFont.truetype(G, 44), fill=GOLD)
f_b = ImageFont.truetype(G, 34)
for i, line in enumerate(["·  30 práticas diárias, dez minutos por dia",
                          "·  Um ensinamento curto, um pequeno ritual",
                          "·  Uma linha de diário para cada noite"]):
    d.text((760, 540 + i * 62), line, font=f_b, fill=CREAM)
d.text((760, 780), "MESTRE KAION", font=ImageFont.truetype(G, 34), fill=GOLD)
im.save(f"{OUT}/cover_wide_pt.png")

# ---- portrait 864x1184 (book interior cover page photo) ----
cover_fit(f"{A}/pt_mestre_mat.png", 864, 1184, 0.10).save(f"{OUT}/cover_portrait_pt.png")

print("covers written: gumroad_cover_pt.png, cover_wide_pt.png, cover_portrait_pt.png")
