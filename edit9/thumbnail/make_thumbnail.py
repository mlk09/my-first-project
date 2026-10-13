#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 self-balancing robot: PID OFF (fallen) vs PID ON
(standing) split, big hook text. Optional args: <standing frame> <fallen frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F3D = os.path.join(HERE, "..", "work", "frames3d")
STAND = sys.argv[1] if len(sys.argv) > 1 else os.path.join(F3D, "0340.png")
FALLEN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(F3D, "0040.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, GRN, RED, INK = (255, 214, 10), (255, 255, 255), (40, 230, 110), (255, 60, 60), (15, 18, 26)

canvas = Image.open(STAND).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 700)) if y < 700 else int(200 * max(0, (y - 1500) / 420)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


# 'before' inset: fallen robot, red frame + X
fb = Image.open(FALLEN).convert("RGB").resize((360, 640), Image.LANCZOS).crop((0, 140, 360, 560))
inset = Image.new("RGBA", (380, 440), RED + (255,))
inset.paste(fb, (10, 10))
inset = inset.rotate(6, expand=True, resample=Image.BICUBIC)
sh = Image.new("RGBA", inset.size)
sh.putalpha(inset.split()[3].point(lambda v: min(v, 160)))
canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (40, 1150))
canvas.alpha_composite(inset, (25, 1130))
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((60, 1110, 330, 1180), 35, fill=RED)
d.text((195, 1145), "PID OFF", font=ImageFont.truetype(FONT, 40), fill=WHT, anchor="mm")
canvas.alpha_composite(emoji("❌", 110), (290, 1420))
# 'after' tag on the standing robot
d.rounded_rectangle((W - 360, 700, W - 60, 775), 38, fill=GRN)
d.text((W - 210, 738), "PID ON", font=ImageFont.truetype(FONT, 44), fill=INK, anchor="mm")
canvas.alpha_composite(emoji("✅", 90), (W - 150, 790))

text(d, (W // 2, 140), "GIRTA NAHI!", 140, YEL, 13)
text(d, (W // 2, 290), "Self-Balancing Robot", 72, WHT, 8)
canvas.alpha_composite(emoji("🤖", 120, -8), (60, 360))
d.rounded_rectangle((210, 400, W - 110, 500), 50, fill=(60, 220, 255))
d.text(((210 + W - 110) // 2, 450), "ESP32 + MPU6050 + PID", font=ImageFont.truetype(FONT, 48), fill=INK, anchor="mm")
d.rounded_rectangle((40, 1790, 520, 1870), 40, fill=WHT)
d.text((280, 1830), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
