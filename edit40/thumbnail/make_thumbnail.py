#!/usr/bin/env python3
"""Thumbnails for JARVIS Part 2 (edit40): the user's real balancing robot (PID ON frame) with the JARVIS orb,
cyan 'JARVIS Part 2', yellow 'Awaaz se Robot chala!', green command bubble, purple pill.
1080x1920 (words inside y 190..1690) + 1280x720."""
import importlib.util
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_spec = importlib.util.spec_from_file_location("b40", os.path.join(HERE, "..", "build.py"))
b40 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b40)
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 220, 255), (130, 60, 255)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


real = Image.open(os.path.join(b40.SRC, "0170.png")).convert("RGB")
real = ImageEnhance.Contrast(real).enhance(1.08)
W, H = 1080, 1920
c = real.resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([240 if y < 640 else (int(240 * max(0, 1 - (y - 640) / 200)) if y < 1000 else int(170 * max(0, (y - 1450) / 450))) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 50, 250), "JARVIS Part 2", 112, CYAN, 12)
c.alpha_composite(emoji("🤖", 104, -6), (W // 2 - 50 + int(d.textlength("JARVIS Part 2", font=F(112)) / 2) + 12, 196))
d = ImageDraw.Draw(c)
text(d, (W // 2, 395), "Awaaz se Robot chala!", 78, YEL, 10)
d.rounded_rectangle((170, 480, W - 170, 580), 50, fill=(37, 211, 102))
d.text((W // 2 - 30, 530), "\"Jarvis, aage chalo!\"", font=F(50), fill=INK, anchor="mm")
c.alpha_composite(emoji("🗣️", 60), (W - 250, 500))
lay = Image.new("RGBA", (W, H))
b40.j2d.orb_state = lambda ff: ("speak", ff)
b40.j2d.draw_orb(lay, W - 190, 820, 140, 200)
c.alpha_composite(lay)
d = ImageDraw.Draw(c)
d.rounded_rectangle((60, 1500, 730, 1600), 50, fill=PURP)
d.text((395, 1550), "ESP32 Self-Balancing", font=F(46), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)
W, H = 1280, 720
big = real.resize((W, int(W * real.height / real.width)), Image.LANCZOS)
c = big.crop((0, 900, W, 900 + H)).convert("RGBA")
sh = Image.new("L", (W, 1))
sh.putdata([int(215 * max(0, 1 - x / 760)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, sh.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (40, 95), "JARVIS Part 2", 96, CYAN, 10, anchor="lm")
c.alpha_composite(emoji("🤖", 84, -6), (40 + int(d.textlength("JARVIS Part 2", font=F(96))) + 14, 50))
d = ImageDraw.Draw(c)
text(d, (40, 215), "Awaaz se Robot chala!", 62, YEL, 8, anchor="lm")
d.rounded_rectangle((40, 290, 600, 370), 40, fill=(37, 211, 102))
d.text((320, 330), "\"Jarvis, aage chalo!\"", font=F(38), fill=INK, anchor="mm")
lay = Image.new("RGBA", (W, H))
b40.j2d.draw_orb(lay, 1110, 170, 110, 200)
c.alpha_composite(lay)
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 600, 580, 680), 40, fill=PURP)
d.text((310, 640), "ESP32 Self-Balancing", font=F(36), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnails in", HERE)
