#!/usr/bin/env python3
"""Python ki Pathshala - channel art.

Writes
  output/pathshala_thumbnail_1920x1080.jpg   (16:9 - channel trailer / video thumbnail / social)
  output/pathshala_banner_2560x1440.jpg      (YouTube banner, all text inside the 1546x423 safe area)
  output/pathshala_logo_800x800.png          (profile picture)
Run cut_mascot.py first (assets/mascot.png).
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "output")
BALOO = os.path.join(A, "fonts", "Baloo2.ttf")
FREDOKA = os.path.join(A, "fonts", "Fredoka.ttf")
CHALK = os.path.join(A, "fonts", "Kalam-Bold.ttf")
MONO = os.path.join(HERE, "..", "edit7", "assets", "fonts", "JetBrainsMono-Bold.ttf")

YEL = (255, 196, 30)
WHITE = (246, 248, 244)
RED = (255, 82, 82)
DARK = (8, 30, 16)


def font(path, size, var=None):
    f = ImageFont.truetype(path, size)
    if var:
        f.set_variation_by_name(var)
    return f


def board(W, H, seed=3):
    """chalkboard: radial green gradient + chalk dust + smudges"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * 0.42) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    t = np.clip(r / 0.75, 0, 1)[..., None]
    c0, c1 = np.array([30, 92, 50], np.float32), np.array([7, 30, 15], np.float32)
    img = c0 * (1 - t) + c1 * t
    rng = np.random.default_rng(seed)
    img += rng.normal(0, 3.5, (H, W, 1))
    smudge = rng.normal(0, 1, (H // 16, W // 16)).astype(np.float32)
    smudge = np.asarray(Image.fromarray(smudge).resize((W, H), Image.BICUBIC))
    img += np.clip(smudge, 0, None)[..., None] * 5
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


def wood_frame(im, w):
    W, H = im.size
    fr = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(fr)
    rng = np.random.default_rng(1)
    for k in range(w):
        f = k / w
        base = np.array([120, 72, 38]) * (0.75 + 0.35 * math.sin(f * math.pi))
        col = tuple(int(v) for v in base) + (255,)
        d.rectangle((k, k, W - 1 - k, H - 1 - k), outline=col)
    grain = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grain)
    for _ in range(260):
        y = int(rng.uniform(0, w))
        x = int(rng.uniform(0, W))
        gd.line((x, y, x + int(rng.uniform(40, 200)), y), fill=(60, 30, 10, 70), width=2)
        gd.line((x, H - 1 - y, x + int(rng.uniform(40, 200)), H - 1 - y), fill=(60, 30, 10, 70), width=2)
        yy = int(rng.uniform(0, H))
        gd.line((y, yy, y, yy + int(rng.uniform(40, 200))), fill=(60, 30, 10, 70), width=2)
        gd.line((W - 1 - y, yy, W - 1 - y, yy + int(rng.uniform(40, 200))), fill=(60, 30, 10, 70), width=2)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle((0, 0, W, H), fill=255)
    ImageDraw.Draw(m).rectangle((w, w, W - 1 - w, H - 1 - w), fill=0)
    fr.alpha_composite(grain)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sm).rectangle((w - 2, w - 2, W - w + 1, H - w + 1), outline=255, width=18)
    sh.putalpha(sm.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8)))
    im.alpha_composite(sh)
    im.paste(fr, (0, 0), m)


def chalk_text(im, xy, txt, f, alpha=60, rot=0, col=(255, 255, 255)):
    l, t, r, b = f.getbbox(txt)
    lay = Image.new("RGBA", (r - l + 20, b - t + 20))
    ImageDraw.Draw(lay).text((10 - l, 10 - t), txt, font=f, fill=col + (alpha,))
    noise = np.random.default_rng(len(txt)).random(lay.size[::-1]) > 0.25
    a = np.asarray(lay.getchannel("A")) * noise
    lay.putalpha(Image.fromarray(a.astype(np.uint8)))
    if rot:
        lay = lay.rotate(rot, Image.BICUBIC, expand=True)
    im.alpha_composite(lay, (int(xy[0]), int(xy[1])))


