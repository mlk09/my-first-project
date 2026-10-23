#!/usr/bin/env python3
"""Thumbnails for the ESP32 + OLED + TTP223 touch-sensor '3 modes' short: a 1080x1920 Shorts cover
(all words inside the desktop-safe band y = 190..1690) and a 1280x720 laptop version. Background =
close-up of the touch pad with a finger pressing it + ripples, '1 TOUCH = 3 KAAM!' and the three
mode chips (LAMP / BELL / COUNTER). Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0150.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0215.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, CYAN = (255, 214, 10), (255, 255, 255), (15, 18, 26), (60, 220, 255)
CHIPS = [("💡", "LAMP", (255, 190, 40)), ("🔔", "BELL", (255, 120, 60)), ("🔢", "COUNTER", (60, 220, 255))]


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def ripples(d, cx, cy, r):
    for k in range(3):
        rr = r * (1.0 + 0.35 * k)
        d.ellipse((cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8), outline=CYAN + (230 - 60 * k,), width=10 - 2 * k)


def oled_inset(w, ang):
    ol = Image.open(OLEDF).convert("RGB").resize((w, w // 2), Image.LANCZOS)
    pad = w // 24
    box = Image.new("RGBA", (w + 2 * pad, w // 2 + 2 * pad), (20, 70, 165, 255))
    box.paste(ol, (pad, pad))
    return box.rotate(ang, expand=True, resample=Image.BICUBIC)


def chip(c, d, cx, cy, ic, name, col, w, h, fs):
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), h / 2, fill=col, outline=WHT, width=5)
    c.alpha_composite(emoji(ic, int(h * 0.62)), (int(cx - w / 2 + h * 0.2), int(cy - h * 0.31)))
    d.text((cx + h * 0.28, cy), name, font=F(fs), fill=INK, anchor="mm")


def shade(c, top, bottom):
    w, h = c.size
    g = Image.new("L", (1, h))
    g.putdata([int(235 * max(0, 1 - (y - top[0]) / top[1])) if y < top[0] + top[1] else
               int(220 * max(0, (y - bottom[0]) / bottom[1])) for y in range(h)])
    c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), 0)] * 3, g.resize((w, h)))))


src = ImageEnhance.Color(Image.open(FRAME).convert("RGB")).enhance(1.25)

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
c = src.resize((W, H), Image.LANCZOS).convert("RGBA")
shade(c, (150, 600), (1250, 450))
d = ImageDraw.Draw(c)
PX, PY, PR = 540, 960, 230                                     # pad centre in the close-up
ripples(d, PX, PY, PR)
c.alpha_composite(emoji("👇", 330, 0), (PX - 165, PY - 330))
d = ImageDraw.Draw(c)
text(d, (W // 2, 270), "1 TOUCH =", 110, WHT, 10)
text(d, (W // 2, 410), "3 KAAM!", 150, YEL, 13)
for k, (ic, name, col) in enumerate(CHIPS):
    chip(c, d, W // 2, 1250 + k * 105, ic, name, col, 470, 90, 46)
    d = ImageDraw.Draw(c)
d.rounded_rectangle((140, 1570, W - 140, 1640), 35, fill=WHT)
d.text((W // 2, 1605), "ESP32 + Touch Sensor + OLED", font=F(40), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
sw = 640
crop = src.resize((sw, int(sw * src.height / src.width)), Image.LANCZOS)
top = int(crop.height * 0.5 - H / 2)
c.alpha_composite(crop.crop((0, top, sw, top + H)).convert("RGBA"), (W - sw, 0))
fade = Image.new("L", (W, 1))
fade.putdata([255 if x < W - sw else int(255 * max(0, 1 - (x - (W - sw)) / 200)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 12)] * 3, fade.resize((W, H)))))
d = ImageDraw.Draw(c)
px, py, pr = W - sw // 2, H // 2, int(PR * sw / 1080)
ripples(d, px, py, pr)
c.alpha_composite(emoji("👇", 210), (px - 105, py - 210))
d = ImageDraw.Draw(c)
text(d, (40, 95), "1 TOUCH =", 86, WHT, 8, anchor="lm")
text(d, (40, 215), "3 KAAM!", 120, YEL, 11, anchor="lm")
for k, (ic, name, col) in enumerate(CHIPS):
    chip(c, d, 250, 350 + k * 88, ic, name, col, 400, 74, 38)
    d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 625, 600, 690), 33, fill=WHT)
d.text((320, 658), "ESP32 + Touch Sensor + OLED", font=F(32), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=93)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
