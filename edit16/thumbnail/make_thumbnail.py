#!/usr/bin/env python3
"""1080x1920 Shorts thumbnail for the ESP32 + OLED + DHT11 temperature-controlled LED: hot mug + red
LED as background, OLED 'HOT! RED LED ON' inset, big hook text and a 35 degC heat badge.
Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0310.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0310.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail.jpg")
W, H = 1080, 1920
YEL, WHT, INK, RED, CYAN = (255, 214, 10), (255, 255, 255), (15, 18, 26), (255, 60, 60), (60, 220, 255)

canvas = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(235 * max(0, 1 - y / 720)) if y < 720 else int(210 * max(0, (y - 1450) / 470)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
red = Image.new("L", (W, H), 0)                                    # warm edge glow
ImageDraw.Draw(red).rectangle((0, 0, W, H), outline=255, width=60)
canvas.alpha_composite(Image.merge("RGBA", (Image.new("L", (W, H), 255), Image.new("L", (W, H), 40), Image.new("L", (W, H), 30),
                                            red.filter(ImageFilter.GaussianBlur(60)).point(lambda v: v * 0.45))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


ol = Image.open(OLEDF).convert("RGB").resize((440, 220), Image.LANCZOS)
box = Image.new("RGBA", (476, 256), (20, 70, 165, 255))
box.paste(ol, (18, 18))
box = box.rotate(5, expand=True, resample=Image.BICUBIC)
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
                       .filter(ImageFilter.GaussianBlur(20)), (40, 1340))
canvas.alpha_composite(box, (30, 1330))

d = ImageDraw.Draw(canvas)
text(d, (W // 2 - 50, 140), "GARAM = LED ON", 100, YEL, 11)
canvas.alpha_composite(emoji("🔥", 100, 8), (W - 110, 80))
text(d, (W // 2 - 40, 285), "Thanda = OFF", 96, CYAN, 10)
canvas.alpha_composite(emoji("❄️", 100, -8), (W - 200, 230))
d.rounded_rectangle((150, 390, W - 150, 490), 50, fill=WHT)
d.text((W // 2, 440), "ESP32 + DHT11 + OLED", font=ImageFont.truetype(FONT, 50), fill=INK, anchor="mm")
d.ellipse((W - 330, 1300, W - 50, 1580), fill=RED, outline=WHT, width=10)          # heat badge
d.text((W - 190, 1420), "35°C", font=ImageFont.truetype(FONT, 76), fill=WHT, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
d.text((W - 190, 1500), "HOT!", font=ImageFont.truetype(FONT, 44), fill=YEL, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
d.rounded_rectangle((60, 1640, 740, 1740), 50, fill=(255, 120, 30))
d.text((400, 1690), "Auto Temp Control", font=ImageFont.truetype(FONT, 50), fill=WHT, anchor="mm")
d.rounded_rectangle((40, 1800, 520, 1880), 40, fill=WHT)
d.text((280, 1840), "@The IOT Engineer", font=ImageFont.truetype(FONT, 32), fill=INK, anchor="mm")
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
