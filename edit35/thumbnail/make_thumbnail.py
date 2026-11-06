#!/usr/bin/env python3
"""Thumbnails for the ESP32 Smart Dustbin short (edit35): B&W + colour-screen graded hook frame (hand with the
paper ball, lid open), the 'BIN CAM' panel (OPEN, 12 cm) as a big card, yellow hook, green title, pills.
1080x1920 (words inside y 190..1690) + 1280x720."""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b35", os.path.join(HERE, "..", "build_short.py"))
b35 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b35)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, GRN, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 235, 120), (60, 220, 255), (130, 60, 255)
CARD_F = 12


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
    g = b35.bingfx.draw_hd(CARD_F, 1000, 500).resize((w, h), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    c = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", c.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 190))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    c.paste(g, (20, 20), m)
    ImageDraw.Draw(c).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=GRN, width=max(4, w // 90))
    return c.rotate(ang, expand=True, resample=Image.BICUBIC)


bg = Image.fromarray(b35.grade(b35.load3d(16), 16))
W, H = 1080, 1920
c = bg.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(150 * max(0, (y - 1450) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
cd = card(820)
c.alpha_composite(cd, (W - cd.width + 10, 1060))
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
c = bg.resize((W, int(W * 1920 / 1080)), Image.LANCZOS).crop((0, 600, W, 600 + H)).convert("RGBA")
sh = Image.new("L", (W, 1))
sh.putdata([int(215 * max(0, 1 - x / 780)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
cd = card(520, -5)
c.alpha_composite(cd, (W - cd.width + 10, 330))
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
