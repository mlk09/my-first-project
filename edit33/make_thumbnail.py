#!/usr/bin/env python3
"""EP 26 try / except thumbnails (plexus background): 1080x1920 (Shorts) + 1280x720 (YouTube / playlist).

Same look as the video: dark charcoal grid, orange code, yellow ribbon, mascot.
Story in one glance: def namaste(): written once -> called 3 times -> 3 outputs.

Usage:  python3 edit27/make_thumbnail.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit11"))
sys.path.insert(0, os.path.join(HERE, "..", "brand"))
import build_ep04 as p4   # noqa: E402

mb, bs = p4.mb, p4.bs
MONO, CAP = p4.MONO, p4.CAP
WHITE, YEL, GREEN, RED, ORANGE = p4.WHITE, p4.YEL, p4.GREEN, p4.RED, p4.ORANGE
OUT = os.path.join(HERE, "output")


def grid_bg(w, h, cell=90):
    import plexus_bg as pb
    im = pb.background(4.0)
    return im.resize((w, h)) if (w, h) != im.size else im


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


def code_card(lines, size, w):
    f = mb.font(MONO, size)
    lh = int(size * 1.55)
    h = 60 + lh * len(lines) + 30
    im = Image.new("RGBA", (w + 40, h + 40))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 26, fill=(28, 29, 34), outline=(70, 74, 86), width=3)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((46 + 30 * k, 40, 64 + 30 * k, 58), fill=c)
    for k, (txt, col) in enumerate(lines):
        d.text((54, 20 + 60 + lh * k + lh / 2), txt, font=f, fill=col, anchor="lm")
    return im


CODE = [("try:", ORANGE), ('    n = int("abc")', (120, 220, 255)), ("except ValueError:", ORANGE),
        ('    print("Oops!")', (230, 220, 140)), ("# no crash :)", (140, 230, 140))]


def vertical():
    W, H = 1080, 1920
    im = grid_bg(W, H)
    glow_spot(im, 540, 620, 460, (80, 150, 255), 60)
    glow_spot(im, 540, 1250, 420, (60, 200, 110), 60)
    mb.paste_c(im, badge("PYTHON KI PATHSHALA • EP 26", 34), 540, 130)
    mb.paste_c(im, text("PYTHON", 150, WHITE), 540, 320, -2)
    mb.paste_c(im, text("TRY/EXCEPT", 150, YEL, extrude=11, ecol=(150, 95, 0)), 540, 560, -3)
    rb = mb.ribbon([("PROGRAM CRASH SE BACHAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 58, "ExtraBold"),
                   110, 36, fill=YEL)
    mb.paste_c(im, rb, 540, 780, 2)
    mb.paste_c(im, code_card(CODE, 46, 760), 540, 1110)
    mb.paste_c(im, chip("SAFE", GREEN, 64), 640, 1420)
    mb.paste_c(im, text("ERROR →", 64, RED, stroke=7, extrude=5, ecol=(20, 90, 40)), 300, 1420, -3)
    mb.paste_c(im, mb.mascot(330), 900, 1735)
    mb.paste_c(im, mb.bubble("Safe raho!", mb.font(mb.BALOO, 50, "ExtraBold"), 24), 500, 1640)
    mb.paste_c(im, text("PROGRAM KA HELMET", 58, WHITE, stroke=8, extrude=6), 400, 1810, -3)
    return im.convert("RGB")


def horizontal():
    W, H = 1280, 720
    im = grid_bg(W, H, 64)
    glow_spot(im, 330, 330, 330, (80, 150, 255), 60)
    glow_spot(im, 940, 380, 300, (60, 200, 110), 60)
    mb.paste_c(im, badge("EP 26", 30), 90, 50)
    mb.paste_c(im, text("PYTHON", 92, WHITE, stroke=8, extrude=6), 310, 130, -2)
    mb.paste_c(im, text("TRY/EXCEPT", 100, YEL, extrude=8, ecol=(150, 95, 0)), 320, 300, -3)
    rb = mb.ribbon([("CRASH SE BACHAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 48, "ExtraBold"), 86, 30,
                   fill=YEL)
    mb.paste_c(im, rb, 320, 470, 2)
    mb.paste_c(im, text("PROGRAM KA HELMET", 44, WHITE, stroke=6, extrude=4), 320, 610, -3)
    mb.paste_c(im, code_card(CODE, 32, 500), 940, 250)
    for k in range(3):
        pass
    mb.paste_c(im, mb.mascot(200), 1180, 625)
    mb.paste_c(im, mb.bubble("Safe raho!", mb.font(mb.BALOO, 34, "ExtraBold"), 18), 920, 620)
    return im.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    v = vertical()
    v.save(os.path.join(OUT, "EP26_Try_Except_thumbnail_1080x1920.jpg"), quality=93)
    h = horizontal()
    h.save(os.path.join(OUT, "EP26_Try_Except_thumbnail_1280x720.jpg"), quality=93)
    print("ok")


if __name__ == "__main__":
    main()
