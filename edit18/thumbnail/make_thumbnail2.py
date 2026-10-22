#!/usr/bin/env python3
"""Alternate thumbnails for the ESP32 RGB colour mixer: three close-ups of the diffuser ball side by
side (RED | R+G = YELLOW | R+G+B = WHITE) under a 'RANG MILAO!' header. 1080x1920 Shorts cover (all
words inside the desktop-safe band y = 190..1690) + 1280x720 laptop version."""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F3D = os.path.join(HERE, "..", "work", "frames3d")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
YEL, WHT, INK = (255, 214, 10), (255, 255, 255), (15, 18, 26)
RED, GRN, BLU = (255, 60, 60), (40, 230, 110), (60, 140, 255)
PANELS = [(130, "RED", [("R", RED)]), (150, "YELLOW", [("R", RED), ("G", GRN)]),
          (170, "WHITE", [("R", RED), ("G", GRN), ("B", BLU)])]
CROP = (100, 190, 620, 1072)                 # ball + module in the 720x1280 render


def F(s):
    return ImageFont.truetype(FONT, s)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def panel(f, w, h):
    im = Image.open(os.path.join(F3D, f"{f:04d}.png")).convert("RGB").crop(CROP)
    im = ImageEnhance.Color(im).enhance(1.4).resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 28, fill=255)
    out = Image.new("RGBA", (w, h))
    out.paste(im, (0, 0), m)
    ImageDraw.Draw(out).rounded_rectangle((0, 0, w - 1, h - 1), 28, outline=WHT, width=6)
    return out


def chips(d, cx, cy, items, r):
    gap = r * 2.2
    x0 = cx - (len(items) - 1) * gap / 2
    for k, (ch, col) in enumerate(items):
        x = x0 + k * gap
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=col, outline=WHT, width=max(3, r // 9))
        d.text((x, cy), ch, font=F(int(r * 1.1)), fill=WHT, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))


def background(w, h):
    bg = Image.open(os.path.join(F3D, "0150.png")).convert("RGB").resize((w, h), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(26))
    return Image.blend(bg, Image.new("RGB", (w, h), (8, 10, 16)), 0.6).convert("RGBA")


# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
c = background(W, H)
d = ImageDraw.Draw(c)
text(d, (W // 2, 270), "RANG MILAO!", 124, YEL, 12)
pw, ph, gap = 330, 560, 22
x0 = (W - 3 * pw - 2 * gap) // 2
for k, (f, name, items) in enumerate(PANELS):
    x = x0 + k * (pw + gap)
    c.alpha_composite(panel(f, pw, ph), (x, 420))
    d = ImageDraw.Draw(c)
    chips(d, x + pw // 2, 1060, items, 44)
    col = (RED, YEL, WHT)[k]
    text(d, (x + pw // 2, 1165), name, 58 if k != 1 else 52, col, 7)
text(d, (W // 2, 1300), "1 LED =", 64, WHT, 7)
text(d, (W // 2, 1395), "16 MILLION COLORS", 72, YEL, 8)
d.rounded_rectangle((140, 1490, W - 140, 1590), 50, fill=(130, 60, 255))
d.text((W // 2, 1540), "ESP32 + RGB LED + OLED", font=F(50), fill=WHT, anchor="mm")
d.rounded_rectangle((W // 2 - 205, 1610, W // 2 + 205, 1675), 33, fill=WHT)
d.text((W // 2, 1643), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail2.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = background(W, H)
d = ImageDraw.Draw(c)
text(d, (W // 2, 70), "RANG MILAO!", 92, YEL, 9)
pw, ph, gap = 224, 380, 60
x0 = (W - 3 * pw - 2 * gap) // 2
for k, (f, name, items) in enumerate(PANELS):
    x = x0 + k * (pw + gap)
    c.alpha_composite(panel(f, pw, ph), (x, 135))
    d = ImageDraw.Draw(c)
    chips(d, x + pw // 2, 545, items, 30)
    text(d, (x + pw // 2, 600), name, 44, (RED, YEL, WHT)[k], 5)
d.rounded_rectangle((W // 2 - 300, 640, W // 2 + 300, 705), 33, fill=(130, 60, 255))
d.text((W // 2, 673), "ESP32 + RGB LED + OLED", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail2_16x9.jpg"), quality=93)
print("wrote thumbnail2.jpg + thumbnail2_16x9.jpg in", HERE)
