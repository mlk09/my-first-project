#!/usr/bin/env python3
"""Draws the Chrome Dino game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (pixel
T-rex with running legs, cacti, pterodactyl, dotted ground, 5-digit score + HI, menu / 3-2-1 /
GAME OVER / NEW BEST pages, inverted night mode) and draw_hd() = a crisp full-colour version of the
same frame for the edit (desert sky that turns to a starry night, sun / moon, dunes, green cacti,
purple pterodactyl, a cute green T-rex)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, LEVELS, GROUND, DINO_X, DINO_W, DINO_H, SIZES, BIRD_Y, HIGH_OLD,  # noqa: E402
                      game, phase, level, countdown, final_score, night)

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
# 14 x 16 T-rex (chrome style), '#' = pixel; legs drawn separately
DINO = ["......########",
        ".....##.######",
        ".....#########",
        ".....#########",
        ".....#####....",
        ".....#######..",
        "#...#####.....",
        "#..#######....",
        "##########....",
        "#########.#...",
        ".########.....",
        "..######......",
        "...####.......",
        "...#..#......."]


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def dino_1bit(d, x, y, frame, dead, fill=1):
    for r, row in enumerate(DINO):
        for c, ch in enumerate(row):
            if ch == "#":
                d.point((x + c, y + r), fill=fill)
    if dead:
        d.point((x + 7, y + 1), fill=fill)                      # X eye
        d.rectangle((x + 6, y + 1, x + 8, y + 1), fill=1 - fill)
        d.point((x + 7, y + 1), fill=fill)
    lp = (frame // 3) % 2                                       # running legs
    d.line((x + 3, y + 14, x + 3, y + 15 - lp), fill=fill)
    d.line((x + 6, y + 14, x + 6, y + 14 + lp), fill=fill)


def cactus_1bit(d, x, kind, fill=1):
    w, h = SIZES[kind]
    parts = [(x, w)] if kind != "c3" else [(x, 6), (x + 8, 7)]
    for px, pw in parts:
        cx = px + pw // 2
        d.rectangle((cx - 1, GROUND - h, cx + 1, GROUND), fill=fill)
        d.line((px, GROUND - h + 5, px, GROUND - h + 9), fill=fill)
        d.line((px, GROUND - h + 9, cx, GROUND - h + 9), fill=fill)
        d.line((px + pw - 1, GROUND - h + 3, px + pw - 1, GROUND - h + 7), fill=fill)
        d.line((cx, GROUND - h + 7, px + pw - 1, GROUND - h + 7), fill=fill)


def bird_1bit(d, x, f, fill=1):
    y = BIRD_Y
    d.rectangle((x + 3, y - 1, x + 12, y + 1), fill=fill)
    d.line((x, y, x + 3, y - 1), fill=fill)
    up = (f // 5) % 2
    d.line((x + 6, y, x + 9, y - 5 if up else y + 5), fill=fill)
    d.line((x + 7, y, x + 10, y - 4 if up else y + 4), fill=fill)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    if ph == "title":
        d.text((64, 10), "CHROME DINO", font=fo(11), fill=1, anchor="mm")
        dino_1bit(d, 57, 22, f, False)
        d.line((10, 39, 118, 39), fill=1)
        d.text((64, 52), "PRESS KNOB", font=fo(8, False), fill=1, anchor="mm")
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
    dead = g["state"] == "DEAD"
    if ph == "hook" and f < 14:                                 # 'no internet' card
        d.text((64, 14), "No internet", font=fo(11), fill=1, anchor="mm")
        for k in range(3):
            r = 6 + k * 5
            d.arc((64 - r, 40 - r, 64 + r, 40 + r), 225, 315, fill=1, width=2)
        d.line((52, 26, 76, 44), fill=1, width=2)
        return im
    for x, kind in g["obs"]:
        if kind == "bird":
            bird_1bit(d, int(x), f)
        else:
            cactus_1bit(d, int(x), kind)
    d.line((0, GROUND, 127, GROUND), fill=1)
    off = int(g["k"] * 2.8) % 9
    for x in range(-off, 128, 9):
        d.point((x, GROUND + 3), fill=1)
        d.point((x + 4, GROUND + 5), fill=1)
    dino_1bit(d, DINO_X, int(GROUND - DINO_H + 2 + g["dino_y"]), f, dead)
    d.text((126, 1), f"HI {HIGH_OLD:05d}  {g['dist']:05d}", font=fo(7, False), fill=1, anchor="ra")
    if ph in ("over", "best"):
        d.rectangle((14, 12, 113, 44), fill=0, outline=1)
        if ph == "over" or (f // 5) % 2 == 0:
            d.text((64, 22), "GAME OVER" if ph == "over" else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
        d.text((64, 36), f"SCORE {final_score()}", font=fo(8, False), fill=1, anchor="mm")
    if night(f) > 0.5 and ph != "hook":
        im = Image.eval(im, lambda v: 1 - v)                     # night mode = inverted, like Chrome
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
def lerp(a, b, u):
    return tuple(int(x + (y - x) * u) for x, y in zip(a, b))


def trex_hd(w, frame, dead=False, jumping=False):
    """Cute green T-rex sprite (RGBA, w x w)."""
    s = 4
    W = int(w * s)
    im = Image.new("RGBA", (W, W))
    d = ImageDraw.Draw(im)
    o = max(2, int(w * 0.035 * s))
    G, GD, BL = (90, 200, 90), (40, 110, 50), (35, 30, 30)
    lp = 0 if (jumping or dead) else (frame // 3) % 2
    d.polygon([(W * 0.02, W * 0.5), (W * 0.3, W * 0.4), (W * 0.34, W * 0.66), (W * 0.1, W * 0.62)], fill=G, outline=BL)  # tail
    for i, (lx, up) in enumerate(((0.3, lp), (0.5, 1 - lp))):          # thick legs + feet
        ly = W * (0.86 - 0.06 * up)
        d.rounded_rectangle((W * lx, W * 0.66, W * (lx + 0.13), ly), o * 2, fill=G, outline=BL, width=o)
        d.rounded_rectangle((W * (lx - 0.01), ly - W * 0.04, W * (lx + 0.2), ly + W * 0.05), o * 2, fill=G, outline=BL, width=o)
    d.ellipse((W * 0.14, W * 0.32, W * 0.72, W * 0.82), fill=G, outline=BL, width=o)                 # body
    d.ellipse((W * 0.3, W * 0.48, W * 0.62, W * 0.78), fill=(190, 240, 160))                     # belly
    d.rounded_rectangle((W * 0.46, W * 0.04, W * 0.98, W * 0.42), int(W * 0.1), fill=G, outline=BL, width=o)  # head
    d.rounded_rectangle((W * 0.5, W * 0.26, W * 0.97, W * 0.4), int(W * 0.05), fill=(190, 240, 160))
    for k in range(4):                                                                         # teeth
        tx = W * (0.62 + k * 0.08)
        d.polygon([(tx, W * 0.3), (tx + W * 0.03, W * 0.35), (tx + W * 0.06, W * 0.3)], fill=(255, 255, 255))
    ex, ey, er = W * 0.72, W * 0.16, W * 0.075
    if dead:
        d.line((ex - er, ey - er, ex + er, ey + er), fill=BL, width=o * 2)
        d.line((ex - er, ey + er, ex + er, ey - er), fill=BL, width=o * 2)
    else:
        d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(255, 255, 255), outline=BL, width=o)
        d.ellipse((ex - er * 0.2, ey - er * 0.5, ex + er * 0.6, ey + er * 0.4), fill=BL)
    d.rounded_rectangle((W * 0.6, W * 0.46, W * 0.76, W * 0.54), o * 2, fill=G, outline=BL, width=o)        # arm
    for k in range(4):                                                                         # back spikes
        sx = W * (0.2 + k * 0.08)
        d.polygon([(sx, W * (0.4 - 0.02 * k)), (sx + W * 0.04, W * (0.3 - 0.02 * k)), (sx + W * 0.08, W * (0.38 - 0.02 * k))],
                  fill=(255, 140, 60), outline=BL)
    return im.resize((int(w), int(w)), Image.LANCZOS)


def cactus_hd(d, x0, ybase, w, h, sc):
    G, GD, BL = (70, 170, 70), (40, 120, 50), (25, 60, 30)
    cw = w * 0.38
    cx = x0 + w / 2
    d.rounded_rectangle((cx - cw / 2, ybase - h, cx + cw / 2, ybase), int(cw / 2), fill=G, outline=BL, width=int(0.35 * sc))
    for side in (-1, 1):
        ay = ybase - h * (0.55 if side < 0 else 0.7)
        ax = cx + side * w * 0.42
        d.rounded_rectangle((min(cx, ax) - cw * 0.3, ay, max(cx, ax) + cw * 0.3, ay + cw * 0.6), int(cw * 0.3), fill=G, outline=BL, width=int(0.3 * sc))
        d.rounded_rectangle((ax - cw * 0.3, ay - h * 0.25, ax + cw * 0.3, ay + cw * 0.6), int(cw * 0.3), fill=G, outline=BL, width=int(0.3 * sc))
    d.line((cx - cw * 0.1, ybase - h * 0.9, cx - cw * 0.1, ybase - h * 0.1), fill=GD, width=max(2, int(0.25 * sc)))


def ptero_hd(d, x, y, sc, f):
    P, PD, BL = (170, 110, 220), (120, 70, 170), (40, 25, 50)
    up = (f // 5) % 2
    w = 14 * sc
    d.polygon([(x + w * 0.35, y), (x + w * 0.6, y - (w * 0.5 if up else -w * 0.45)), (x + w * 0.75, y)], fill=PD, outline=BL)
    d.ellipse((x + w * 0.2, y - w * 0.12, x + w * 0.85, y + w * 0.12), fill=P, outline=BL, width=int(0.25 * sc))
    d.polygon([(x, y), (x + w * 0.25, y - w * 0.1), (x + w * 0.25, y + w * 0.08)], fill=(255, 190, 60), outline=BL)
    d.ellipse((x + w * 0.22, y - w * 0.07, x + w * 0.3, y + w * 0.01), fill=(255, 255, 255))


def draw_hd(f, w=1000, h=500, dino=True):
    sc = w / 128.0
    ys = h / 64.0
    n = night(f)
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im, "RGBA")
    top = lerp((120, 200, 255), (20, 24, 60), n)
    bot = lerp((255, 225, 170), (60, 50, 110), n)
    for y in range(h):
        d.line((0, y, w, y), fill=lerp(top, bot, y / h))
    g = game(f)
    k = g["k"] if g else f
    if n > 0.05:                                              # stars
        for i in range(60):
            sx, sy = (i * 137) % w, (i * 71) % int(h * 0.55)
            r = 1 + (i % 3)
            d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(255, 255, 230, int(255 * n * (0.5 + 0.5 * math.sin(f * 0.3 + i)))))
    sx = w * 0.82
    if n < 0.5:
        d.ellipse((sx - 48, h * 0.12, sx + 48, h * 0.12 + 96), fill=(255, 210, 70, int(255 * (1 - 2 * n))))
    else:
        d.ellipse((sx - 40, h * 0.12, sx + 40, h * 0.12 + 80), fill=(250, 250, 225, int(255 * (2 * n - 1))))
        d.ellipse((sx - 10, h * 0.12 - 6, sx + 50, h * 0.12 + 66), fill=top + (int(255 * (2 * n - 1)),))
    off = k * 2.8 * sc
    for i in range(6):                                        # clouds
        cx = (i * 240 - off * 0.12) % (w + 300) - 150
        cy = h * (0.18 + 0.1 * (i % 3))
        for dx, r in ((-40, 34), (0, 48), (46, 36)):
            d.ellipse((cx + dx - r, cy - r * 0.6, cx + dx + r, cy + r * 0.6), fill=(255, 255, 255, int(220 * (1 - 0.6 * n))))
    gy = GROUND * ys
    for i in range(10):                                       # far dunes
        bx = (i * 220 - off * 0.3) % (w + 440) - 220
        d.ellipse((bx, gy - 90, bx + 440, gy + 60), fill=lerp((240, 190, 120), (90, 70, 120), n) + (255,))
    d.rectangle((0, gy, w, h), fill=lerp((235, 200, 130), (110, 90, 140), n))
    d.rectangle((0, gy, w, gy + 0.6 * sc), fill=lerp((170, 120, 60), (60, 45, 90), n))
    for i in range(40):                                       # pebbles
        px = (i * 53 - off) % (w + 60) - 30
        py = gy + 1.2 * sc + (i * 17) % int(h - gy - 2 * sc)
        d.ellipse((px, py, px + 0.8 * sc, py + 0.5 * sc), fill=lerp((190, 150, 90), (80, 60, 110), n))
    ph = phase(f)
    if g and ph not in ("title", "menu", "count"):
        for x, kind in g["obs"]:
            ow, oh = SIZES[kind]
            if kind == "bird":
                ptero_hd(d, x * sc, BIRD_Y * ys, sc, f)
            elif kind == "c3":
                cactus_hd(d, x * sc, gy, 6 * sc, 12 * ys, sc)
                cactus_hd(d, (x + 8) * sc, gy, 7 * sc, 14 * ys, sc)
            else:
                cactus_hd(d, x * sc, gy, ow * sc, oh * ys, sc)
        if dino:
            dead = g["state"] == "DEAD"
            t = trex_hd(DINO_H * 1.25 * sc, f, dead, g["dino_y"] < 0)
            im.paste(t, (int(DINO_X * sc - 0.1 * t.width), int(gy + g["dino_y"] * ys - t.height * 0.9)), t)
    elif dino:
        t = trex_hd(24 * sc, f)
        im.paste(t, (int(w * 0.5 - t.width / 2), int(gy - t.height * 0.9)), t)
    return im


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
