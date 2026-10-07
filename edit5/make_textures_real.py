#!/usr/bin/env python3
"""Photoreal-look textures: breadboard holes, ESP-WROOM-32 shield label, OLED screens with a level graph."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "tex")
OLED = os.path.join(HERE, "work", "oled_real")
os.makedirs(OUT, exist_ok=True)
os.makedirs(OLED, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---- breadboard top (4.2 x 1.9 units -> 2100 x 950 px)
W, H = 2100, 950
im = Image.new("RGB", (W, H), (236, 234, 228))
d = ImageDraw.Draw(im)
d.rectangle((0, H // 2 - 22, W, H // 2 + 22), fill=(222, 220, 214))           # centre channel
for rail_y, col in ((40, (200, 40, 40)), (95, (40, 70, 200)), (H - 95, (200, 40, 40)), (H - 40, (40, 70, 200))):
    d.line((30, rail_y, W - 30, rail_y), fill=col, width=4)
pitch = 30
for x in range(60, W - 40, pitch):
    for y in list(range(150, H // 2 - 40, pitch)) + list(range(H // 2 + 50, H - 140, pitch)):
        d.rectangle((x - 6, y - 6, x + 6, y + 6), fill=(60, 58, 55))
    if (x // pitch) % 6 != 0:
        for y in (60, 78, H - 78, H - 60):
            d.rectangle((x - 5, y - 5, x + 5, y + 5), fill=(60, 58, 55))
f = ImageFont.truetype(SANS, 16)
for i, x in enumerate(range(60, W - 40, pitch * 5)):
    d.text((x, 128), str(i * 5 + 1), font=f, fill=(120, 118, 112), anchor="mm")
im.save(os.path.join(OUT, "breadboard.png"))

# ---- ESP-WROOM-32 shield label
im = Image.new("RGB", (620, 720), (196, 198, 202))
d = ImageDraw.Draw(im)
d.text((310, 200), "ESP-WROOM-32", font=ImageFont.truetype(SANS, 54), fill=(70, 72, 78), anchor="mm")
d.text((310, 290), "WiFi + BT", font=ImageFont.truetype(SANS, 40), fill=(90, 92, 98), anchor="mm")
d.text((310, 380), "CE  FCC ID", font=ImageFont.truetype(SANS, 34), fill=(110, 112, 118), anchor="mm")
d.rectangle((250, 470, 370, 590), outline=(90, 92, 98), width=6)
im.save(os.path.join(OUT, "wroom.png"))

# ---- OLED screens: "Water Level: NN%" + scrolling history graph (white/cyan on black, 128x64 look)
SW, SH = 512, 256
hist = []
for p in range(101):
    hist.append(p)
    im = Image.new("RGB", (SW, SH), (2, 3, 6))
    d = ImageDraw.Draw(im)
    if p >= 100:
        d.text((SW // 2, 70), "WARNING:", font=ImageFont.truetype(MONO, 60), fill=(255, 70, 50), anchor="mm")
        d.text((SW // 2, 150), "TANK FULL", font=ImageFont.truetype(MONO, 66), fill=(255, 70, 50), anchor="mm")
        d.text((SW // 2, 220), "Wi-Fi alert sent", font=ImageFont.truetype(MONO, 30), fill=(200, 230, 255), anchor="mm")
    else:
        d.text((16, 34), f"Water Level: {p}%", font=ImageFont.truetype(MONO, 44), fill=(220, 240, 255), anchor="lm")
        x0, y0, x1, y1 = 40, 80, SW - 16, SH - 50
        d.line((x0, y0, x0, y1), fill=(150, 200, 255), width=3)
        d.line((x0, y1, x1, y1), fill=(150, 200, 255), width=3)
        for k in range(0, 101, 25):
            yy = y1 - (y1 - y0) * k / 100
            d.line((x0 - 8, yy, x0, yy), fill=(150, 200, 255), width=2)
        pts = hist[-40:]
        if len(pts) > 1:
            xy = [(x0 + 4 + (x1 - x0 - 8) * i / 39, y1 - (y1 - y0) * v / 100) for i, v in enumerate(pts)]
            d.line(xy, fill=(120, 220, 255), width=5)
        bw = int((SW - 32) * p / 100)
        d.rectangle((16, SH - 34, SW - 16, SH - 12), outline=(220, 240, 255), width=3)
        d.rectangle((16, SH - 34, 16 + bw, SH - 12), fill=(220, 240, 255))
    im.save(os.path.join(OLED, f"{p:03d}.png"))
print("textures in", OUT, "and", OLED)
