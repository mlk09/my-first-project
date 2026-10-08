#!/usr/bin/env python3
"""Phone app frames for the Tap-to-Light short (own design, MIT App Inventor style): Bluetooth
connect bar, 2x2 colour buttons that glow when their LED is on, ALL ON / ALL OFF, PARTY MODE,
and a touch ripple on every tap. One PNG per video frame."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, TAPS, PARTY, COLORS, leds, connected  # noqa: E402

OUT = os.path.join(HERE, "work", "app")
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H = 540, 1170
BG, CARD, TXT, SUB = (12, 14, 22), (26, 30, 44), (240, 242, 250), (140, 148, 168)
COL = [(255, 60, 60), (255, 205, 40), (50, 230, 110), (60, 140, 255)]
BTN = {i: (40 + (i % 2) * 240, 330 + (i // 2) * 240, 260 + (i % 2) * 240, 550 + (i // 2) * 240) for i in range(4)}
BTN["ALL"], BTN["OFF"] = (40, 820, 260, 920), (280, 820, 500, 920)
BTN["PARTY"], BTN["CONNECT"] = (40, 950, 500, 1060), (40, 190, 500, 280)


def f(sz, b=True):
    return ImageFont.truetype(SANS if b else REG, sz)


def center(b):
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


for fr in range(N):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((40, 40), "9:41", font=f(24), fill=TXT, anchor="lm")
    d.text((W - 40, 40), "BT  WiFi  86%", font=f(18, False), fill=SUB, anchor="rm")
    d.text((40, 115), "Tap to Light", font=f(44), fill=TXT, anchor="lm")
    d.text((40, 158), "ESP32 LED Controller · App Inventor", font=f(19, False), fill=SUB, anchor="lm")
    on = leds(fr)
    con = connected(fr)
    b = BTN["CONNECT"]
    d.rounded_rectangle(b, 22, fill=(20, 60, 40) if con else CARD, outline=(50, 230, 110) if con else (70, 80, 110), width=3)
    d.text(center(b), "Connected · ESP32_LED" if con else "Tap to CONNECT (Bluetooth)", font=f(24),
           fill=(80, 240, 140) if con else TXT, anchor="mm")
    glow = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(glow)
    for i in range(4):
        b = BTN[i]
        c = COL[i]
        if on[i]:
            gd.rounded_rectangle(b, 40, fill=c)
            d.rounded_rectangle(b, 40, fill=c)
        else:
            d.rounded_rectangle(b, 40, fill=CARD, outline=tuple(v // 2 for v in c), width=4)
        cx, cy = center(b)
        d.ellipse((cx - 34, cy - 60, cx + 34, cy + 8), fill=(255, 255, 255) if on[i] else tuple(v // 3 for v in c))
        d.text((cx, cy + 50), COLORS[i], font=f(26), fill=(20, 20, 25) if on[i] else c, anchor="mm")
        d.text((cx, cy + 82), "ON" if on[i] else "OFF", font=f(20), fill=(20, 20, 25) if on[i] else SUB, anchor="mm")
    party = PARTY[0] + 2 <= fr < PARTY[1] + 2
    for key, txt in (("ALL", "ALL ON"), ("OFF", "ALL OFF")):
        d.rounded_rectangle(BTN[key], 30, fill=CARD)
        d.text(center(BTN[key]), txt, font=f(28), fill=TXT, anchor="mm")
    b = BTN["PARTY"]
    if party:
        c = COL[(fr // 3) % 4]
        gd.rounded_rectangle(b, 34, fill=c)
        d.rounded_rectangle(b, 34, fill=c)
    else:
        d.rounded_rectangle(b, 34, fill=(70, 40, 120))
    d.text(center(b), "PARTY MODE", font=f(34), fill=(255, 255, 255), anchor="mm")
    im.paste(Image.eval(glow.filter(ImageFilter.GaussianBlur(18)), lambda v: v // 2), (0, 0),
             glow.filter(ImageFilter.GaussianBlur(18)).convert("L").point(lambda v: min(v, 110)))
    d = ImageDraw.Draw(im)
    for i in range(4):                       # redraw crisp labels over the glow
        if on[i]:
            b = BTN[i]
            cx, cy = center(b)
            d.rounded_rectangle(b, 40, fill=COL[i])
            d.ellipse((cx - 34, cy - 60, cx + 34, cy + 8), fill=(255, 255, 255))
            d.text((cx, cy + 50), COLORS[i], font=f(26), fill=(20, 20, 25), anchor="mm")
            d.text((cx, cy + 82), "ON", font=f(20), fill=(20, 20, 25), anchor="mm")
    if party:
        d.rounded_rectangle(BTN["PARTY"], 34, fill=COL[(fr // 3) % 4])
        d.text(center(BTN["PARTY"]), "PARTY MODE", font=f(34), fill=(255, 255, 255), anchor="mm",
               stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((W / 2, 1120), "@The IOT Engineer", font=f(18, False), fill=SUB, anchor="mm")
    # touch ripple
    for t, key in TAPS:
        age = fr - t
        if 0 <= age < 10:
            cx, cy = center(BTN[key])
            r = 22 + age * 9
            a = int(255 * (1 - age / 10))
            ov = Image.new("RGBA", (W, H))
            od = ImageDraw.Draw(ov)
            if age < 4:
                od.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=(255, 255, 255, 150))
            od.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, a), width=6)
            im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    im.save(os.path.join(OUT, f"{fr:04d}.png"))
print("app frames in", OUT)
