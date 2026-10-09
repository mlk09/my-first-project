#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 Tap-to-Light video: glowing LED macro frame,
the app screen as a tilted inset, big hook text."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = os.path.join(WORK, "frames3d", "0220.png")     # LED macro, all four LEDs on
APP = os.path.join(WORK, "app", "0200.png")            # app with all buttons ON
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, CYAN = (255, 214, 10), (255, 255, 255), (60, 220, 255)

bg = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS)
glow = bg.filter(ImageFilter.GaussianBlur(40))
canvas = Image.blend(bg, Image.eval(glow, lambda v: min(255, v * 2)), 0.25).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 760)) if y < 760 else int(200 * max(0, (y - 1450) / 470)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


# phone inset (bottom-right, tilted)
src = Image.open(APP).convert("RGBA")
ad = ImageDraw.Draw(src)                                # retitle the app for the thumbnail
ad.rectangle((20, 80, 540, 178), fill=(12, 14, 22))
ad.text((40, 115), "LED Controller", font=ImageFont.truetype(FONT, 40), fill=(240, 242, 250), anchor="lm")
ad.text((40, 158), "ESP32 · Bluetooth · App Inventor", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19),
        fill=(140, 148, 168), anchor="lm")
app = src.resize((340, 737), Image.LANCZOS)
ph = Image.new("RGBA", (380, 777), (10, 10, 12, 255))
ph.alpha_composite(app, (20, 20))
m = Image.new("L", ph.size, 0)
ImageDraw.Draw(m).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), 46, fill=255)
ph.putalpha(m)
ph = ph.rotate(-8, expand=True, resample=Image.BICUBIC)
sh = Image.new("RGBA", ph.size, (0, 0, 0, 0))
sh.putalpha(ph.split()[3].point(lambda v: min(v, 170)))
canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (W - ph.width - 20, 1040))
canvas.alpha_composite(ph, (W - ph.width - 40, 1020))
canvas.alpha_composite(emoji("👆", 150, 10), (W - 330, 1500))

d = ImageDraw.Draw(canvas)
text(d, (W // 2, 140), "MOBILE SE", 140, WHT, 12)
text(d, (W // 2, 295), "LED CONTROL!", 118, YEL, 12)
canvas.alpha_composite(emoji("💡", 130, -12), (40, 560))
d.rounded_rectangle((90, 420, W - 90, 530), 55, fill=CYAN)
d.text((W // 2, 475), "ESP32 + BLUETOOTH APP", font=ImageFont.truetype(FONT, 54), fill=(10, 14, 22), anchor="mm")
d.rounded_rectangle((40, 1700, 600, 1790), 45, fill=(255, 60, 60))
d.text((320, 1745), "Bina wire, sirf phone se", font=ImageFont.truetype(FONT, 36), fill=WHT, anchor="mm")
d.rounded_rectangle((40, 1820, 520, 1890), 35, fill=(255, 255, 255))
d.text((280, 1855), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=(15, 18, 26), anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
