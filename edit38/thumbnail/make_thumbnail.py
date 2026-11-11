#!/usr/bin/env python3
"""Thumbnails for the 2D 'Maine apna JARVIS bana liya' short (edit38): big glowing AI orb on the round display above
the ESP32-S3 board, yellow hook, huge cyan 'JARVIS', a chat bubble, purple pill. 1080x1920 (words inside
y 190..1690) + 1280x720."""
import importlib.util
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("j2d", os.path.join(HERE, "..", "jarvis2d.py"))
j = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(j)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 220, 255), (130, 60, 255)
F_ = 190                                                  # speaking orb frame (radial waveform)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def scene(w, h, cx, cy, s):
    bg = Image.fromarray(np.clip(j.background(0), 0, 255).astype(np.uint8)).resize((w, h)).convert("RGBA")
    lay = Image.new("RGBA", (w, h))
    j.draw_device(lay, F_, cx, cy, s)
    j.draw_orb(lay, cx, cy, 300 * s, F_)
    bg.alpha_composite(lay)
    return bg


# ---------------------------------------------------------------- 9:16
W, H = 1080, 1920
c = scene(W, H, W / 2, 980, 1.05)
d = ImageDraw.Draw(c)
text(d, (W // 2 - 40, 265), "Maine bana liya apna", 70, YEL, 9)
text(d, (W // 2 - 50, 410), "JARVIS", 170, CYAN, 14)
c.alpha_composite(emoji("🤖", 140, -6), (W // 2 - 50 + int(d.textlength("JARVIS", font=F(170)) / 2) + 14, 330))
d = ImageDraw.Draw(c)
d.rounded_rectangle((130, 560, W - 130, 660), 50, fill=(37, 211, 102))
d.text((W // 2 - 30, 610), "Jarvis, light on karo!", font=F(48), fill=INK, anchor="mm")
c.alpha_composite(emoji("💡", 58), (W // 2 + 255, 581))
d = ImageDraw.Draw(c)
d.rounded_rectangle((60, 1500, 730, 1600), 50, fill=PURP)
d.text((395, 1550), "ESP32 + ChatGPT AI", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
# ---------------------------------------------------------------- 16:9
W, H = 1280, 720
c = scene(W, H, 1050, 320, 0.6)
d = ImageDraw.Draw(c)
text(d, (40, 95), "Maine bana liya apna", 58, YEL, 8, anchor="lm")
text(d, (40, 245), "JARVIS", 150, CYAN, 12, anchor="lm")
c.alpha_composite(emoji("🤖", 110, -6), (40 + int(d.textlength("JARVIS", font=F(150))) + 14, 185))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 380, 600, 460), 40, fill=(37, 211, 102))
d.text((300, 420), "Jarvis, light on karo!", font=F(38), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 580, 680), 40, fill=PURP)
d.text((310, 640), "ESP32 + ChatGPT AI", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
