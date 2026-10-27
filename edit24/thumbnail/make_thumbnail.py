#!/usr/bin/env python3
"""Thumbnails for the ESP32 Snake short in the LED Flow thumbnail style, made to pop for kids:
big yellow 'ESP32 pe GAME!', pink SNAKE GAME, the crisp colour game frame (big bird between two
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
GF = PLAY0 + 110                                        # long snake heading for an apple
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
    g = gamegfx.lawn(w, h).convert("RGBA")                          # garden only, hero snake drawn here
    dd = ImageDraw.Draw(g)
    import math
    r = h * 0.075
    pts = [(w * (0.06 + 0.5 * u), h * (0.6 + 0.2 * math.sin(u * 9))) for u in (i / 60 for i in range(61))]
    S, SD, SL = gamegfx.SNAKE, gamegfx.SNAKE_D, gamegfx.SNAKE_L
    dd.line(pts, fill=SD, width=int(r * 2) + 8, joint="curve")
    dd.line(pts, fill=S, width=int(r * 2), joint="curve")
    for i in range(4, 60, 6):
        x, y = pts[i]
        dd.ellipse((x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35), fill=(255, 210, 60))
    dd.line(pts, fill=SL, width=int(r * 0.35), joint="curve")
    hx, hy = pts[-1]
    hr = r * 1.35
    dd.line((hx + hr * 0.8, hy, hx + hr * 1.7, hy), fill=(230, 40, 60), width=int(r * 0.22))
    dd.line((hx + hr * 1.7, hy, hx + hr * 2.0, hy - hr * 0.3), fill=(230, 40, 60), width=int(r * 0.18))
    dd.line((hx + hr * 1.7, hy, hx + hr * 2.0, hy + hr * 0.3), fill=(230, 40, 60), width=int(r * 0.18))
    dd.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=S, outline=SD, width=4)
    for sg in (-1, 1):
        ex, ey, er = hx + hr * 0.25, hy + sg * hr * 0.45, hr * 0.36
        dd.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(255, 255, 255), outline=SD, width=3)
        dd.ellipse((ex - er * 0.1, ey - er * 0.45, ex + er * 0.8, ey + er * 0.45), fill=(20, 20, 30))
    gamegfx.apple_hd(dd, w * 0.76, h * 0.55, w * 0.075, 0)          # big hero apple
    d = ImageDraw.Draw(g)
    d.ellipse((w * 0.78, h * 0.08, w * 0.94, h * 0.08 + w * 0.16), fill=(255, 205, 40), outline=(150, 90, 0), width=max(3, w // 160))
    d.text((w * 0.86, h * 0.08 + w * 0.08), "+10", font=F(int(w * 0.055)), fill=(120, 60, 0), anchor="mm")
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
c.alpha_composite(emoji("🐍", 92, 8), (W - 150, 215))
d = ImageDraw.Draw(c)
text(d, (W // 2, 405), "SNAKE GAME", 104, PINK, 11)
d.rounded_rectangle((190, 500, W - 190, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Knob ghumao = Turn!", font=F(48), fill=INK, anchor="mm")
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
c.alpha_composite(emoji("🐍", 80, 8), (40 + int(d.textlength("ESP32 pe GAME!", font=F(86))) + 14, 48))
d = ImageDraw.Draw(c)
text(d, (40, 205), "SNAKE GAME", 84, PINK, 9, anchor="lm")
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Knob ghumao = Turn!", font=F(38), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + OLED Game", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
