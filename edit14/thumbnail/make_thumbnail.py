#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 + OLED rotary-encoder LED flow: rainbow LED row + knob,
OLED inset (step counter + arrows), big hook text. Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0430.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0230.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, INK, RED = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 60, 60)

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


# OLED radar inset with a glowing frame
ol = Image.open(OLEDF).convert("RGB").resize((560, 280), Image.LANCZOS)
box = Image.new("RGBA", (600, 320), (20, 70, 165, 255))
box.paste(ol, (20, 20))
box = box.rotate(-5, expand=True, resample=Image.BICUBIC)
glow = Image.new("RGBA", box.size)
glow.putalpha(box.split()[3])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
                       .filter(ImageFilter.GaussianBlur(20)), (W - box.width - 30, 1240))
canvas.alpha_composite(box, (W - box.width - 40, 1230))

d = ImageDraw.Draw(canvas)
text(d, (W // 2, 140), "KNOB GHUMAO", 124, YEL, 12)
text(d, (W // 2, 285), "LED Ka Jaadu!", 96, (255, 120, 220), 10)
canvas.alpha_composite(emoji("🌈", 120, -8), (40, 330))
d.rounded_rectangle((200, 390, W - 120, 490), 50, fill=(60, 220, 255))
d.text(((200 + W - 120) // 2, 440), "ESP32 + Rotary Encoder", font=ImageFont.truetype(FONT, 48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1600, 640, 1700), 50, fill=(130, 60, 255))
d.text((350, 1650), "Rainbow LED Flow", font=ImageFont.truetype(FONT, 46), fill=WHT, anchor="mm")
d.rounded_rectangle((40, 1790, 520, 1870), 40, fill=WHT)
d.text((280, 1830), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
