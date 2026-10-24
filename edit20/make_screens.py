#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 + PIR motion alarm (own design, 128x64 1-bit): a lock icon with
DISARMED / ARMED, a 3-2-1 arming countdown, a live 'scan' bar while ARMED, a flashing inverted
'MOTION DETECTED! / ALARM' page with an intruder counter, and ALL CLEAR. Upscaled 8x with pixel gaps."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, SHOTS, armed, alarm, detecting, countdown  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def lock(d, cx, cy, closed, fill=1):
    d.rounded_rectangle((cx - 9, cy - 2, cx + 9, cy + 13), 2, fill=fill)
    if closed:
        d.arc((cx - 7, cy - 14, cx + 7, cy + 2), 180, 360, fill=fill, width=3)
        d.line((cx - 7, cy - 6, cx - 7, cy), fill=fill, width=3)
    else:
        d.arc((cx - 3, cy - 16, cx + 11, cy), 180, 360, fill=fill, width=3)
    d.line((cx + 7, cy - 8, cx + 7, cy), fill=fill, width=3)
    d.ellipse((cx - 2, cy + 3, cx + 2, cy + 7), fill=1 - fill)


def intruders(fr):
    starts = [k for k in range(1, fr + 1) if alarm(k) and not alarm(k - 1)]
    return len([k for k in starts if k >= SHOTS[1]]) + (1 if fr < SHOTS[1] and alarm(fr) else 0)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    if alarm(fr):
        flash = (fr // 4) % 2 == 0
        if flash:
            d.rectangle((0, 0, 127, 63), fill=1)
        c = 0 if flash else 1
        d.text((64, 12), "MOTION", font=f(15, True), fill=c, anchor="mm")
        d.text((64, 30), "DETECTED!", font=f(15, True), fill=c, anchor="mm")
        d.text((64, 52), "!! ALARM ON !!", font=f(10, True), fill=c, anchor="mm")
        return im
    cd = countdown(fr)
    if cd:
        d.text((64, 7), "ARMING IN", font=f(11, True), fill=1, anchor="mm")
        d.text((64, 38), str(cd), font=f(34, True), fill=1, anchor="mm")
        return im
    if not armed(fr):
        lock(d, 20, 30, False)
        d.text((80, 24), "DISARMED", font=f(13, True), fill=1, anchor="mm")
        d.text((80, 44), "knob = ARM", font=f(9), fill=1, anchor="mm")
        return im
    lock(d, 14, 22, True)
    d.text((76, 14), "ARMED", font=f(16, True), fill=1, anchor="mm")
    d.text((76, 32), "PIR scanning", font=f(9), fill=1, anchor="mm")
    x = int(6 + 116 * (0.5 + 0.5 * math.sin(fr * 0.25)))         # scanning dot
    d.line((4, 44, 123, 44), fill=1)
    d.rectangle((x - 5, 41, x + 5, 47), fill=1)
    n = intruders(fr)
    d.text((64, 57), "ALL CLEAR" if n else "AREA SAFE", font=f(10, True), fill=1, anchor="mm")
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
