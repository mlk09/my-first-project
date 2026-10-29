#!/usr/bin/env python3
"""Draws the 2-player Pong game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (dashed
net, two paddles, ball, big scores, TUM / DOST labels, menu / 3-2-1 / WINNER pages) and draw_hd() = a
crisp neon-arcade colour version of the same frame for the edit (glowing court, cyan TUM paddle,
pink DOST paddle, white-hot ball with a motion trail, hit sparks)."""
import math
import os
import sys

import numpy as np

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, TOP, PH, PW, BALL, P1X, P2X, game, phase, countdown, mode  # noqa: E402

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    if ph == "title":
        d.text((64, 12), "PONG", font=fo(18), fill=1, anchor="mm")
        d.rectangle((6, 30, 8, 44), fill=1)
        d.rectangle((119, 34, 121, 48), fill=1)
        bx = 20 + (f * 3) % 90
        d.rectangle((bx, 38, bx + 2, 40), fill=1)
        d.text((64, 56), "2 KNOB = 2 PLAYER", font=fo(7, False), fill=1, anchor="mm")
        return im
    if ph == "menu":
        d.rectangle((0, 0, 127, 12), fill=1)
        d.text((64, 6), "SELECT MODE", font=fo(9), fill=0, anchor="mm")
        for i, m in enumerate(("1 PLAYER", "2 PLAYER")):
            y = 28 + i * 16
            if m == mode(f):
                d.rectangle((20, y - 7, 107, y + 7), fill=1)
            d.text((64, y), m, font=fo(10), fill=0 if m == mode(f) else 1, anchor="mm")
        return im
    if ph == "count":
        d.text((64, 8), "TUM  vs  DOST", font=fo(9), fill=1, anchor="mm")
        d.text((64, 38), str(countdown(f)), font=fo(30), fill=1, anchor="mm")
        return im
    d.text((40, 0), str(g["s1"]), font=fo(9), fill=1, anchor="ma")
    d.text((88, 0), str(g["s2"]), font=fo(9), fill=1, anchor="ma")
    d.text((2, 1), "TUM", font=fo(6, False), fill=1)
    d.text((126, 1), "DOST", font=fo(6, False), fill=1, anchor="ra")
    d.line((0, TOP, 127, TOP), fill=1)
    for y in range(TOP + 2, 64, 6):
        d.line((63, y, 63, y + 2), fill=1)
    d.rectangle((P1X, g["p1"], P1X + PW - 1, g["p1"] + PH - 1), fill=1)
    d.rectangle((P2X, g["p2"], P2X + PW - 1, g["p2"] + PH - 1), fill=1)
    if g["state"] == "RALLY" and -BALL < g["bx"] < 128:
        d.rectangle((g["bx"], g["by"], g["bx"] + BALL - 1, g["by"] + BALL - 1), fill=1)
    if ph == "win":
        d.rectangle((16, 18, 111, 52), fill=0, outline=1)
        if (f // 5) % 2 == 0:
            d.text((64, 28), "TUM JEETE!", font=fo(11), fill=1, anchor="mm")
        d.text((64, 43), f"{g['s1']} - {g['s2']}", font=fo(10), fill=1, anchor="mm")
    return im


def oled_png(f):
    im = draw_oled(f).convert("L")
    S = 8
    big = Image.new("RGB", (128 * S, 64 * S), (2, 3, 6))
    px = im.load()
    d = ImageDraw.Draw(big)
    for yy in range(64):
        for xx in range(128):
            if px[xx, yy]:
                d.rectangle((xx * S, yy * S, xx * S + S - 2, yy * S + S - 2), fill=(185, 235, 255))
    return big


# ------------------------------------------------------------------ HD neon version
C1, C2, CB = (40, 230, 255), (255, 60, 170), (255, 255, 255)
_BG = {}


def court(w, h):
    if (w, h) not in _BG:
        im = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(im)
        for y in range(h):
            u = y / h
            d.line((0, y, w, y), fill=(int(14 + 10 * u), int(10 + 8 * u), int(40 + 30 * u)))
        sx, sy = w / 128, h / 64
        for gx in range(0, 129, 8):                                # faint arcade grid
            d.line((gx * sx, TOP * sy, gx * sx, h), fill=(40, 34, 90))
        for gy in range(TOP, 65, 8):
            d.line((0, gy * sy, w, gy * sy), fill=(40, 34, 90))
        glow = Image.new("RGB", (w, h))
        gd = ImageDraw.Draw(glow)
        gd.rectangle((4, TOP * sy, w - 4, h - 4), outline=(160, 120, 255), width=8)
        for y in range(int(TOP * sy) + 8, h, int(6 * sy)):
            gd.rectangle((w / 2 - 5, y, w / 2 + 5, y + 3 * sy), fill=(200, 200, 255))
        a = np.asarray(im).astype(np.float32)
        gl = np.asarray(glow.filter(ImageFilter.GaussianBlur(12))).astype(np.float32) * 1.4
        im = Image.fromarray(np.clip(np.maximum(a, np.asarray(glow) * 0.8) + gl, 0, 255).astype(np.uint8))
        _BG[(w, h)] = im
    return _BG[(w, h)].copy()


def draw_hd(f, w=1000, h=500):
    sx, sy = w / 128, h / 64
    im = court(w, h).convert("RGBA")
    g = game(f)
    if not g:
        return im.convert("RGB")
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    sharp = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(sharp)
    for side, x, y, col in ((1, P1X, g["p1"], C1), (2, P2X, g["p2"], C2)):
        box = (x * sx - 4, y * sy, (x + PW) * sx + 4, (y + PH) * sy)
        gd.rounded_rectangle(box, 14, fill=col + (255,))
        d.rounded_rectangle(box, 14, fill=col + (255,), outline=(255, 255, 255, 200), width=3)
    if g["state"] == "RALLY":
        for k in range(1, 7):                                        # motion trail
            pg = game(f - k)
            if pg and pg["state"] == "RALLY":
                r = (BALL * sx / 2) * (1 - k / 8)
                cx, cy = (pg["bx"] + BALL / 2) * sx, (pg["by"] + BALL / 2) * sy
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 240, 160, int(160 * (1 - k / 7))))
        cx, cy = (g["bx"] + BALL / 2) * sx, (g["by"] + BALL / 2) * sy
        r = BALL * sx / 2 + 2
        gd.ellipse((cx - r * 1.6, cy - r * 1.6, cx + r * 1.6, cy + r * 1.6), fill=(255, 230, 120, 255))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CB + (255,))
    for k in range(0, 8):                                            # hit sparks
        pg = game(f - k)
        if pg and pg["hit"]:
            col = C1 if pg["hit"] == 1 else C2
            x0 = (P1X + PW) * sx if pg["hit"] == 1 else P2X * sx
            y0 = (pg["by"] + BALL / 2) * sy
            for j in range(10):
                a = (j / 10) * math.pi - math.pi / 2 + (0 if pg["hit"] == 1 else math.pi)
                rr = 10 + k * 9
                d.line((x0 + rr * 0.5 * math.cos(a), y0 + rr * 0.5 * math.sin(a), x0 + rr * math.cos(a), y0 + rr * math.sin(a)),
                       fill=col + (int(255 * (1 - k / 8)),), width=4)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sharp)
    d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(MONT, int(9 * sy))
    d.text((w * 0.4, TOP * sy / 2 + 2), str(g["s1"]), font=fnt, fill=C1, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((w * 0.6, TOP * sy / 2 + 2), str(g["s2"]), font=fnt, fill=C2, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    lab = ImageFont.truetype(MONT, int(4.2 * sy))
    d.text((16, TOP * sy / 2 + 2), "TUM", font=lab, fill=C1, anchor="lm")
    d.text((w - 16, TOP * sy / 2 + 2), "DOST", font=lab, fill=C2, anchor="rm")
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
