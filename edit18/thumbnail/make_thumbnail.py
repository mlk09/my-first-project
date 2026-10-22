#!/usr/bin/env python3
"""Thumbnails for the ESP32 + OLED RGB colour mixer: a 1080x1920 Shorts cover (all words inside the
desktop-safe band y = 190..1690) and a 1280x720 version for laptop / desktop feeds. Background =
the glowing diffuser ball + knob, OLED inset with R / G / B bars, '16 MILLION COLORS?' with a
rainbow-filled word and R / G / B chips. Optional args: <background frame> <oled frame>."""
import colorsys
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0150.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0150.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
YEL, WHT, INK = (255, 214, 10), (255, 255, 255), (15, 18, 26)
RGBC = ((255, 60, 60), (40, 230, 110), (60, 140, 255))


def F(s):
    return ImageFont.truetype(FONT, s)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def rainbow_text(c, xy, s, size, stroke=11, anchor="mm"):
    """Word filled with a left-to-right hue gradient, black outline."""
    d = ImageDraw.Draw(c)
    d.text(xy, s, font=F(size), fill=(0, 0, 0), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))
    m = Image.new("L", c.size, 0)
    ImageDraw.Draw(m).text(xy, s, font=F(size), fill=255, anchor=anchor)
    x0, _, x1, _ = m.getbbox()
    row = np.array([colorsys.hsv_to_rgb(0.85 * (x - x0) / max(1, x1 - x0), 0.85, 1.0) for x in range(c.size[0])]) * 255
    grad = Image.fromarray(np.repeat(row[None].astype(np.uint8), c.size[1], 0), "RGB").convert("RGBA")
    grad.putalpha(m)
    c.alpha_composite(grad)


def oled_inset(w, ang):
    ol = Image.open(OLEDF).convert("RGB").resize((w, w // 2), Image.LANCZOS)
    pad = w // 24
    box = Image.new("RGBA", (w + 2 * pad, w // 2 + 2 * pad), (20, 70, 165, 255))
    box.paste(ol, (pad, pad))
    return box.rotate(ang, expand=True, resample=Image.BICUBIC)


def chips(d, cx, cy, r, gap):
    for k, (ch, col) in enumerate(zip("RGB", RGBC)):
        x = cx + (k - 1) * gap
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=col, outline=WHT, width=max(4, r // 10))
        d.text((x, cy), ch, font=F(int(r * 1.1)), fill=WHT, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))


def shade(c, top, bottom):
    w, h = c.size
    g = Image.new("L", (1, h))
    g.putdata([int(235 * max(0, 1 - (y - top[0]) / top[1])) if y < top[0] + top[1] else
               int(210 * max(0, (y - bottom[0]) / bottom[1])) for y in range(h)])
    c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), 0)] * 3, g.resize((w, h)))))


src = Image.open(FRAME).convert("RGB")

# ---------------------------------------------------------------- 9:16 Shorts cover (mobile + desktop safe)
W, H = 1080, 1920
c = src.resize((W, H), Image.LANCZOS).convert("RGBA")
shade(c, (150, 650), (1350, 450))
d = ImageDraw.Draw(c)
text(d, (W // 2, 255), "1 LED =", 92, WHT, 9)
text(d, (W // 2, 385), "16 MILLION", 128, YEL, 12)
rainbow_text(c, (W // 2, 520), "COLORS?", 136)
d = ImageDraw.Draw(c)
box = oled_inset(420, -5)
c.alpha_composite(box, (W - box.width - 40, 1110))
d = ImageDraw.Draw(c)
chips(d, 250, 1300, 70, 150)
d.rounded_rectangle((60, 1500, 760, 1600), 50, fill=(130, 60, 255))
d.text((410, 1550), "ESP32 RGB Mixer", font=F(52), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
sw = 620
crop = src.resize((sw, int(sw * src.height / src.width)), Image.LANCZOS)
top = int(crop.height * 0.02)
crop = crop.crop((0, top, sw, top + H)).convert("RGBA")
c.alpha_composite(crop, (W - sw, 0))
fade = Image.new("L", (W, 1))
fade.putdata([255 if x < W - sw else int(255 * max(0, 1 - (x - (W - sw)) / 220)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 12)] * 3, fade.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (40, 80), "1 LED =", 70, WHT, 8, anchor="lm")
text(d, (40, 190), "16 MILLION", 110, YEL, 10, anchor="lm")
rainbow_text(c, (40, 310), "COLORS?", 116, 10, anchor="lm")
d = ImageDraw.Draw(c)
chips(d, 150, 450, 52, 115)
box = oled_inset(300, -4)
c.alpha_composite(box, (380, 385))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 560, 560, 630), 35, fill=(130, 60, 255))
d.text((300, 595), "ESP32 RGB Mixer", font=F(42), fill=WHT, anchor="mm")
d.rounded_rectangle((40, 650, 400, 705), 28, fill=WHT)
d.text((220, 678), "@The IOT Engineer", font=F(26), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=93)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
