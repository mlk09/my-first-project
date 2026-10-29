#!/usr/bin/env python3
"""Thumbnails for the ESP32 2-player Pong short in the LED Flow thumbnail style, made to pop for kids:
big yellow 'ESP32 pe GAME!', pink PONG 2 PLAYER, the crisp colour game frame (big bird between two
green pipes) bursting out of the 3D OLED console, score coin, cyan / purple pills. 1080x1920 Shorts
cover (all words inside the desktop-safe band y = 190..1690) + 1280x720 laptop version.
Optional args: <background frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import gamegfx  # noqa: E402
from timeline import PLAY0  # noqa: E402

WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0250.png")
GF = PLAY0 + 100                                        # mid-rally, ball near the pink paddle
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL, WHT, INK, PINK, CYAN, PURP = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 120, 220), (60, 220, 255), (130, 60, 255)


def F(s):
    return ImageFont.truetype(FONT, s)


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10, anchor="mm"):
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def game_card(w, ang=-4):
    """Colour game frame with a big bird, yellow frame + drop shadow, slightly tilted."""
    h = w // 2
    g = gamegfx.draw_hd(GF, w, h).convert("RGBA")
    d = ImageDraw.Draw(g)
    for k in range(8, 0, -1):                                       # hero ball with a glowing trail
        r = w * 0.022 * (1 - k / 10)
        cx, cy = w * (0.74 - k * 0.035), h * (0.36 + k * 0.025)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 235, 140, int(220 * (1 - k / 9))))
    gl = Image.new("RGBA", (w, h))
    ImageDraw.Draw(gl).ellipse((w * 0.74 - w * 0.05, h * 0.36 - w * 0.05, w * 0.74 + w * 0.05, h * 0.36 + w * 0.05), fill=(255, 220, 110, 255))
    g.alpha_composite(gl.filter(ImageFilter.GaussianBlur(w // 50)))
    d = ImageDraw.Draw(g)
    d.ellipse((w * 0.74 - w * 0.024, h * 0.36 - w * 0.024, w * 0.74 + w * 0.024, h * 0.36 + w * 0.024), fill=(255, 255, 255))
    d.text((w * 0.5, h * 0.55), "VS", font=F(int(w * 0.13)), fill=(255, 214, 10), anchor="mm", stroke_width=max(4, w // 120), stroke_fill=(0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    card = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", card.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 170))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    card.paste(g, (20, 20), m)
    ImageDraw.Draw(card).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=YEL, width=max(4, w // 90))
    return card.rotate(ang, expand=True, resample=Image.BICUBIC)


src = ImageEnhance.Color(Image.open(FRAME).convert("RGB").resize((1080, 1920), Image.LANCZOS)).enhance(1.2)

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
c = src.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(210 * max(0, (y - 1350) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
card = game_card(980)
c.alpha_composite(card, ((W - card.width) // 2, 640))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 50, 265), "ESP32 pe GAME!", 98, YEL, 11)
c.alpha_composite(emoji("🏓", 92, 8), (W - 150, 215))
d = ImageDraw.Draw(c)
text(d, (W // 2, 405), "PONG 2 PLAYER", 96, PINK, 10)
d.rounded_rectangle((190, 500, W - 190, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Dost ke saath khelo!", font=F(44), fill=INK, anchor="mm")
d.rounded_rectangle((60, 1500, 690, 1600), 50, fill=PURP)
d.text((375, 1550), "ESP32 + OLED Game", font=F(48), fill=WHT, anchor="mm")
d.rounded_rectangle((60, 1615, 470, 1680), 33, fill=WHT)
d.text((265, 1648), "@The IOT Engineer", font=F(28), fill=INK, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail.jpg"), quality=95)

# ---------------------------------------------------------------- 16:9 (laptop / desktop)
W, H = 1280, 720
c = Image.new("RGBA", (W, H), (12, 14, 20, 255))
bg = src.resize((W, int(W * 1920 / 1080)), Image.LANCZOS).crop((0, 800, W, 800 + H)).filter(ImageFilter.GaussianBlur(6))
c.alpha_composite(ImageEnhance.Brightness(bg).enhance(0.55).convert("RGBA"))
card = game_card(620, -5)
c.alpha_composite(card, (W - card.width + 10, 250))
d = ImageDraw.Draw(c)
text(d, (40, 90), "ESP32 pe GAME!", 86, YEL, 9, anchor="lm")
c.alpha_composite(emoji("🏓", 80, 8), (40 + int(d.textlength("ESP32 pe GAME!", font=F(86))) + 14, 48))
d = ImageDraw.Draw(c)
text(d, (40, 205), "PONG 2 PLAYER", 74, PINK, 8, anchor="lm")
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Dost ke saath khelo!", font=F(34), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + OLED Game", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
