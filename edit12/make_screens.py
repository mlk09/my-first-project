#!/usr/bin/env python3
"""SH1106 OLED parking-sensor frames (own design): 128x64 1-bit — status bar (SAFE / SLOW / STOP!,
inverted + flashing at STOP), big distance read-out, a top-down car icon with three warning arcs
behind it that light up as the gap closes, and a distance bar. Upscaled to 1024x512 with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, BOOT, SAFE, STOP, dist, zone  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    if fr < BOOT:
        return im
    z = zone(fr)
    dd = dist(fr)
    if z == "STOP" and (fr // 4) % 2 == 0:
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), "STOP!", font=f(11, True), fill=0, anchor="mm")
    else:
        d.rectangle((0, 0, 127, 13), outline=1)
        d.text((64, 7), {"SAFE": "SAFE", "SLOW": "SLOW DOWN", "STOP": "STOP!"}[z], font=f(10, True), fill=1, anchor="mm")
    d.text((4, 34), f"{dd:4.1f}", font=f(20, True), fill=1, anchor="lm")
    d.text((62, 40), "cm", font=f(10), fill=1, anchor="lm")
    # car icon (rear towards the arcs on the right) + arcs
    cx, cy = 92, 34
    d.rounded_rectangle((cx - 10, cy - 6, cx + 10, cy + 6), 3, outline=1, fill=0)
    d.rectangle((cx - 4, cy - 4, cx + 4, cy + 4), outline=1)
    n_arcs = 0 if z == "SAFE" else 1 + int(2 * (SAFE - max(dd, STOP)) / (SAFE - STOP)) if z == "SLOW" else 3
    for i in range(3):
        r = 6 + i * 6
        box = (cx + 10 - r + 4, cy - r, cx + 10 + r + 4, cy + r)
        if i < n_arcs:
            d.arc(box, 300, 60, fill=1, width=2)
        else:
            for a in range(300, 420, 30):
                d.arc(box, a, a + 6, fill=1)
    # distance bar: full at 40 cm
    w = int(118 * min(1.0, dd / 40.0))
    d.rectangle((4, 54, 122, 61), outline=1)
    d.rectangle((5, 55, 5 + w, 60), fill=1)
    for mark in (STOP, SAFE):
        x = 5 + int(118 * mark / 40)
        d.line((x, 52, x, 63), fill=1)
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
