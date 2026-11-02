#!/usr/bin/env python3
"""Thumbnails for the ESP32 Car Racing short in the LED Flow thumbnail style, made to pop for kids:
big yellow 'ESP32 pe GAME!', pink 'CAR RACING', the crisp colour game frame (big bird between two
green pipes) bursting out of the 3D OLED console, score coin, cyan / purple pills. 1080x1920 Shorts
cover (all words inside the desktop-safe band y = 190..1690) + 1280x720 laptop version.
Optional args: <background frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import gamegfx  # noqa: E402
from tunnel import tunnel  # noqa: E402

WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0150.png")
GF = 140                                                # nitro flames + close call + coin
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
    """Colour Car Racing frame mid-NITRO, yellow frame + drop shadow, slightly tilted."""
    h = w // 2
    g = gamegfx.draw_hd(GF, w, h).convert("RGBA")
    d = ImageDraw.Draw(g)
    d.ellipse((w * 0.80, h * 0.62, w * 0.96, h * 0.62 + w * 0.16), fill=(255, 205, 40), outline=(150, 90, 0), width=max(3, w // 160))
    d.text((w * 0.88, h * 0.62 + w * 0.08), "+50", font=F(int(w * 0.055)), fill=(120, 60, 0), anchor="mm")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w // 28, fill=255)
    card = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", card.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), w // 28, fill=(0, 0, 0, 170))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    card.paste(g, (20, 20), m)
    ImageDraw.Draw(card).rounded_rectangle((20, 20, w + 19, h + 19), w // 28, outline=YEL, width=max(4, w // 90))
    return card.rotate(ang, expand=True, resample=Image.BICUBIC)


def on_tunnel(im):
    """The 3D frame is rendered on transparent film; put it on the cinematic digital tunnel."""
    if im.mode != "RGBA":
        return im.convert("RGB")
    im = im.resize((1080, 1920), Image.LANCZOS)
    bg = Image.fromarray(tunnel(250)).convert("RGBA")
    bg.alpha_composite(im)
    return bg.convert("RGB")


src = ImageEnhance.Color(on_tunnel(Image.open(FRAME)).resize((1080, 1920), Image.LANCZOS)).enhance(1.2)

# ---------------------------------------------------------------- 9:16 Shorts cover
W, H = 1080, 1920
c = src.convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - (y - 150) / 650)) if y < 800 else int(210 * max(0, (y - 1350) / 450)) for y in range(H)])
c.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
card = game_card(980)
c.alpha_composite(card, ((W - card.width) // 2, 640))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 265), "Ye MOBILE nahi hai!", 80, YEL, 10)
c.alpha_composite(emoji("😱", 84, 8), (W // 2 - 45 + int(d.textlength("Ye MOBILE nahi hai!", font=F(80)) / 2) + 8, 218))
d = ImageDraw.Draw(c)
text(d, (W // 2 - 45, 400), "CAR RACING", 112, PINK, 11)
c.alpha_composite(emoji("🏎️", 110, -6), (W // 2 - 45 + int(d.textlength("CAR RACING", font=F(112)) / 2) + 10, 340))
d = ImageDraw.Draw(c)
d.rounded_rectangle((190, 500, W - 190, 590), 45, fill=CYAN)
d.text((W // 2, 545), "Knob = Steering!", font=F(48), fill=INK, anchor="mm")
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
text(d, (40, 90), "Ye MOBILE nahi hai!", 74, YEL, 9, anchor="lm")
c.alpha_composite(emoji("😱", 74, 8), (40 + int(d.textlength("Ye MOBILE nahi hai!", font=F(74))) + 12, 50))
d = ImageDraw.Draw(c)
text(d, (40, 205), "CAR RACING", 96, PINK, 9, anchor="lm")
c.alpha_composite(emoji("🏎️", 90, -6), (40 + int(d.textlength("CAR RACING", font=F(96))) + 14, 155))
d = ImageDraw.Draw(c)
d.rounded_rectangle((40, 280, 520, 355), 38, fill=CYAN)
d.text((280, 318), "Knob = Steering!", font=F(38), fill=INK, anchor="mm")
d.rounded_rectangle((40, 600, 540, 680), 40, fill=PURP)
d.text((290, 640), "ESP32 + OLED Game", font=F(38), fill=WHT, anchor="mm")
c.convert("RGB").save(os.path.join(HERE, "thumbnail_16x9.jpg"), quality=95)
print("wrote thumbnail.jpg + thumbnail_16x9.jpg in", HERE)
