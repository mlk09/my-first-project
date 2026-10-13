#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for ESP32 + OLED (I2C): OLED close-up saying HELLO!, big hook
text, SDA/SCL wire chips. Optional arg: background frame path."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "work", "frames3d", "0044.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, INK = (255, 214, 10), (255, 255, 255), (15, 18, 26)
SDA_C, SCL_C = (80, 150, 255), (255, 210, 40)

canvas = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 720)) if y < 720 else int(210 * max(0, (y - 1450) / 470)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


d = ImageDraw.Draw(canvas)
text(d, (W // 2, 140), "SIRF 2 WIRE!", 128, YEL, 12)
text(d, (W // 2, 285), "ESP32 + OLED", 104, WHT, 10)
canvas.alpha_composite(emoji("🤯", 130, -8), (W // 2 - 65, 1410))
d.rounded_rectangle((130, 390, W - 130, 490), 50, fill=(60, 220, 255))
d.text((W // 2, 440), "I2C Display Tutorial", font=ImageFont.truetype(FONT, 52), fill=INK, anchor="mm")
for i, (lab, sub, col) in enumerate((("SDA", "Data", SDA_C), ("SCL", "Clock", SCL_C))):
    x0 = 90 + i * 470
    d.rounded_rectangle((x0, 1560, x0 + 430, 1700), 40, fill=col)
    d.text((x0 + 215, 1610), lab, font=ImageFont.truetype(FONT, 60), fill=INK, anchor="mm")
    d.text((x0 + 215, 1668), sub, font=ImageFont.truetype(FONT, 34), fill=INK, anchor="mm")
d.rounded_rectangle((40, 1790, 520, 1870), 40, fill=WHT)
d.text((280, 1830), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