def doodles(im, items, scale=1.0):
    for txt, x, y, size, rot, kind in items:
        f = font(MONO, int(size * scale)) if kind == "code" else font(CHALK, int(size * scale))
        chalk_text(im, (x, y), txt, f, alpha=55, rot=rot)


def outlined(txt, f, fill, stroke, scol, extrude=0, ecol=(0, 0, 0), shadow=True, tex=False):
    """big title text: 3D extrude + outline + soft drop shadow (+ optional chalk texture)"""
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    pad = 40 + extrude
    W, H = r - l + 2 * pad, b - t + 2 * pad
    out = Image.new("RGBA", (W, H))
    o = (pad - l, pad - t)
    if shadow:
        s = Image.new("RGBA", (W, H))
        ImageDraw.Draw(s).text((o[0] + extrude + 6, o[1] + extrude + 10), txt, font=f, fill=(0, 0, 0, 170),
                               stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        out.alpha_composite(s.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(out)
    for k in range(extrude, 0, -1):
        d.text((o[0] + k, o[1] + k), txt, font=f, fill=ecol, stroke_width=stroke, stroke_fill=ecol)
    d.text(o, txt, font=f, fill=scol, stroke_width=stroke, stroke_fill=scol)
    face = Image.new("RGBA", (W, H))
    ImageDraw.Draw(face).text(o, txt, font=f, fill=fill)
    if tex:   # subtle chalk grain on the face
        a = np.asarray(face.getchannel("A")).astype(np.float32)
        a *= 0.9 + 0.1 * (np.random.default_rng(5).random(a.shape) > 0.3)
        face.putalpha(Image.fromarray(a.astype(np.uint8)))
    hi = Image.new("RGBA", (W, H))   # top highlight
    gy = np.linspace(1, 0, H)[:, None] * np.ones((1, W))
    hi.putalpha(Image.fromarray((np.clip(gy * 1.6 - 0.6, 0, 1) * 70).astype(np.uint8)))
    hi = Image.composite(hi, Image.new("RGBA", (W, H)), face.getchannel("A"))
    out.alpha_composite(face)
    out.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 0)))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (W, H), (255, 255, 255)).split(), hi.getchannel("A"))))
    return out


def paste_c(base, im, cx, cy, rot=0):
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def swoosh(base, x0, x1, y, col, width, rot=0):
    lay = Image.new("RGBA", base.size)
    d = ImageDraw.Draw(lay)
    n = 60
    pts_top = [(x0 + (x1 - x0) * i / n, y - math.sin(i / n * math.pi) * width * 0.6) for i in range(n + 1)]
    for i in range(n):
        th = width * math.sin((i + 0.5) / n * math.pi) ** 0.6
        d.line([pts_top[i], pts_top[i + 1]], fill=col + (255,), width=max(2, int(th)))
    a = np.asarray(lay.getchannel("A")).astype(np.float32)
    a *= np.random.default_rng(9).random(a.shape) > 0.18
    lay.putalpha(Image.fromarray(a.astype(np.uint8)))
    base.alpha_composite(lay)


def glow(base, cx, cy, r, col, a=120):
    g = Image.new("L", base.size, 0)
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=a)
    g = g.filter(ImageFilter.GaussianBlur(r * 0.45))
    lay = Image.new("RGBA", base.size, col + (0,))
    lay.putalpha(g)
    base.alpha_composite(lay)


