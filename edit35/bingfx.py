#!/usr/bin/env python3
"""Smart dustbin screens. draw_oled(f) = 128x64 OLED page in colour pixels (title bar, live distance, bar
gauge, LID OPEN / CLOSED box, item counter, tiny bin icon whose lid follows the servo); oled_png(f) its 8x
pixel texture for the 3D render; draw_hd(f, w, h) = the crisp 'BIN CAM' panel for the edit (big distance,
gradient gauge with the 20 cm trigger line, sonar waves, animated bin + lid, OPEN / CLOSED chip, items)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bintime import N, DETECT, dist, lid, lid_open, items, detected  # noqa: E402

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
GRN, RED, CYN, WHT, YEL, GRY = (60, 255, 120), (255, 60, 70), (80, 220, 255), (240, 245, 255), (255, 214, 10), (120, 125, 140)


def fo(sz, path=BIG):
    return ImageFont.truetype(path, sz)


def bin_icon(d, x, y, s, a, col, width=1):
    """Bin outline (x, y = bottom-left), lid hinged at the back-right, a = 0..1 open."""
    w, h = 18 * s, 20 * s
    d.line([(x + 2 * s, y - h), (x + 3 * s, y), (x + w - 3 * s, y), (x + w - 2 * s, y - h)], fill=col, width=width)
    for k in range(3):
        xx = x + (6 + 3 * k) * s
        d.line([(xx, y - h + 4 * s), (xx, y - 3 * s)], fill=col, width=width)
    ang = math.radians(-100 * a)
    hx, hy = x + w, y - h - 1 * s
    L = w + 2 * s
    ex, ey = hx - L * math.cos(ang), hy + L * math.sin(ang)
    d.line([(hx, hy), (ex, ey)], fill=col, width=width + 1)


def draw_oled(f):
    im = Image.new("RGB", (128, 64), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 127, 10), fill=CYN)
    d.text((64, 5), "SMART BIN", font=fo(8), fill=(0, 0, 0), anchor="mm")
    dv = dist(f)
    txt = f"{int(round(dv))}cm" if dv is not None else "-- cm"
    d.text((2, 14), "DIST", font=fo(7, MONO), fill=GRY)
    d.text((2, 30), txt, font=fo(15), fill=GRN if (dv is not None and dv < DETECT) else WHT, anchor="lm")
    d.rectangle((2, 42, 70, 46), outline=GRY)
    if dv is not None:
        k = max(0.0, min(1.0, 1 - dv / 40))
        d.rectangle((3, 43, 3 + 66 * k, 45), fill=GRN if dv < DETECT else YEL)
    tx = 2 + 66 * (1 - DETECT / 40)
    d.line((tx, 40, tx, 48), fill=RED)
    op = lid_open(f)
    d.rectangle((2, 51, 70, 62), fill=GRN if op else (0, 0, 0), outline=GRN if op else GRY)
    d.text((36, 56.5), "LID: OPEN" if op else "LID: CLOSED", font=fo(7), fill=(0, 0, 0) if op else WHT, anchor="mm")
    bin_icon(d, 88, 61, 1.0, lid(f), WHT, 1)
    d.text((126, 15), f"ITEMS:{items(f)}", font=fo(7, MONO), fill=YEL, anchor="ra")
    return im


def oled_png(f):
    im = draw_oled(f)
    S = 8
    big = Image.new("RGB", (128 * S, 64 * S), (2, 3, 6))
    px = im.load()
    d = ImageDraw.Draw(big)
    for yy in range(64):
        for xx in range(128):
            c = px[xx, yy]
            if sum(c) > 60:
                d.rectangle((xx * S, yy * S, xx * S + S - 2, yy * S + S - 2), fill=c)
    return big


def draw_hd(f, w=1000, h=500):
    im = Image.new("RGBA", (w, h), (8, 12, 20, 255))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 50):
        d.line((x, 0, x, h), fill=(18, 30, 44, 255))
    for y in range(0, h, 50):
        d.line((0, y, w, y), fill=(18, 30, 44, 255))
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    dv = dist(f)
    det = dv is not None and dv < DETECT
    if dv is not None:                                         # sonar waves from the sensor (left)
        for k in range(4):
            r = ((f * 9 + k * 60) % 240) + 20
            a = int(255 * (1 - r / 260))
            gd.arc((60 - r, h * 0.42 - r, 60 + r, h * 0.42 + r), -40, 40, fill=(GRN if det else CYN) + (a,), width=8)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.text((40, 40), "DISTANCE", font=fo(int(h * 0.07), MONT), fill=GRY + (255,))
    v = f"{int(round(dv))}" if dv is not None else "--"
    col = GRN if det else WHT
    d.text((40, h * 0.36), v, font=fo(int(h * 0.34), MONT), fill=col + (255,), anchor="lm", stroke_width=4, stroke_fill=(0, 0, 0))
    tw = d.textlength(v, font=fo(int(h * 0.34), MONT))
    d.text((40 + tw + 12, h * 0.42), "cm", font=fo(int(h * 0.1), MONT), fill=col + (255,), anchor="lm")
    gx0, gx1, gy = 40, w * 0.58, h * 0.66                      # gauge
    for i in range(int(gx1 - gx0)):
        u = i / (gx1 - gx0)
        c = (int(60 + 195 * u), int(255 - 120 * u), 90)
        d.line((gx0 + i, gy, gx0 + i, gy + 34), fill=c + (70,))
    if dv is not None:
        k = max(0.0, min(1.0, 1 - dv / 40))
        for i in range(int((gx1 - gx0) * k)):
            u = i / (gx1 - gx0)
            c = (int(60 + 195 * u), int(255 - 120 * u), 90)
            d.line((gx0 + i, gy, gx0 + i, gy + 34), fill=c + (255,))
    tx = gx0 + (gx1 - gx0) * (1 - DETECT / 40)
    d.line((tx, gy - 14, tx, gy + 48), fill=RED + (255,), width=5)
    d.text((tx, gy + 70), "20 cm = OPEN", font=fo(int(h * 0.055), MONT), fill=RED + (255,), anchor="mm")
    op = lid_open(f)
    bx, by, s = w * 0.66, h * 0.95, 7.5                       # big animated bin
    bin_icon(d, bx, by, s, lid(f), (GRN if op else WHT) + (255,), 8)
    d.rounded_rectangle((w - 300, 26, w - 30, 96), 35, fill=((30, 170, 80) if op else (70, 74, 90)) + (255,), outline=WHT + (255,), width=3)
    d.text((w - 165, 61), "OPEN" if op else "CLOSED", font=fo(int(h * 0.08), MONT), fill=WHT + (255,), anchor="mm")
    d.text((w - 165, 130), f"ITEMS: {items(f)}", font=fo(int(h * 0.065), MONT), fill=YEL + (255,), anchor="mm")
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
