#!/usr/bin/env python3
"""EP 20 Sets thumbnails: 1080x1920 (Shorts) + 1280x720 (YouTube / playlist).

Same look as the video: dark charcoal grid, orange code, yellow ribbon, mascot.
Story in one glance: [apple, mango, apple, kiwi, mango] -> duplicates crossed in red -> {apple, mango, kiwi}.

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


def vertical():
    W, H = 1080, 1920
    im = grid_bg(W, H)
    glow_spot(im, 540, 640, 460, (255, 150, 40), 70)
    glow_spot(im, 540, 1250, 420, (60, 200, 110), 60)
    mb.paste_c(im, badge("PYTHON KI PATHSHALA • EP 20", 34), 540, 130)
    mb.paste_c(im, text("PYTHON", 150, WHITE), 540, 330, -2)
    mb.paste_c(im, text("SETS", 330, YEL, extrude=14, ecol=(150, 95, 0)), 540, 590, -3)
    rb = mb.ribbon([("DUPLICATES HATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 70, "ExtraBold"), 120, 40,
                   fill=YEL)
    mb.paste_c(im, rb, 540, 820, 2)
    # before row: duplicates crossed
    items = [("apple", False), ("mango", False), ("apple", True), ("kiwi", False), ("mango", True)]
    xs = [175, 445, 720, 300, 600]
    ys = [1010, 1010, 1010, 1130, 1130]
    for (it, dup), x, y in zip(items, xs, ys):
        mb.paste_c(im, chip(it, RED if dup else (200, 200, 210), 46, dup), x, y, -3 if dup else 0)
    # arrow
    d = ImageDraw.Draw(im)
    d.line((540, 1215, 540, 1300), fill=YEL, width=14)
    d.polygon([(540, 1340), (500, 1290), (580, 1290)], fill=YEL)
    # after: { apple mango kiwi }
    f = mb.font(MONO, 190)
    lay = Image.new("RGBA", im.size)
    ld = ImageDraw.Draw(lay)
    ld.text((100, 1455), "{", font=f, fill=GREEN, anchor="mm")
    ld.text((975, 1455), "}", font=f, fill=GREEN, anchor="mm")
    im.alpha_composite(p4.glow(lay, GREEN, 14))
    for it, x in (("apple", 290), ("mango", 540), ("kiwi", 775)):
        mb.paste_c(im, chip(it, GREEN, 44), x, 1470)
    mb.paste_c(im, mb.mascot(330), 900, 1735)
    mb.paste_c(im, mb.bubble("Sab unique!", mb.font(mb.BALOO, 50, "ExtraBold"), 24), 560, 1700)
    mb.paste_c(im, text("1 LINE MEIN!", 76, WHITE, stroke=8, extrude=6), 300, 1820, -3)
    return im.convert("RGB")


def horizontal():
    W, H = 1280, 720
    im = grid_bg(W, H, 64)
    glow_spot(im, 330, 330, 330, (255, 150, 40), 70)
    glow_spot(im, 940, 420, 300, (60, 200, 110), 60)
    mb.paste_c(im, badge("EP 20", 30), 90, 50)
    mb.paste_c(im, text("PYTHON", 92, WHITE, stroke=8, extrude=6), 300, 130, -2)
    mb.paste_c(im, text("SETS", 230, YEL, extrude=12, ecol=(150, 95, 0)), 320, 320, -3)
    rb = mb.ribbon([("DUPLICATES HATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 50, "ExtraBold"), 86, 30,
                   fill=YEL)
    mb.paste_c(im, rb, 330, 500, 2)
    mb.paste_c(im, text("1 LINE MEIN!", 54, WHITE, stroke=7, extrude=5), 300, 630, -3)
    # right side: before -> after
    for (it, dup), (x, y) in zip([("apple", False), ("apple", True), ("mango", False), ("mango", True)],
                                 [(760, 120), (1000, 120), (760, 215), (1000, 215)]):
        mb.paste_c(im, chip(it, RED if dup else (200, 200, 210), 34, dup), x, y, -3 if dup else 0)
    d = ImageDraw.Draw(im)
    d.line((880, 285, 880, 345), fill=YEL, width=12)
    d.polygon([(880, 375), (848, 335), (912, 335)], fill=YEL)
    f = mb.font(MONO, 120)
    lay = Image.new("RGBA", im.size)
    ld = ImageDraw.Draw(lay)
    ld.text((655, 460), "{", font=f, fill=GREEN, anchor="mm")
    ld.text((1110, 460), "}", font=f, fill=GREEN, anchor="mm")
    im.alpha_composite(p4.glow(lay, GREEN, 12))
    mb.paste_c(im, chip("apple", GREEN, 34), 775, 470)
    mb.paste_c(im, chip("mango", GREEN, 34), 985, 470)
    mb.paste_c(im, mb.mascot(200), 1180, 625)
    mb.paste_c(im, mb.bubble("Sab unique!", mb.font(mb.BALOO, 36, "ExtraBold"), 18), 950, 640)
    return im.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    v = vertical()
    v.save(os.path.join(OUT, "EP20_Sets_thumbnail_1080x1920.jpg"), quality=93)
    h = horizontal()
    h.save(os.path.join(OUT, "EP20_Sets_thumbnail_1280x720.jpg"), quality=93)
    print("ok")


if __name__ == "__main__":
    main()
