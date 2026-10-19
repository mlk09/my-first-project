#!/usr/bin/env python3
"""Alternate 1080x1920 thumbnail for the ESP32 Rock-Paper-Scissors robot: 'ROBOT vs INSAAN' split
header with a lightning VS badge, the robot box mid-round as background, the OLED 'YOU WIN!' screen
as a tilted inset, and a row of ✊ ✋ ✌️ chips. Optional args: <background frame> <oled frame>."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "frames3d", "0182.png")
OLEDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "oled", "0330.png")
FONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(HERE, "thumbnail2.jpg")
W, H = 1080, 1920
YEL, WHT, INK, GRN, RED, BLU = (255, 214, 10), (255, 255, 255), (15, 18, 26), (40, 230, 110), (255, 60, 60), (40, 120, 255)

canvas = Image.open(FRAME).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
g = Image.new("L", (1, H))
g.putdata([int(150 * max(0, 1 - (y - 560) / 300)) if y > 560 else 0 for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g.resize((W, H)))))
g2 = Image.new("L", (1, H))
g2.putdata([int(230 * max(0, (y - 1350) / 570)) for y in range(H)])
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3, g2.resize((W, H)))))


def emoji(ch, size, ang=0):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC)


def text(d, xy, s, size, fill, stroke=10):
    d.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


# split header: red robot half | blue human half, diagonal cut
head = Image.new("RGBA", (W, 560))
hd = ImageDraw.Draw(head)
hd.polygon([(0, 0), (W / 2 + 70, 0), (W / 2 - 70, 560), (0, 560)], fill=RED + (255,))
hd.polygon([(W / 2 + 70, 0), (W, 0), (W, 560), (W / 2 - 70, 560)], fill=BLU + (255,))
canvas.alpha_composite(head)
canvas.alpha_composite(emoji("🤖", 230), (60, 120))
canvas.alpha_composite(emoji("🧑", 230), (W - 290, 120))
d = ImageDraw.Draw(canvas)
text(d, (190, 440), "ROBOT", 76, WHT, 8)
text(d, (W - 180, 440), "INSAAN", 70, WHT, 8)
bolt = Image.new("RGBA", (300, 300))                       # VS lightning badge
bd = ImageDraw.Draw(bolt)
bd.ellipse((20, 20, 280, 280), fill=YEL + (255,), outline=INK + (255,), width=12)
bd.text((150, 150), "VS", font=ImageFont.truetype(FONT, 120), fill=INK, anchor="mm")
canvas.alpha_composite(bolt.rotate(-8, resample=Image.BICUBIC), (W // 2 - 150, 130))
d = ImageDraw.Draw(canvas)
text(d, (W // 2, 660), "KAUN JEETEGA?", 112, YEL, 12)

# OLED inset with glow
ol = Image.open(OLEDF).convert("RGB").resize((560, 280), Image.LANCZOS)
box = Image.new("RGBA", (600, 320), (20, 70, 165, 255))
box.paste(ol, (20, 20))
box = box.rotate(6, expand=True, resample=Image.BICUBIC)
canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", box.size, 255)] * 3, box.split()[3].point(lambda v: min(v, 150))))
                       .filter(ImageFilter.GaussianBlur(22)), (40, 1090))
canvas.alpha_composite(box, (30, 1080))

# hand chips
for i, ch in enumerate(("✊", "✋", "✌️")):
    cx = 220 + i * 320
    ImageDraw.Draw(canvas).ellipse((cx - 115, 1600 - 115, cx + 115, 1600 + 115), fill=WHT, outline=INK, width=8)
    canvas.alpha_composite(emoji(ch, 150), (cx - 75, 1600 - 75))
d = ImageDraw.Draw(canvas)
d.rounded_rectangle((200, 1770, W - 200, 1850), 40, fill=(60, 220, 255))
d.text((W // 2, 1810), "ESP32 + OLED Game", font=ImageFont.truetype(FONT, 44), fill=INK, anchor="mm")
d.text((W - 30, 1895), "@The IOT Engineer", font=ImageFont.truetype(FONT, 26), fill=WHT, anchor="rm",
       stroke_width=3, stroke_fill=(0, 0, 0))
canvas.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
