#!/usr/bin/env python3
"""Thumbnails for the ESP32 Smart Dustbin short (edit36): the original clip frame with the hand dropping the paper
ball into the open bin, yellow hook, green title, cyan / purple pills. 1080x1920 (words inside y 190..1690) +
1280x720."""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
SRC = os.path.join(HERE, "..", "work", "src")
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, GRN, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 235, 120), (60, 220, 255), (130, 60, 255)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


src = ImageEnhance.Contrast(Image.open(os.path.join(SRC, "0112.png")).convert("RGB")).enhance(1.08)
W, H = 1080, 1920
c = src.resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(225 * max(0, 1 - (y - 150) / 560)) if y < 800 else int(170 * max(0, (y - 1450) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 265), "Khud khulta hai!", 88, YEL, 10)
c.alpha_composite(emoji("😱", 88, 8), (W // 2 - 45 + int(d.textlength("Khud khulta hai!", font=F(88)) / 2) + 10, 218))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 40, 400), "SMART DUSTBIN", 92, GRN, 11)
c.alpha_composite(emoji("🗑️", 86, -6), (W // 2 - 40 + int(d.textlength("SMART DUSTBIN", font=F(92)) / 2) + 12, 352))
d = ImageDraw.Draw(c)
d.rounded_rectangle((200, 500, W - 200, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Haath dikhao = OPEN!", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 690, 1600), 50, fill=PURP)
d.text((375, 1550), "ESP32 + HC-SR04", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
W, H = 1280, 720
big = src.resize((W, int(W * 1280 / 720)), Image.LANCZOS)
c = big.crop((0, 500, W, 500 + H)).convert("RGBA")
sh = Image.new("L", (W, 1))
sh.putdata([int(215 * max(0, 1 - x / 760)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (40, 90), "Khud khulta hai!", 74, YEL, 9, anchor="lm")
c.alpha_composite(emoji("😱", 72, 8), (40 + int(d.textlength("Khud khulta hai!", font=F(74))) + 12, 54))
d = ImageDraw.Draw(c)
text(d, (40, 205), "SMART DUSTBIN", 84, GRN, 9, anchor="lm")
c.alpha_composite(emoji("🗑️", 76, -6), (40 + int(d.textlength("SMART DUSTBIN", font=F(84))) + 14, 165))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Haath dikhao = OPEN!", font=F(36), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + HC-SR04", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
