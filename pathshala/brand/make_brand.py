#!/usr/bin/env python3
"""Profile picture and page cover for Python Ki Pathshala (Facebook / YouTube).

Reuses the EP01 short's look (cream background, navy text, yellow highlight,
two-tone Py badge) so the page and the reels feel like one brand.

Run:   python3 pathshala/brand/make_brand.py
Output: pathshala/brand/output/profile_1080.png  (upload as the profile picture; shown as a circle)
        pathshala/brand/output/cover_1640x624.png (Facebook page cover)
        pathshala/brand/output/profile_colorful_1080.png, cover_colorful_1640x624.png (vibrant versions)
"""
import os
import sys

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ep01-python-kya-hai"))
from build_short import (BLUE, CREAM, GRAY, GREEN, NAVY, PURPLE, RED, WHITE, YELLOW,  # noqa: E402
                         card, font, paste, pill, py_badge, rays, text)

OUT = os.path.join(HERE, "output")


def bg(w, h, tint=CREAM, glow_at=(0.5, 0.5), dots=True, glyphs=True, seed=4):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.clip(1 - np.hypot((xx - w * glow_at[0]) / max(w, h), (yy - h * glow_at[1]) / max(w, h)) * 1.4, 0, 1)[..., None]
    t = np.array(tint, np.float32)
    base = t * (0.94 + 0.06 * g) + (255 - t) * 0.6 * g
    if dots:
        d = (((xx % 46) - 23) ** 2 + ((yy % 46) - 23) ** 2 < 4).astype(np.float32)[..., None]
        base *= 1 - 0.06 * d
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    if glyphs:
        dr = ImageDraw.Draw(im)
        rng = np.random.default_rng(seed)
        for _ in range(int(w * h / 26000)):
            dr.text((rng.uniform(0, w), rng.uniform(0, h)), rng.choice(list("{}[]()01:#=<>")),
                    font=font(int(rng.uniform(26, 60)), "mono"), fill=tuple(int(c * 0.84) for c in tint) + (255,))
    return im


def profile(path, S=1080):
    im = bg(S, S, tint=(255, 243, 204), glyphs=False)
    paste(im, rays(1500), S / 2, S * 0.44, 1.0, a=0.75)
    # content kept inside the central circle (Facebook/YouTube crop it round)
    paste(im, py_badge(560), S / 2, S * 0.42)
    paste(im, pill("PATHSHALA", 92, fg=NAVY, bg=YELLOW, border=NAVY, padx=44, pady=22), S / 2, S * 0.78, rot=-3)
    im.convert("RGB").save(path)


def code_card(lines, w, h):
    c = card(w, h, r=28).copy()
    d = ImageDraw.Draw(c)
    x0, y0 = 40, 40           # card() sprite has a 40 px shadow pad
    for k, col in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((x0 + 26 + k * 34, y0 + 24, x0 + 46 + k * 34, y0 + 44), fill=col + (255,))
    c.alpha_composite(text("pathshala.py", 24, GRAY, "mono"), (x0 + 140, y0 + 20))
    d.line([(x0 + 6, y0 + 68), (x0 + w - 6, y0 + 68)], fill=(225, 225, 235, 255), width=3)
    f = font(32, "mono")
    for i, segs in enumerate(lines):
        x = x0 + 30
        for s, col in segs:
            d.text((x, y0 + 96 + i * 52), s, font=f, fill=col + (255,))
            x += f.getlength(s)
    return c


