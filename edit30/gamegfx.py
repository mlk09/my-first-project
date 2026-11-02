#!/usr/bin/env python3
"""Draws the Car Racing game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (scrolling lane
dashes, player car, outlined traffic, coins, nitro flames, chequered finish, SCORE / HI bar, nitro meter)
and draw_hd() = a crisp colour version for the edit (neon night highway, glossy top-down cars, glowing
coins, blue nitro flames + speed lines, chequered finish arch, sparks on close calls)."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, SHOTS, TOP, LANES, ROAD_Y0, LANE_H, PX, CAR_W, CAR_H, HIGH_OLD, COIN_COL, FINISH,  # noqa: E402
                      game, final_score, DODGE)

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
CAR_COLS = [(60, 140, 255), (40, 220, 140), (255, 140, 30), (170, 80, 255), (255, 230, 60)]
PLAYER = (255, 40, 70)
ROAD_Y1 = ROAD_Y0 + LANES * LANE_H


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    g = game(f)
    d.text((1, -1), f"SCORE {g['score']:04d}", font=fo(7, False), fill=1)
    d.text((127, -1), f"HI {HIGH_OLD}", font=fo(7, False), fill=1, anchor="ra")
    for k in range(COIN_COL):                                     # nitro meter
        x = 62 + k * 6
        d.rectangle((x, 1, x + 4, 5), fill=1 if g["meter"] > k or g["nitro"] else 0, outline=1)
    d.line((0, ROAD_Y0 - 1, 127, ROAD_Y0 - 1), fill=1)
    d.line((0, ROAD_Y1, 127, ROAD_Y1), fill=1)
    off = g["dist"] % 16
    for l in range(1, LANES):
        y = ROAD_Y0 + l * LANE_H
        for x in range(-16, 140, 16):
            d.line((x - off, y, x - off + 7, y), fill=1)
    fx = g["finish_x"]
    if -8 < fx < 136:
        for j in range(ROAD_Y0, ROAD_Y1, 3):
            for i in range(2):
                if (j // 3 + i) % 2 == 0:
                    d.rectangle((fx + i * 3, j, fx + i * 3 + 2, j + 2), fill=1)
    for (x, y) in g["coins"]:
        d.ellipse((x + 4, y - 3, x + 10, y + 3), outline=1)
        d.point((x + 7, y), fill=1)
    for (x, y, _) in g["cars"]:
        d.rounded_rectangle((x, y - CAR_H / 2, x + CAR_W - 1, y + CAR_H / 2 - 1), 2, outline=1)
        d.rectangle((x + 4, y - 2, x + 7, y + 1), fill=1)
    y = g["py"]
    d.rounded_rectangle((PX, y - CAR_H / 2, PX + CAR_W - 1, y + CAR_H / 2 - 1), 2, fill=1)
    d.rectangle((PX + 9, y - 2, PX + 11, y + 1), fill=0)
    if g["nitro"] and (f // 2) % 2 == 0:
        d.polygon([(PX - 1, y - 2), (PX - 8, y), (PX - 1, y + 2)], fill=1)
    if FINISH <= f < SHOTS[5]:
        d.rectangle((24, 20, 103, 50), fill=0, outline=1)
        d.text((64, 29), "FINISH!" if f < FINISH + 14 or (f // 5) % 2 == 0 else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
        d.text((64, 42), f"SCORE {final_score()}", font=fo(8, False), fill=1, anchor="mm")
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


# ------------------------------------------------------------------ HD colour version
_BG = {}


def road(w, h):
    if (w, h) not in _BG:
        sy = h / 64
        im = Image.new("RGB", (w, h), (10, 8, 30))
        d = ImageDraw.Draw(im)
        for y in range(int(ROAD_Y0 * sy)):
            u = y / (ROAD_Y0 * sy)
            d.line((0, y, w, y), fill=(int(40 + 60 * u), int(10 + 20 * u), int(70 + 40 * u)))
        for y in range(int(ROAD_Y1 * sy), h):
            u = (y - ROAD_Y1 * sy) / (h - ROAD_Y1 * sy + 1)
            d.line((0, y, w, y), fill=(int(20 + 10 * u), int(60 - 20 * u), int(50 - 10 * u)))
        rng = np.random.default_rng(7)
        a = np.asarray(im).astype(np.float32)
        y0, y1 = int(ROAD_Y0 * sy), int(ROAD_Y1 * sy)
        a[y0:y1] = np.array((34, 36, 48), np.float32) + rng.normal(0, 5, (y1 - y0, w, 1))
        _BG[(w, h)] = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    return _BG[(w, h)].copy()


def car_hd(d, gd, x, y, w, h, col, player=False):
    dark = tuple(int(v * 0.45) for v in col)
    hi = tuple(min(255, int(v * 0.5 + 130)) for v in col)
    d.rounded_rectangle((x + 4, y + 6, x + w + 4, y + h + 6), int(h * 0.35), fill=(0, 0, 0, 110))   # shadow
    if player:
        gd.rounded_rectangle((x - 6, y - 6, x + w + 6, y + h + 6), int(h * 0.4), fill=col + (255,))
    d.rounded_rectangle((x, y, x + w, y + h), int(h * 0.38), fill=col + (255,), outline=dark + (255,), width=4)
    d.rounded_rectangle((x + w * 0.55, y + h * 0.16, x + w * 0.78, y + h * 0.84), int(h * 0.15), fill=(30, 40, 60, 255))  # windshield
    d.rounded_rectangle((x + w * 0.2, y + h * 0.2, x + w * 0.48, y + h * 0.8), int(h * 0.15), fill=hi + (255,))         # roof
    if player:
        d.rectangle((x + w * 0.05, y + h * 0.42, x + w * 0.95, y + h * 0.58), fill=(255, 255, 255, 235))               # racing stripe
    for wy in (y - h * 0.08, y + h * 0.88):                                                                            # wheels
        for wx in (x + w * 0.15, x + w * 0.68):
            d.rounded_rectangle((wx, wy, wx + w * 0.2, wy + h * 0.2), 4, fill=(15, 15, 20, 255))
    d.ellipse((x + w - 10, y + h * 0.1, x + w, y + h * 0.3), fill=(255, 250, 200, 255))                              # headlights
    d.ellipse((x + w - 10, y + h * 0.7, x + w, y + h * 0.9), fill=(255, 250, 200, 255))
    gd.ellipse((x + w - 14, y + h * 0.05, x + w + 30, y + h * 0.95), fill=(255, 240, 180, 120))


def draw_hd(f, w=1000, h=500):
    sx, sy = w / 128, h / 64
    im = road(w, h).convert("RGBA")
    g = game(f)
    if not g:
        return im.convert("RGB")
    sharp = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(sharp)
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    off = g["dist"] * sx
    y0, y1 = ROAD_Y0 * sy, ROAD_Y1 * sy
    for k in range(-1, 14):                                   # roadside neon posts (top) + trees (bottom)
        x = (k * 90 - off * 0.9) % (w + 180) - 90
        gd.rectangle((x, y0 - 30, x + 10, y0 - 6), fill=(255, 60, 200, 255) if k % 2 else (60, 220, 255, 255))
        d.rectangle((x + 2, y0 - 28, x + 8, y0 - 8), fill=(255, 255, 255, 230))
        tx = (k * 110 - off) % (w + 220) - 110
        d.ellipse((tx, y1 + 12, tx + 46, y1 + 58), fill=(30, 140, 70, 255), outline=(20, 90, 50, 255), width=3)
    gd.line((0, y0, w, y0), fill=(60, 220, 255, 255), width=10)
    gd.line((0, y1, w, y1), fill=(255, 60, 200, 255), width=10)
    d.line((0, y0, w, y0), fill=(200, 250, 255, 255), width=4)
    d.line((0, y1, w, y1), fill=(255, 200, 240, 255), width=4)
    dash = 16 * sx
    for l in range(1, LANES):
        yy = (ROAD_Y0 + l * LANE_H) * sy
        x = -(off % dash) - dash
        while x < w:
            d.rounded_rectangle((x, yy - 3, x + dash * 0.5, yy + 3), 3, fill=(235, 235, 240, 230))
            x += dash
    fxh = g["finish_x"] * sx                                   # chequered finish band + arch
    if -60 < fxh < w + 60:
        c = int((y1 - y0) / 12)
        for j in range(12):
            for i in range(3):
                col = (250, 250, 250, 255) if (i + j) % 2 == 0 else (20, 20, 24, 255)
                d.rectangle((fxh + i * c, y0 + j * c, fxh + (i + 1) * c, y0 + (j + 1) * c), fill=col)
        gd.rectangle((fxh - 10, 0, fxh + 3 * c + 10, y0), fill=(255, 220, 40, 200))
        d.rounded_rectangle((fxh - 30, 6, fxh + 3 * c + 30, y0 - 6), 10, fill=(255, 200, 30, 255), outline=(255, 255, 255, 255), width=3)
        d.text((fxh + 1.5 * c, (6 + y0 - 6) / 2), "FINISH", font=fo(int(y0 * 0.42)), fill=(30, 20, 0, 255), anchor="mm")
    for (x, y) in g["coins"]:
        cx, cy, r = (x + 7) * sx, y * sy, 3.6 * sx
        gd.ellipse((cx - r * 1.6, cy - r * 1.6, cx + r * 1.6, cy + r * 1.6), fill=(255, 210, 40, 255))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 205, 40, 255), outline=(170, 100, 0, 255), width=4)
        d.text((cx, cy), "$", font=fo(int(r * 1.2)), fill=(150, 80, 0, 255), anchor="mm")
    for (x, y, ci) in g["cars"]:
        car_hd(d, gd, x * sx, (y - CAR_H / 2) * sy, CAR_W * sx, CAR_H * sy, CAR_COLS[ci])
    py = g["py"]
    if g["nitro"]:                                             # blue nitro flames + speed lines
        for k in range(5):
            fl = (70 + 30 * ((f + k) % 3)) * (1 - k * 0.1)
            fy = py * sy + (k - 2) * 9
            gd.ellipse((PX * sx - fl * 1.5, fy - 20, PX * sx + 10, fy + 20), fill=(60, 140, 255, 255))
            d.ellipse((PX * sx - fl, fy - 10, PX * sx + 6, fy + 10), fill=(120, 200, 255, 255))
            d.ellipse((PX * sx - fl * 0.5, fy - 5, PX * sx + 6, fy + 5), fill=(240, 250, 255, 255))
        rng = np.random.default_rng(f)
        for k in range(16):
            yy = rng.uniform(y0, y1)
            xx = rng.uniform(0, w)
            d.line((xx, yy, xx + rng.uniform(80, 200), yy), fill=(255, 255, 255, 150), width=3)
    car_hd(d, gd, PX * sx, (py - CAR_H / 2) * sy, CAR_W * sx, CAR_H * sy, PLAYER, player=True)
    for k in range(0, 8):                                      # close-call sparks
        if any(fp == f - k for fp, _ in DODGE):
            cx, cy = (PX + CAR_W * 0.5) * sx, py * sy
            for j in range(10):
                a = j * 2 * math.pi / 10 + k
                rr = 30 + k * 18
                d.line((cx + rr * math.cos(a), cy + rr * math.sin(a), cx + (rr + 22) * math.cos(a), cy + (rr + 22) * math.sin(a)),
                       fill=(255, 230, 80, int(255 * (1 - k / 8))), width=5)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(sharp)
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
