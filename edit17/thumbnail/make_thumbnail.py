#!/usr/bin/env python3
"""Thumbnails for the ESP32 + OLED + HC-SR04 object-detection alarm: a 1080x1920 Shorts cover
(mobile) and a 1280x720 version (laptop / desktop feed). Background = block right in front of the
sensor with the red LED on, OLED 'WARNING!' inset, big hook text and a distance badge.
Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0320.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0320.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
sys.path.insert(0, os.path.join(HERE, ".."))
from timeline import dist  # noqa: E402

FR = int(os.path.basename(OLEDF)[:4])
YEL, WHT, INK, RED, GRN = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 60, 60), (40, 230, 110)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def red_edge(canvas, strength=0.45):
    w, h = canvas.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rectangle((0, 0, w, h), outline=255, width=60)
    m = m.filter(ImageFilter.GaussianBlur(60)).point(lambda v: v * strength)
    canvas.alpha_composite(Image.merge("RGBA", (Image.new("L", (w, h), 255), Image.new("L", (w, h), 40),
                                                Image.new("L", (w, h), 30), m)))


def oled_inset(w, ang):
    ol = Image.open(OLEDF).convert("RGB").resize((w, w // 2), Image.LANCZOS)
    pad = w // 24
    box = Image.new("RGBA", (w + 2 * pad, w // 2 + 2 * pad), (20, 70, 165, 255))
    box.paste(ol, (pad, pad))
    box = box.rotate(ang, expand=True, resample=Image.BICUBIC)
    glow = Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
    return box, glow.filter(ImageFilter.GaussianBlur(20))


def badge(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED, outline=WHT, width=max(6, r // 14))
    d.text((cx, cy - r * 0.15), f"{dist(FR):.0f} cm", font=F(int(r * 0.5)), fill=WHT, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d.text((cx, cy + r * 0.4), "ALERT!", font=F(int(r * 0.3)), fill=YEL, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))


src = Image.open(FRAME).convert("RGB")

# ---------------------------------------------------------------- 9:16 Shorts cover (mobile)
# Desktop YouTube crops ~140 px off the top and bottom of a Shorts cover (and puts a "New" chip
# top-left), so every word stays inside the safe band y = 190..1690.
W, H = 1080, 1920
c = src.resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 600)) if y < 750 else int(210 * max(0, (y - 1350) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
red_edge(c)
box, glow = oled_inset(420, 5)
c.alpha_composite(glow, (50, 1150))
c.alpha_composite(box, (40, 1140))
d = ImageDraw.Draw(c)
text(d, (W // 2, 260), "KOI PAAS AAYA?", 96, YEL, 10)
text(d, (W // 2 - 50, 400), "WARNING!", 124, RED, 12)
c.alpha_composite(emoji("🚨", 104), (W - 200, 345))
d = ImageDraw.Draw(c)
d.rounded_rectangle((110, 495, W - 110, 585), 45, fill=WHT)
d.text((W // 2, 540), "ESP32 + Ultrasonic + OLED", font=F(46), fill=INK, anchor="mm")
badge(d, W - 190, 1250, 135)
d.rounded_rectangle((60, 1500, 840, 1600), 50, fill=(255, 120, 30))
d.text((450, 1550), "Object Detection Alarm", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=93)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
sw = 620                                                       # right: the 3D shot (centre crop)
crop = src.resize((sw, int(sw * src.height / src.width)), Image.LANCZOS)
top = int(crop.height * 0.12)
crop = crop.crop((0, top, sw, top + H)).convert("RGBA")
c.alpha_composite(crop, (W - sw, 0))
fade = Image.new("L", (W, 1))
fade.putdata([255 if x < W - sw else int(255 * max(0, 1 - (x - (W - sw)) / 220)) for x in range(W)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 12)] * 3, fade.resize((W, H)))))
red_edge(c, 0.4)
d = ImageDraw.Draw(c)
text(d, (40, 90), "KOI PAAS AAYA?", 70, YEL, 8, anchor="lm")
text(d, (40, 200), "WARNING!", 112, RED, 10, anchor="lm")
c.alpha_composite(emoji("🚨", 92), (40 + int(d.textlength("WARNING!", font=F(112))) + 14, 152))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 285, 640, 365), 40, fill=WHT)
d.text((340, 325), "ESP32 + Ultrasonic + OLED", font=F(38), fill=INK, anchor="mm")
box, _ = oled_inset(330, 4)
c.alpha_composite(box, (40, 392))
d = ImageDraw.Draw(c)
badge(d, 560, 520, 105)
d.rounded_rectangle((40, 640, 470, 700), 30, fill=WHT)
d.text((255, 670), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=93)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
