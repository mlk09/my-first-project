#!/usr/bin/env python3
"""Thumbnails for the ESP32 Fingerprint Door Lock short (edit34): the original clip colours, finger on the
fingerprint sensor as background, the OLED 'MATCH FOUND / AUTHORIZED' close-up as a big card, yellow hook, red
'FINGERPRINT', pills. 1080x1920 (words inside y 190..1690) + 1280x720."""Thumbnails for the ESP32 Fingerprint Door Lock short (edit34, original clip colours): B&W lab shot with only the screens in
colour (same grade as the video), the glowing ECG OLED close-up as a big card, yellow 'Ungli rakho...',
red 'HEART RATE MONITOR', pills. 1080x1920 (words inside y 190..1690) + 1280x720."""
import importlib.util
import os

import cv2
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b33", os.path.join(HERE, "..", "build.py"))
b33 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b33)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, RED, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 70, 95), (60, 220, 255), (130, 60, 255)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def graded(f):
    im = cv2.cvtColor(cv2.imread(os.path.join(b33.SRC, f"{f:04d}.png")), cv2.COLOR_BGR2RGB)
    return Image.fromarray(b33.grade(im, f))


def card(w, ang=-4):
    g = graded(140).crop((560, 150, 1100, 560))                  # OLED: MATCH FOUND / AUTHORIZED
    h = int(w * g.height / g.width)
    g = ImageEnhance.Contrast(g.resize((w, h), Image.LANCZOS)).enhance(1.1).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    c = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", c.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 190))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    c.paste(g, (20, 20), m)
    ImageDraw.Draw(c).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=YEL, width=max(4, w // 90))
    return c.rotate(ang, expand=True, resample=Image.BICUBIC)


bg = graded(75)                                                   # finger on the glowing fingerprint sensor
# ---------------------------------------------------------------- 9:16
W, H = 1080, 1920
s = H / bg.height
big = bg.resize((int(bg.width * s), H), Image.LANCZOS)
x0 = int(min(max(800 * s - W / 2, 0), big.width - W))
c = big.crop((x0, 0, x0 + W, H)).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(170 * max(0, (y - 1450) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
cd = card(900)
c.alpha_composite(cd, ((W - cd.width) // 2, 640))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 265), "Chabi ki zarurat nahi!", 70, YEL, 9)
c.alpha_composite(emoji("😱", 76, 8), (W // 2 - 45 + int(d.textlength("Chabi ki zarurat nahi!", font=F(70)) / 2) + 10, 225))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 40, 400), "FINGERPRINT", 104, RED, 11)
c.alpha_composite(emoji("🔐", 96, -6), (W // 2 - 40 + int(d.textlength("FINGERPRINT", font=F(104)) / 2) + 12, 345))
d = ImageDraw.Draw(c)
d.rounded_rectangle((170, 500, W - 170, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Ungli rakho = Door open!", font=F(46), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 730, 1600), 50, fill=PURP)
d.text((395, 1550), "ESP32 Door Lock", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
# ---------------------------------------------------------------- 16:9
W, H = 1280, 720
c = bg.resize((W, H), Image.LANCZOS).convert("RGBA")
sh = Image.new("L", (W, 1))
sh.putdata([int(215 * max(0, 1 - x / 780)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
cd = card(520, -5)
c.alpha_composite(cd, (W - cd.width + 10, 250))
d = ImageDraw.Draw(c)
text(d, (40, 90), "Chabi ki zarurat nahi!", 62, YEL, 8, anchor="lm")
c.alpha_composite(emoji("😱", 64, 8), (40 + int(d.textlength("Chabi ki zarurat nahi!", font=F(62))) + 12, 58))
d = ImageDraw.Draw(c)
text(d, (40, 205), "FINGERPRINT", 88, RED, 9, anchor="lm")
c.alpha_composite(emoji("🔐", 80, -6), (40 + int(d.textlength("FINGERPRINT", font=F(88))) + 14, 160))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 280, 560, 355), 38, fill=CYAN)
d.text((300, 318), "Ungli rakho = Door open!", font=F(34), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 580, 680), 40, fill=PURP)
d.text((310, 640), "ESP32 Door Lock", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
