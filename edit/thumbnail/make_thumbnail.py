#!/usr/bin/env python3
"""Build the 1080x1920 thumbnail for the ÷2 short from the raw clip's final frame."""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
FONT = os.path.join(HERE, "..", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SRC = os.path.join(ROOT, "IoT-Short-Ultrasonic-Divide2-Canva-28sec.mp4")
FRAME = os.path.join(HERE, "..", "work", "end.png")
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, RED, GRN, WHT = (255, 225, 26), (255, 50, 50), (60, 225, 100), (255, 255, 255)

if not os.path.exists(FRAME):
    os.makedirs(os.path.dirname(FRAME), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "27.3", "-i", SRC, "-frames:v", "1", FRAME], check=True)
frame = Image.open(FRAME).convert("RGB")

# background: purple -> blue -> teal gradient like the clip, with a soft glow
grad = Image.new("RGB", (1, 3))
grad.putdata([(110, 50, 200), (40, 70, 210), (30, 150, 160)])
bg = grad.resize((W, H), Image.BICUBIC)
glow = Image.new("L", (W, H), 0)
ImageDraw.Draw(glow).ellipse((90, 160, 990, 760), fill=110)
bg.paste((255, 225, 120), mask=glow.filter(ImageFilter.GaussianBlur(120)))
canvas = bg.convert("RGBA")


def text(draw, xy, s, size, fill, stroke=None, anchor="mm"):
    f = ImageFont.truetype(FONT, size)
    sw = stroke if stroke is not None else max(4, size // 9)
    draw.text(xy, s, font=f, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0), anchor=anchor)


def shadowed(layer_fn, blur=10, offset=(0, 12), alpha=180):
    sh = Image.new("RGBA", (W, H))
    layer_fn(ImageDraw.Draw(sh), shadow=True)
    a = sh.split()[3].point(lambda v: min(alpha, v))
    sh = Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, a)).filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, offset)
    top = Image.new("RGBA", (W, H))
    layer_fn(ImageDraw.Draw(top), shadow=False)
    canvas.alpha_composite(top)


# diagram card: crop sensor -> waves -> wall from the final frame, enlarge, tilt
card = frame.crop((49, 520, 1031, 1090)).resize((1000, 580), Image.LANCZOS).convert("RGBA")
mask = Image.new("L", card.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, *card.size), 36, fill=255)
card.putalpha(mask)
border = Image.new("RGBA", (card.width + 24, card.height + 24))
ImageDraw.Draw(border).rounded_rectangle((0, 0, *border.size), 46, fill=(255, 225, 26, 255))
border.alpha_composite(card, (12, 12))
border = border.rotate(-3, expand=True, resample=Image.BICUBIC)
sh = Image.new("RGBA", border.size, (0, 0, 0, 0))
sh.putalpha(border.split()[3].point(lambda v: 150 if v else 0))
sh = sh.filter(ImageFilter.GaussianBlur(18))
cx, cy = (W - border.width) // 2, 780
canvas.alpha_composite(sh, (cx, cy + 20))
canvas.alpha_composite(border, (cx, cy))


def headline(d, shadow):
    k = (0, 0, 0) if shadow else None
    text(d, (W // 2, 170), "CODE MEIN", 110, k or WHT)
    text(d, (W // 2, 420), "÷2", 320, k or YEL, stroke=22)
    text(d, (W // 2, 655), "KYUN?", 140, k or WHT)


shadowed(headline)


def labels(d, shadow):
    k = (0, 0, 0) if shadow else None
    # red sticker: what the sensor reads
    d.rounded_rectangle((70, 1440, 520, 1590), 30, fill=k or RED, outline=(0, 0, 0), width=8)
    text(d, (295, 1488), "SENSOR", 46, k or WHT, stroke=5)
    text(d, (295, 1550), "40 CM", 70, k or WHT, stroke=6)
    # green sticker: the real distance
    d.rounded_rectangle((560, 1440, 1010, 1590), 30, fill=k or GRN, outline=(0, 0, 0), width=8)
    text(d, (785, 1488), "ASLI", 46, k or WHT, stroke=5)
    text(d, (785, 1550), "20 CM", 70, k or WHT, stroke=6)
    text(d, (W // 2, 1740), "WAVE DO BAAR CHALI!", 66, k or YEL, stroke=8)


shadowed(labels)

# emoji accents
ef = ImageFont.truetype(EMOJI, 109)
for ch, pos, size, ang in (("🤯", (800, 330), 190, -12), ("😳", (40, 1300), 150, 10)):
    im = Image.new("RGBA", (140, 140))
    ImageDraw.Draw(im).text((8, 8), ch, font=ef, embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, pos)

# small brand tag
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((340, 1820, 740, 1880), 30, fill=(255, 107, 87))
text(d, (W // 2, 1850), "HC-SR04 • ARDUINO", 30, WHT, stroke=0)

canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
