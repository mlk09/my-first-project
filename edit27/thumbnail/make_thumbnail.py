#!/usr/bin/env python3
"""Thumbnails for the 'ESP32 Gaming Console: 4 Retro Games' combo short: big yellow 'ESP32 GAMING
CONSOLE', pink '4 RETRO GAMES!', and the four crisp GAME CAM panels (Flappy / Dino / Snake / Pong) in a
2x2 grid with coloured frames + name chips. 1080x1920 Shorts cover (all words inside the desktop-safe
band y = 190..1690) + 1280x720 laptop version."""
import os

import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
FONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, PINK, CYAN = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 120, 220), (60, 220, 255)
GAMES = [("edit22", "esp32-oled-flappy-bird-game-SHORT.mp4", 262, "🐦", "FLAPPY BIRD", (255, 205, 40)),
         ("edit23", "esp32-oled-chrome-dino-game-SHORT.mp4", 300, "🦖", "CHROME DINO", (90, 220, 90)),
         ("edit24", "esp32-oled-snake-game-SHORT.mp4", 280, "🐍", "SNAKE", (80, 150, 255)),
         ("edit26", "esp32-oled-pong-2-player-game-SHORT.mp4", 300, "🏓", "2P PONG", (255, 70, 180))]
PANEL = (30, 306, 1050, 836)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def grab(ed, vid, f):
    cap = cv2.VideoCapture(os.path.join(ROOT, ed, "output", vid))
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, fr = cap.read()
    cap.release()
    return Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))


SHOTS = [grab(*g[:3]) for g in GAMES]
TILES = [s.crop(PANEL) for s in SHOTS]


def card(i, w, ang):
    t = TILES[i].resize((w, int(w * TILES[i].height / TILES[i].width)), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", t.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, t.width - 1, t.height - 1), w // 22, fill=255)
    out = Image.new("RGBA", (t.width + 40, t.height + 40))
    sh = Image.new("RGBA", out.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 28, t.width + 20, t.height + 28), w // 22, fill=(0, 0, 0, 180))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    out.paste(t, (20, 20), m)
    ImageDraw.Draw(out).rounded_rectangle((20, 20, t.width + 19, t.height + 19), w // 22, outline=GAMES[i][5], width=max(5, w // 60))
    return out.rotate(ang, expand=True, resample=Image.BICUBIC)


def chip(c, cx, cy, i, h):
    d = ImageDraw.Draw(c)
    w = int(h * 4.6)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), h // 2, fill=GAMES[i][5], outline=WHT, width=3)
    c.alpha_composite(emoji(GAMES[i][3], int(h * 0.7)), (int(cx - w / 2 + h * 0.2), int(cy - h * 0.35)))
    d.text((cx + h * 0.35, cy), GAMES[i][4], font=F(int(h * 0.5)), fill=INK, anchor="mm")


def background(w, h):
    bg = SHOTS[3].resize((w, int(w * 1920 / 1080)), Image.LANCZOS).crop((0, 600, w, 600 + h)) if w > h else SHOTS[3].resize((w, h))
    bg = bg.filter(ImageFilter.GaussianBlur(20))
    return Image.blend(bg.convert("RGB"), Image.new("RGB", (w, h), (10, 8, 30)), 0.55).convert("RGBA")


# ---------------------------------------------------------------- 9:16
W, H = 1080, 1920
c = background(W, H)
d = ImageDraw.Draw(c)
text(d, (W // 2, 270), "ESP32 GAMING", 112, YEL, 12)
text(d, (W // 2 - 50, 395), "CONSOLE", 112, WHT, 12)
c.alpha_composite(emoji("🎮", 104, 6), (int(W // 2 - 50 + d.textlength("CONSOLE", font=F(112)) / 2 + 14), 335))
d = ImageDraw.Draw(c)
d.rounded_rectangle((150, 480, W - 150, 580), 50, fill=PINK)
d.text((W // 2, 530), "4 RETRO GAMES!", font=F(60), fill=INK, anchor="mm")
for i, (x, y, ang) in enumerate(((20, 620, 3), (540, 640, -3), (20, 1050, -2), (540, 1065, 3))):
    cd = card(i, 500, ang)
    c.alpha_composite(cd, (x, y))
    chip(c, x + cd.width // 2, y + cd.height - 10, i, 64)
d = ImageDraw.Draw(c)
d.rounded_rectangle((W // 2 - 300, 1505, W // 2 + 300, 1585), 40, fill=CYAN)
d.text((W // 2, 1545), "1 ESP32 = 4 Games", font=F(48), fill=INK, anchor="mm")
d.rounded_rectangle((W // 2 - 205, 1615, W // 2 + 205, 1680), 33, fill=WHT)
d.text((W // 2, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)

# ---------------------------------------------------------------- 16:9
W, H = 1280, 720
c = background(W, H)
d = ImageDraw.Draw(c)
text(d, (36, 95), "ESP32 GAMING", 62, YEL, 8, anchor="lm")
text(d, (36, 190), "CONSOLE", 62, WHT, 8, anchor="lm")
c.alpha_composite(emoji("🎮", 64, 6), (36 + int(d.textlength("CONSOLE", font=F(62))) + 12, 156))
d = ImageDraw.Draw(c)
d.rounded_rectangle((36, 262, 486, 338), 38, fill=PINK)
d.text((261, 300), "4 RETRO GAMES!", font=F(42), fill=INK, anchor="mm")
for i, (x, y, ang) in enumerate(((600, 30, 3), (930, 40, -3), (600, 360, -2), (930, 370, 3))):
    cd = card(i, 310, ang)
    c.alpha_composite(cd, (x, y))
    chip(c, x + cd.width // 2, y + cd.height - 6, i, 44)
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 610, 480, 680), 35, fill=CYAN)
d.text((260, 645), "1 ESP32 = 4 Games", font=F(40), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
