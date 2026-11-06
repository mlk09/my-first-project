#!/usr/bin/env python3
"""CREAM theme (light, warm white-cream) for the cinematic shorts.

* background(t): warm cream paper with a slowly drifting dot grid, two soft pastel blobs (peach / mint)
  that float around, and faint code glyphs ( { } def ( ) [ ] # ) drifting upwards
* caption_img(text): sticker captions - dark navy text, thick white outline, soft shadow;
  *word* = deep orange, +text+ = green, -text- = red
* vignette(): a very light edge falloff (the dark-theme vignette would turn the edges grey)
"""
import math
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
INK = (28, 32, 64)
DEEP = (60, 70, 210)
HOT = (232, 104, 16)
LEAF = (22, 150, 72)
CHERRY = (214, 40, 54)
CREAM = np.array([250, 245, 233], np.float32)


@lru_cache(None)
def _base():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .42) / H) ** 2)
    shade = np.clip(1 - 0.10 * r ** 1.6, 0.9, 1)[..., None]
    return CREAM * shade


@lru_cache(None)
def _dots():
    cell = 54
    im = Image.new("L", (W + cell, H + cell), 0)
    d = ImageDraw.Draw(im)
    for y in range(0, H + cell, cell):
        for x in range(0, W + cell, cell):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
    return np.asarray(im).astype(np.float32) / 255, cell


@lru_cache(None)
def _blob(r):
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32)
    return np.exp(-(xx ** 2 + yy ** 2) / (2 * (r * 0.42) ** 2))


@lru_cache(None)
def _glyphs():
    out = []
    rng = np.random.default_rng(27)
    from PIL import ImageFont
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 64)
    except OSError:
        f = ImageFont.load_default()
    for k in range(14):
        s = ["{ }", "def", "( )", "[ ]", "#", "==", "py", ":"][k % 8]
        im = Image.new("RGBA", (220, 110))
        ImageDraw.Draw(im).text((110, 55), s, font=f, fill=(205, 190, 160, 255), anchor="mm")
        out.append((im, rng.uniform(60, W - 60), rng.uniform(0, H), rng.uniform(10, 24), rng.uniform(-12, 12)))
    return out


def background(t):
    a = _base().copy()
    dots, cell = _dots()
    ox, oy = int(t * 8) % cell, int(t * 14) % cell
    a -= dots[oy:oy + H, ox:ox + W][..., None] * np.array([30, 36, 50], np.float32)
    for (cx0, cy0, r, col, sx, sy, ph) in ((300, 560, 520, (255, 205, 165), 140, 90, 0.0),
                                           (820, 1380, 560, (190, 232, 210), 120, 140, 1.7),
                                           (760, 300, 380, (210, 215, 255), 90, 70, 3.1)):
        cx = int(cx0 + sx * math.sin(t * 0.35 + ph))
        cy = int(cy0 + sy * math.cos(t * 0.28 + ph))
        b = _blob(r)
        x0, y0 = cx - r, cy - r
        xs, ys = max(0, -x0), max(0, -y0)
        xe, ye = min(2 * r, W - x0), min(2 * r, H - y0)
        if xe > xs and ye > ys:
            reg = a[y0 + ys:y0 + ye, x0 + xs:x0 + xe]
            m = b[ys:ye, xs:xe][..., None] * 0.55
            reg[:] = reg * (1 - m) + np.array(col, np.float32) * m
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    for im, x, y0, sp, rot in _glyphs():
        y = (y0 - t * sp) % (H + 120) - 60
        g = im.rotate(rot + 4 * math.sin(t * 0.6 + x), Image.BICUBIC)
        g.putalpha(g.getchannel("A").point(lambda v: int(v * 0.55)))
        img.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
    return img


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.08 * r ** 2.4, 0.9, 1)[..., None]


def make_caption_img(mb, CAP):
    @lru_cache(None)
    def caption_img(text):
        tags = {"*": HOT, "+": LEAF, "-": CHERRY}
        parts = []
        whole = text[0] in "+-" and text[-1] == text[0] and len(text) > 1
        body = text[1:-1] if whole else text
        for tok in body.split(" "):
            c = tags[text[0]] if whole else INK
            if not whole and len(tok) > 2 and tok[0] in tags and tok[0] in tok[1:]:
                ch = tok[0]
                end = tok.rindex(ch)
                c, tok = tags[ch], tok[1:end] + tok[end + 1:]
            parts.append((tok, c))
        size = 76
        f = mb.font(CAP, size)
        sp = f.getlength(" ")
        tw = sum(f.getlength(p) for p, _ in parts) + sp * (len(parts) - 1)
        if tw > 980:
            size = int(size * 980 / tw)
            f = mb.font(CAP, size)
            sp = f.getlength(" ")
            tw = sum(f.getlength(p) for p, _ in parts) + sp * (len(parts) - 1)
        im = Image.new("RGBA", (W, 200))
        d = ImageDraw.Draw(im)
        x = (W - tw) / 2
        for p, c in parts:
            d.text((x, 100), p, font=f, fill=c, anchor="lm", stroke_width=9, stroke_fill=(255, 255, 255))
            x += f.getlength(p) + sp
        sh = Image.new("RGBA", im.size, (90, 70, 40, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * .35)))
        out = Image.new("RGBA", im.size)
        out.alpha_composite(sh, (0, 7))
        out.alpha_composite(im)
        return out
    return caption_img
