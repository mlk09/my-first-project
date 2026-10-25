#!/usr/bin/env python3
"""SH1106 OLED frames for the ESP32 joystick robot arm (own design, 128x64 1-bit): four servo bars
(BASE / SHLD / ELBW / GRIP) with angles, a joystick box with a live dot, and a status line
(READY / MOVING / GRAB! / HOLDING / DROP!) that inverts on GRAB / DROP. Upscaled 8x with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, ik, joystick, status  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz):
    return ImageFont.truetype(MONO, sz)


def servo_vals(fr):
    yaw, a1, a2, wr, grip = ik(fr)
    return [("BASE", 90 + yaw), ("SHLD", a1), ("ELBW", 180 + a2), ("GRIP", 30 + 60 * grip)]


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    st = status(fr)
    inv = st in ("GRAB!", "DROP!") and (fr // 3) % 2 == 0
    if inv:
        d.rectangle((0, 0, 127, 11), fill=1)
    d.text((2, 1), "ROBOT ARM", font=f(9), fill=0 if inv else 1)
    d.text((126, 1), st, font=f(9), fill=0 if inv else 1, anchor="ra")
    for i, (lab, v) in enumerate(servo_vals(fr)):
        y = 15 + i * 12
        d.text((1, y), lab, font=f(8), fill=1)
        d.rectangle((27, y + 1, 79, y + 8), outline=1)
        d.rectangle((27, y + 1, 27 + int(52 * max(0, min(180, v)) / 180), y + 8), fill=1)
        d.text((97, y), f"{v:3.0f}", font=f(8), fill=1, anchor="ra")
    jx, jy, pr = joystick(fr)                              # joystick box
    d.rectangle((101, 15, 126, 61), outline=1)
    d.line((113, 17, 113, 59), fill=1)
    d.line((103, 38, 124, 38), fill=1)
    cx, cy = 113 + int(10 * jx), 38 - int(19 * jy)
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=1 if not pr else 0, outline=1)
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
