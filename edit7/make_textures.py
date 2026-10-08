#!/usr/bin/env python3
"""Procedural textures for the Tap-to-Light scene: green self-healing cutting mat and a
full-size (830-point) breadboard top. Written to edit7/work/tex/."""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "tex")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# cutting mat: one tile = 10 x 10 scene units, 1 cm grid = 0.4 units
S = 2048
im = Image.new("RGB", (S, S), (22, 74, 58))
rnd = random.Random(5)
px = im.load()
for _ in range(60000):                                   # speckle
    x, y = rnd.randrange(S), rnd.randrange(S)
    v = rnd.randint(-10, 10)
    r, g, b = px[x, y]
    px[x, y] = (r + v, g + v, b + v)
im = im.filter(ImageFilter.GaussianBlur(0.8))
d = ImageDraw.Draw(im)
step = S / 25
for i in range(26):
    w = 3 if i % 5 == 0 else 1
    c = (150, 200, 180) if i % 5 == 0 else (90, 150, 130)
    d.line((i * step, 0, i * step, S), fill=c, width=w)
    d.line((0, i * step, S, i * step), fill=c, width=w)
    if i % 5 == 0 and i < 25:
        d.text((i * step + 6, 6), str(i), font=ImageFont.truetype(SANS, 22), fill=(170, 215, 195))
for a in (0.25, 0.5, 0.75):                               # 45-degree guide lines
    d.line((0, S * a, S * (1 - a), S), fill=(70, 130, 110), width=1)
im.save(os.path.join(OUT, "mat.png"))

# breadboard: 6.6 x 2.2 units at 200 px/unit, 0.1-unit (2.54 mm) pitch
BW, BH, P = 1320, 440, 20
im = Image.new("RGB", (BW, BH), (236, 234, 226))
d = ImageDraw.Draw(im)
d.rectangle((0, BH / 2 - 7, BW, BH / 2 + 7), fill=(205, 203, 195))            # centre channel
fnt = ImageFont.truetype(SANS, 9)


def hole(x, y):
    d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(60, 60, 62))


x0 = 20
for c in range(63):
    x = x0 + c * P
    for r in range(5):
        hole(x, BH / 2 + 22 + r * P)     # a-e
        hole(x, BH / 2 - 22 - r * P)     # f-j
    if c % 5 == 0:
        d.text((x, BH / 2 + 22 + 5 * P), str(c + 1), font=fnt, fill=(120, 120, 120), anchor="mt")
for side in (1, -1):                      # power rails
    yc = BH / 2 + side * (22 + 4 * P + 50)
    for c in range(63):
        if c % 6 == 5:
            continue
        hole(x0 + c * P, yc - 10)
        hole(x0 + c * P, yc + 10)
    d.line((10, yc - 26, BW - 10, yc - 26), fill=(220, 50, 50) if side < 0 else (40, 90, 210), width=3)
    d.line((10, yc + 26, BW - 10, yc + 26), fill=(40, 90, 210) if side < 0 else (220, 50, 50), width=3)
im.save(os.path.join(OUT, "breadboard.png"))
print("textures in", OUT)
