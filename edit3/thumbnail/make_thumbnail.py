#!/usr/bin/env python3
"""1280x720 YouTube thumbnail: scared Bolt + the haunted bag, big spooky title."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FRAMES = os.path.join(ROOT, "work", "frames")
FONT = os.path.join(ROOT, "assets", "fonts", "Creepster.ttf")
FONT2 = os.path.join(ROOT, "assets", "fonts", "Fredoka-Bold.ttf")
FPS = 24


def frame(t):
    return Image.open(os.path.join(FRAMES, f"f_{int(round(t * FPS)):05d}.png")).convert("RGB")


def cover(im, w, h, cx=0.5, cy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * cx)
    y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def main():
    W, H = 1280, 720
    bolt = cover(frame(57.0), 700, H, 0.5, 0.4)
    bag = cover(frame(62.6), 700, H, 0.5, 0.35)
    canvas = Image.new("RGB", (W, H))
    canvas.paste(bolt, (0, 0))
    # bag on the right with a soft diagonal seam
    mask = Image.new("L", (700, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(120, 0), (700, 0), (700, H), (0, H)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(bag, (W - 700, 0), mask)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.25)
    canvas = ImageEnhance.Color(canvas).enhance(1.35)
    canvas = ImageEnhance.Brightness(canvas).enhance(1.15)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    arr = (np.asarray(canvas).astype(np.float32) * v[..., None].clip(0.3, 1)).clip(0, 255)
    canvas = Image.fromarray(arr.astype(np.uint8))
    draw = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 150)
    text = "HAUNTED BAG!?"
    bb = draw.textbbox((0, 0), text, font=f1)
    x = (W - (bb[2] - bb[0])) // 2
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, 455), text, font=f1, fill=(255, 90, 0, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(16))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow)
    draw = ImageDraw.Draw(canvas)
    draw.text((x, 455), text, font=f1, fill=(255, 150, 30), stroke_width=7, stroke_fill=(15, 5, 20))
    f2 = ImageFont.truetype(FONT2, 46)
    sub = "A SPOOKY STORY FOR KIDS"
    bb = draw.textbbox((0, 0), sub, font=f2)
    sx = (W - (bb[2] - bb[0])) // 2
    draw.rounded_rectangle((sx - 24, 22, sx + bb[2] - bb[0] + 24, 92), 18, fill=(255, 205, 40))
    draw.text((sx, 30), sub, font=f2, fill=(25, 10, 30))
    out = os.path.join(HERE, "thumbnail.jpg")
    canvas.convert("RGB").save(out, quality=92)
    print(out)


if __name__ == "__main__":
    main()
