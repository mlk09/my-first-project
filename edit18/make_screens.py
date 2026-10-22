#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 RGB colour mixer (own design, 128x64 1-bit): R / G / B bars with
0-255 values and the colour name; the hue page shows the knob hue in degrees, the brightness page a
big PWM % bar, and PARTY mode bouncing stars. Upscaled 8x with pixel gaps."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, mode, rgb, to255, name, hue, bright  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def bars(d, fr, y0=24):
    for i, (lab, v) in enumerate(zip("RGB", to255(rgb(fr)))):
        y = y0 + i * 10
        d.text((1, y), lab, font=f(9, True), fill=1)
        d.rectangle((11, y + 1, 95, y + 8), outline=1)
        d.rectangle((11, y + 1, 11 + int(84 * v / 255), y + 8), fill=1)
        d.text((127, y), f"{v:3d}", font=f(9, True), fill=1, anchor="ra")


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    m = mode(fr)
    if m == "party":
        d.rectangle((0, 0, 127, 15), fill=1)
        d.text((64, 8), "PARTY MODE!", font=f(11, True), fill=0, anchor="mm")
        for k in range(7):
            x = 10 + k * 18
            y = 38 + 12 * math.sin(fr * 0.5 + k)
            d.regular_polygon((x, y, 5), 4, rotation=fr * 20 + k * 10, fill=1)
        d.text((64, 58), name(fr), font=f(9, True), fill=1, anchor="mm")
        return im
    if m == "bright":
        d.text((1, 0), "BRIGHTNESS", font=f(10, True), fill=1)
        d.text((127, 0), "PWM", font=f(10, True), fill=1, anchor="ra")
        p = int(round(bright(fr) * 100))
        d.text((64, 30), f"{p}%", font=f(22, True), fill=1, anchor="mm")
        d.rectangle((4, 46, 123, 58), outline=1)
        d.rectangle((4, 46, 4 + int(119 * p / 100), 58), fill=1)
        return im
    d.text((1, 0), "RGB MIXER", font=f(10, True), fill=1)
    if m == "hue":
        d.text((127, 0), f"HUE {hue(fr):.0f}", font=f(9, True), fill=1, anchor="ra")
    d.text((64, 16), name(fr), font=f(11, True), fill=1, anchor="mm")
    bars(d, fr)
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
