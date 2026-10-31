#!/usr/bin/env python3
"""Draws the Brick Breaker game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (outlined
/ filled bricks, paddle, ball, SCORE / HI bar, menu / 3-2-1 / LEVEL CLEAR / NEW BEST pages) and
draw_hd() = a crisp colour version of the same frame for the edit (deep-space backdrop, glossy
rainbow bricks, chrome paddle, white ball that turns into a flaming FIREBALL, brick-burst particles)."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, LEVELS, ROWS, COLS, TOP, PAD_Y, PAD_W, PAD_H, BALL, HIGH_OLD, BW, BH,  # noqa: E402
                      brick_rect, game, phase, level, countdown, final_score)

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
ROW_COL = [(255, 70, 150), (255, 200, 40), (40, 220, 255)]


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    if ph == "title":
        d.text((64, 10), "BRICK", font=fo(13), fill=1, anchor="mm")
        d.text((64, 25), "BREAKER", font=fo(13), fill=1, anchor="mm")
        for c in range(6):
            d.rectangle((16 + c * 16, 36, 29 + c * 16, 40), fill=1 if (c + f // 6) % 2 else 0, outline=1)
        d.text((64, 56), "PRESS KNOB", font=fo(8, False), fill=1, anchor="mm")
        return im
    if ph == "menu":
        d.rectangle((0, 0, 127, 12), fill=1)
        d.text((64, 6), "SELECT LEVEL", font=fo(9), fill=0, anchor="mm")
        for i, lv in enumerate(LEVELS):
            y = 22 + i * 13
            if i == level(f):
                d.rectangle((24, y - 6, 103, y + 6), fill=1)
            d.text((64, y), lv, font=fo(10), fill=0 if i == level(f) else 1, anchor="mm")
        return im
    if ph == "count":
        d.text((64, 8), "GET READY!", font=fo(10), fill=1, anchor="mm")
        d.text((64, 38), str(countdown(f)), font=fo(30), fill=1, anchor="mm")
        return im
    d.text((1, -1), f"SCORE {g['score']:03d}", font=fo(7, False), fill=1)
    d.text((127, -1), f"HI {HIGH_OLD:03d}", font=fo(7, False), fill=1, anchor="ra")
    d.line((0, TOP - 1, 127, TOP - 1), fill=1)
    for (r, c) in g["bricks"]:
        x0, y0, x1, y1 = brick_rect(r, c)
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=1 if r != 1 else 0, outline=1)
    d.rectangle((g["px"] - PAD_W / 2, PAD_Y, g["px"] + PAD_W / 2, PAD_Y + PAD_H - 1), fill=1)
    d.rectangle((g["bx"], g["by"], g["bx"] + BALL - 1, g["by"] + BALL - 1), fill=1)
    if ph in ("clear", "best"):
        d.rectangle((14, 18, 113, 50), fill=0, outline=1)
        if ph == "clear" or (f // 5) % 2 == 0:
            d.text((64, 28), "LEVEL CLEAR!" if ph == "clear" else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
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


def space(w, h):
    if (w, h) not in _BG:
        im = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(im)
        for y in range(h):
            u = y / h
            d.line((0, y, w, y), fill=(int(20 + 30 * u), int(10 + 10 * u), int(50 + 40 * u)))
        rng = np.random.default_rng(3)
        for _ in range(140):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.8, 2.6)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230))
        neb = Image.new("RGB", (w, h))
        nd = ImageDraw.Draw(neb)
        nd.ellipse((-w * 0.2, h * 0.3, w * 0.6, h * 1.2), fill=(120, 40, 160))
        nd.ellipse((w * 0.5, -h * 0.3, w * 1.2, h * 0.6), fill=(30, 80, 170))
        im = Image.blend(im, Image.fromarray(np.maximum(np.asarray(im), np.asarray(neb.filter(ImageFilter.GaussianBlur(w // 8))))), 0.5)
        _BG[(w, h)] = im
    return _BG[(w, h)].copy()


def brick_hd(d, box, col, sc):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, int(sc * 0.9), fill=col, outline=tuple(int(v * 0.55) for v in col), width=max(2, int(sc * 0.3)))
    d.rounded_rectangle((x0 + sc * 0.6, y0 + sc * 0.5, x1 - sc * 0.6, y0 + (y1 - y0) * 0.38), int(sc * 0.5),
                        fill=tuple(min(255, int(v * 0.6 + 110)) for v in col))


def draw_hd(f, w=1000, h=500):
    sx, sy = w / 128, h / 64
    im = space(w, h).convert("RGBA")
    g = game(f)
    if not g:
        return im.convert("RGB")
    sharp = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(sharp)
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    for (r, c) in g["bricks"]:
        x0, y0, x1, y1 = brick_rect(r, c)
        brick_hd(d, (x0 * sx + 2, y0 * sy + 2, x1 * sx - 2, y1 * sy - 2), ROW_COL[r], sx)
    for k in range(0, 10):                                      # brick-burst particles
        pg = game(f - k)
        if pg and pg["hit_brick"]:
            r, c = pg["hit_brick"]
            x0, y0, x1, y1 = brick_rect(r, c)
            cx, cy = (x0 + x1) / 2 * sx, (y0 + y1) / 2 * sy
            for j in range(12):
                a = j * 2 * math.pi / 12 + r
                rr = 10 + k * 16
                s = max(3, int(15 - k))
                px_, py_ = cx + rr * math.cos(a), cy + rr * math.sin(a) + k * k * 1.2
                d.rectangle((px_ - s, py_ - s, px_ + s, py_ + s), fill=ROW_COL[r] + (int(255 * (1 - k / 10) ** 0.5),),
                            outline=(255, 255, 255, int(200 * (1 - k / 10))), width=2)
            if k < 3:                                         # white flash on the broken brick
                d.rounded_rectangle((x0 * sx, y0 * sy, x1 * sx, y1 * sy), int(sx), fill=(255, 255, 255, int(230 * (1 - k / 3))))
    px0, px1 = (g["px"] - PAD_W / 2) * sx, (g["px"] + PAD_W / 2) * sx
    pbox = (px0, PAD_Y * sy, px1, (PAD_Y + PAD_H) * sy + 4)
    gd.rounded_rectangle(pbox, 18, fill=(120, 200, 255, 255))
    d.rounded_rectangle(pbox, 18, fill=(200, 210, 230, 255), outline=(255, 255, 255, 255), width=3)
    d.rounded_rectangle((px0 + 10, PAD_Y * sy + 4, px1 - 10, PAD_Y * sy + 12), 6, fill=(255, 255, 255, 220))
    fire = g.get("fire")
    cx, cy = (g["bx"] + BALL / 2) * sx, (g["by"] + BALL / 2) * sy
    r = BALL * sx / 2 + 3
    for k in range(1, 8):                                       # trail (flames when fireball)
        pg = game(f - k)
        if pg and pg["state"] == "PLAY":
            tx, ty = (pg["bx"] + BALL / 2) * sx, (pg["by"] + BALL / 2) * sy
            rr = r * (1.25 if fire else 0.9) * (1 - k / 9)
            col = (255, 140 - k * 10, 30) if fire else (220, 230, 255)
            d.ellipse((tx - rr, ty - rr, tx + rr, ty + rr), fill=col + (int(220 * (1 - k / 8)),))
    gd.ellipse((cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2), fill=((255, 140, 30) if fire else (200, 220, 255)) + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=((255, 230, 120) if fire else (255, 255, 255)) + (255,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sharp)
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
