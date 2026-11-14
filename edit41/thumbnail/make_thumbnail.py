#!/usr/bin/env python3
"""Thumbnails for JARVIS Part 3 (edit41): camera-feed card with the green 'BOSS 98%' box, JARVIS orb, cyan
'JARVIS Part 3', yellow 'Mujhe PEHCHAAN liya!', purple pill. 1080x1920 (words inside y 190..1690) + 1280x720."""
import importlib.util
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b41", os.path.join(HERE, "..", "build.py"))
b41 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b41)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 220, 255), (130, 60, 255)
F_ = b41.BOSS_HIT + 20


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def feed():
    lay = Image.new("RGBA", (b41.W, b41.H))
    b41.cam_panel(lay, F_, "boss", b41.S_BOSS, b41.BOSS_HIT)
    return lay.crop((b41.PX0 - 10, b41.PY0 - 10, b41.PX0 + b41.PS + 10, b41.PY0 + b41.PS + 10))


bg = Image.fromarray(np.clip(b41.j2d.background(0), 0, 255).astype(np.uint8))
b41.j2d.orb_state = lambda ff: ("speak", ff)
W, H = 1080, 1920
c = bg.resize((W, H)).convert("RGBA")
card = feed().resize((840, 840), Image.LANCZOS).rotate(-3, expand=True, resample=Image.BICUBIC)
c.alpha_composite(card, ((W - card.width) // 2, 640))
lay = Image.new("RGBA", (W, H))
b41.j2d.draw_orb(lay, W - 190, 1500, 130, 200)
c.alpha_composite(lay)
d = ImageDraw.Draw(c)
text(d, (W // 2 - 50, 260), "JARVIS Part 3", 112, CYAN, 12)
c.alpha_composite(emoji("👀", 100), (W // 2 - 50 + int(d.textlength("JARVIS Part 3", font=F(112)) / 2) + 12, 208))
d = ImageDraw.Draw(c)
text(d, (W // 2, 405), "Mujhe PEHCHAAN liya!", 80, YEL, 10)
d.rounded_rectangle((170, 490, W - 170, 580), 45, fill=(37, 211, 102))
d.text((W // 2, 535), "Welcome back, Boss!", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 730, 1600), 50, fill=PURP)
d.text((395, 1550), "ESP32-CAM Face AI", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
W, H = 1280, 720
c = bg.resize((W, int(W * 1920 / 1080))).crop((0, 400, W, 400 + H)).convert("RGBA")
card = feed().resize((500, 500), Image.LANCZOS).rotate(-4, expand=True, resample=Image.BICUBIC)
c.alpha_composite(card, (W - card.width - 10, H - card.height - 20))
d = ImageDraw.Draw(c)
text(d, (40, 100), "JARVIS Part 3", 84, CYAN, 10, anchor="lm")
c.alpha_composite(emoji("👀", 72), (40 + int(d.textlength("JARVIS Part 3", font=F(84))) + 12, 64))
d = ImageDraw.Draw(c)
text(d, (40, 220), "Mujhe PEHCHAAN liya!", 56, YEL, 8, anchor="lm")
d.rounded_rectangle((40, 290, 560, 370), 40, fill=(37, 211, 102))
d.text((300, 330), "Welcome back, Boss!", font=F(38), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 560, 680), 40, fill=PURP)
d.text((300, 640), "ESP32-CAM Face AI", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
