#!/usr/bin/env python3
"""Smart plant screens. draw_oled(f) = 128x64 OLED page in colour pixels (title, big moisture %, bar, DRY /
WATERING / WET status, pump state, a tiny plant face that is sad when dry and smiles when wet); oled_png(f) its
8x pixel texture for the 3D render; draw_hd(f, w, h) = the 'PLANT CAM' panel (moisture gauge, live moisture
graph with the 30 % trigger line, pump chip with flowing drops, happy / sad plant)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from planttime import N, LOW, moisture, state, pump, wet, history  # noqa: E402

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
GRN, RED, CYN, WHT, YEL, GRY, BLU = (70, 240, 110), (255, 70, 70), (80, 220, 255), (240, 245, 255), (255, 214, 10), (120, 125, 140), (60, 150, 255)


def fo(sz, path=BIG):
    return ImageFont.truetype(path, sz)


def st_col(s):
    return {"DRY": RED, "WATERING": BLU, "WET": GRN}[s]


def plant_face(d, cx, cy, r, happy, col, width=1):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=width)
    e = r * 0.35
    d.ellipse((cx - e - r * 0.12, cy - r * 0.35 - r * 0.12, cx - e + r * 0.12, cy - r * 0.35 + r * 0.12), fill=col)
    d.ellipse((cx + e - r * 0.12, cy - r * 0.35 - r * 0.12, cx + e + r * 0.12, cy - r * 0.35 + r * 0.12), fill=col)
    if happy:
        d.arc((cx - r * 0.5, cy - r * 0.3, cx + r * 0.5, cy + r * 0.55), 20, 160, fill=col, width=width)
    else:
        d.arc((cx - r * 0.5, cy + r * 0.2, cx + r * 0.5, cy + r * 0.95), 200, 340, fill=col, width=width)
    # two leaves on top
    d.ellipse((cx - r * 0.9, cy - r * 1.7, cx - r * 0.05, cy - r * 1.05), outline=col, width=width)
    d.ellipse((cx + r * 0.05, cy - r * 1.7, cx + r * 0.9, cy - r * 1.05), outline=col, width=width)


def draw_oled(f):
    im = Image.new("RGB", (128, 64), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 127, 10), fill=GRN)
    d.text((64, 5), "SMART PLANT", font=fo(8), fill=(0, 0, 0), anchor="mm")
    m = moisture(f)
    s = state(f)
    d.text((2, 14), "SOIL", font=fo(7, MONO), fill=GRY)
    d.text((2, 30), f"{int(round(m))}%", font=fo(16), fill=st_col(s), anchor="lm")
    d.rectangle((2, 41, 72, 45), outline=GRY)
    d.rectangle((3, 42, 3 + 68 * m / 100, 44), fill=st_col(s))
    d.line((2 + 70 * LOW / 100, 39, 2 + 70 * LOW / 100, 47), fill=YEL)
    d.rectangle((2, 50, 72, 62), fill=st_col(s))
    d.text((37, 56), {"DRY": "SOIL: DRY", "WATERING": "WATERING..", "WET": "SOIL: WET"}[s], font=fo(7), fill=(0, 0, 0), anchor="mm")
    plant_face(d, 100, 38, 10, s != "DRY", GRN if s != "DRY" else RED, 1)
    d.text((100, 58), "PUMP ON" if pump(f) else "PUMP OFF", font=fo(6, MONO), fill=BLU if pump(f) else GRY, anchor="mm")
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
    im = Image.new("RGBA", (w, h), (8, 16, 12, 255))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 50):
        d.line((x, 0, x, h), fill=(16, 34, 24, 255))
    for y in range(0, h, 50):
        d.line((0, y, w, y), fill=(16, 34, 24, 255))
    m = moisture(f)
    s = state(f)
    col = st_col(s)
    d.text((40, 40), "SOIL MOISTURE", font=fo(int(h * 0.065), MONT), fill=GRY + (255,))
    v = f"{int(round(m))}"
    d.text((40, h * 0.33), v, font=fo(int(h * 0.3), MONT), fill=col + (255,), anchor="lm", stroke_width=4, stroke_fill=(0, 0, 0))
    tw = d.textlength(v, font=fo(int(h * 0.3), MONT))
    d.text((40 + tw + 10, h * 0.37), "%", font=fo(int(h * 0.12), MONT), fill=col + (255,), anchor="lm")
    gx0, gy0, gx1, gy1 = 40, h * 0.56, w * 0.62, h * 0.93         # moisture graph
    d.rounded_rectangle((gx0, gy0, gx1, gy1), 14, outline=(40, 70, 55, 255), width=2)
    ty = gy1 - (gy1 - gy0) * LOW / 100
    d.line((gx0, ty, gx1, ty), fill=YEL + (255,), width=3)
    d.text((gx1 - 8, ty - 6), "30% = PUMP ON", font=fo(int(h * 0.045), MONT), fill=YEL + (255,), anchor="rb")
    hist = history(f)
    pts = [(gx0 + (gx1 - gx0) * i / (len(hist) - 1), gy1 - (gy1 - gy0) * hv / 100) for i, hv in enumerate(hist)]
    glow = Image.new("RGBA", (w, h))
    ImageDraw.Draw(glow).line(pts, fill=CYN + (255,), width=12)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.line(pts, fill=CYN + (255,), width=5)
    d.ellipse((pts[-1][0] - 9, pts[-1][1] - 9, pts[-1][0] + 9, pts[-1][1] + 9), fill=WHT + (255,))
    pon = pump(f)                                                  # pump chip
    d.rounded_rectangle((w - 330, 26, w - 30, 96), 35, fill=(BLU if pon else (70, 74, 90)) + (255,), outline=WHT + (255,), width=3)
    d.text((w - 180, 61), "PUMP ON" if pon else "PUMP OFF", font=fo(int(h * 0.075), MONT), fill=WHT + (255,), anchor="mm")
    if pon:
        for k in range(5):
            yy = 110 + ((f * 6 + k * 22) % 110)
            d.ellipse((w - 190 + 12 * math.sin(k), yy, w - 172 + 12 * math.sin(k), yy + 24), fill=BLU + (230,))
    happy = s != "DRY"
    fc = GRN if happy else RED
    plant_face(d, w * 0.80, h * 0.70, h * 0.14, happy, fc + (255,), 7)
    d.text((w * 0.80, h * 0.93), {"DRY": "PYAASA", "WATERING": "PEE RAHA", "WET": "KHUSH"}[s], font=fo(int(h * 0.06), MONT), fill=fc + (255,), anchor="mm")
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