def cover(path, Wc=1640, Hc=624, scale=1.0):
    """Facebook cover. Mobile shows only the centre ~1110 px, and the profile
    picture overlaps the bottom-left, so the key text sits centre/right-of-centre."""
    im = bg(Wc, Hc, tint=CREAM, glow_at=(0.5, 0.45))
    s = scale
    cx = Wc * 0.47
    # left decoration: Py badge on rays (fine if cropped on mobile)
    paste(im, rays(1400), Wc * 0.13, Hc * 0.42, 0.7 * s, a=0.7)
    paste(im, py_badge(int(300 * s)), Wc * 0.13, Hc * 0.40, rot=-6)
    # right decoration: code card
    code = [[("print", BLUE), ("(", GRAY), ('"Namaste', GREEN)],
            [('  Duniya!"', GREEN), (")", GRAY)],
            [("# roz 1 concept", GRAY)],
            [("seekho", NAVY), (" = ", GRAY), ("True", PURPLE)]]
    paste(im, code_card(code, 400, 330), Wc * 0.895, Hc * 0.47, 0.82 * s, rot=4)
    # centre title block
    paste(im, pill("PYTHON", int(104 * s), fg=NAVY, bg=YELLOW, border=NAVY, padx=int(38 * s), pady=int(18 * s)),
          cx - 170 * s, Hc * 0.25, rot=-3)
    paste(im, text("KI PATHSHALA", int(84 * s), NAVY), cx + 40 * s, Hc * 0.45)
    paste(im, text("Python seekho apni bhasha mein  •  Hinglish", int(32 * s), BLUE), cx, Hc * 0.61)
    chips = ["Roz 1 Reel", "Zero se Coding", "Beginners Welcome"]
    sprites = [pill(ch, int(27 * s), fg=NAVY, bg=WHITE, border=NAVY, padx=int(24 * s), pady=int(12 * s)) for ch in chips]
    gap = -20 * s                      # pill sprites carry ~48 px of shadow padding
    x = cx - (sum(p.width for p in sprites) + gap * (len(sprites) - 1)) / 2
    for p in sprites:
        paste(im, p, x + p.width / 2, Hc * 0.77)
        x += p.width + gap
    paste(im, pill("NEW REEL DAILY  •  7 PM", int(26 * s), fg=WHITE, bg=RED, border=NAVY, padx=int(22 * s),
                   pady=int(10 * s)), cx, Hc * 0.91)
    im.convert("RGB").save(path)


# ---------------------------------------------------------------- colourful versions
PINK = (255, 64, 160)
CYAN = (0, 200, 230)
LIME = (130, 220, 60)
ORANGE = (255, 140, 30)
GRAD = [(0.0, (106, 17, 203)), (0.35, (37, 117, 252)), (0.65, (0, 201, 167)), (1.0, (255, 196, 0))]


