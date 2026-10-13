#!/usr/bin/env python3
"""Procedural textures for the self-balancing robot scene -> edit9/work/tex/: green cutting mat
(1 cm grid, same look as the Tap-to-Light short), MPU6050 and DRV8833 breakout tops."""
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
for a in (0.25, 0.5, 0.75):
    d.line((0, S * a, S * (1 - a), S), fill=(70, 130, 110), width=1)
im.save(os.path.join(OUT, "mat.png"))


def board(name, size, bg, title, sub, extra=None):
    w, h = size
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    for i in range(8):                                    # header pads along one edge
        x = 30 + i * (w - 60) / 7
        d.ellipse((x - 11, h - 34, x + 11, h - 12), fill=(215, 175, 80))
        d.ellipse((x - 4, h - 27, x + 4, h - 19), fill=(40, 40, 40))
    d.text((w / 2, 40), title, font=ImageFont.truetype(SANS, 34), fill=(240, 242, 250), anchor="mm")
    d.text((w / 2, 80), sub, font=ImageFont.truetype(SANS, 20), fill=(220, 225, 240), anchor="mm")
    if extra:
        extra(d, w, h)
    im.save(os.path.join(OUT, name))


def axes(d, w, h):
    cx, cy = w * 0.72, h * 0.55
    d.line((cx, cy, cx + 50, cy), fill=(240, 240, 240), width=4)
    d.line((cx, cy, cx, cy - 50), fill=(240, 240, 240), width=4)
    d.text((cx + 58, cy), "X", font=ImageFont.truetype(SANS, 18), fill=(240, 240, 240), anchor="lm")
    d.text((cx, cy - 58), "Y", font=ImageFont.truetype(SANS, 18), fill=(240, 240, 240), anchor="mb")
    d.rectangle((w * 0.25, h * 0.4, w * 0.25 + 50, h * 0.4 + 50), fill=(25, 25, 28))


board("mpu6050.png", (320, 240), (20, 70, 160), "GY-521", "MPU-6050", axes)
board("drv8833.png", (280, 220), (110, 30, 120), "DRV8833", "Motor Driver")
board("buck.png", (320, 240), (25, 90, 190), "3.3V", "Buck Converter")
print("textures in", OUT)
