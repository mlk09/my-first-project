#!/usr/bin/env python3
"""Thumbnails for the colourised B&W Car Racing short (edit31): moody B&W hand + console frame with only the
LEDs / screens in colour (same look as the video), a big neon game card from the colourised full-screen
racing shot, yellow 'Ye MOBILE nahi hai!', pink 'CAR RACING', cyan / purple pills. 1080x1920 cover (all
words inside the desktop-safe band y = 190..1690) + 1280x720 laptop version."""
import importlib.util
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b31", os.path.join(HERE, "..", "build.py"))
b31 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b31)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, PINK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 120, 220), (60, 220, 255), (130, 60, 255)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def clip(f):
    im = cv2.cvtColor(cv2.imread(os.path.join(b31.SRC, f"{f:04d}.png")), cv2.COLOR_BGR2RGB)
    return Image.fromarray(b31.colorize(im, f))


def game_card(w, ang=-4):
    """Neon racing screen (colourised full-screen game shot, the NITRO view) with a yellow frame."""
    g = clip(176).crop((22, 255, 698, 760))                    # top game screen incl. score
    h = int(w * g.height / g.width)
    g = ImageEnhance.Color(g.resize((w, h), Image.LANCZOS)).enhance(1.25).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    card = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", card.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 180))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    card.paste(g, (20, 20), m)
    ImageDraw.Draw(card).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=YEL, width=max(4, w // 90))
    return card.rotate(ang, expand=True, resample=Image.BICUBIC)


bg_src = clip(150).crop((205, 600, 588, 1280)).resize((1080, 1920), Image.LANCZOS)   # knob + glowing red / green LEDs (no captions)
bg_src = bg_src.filter(ImageFilter.GaussianBlur(2))

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
c = bg_src.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(160 * max(0, (y - 1450) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
card = game_card(900)
c.alpha_composite(card, ((W - card.width) // 2, 610))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 265), "Ye MOBILE nahi hai!", 80, YEL, 10)
c.alpha_composite(emoji("😱", 84, 8), (W // 2 - 45 + int(d.textlength("Ye MOBILE nahi hai!", font=F(80)) / 2) + 8, 218))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 400), "CAR RACING", 112, PINK, 11)
c.alpha_composite(emoji("🏎️", 110, -6), (W // 2 - 45 + int(d.textlength("CAR RACING", font=F(112)) / 2) + 10, 340))
d = ImageDraw.Draw(c)
d.rounded_rectangle((190, 500, W - 190, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Knob = Steering!", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 690, 1600), 50, fill=PURP)
d.text((375, 1550), "ESP32 + OLED Game", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (8, 8, 10, 255))
bg = bg_src.resize((W, int(W * 1920 / 1080)), Image.LANCZOS).crop((0, 700, W, 700 + H))
c.alpha_composite(ImageEnhance.Brightness(bg).enhance(0.8).convert("RGBA"))
sh = Image.new("L", (W, 1))
sh.putdata([int(200 * max(0, 1 - x / 760)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
card = game_card(540, -5)
c.alpha_composite(card, (W - card.width + 10, 250))
d = ImageDraw.Draw(c)
text(d, (40, 90), "Ye MOBILE nahi hai!", 74, YEL, 9, anchor="lm")
c.alpha_composite(emoji("😱", 74, 8), (40 + int(d.textlength("Ye MOBILE nahi hai!", font=F(74))) + 12, 50))
d = ImageDraw.Draw(c)
text(d, (40, 205), "CAR RACING", 96, PINK, 9, anchor="lm")
c.alpha_composite(emoji("🏎️", 90, -6), (40 + int(d.textlength("CAR RACING", font=F(96))) + 14, 155))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Knob = Steering!", font=F(38), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + OLED Game", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
