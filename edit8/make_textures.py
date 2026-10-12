#!/usr/bin/env python3
"""Procedural textures for the RFID door-lock scene -> edit8/work/tex/: oak door grain,
half-size breadboard, MFRC522 blue PCB with antenna coil, white RFID card, grey floor tiles."""
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "tex")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
rnd = np.random.default_rng(4)

# oak: vertical grain, 1024 x 2048
w, h = 1024, 2048
x = np.arange(w)[None, :]
y = np.arange(h)[:, None]
warp = 18 * np.sin(y / 230 + np.sin(x / 90)) + 6 * np.sin(y / 37 + x / 51)
g = np.sin((x + warp) / 7.0) * 0.5 + np.sin((x + warp * 1.7) / 2.3) * 0.18
g += rnd.normal(0, 0.12, (h, w))
g = (g - g.min()) / (g.max() - g.min())
base = np.array([196, 120, 52], np.float32)
dark = np.array([150, 82, 32], np.float32)
img = base * (1 - g[..., None] * 0.9) + dark * 0.75 * g[..., None] * 0.9
Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(OUT, "oak.png"))

# half breadboard 4.6 x 3.0 units at 200 px/unit
BW, BH, P = 920, 600, 20
im = Image.new("RGB", (BW, BH), (238, 236, 228))
d = ImageDraw.Draw(im)
d.rectangle((0, BH / 2 - 7, BW, BH / 2 + 7), fill=(208, 206, 198))
for c in range(44):
    xx = 30 + c * P
    for r in range(5):
        for yy in (BH / 2 + 22 + r * P, BH / 2 - 22 - r * P):
            d.rectangle((xx - 3, yy - 3, xx + 3, yy + 3), fill=(60, 60, 62))
for side in (1, -1):
    yc = BH / 2 + side * (22 + 4 * P + 70)
    for c in range(44):
        if c % 6 != 5:
            for o in (-10, 10):
                d.rectangle((30 + c * P - 3, yc + o - 3, 30 + c * P + 3, yc + o + 3), fill=(60, 60, 62))
    d.line((10, yc - 26, BW - 10, yc - 26), fill=(220, 50, 50), width=3)
    d.line((10, yc + 26, BW - 10, yc + 26), fill=(40, 90, 210), width=3)
im.save(os.path.join(OUT, "breadboard.png"))

# MFRC522: 1.6 x 2.4 units (portrait) at 250 px/unit
RW, RH = 400, 600
im = Image.new("RGB", (RW, RH), (20, 85, 170))
d = ImageDraw.Draw(im)
for i in range(4):                                         # antenna coil
    m = 40 + i * 12
    d.rounded_rectangle((m, 210 + i * 12, RW - m, RH - 40 - i * 12), 40, outline=(70, 140, 220), width=6)
cx, cy = RW / 2, 400
for r in (30, 60, 90):                                     # contactless symbol
    d.arc((cx - r, cy - r, cx + r, cy + r), 210, 330, fill=(235, 240, 250), width=9)
    d.arc((cx - r, cy - r, cx + r, cy + r), 30, 150, fill=(235, 240, 250), width=9)
d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(235, 240, 250))
d.text((RW / 2, 270), "MFRC522", font=ImageFont.truetype(SANS, 44), fill=(240, 242, 250), anchor="mm")
d.text((RW / 2, 530), "RFID-RC522", font=ImageFont.truetype(SANS, 26), fill=(200, 215, 240), anchor="mm")
for i in range(8):                                         # header pads
    d.ellipse((60 + i * 38 - 11, 30 - 11, 60 + i * 38 + 11, 30 + 11), fill=(215, 175, 80))
im.save(os.path.join(OUT, "rc522.png"))

# RFID card 3.4 x 2.15 units at 300 px/unit
CW, CH = 1020, 645
im = Image.new("RGB", (CW, CH), (246, 246, 244))
d = ImageDraw.Draw(im)
for i in range(CH):
    d.line((0, i, CW, i), fill=(246 - i // 40, 246 - i // 40, 250))
d.rounded_rectangle((60, 60, 220, 180), 16, fill=(215, 180, 90))
d.text((60, 330), "VISITOR", font=ImageFont.truetype(MONT, 90), fill=(40, 45, 60), anchor="lm")
d.text((60, 430), "Card ID: E3 07 5B A2", font=ImageFont.truetype(SANS, 40), fill=(110, 115, 130), anchor="lm")
d.text((CW - 60, CH - 70), "13.56 MHz", font=ImageFont.truetype(SANS, 36), fill=(110, 115, 130), anchor="rm")
im.save(os.path.join(OUT, "card.png"))

# floor tiles
S = 1024
im = Image.new("RGB", (S, S), (150, 148, 144))
px = im.load()
r = random.Random(2)
for _ in range(40000):
    a, b = r.randrange(S), r.randrange(S)
    v = r.randint(-12, 12)
    c = px[a, b]
    px[a, b] = (c[0] + v, c[1] + v, c[2] + v)
d = ImageDraw.Draw(im)
for i in range(0, S + 1, S // 2):
    d.line((i, 0, i, S), fill=(110, 108, 104), width=6)
    d.line((0, i, S, i), fill=(110, 108, 104), width=6)
im.filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(OUT, "floor.png"))
print("textures in", OUT)
