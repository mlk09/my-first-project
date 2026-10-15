#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 + OLED robot eyes: OLED close-up with the eyes, a strip
of four mood screens (happy / angry / sleepy / love), big hook text. Optional arg: background frame."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0030.png")
OLED = os.path.join(WORK, "oled")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, INK = (255, 214, 10), (255, 255, 255), (15, 18, 26)
MOODS = [("0230", "KHUSH", (40, 230, 110)), ("0310", "GUSSA", (255, 60, 60)),
         ("0390", "NEEND", (90, 140, 255)), ("0430", "PYAAR", (255, 90, 170))]

canvas = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 640)) if y < 640 else int(225 * max(0, (y - 1250) / 520)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


d = ImageDraw.Draw(canvas)
text(d, (W // 2, 140), "ROBOT EYES", 140, YEL, 13)
text(d, (W // 2, 290), "Jo Feel Karti Hain!", 84, WHT, 9)
canvas.alpha_composite(emoji("👀", 120, -8), (40, 340))
d.rounded_rectangle((200, 400, W - 110, 500), 50, fill=(60, 220, 255))
d.text(((200 + W - 110) // 2, 450), "ESP32 + OLED + Touch", font=ImageFont.truetype(FONT, 50), fill=INK, anchor="mm")
for i, (fr, name, col) in enumerate(MOODS):                    # 2x2 mood strip
    x0, y0 = 60 + (i % 2) * 490, 1300 + (i // 2) * 260
    sc = Image.open(os.path.join(OLED, f"{fr}.png")).convert("RGB").resize((290, 145), Image.LANCZOS)
    tile = Image.new("RGBA", (470, 230), col + (255,))
    tile.paste(sc, (18, 42))
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 160))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x0 + 8, y0 + 10))
    canvas.alpha_composite(tile, (x0, y0))
    ImageDraw.Draw(canvas).text((x0 + 390, y0 + 115), name, font=ImageFont.truetype(FONT, 28), fill=INK, anchor="mm")
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((40, 1830, 520, 1900), 35, fill=WHT)
d.text((280, 1865), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
