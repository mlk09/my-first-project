#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the Serial.begin(9600) video, built on a 3D render frame."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "..", "work", "frames_v1", "0470.png")   # red X over 115200 laptop
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, RED, GRN, WHT = (255, 225, 26), (255, 45, 45), (40, 225, 100), (255, 255, 255)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
# push the 3D shot down a bit so the headline has room, fill the top with its own blurred colour
canvas = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
shot = bg.crop((0, 150, W, H)).convert("RGBA")
canvas.alpha_composite(shot, (0, 330))
# dark gradient behind the headline
grad = Image.new("L", (1, H))
grad.putdata([int(235 * max(0, 1 - y / 760)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, grad.resize((W, H)))))
bot = Image.new("L", (1, H))
bot.putdata([int(220 * max(0, (y - 1450) / 470)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, bot.resize((W, H)))))


def text(d, xy, s, size, fill, stroke=None, anchor="mm"):
    f = ImageFont.truetype(FONT, size)
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke if stroke is not None else max(4, size // 9),
           stroke_fill=(0, 0, 0), anchor=anchor)


def layer(fn, shadow=True):
    if shadow:
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
    text(d, (W // 2, 140), "Serial.begin(", 92, k or WHT)
    text(d, (W // 2 - 60, 330), "9600", 250, k or GRN, stroke=20)
    text(d, (W // 2 + 340, 300), ")", 200, k or WHT, stroke=16)
    # yellow box like the video's title card
    f = ImageFont.truetype(FONT, 86)
    tw = d.textlength("KYA HAI?", font=f)
    d.rectangle((W // 2 - tw / 2 - 30, 470, W // 2 + tw / 2 + 30, 580), fill=k or YEL)
    if not s:
        d.text((W // 2, 525), "KYA HAI?", font=f, fill=(0, 0, 0), anchor="mm")


layer(headline)


def stickers(d, s):
    k = (0, 0, 0) if s else None
    d.rounded_rectangle((60, 1500, 515, 1680), 32, fill=k or GRN, outline=(0, 0, 0), width=8)
    text(d, (287, 1555), "CODE", 50, k or WHT, stroke=5)
    text(d, (287, 1628), "9600", 84, k or WHT, stroke=7)
    d.rounded_rectangle((565, 1500, 1020, 1680), 32, fill=k or RED, outline=(0, 0, 0), width=8)
    text(d, (792, 1555), "MONITOR", 50, k or WHT, stroke=5)
    text(d, (792, 1628), "115200", 84, k or WHT, stroke=7)
    d.text((W // 2, 1590), "≠", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 130),
           fill=k or YEL, stroke_width=10, stroke_fill=(0, 0, 0), anchor="mm")
    text(d, (W // 2, 1775), "GARBAGE KYUN AAYA?", 70, k or YEL, stroke=8)


layer(stickers)

ef = ImageFont.truetype(EMOJI, 109)
for ch, pos, size, ang in (("🤯", (860, 590), 170, -12), ("😱", (40, 1330), 150, 10)):
    im = Image.new("RGBA", (140, 140))
    ImageDraw.Draw(im).text((8, 8), ch, font=ef, embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, pos)

d = ImageDraw.Draw(canvas)
d.rounded_rectangle((300, 1850, 780, 1905), 28, fill=(255, 107, 87))
text(d, (W // 2, 1878), "ARDUINO · CODE KA RAAZ #2", 28, WHT, stroke=0)

canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
