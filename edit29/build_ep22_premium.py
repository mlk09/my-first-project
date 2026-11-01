#!/usr/bin/env python3
"""EP 22 Functions - PREMIUM look (24.7 s), styled after the user's AI reference clip.

Decoded from the reference (1080x1920, 24 fps, 10 s): the same EP 22 content, re-dressed with
  * a warm ORANGE SPOTLIGHT pouring down from the top centre over the dark grid
  * an anime SPEED-LINE burst behind the hook text
  * def( ) burning with an orange FIRE glow
  * a dark-glass recipe card with neon edges and HUD corner brackets
  * an illustrated, STEAMING bowl of Maggi instead of plain chips
  * a glossy editor frame with a soft glow, plus sparkles around the output
  * drifting 4-point sparkle stars in the background
Content and timing = build_ep22_short.py (same time map, SFX and music).

Usage:  python3 edit29/build_ep22_premium.py
"""
import math
import os
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep22_short as sh   # noqa: E402

e = sh.e
p4, mb = e.p4, e.mb
W, H = e.W, e.H
paste, pop, ease, _glow = e.paste, e.pop, e.ease, e.glow


def glow(im, col, r=10):
    """p4.glow pads by 3r on each side; crop back so overlays stay registered"""
    g = _glow(im, col, r)
    p = r * 3
    return g.crop((p, p, p + im.width, p + im.height))
YEL, GREEN, ORANGE, WHITE, CYAN = e.YEL, e.GREEN, e.ORANGE, e.WHITE, (90, 220, 255)
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP22_Functions_Premium.mp4")
_bg0 = p4.background


# ------------------------------------------------------------------ background: spotlight + speed lines + sparkles
@lru_cache(None)
def spotlight():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cone = np.exp(-((xx - W / 2) / (180 + 0.55 * yy)) ** 2) * np.exp(-yy / 900)
    core = np.exp(-(((xx - W / 2) / 260) ** 2 + ((yy + 60) / 260) ** 2))
    a = np.clip(cone * 0.55 + core * 0.9, 0, 1)
    rgb = np.zeros((H, W, 4), np.uint8)
    rgb[..., 0], rgb[..., 1], rgb[..., 2] = 255, 160, 60
    rgb[..., 3] = (a * 120).astype(np.uint8)
    return Image.fromarray(rgb)


def speed_lines(t, strength):
    lay = Image.new("RGBA", (W // 2, H // 2))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(int(t * 12))          # re-jitter 12x per second, like hand-drawn action lines
    cx, cy = W / 4, 300
    for _ in range(46):
        ang = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(260, 380)
        r1 = r0 + rng.uniform(250, 700)
        w = rng.uniform(1.5, 5)
        pts = [(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)),
               (cx + r1 * math.cos(ang + 0.012), cy + r1 * math.sin(ang + 0.012)),
               (cx + r1 * math.cos(ang - 0.012), cy + r1 * math.sin(ang - 0.012))]
        d.polygon(pts, fill=(235, 235, 240, int(rng.uniform(90, 200) * strength)))
        d.line((pts[0], ((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2)),
               fill=(255, 255, 255, int(150 * strength)), width=int(w))
    return lay.resize((W, H), Image.BILINEAR)


@lru_cache(None)
def star4(s):
    im = Image.new("RGBA", (s * 2, s * 2))
    d = ImageDraw.Draw(im)
    c = s
    d.polygon([(c, 0), (c + s * 0.22, c - s * 0.22), (2 * s, c), (c + s * 0.22, c + s * 0.22), (c, 2 * s),
               (c - s * 0.22, c + s * 0.22), (0, c), (c - s * 0.22, c - s * 0.22)], fill=(220, 225, 235, 255))
    return im


def background(t):
    fr = _bg0(t).copy()
    fr.alpha_composite(spotlight())
    if t < 3.4:
        fr.alpha_composite(speed_lines(t, 1.0 if t < 3.0 else 1 - (t - 3.0) / 0.4))
    rng = np.random.default_rng(22)
    for k in range(7):
        x0, y0, sp = rng.uniform(80, W - 80), rng.uniform(300, H - 200), rng.uniform(6, 14)
        tw = 0.5 + 0.5 * math.sin(t * rng.uniform(1.5, 3) + k)
        y = (y0 - t * sp) % (H - 300) + 250
        paste(fr, star4(int(14 + 8 * tw)), x0, y, 1, 0.25 + 0.45 * tw)
    return fr


# ------------------------------------------------------------------ hook: def( ) on fire
def fire_glow(layer, t):
    a = np.asarray(layer.getchannel("A"))
    flick = 0.85 + 0.15 * math.sin(t * 23) * math.sin(t * 7.3)
    out = Image.new("RGBA", layer.size)
    for r, col, k in ((40, (255, 90, 0), 1.0), (18, (255, 150, 30), 1.2), (7, (255, 220, 120), 1.0)):
        g = Image.fromarray(a).filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * k * flick)))
        c = Image.new("RGBA", layer.size, col + (0,))
        c.putalpha(g)
        out.alpha_composite(c)
    # heat shimmer: a few rising embers
    d = ImageDraw.Draw(out)
    rng = np.random.default_rng(5)
    for _ in range(14):
        x = rng.uniform(260, 820)
        sp = rng.uniform(80, 160)
        y = 860 - ((t * sp + rng.uniform(0, 300)) % 300)
        s = rng.uniform(3, 7)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 170, 60, int(200 * (1 - (860 - y) / 300))))
    out.alpha_composite(layer)
    return out


