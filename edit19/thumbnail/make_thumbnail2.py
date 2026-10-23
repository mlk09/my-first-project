#!/usr/bin/env python3
"""Alternate thumbnails for the ESP32 touch-sensor short in the LED Flow thumbnail style: big yellow
'TOUCH KARO' + pink 'LED ON Ho Jaye!', cyan component pill, the wide hook shot with a finger + cyan
ripples on the pad, tilted OLED inset bottom-right and a purple tag pill. 1080x1920 Shorts cover (all
words inside the desktop-safe band y = 190..1690) + 1280x720 laptop version."""
import json
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
BGF = 16                                             # hook frame: finger on the pad, LED on
FRAME = os.path.join(WORK, "frames3d", f"{BGF:04d}.png")
OLEDF = os.path.join(WORK, "oled", "0210.png")       # MODE: LAMP  ON
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, PINK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 120, 220), (60, 220, 255), (130, 60, 255)
PX, PY, PR = json.load(open(os.path.join(WORK, "pad_xy.json")))[BGF]


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def finger(c, x, y, r):
    d = ImageDraw.Draw(c)
    for k in range(3):
        rr = r * (1.1 + 0.4 * k)
        d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), outline=CYAN + (230 - 60 * k,), width=max(4, int(r / 8) - 2 * k))
    sz = int(r * 2.6)
    c.alpha_composite(emoji("👇", sz), (int(x - sz * 0.5), int(y - sz * 0.95)))


def oled_box(w, ang):
    ol = Image.open(OLEDF).convert("RGB").resize((w, w // 2), Image.LANCZOS)
    pad = w // 26
    box = Image.new("RGBA", (w + 2 * pad, w // 2 + 2 * pad), (20, 70, 165, 255))
    box.paste(ol, (pad, pad))
    box = box.rotate(ang, expand=True, resample=Image.BICUBIC)
    glow = Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
    return box, glow.filter(ImageFilter.GaussianBlur(20))


src = ImageEnhance.Color(Image.open(FRAME).convert("RGB")).enhance(1.2)

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
Z, TX, TY = 1.3, 540, 830                             # zoom in and drop the pad below the title block
big = src.resize((int(W * Z), int(H * Z)), Image.LANCZOS)
ox, oy = int(TX - PX * Z), int(TY - PY * Z)
c = Image.new("RGBA", (W, H), (10, 12, 16, 255))
c.paste(big, (ox, oy))
PX, PY, PR = TX, TY, PR * Z
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 600)) if y < 750 else int(210 * max(0, (y - 1350) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
finger(c, PX, PY, PR)
box, glow = oled_box(480, -5)
c.alpha_composite(glow, (W - box.width - 30, 1170))
c.alpha_composite(box, (W - box.width - 40, 1160))
d = ImageDraw.Draw(c)
text(d, (W // 2, 265), "TOUCH KARO", 116, YEL, 12)
text(d, (W // 2, 400), "LED ON Ho Jaye!", 88, PINK, 10)
c.alpha_composite(emoji("👆", 110, -8), (50, 450))
d = ImageDraw.Draw(c)
d.rounded_rectangle((200, 495, W - 120, 590), 48, fill=CYAN)
d.text(((200 + W - 120) // 2, 542), "ESP32 + Touch Sensor", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 640, 1600), 50, fill=PURP)
d.text((350, 1550), "1 Touch = 3 Modes", font=F(46), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail2.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
PX, PY, PR = json.load(open(os.path.join(WORK, "pad_xy.json")))[BGF]
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
sw = 620
scale = sw / src.width
crop = src.resize((sw, int(src.height * scale)), Image.LANCZOS)
top = int(PY / 1920 * crop.height - 300)
c.alpha_composite(crop.crop((0, top, sw, top + H)).convert("RGBA"), (W - sw, 0))
fade = Image.new("L", (W, 1))
fade.putdata([255 if x < W - sw else int(255 * max(0, 1 - (x - (W - sw)) / 200)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 12)] * 3, fade.resize((W, H)))))
finger(c, W - sw + PX / 1080 * sw, PY / 1920 * crop.height - top, PR / 1080 * sw)
d = ImageDraw.Draw(c)
text(d, (40, 85), "TOUCH KARO", 96, YEL, 10, anchor="lm")
text(d, (40, 195), "LED ON Ho Jaye!", 70, PINK, 8, anchor="lm")
c.alpha_composite(emoji("👆", 80, -8), (40, 250))
d = ImageDraw.Draw(c)
d.rounded_rectangle((140, 260, 640, 335), 38, fill=CYAN)
d.text((390, 298), "ESP32 + Touch Sensor", font=F(38), fill=INK, anchor="mm")
box, glow = oled_box(300, -4)
c.alpha_composite(glow, (50, 370))
c.alpha_composite(box, (40, 362))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 610, 500, 690), 40, fill=PURP)
d.text((270, 650), "1 Touch = 3 Modes", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail2_16x9.jpg"), quality=93)
print("wrote thumbnail2.jpg + thumbnail2_16x9.jpg in", HERE)
