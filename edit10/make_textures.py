#!/usr/bin/env python3
"""Procedural textures for the ESP32 + OLED scene (units = cm) -> edit10/work/tex/: green cutting
mat, half-size breadboard top, SH1106 OLED module PCB top."""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "tex")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# cutting mat: one tile = 25 x 25 cm, 1 cm grid
S = 2048
im = Image.new("RGB", (S, S), (22, 74, 58))
rnd = random.Random(5)
px = im.load()
for _ in range(60000):
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
im.save(os.path.join(OUT, "mat.png"))

# half breadboard 8.4 x 5.6 cm at 100 px/cm, 2.54 mm pitch
BW, BH, P = 840, 560, 25.4
im = Image.new("RGB", (BW, BH), (238, 236, 228))
d = ImageDraw.Draw(im)
d.rectangle((0, BH / 2 - 9, BW, BH / 2 + 9), fill=(208, 206, 198))
for c in range(31):
    xx = 40 + c * P
    for r in range(5):
        for yy in (BH / 2 + 28 + r * P, BH / 2 - 28 - r * P):
            d.rectangle((xx - 4, yy - 4, xx + 4, yy + 4), fill=(60, 60, 62))
for side in (1, -1):
    yc = BH / 2 + side * (28 + 4 * P + 62)
    for c in range(31):
        if c % 6 != 5:
            for o in (-12, 12):
                d.rectangle((40 + c * P - 4, yc + o - 4, 40 + c * P + 4, yc + o + 4), fill=(60, 60, 62))
    d.line((10, yc - 30, BW - 10, yc - 30), fill=(220, 50, 50), width=3)
    d.line((10, yc + 30, BW - 10, yc + 30), fill=(40, 90, 210), width=3)
im.save(os.path.join(OUT, "breadboard.png"))

# SH1106 1.3" module PCB 3.5 x 3.6 cm at 200 px/cm
MW, MH = 700, 720
im = Image.new("RGB", (MW, MH), (20, 70, 165))
d = ImageDraw.Draw(im)
for i, lab in enumerate(["GND", "VCC", "SCL", "SDA"]):
    x = MW / 2 + (i - 1.5) * 50.8
    d.ellipse((x - 16, 40 - 16, x + 16, 40 + 16), fill=(215, 175, 80))
    d.ellipse((x - 6, 34, x + 6, 46), fill=(30, 30, 30))
    d.text((x, 82), lab, font=ImageFont.truetype(SANS, 22), fill=(240, 242, 250), anchor="mm")
for x, y in ((40, 40), (MW - 40, 40), (40, MH - 40), (MW - 40, MH - 40)):
    d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=(200, 200, 205))
    d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(30, 30, 35))
d.text((MW / 2, MH - 50), "1.3\" OLED  SH1106", font=ImageFont.truetype(SANS, 26), fill=(220, 230, 250), anchor="mm")
im.save(os.path.join(OUT, "oled_pcb.png"))
print("textures in", OUT)
