#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 + DHT11 temperature-controlled LED (own design, 128x64 1-bit):
big live TEMP, HUM, the knob-set limit, an LED ON/OFF banner and a scrolling temperature graph with a
dashed threshold line. While the knob turns the screen switches to a big 'SET LIMIT' page.
Upscaled 8x with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, SHOTS, temp, hum, limit, hot  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8
GX0, GX1, GY0, GY1 = 74, 127, 12, 50          # graph box
TLO, THI = 24.0, 37.0


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def gy(t):
    return GY1 - (min(max(t, TLO), THI) - TLO) / (THI - TLO) * (GY1 - GY0)


def setting(fr):
    return SHOTS[3] + 4 <= fr < SHOTS[4] - 4


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    lim = int(limit(fr))
    if setting(fr):                                         # knob page
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), "SET TEMP LIMIT", font=f(10, True), fill=0, anchor="mm")
        d.text((54, 37), f"{lim}", font=f(30, True), fill=1, anchor="mm")
        d.text((80, 28), "o", font=f(9, True), fill=1, anchor="mm")
        d.text((90, 37), "C", font=f(16, True), fill=1, anchor="mm")
        d.polygon([(6, 37), (14, 31), (14, 43)], fill=1)
        d.polygon([(122, 37), (114, 31), (114, 43)], fill=1)
        d.text((64, 58), f"NOW {temp(fr):.1f}C", font=f(9), fill=1, anchor="mm")
        return im
    t, h, on = temp(fr), hum(fr), hot(fr)
    d.text((1, 0), "DHT11", font=f(9, True), fill=1)
    d.text((127, 0), f"SET {lim}C", font=f(9, True), fill=1, anchor="ra")
    d.text((1, 13), f"{t:.1f}", font=f(21, True), fill=1)
    d.text((58, 14), "o", font=f(7, True), fill=1)
    d.text((63, 17), "C", font=f(11, True), fill=1)
    d.text((1, 39), f"HUM {h:.0f}%", font=f(9), fill=1)
    # graph: last 52 frames, one px per frame
    for x in range(GX0, GX1 + 1, 4):                        # dashed threshold
        d.line((x, gy(lim), x + 1, gy(lim)), fill=1)
    d.line((GX0, GY1 + 1, GX1, GY1 + 1), fill=1)
    pts = [(GX1 - i, gy(temp(fr - i))) for i in range(GX1 - GX0 + 1) if fr - i >= 0]
    if len(pts) > 1:
        d.line(pts, fill=1, width=1)
    if pts:
        d.ellipse((pts[0][0] - 2, pts[0][1] - 2, pts[0][0] + 1, pts[0][1] + 1), fill=1)
    if on:
        d.rectangle((0, 52, 127, 63), fill=1)
        d.text((64, 58), "HOT!  RED LED ON", font=f(9, True), fill=0, anchor="mm")
    else:
        d.rectangle((0, 52, 127, 63), outline=1)
        d.text((64, 58), "OK  -  LED OFF", font=f(9, True), fill=1, anchor="mm")
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
