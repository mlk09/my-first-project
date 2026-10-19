#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 + OLED Rock-Paper-Scissors robot: robot box close-up,
big hook text, BOT vs YOU scoreboard, hand emojis. Optional arg: background frame."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "work", "frames3d", "0040.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, INK, GRN, RED = (255, 214, 10), (255, 255, 255), (15, 18, 26), (40, 230, 110), (255, 60, 60)

canvas = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 640)) if y < 640 else int(225 * max(0, (y - 1300) / 520)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


d = ImageDraw.Draw(canvas)
text(d, (W // 2, 130), "ROBOT KO", 130, WHT, 12)
text(d, (W // 2, 270), "HARAO!", 150, YEL, 13)
d.rounded_rectangle((110, 380, W - 110, 480), 50, fill=(60, 220, 255))
d.text((W // 2, 430), "Rock Paper Scissors • ESP32", font=ImageFont.truetype(FONT, 46), fill=INK, anchor="mm")
canvas.alpha_composite(emoji("✊", 130, -12), (40, 520))
canvas.alpha_composite(emoji("✌️", 130, 12), (W - 180, 520))
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((120, 1450, W - 120, 1700), 70, fill=(10, 12, 18, 230), outline=(255, 255, 255, 160), width=4)
canvas.alpha_composite(emoji("🤖", 160), (150, 1495))
canvas.alpha_composite(emoji("🧑", 160), (W - 310, 1495))
d = ImageDraw.Draw(canvas)
text(d, (W // 2 - 110, 1575), "1", 170, RED, 12)
text(d, (W // 2, 1565), ":", 140, WHT, 10)
text(d, (W // 2 + 110, 1575), "3", 170, GRN, 12)
d.rounded_rectangle((40, 1790, 520, 1870), 40, fill=WHT)
d.text((280, 1830), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
