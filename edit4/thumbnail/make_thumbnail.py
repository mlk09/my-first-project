#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the INPUT_PULLUP video, built on the 3D hook frame."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "..", "work", "frames3d", "0060.png")   # ghost-pressed button + Arduino
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, RED, GRN, WHT = (255, 214, 10), (240, 40, 40), (40, 220, 100), (255, 255, 255)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
canvas = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
canvas.alpha_composite(bg.crop((0, 900, W, H)).convert("RGBA"), (0, 700))
for a0, a1, top in ((235, 820, True), (1420, 1920, False)):
    g = Image.new("L", (1, H))
    g.putdata([int(a0 * max(0, 1 - y / a1)) if top else int(225 * max(0, (y - a0) / (a1 - a0))) for y in range(H)])
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def text(d, xy, s, size, fill, stroke=None, f=FONT):
    d.text(xy, s, font=ImageFont.truetype(f, size), fill=fill, anchor="mm",
           stroke_width=stroke if stroke is not None else max(4, size // 9), stroke_fill=(0, 0, 0))


def layer(fn):
    sh = Image.new("RGBA", (W, H))
    fn(ImageDraw.Draw(sh), True)
    a = sh.split()[3].point(lambda v: min(170, v))
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, a)).filter(ImageFilter.GaussianBlur(10)), (0, 12))
    top = Image.new("RGBA", (W, H))
    fn(ImageDraw.Draw(top), False)
    canvas.alpha_composite(top)


def headline(d, s):
    k = (0, 0, 0) if s else None
    text(d, (W // 2, 140), "BUTTON DABAYA NAHI", 74, k or WHT, stroke=8)
    text(d, (W // 2, 230), "PHIR BHI…", 64, k or WHT, stroke=7)
    text(d, (W // 2, 400), "PRESSED?!", 168, k or RED, stroke=14)
    d.rectangle((150, 530, W - 150, 640), fill=k or YEL)
    if not s:
        d.text((W // 2, 585), "INPUT_PULLUP", font=ImageFont.truetype(MONO, 80), fill=(0, 0, 0), anchor="mm")


layer(headline)


def stickers(d, s):
    k = (0, 0, 0) if s else None
    d.rounded_rectangle((50, 1470, 525, 1660), 32, fill=k or RED, outline=(0, 0, 0), width=8)
    text(d, (287, 1525), "INPUT", 52, k or WHT, stroke=5)
    text(d, (287, 1605), "0 1 1 0 ?", 72, k or WHT, stroke=7)
    d.rounded_rectangle((555, 1470, 1030, 1660), 32, fill=k or GRN, outline=(0, 0, 0), width=8)
    text(d, (792, 1525), "INPUT_PULLUP", 46, k or WHT, stroke=5)
    text(d, (792, 1605), "1 1 1 1 ✓", 72, k or WHT, stroke=7, f=SANS)
    text(d, (W // 2, 1770), "FLOATING PIN KA RAAZ", 66, k or YEL, stroke=8)


layer(stickers)
ef = ImageFont.truetype(EMOJI, 109)
for ch, pos, size, ang in (("👻", (40, 650), 170, 12), ("🤯", (870, 650), 170, -12)):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ef, embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, pos)
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((300, 1850, 780, 1905), 28, fill=(255, 107, 87))
d.text((W // 2, 1878), "ARDUINO · CODE KA RAAZ #4", font=ImageFont.truetype(FONT, 28), fill=WHT, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
