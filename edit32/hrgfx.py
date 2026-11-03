#!/usr/bin/env python3
"""Heart-rate monitor screens. draw_oled(f) = the 128x64 OLED page drawn in colour pixels (red heart that
pulses on each beat, big BPM, SpO2, NORMAL / HIGH! status, scrolling green ECG) and oled_png(f) its 8x
pixel-grid texture for the 3D render; draw_hd(f, w, h) = the crisp 'HEART CAM' monitor panel for the edit
(dark grid, glowing neon ECG, glossy pulsing heart, big BPM digits, status chip, red alarm tint)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from hrtime import N, FPS, SPO2, phase, ecg, since_beat, shown_bpm, high  # noqa: E402

BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
RED, GRN, CYN, WHT, YEL = (255, 45, 70), (60, 255, 120), (80, 220, 255), (240, 245, 255), (255, 214, 10)
WIN = 2.4 * FPS                       # ECG window (frames)


def fo(sz, path=BIG):
    return ImageFont.truetype(path, sz)


def heart(d, cx, cy, s, fill, outline=None, width=1):
    r = s * 0.27
    d.ellipse((cx - 2 * r, cy - r * 1.5, cx, cy + r * 0.5), fill=fill, outline=outline, width=width)
    d.ellipse((cx, cy - r * 1.5, cx + 2 * r, cy + r * 0.5), fill=fill, outline=outline, width=width)
    d.polygon([(cx - 2 * r + r * 0.12, cy - r * 0.2), (cx + 2 * r - r * 0.12, cy - r * 0.2), (cx, cy + r * 2.1)], fill=fill)


def pump(f):
    return 1 + 0.22 * math.exp(-since_beat(f) / 2.0)


def draw_oled(f):
    im = Image.new("RGB", (128, 64), (0, 0, 0))
    d = ImageDraw.Draw(im)
    hi = high(f)
    d.text((1, -1), "HEART RATE", font=fo(8, MONO), fill=CYN)
    d.text((127, -1), f"SpO2 {SPO2}%", font=fo(8, MONO), fill=CYN, anchor="ra")
    heart(d, 15, 22, 22 * pump(f), RED)
    col = RED if hi else WHT
    d.text((31, 31), f"{shown_bpm(f)}", font=fo(24), fill=col, anchor="lm")
    d.text((31 + d.textlength(f"{shown_bpm(f)}", font=fo(24)) + 2, 36), "BPM", font=fo(9), fill=col, anchor="lm")
    if hi:
        if (f // 4) % 2 == 0:
            d.rectangle((95, 10, 127, 21), fill=RED)
            d.text((111, 15.5), "HIGH!", font=fo(8), fill=(0, 0, 0), anchor="mm")
    else:
        d.rectangle((92, 10, 127, 21), outline=GRN)
        d.text((109.5, 15.5), "NORMAL", font=fo(7), fill=GRN, anchor="mm")
    pts = []
    for x in range(128):
        t = f - (1 - x / 127) * WIN
        pts.append((x, 56 - ecg(phase(t)) * 14))
    d.line(pts, fill=GRN, width=1)
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
    hi = high(f)
    im = Image.new("RGBA", (w, h), (6, 10, 16, 255))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 40):                                   # monitor grid
        d.line((x, 0, x, h), fill=(20, 60, 40, 255) if x % 200 else (30, 90, 60, 255), width=1)
    for y in range(0, h, 40):
        d.line((0, y, w, y), fill=(20, 60, 40, 255) if y % 200 else (30, 90, 60, 255), width=1)
    if hi and (f // 4) % 2 == 0:                                 # red alarm tint
        tint = Image.new("RGBA", (w, h), (255, 0, 40, 46))
        im.alpha_composite(tint)
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    sharp = Image.new("RGBA", (w, h))
    sd = ImageDraw.Draw(sharp)
    base, amp = h * 0.80, h * 0.36
    pts = []
    for x in range(0, w + 1, 3):
        t = f - (1 - x / w) * WIN
        pts.append((x, base - ecg(phase(t)) * amp))
    ecol = (255, 80, 100) if hi else GRN
    gd.line(pts, fill=ecol + (255,), width=16)
    sd.line(pts, fill=ecol + (255,), width=6)
    sd.line(pts, fill=(235, 255, 240, 255), width=2)
    gd.ellipse((w - 26, pts[-1][1] - 26, w + 26, pts[-1][1] + 26), fill=(255, 255, 255, 255))
    s = pump(f)                                                  # glossy heart
    cx, cy, hs = w * 0.14, h * 0.31, h * 0.30 * s
    heart(gd, cx, cy, hs * 1.15, RED + (255,))
    heart(sd, cx, cy, hs, (220, 20, 50, 255))
    heart(sd, cx - hs * 0.02, cy - hs * 0.04, hs * 0.8, (255, 70, 95, 255))
    sd.ellipse((cx - hs * 0.42, cy - hs * 0.36, cx - hs * 0.2, cy - hs * 0.2), fill=(255, 220, 230, 230))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(sharp)
    d = ImageDraw.Draw(im)
    bcol = (255, 90, 110) if hi else (255, 255, 255)
    v = f"{shown_bpm(f)}"
    d.text((w * 0.27, h * 0.30), v, font=fo(int(h * 0.36), MONT), fill=bcol + (255,), anchor="lm",
           stroke_width=4, stroke_fill=(0, 0, 0))
    tw = d.textlength(v, font=fo(int(h * 0.36), MONT))
    d.text((w * 0.27 + tw + 14, h * 0.36), "BPM", font=fo(int(h * 0.09), MONT), fill=bcol + (255,), anchor="lm")
    d.text((w - 30, h * 0.12), f"SpO2 {SPO2}%", font=fo(int(h * 0.075), MONT), fill=CYN + (255,), anchor="rm")
    if hi:
        if (f // 4) % 2 == 0:
            d.rounded_rectangle((w - 250, h * 0.22, w - 30, h * 0.36), 26, fill=(255, 40, 60, 255), outline=WHT + (255,), width=3)
            d.text((w - 140, h * 0.29), "HIGH! 🚨"[:5], font=fo(int(h * 0.075), MONT), fill=WHT + (255,), anchor="mm")
    else:
        d.rounded_rectangle((w - 250, h * 0.22, w - 30, h * 0.36), 26, fill=(20, 120, 60, 255), outline=GRN + (255,), width=3)
        d.text((w - 140, h * 0.29), "NORMAL", font=fo(int(h * 0.07), MONT), fill=WHT + (255,), anchor="mm")
    return im.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(HERE, "work", "oled")
    os.makedirs(out, exist_ok=True)
    for fr in range(N):
        oled_png(fr).save(os.path.join(out, f"{fr:04d}.png"))
    print("oled frames in", out)
