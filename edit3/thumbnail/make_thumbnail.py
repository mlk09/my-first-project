#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the millis() vs delay() video, built on a 3D render frame."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "..", "work", "frames3d", "0790.png")   # delay lane frozen at the red wall
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, RED, GRN, WHT = (255, 214, 10), (240, 40, 40), (40, 220, 100), (255, 255, 255)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
canvas = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
canvas.alpha_composite(bg.crop((0, 250, W, H)).convert("RGBA"), (0, 470))
for top, a0, a1 in ((True, 240, 820), (False, 1430, 1920)):
    g = Image.new("L", (1, H))
    if top:
        g.putdata([int(a0 * max(0, 1 - y / a1)) for y in range(H)])
    else:
        g.putdata([int(225 * max(0, (y - a0) / (a1 - a0))) for y in range(H)])
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def text(d, xy, s, size, fill, stroke=None):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm",
           stroke_width=stroke if stroke is not None else max(4, size // 9), stroke_fill=(0, 0, 0))


def layer(fn):
    sh = Image.new("RGBA", (W, H))
    fn(ImageDraw.Draw(sh), True)
    a = sh.split()[3].point(lambda v: min(170, v))
    sh = Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, a)).filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(sh, (0, 12))
    top = Image.new("RGBA", (W, H))
    fn(ImageDraw.Draw(top), False)
    canvas.alpha_composite(top)


def headline(d, s):
    k = (0, 0, 0) if s else None
    text(d, (W // 2, 170), "millis()", 190, k or GRN, stroke=16)
    text(d, (W // 2, 330), "VS", 90, k or WHT, stroke=8)
    text(d, (W // 2, 490), "delay()", 190, k or RED, stroke=16)


layer(headline)


def stickers(d, s):
    k = (0, 0, 0) if s else None
    d.rounded_rectangle((50, 1470, 525, 1660), 32, fill=k or RED, outline=(0, 0, 0), width=8)
    text(d, (287, 1525), "delay()", 52, k or WHT, stroke=5)
    text(d, (287, 1605), "RUKO!", 84, k or WHT, stroke=7)
    d.rounded_rectangle((555, 1470, 1030, 1660), 32, fill=k or GRN, outline=(0, 0, 0), width=8)
    text(d, (792, 1525), "millis()", 52, k or WHT, stroke=5)
    text(d, (792, 1605), "CHALO!", 84, k or WHT, stroke=7)
    text(d, (W // 2, 1770), "PROGRAM RUKTA KYUN?", 68, k or YEL, stroke=8)


layer(stickers)

ef = ImageFont.truetype(EMOJI, 109)
for ch, pos, size, ang in (("⏱️", (60, 560), 170, 12), ("🤯", (850, 560), 170, -12), ("✋", (40, 1320), 140, 10),
                           ("🏃", (900, 1320), 140, -8)):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ef, embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, pos)

d = ImageDraw.Draw(canvas)
d.rounded_rectangle((300, 1850, 780, 1905), 28, fill=(255, 107, 87))
d.text((W // 2, 1878), "ARDUINO · CODE KA RAAZ #3", font=ImageFont.truetype(FONT, 28), fill=WHT, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
