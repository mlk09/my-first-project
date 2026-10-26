#!/usr/bin/env python3
"""Draws the Flappy Bird game state two ways: draw_oled() = the 1-bit 128x64 SH1106 screen (pixel bird,
outlined pipes, dotted ground, score, menu / 3-2-1 / GAME OVER / NEW BEST pages) and draw_hd() = a
crisp full-colour version of the same frame for the edit (sky gradient, parallax clouds and city,
shaded green pipes, a big yellow bird with flapping wing, striped ground, chunky score)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import (N, PLAY0, START, LEVELS, PIPE_GAP, PIPE_W, BIRD_X, HIGH_OLD, SPEED,  # noqa: E402
                      game, phase, level, countdown, crash_frame, final_score)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
BIRD = ["..####..",
        ".#....#.",
        "#..#.#.#",
        "#......#",
        ".#..###.",
        "..##...."]


def fo(sz, big=True):
    return ImageFont.truetype(BIG if big else MONO, sz)


def scroll(f):
    """Ground / city scroll offset in OLED px."""
    return (f * SPEED) if phase(f) in ("hook", "play") else (f * 0.6)


# ------------------------------------------------------------------ 1-bit OLED
def bird_1bit(d, x, y, flap_up):
    """8x6 sprite drawn at 2x (16x12 px) like the real ESP32 game builds."""
    for r, row in enumerate(BIRD):
        for c, ch in enumerate(row):
            if ch == "#":
                d.rectangle((x - 8 + 2 * c, y - 6 + 2 * r, x - 7 + 2 * c, y - 5 + 2 * r), fill=1)
    wy = y - 2 if flap_up else y + 2                       # wing
    d.rectangle((x - 6, wy, x - 1, wy + 1), fill=1)


def draw_oled(f):
    im = Image.new("1", (128, 64), 0)
    d = ImageDraw.Draw(im)
    ph = phase(f)
    g = game(f)
    off = int(scroll(f)) % 6
    if ph in ("title",):
        d.text((64, 14), "FLAPPY", font=fo(15), fill=1, anchor="mm")
        d.text((64, 31), "BIRD", font=fo(15), fill=1, anchor="mm")
        bird_1bit(d, 64, 46 + int(2 * math.sin(f * 0.4)), (f // 4) % 2 == 0)
        d.text((64, 58), "PRESS KNOB", font=fo(8, False), fill=1, anchor="mm")
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
    for x, gy in g["pipes"]:                                 # pipes
        top, bot = gy - PIPE_GAP / 2, gy + PIPE_GAP / 2
        d.rectangle((x, -1, x + PIPE_W, top), outline=1)
        d.rectangle((x - 1, top - 4, x + PIPE_W + 1, top), outline=1, fill=0)
        d.rectangle((x, bot, x + PIPE_W, 60), outline=1)
        d.rectangle((x - 1, bot, x + PIPE_W + 1, bot + 4), outline=1, fill=0)
    d.line((0, 60, 127, 60), fill=1)
    for x in range(-off, 128, 6):
        d.point((x, 62), fill=1)
    dead = g["state"] == "DEAD"
    bird_1bit(d, BIRD_X, int(g["bird_y"]), g["vel"] < 0 and not dead)
    sc = f"{g['score']:02d}"
    d.rectangle((96, 0, 127, 11), fill=0)
    d.text((126, 1), sc, font=fo(10), fill=1, anchor="ra")
    if ph in ("over", "best"):
        d.rectangle((14, 14, 113, 50), fill=0, outline=1)
        if ph == "over" or (f // 5) % 2 == 0:
            d.text((64, 24), "GAME OVER" if ph == "over" else "NEW BEST!", font=fo(11), fill=1, anchor="mm")
        d.text((64, 41), f"SCORE {final_score()}  BEST {max(HIGH_OLD, final_score()) if ph == 'best' else HIGH_OLD}",
               font=fo(7, False), fill=1, anchor="mm")
    return im


def oled_png(f):
    im = draw_oled(f)
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
SKY_T, SKY_B = (64, 170, 245), (150, 225, 255)
PIPE_C, PIPE_D, PIPE_L = (90, 200, 60), (40, 120, 30), (170, 240, 120)


def bird_hd(w, ang, wing_up):
    """Big yellow bird sprite (RGBA, w x 0.8w), rotated by ang degrees."""
    s = 4
    W, H = int(w * s), int(w * 0.8 * s)
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    o = int(w * 0.06 * s)
    d.ellipse((o, o, W - o * 4, H - o), fill=(255, 205, 40), outline=(60, 35, 10), width=o)
    d.ellipse((o * 3, H * 0.45, W * 0.55, H - o * 2.5), fill=(255, 240, 160))               # belly
    ex, ey, er = W * 0.62, H * 0.3, W * 0.16
    d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(255, 255, 255), outline=(60, 35, 10), width=o)
    d.ellipse((ex - er * 0.15, ey - er * 0.45, ex + er * 0.5, ey + er * 0.3), fill=(20, 20, 25))
    d.polygon([(W * 0.68, H * 0.52), (W - o, H * 0.6), (W * 0.68, H * 0.78)], fill=(250, 110, 40), outline=(60, 35, 10))
    d.line((W * 0.7, H * 0.65, W - o * 2, H * 0.64), fill=(60, 35, 10), width=o)
    wy = H * (0.28 if wing_up else 0.52)
    d.ellipse((o * 1.5, wy, W * 0.42, wy + H * 0.28), fill=(255, 245, 210), outline=(60, 35, 10), width=o)
    im = im.resize((int(w), int(w * 0.8)), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def pipe_hd(d, x0, x1, y0, y1, cap_at_bottom, sc):
    lip = 0.6 * sc
    d.rectangle((x0, y0, x1, y1), fill=PIPE_C, outline=PIPE_D, width=int(0.35 * sc))
    d.rectangle((x0 + (x1 - x0) * 0.15, y0, x0 + (x1 - x0) * 0.3, y1), fill=PIPE_L)
    cy0, cy1 = (y1 - 4 * sc, y1) if cap_at_bottom else (y0, y0 + 4 * sc)
    d.rectangle((x0 - lip, cy0, x1 + lip, cy1), fill=PIPE_C, outline=PIPE_D, width=int(0.35 * sc))
    d.rectangle((x0 - lip + (x1 - x0) * 0.15, cy0, x0 + (x1 - x0) * 0.3, cy1), fill=PIPE_L)


_BG = {}


def background(w, h, sc):
    key = (w, h)
    if key not in _BG:
        bg = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(bg)
        for y in range(h):
            u = y / h
            d.line((0, y, w, y), fill=tuple(int(a + (b - a) * u) for a, b in zip(SKY_T, SKY_B)))
        _BG[key] = bg
    return _BG[key].copy()


def draw_hd(f, w=1000, h=500, bird=True):
    """Full-colour frame (RGB, w x h) of the game at frame f."""
    sc = w / 128.0
    im = background(w, h, sc)
    d = ImageDraw.Draw(im, "RGBA")
    off = scroll(f)
    for k in range(6):                                        # clouds (slow parallax)
        cx = (k * 260 - off * sc * 0.15) % (w + 300) - 150
        cy = h * (0.15 + 0.12 * (k % 3))
        for dx, r in ((-50, 40), (0, 58), (55, 44), (100, 30)):
            d.ellipse((cx + dx - r, cy - r * 0.7, cx + dx + r, cy + r * 0.7), fill=(255, 255, 255, 235))
    gy = 60 * sc * h / (64 * sc)                               # ground line in px
    for k in range(18):                                       # city silhouette (mid parallax)
        bx = (k * 90 - off * sc * 0.35) % (w + 180) - 90
        bh = h * (0.12 + 0.08 * ((k * 7) % 5) / 4)
        d.rectangle((bx, gy - bh, bx + 70, gy), fill=(120, 200, 190, 255))
        for wy in range(int(gy - bh + 12), int(gy - 10), 22):
            for wx in (bx + 12, bx + 40):
                d.rectangle((wx, wy, wx + 12, wy + 10), fill=(180, 240, 230, 255))
    for k in range(30):                                       # bushes
        bx = (k * 60 - off * sc * 0.6) % (w + 120) - 60
        d.ellipse((bx, gy - 34, bx + 80, gy + 20), fill=(110, 205, 90, 255))
    g = game(f)
    ph = phase(f)
    yscale = h / 64.0
    if g and ph not in ("title", "menu", "count"):
        for x, gyp in g["pipes"]:
            x0, x1 = x * sc, (x + PIPE_W) * sc
            top, bot = (gyp - PIPE_GAP / 2) * yscale, (gyp + PIPE_GAP / 2) * yscale
            pipe_hd(d, x0, x1, -10, top, True, sc)
            pipe_hd(d, x0, x1, bot, gy, False, sc)
    d.rectangle((0, gy, w, h), fill=(222, 216, 149))          # ground
    d.rectangle((0, gy, w, gy + 0.9 * sc), fill=(115, 191, 46))
    st = int(-(off * sc) % (3 * sc))
    for x in range(st - int(3 * sc), w, int(3 * sc)):
        d.polygon([(x, gy + 0.9 * sc), (x + 1.5 * sc, gy + 0.9 * sc), (x + 3 * sc, gy + 2.2 * sc), (x + 1.5 * sc, gy + 2.2 * sc)],
                  fill=(155, 227, 89))
    if not bird:
        return im
    if g and ph not in ("title", "menu", "count"):
        dead = g["state"] == "DEAD"
        ang = -max(-30, min(80, g["vel"] * 14)) if not dead else -80
        b = bird_hd(14 * sc, ang, (f // 3) % 2 == 0 and not dead)
        im.paste(b, (int(BIRD_X * sc - b.width / 2), int(g["bird_y"] * yscale - b.height / 2)), b)
    else:
        b = bird_hd(16 * sc, 0, (f // 4) % 2 == 0)
        im.paste(b, (int(w * 0.5 - b.width / 2), int(h * 0.42 + 8 * math.sin(f * 0.4) - b.height / 2)), b)
    return im


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
