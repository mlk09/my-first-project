#!/usr/bin/env python3
"""Python ki Pathshala EP 24 - Default arguments, CINEMATIC plexus look (about 26.5 s)

Same look as EP 23: animated plexus network background, cool light cone, speed-line burst + lens flare
on the hook, glowing hero word with embers, HUD machine card, glowing editor, sparkles, light-leak +
chromatic split on every cut, grain + vignette.
Content: chai(cheeni=1) machine (no value -> 1 spoon, chai(3) -> 3 spoons), greet(naam="Dost"),
SyntaxError trap (default before non-default), quiz power(3) with n=2 (no reveal).

Usage:  python3 edit31/build_ep24.py [--preview]
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit11"))
sys.path.insert(0, os.path.join(HERE, "..", "brand"))
import build_ep04 as p4   # noqa: E402  EP 04 engine: typewriter, editor + terminal, captions, mascot
import plexus_bg as pb    # noqa: E402

fx, bs, mb, es = p4.fx, p4.bs, p4.mb, p4.es
clamp, ease, pop, paste = p4.clamp, p4.ease, p4.pop, p4.paste
W, H, FPS, SR = p4.W, p4.H, p4.FPS, p4.SR
CAP, MONO = p4.CAP, p4.MONO
WHITE, YEL, GREEN, RED, ORANGE, GREY = p4.WHITE, p4.YEL, p4.GREEN, p4.RED, p4.ORANGE, p4.GREY
CYAN, ICE = (80, 210, 255), (170, 225, 255)
es.NEXT = "EP 25: LAMBDA"

SCENES = [(0.0, "hook"), (3.0, "machine"), (7.5, "param"), (13.5, "error"), (19.5, "quiz")]
ERR_T = 15.6
END0 = 23.0
END_DUR = 3.5
TOTAL = END0 + END_DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP24_Default_Args.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0


def glow(im, col, r=10):
    """p4.glow pads by 3r; crop back so the result stays registered with the input"""
    g = p4.glow(im, col, r)
    p = r * 3
    return g.crop((p, p, p + im.width, p + im.height))


p4.CODE_FS = 42
p4.EDITOR = {
    "param": {
        "code": [[('def greet(naam="Dost"):', 7.7)], [('    print("Namaste", naam)', 8.8)], [("greet()", 10.0)],
                 [('greet("Aman")', 10.5)]],
        "run": 11.2,
        "term": [("$ python main.py", GREY, 11.4, None), ("Namaste Dost", GREEN, 11.7, None),
                 ("Namaste Aman", GREEN, 12.0, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 12.0,
    },
    "error": {
        "code": [[("def bill(tip=10, amount):", 13.7)], [("    return amount + tip", 14.5)]],
        "run": 15.3,
        "term": [("$ python main.py", GREY, 15.45, None), ("SyntaxError: non-default", RED, ERR_T, None),
                 ("argument follows default", RED, ERR_T, None)],
        "wait": (NEVER, NEVER), "enter": NEVER,
    },
}
p4.CAPTIONS = [
    (0.3, "VALUE *NA* DO, PHIR BHI?"), (1.6, "*DEFAULT* VALUE LAGAO!"),
    (3.2, "SOCHO *CHAI* KI CHEENI"), (4.4, "KUCH NA BOLO = *1* CHAMMACH"), (5.8, "*chai(3)* = 3 CHAMMACH!"),
    (7.7, "*=* SE DEFAULT VALUE DO"), (10.0, "*KHAALI* CALL = DEFAULT"), (11.2, "*RUN* KARO"),
    (11.8, "+DOST AUR AMAN!+"),
    (13.7, "DEFAULT *PEHLE* LIKH DIYA?"), (15.3, "*RUN* KARO"), (15.7, "-ERROR!-"),
    (17.0, "DEFAULT HAMESHA *AAKHIR* MEIN!"),
    (19.7, "*QUIZ* TIME!"), (21.3, "OUTPUT KYA AAYEGA?"), (22.2, "*COMMENT* KARO!"),
]
p4.REACT = [(11.8, "Default!", GREEN), (ERR_T + 0.1, "Oops!", RED)]
p4.END0 = END0
p4.ERR_T = ERR_T


# ------------------------------------------------------------------ background + cinematic layers
@lru_cache(None)
def light_cone():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cone = np.exp(-((xx - W / 2) / (150 + 0.5 * yy)) ** 2) * np.exp(-yy / 1100)
    core = np.exp(-(((xx - W / 2) / 240) ** 2 + ((yy + 40) / 240) ** 2))
    a = np.clip(cone * 0.5 + core * 0.9, 0, 1)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = 110, 180, 255
    out[..., 3] = (a * 95).astype(np.uint8)
    return Image.fromarray(out)


@lru_cache(None)
def star4(s):
    im = Image.new("RGBA", (s * 2, s * 2))
    c = s
    ImageDraw.Draw(im).polygon([(c, 0), (c + s * .22, c - s * .22), (2 * s, c), (c + s * .22, c + s * .22), (c, 2 * s),
                                (c - s * .22, c + s * .22), (0, c), (c - s * .22, c - s * .22)], fill=(225, 235, 255, 255))
    return im


def speed_lines(t, strength):
    lay = Image.new("RGBA", (W // 2, H // 2))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(int(t * 12))
    cx, cy = W / 4, 330
    for _ in range(50):
        ang = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(250, 370)
        r1 = r0 + rng.uniform(250, 700)
        pts = [(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)),
               (cx + r1 * math.cos(ang + .012), cy + r1 * math.sin(ang + .012)),
               (cx + r1 * math.cos(ang - .012), cy + r1 * math.sin(ang - .012))]
        d.polygon(pts, fill=(200, 225, 255, int(rng.uniform(70, 170) * strength)))
    return lay.resize((W, H), Image.BILINEAR)


def background(t):
    fr = pb.background(t)
    fr.alpha_composite(light_cone())
    if t < 3.2:
        fr.alpha_composite(speed_lines(t, 1.0 if t < 2.8 else 1 - (t - 2.8) / 0.4))
    rng = np.random.default_rng(23)
    for k in range(6):
        x0, y0, sp = rng.uniform(80, W - 80), rng.uniform(300, H - 200), rng.uniform(6, 14)
        tw = 0.5 + 0.5 * math.sin(t * rng.uniform(1.5, 3) + k)
        paste(fr, star4(int(12 + 8 * tw)), x0, (y0 - t * sp) % (H - 300) + 250, 1, 0.2 + 0.4 * tw)
    return fr


p4.background = background


def energy_glow(layer, t, col=CYAN):
    a = np.asarray(layer.getchannel("A"))
    flick = 0.85 + 0.15 * math.sin(t * 23) * math.sin(t * 7.3)
    out = Image.new("RGBA", layer.size)
    for r, c, k in ((40, (30, 120, 255), 1.0), (18, col, 1.25), (6, (220, 245, 255), 1.0)):
        g = Image.fromarray(a).filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * k * flick)))
        cl = Image.new("RGBA", layer.size, c + (0,))
        cl.putalpha(g)
        out.alpha_composite(cl)
    d = ImageDraw.Draw(out)
    rng = np.random.default_rng(7)
    for _ in range(16):
        x = rng.uniform(220, 860)
        sp = rng.uniform(80, 170)
        y = 870 - ((t * sp + rng.uniform(0, 320)) % 320)
        s = rng.uniform(2.5, 6)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(150, 220, 255, int(220 * (1 - (870 - y) / 320))))
    out.alpha_composite(layer)
    return out


# ------------------------------------------------------------------ scenes
def draw_hook(st, t):
    p4.type_text(st, t, 0.15, "VALUE NA DO?", CAP, 96, WHITE, 540, 560, cps=16)
    lay = Image.new("RGBA", (W, H))
    p4.type_text(lay, t, 0.9, "default", MONO, 180, ICE, 540, 785, cps=9)
    st.alpha_composite(energy_glow(lay, t))
    rb = mb.ribbon([("PHIR BHI CHALEGA!", (20, 20, 20), False)], mb.font(mb.BALOO, 56, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 1000, pop(t - 1.8), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1240, pop(t - 2.1, 0.4))
    if t > 2.4:
        paste(st, mb.bubble("Auto value!", mb.font(mb.BALOO, 46, "ExtraBold"), 22), 450, 1150, pop(t - 2.4, 0.3))


IN_T, OUT_T = 4.3, 5.7


def machine(t):
    im = Image.new("RGBA", (720, 520))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 60, 60, 660, 460
    d.rounded_rectangle((x0, y0, x1, y1), 36, fill=(14, 20, 36, 235))
    edge = Image.new("RGBA", im.size)
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle((x0, y0, x1, y1), 36, outline=(200, 230, 255, 255), width=4)
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ed.line((cx, cy + sy * 24, cx, cy + sy * 80), fill=CYAN + (255,), width=10)
        ed.line((cx + sx * 24, cy, cx + sx * 80, cy), fill=CYAN + (255,), width=10)
    im.alpha_composite(glow(edge, CYAN, 14))
    d = ImageDraw.Draw(im)
    d.text((360, 150), "def chai(cheeni=1)", font=mb.font(MONO, 46), fill=ICE, anchor="mm")
    # rotating gears
    for gx, gy, gr, sp in ((260, 310, 70, 1.6), (430, 330, 52, -2.2)):
        ang = t * sp
        pts = []
        for k in range(24):
            r = gr if k % 2 == 0 else gr * 0.78
            a = ang + k * math.pi / 12
            pts.append((gx + r * math.cos(a), gy + r * math.sin(a)))
        d.polygon(pts, fill=(60, 90, 140))
        d.ellipse((gx - gr * .35, gy - gr * .35, gx + gr * .35, gy + gr * .35), fill=(14, 20, 36))
    d.text((560, 320), "+", font=mb.font(CAP, 90), fill=YEL, anchor="mm")
    return im


def draw_machine(st, t):
    paste(st, machine(t), 540, 880, pop(t - 3.1, 0.35))
    if IN_T <= t < OUT_T:                  # empty call -> default 1 spoon
        paste(st, p4.pill("chai()", CYAN, 50), 540, 410, pop(t - IN_T, 0.3))
        if t >= IN_T + 0.5:
            paste(st, glow(chip_img("cheeni = 1", GREEN, 52), GREEN, 12), 540, 1180, pop(t - IN_T - 0.5, 0.35))
            paste(st, p4.pill("DEFAULT", YEL, 44), 540, 1340, pop(t - IN_T - 0.8, 0.3))
    if t >= OUT_T:                         # chai(3) -> 3 spoons
        paste(st, p4.pill("chai(3)", CYAN, 50), 540, 410, pop(t - OUT_T, 0.3))
        if t >= OUT_T + 0.5:
            paste(st, glow(chip_img("cheeni = 3", ORANGE, 52), ORANGE, 12), 540, 1180, pop(t - OUT_T - 0.5, 0.35))
            paste(st, p4.pill("APNI VALUE", ORANGE, 44), 540, 1340, pop(t - OUT_T - 0.8, 0.3))
            star_burst(st, t, OUT_T + 0.8, 540, 1180)


@lru_cache(None)
def chip_img(txt, col, size=60):
    f = mb.font(MONO, size)
    w = int(f.getlength(txt)) + size + 20
    h = int(size * 1.8)
    im = Image.new("RGBA", (w + 30, h + 30))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + w, 15 + h), h // 3, fill=(16, 22, 36), outline=col, width=6)
    d.text((15 + w / 2, 15 + h / 2 + 2), txt, font=f, fill=WHITE, anchor="mm")
    return glow(im, col, 10)


def star_burst(st, t, t0, cx, cy, col=YEL):
    a = t - t0
    if not 0 <= a < 0.8:
        return
    for k in range(10):
        ang = k * math.pi / 5 + 0.3
        r = 160 * ease(a / 0.6)
        paste(st, glow(star4(int(16 * (1 - a / 0.8)) + 2), col, 6), cx + r * math.cos(ang), cy + r * math.sin(ang),
              1, 1 - a / 0.8)


QUIZ_CODE = [(20.1, "def power(x, n=2):"), (20.6, "    return x ** n"), (21.1, "print(power(3))")]


def draw_quiz(st, t):
    lay = Image.new("RGBA", (W, H))
    p4.type_text(lay, t, 19.6, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    st.alpha_composite(energy_glow(lay, t, (255, 200, 60)) if t < 20.3 else lay)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 66, ICE, 160, 620 + k * 115, cps=22, anchor="lm",
                     cursor=k == len(QUIZ_CODE) - 1)
    if t > 21.6:
        paste(st, p4.pill("9?   3?   ya ERROR?", YEL, 58), 540, 1000, pop(t - 21.6, 0.3))
    if t >= 21.9:
        s_ = 1 + 0.12 * math.sin((t - 21.9) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1180, pop(t - 21.9, 0.3) * s_)


GRID = {"hook": draw_hook, "machine": draw_machine, "quiz": draw_quiz}


# ------------------------------------------------------------------ glossy glowing editor + sparkles
_chrome0 = p4.editor_chrome


@lru_cache(None)
def editor_chrome():
    im = Image.new("RGBA", (W, H))
    edge = Image.new("RGBA", (W, H))
    ImageDraw.Draw(edge).rounded_rectangle((p4.EX0, p4.EY0, p4.EX1, p4.EY1), 26, outline=(80, 170, 255, 255), width=14)
    g = edge.filter(ImageFilter.GaussianBlur(22))
    g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * 1.9))))
    im.alpha_composite(g)
    im.alpha_composite(_chrome0())
    ring = Image.new("RGBA", (W, H))
    ImageDraw.Draw(ring).rounded_rectangle((p4.EX0 - 2, p4.EY0 - 2, p4.EX1 + 2, p4.EY1 + 2), 28,
                                           outline=(170, 220, 255, 255), width=3)
    im.alpha_composite(ring)
    return im


p4.editor_chrome = editor_chrome


def return_highlight(st, t):
    """glowing box around naam="Dost" (the default value) while it is explained"""
    if not 8.0 <= t < 10.6:
        return
    f = mb.font(MONO, p4.CODE_FS)
    x0 = p4.EX0 + 110 + f.getlength("def greet(")
    y = p4.CODE_Y0
    lay = Image.new("RGBA", (W, H))
    ImageDraw.Draw(lay).rounded_rectangle((x0 - 8, y - 46, x0 + f.getlength('naam="Dost"') + 8, y + 12), 10,
                                          outline=CYAN + (255,), width=4)
    al = ease((t - 8.0) / 0.25) * (1 - ease((t - 10.3) / 0.3))
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
    st.alpha_composite(glow(lay, CYAN, 10))


def editor_sparkles(fr, t):
    for cfg in p4.EDITOR.values():
        ok = cfg.get("ok")
        if ok is None or not ok <= t < ok + 1.4:
            continue
        a = t - ok
        rng = np.random.default_rng(int(ok * 10))
        for k in range(10):
            x = rng.uniform(p4.EX0 + 40, p4.EX1 - 40)
            y = rng.uniform(p4.TERM_Y0, p4.EY1 - 40) - 60 * a
            al = max(0.0, 1 - a / 1.4) * (0.6 + 0.4 * math.sin(a * 12 + k))
            paste(fr, glow(star4(int(10 + 12 * rng.random())), YEL, 6), x, y, 1, al)


def editor_focus(t, name):
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


# ------------------------------------------------------------------ frame
def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return SCENES[k]


_end = []


@lru_cache(None)
def leak_mask():
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    return (xx * 4 + yy * 4 * 0.6)


def cinematic(arr, t, s0):
    a = t - s0
    if s0 > 0 and a < 0.45:                       # light-leak sweep across the cut
        pos = -400 + (W + H * 0.6 + 800) * (a / 0.45)
        band = np.exp(-((leak_mask() - pos) / 260.0) ** 2)
        band = cv2.resize(band.astype(np.float32), (W, H))[..., None]
        arr = arr + band * np.array([120, 170, 255], np.float32) * 0.55
    if s0 > 0 and a < 0.2:                        # chromatic split on the punch-in
        k = int(10 * (1 - a / 0.2))
        arr[..., 0] = np.roll(arr[..., 0], k, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -k, axis=1)
    return arr


def lens_flare(fr, t, t0=0.9, cx=540, cy=785):
    a = t - t0
    if not 0 <= a < 0.9:
        return
    k = 1 - a / 0.9
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - 90, cy - 90, cx + 90, cy + 90), fill=(200, 230, 255, int(170 * k)))
    d.rectangle((0, cy - 6, W, cy + 6), fill=(170, 215, 255, int(160 * k)))
    for j, (off, r) in enumerate(((-260, 40), (220, 26), (380, 60))):
        d.ellipse((cx + off - r, cy + off * 0.4 - r, cx + off + r, cy + off * 0.4 + r), fill=(120, 190, 255, int(70 * k)))
    fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))


def frame(i, t=None):
    t = i / FPS if t is None else t
    if t >= END0:
        if not _end:
            es.static_layer = lambda: Image.new("RGBA", (W, H))
            es.mb.wood_frame = lambda *a, **k: None
            _end.append(1)
        fr = p4.background(t).copy()
        fr.alpha_composite(es.frame(min((t - END0) * es.DUR / END_DUR, es.DUR - 0.01)))
        arr = np.asarray(fr.convert("RGB")).astype(np.float32) * p4.vignette()
        arr = cinematic(arr, t, END0)
        return np.clip(arr, 0, 255).astype(np.uint8)
    s0, name = scene_at(t)
    st = Image.new("RGBA", (W, H))
    cy, z = 960, 1.0
    if name in p4.EDITOR:
        p4.draw_editor(st, t, name)
        return_highlight(st, t)
        cy, z = editor_focus(t, name)
    else:
        GRID[name](st, t)
        z = 1.0 + 0.04 * ease((t - s0) / 4)
    a = t - s0
    if s0 > 0 and a < 0.22:
        z *= 1 + 0.12 * (1 - ease(a / 0.22))
    M = cv2.getRotationMatrix2D((W / 2, cy), 0, z)
    M[1, 2] += 860 - cy
    stage = cv2.warpAffine(np.asarray(st), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fr = p4.background(t).copy()
    fr.alpha_composite(Image.fromarray(stage))
    lens_flare(fr, t)
    if name == "error" and t >= ERR_T:
        paste(fr, mb.outlined("ERROR!", mb.font(mb.BALOO, 150, "ExtraBold"), RED, 10, (10, 10, 10), 8,
                              (120, 0, 0)), 540, 1170, pop(t - ERR_T, 0.25), 1, -6)
    editor_sparkles(fr, t)
    p4.draw_mascot(fr, t)
    p4.draw_caption(fr, t)
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 24", (0, 0, 0, 150), 28, YEL)
    fr.alpha_composite(pill_t, (W // 2 - pill_t.width // 2, 140))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    arr = cinematic(arr, t, s0)
    if 0 <= t - ERR_T < 0.3:
        e_ = t - ERR_T
        arr = arr * (1 - 0.35 * (1 - e_ / 0.3)) + np.array([255, 30, 40]) * 0.35 * (1 - e_ / 0.3)
    for ts, amp in ((0.9, 12), (ERR_T, 22)):
        e_ = t - ts
        if 0 <= e_ < 0.3:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.3)), axis=1)
    arr *= p4.vignette()
    arr += cv2.resize(p4.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def shimmer(dur=0.8):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f0 * tt) for f0 in (1568, 1976, 2349, 3136))
    return s * np.sin(np.pi * tt / dur) * 0.07


def gear(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    clicks = (np.sin(2 * np.pi * 18 * tt) > 0.92).astype(float)
    return fx.filt(fx.noise(n, 31) * clicks, "bandpass", [1500, 6000]) * 0.5


def sfx_track():
    buf = np.zeros(int(TOTAL * SR) + SR)
    P = fx.place
    tc = p4.type_clicks
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.35, int(s0 * 10)), s0 - 0.2, 0.6)
    P(buf, fx.whoosh(0.4, 1), 0.0, 0.4)
    tc(buf, 0.15, len("FUNCTION SE"), 16, 1, 0.4)
    P(buf, fx.boom(), 0.9, 0.8)
    P(buf, shimmer(1.0), 0.9, 0.9)
    tc(buf, 0.9, len("return"), 9, 20, 0.45)
    P(buf, fx.pop(), 1.8, 0.55)
    P(buf, fx.pop(), 2.1, 0.5)
    P(buf, fx.pop(), 2.4, 0.5)
    P(buf, fx.whoosh(0.3, 3), 3.1, 0.4)
    P(buf, gear(4.0), 3.3, 0.6)
    for t0 in (IN_T, OUT_T):
        P(buf, fx.pop(), t0, 0.5)
        P(buf, fx.whoosh(0.4, int(t0 * 3)), t0 + 0.2, 0.45)
        P(buf, fx.ding(), t0 + 0.5, 0.5)
        P(buf, fx.pop(), t0 + 0.8, 0.4)
    P(buf, shimmer(0.7), OUT_T + 0.8, 0.8)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_.strip()), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for txt, col, t0, user in cfg["term"]:
            P(buf, bs.note_pop(1300), t0, 0.15)
        if "ok" in cfg:
            P(buf, fx.ding(), cfg["ok"], 0.5)
            P(buf, shimmer(0.6), cfg["ok"], 0.6)
    P(buf, fx.boom(), ERR_T, 0.9)
    P(buf, p4.buzzer(), ERR_T, 0.8)
    P(buf, p4.glitch(), ERR_T + 0.05, 0.7)
    P(buf, fx.whoosh(0.3, 6), 8.0, 0.4)
    P(buf, bs.note_pop(1046.5), 8.05, 0.35)
    P(buf, fx.riser(0.5), 19.1, 0.35)
    P(buf, fx.boom(), 19.6, 0.65)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt.strip()), 22, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 21.6, 0.55)
    P(buf, fx.pop(), 21.9, 0.6)
    P(buf, bs.thud(), 21.9, 0.4)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    end = es.sfx()
    sp = es.DUR / END_DUR
    end = np.interp(np.linspace(0, len(end) - 1, int(len(end) / sp)), np.arange(len(end)), end)
    P(buf, end, END0, 0.9)
    return buf[: int(TOTAL * SR)]


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=ERR_T)
    fx.write_wav(os.path.join(WORK, "music.wav"), music)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track() * 0.8)
    out = os.path.join(WORK, "mix.wav")
    fc = ("[0:a]loudnorm=I=-18:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[sfx];"
          "[mus][sfx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i",
                    os.path.join(WORK, "sfx.wav"), "-filter_complex", fc, "-map", "[out]", "-t", f"{TOTAL:.3f}", out],
                   check=True)
    return out


p4.OUT, p4.WORK, p4.TOTAL = OUT, WORK, TOTAL
p4.frame, p4.build_audio = frame, build_audio

if __name__ == "__main__":
    p4.main()