def draw_hook(st, t):
    p4.type_text(st, t, 0.15, "PYTHON MEIN", e.CAP, 92, WHITE, 540, 560, cps=16)
    lay = Image.new("RGBA", (W, H))
    p4.type_text(lay, t, 0.9, "def( )", e.MONO, 200, (255, 175, 70), 540, 780, cps=8)
    st.alpha_composite(fire_glow(lay, t))
    rb = mb.ribbon([("EK BAAR LIKHO, BAAR-BAAR CHALAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 46, "ExtraBold"),
                   100, 34, fill=YEL)
    paste(st, rb, 540, 990, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Mehnat bachao!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 450, 1140, pop(t - 2.8, 0.3))


# ------------------------------------------------------------------ recipe: neon HUD card + steaming bowl
def hud_card(t):
    im = Image.new("RGBA", (700, 470))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 40, 40, 660, 430
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=(16, 18, 26, 225))
    edge = Image.new("RGBA", im.size)
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle((x0, y0, x1, y1), 30, outline=(220, 235, 255, 255), width=4)
    L = 70
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ed.line((cx, cy + sy * 22, cx, cy + sy * L), fill=(255, 160, 60, 255), width=9)
        ed.line((cx + sx * 22, cy, cx + sx * L, cy), fill=(255, 160, 60, 255), width=9)
    ed.line((x0 + 240, y1, x0 + 380, y1), fill=(255, 160, 60, 255), width=8)
    im.alpha_composite(glow(edge, CYAN, 14))
    d = ImageDraw.Draw(im)
    d.text((350, 95), "MAGGI RECIPE", font=mb.font(e.CAP, 48), fill=YEL, anchor="mm")
    for k, stp in enumerate(e.STEPS):
        if t >= 4.6 + 0.3 * k:
            d.text((90, 175 + 64 * k), stp, font=mb.font(e.CAP, 40), fill=WHITE, anchor="lm")
    return im


@lru_cache(None)
def bowl_img():
    S = 2
    im = Image.new("RGBA", (420 * S, 300 * S))
    d = ImageDraw.Draw(im)
    # noodles mound
    d.ellipse((40 * S, 40 * S, 380 * S, 150 * S), fill=(245, 200, 90))
    rng = np.random.default_rng(3)
    for _ in range(60):
        x = rng.uniform(70, 350) * S
        y = rng.uniform(55, 130) * S
        w = rng.uniform(30, 70) * S
        d.arc((x - w / 2, y - 14 * S, x + w / 2, y + 14 * S), rng.uniform(0, 180), rng.uniform(200, 360),
              fill=(215, 160, 50), width=3 * S)
    d.ellipse((230 * S, 60 * S, 330 * S, 120 * S), fill=(255, 255, 250))          # egg
    d.ellipse((262 * S, 74 * S, 300 * S, 106 * S), fill=(255, 190, 40))
    for _ in range(18):                                                          # spring onion
        x, y = rng.uniform(80, 340) * S, rng.uniform(60, 125) * S
        d.ellipse((x - 6 * S, y - 4 * S, x + 6 * S, y + 4 * S), fill=(70, 180, 70))
    # bowl
    d.chord((20 * S, -40 * S, 400 * S, 300 * S), 0, 180, fill=(235, 238, 245))
    d.chord((20 * S, -40 * S, 400 * S, 300 * S), 0, 180, outline=(200, 205, 215), width=4 * S)
    for k, yy in enumerate((150, 180)):
        d.arc((40 * S, (yy - 175) * S, 380 * S, (yy + 120) * S), 20, 160, fill=(215, 55, 55), width=10 * S)
    d.ellipse((20 * S, 100 * S, 400 * S, 160 * S), outline=(210, 60, 60), width=8 * S)
    d.rounded_rectangle((150 * S, 268 * S, 270 * S, 292 * S), 10 * S, fill=(200, 205, 215))
    return im.resize((420, 300), Image.LANCZOS)


def steam(t, w=420, h=320):
    lay = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(lay)
    for k in range(3):
        x0 = 130 + 80 * k
        pts = []
        for j in range(30):
            v = j / 29
            y = h - 20 - v * (h - 40)
            x = x0 + 28 * math.sin(v * 7 + t * 3.2 + k * 2) * (0.4 + v)
            pts.append((x, y))
        d.line(pts, fill=(255, 255, 255, 150), width=16, joint="curve")
    lay = lay.filter(ImageFilter.GaussianBlur(9))
    fade = np.linspace(0, 1, h)[:, None] ** 0.8 * np.ones((1, w))
    a = np.asarray(lay.getchannel("A")).astype(np.float32) * fade
    lay.putalpha(Image.fromarray(a.astype(np.uint8)))
    return lay


def draw_recipe(st, t):
    paste(st, hud_card(t), 540, 640, pop(t - 4.3, 0.3))
    if t >= e.CALL_T:
        a = t - e.CALL_T
        paste(st, steam(t), 540, 860, 1, min(1, a / 0.4))
        paste(st, bowl_img(), 540, 1060, pop(a, 0.35))
        n = min(3, 1 + int(a / 0.35))
        paste(st, mb.outlined(f"x{n}", mb.font(mb.BALOO, 110, "ExtraBold"), GREEN, 8, (10, 10, 10), 6, (20, 90, 40)),
              860, 960, pop(a - 0.35 * (n - 1), 0.25), 1, 8)
    if t > 8.8:
        paste(st, p4.pill("RECIPE = FUNCTION", YEL, 50), 540, 1290, pop(t - 8.8, 0.3))


# ------------------------------------------------------------------ glossy glowing editor + sparkles
_chrome0 = p4.editor_chrome


@lru_cache(None)
def editor_chrome():
    im = Image.new("RGBA", (W, H))
    edge = Image.new("RGBA", (W, H))
    ImageDraw.Draw(edge).rounded_rectangle((p4.EX0, p4.EY0, p4.EX1, p4.EY1), 26, outline=(255, 160, 60, 255), width=14)
    g = edge.filter(ImageFilter.GaussianBlur(22))
    g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * 1.8))))
    im.alpha_composite(g)
    ring = Image.new("RGBA", (W, H))
    ImageDraw.Draw(ring).rounded_rectangle((p4.EX0 - 2, p4.EY0 - 2, p4.EX1 + 2, p4.EY1 + 2), 28,
                                           outline=(255, 200, 140, 255), width=3)
    im.alpha_composite(ring)
    im.alpha_composite(_chrome0())
    hl = Image.new("RGBA", (W, H))                                   # glossy top highlight
    ImageDraw.Draw(hl).rounded_rectangle((p4.EX0 + 6, p4.EY0 + 4, p4.EX1 - 6, p4.EY0 + 40), 20,
                                         fill=(255, 255, 255, 18))
    im.alpha_composite(hl)
    return im


def editor_sparkles(fr, t):
    for name, cfg in p4.EDITOR.items():
        ok = cfg.get("ok")
        if ok is None or not (ok <= t < ok + 1.6):
            continue
        a = t - ok
        rng = np.random.default_rng(int(ok * 10))
        for k in range(10):
            x = rng.uniform(p4.EX0 + 40, p4.EX1 - 40)
            y = rng.uniform(p4.TERM_Y0 - 40, p4.EY1 - 40) - 60 * a
            s = int(10 + 12 * rng.random())
            al = max(0.0, 1 - a / 1.6) * (0.6 + 0.4 * math.sin(a * 12 + k))
            paste(fr, _glow(star4(s), YEL, 6), x, y, 1, al)


# ------------------------------------------------------------------ wire it up
p4.background = background
p4.editor_chrome = editor_chrome
e.GRID["hook"], e.GRID["recipe"] = draw_hook, draw_recipe
_mascot0 = p4.draw_mascot


def draw_mascot(fr, t):
    editor_sparkles(fr, t)
    _mascot0(fr, t)


p4.draw_mascot = draw_mascot
p4.OUT = OUT

if __name__ == "__main__":
    p4.main()
