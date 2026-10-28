#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 + MQ-2 gas alarm (own design, 128x64 1-bit): big live ppm, a
0-1000 ppm bar with the limit marker, a spinning fan icon, SAFE / flashing GAS LEAK! banner, and a
SET LIMIT page while the knob turns. Upscaled 8x with pixel gaps."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, SHOTS, ppm, limit, alarm, fan, fan_angle  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def fan_icon(d, cx, cy, r, ang, fill=1):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fill)
    for k in range(3):
        a = math.radians(ang + k * 120)
        d.polygon([(cx, cy), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)),
                   (cx + r * 0.9 * math.cos(a + 0.7), cy + r * 0.9 * math.sin(a + 0.7))], fill=fill)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    lim = int(limit(fr))
    if SHOTS[3] + 4 <= fr < SHOTS[4] - 4:                     # knob page
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), "SET GAS LIMIT", font=fo(10), fill=0, anchor="mm")
        d.text((56, 36), f"{lim}", font=fo(26), fill=1, anchor="mm")
        d.text((92, 42), "ppm", font=fo(9), fill=1, anchor="mm")
        d.polygon([(6, 36), (14, 30), (14, 42)], fill=1)
        d.polygon([(122, 36), (114, 30), (114, 42)], fill=1)
        d.text((64, 58), f"NOW {ppm(fr):.0f} ppm", font=fo(8, False), fill=1, anchor="mm")
        return im
    p, al = ppm(fr), alarm(fr)
    if al and (fr // 4) % 2 == 0:                              # flashing alarm page
        d.rectangle((0, 0, 127, 63), fill=1)
        d.text((64, 12), "GAS LEAK!", font=fo(15), fill=0, anchor="mm")
        d.text((64, 33), f"{p:.0f} ppm", font=fo(14), fill=0, anchor="mm")
        d.text((64, 53), "FAN ON  ALARM ON", font=fo(8, False), fill=0, anchor="mm")
        return im
    d.text((1, 0), "MQ-2 GAS", font=fo(9), fill=1)
    d.text((127, 0), f"LIMIT {lim}", font=fo(8, False), fill=1, anchor="ra")
    d.text((2, 14), f"{p:.0f}", font=fo(22), fill=1)
    d.text((62, 24), "ppm", font=fo(9), fill=1)
    fan_icon(d, 112, 26, 11, fan_angle(fr) if fan(fr) > 0.02 else 0)
    x0, x1, y0, y1 = 2, 125, 42, 49                           # 0..1000 ppm bar
    d.rectangle((x0, y0, x1, y1), outline=1)
    d.rectangle((x0, y0, x0 + int((x1 - x0) * min(p, 1000) / 1000), y1), fill=1)
    lx = x0 + int((x1 - x0) * lim / 1000)
    d.line((lx, y0 - 3, lx, y1 + 3), fill=1)
    if al:
        d.rectangle((0, 53, 127, 63), fill=1)
        d.text((64, 58), "GAS LEAK! FAN ON", font=fo(9), fill=0, anchor="mm")
    else:
        d.rectangle((0, 53, 127, 63), outline=1)
        d.text((64, 58), "AIR SAFE" + ("  FAN ON" if fan(fr) > 0.05 else ""), font=fo(9), fill=1, anchor="mm")
    return im


if __name__ == "__main__":
    for fr in range(N):
        im = screen(fr)
        big = Image.new("RGB", (CW * S, CH * S), (2, 3, 6))
        px = im.load()
        dd = ImageDraw.Draw(big)
        for yy in range(CH):
            for xx in range(CW):
                if px[xx, yy]:
                    dd.rectangle((xx * S, yy * S, xx * S + S - 2, yy * S + S - 2), fill=(185, 235, 255))
        big.save(os.path.join(OUT, f"{fr:04d}.png"))
    print("oled frames in", OUT)
