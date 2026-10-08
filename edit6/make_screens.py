#!/usr/bin/env python3
"""Phone dashboard frames for the Smart Plant IoT short (own design: dark app, LDR gauge,
servo slider, live light graph). One PNG per video frame (24 fps, 384 frames)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, ldr, servo_deg, night  # noqa: E402

OUT = os.path.join(HERE, "work", "dash")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H = 540, 1170
BG, CARD, TXT, SUB = (14, 18, 28), (28, 34, 50), (235, 240, 250), (140, 150, 170)
GRN, CYAN, AMB, RED = (60, 220, 130), (70, 200, 255), (255, 190, 60), (255, 80, 80)


def f(sz, b=True):
    return ImageFont.truetype(SANS if b else REG, sz)


hist = []
for fr in range(N):
    v = ldr(fr)
    hist.append(v)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((W // 2, 40), "10:42", font=f(26), fill=TXT, anchor="mm")
    d.text((30, 110), "Smart Plant", font=f(40), fill=TXT, anchor="lm")
    d.ellipse((W - 70, 95, W - 40, 125), fill=GRN)
    d.text((30, 152), "Arduino UNO R4 WiFi · Online", font=f(20, False), fill=SUB, anchor="lm")
    # LDR gauge card
    d.rounded_rectangle((24, 190, W - 24, 520), 28, fill=CARD)
    d.text((48, 222), "LIGHT (LDR)", font=f(22), fill=SUB, anchor="lm")
    cx, cy, r = W // 2, 400, 120
    d.arc((cx - r, cy - r, cx + r, cy + r), 150, 390, fill=(50, 58, 80), width=22)
    col = GRN if v > 50 else AMB if v > 25 else RED
    d.arc((cx - r, cy - r, cx + r, cy + r), 150, 150 + 240 * v / 100, fill=col, width=22)
    d.text((cx, cy - 8), f"{int(v)}%", font=f(64), fill=TXT, anchor="mm")
    d.text((cx, cy + 52), "BRIGHT" if v > 50 else "DIM" if v > 25 else "DARK", font=f(22), fill=col, anchor="mm")
    # servo slider card
    s = servo_deg(fr)
    d.rounded_rectangle((24, 540, W - 24, 700), 28, fill=CARD)
    d.text((48, 575), "SERVO", font=f(22), fill=SUB, anchor="lm")
    d.text((W - 48, 575), f"{int(s)}°", font=f(34), fill=CYAN, anchor="rm")
    x0, x1, y = 60, W - 60, 645
    d.rounded_rectangle((x0, y - 6, x1, y + 6), 6, fill=(50, 58, 80))
    kx = x0 + (x1 - x0) * s / 180
    d.rounded_rectangle((x0, y - 6, kx, y + 6), 6, fill=CYAN)
    d.ellipse((kx - 20, y - 20, kx + 20, y + 20), fill=(255, 255, 255))
    # live graph card
    d.rounded_rectangle((24, 720, W - 24, 1010), 28, fill=CARD)
    d.text((48, 752), "LDR READINGS", font=f(22), fill=SUB, anchor="lm")
    d.rounded_rectangle((W - 120, 738, W - 48, 766), 14, fill=(255, 70, 90))
    d.text((W - 84, 752), "LIVE", font=f(18), fill=(255, 255, 255), anchor="mm")
    gx0, gy0, gx1, gy1 = 48, 790, W - 48, 985
    for k in range(5):
        yy = gy0 + (gy1 - gy0) * k / 4
        d.line((gx0, yy, gx1, yy), fill=(42, 50, 70), width=1)
    pts = hist[-90:]
    if len(pts) > 1:
        xy = [(gx0 + (gx1 - gx0) * i / 89, gy1 - (gy1 - gy0) * (p / 100)) for i, p in enumerate(pts)]
        d.line(xy, fill=GRN, width=4, joint="curve")
    # LED status card
    on = night(fr) > 0.6
    d.rounded_rectangle((24, 1030, W - 24, 1130), 28, fill=CARD)
    d.text((48, 1080), "GROW LED", font=f(22), fill=SUB, anchor="lm")
    d.rounded_rectangle((W - 150, 1058, W - 48, 1102), 22, fill=RED if on else (50, 58, 80))
    d.text((W - 99, 1080), "ON" if on else "OFF", font=f(22), fill=(255, 255, 255), anchor="mm")
    im.save(os.path.join(OUT, f"{fr:04d}.png"))
print("dashboard frames in", OUT)
