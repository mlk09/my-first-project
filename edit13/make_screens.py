#!/usr/bin/env python3
"""SH1106 OLED robot-eye frames (own design, RoboEyes style): two big rounded-rectangle eyes on
128x64 1-bit, with gaze offset, blinks, and mood lids — happy (bottom arcs), angry (inner slanted
lids), annoyed (flat top lids), sleepy (half-closed + Zzz), love (heart eyes). Upscaled 8x."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, mood, blink, look  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
CW, CH, S = 128, 64, 8
EW, EH, GAP = 36, 36, 14


def heart(d, cx, cy, s):
    d.ellipse((cx - s, cy - s * 0.8, cx, cy + s * 0.2), fill=1)
    d.ellipse((cx, cy - s * 0.8, cx + s, cy + s * 0.2), fill=1)
    d.polygon([(cx - s, cy - 0.15 * s), (cx + s, cy - 0.15 * s), (cx, cy + s)], fill=1)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    m = mood(fr)
    if m == "off":
        return im
    lx, ly = look(fr)
    b = blink(fr)
    cy = 32 + ly
    for side in (-1, 1):
        cx = 64 + side * (EW / 2 + GAP / 2) + lx
        if m == "love":
            s = 15 + (1.5 if (fr // 6) % 2 else 0)
            heart(d, cx, cy, s)
            continue
        h = EH * (1 - 0.92 * b)
        if m == "sleepy":
            h = min(h, EH * 0.38)
        x0, x1 = cx - EW / 2, cx + EW / 2
        y0, y1 = cy - h / 2, cy + h / 2
        if m == "sleepy":
            y0, y1 = cy + EH / 2 - h - 4, cy + EH / 2 - 4
        d.rounded_rectangle((x0, y0, x1, y1), radius=min(9, h / 2), fill=1)
        if m == "happy" and b < 0.5:                               # cheeks push the eye up: bottom arc cut
            d.ellipse((x0 - 6, cy + 2, x1 + 6, cy + EH), fill=0)
        if m == "angry":                                           # slanted inner lids
            inner = x1 if side < 0 else x0
            outer = x0 if side < 0 else x1
            d.polygon([(outer, y0 - 2), (inner, y0 + 16), (inner, y0 - 2)], fill=0)
        if m == "annoyed":
            d.rectangle((x0, y0 - 1, x1, y0 + 12), fill=0)
    if m == "sleepy" and (fr // 10) % 3 != 0:
        k = (fr // 10) % 3
        d.text((112, 14 - 4 * k), "z" if k == 1 else "Z", font=ImageFont.truetype(MONO, 9 + 3 * k), fill=1, anchor="mm")
    return im


for fr in range(N):
    im = screen(fr)
    big = Image.new("RGB", (CW * S, CH * S), (2, 3, 6))
    px = im.load()
    d = ImageDraw.Draw(big)
    for yy in range(CH):
        for xx in range(CW):
            if px[xx, yy]:
                d.rectangle((xx * S, yy * S, xx * S + S - 2, yy * S + S - 2), fill=(185, 235, 255))
    big.save(os.path.join(OUT, f"{fr:04d}.png"))
print("oled frames in", OUT)
