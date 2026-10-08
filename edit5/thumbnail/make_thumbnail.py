#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 water-level video (blue-tank version), built on its 3D frame."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "..", "work", "frames3d_v1", "0320.png")   # full tank, OLED "TANK FULL", LEDs on
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
CYAN, YEL, RED, WHT, INK = (60, 200, 255), (255, 214, 10), (240, 40, 40), (255, 255, 255), (15, 18, 26)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
canvas = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
canvas.alpha_composite(bg.crop((0, 700, W, H)).convert("RGBA"), (0, 590))
for a0, a1, top in ((240, 860, True), (1560, 1920, False)):
    g = Image.new("L", (1, H))
    g.putdata([int(a0 * max(0, 1 - y / a1)) if top else int(230 * max(0, (y - a0) / (a1 - a0))) for y in range(H)])
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def text(d, xy, s, size, fill, stroke=None, f=FONT):
    d.text(xy, s, font=ImageFont.truetype(f, size), fill=fill, anchor="mm",
           stroke_width=stroke if stroke is not None else max(4, size // 9), stroke_fill=(0, 0, 0))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


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
    text(d, (W // 2, 130), "ESP32", 120, k or CYAN, stroke=10)
    text(d, (W // 2, 265), "WATER LEVEL", 110, k or WHT, stroke=10)
    text(d, (W // 2, 385), "INDICATOR", 100, k or WHT, stroke=9)
    d.rounded_rectangle((170, 450, W - 170, 560), 26, fill=k or RED)
    if not s:
        d.text((W // 2, 505), "TANK FULL ALERT!", font=ImageFont.truetype(FONT, 58), fill=WHT, anchor="mm")


layer(headline)


def bottom(d, s):
    k = (0, 0, 0) if s else None
    # phone notification card
    d.rounded_rectangle((90, 1500, W - 90, 1720), 40, fill=k or (245, 246, 250))
    if not s:
        d.rounded_rectangle((120, 1535, 260, 1675), 30, fill=(30, 140, 255))
        d.text((300, 1555), "SMART TANK · ESP32", font=ImageFont.truetype(BOLD, 34), fill=(90, 95, 110), anchor="lm")
        d.text((300, 1615), "Tank FULL! Motor OFF", font=ImageFont.truetype(FONT, 50), fill=INK, anchor="lm")
        d.text((300, 1675), "Level 100% · via Wi-Fi", font=ImageFont.truetype(BOLD, 34), fill=(30, 140, 255), anchor="lm")
    text(d, (W // 2, 1790), "IoT PROJECT · ECE / DIPLOMA", 50, k or YEL, stroke=6)


layer(bottom)
canvas.alpha_composite(emoji("💧", 100), (145, 1555))
canvas.alpha_composite(emoji("💧", 130, 10), (60, 560))
canvas.alpha_composite(emoji("🔔", 130, -10), (880, 570))
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((300, 1850, 780, 1905), 28, fill=(255, 107, 87))
d.text((W // 2, 1878), "@The IOT Engineer", font=ImageFont.truetype(FONT, 30), fill=WHT, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
