#!/usr/bin/env python3
"""OLED textures (0-100 %) for the ESP32 water-level short. Own design: tank icon + big % + 3-step bar."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H = 512, 256
CYAN, AMBER, RED = (90, 220, 255), (255, 190, 40), (255, 60, 60)

for p in range(101):
    im = Image.new("RGB", (W, H), (4, 6, 10))
    d = ImageDraw.Draw(im)
    col = CYAN if p < 50 else AMBER if p < 90 else RED
    # tank icon on the left, filled to p %
    d.rectangle((24, 40, 124, 220), outline=col, width=6)
    fill_top = 214 - int(168 * p / 100)
    d.rectangle((32, fill_top, 116, 214), fill=col)
    for i, y in enumerate((88, 130, 172)):
        d.line((124, y, 138, y), fill=col, width=4)
    if p >= 100:
        d.text((330, 70), "TANK", font=ImageFont.truetype(MONO, 64), fill=RED, anchor="mm")
        d.text((330, 140), "FULL!", font=ImageFont.truetype(MONO, 72), fill=RED, anchor="mm")
        d.text((330, 210), "MOTOR OFF", font=ImageFont.truetype(MONO, 34), fill=(255, 255, 255), anchor="mm")
    else:
        d.text((330, 32), "WATER LEVEL", font=ImageFont.truetype(MONO, 30), fill=(200, 210, 220), anchor="mm")
        d.text((330, 118), f"{p}%", font=ImageFont.truetype(MONO, 110), fill=col, anchor="mm")
        for i, (lo, c) in enumerate(((0, CYAN), (50, AMBER), (90, RED))):
            x0 = 180 + i * 104
            d.rectangle((x0, 196, x0 + 92, 226), outline=c, width=3, fill=c if p >= lo + 1 else None)
    im.save(os.path.join(OUT, f"{p:03d}.png"))
print("oled screens in", OUT)
