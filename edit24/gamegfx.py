#!/usr/bin/env python3
"""Draws the Snake game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (Nokia-style
block snake with an eye, diamond apple, border, SCORE / HI bar, menu / 3-2-1 / GAME OVER / NEW BEST
pages) and draw_hd() = a crisp full-colour version of the same frame for the edit (checkered garden
lawn, hedge border, a cute green snake with eyes and a flicking tongue, shiny red apples)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, LEVELS, GW, GH, CELL, TOP, DIRS, HIGH_OLD,  # noqa: E402
                      game, phase, level, countdown, final_score)

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def cell_xy(c):
    return c[0] * CELL, TOP + c[1] * CELL


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    if ph == "title":
        d.text((64, 12), "SNAKE", font=fo(16), fill=1, anchor="mm")
        for i in range(10):                                         # wiggly title snake
            x = 24 + i * 8
            y = 38 + int(5 * math.sin(i * 0.9 + f * 0.4))
            d.rectangle((x, y, x + 6, y + 6), fill=1)
        d.rectangle((102, 36, 104, 38), fill=0)
        d.text((64, 56), "PRESS KNOB", font=fo(8, False), fill=1, anchor="mm")
        return im
    if ph == "menu":
        d.rectangle((0, 0, 127, 12), fill=1)
        d.text((64, 6), "SELECT SPEED", font=fo(9), fill=0, anchor="mm")
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
    d.text((1, -1), f"SCORE {g['eaten'] * 10:03d}", font=fo(7, False), fill=1)
    d.text((127, -1), f"HI {HIGH_OLD:03d}", font=fo(7, False), fill=1, anchor="ra")
    d.rectangle((0, TOP - 1, 127, 63), outline=1)
    ax, ay = cell_xy(g["apple"])                                      # diamond apple
    d.polygon([(ax + 2, ay), (ax + 4, ay + 2), (ax + 2, ay + 4), (ax, ay + 2)], fill=1)
    dead = g["state"] == "DEAD"
    blink = dead and (f // 4) % 2 == 1
    if not blink:
        for i, c in enumerate(g["body"]):
            x, y = cell_xy(c)
            d.rectangle((x, y, x + CELL - 2, y + CELL - 2), fill=1)
            if i == 0:
                d.point((x + 1, y + 1), fill=0)
    if ph in ("over", "best"):
        d.rectangle((18, 16, 109, 50), fill=0, outline=1)
        if ph == "over" or (f // 5) % 2 == 0:
            d.text((64, 26), "GAME OVER" if ph == "over" else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
        d.text((64, 41), f"SCORE {final_score()}", font=fo(8, False), fill=1, anchor="mm")
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
GRASS_A, GRASS_B = (150, 215, 80), (135, 200, 70)
HEDGE, HEDGE_D = (60, 140, 60), (35, 95, 40)
SNAKE, SNAKE_D, SNAKE_L = (60, 120, 230), (25, 60, 150), (130, 190, 255)
_BG = {}


def lawn(w, h):
    if (w, h) not in _BG:
        im = Image.new("RGB", (w, h), HEDGE)
        d = ImageDraw.Draw(im)
        sx, sy = w / GW, (h - h * TOP / 64) / GH
        oy = h * TOP / 64
        for gx in range(GW):
            for gy in range(GH):
                d.rectangle((gx * sx, oy + gy * sy, (gx + 1) * sx, oy + (gy + 1) * sy), fill=GRASS_A if (gx + gy) % 2 else GRASS_B)
        for k in range(0, w, 26):                                    # hedge bumps along the top bar
            d.ellipse((k - 6, oy - 26, k + 32, oy + 8), fill=HEDGE, outline=HEDGE_D, width=2)
        for k in range(14):                                          # little flowers
            fx_, fy_ = (k * 197) % w, oy + 20 + (k * 89) % int(h - oy - 40)
            for a in range(5):
                d.ellipse((fx_ + 7 * math.cos(a * 1.256) - 4, fy_ + 7 * math.sin(a * 1.256) - 4,
                           fx_ + 7 * math.cos(a * 1.256) + 4, fy_ + 7 * math.sin(a * 1.256) + 4), fill=(255, 255, 255))
            d.ellipse((fx_ - 4, fy_ - 4, fx_ + 4, fy_ + 4), fill=(255, 210, 40))
        _BG[(w, h)] = im
    return _BG[(w, h)].copy()


def apple_hd(d, cx, cy, r, f):
    bob = 0.08 * r * math.sin(f * 0.35)
    cy += bob
    d.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r), fill=(230, 40, 40), outline=(120, 10, 10), width=max(2, int(r * 0.12)))
    d.ellipse((cx - r * 0.55, cy - r * 0.55, cx - r * 0.15, cy - r * 0.15), fill=(255, 160, 160))
    d.line((cx, cy - r * 0.9, cx + r * 0.1, cy - r * 1.35), fill=(100, 60, 20), width=max(2, int(r * 0.15)))
    d.ellipse((cx + r * 0.1, cy - r * 1.45, cx + r * 0.75, cy - r * 1.05), fill=(80, 190, 60), outline=(30, 100, 30), width=2)


def draw_hd(f, w=1000, h=500, snake=True, zoom=2.0):
    """Game-cam view: the whole board drawn zoom x larger, then a w x h window that follows the head."""
    big = _draw_full(f, int(w * zoom), int(h * zoom), snake)
    if zoom == 1.0:
        return big
    g = game(f)
    if g and phase(f) not in ("title", "menu", "count"):
        sx = big.width / GW
        sy = (big.height - big.height * TOP / 64) / GH
        hx = (g["body"][0][0] + 0.5) * sx
        hy = big.height * TOP / 64 + (g["body"][0][1] + 0.5) * sy
    else:
        hx, hy = big.width / 2, big.height / 2
    x0 = int(min(max(hx - w / 2, 0), big.width - w))
    y0 = int(min(max(hy - h / 2, 0), big.height - h))
    return big.crop((x0, y0, x0 + w, y0 + h))


def _draw_full(f, w, h, snake):
    im = lawn(w, h)
    d = ImageDraw.Draw(im, "RGBA")
    sx, sy = w / GW, (h - h * TOP / 64) / GH
    oy = h * TOP / 64
    g = game(f)
    ph = phase(f)

    def ctr(c):
        return (c[0] + 0.5) * sx, oy + (c[1] + 0.5) * sy
    if g and ph not in ("title", "menu", "count"):
        ax, ay = ctr(g["apple"])
        apple_hd(d, ax, ay, sx * 0.42, f)
        dead = g["state"] == "DEAD"
        if snake:
            body = g["body"]
            n = len(body)
            r = sx * 0.46
            pts = [ctr(c) for c in body]
            d.line(pts, fill=SNAKE_D, width=int(r * 2.0) + 4, joint="curve")          # outline
            d.line(pts, fill=SNAKE, width=int(r * 2.0), joint="curve")
            for cx, cy in pts:
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=SNAKE)
            for i, (cx, cy) in enumerate(pts[1:], 1):                                 # yellow spots
                if i % 2 == 0:
                    d.ellipse((cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32), fill=(255, 210, 60))
            d.line(pts, fill=SNAKE_L + (90,), width=max(2, int(r * 0.35)), joint="curve")  # shine
            hx, hy = ctr(body[0])
            dx, dy = DIRS[g["dir"]]
            hr = r * 1.15
            if (f // 6) % 3 == 0 and not dead:                       # tongue flick
                tx, ty = hx + dx * hr * 1.5, hy + dy * hr * 1.5
                d.line((hx + dx * hr, hy + dy * hr, tx, ty), fill=(230, 40, 60), width=max(2, int(sx * 0.1)))
                d.line((tx, ty, tx + (dx - dy) * hr * 0.3, ty + (dy + dx) * hr * 0.3), fill=(230, 40, 60), width=max(2, int(sx * 0.08)))
                d.line((tx, ty, tx + (dx + dy) * hr * 0.3, ty + (dy - dx) * hr * 0.3), fill=(230, 40, 60), width=max(2, int(sx * 0.08)))
            d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=SNAKE, outline=SNAKE_D, width=3)
            px_, py_ = -dy, dx                                        # eyes sit sideways of the heading
            for sgn in (-1, 1):
                ex, ey = hx + dx * hr * 0.25 + sgn * px_ * hr * 0.45, hy + dy * hr * 0.25 + sgn * py_ * hr * 0.45
                er = hr * 0.33
                d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(255, 255, 255), outline=SNAKE_D, width=2)
                if dead:
                    d.line((ex - er * 0.6, ey - er * 0.6, ex + er * 0.6, ey + er * 0.6), fill=(20, 20, 30), width=3)
                    d.line((ex - er * 0.6, ey + er * 0.6, ex + er * 0.6, ey - er * 0.6), fill=(20, 20, 30), width=3)
                else:
                    d.ellipse((ex + dx * er * 0.35 - er * 0.45, ey + dy * er * 0.35 - er * 0.45,
                               ex + dx * er * 0.35 + er * 0.45, ey + dy * er * 0.35 + er * 0.45), fill=(20, 20, 30))
    return im


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
