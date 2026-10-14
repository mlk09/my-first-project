#!/usr/bin/env python3
"""Profile picture and page cover for Python Ki Pathshala (Facebook / YouTube).

Reuses the EP01 short's look (cream background, navy text, yellow highlight,
two-tone Py badge) so the page and the reels feel like one brand.

Run:   python3 pathshala/brand/make_brand.py
Output: pathshala/brand/output/profile_1080.png  (upload as the profile picture; shown as a circle)
        pathshala/brand/output/cover_1640x624.png (Facebook page cover)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

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


def main():
    os.makedirs(OUT, exist_ok=True)
    profile(os.path.join(OUT, "profile_1080.png"))
    cover(os.path.join(OUT, "cover_1640x624.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
