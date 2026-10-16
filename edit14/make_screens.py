#!/usr/bin/env python3
"""SH1106 OLED frames for the rotary-encoder LED flow (own design): header with mode, big step
counter, direction arrows (>>> / <<<), a speed bar, and a row of 8 LED dots mirroring the real LEDs.
128x64 1-bit, upscaled 8x with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, NLED, knob, step, direction, mode, leds  # noqa: E402

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
    m = mode(fr)
    d.rectangle((0, 0, 127, 12), fill=1)
    d.text((64, 6), f"MODE: {m}", font=f(9, True), fill=0, anchor="mm")
    lv = leds(fr)
    for i in range(NLED):                                   # LED dots row
        x = 8 + i * 16
        if lv[i] > 0.6:
            d.ellipse((x - 5, 55 - 5, x + 5, 55 + 5), fill=1)
        elif lv[i] > 0.1:
            d.ellipse((x - 4, 55 - 4, x + 4, 55 + 4), outline=1)
            d.point((x, 55), fill=1)
        else:
            d.point((x, 55), fill=1)
    if m == "BREATHE":
        b = lv[0]
        r = 4 + 12 * b
        d.ellipse((64 - r, 31 - r, 64 + r, 31 + r), outline=1, width=2)
        return im
    d.text((4, 30), f"{step(fr):+03d}", font=f(20, True), fill=1, anchor="lm")
    dr = direction(fr)
    arrow = ">>>" if dr > 0 else "<<<" if dr < 0 else " = "
    d.text((96, 25), arrow, font=f(13, True), fill=1, anchor="mm")
    sp = min(1.0, abs(knob(fr + 1) - knob(fr - 1)) / 40.0)
    d.rectangle((70, 36, 122, 42), outline=1)
    d.rectangle((71, 37, 71 + int(50 * sp), 41), fill=1)
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
