#!/usr/bin/env python3
"""Thumbnails for the ESP32 joystick robot arm in the LED Flow thumbnail style: big yellow
'JOYSTICK GHUMAO', pink 'ROBOT ARM CHALE!', cyan component pill, the arm carrying the red cube,
tilted OLED servo inset and a purple 'Pick & Drop' pill. 1080x1920 Shorts cover (all words inside the
desktop-safe band y = 190..1690) + 1280x720 laptop version. Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0290.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0250.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, RED, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 60, 60), (60, 220, 255), (130, 60, 255)
FOCUS = (540, 560)                                   # arm holding the cube in the carry shot


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def oled_box(w, ang):
    ol = Image.open(OLEDF).convert("RGB").resize((w, w // 2), Image.LANCZOS)
    pad = w // 26
    box = Image.new("RGBA", (w + 2 * pad, w // 2 + 2 * pad), (20, 70, 165, 255))
    box.paste(ol, (pad, pad))
    box = box.rotate(ang, expand=True, resample=Image.BICUBIC)
    glow = Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
    return box, glow.filter(ImageFilter.GaussianBlur(20))


def red_edge(c, strength=0.45):
    w, h = c.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rectangle((0, 0, w, h), outline=255, width=60)
    m = m.filter(ImageFilter.GaussianBlur(60)).point(lambda v: v * strength)
    c.alpha_composite(Image.merge("RGBA", (Image.new("L", (w, h), 255), Image.new("L", (w, h), 40), Image.new("L", (w, h), 30), m)))


src = ImageEnhance.Color(Image.open(FRAME).convert("RGB").resize((1080, 1920), Image.LANCZOS)).enhance(1.2)

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
Z, TX, TY = 1.35, 600, 900
big = src.resize((int(W * Z), int(H * Z)), Image.LANCZOS)
c = Image.new("RGBA", (W, H), (10, 12, 16, 255))
c.paste(big, (int(TX - FOCUS[0] * Z), int(TY - FOCUS[1] * Z)))
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 600)) if y < 750 else int(210 * max(0, (y - 1350) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
box, glow = oled_box(470, -5)
c.alpha_composite(glow, (W - box.width - 30, 1170))
c.alpha_composite(box, (W - box.width - 40, 1160))
d = ImageDraw.Draw(c)
text(d, (W // 2, 265), "JOYSTICK GHUMAO", 100, YEL, 11)
text(d, (W // 2, 400), "ROBOT ARM CHALE!", 86, (255, 120, 220), 10)
c.alpha_composite(emoji("🦾", 110, -8), (40, 450))
d = ImageDraw.Draw(c)
d.rounded_rectangle((190, 495, W - 120, 590), 48, fill=CYAN)
d.text(((190 + W - 120) // 2, 542), "ESP32 + 4 Servo", font=F(50), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 680, 1600), 50, fill=PURP)
d.text((370, 1550), "Pick & Drop", font=F(50), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
sw = 640
crop = src.resize((sw, int(1920 * sw / 1080)), Image.LANCZOS)
top = int(FOCUS[1] * sw / 1080 - 300)
c.alpha_composite(crop.crop((0, top, sw, top + H)).convert("RGBA"), (W - sw, 0))
fade = Image.new("L", (W, 1))
fade.putdata([255 if x < W - sw else int(255 * max(0, 1 - (x - (W - sw)) / 200)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 12)] * 3, fade.resize((W, H)))))
d = ImageDraw.Draw(c)
text(d, (40, 85), "JOYSTICK GHUMAO", 76, YEL, 9, anchor="lm")
text(d, (40, 195), "ROBOT ARM CHALE!", 66, (255, 120, 220), 8, anchor="lm")
c.alpha_composite(emoji("🦾", 76), (40 + int(d.textlength("ROBOT ARM CHALE!", font=F(66))) + 12, 158))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 268, 560, 340), 36, fill=CYAN)
d.text((300, 304), "ESP32 + 4 Servo", font=F(40), fill=INK, anchor="mm")
box, glow = oled_box(300, -4)
c.alpha_composite(glow, (50, 375))
c.alpha_composite(box, (40, 367))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 610, 470, 690), 40, fill=PURP)
d.text((255, 650), "Pick & Drop", font=F(40), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=93)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
