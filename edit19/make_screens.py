#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 + TTP223 touch-sensor '3 modes' short (own design, 128x64 1-bit):
intro 'TOUCH ME' with a fingerprint pad icon (inverted 'TOUCHED!' while touched), a MODE picker page
while the knob clicks, then LAMP (bulb ON / OFF), BELL (ringing bell + DING DONG) and COUNT (big
counter, HOLD-to-reset bar). Upscaled 8x with pixel gaps."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, MODES, KNOB_CLICKS, BELL_AT, mode, mode_idx, touching, led, count, hold_prog, reset_at  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def pad_icon(d, cx, cy, r, fill=1):
    for k in range(4):
        rr = r - k * r / 4
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=fill, width=1)


def bulb(d, cx, cy, on):
    d.ellipse((cx - 11, cy - 16, cx + 11, cy + 6), outline=1, width=2, fill=1 if on else 0)
    d.rectangle((cx - 6, cy + 6, cx + 6, cy + 13), fill=1)
    if on:
        for k in range(8):
            a = k * math.pi / 4
            d.line((cx + 15 * math.cos(a), cy - 5 + 15 * math.sin(a), cx + 20 * math.cos(a), cy - 5 + 20 * math.sin(a)), fill=1, width=2)


def bell(d, cx, cy, ang):
    pts = []
    for k in range(13):
        t = k / 12
        pts.append((cx - 12 + 24 * t, cy + 8 - 20 * math.sin(math.pi * t) ** 0.6))
    im = Image.new("1", (40, 40), 0)
    dd = ImageDraw.Draw(im)
    dd.polygon([(p[0] - cx + 20, p[1] - cy + 20) for p in pts], fill=1)
    dd.rectangle((6, 27, 34, 30), fill=1)
    dd.ellipse((16, 30, 24, 37), fill=1)
    im = im.rotate(ang, resample=Image.NEAREST)
    d.bitmap((cx - 20, cy - 20), im, fill=1)


def picking(fr):
    return any(c <= fr < c + 16 for c, _ in KNOB_CLICKS)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    m = mode(fr)
    if m == "INTRO":
        if touching(fr):
            d.rectangle((0, 0, 127, 63), fill=1)
            pad_icon(d, 30, 32, 22, 0)
            d.text((92, 26), "TOUCHED!", font=f(11, True), fill=0, anchor="mm")
            d.text((92, 44), "ESP32 OK", font=f(9), fill=0, anchor="mm")
        else:
            pad_icon(d, 30, 32, 22)
            d.text((88, 26), "TOUCH", font=f(14, True), fill=1, anchor="mm")
            d.text((88, 44), "ME :)", font=f(12, True), fill=1, anchor="mm")
        return im
    if picking(fr):
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), "SELECT MODE", font=f(10, True), fill=0, anchor="mm")
        d.text((64, 37), MODES[mode_idx(fr)] if fr >= [c for c, _ in KNOB_CLICKS if c <= fr][-1] + 5 else
               MODES[max(0, mode_idx(fr))], font=f(18, True), fill=1, anchor="mm")
        d.polygon([(6, 37), (14, 31), (14, 43)], fill=1)
        d.polygon([(122, 37), (114, 31), (114, 43)], fill=1)
        for k in range(3):
            x = 52 + k * 12
            d.ellipse((x - 2, 56, x + 2, 60), fill=1 if k == mode_idx(fr) else 0, outline=1)
        return im
    d.text((1, 0), f"MODE: {m}", font=f(10, True), fill=1)
    if touching(fr):
        d.rectangle((100, 0, 127, 10), fill=1)
        d.text((114, 5), "TCH", font=f(8, True), fill=0, anchor="mm")
    if m == "LAMP":
        bulb(d, 32, 38, led(fr))
        d.text((88, 38), "ON" if led(fr) else "OFF", font=f(22, True), fill=1, anchor="mm")
    elif m == "BELL":
        a = fr - BELL_AT
        ring = 0 <= a < 36
        bell(d, 30, 38, 18 * math.sin(a * 0.9) * (1 - a / 36) if ring else 0)
        d.text((88, 30), "DING" if ring and (a // 9) % 2 == 0 else ("DONG" if ring else "READY"), font=f(14, True), fill=1, anchor="mm")
        d.text((88, 50), "TAP = BELL", font=f(8), fill=1, anchor="mm")
    else:
        if reset_at(fr):
            d.text((64, 36), "RESET!", font=f(20, True), fill=1, anchor="mm")
            return im
        d.text((64, 33), f"{count(fr)}", font=f(28, True), fill=1, anchor="mm")
        p = hold_prog(fr)
        if p > 0:
            d.rectangle((4, 52, 123, 61), outline=1)
            d.rectangle((4, 52, 4 + int(119 * p), 61), fill=1)
        else:
            d.text((64, 57), "HOLD = RESET", font=f(8), fill=1, anchor="mm")
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
