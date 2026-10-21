#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 + HC-SR04 object-detection alarm (own design, 128x64 1-bit):
live distance in big digits, the knob-set RANGE, a distance bar with the range marker and an
AREA CLEAR / flashing WARNING banner. While the knob turns the screen switches to a big 'SET RANGE'
page. Upscaled 8x with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, SHOTS, FAR, dist, rng, alert  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def setting(fr):
    return SHOTS[3] + 4 <= fr < SHOTS[4] - 4


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    r = int(rng(fr))
    if setting(fr):                                         # knob page
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), "SET ALARM RANGE", font=f(10, True), fill=0, anchor="mm")
        d.text((56, 37), f"{r}", font=f(30, True), fill=1, anchor="mm")
        d.text((92, 40), "cm", font=f(14, True), fill=1, anchor="mm")
        d.polygon([(6, 37), (14, 31), (14, 43)], fill=1)
        d.polygon([(122, 37), (114, 31), (114, 43)], fill=1)
        d.text((64, 58), f"OBJECT {dist(fr):.0f}cm", font=f(9), fill=1, anchor="mm")
        return im
    dd, on = dist(fr), alert(fr)
    if on and (fr // 4) % 2 == 0:                           # flashing warning page
        d.rectangle((0, 0, 127, 63), fill=1)
        d.text((64, 13), "WARNING!", font=f(16, True), fill=0, anchor="mm")
        d.text((64, 33), "OBJECT DETECTED", font=f(9, True), fill=0, anchor="mm")
        d.text((64, 51), f"{dd:.0f} cm", font=f(16, True), fill=0, anchor="mm")
        return im
    d.text((1, 0), "HC-SR04", font=f(9, True), fill=1)
    d.text((127, 0), f"RANGE {r}cm", font=f(9, True), fill=1, anchor="ra")
    txt = f"{dd:.0f}" if dd < 39.5 else "--"
    d.text((2, 12), txt, font=f(24, True), fill=1)
    d.text((44 if len(txt) > 1 else 26, 22), "cm", font=f(12, True), fill=1)
    # distance bar: 0..40 cm, range marker
    x0, x1, y0, y1 = 70, 126, 18, 30
    d.rectangle((x0, y0, x1, y1), outline=1)
    w = int((x1 - x0) * min(dd, FAR) / FAR)
    d.rectangle((x0, y0, x0 + w, y1), fill=1)
    rx = x0 + int((x1 - x0) * r / FAR)
    d.line((rx, y0 - 4, rx, y1 + 4), fill=1, width=1)
    d.text((rx, y1 + 9), "R", font=f(8, True), fill=1, anchor="mm")
    if on:
        d.rectangle((0, 52, 127, 63), fill=1)
        d.text((64, 58), "ALERT! RED LED ON", font=f(9, True), fill=0, anchor="mm")
    else:
        d.rectangle((0, 52, 127, 63), outline=1)
        d.text((64, 58), "AREA CLEAR - OK", font=f(9, True), fill=1, anchor="mm")
    return im


if __name__ == "__main__":
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