def grad_bg(w, h, seed=2):
    """Diagonal purple -> blue -> teal -> yellow gradient with soft colour blobs and sprinkles."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx / w * 0.75 + yy / h * 0.25)
    img = np.zeros((h, w, 3), np.float32)
    for (u0, c0), (u1, c1) in zip(GRAD, GRAD[1:]):
        m = ((u >= u0) & (u <= u1))[..., None]
        k = ((u - u0) / (u1 - u0))[..., None]
        img = np.where(m, np.array(c0) + (np.array(c1) - np.array(c0)) * k, img)
    rng = np.random.default_rng(seed)
    for col in (PINK, CYAN, ORANGE, (255, 255, 255)):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.25, 0.45) * max(w, h)
        g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r / 2) ** 2)))[..., None] * 0.45
        img = img * (1 - g) + np.array(col, np.float32) * g
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for _ in range(int(w * h / 22000)):
        d.text((rng.uniform(0, w), rng.uniform(0, h)), rng.choice(list("{}[]()01:#=<>")),
               font=font(int(rng.uniform(26, 64)), "mono"), fill=(255, 255, 255, 60))
    im.alpha_composite(over)
    return im


def sprinkles(im, n, seed=5, box=None, avoid=None):
    """Confetti dots, bars and stars scattered over the image (skipping the `avoid` ellipse)."""
    w, h = im.size
    x0, y0, x1, y1 = box or (0, 0, w, h)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    cols = [YELLOW, PINK, CYAN, LIME, ORANGE, WHITE]
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if avoid and ((x - avoid[0]) / avoid[2]) ** 2 + ((y - avoid[1]) / avoid[3]) ** 2 < 1:
            continue
        col = cols[rng.integers(len(cols))] + (235,)
        k, sz = rng.integers(3), rng.uniform(7, 16)
        if k == 0:
            d.ellipse((x - sz / 2, y - sz / 2, x + sz / 2, y + sz / 2), fill=col)
        elif k == 1:
            a = rng.uniform(0, math.pi)
            dx, dy = math.cos(a) * sz, math.sin(a) * sz
            d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=col, width=int(sz / 2.2))
        else:
            pts = [(x + (sz if i % 2 == 0 else sz / 2.3) * math.cos(-math.pi / 2 + i * math.pi / 5),
                    y + (sz if i % 2 == 0 else sz / 2.3) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
            d.polygon(pts, fill=col)


def rainbow_rays(size, n=24):
    cols = [YELLOW, PINK, CYAN, LIME, ORANGE, WHITE]
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=cols[i % len(cols)] + (120,))
    yy, xx = np.mgrid[0:size, 0:size]
    fade = np.clip(1.2 - np.hypot(xx - c, yy - c) / c, 0, 1) ** 1.2
    im.putalpha(Image.fromarray((np.asarray(im.getchannel("A"), np.float32) * fade).astype(np.uint8)))
    return im


def outlined(s, size, fill=WHITE, stroke=NAVY, sw=None, shadow=True):
    f = font(size)
    sw = sw or max(3, size // 14)
    x0, y0, x1, y1 = f.getbbox(s, stroke_width=sw)
    im = Image.new("RGBA", (x1 - x0 + 16, y1 - y0 + 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8 - x0, 8 - y0), s, font=f, fill=fill + (255,), stroke_width=sw, stroke_fill=stroke + (255,))
    if not shadow:
        return im
    pad = 24
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, NAVY + (0,))
    sh.putalpha(im.getchannel("A").point(lambda v: v * 120 // 255))
    out.alpha_composite(sh, (pad + 6, pad + 10))
    out = out.filter(ImageFilter.GaussianBlur(6))
    out.alpha_composite(im, (pad, pad))
    return out


def profile_colorful(path, S=1080):
    im = grad_bg(S, S, seed=8)
    paste(im, rainbow_rays(1600), S / 2, S * 0.44, 1.0)
    sprinkles(im, 140, seed=3, avoid=(S / 2, S * 0.45, 330, 330))
    # white halo behind the badge so it pops off the colours
    halo = Image.new("RGBA", (1000, 1000), (255, 255, 255, 0))   # white, so the blur has no grey fringe
    ImageDraw.Draw(halo).ellipse((210, 210, 790, 790), fill=(255, 255, 255, 200))
    paste(im, halo.filter(ImageFilter.GaussianBlur(40)), S / 2, S * 0.43)
    paste(im, py_badge(560), S / 2, S * 0.42)
    paste(im, pill("PATHSHALA", 92, fg=NAVY, bg=YELLOW, border=NAVY, padx=44, pady=22), S / 2, S * 0.78, rot=-3)
    im.convert("RGB").save(path)


def cover_colorful(path, Wc=1640, Hc=624):
    im = grad_bg(Wc, Hc, seed=2)
    cx = Wc * 0.47
    paste(im, rainbow_rays(1400), Wc * 0.13, Hc * 0.42, 0.75)
    sprinkles(im, 160, seed=11, avoid=(cx, Hc * 0.5, 520, 250))
    paste(im, py_badge(300), Wc * 0.13, Hc * 0.40, rot=-6)
    code = [[("print", BLUE), ("(", GRAY), ('"Namaste', GREEN)],
            [('  Duniya!"', GREEN), (")", GRAY)],
            [("# roz 1 concept", GRAY)],
            [("seekho", NAVY), (" = ", GRAY), ("True", PURPLE)]]
    paste(im, code_card(code, 400, 330), Wc * 0.895, Hc * 0.47, 0.82, rot=4)
    paste(im, pill("PYTHON", 104, fg=NAVY, bg=YELLOW, border=NAVY, padx=38, pady=18), cx - 170, Hc * 0.25, rot=-3)
    paste(im, outlined("KI PATHSHALA", 84), cx + 40, Hc * 0.45)
    paste(im, pill("Python seekho apni bhasha mein  •  Hinglish", 28, fg=NAVY, bg=WHITE, border=None,
                   padx=26, pady=10), cx, Hc * 0.61)
    chips = [("Roz 1 Reel", PINK), ("Zero se Coding", CYAN), ("Beginners Welcome", LIME)]
    sprites = [pill(ch, 27, fg=NAVY, bg=bgc, border=NAVY, padx=24, pady=12) for ch, bgc in chips]
    gap = -20
    x = cx - (sum(p.width for p in sprites) + gap * (len(sprites) - 1)) / 2
    for p in sprites:
        paste(im, p, x + p.width / 2, Hc * 0.77)
        x += p.width + gap
    paste(im, pill("NEW REEL DAILY  •  7 PM", 26, fg=WHITE, bg=RED, border=NAVY, padx=22, pady=10), cx, Hc * 0.91)
    im.convert("RGB").save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    profile(os.path.join(OUT, "profile_1080.png"))
    cover(os.path.join(OUT, "cover_1640x624.png"))
    profile_colorful(os.path.join(OUT, "profile_colorful_1080.png"))
    cover_colorful(os.path.join(OUT, "cover_colorful_1640x624.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
