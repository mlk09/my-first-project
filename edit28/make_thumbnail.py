#!/usr/bin/env python3
"""EP 21 Dictionaries thumbnails: 1080x1920 (Shorts) + 1280x720 (YouTube / playlist).

Same look as the video: dark charcoal grid, orange code, yellow ribbon, mascot.
Story in one glance: phonebook card (Riya -> 97xxx) -> {"Riya": 85} key: value.

Usage:  python3 edit27/make_thumbnail.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit11"))
import build_ep04 as p4   # noqa: E402

mb, bs = p4.mb, p4.bs
MONO, CAP = p4.MONO, p4.CAP
WHITE, YEL, GREEN, RED, ORANGE = p4.WHITE, p4.YEL, p4.GREEN, p4.RED, p4.ORANGE
OUT = os.path.join(HERE, "output")


def grid_bg(w, h, cell=90):
    im = Image.new("RGB", (w, h), (24, 25, 30))
    d = ImageDraw.Draw(im)
    for x in range(0, w + 1, cell):
        d.line((x, 0, x, h), fill=(44, 46, 55), width=2)
    for y in range(0, h + 1, cell):
        d.line((0, y, w, y), fill=(44, 46, 55), width=2)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * .45) / h) ** 2)
    a = np.asarray(im).astype(np.float32) * (1.25 - 0.75 * np.clip(r, 0, 1))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def glow_spot(im, cx, cy, rad, col, alpha=110):
    lay = Image.new("RGBA", im.size)
    ImageDraw.Draw(lay).ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col + (alpha,))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(rad * 0.45)))


def chip(txt, col, size, crossed=False):
    f = mb.font(MONO, size)
    w = int(f.getlength(txt)) + int(size * 1.2)
    h = int(size * 1.9)
    im = Image.new("RGBA", (w + 40, h + 40))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), int(size * 0.45), fill=(20, 21, 26), outline=col,
                        width=max(4, size // 9))
    d.text((20 + w / 2, 20 + h / 2 + 2), txt, font=f, fill=WHITE if not crossed else (150, 150, 160), anchor="mm")
    im = p4.glow(im, col, 12)
    if crossed:
        d = ImageDraw.Draw(im)
        m = 34
        d.line((m, m, im.width - m, im.height - m), fill=RED, width=max(7, size // 6))
        d.line((im.width - m, m, m, im.height - m), fill=RED, width=max(7, size // 6))
    return im


def text(txt, size, fill, path=None, stroke=10, extrude=8, ecol=(10, 10, 10)):
    f = mb.font(path or mb.BALOO, size, "ExtraBold") if path is None else mb.font(path, size)
    return mb.outlined(txt, f, fill, stroke, (10, 10, 10), extrude, ecol)


def badge(txt, size):
    f = mb.font(CAP, size)
    w = int(f.getlength(txt)) + size * 2
    im = Image.new("RGBA", (w, int(size * 2.1)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, im.height - 1), im.height // 2, fill=(0, 0, 0, 190), outline=YEL, width=4)
    d.text((w / 2, im.height / 2 + 1), txt, font=f, fill=YEL, anchor="mm")
    return im


def kv(key, val, size):
    """key chip -> colon -> value chip"""
    k, v = chip(f'"{key}"', YEL, size), chip(str(val), GREEN, size)
    f = mb.font(MONO, int(size * 1.4))
    gap = int(size * 1.2)
    im = Image.new("RGBA", (k.width + gap + v.width, max(k.height, v.height)))
    im.alpha_composite(k, (0, (im.height - k.height) // 2))
    ImageDraw.Draw(im).text((k.width + gap / 2, im.height / 2), ":", font=f, fill=WHITE, anchor="mm")
    im.alpha_composite(v, (k.width + gap, (im.height - v.height) // 2))
    return im


def braces(im, cx, cy, half, size):
    f = mb.font(MONO, size)
    lay = Image.new("RGBA", im.size)
    ld = ImageDraw.Draw(lay)
    ld.text((cx - half, cy), "{", font=f, fill=ORANGE, anchor="mm")
    ld.text((cx + half, cy), "}", font=f, fill=ORANGE, anchor="mm")
    im.alpha_composite(p4.glow(lay, ORANGE, 14))


def vertical():
    W, H = 1080, 1920
    im = grid_bg(W, H)
    glow_spot(im, 540, 640, 460, (255, 150, 40), 70)
    glow_spot(im, 540, 1250, 420, (60, 200, 110), 60)
    mb.paste_c(im, badge("PYTHON KI PATHSHALA • EP 21", 34), 540, 130)
    mb.paste_c(im, text("PYTHON", 150, WHITE), 540, 320, -2)
    mb.paste_c(im, text("DICTIONARY", 160, YEL, extrude=11, ecol=(150, 95, 0)), 540, 560, -3)
    rb = mb.ribbon([("PYTHON KI PHONEBOOK!", (20, 20, 20), False)], mb.font(mb.BALOO, 70, "ExtraBold"), 120, 40,
                   fill=YEL)
    mb.paste_c(im, rb, 540, 780, 2)
    braces(im, 540, 1120, 420, 260)
    for k, (key, val) in enumerate((("Aman", 90), ("Riya", 85), ("Kabir", 70))):
        mb.paste_c(im, kv(key, val, 48), 540, 1000 + 120 * k)
    mb.paste_c(im, text("KEY : VALUE", 90, WHITE, stroke=8, extrude=6), 540, 1400, -2)
    mb.paste_c(im, mb.mascot(330), 900, 1735)
    mb.paste_c(im, mb.bubble("Naam se dhoondho!", mb.font(mb.BALOO, 50, "ExtraBold"), 24), 470, 1640)
    mb.paste_c(im, text("1 MINUTE MEIN!", 70, WHITE, stroke=8, extrude=6), 320, 1810, -3)
    return im.convert("RGB")


def horizontal():
    W, H = 1280, 720
    im = grid_bg(W, H, 64)
    glow_spot(im, 330, 330, 330, (255, 150, 40), 70)
    glow_spot(im, 940, 380, 300, (60, 200, 110), 60)
    mb.paste_c(im, badge("EP 21", 30), 90, 50)
    mb.paste_c(im, text("PYTHON", 92, WHITE, stroke=8, extrude=6), 310, 130, -2)
    mb.paste_c(im, text("DICTIONARY", 98, YEL, extrude=8, ecol=(150, 95, 0)), 310, 300, -3)
    rb = mb.ribbon([("PYTHON KI PHONEBOOK!", (20, 20, 20), False)], mb.font(mb.BALOO, 46, "ExtraBold"), 86, 30,
                   fill=YEL)
    mb.paste_c(im, rb, 330, 470, 2)
    mb.paste_c(im, text("KEY : VALUE", 56, WHITE, stroke=7, extrude=5), 320, 610, -3)
    braces(im, 960, 300, 255, 200)
    for k, (key, val) in enumerate((("Aman", 90), ("Riya", 85), ("Kabir", 70))):
        mb.paste_c(im, kv(key, val, 27), 960, 215 + 86 * k)
    mb.paste_c(im, mb.mascot(200), 1180, 625)
    mb.paste_c(im, mb.bubble("Naam se dhoondho!", mb.font(mb.BALOO, 34, "ExtraBold"), 18), 900, 610)
    return im.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    v = vertical()
    v.save(os.path.join(OUT, "EP21_Dictionaries_thumbnail_1080x1920.jpg"), quality=93)
    h = horizontal()
    h.save(os.path.join(OUT, "EP21_Dictionaries_thumbnail_1280x720.jpg"), quality=93)
    print("ok")


if __name__ == "__main__":
    main()
