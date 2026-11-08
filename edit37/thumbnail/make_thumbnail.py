#!/usr/bin/env python3
"""Thumbnails for the ESP32 Smart Plant Watering short (edit37): B&W + colour graded frame of the happy green
plant, the 'PLANT CAM' panel (72 %, KHUSH) as a big card, yellow hook, green title, pills.
1080x1920 (words inside y 190..1690) + 1280x720."""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b37", os.path.join(HERE, "..", "build_short.py"))
b37 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b37)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, GRN, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 235, 120), (60, 220, 255), (130, 60, 255)
CARD_F = 200


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def card(w, ang=-4):
    h = w // 2
    g = b37.plantgfx.draw_hd(CARD_F, 1000, 500).resize((w, h), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    c = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", c.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 190))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    c.paste(g, (20, 20), m)
    ImageDraw.Draw(c).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=GRN, width=max(4, w // 90))
    return c.rotate(ang, expand=True, resample=Image.BICUBIC)


bg = Image.fromarray(b37.grade(b37.load3d(180), 180))
W, H = 1080, 1920
c = bg.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(150 * max(0, (y - 1450) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
cd = card(820)
c.alpha_composite(cd, (W - cd.width + 10, 930))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 265), "Khud paani peeta hai!", 72, YEL, 9)
c.alpha_composite(emoji("😱", 76, 8), (W // 2 - 45 + int(d.textlength("Khud paani peeta hai!", font=F(72)) / 2) + 10, 226))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 40, 400), "SMART PLANT", 100, GRN, 11)
c.alpha_composite(emoji("🌱", 90, -6), (W // 2 - 40 + int(d.textlength("SMART PLANT", font=F(100)) / 2) + 12, 352))
d = ImageDraw.Draw(c)
d.rounded_rectangle((200, 500, W - 200, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Sookha? Pump ON!", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 690, 1600), 50, fill=PURP)
d.text((375, 1550), "ESP32 + Soil Sensor", font=F(46), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
W, H = 1280, 720
c = bg.resize((W, int(W * 1920 / 1080)), Image.LANCZOS).crop((0, 600, W, 600 + H)).convert("RGBA")
sh = Image.new("L", (W, 1))
sh.putdata([int(215 * max(0, 1 - x / 780)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
cd = card(520, -5)
c.alpha_composite(cd, (W - cd.width + 10, 330))
d = ImageDraw.Draw(c)
text(d, (40, 90), "Khud paani peeta hai!", 62, YEL, 8, anchor="lm")
c.alpha_composite(emoji("😱", 62, 8), (40 + int(d.textlength("Khud paani peeta hai!", font=F(62))) + 12, 60))
d = ImageDraw.Draw(c)
text(d, (40, 205), "SMART PLANT", 88, GRN, 9, anchor="lm")
c.alpha_composite(emoji("🌱", 78, -6), (40 + int(d.textlength("SMART PLANT", font=F(88))) + 14, 165))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Sookha? Pump ON!", font=F(36), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + Soil Sensor", font=F(36), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
