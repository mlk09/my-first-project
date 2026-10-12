#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 RFID door lock: key fob on the reader with the
green LED lit, ACCESS GRANTED badge, big hook text. Pass a frame path to override the default."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "work", "frames3d", "0232.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, GRN, INK = (255, 214, 10), (255, 255, 255), (40, 230, 110), (15, 18, 26)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
canvas = bg.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 760)) if y < 760 else int(210 * max(0, (y - 1420) / 500)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


d = ImageDraw.Draw(canvas)
text(d, (W // 2, 140), "SMART DOOR", 132, WHT, 12)
text(d, (W // 2, 290), "LOCK!", 150, YEL, 13)
canvas.alpha_composite(emoji("🔐", 130, -10), (110, 215))
canvas.alpha_composite(emoji("🚪", 130, 10), (W - 240, 215))
d.rounded_rectangle((110, 410, W - 110, 520), 55, fill=(60, 220, 255))
d.text((W // 2, 465), "ESP32 + RFID RC522", font=ImageFont.truetype(FONT, 56), fill=INK, anchor="mm")
# glow ring around the reader area
ring = Image.new("RGBA", (W, H))
ImageDraw.Draw(ring).ellipse((180, 760, 760, 1340), outline=GRN + (255,), width=14)
canvas.alpha_composite(ring.filter(ImageFilter.GaussianBlur(10)))
canvas.alpha_composite(ring)
# ACCESS GRANTED card
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((70, 1500, W - 70, 1700), 40, fill=(8, 12, 18, 235), outline=GRN, width=6)
d.text((130, 1560), "ACCESS GRANTED", font=ImageFont.truetype(FONT, 62), fill=GRN, anchor="lm")
d.text((130, 1645), "UID: 4A 2F 9C 11", font=ImageFont.truetype(MONO, 44), fill=(200, 210, 225), anchor="lm")
canvas.alpha_composite(emoji("✅", 110), (W - 200, 1545))
d.rounded_rectangle((40, 1790, 520, 1870), 40, fill=(255, 255, 255))
d.text((280, 1830), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
d.rounded_rectangle((560, 1790, W - 40, 1870), 40, fill=(255, 60, 60))
d.text(((560 + W - 40) // 2, 1830), "Bina chaabi!", font=ImageFont.truetype(FONT, 38), fill=WHT, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