def ribbon(txt_parts, f, h, pad=46, fill=YEL):
    """tagline ribbon with notched ends; txt_parts = [(text, colour, strike)]"""
    widths = [f.getlength(t) for t, _, _ in txt_parts]
    W = int(sum(widths) + 2 * pad + 2 * h * 0.35)
    im = Image.new("RGBA", (W + 20, h + 30))
    d = ImageDraw.Draw(im)
    n = h * 0.35
    poly = [(10, 10), (W + 10, 10), (W + 10 - n, 10 + h / 2), (W + 10, 10 + h), (10, 10 + h), (10 + n, 10 + h / 2)]
    sh = Image.new("RGBA", im.size)
    ImageDraw.Draw(sh).polygon([(x + 6, y + 10) for x, y in poly], fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.polygon(poly, fill=fill)
    x = 10 + n + pad
    cy = 10 + h / 2 + 2
    for (t, col, strike), w in zip(txt_parts, widths):
        d.text((x, cy), t, font=f, fill=col, anchor="lm")
        if strike:
            d.line((x - 6, cy + 4, x + w + 6, cy - 10), fill=RED, width=max(4, h // 14))
        x += w
    return im


def chip(txt, f, h, col=(255, 255, 255, 30), border=(255, 255, 255, 120), check=(80, 220, 120)):
    w = int(f.getlength(txt) + h * 1.35 + 30)
    im = Image.new("RGBA", (w + 4, h + 4))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w, h), h // 2, fill=(6, 26, 14, 200), outline=border, width=3)
    r = h * 0.32
    cx, cy = 2 + h / 2, 2 + h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=check)
    d.line([(cx - r * .5, cy), (cx - r * .1, cy + r * .42), (cx + r * .55, cy - r * .4)], fill=(255, 255, 255),
           width=max(3, h // 12), joint="curve")
    d.text((h + 6, 2 + h / 2 + 1), txt, font=f, fill=WHITE, anchor="lm")
    return im


def bubble(txt, f, pad=26):
    w, h = int(f.getlength(txt) + 2 * pad), int(f.size * 1.5 + pad)
    im = Image.new("RGBA", (w + 60, h + 70))
    d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size)
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((16, 16, w + 16, h + 16), 28, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d.rounded_rectangle((8, 8, w + 8, h + 8), 28, fill=(255, 255, 255), outline=DARK, width=5)
    d.polygon([(w - 90, h + 4), (w - 30, h + 4), (w + 10, h + 60)], fill=(255, 255, 255))
    d.line([(w - 90, h + 6), (w + 10, h + 60), (w - 30, h + 6)], fill=DARK, width=5)
    d.text((8 + w / 2, 8 + h / 2), txt, font=f, fill=DARK, anchor="mm")
    return im


def mascot(h):
    m = Image.open(os.path.join(A, "mascot.png")).convert("RGBA")
    m = m.resize((int(m.width * h / m.height), h), Image.LANCZOS)
    out = Image.new("RGBA", (m.width + 60, m.height + 60))
    s = Image.new("RGBA", out.size)
    s.putalpha(Image.new("L", out.size, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 160), (30, 44), m.getchannel("A"))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    # white chalk rim so it pops off the board
    rim = Image.new("RGBA", out.size, (0, 0, 0, 0))
    a = m.getchannel("A").filter(ImageFilter.MaxFilter(9))
    rim.paste((255, 255, 255, 230), (30, 30), a)
    out.alpha_composite(rim)
    out.alpha_composite(m, (30, 30))
    return out


def stars(base, pts, col=YEL):
    d = ImageDraw.Draw(base)
    for x, y, r in pts:
        p = []
        for k in range(8):
            rr = r if k % 2 == 0 else r * 0.38
            a = -math.pi / 2 + k * math.pi / 4
            p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        d.polygon(p, fill=col)


# ------------------------------------------------------------------ layouts
def thumbnail():
    W, H = 1920, 1080
    im = board(W, H)
    doodles(im, [(">>>", 90, 90, 64, 0, "code"), ('print("Hello")', 80, 830, 46, 4, "code"),
                 ("for i in range(5):", 860, 905, 40, -3, "code"), ("{ }", 1760, 80, 70, 8, "code"),
                 ("if x > 5:", 1650, 900, 42, 6, "code"), ("a = 10", 640, 70, 44, -4, "code"),
                 ("x² + y²", 1380, 90, 48, 5, "chalk"), ("01011", 60, 520, 40, 90, "code")])
    glow(im, 1490, 600, 420, YEL, 95)
    glow(im, 640, 470, 520, (90, 200, 120), 55)
    # mascot + speech bubble
    paste_c(im, mascot(820), 1500, 625)
    paste_c(im, bubble('print("Namaste!")', font(MONO, 40)), 1305, 205, 0)
    stars(im, [(1810, 330, 26), (1180, 470, 18), (1840, 760, 18)])
    # badge
    b = ribbon([("100% BEGINNER FRIENDLY", DARK, False)], font(BALOO, 44, "ExtraBold"), 74, 30, fill=(255, 82, 82))
    paste_c(im, b, 360, 175, 3)
    # title
    t1 = outlined("Python ki", font(BALOO, 190, "ExtraBold"), YEL, 10, DARK, 8, (120, 70, 0))
    paste_c(im, t1, 560, 335, 2)
    t2 = outlined("PATHSHALA", font(BALOO, 196, "ExtraBold"), WHITE, 11, DARK, 12, (20, 70, 40), tex=True)
    paste_c(im, t2, 625, 540, 2)
    swoosh(im, 150, 1110, 690, YEL, 30)
    # tagline ribbon
    f = font(BALOO, 50, "ExtraBold")
    rb = ribbon([("Coding se ", DARK, False), ("DARR", (90, 90, 90), True), (" nahi,  ", DARK, False),
                 ("DOSTI", (20, 110, 50), False), (" hoti hai!", DARK, False)], f, 92)
    paste_c(im, rb, 640, 795, -1)
    # chips
    fc = font(BALOO, 36, "Bold")
    x = 110
    for txt in ("Zero se shuru", "Easy Hindi", "Roz naya concept"):
        c = chip(txt, fc, 66)
        im.alpha_composite(c, (x, 900))
        x += c.width + 22
    wood_frame(im, 30)
    return im


def banner():
    W, H = 2560, 1440
    im = board(W, H, seed=8)
    sx0, sy0, sx1, sy1 = (W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2  # safe area
    doodles(im, [(">>>", 120, 160, 80, 0, "code"), ('print("Hello")', 2000, 1160, 60, 4, "code"),
                 ("for i in range(5):", 160, 1120, 56, -3, "code"), ("{ }", 2300, 180, 90, 8, "code"),
                 ("if x > 5:", 360, 300, 56, 6, "code"), ("a = 10", 1900, 300, 60, -4, "code"),
                 ("x² + y²", 1100, 160, 60, 5, "chalk"), ("01011", 2380, 600, 50, 90, "code"),
                 ("def learn():", 1000, 1150, 56, -2, "code")], 1.0)
    glow(im, sx1 - 250, H // 2, 330, YEL, 95)
    paste_c(im, mascot(440), sx1 - 210, H // 2 + 6)
    paste_c(im, bubble('print("Namaste!")', font(MONO, 30), 20), sx1 - 470, sy0 + 40)
    t1 = outlined("Python ki", font(BALOO, 112, "ExtraBold"), YEL, 7, DARK, 5, (120, 70, 0))
    t2 = outlined("PATHSHALA", font(BALOO, 168, "ExtraBold"), WHITE, 9, DARK, 10, (20, 70, 40), tex=True)
    cx = sx0 + 520
    paste_c(im, t1, cx - 120, sy0 + 60, 2)
    paste_c(im, t2, cx, sy0 + 192, 2)
    swoosh(im, sx0 + 40, sx0 + 1010, sy0 + 300, YEL, 22)
    f = font(BALOO, 38, "ExtraBold")
    rb = ribbon([("Coding se ", DARK, False), ("DARR", (90, 90, 90), True), (" nahi,  ", DARK, False),
                 ("DOSTI", (20, 110, 50), False), (" hoti hai!", DARK, False)], f, 70)
    paste_c(im, rb, cx, sy0 + 372, -1)
    fc = font(BALOO, 34, "Bold")
    x = sx0 + 60
    for txt in ("Zero se shuru", "Easy Hindi", "Roz naya concept", "Python Shorts"):
        c = chip(txt, fc, 60)
        im.alpha_composite(c, (int(x), sy1 + 40))
        x += c.width + 20
    return im


def logo():
    S = 800
    im = board(S, S, seed=2)
    glow(im, S // 2, S // 2, 330, YEL, 110)
    paste_c(im, mascot(640), S // 2 + 10, S // 2 + 10)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    thumbnail().convert("RGB").save(os.path.join(OUT, "pathshala_thumbnail_1920x1080.jpg"), quality=93)
    banner().convert("RGB").save(os.path.join(OUT, "pathshala_banner_2560x1440.jpg"), quality=93)
    logo().convert("RGB").save(os.path.join(OUT, "pathshala_logo_800x800.png"))
    print("done")


if __name__ == "__main__":
    main()
