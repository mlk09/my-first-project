#!/usr/bin/env python3
"""SH1106 OLED radar frames (own design): 128x64 1-bit radar scope per video frame — range arcs,
sweep line with a fading trail that follows timeline.sweep(), blip + 'OBJECT 13cm' banner while
timeline.alarm(), 'AREA CLEAR' otherwise. Upscaled to 1024x512 with visible pixel gaps."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, BOOT, OBJ_ANGLE, OBJ_DIST, sweep, alarm, last_hit, presence  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
PIX = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
CW, CH, S = 128, 64, 8
CX, CY, R = 64, 62, 46
MAXCM = 20.0


def f(sz):
    return ImageFont.truetype(PIX, sz)


def pol(a, r):
    t = math.radians(a)
    return CX + r * math.cos(t), CY - r * math.sin(t)


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    if fr < BOOT:
        return im
    for rr in (R / 3, 2 * R / 3, R):                       # range arcs + angle ticks
        d.arc((CX - rr, CY - rr, CX + rr, CY + rr), 180, 360, fill=1)
    for a in (30, 60, 90, 120, 150):
        d.line((CX, CY, *pol(a, R)), fill=1, width=1) if a == 90 else d.point(pol(a, R + 2), fill=1)
    for k in range(1, 6):                                  # fading trail
        if (fr - k) >= 0 and k % 2 == 0:
            d.line((CX, CY, *pol(sweep(fr - k), R)), fill=1)
    d.line((CX, CY, *pol(sweep(fr), R)), fill=1, width=2)
    al = alarm(fr)
    hit = last_hit(fr)
    if hit is not None and fr - hit < 30 and presence(fr) > 0.5:
        bx, by = pol(OBJ_ANGLE, R * OBJ_DIST / MAXCM)
        rr = 3 + (2 if (fr // 3) % 2 else 0)
        d.ellipse((bx - rr, by - rr, bx + rr, by + rr), fill=1)
    if al and (fr // 4) % 2 == 0:
        d.rectangle((0, 0, 127, 13), fill=1)
        d.text((64, 7), f"OBJECT {OBJ_DIST:.0f}cm!", font=f(10), fill=0, anchor="mm")
    elif not al:
        d.text((2, 1), "RADAR", font=f(9), fill=1)
        d.text((126, 1), f"{sweep(fr):3.0f}\N{DEGREE SIGN}", font=f(9), fill=1, anchor="ra")
        d.text((64, 9), "AREA CLEAR", font=f(8), fill=1, anchor="mt") if (fr // 12) % 2 == 0 else None
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
