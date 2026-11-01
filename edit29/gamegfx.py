#!/usr/bin/env python3
"""Draws the Space Invaders game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (pixel
aliens with a 2-frame march, laser ship, bullets, zig-zag bombs, SCORE / HI bar, menu / 3-2-1 /
WAVE CLEAR / NEW BEST pages) and draw_hd() = a crisp colour version of the same frame for the edit
(deep-space backdrop, neon rainbow pixel aliens with glow, glowing laser ship, cyan laser bolts that
turn into a pink TRIPLE LASER, red bombs, pixel-burst explosions)."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, LEVELS, ROWS, TOP, SHIP_Y, SHIP_W, HIGH_OLD, AW, AH,  # noqa: E402
                      alien_rect, game, phase, level, countdown, final_score)

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
ROW_COL = [(255, 70, 190), (255, 210, 40), (40, 230, 255)]
SHIP_COL = (90, 255, 140)

SPR = [
    (["...####...", ".########.", "##.####.##", "##########", "..##..##..", ".##.##.##.", "##......##"],
     ["...####...", ".########.", "##.####.##", "##########", "..##..##..", ".#..##..#.", "..#....#.."]),
    (["..#....#..", "...#..#...", "..######..", ".##.##.##.", "##########", "#.######.#", "#.#....#.#"],
     ["..#....#..", "#..#..#..#", "#.######.#", "###.##.###", "##########", "..######..", ".#......#."]),
    (["....##....", "...####...", "..######..", ".##.##.##.", "##########", "..#.##.#..", ".#.#..#.#."],
     ["....##....", "...####...", "..######..", ".##.##.##.", "##########", ".#..##..#.", "#.#....#.#"]),
]
SHIP = [".....#.....", "....###....", "..#######..", ".#########.", "###########", "###########"]


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def anim(f):
    return (f // 6) % 2


def blit(d, rows, x0, y0, fill=1):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                d.point((int(round(x0)) + i, int(round(y0)) + j), fill=fill)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    if ph == "title":
        d.text((64, 9), "SPACE", font=fo(13), fill=1, anchor="mm")
        d.text((64, 24), "INVADERS", font=fo(13), fill=1, anchor="mm")
        for c in range(3):
            blit(d, SPR[c][anim(f)], 30 + c * 26, 33)
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
    for (r, c) in g["aliens"]:
        x0, y0, _, _ = alien_rect(r, c, g["ox"], g["oy"])
        blit(d, SPR[r][anim(f)], x0, y0)
    if g["hit_xy"]:
        x, y = g["hit_xy"]
        for a in range(8):
            d.point((x + 5 * math.cos(a * 0.785), y + 4 * math.sin(a * 0.785)), fill=1)
    for (bx, by, _) in g["bullets"]:
        d.line((bx, by, bx, by + 3), fill=1)
    for (x, y) in g["bombs"]:
        d.line((x, y, x + 1, y + 1, x, y + 2, x + 1, y + 3), fill=1)
    blit(d, SHIP, g["px"] - SHIP_W / 2, SHIP_Y)
    d.line((0, 63, 127, 63), fill=1)
    if ph in ("clear", "best"):
        d.rectangle((14, 18, 113, 50), fill=0, outline=1)
        if ph == "clear" or (f // 5) % 2 == 0:
            d.text((64, 28), "WAVE CLEAR!" if ph == "clear" else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
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
            d.line((0, y, w, y), fill=(int(8 + 22 * u), int(6 + 14 * u), int(30 + 40 * u)))
        rng = np.random.default_rng(5)
        for _ in range(150):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.8, 2.6)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230))
        neb = Image.new("RGB", (w, h))
        nd = ImageDraw.Draw(neb)
        nd.ellipse((-w * 0.2, -h * 0.2, w * 0.5, h * 0.7), fill=(30, 110, 160))
        nd.ellipse((w * 0.55, h * 0.2, w * 1.25, h * 1.2), fill=(150, 40, 150))
        im = Image.blend(im, Image.fromarray(np.maximum(np.asarray(im), np.asarray(neb.filter(ImageFilter.GaussianBlur(w // 8))))), 0.5)
        # planet horizon at the bottom
        pl = Image.new("RGBA", (w, h))
        ImageDraw.Draw(pl).ellipse((-w * 0.3, h * 0.93, w * 1.3, h * 1.9), fill=(40, 200, 120, 90))
        im = im.convert("RGBA")
        im.alpha_composite(pl.filter(ImageFilter.GaussianBlur(6)))
        _BG[(w, h)] = im.convert("RGB")
    return _BG[(w, h)].copy()


def sprite_hd(d, gd, rows, x0, y0, sx, sy, col):
    hi = tuple(min(255, int(v * 0.5 + 128)) for v in col)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                bx, by = x0 + i * sx, y0 + j * sy
                gd.rectangle((bx, by, bx + sx, by + sy), fill=col + (255,))
                d.rounded_rectangle((bx + 1, by + 1, bx + sx - 1, by + sy - 1), max(2, int(sx * 0.25)), fill=col + (255,))
                d.rectangle((bx + sx * 0.2, by + sy * 0.15, bx + sx * 0.6, by + sy * 0.4), fill=hi + (255,))


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
    for (r, c) in g["aliens"]:
        x0, y0, _, _ = alien_rect(r, c, g["ox"], g["oy"])
        sprite_hd(d, gd, SPR[r][anim(f)], x0 * sx, y0 * sy, sx, sy, ROW_COL[r])
    for k in range(0, 10):                                      # pixel-burst explosions
        pg = game(f - k)
        if pg and pg["hit_brick"]:
            r = pg["hit_brick"][0]
            cx, cy = pg["hit_xy"][0] * sx, pg["hit_xy"][1] * sy
            for j in range(14):
                a = j * 2 * math.pi / 14 + r
                rr = 8 + k * 15
                s = max(3, int(14 - k))
                px_, py_ = cx + rr * math.cos(a), cy + rr * math.sin(a) + k * k
                d.rectangle((px_ - s, py_ - s, px_ + s, py_ + s), fill=ROW_COL[r] + (int(255 * (1 - k / 10) ** 0.5),),
                            outline=(255, 255, 255, int(200 * (1 - k / 10))), width=2)
            if k < 3:                                          # white flash star
                rr = (AW * sx * 0.8) * (1 - k * 0.28)
                a_ = 255
                d.polygon([(cx + rr * math.cos(t * math.pi / 4) * (1 if t % 2 == 0 else 0.35),
                            cy + rr * math.sin(t * math.pi / 4) * (1 if t % 2 == 0 else 0.35)) for t in range(8)],
                          fill=(255, 255, 255, a_))
                d.ellipse((cx - rr * 0.3, cy - rr * 0.3, cx + rr * 0.3, cy + rr * 0.3), fill=tuple(min(255, v + 120) for v in ROW_COL[r]) + (255,))
                gd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=ROW_COL[r] + (a_,))
    fire = g.get("fire")
    lc = (255, 90, 200) if fire else (90, 240, 255)
    for (bx, by, vx) in g["bullets"]:                           # laser bolts (fat glowing capsules)
        x, y0 = bx * sx, by * sy
        x1, y1 = x - vx * sx * 1.4, y0 + 6 * sy
        gd.line((x, y0, x1, y1), fill=lc + (255,), width=int(sx * 3.6))
        d.line((x, y0, x1, y1), fill=lc + (255,), width=int(sx * 1.6))
        d.line((x, y0 + 2, x1, y1 - 2), fill=(255, 255, 255, 255), width=max(3, int(sx * 0.7)))
    for (x, y) in g["bombs"]:                                    # zig-zag bombs
        pts = [(x * sx + (sx if i % 2 else -sx) * 1.1, (y + i * 1.1) * sy) for i in range(5)]
        gd.line(pts, fill=(255, 60, 40, 255), width=int(sx * 2.4))
        d.line(pts, fill=(255, 120, 60, 255), width=int(sx * 1.1))
        d.line(pts, fill=(255, 240, 180, 255), width=max(2, int(sx * 0.4)))
    shx = (g["px"] - SHIP_W / 2) * sx
    if g["hit_pad"]:                                             # muzzle flash
        cx = g["px"] * sx
        gd.ellipse((cx - sx * 3, SHIP_Y * sy - sx * 3, cx + sx * 3, SHIP_Y * sy + sx * 2), fill=lc + (255,))
    sprite_hd(d, gd, SHIP, shx, SHIP_Y * sy, sx, sy * 0.95, (255, 120, 220) if fire else SHIP_COL)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(sharp)
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
