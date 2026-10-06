#!/usr/bin/env python3
"""Laptop-screen textures (Serial Monitor states) used on the 3D laptop."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "screens")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
W, H = 1600, 1000
BG, BAR = (14, 18, 30), (36, 42, 62)


def base(title="Serial Monitor"):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((40 + i * 60, 35, 80 + i * 60, 75), fill=c)
    d.text((240, 55), title, font=ImageFont.truetype(SANS, 46), fill=(220, 225, 240), anchor="lm")
    return im, d


def badge(d, text, col):
    f = ImageFont.truetype(SANS, 52)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((60, 150, 60 + w + 60, 240), 45, fill=col)
    d.text((90, 195), text, font=f, fill=(255, 255, 255), anchor="lm")


def save(im, name):
    im.save(os.path.join(OUT, name + ".png"))


im, d = base()
d.text((70, 300), "> waiting for data_", font=ImageFont.truetype(MONO, 64), fill=(90, 110, 150))
save(im, "idle")

garbage = ["‡¿Ø€‹ı†ƒ¶×", "‡¿Ø€‹ı†ƒ¶×\n¤§Ð¬ÿ±»¢Þ", "‡¿Ø€‹ı†ƒ¶×\n¤§Ð¬ÿ±»¢Þ\nŒ¥µ÷¦ÆØ¿‰"]
for i in range(4):
    im, d = base()
    badge(d, "code 9600  ≠  monitor 115200", (220, 45, 55))
    if i:
        d.multiline_text((70, 320), garbage[i - 1], font=ImageFont.truetype(MONO, 92), fill=(255, 90, 90), spacing=30)
    save(im, f"bad{i}")

for i, t in enumerate(["", "Hel", "Hello Wo", "Hello World!"]):
    im, d = base()
    badge(d, "code 9600  =  monitor 9600", (25, 160, 90))
    d.text((70, 330), t + ("_" if i < 3 else ""), font=ImageFont.truetype(MONO, 120), fill=(90, 255, 140))
    save(im, f"good{i}")

im = Image.new("RGB", (W, H), (20, 14, 50))
d = ImageDraw.Draw(im)
for y in range(H):
    k = y / H
    d.line((0, y, W, y), fill=(int(110 - 70 * k), int(50 + 80 * k), int(200 - 40 * k)))
d.rounded_rectangle((180, 330, W - 180, 520), 95, fill=(255, 225, 26))
d.text((W // 2, 425), "FOLLOW — roz 1 IoT concept", font=ImageFont.truetype(MONT, 70), fill=(20, 20, 30), anchor="mm")
d.text((W // 2, 650), "@The IOT Engineer", font=ImageFont.truetype(MONT, 80), fill=(255, 255, 255), anchor="mm")
d.text((W // 2, 180), "ARDUINO · CODE KA RAAZ #2", font=ImageFont.truetype(MONT, 54), fill=(255, 200, 190), anchor="mm")
save(im, "cta")
print("screens in", OUT)
