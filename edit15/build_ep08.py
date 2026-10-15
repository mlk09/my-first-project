#!/usr/bin/env python3
"""Python ki Pathshala EP 08 - if-else  (1080x1920 Short, works without a voice-over)

Decoded from "Python Basics CONDITIONAL STATEMENTS (if else) in Under a Minute!": if / elif / else
typed live in one continuous take, a white "Warning! indentation" callout, terminal output, light
music bed under the voice.
Text style (from the reference screenshot): every code line sits on its own WHITE LABEL BOX that
wipes in from the left before the text types on; the active branch lights up.
Background: LIGHT NEON COBALT motion grid.
Scenes: traffic-signal analogy with a flat car and signal, the vote-age demo with live condition checks
(False -> else, True -> if), the indentation warning, elif in one shot, quiz, end screen.

Usage:  python3 edit15/build_ep08.py [--preview]
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
ROOT = os.path.join(HERE, "..")
for p in ("brand", "edit", "edit7"):
    sys.path.insert(0, os.path.join(ROOT, p))
_argv, sys.argv = sys.argv, sys.argv[:1]
import build_edit as fx        # noqa: E402
import build_short as bs       # noqa: E402
import make_brand as mb        # noqa: E402
import make_endscreen as es    # noqa: E402
sys.argv = _argv
es.NEXT = "EP 09: ELIF"

OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP08_IfElse.mp4")
WORK = os.path.join(HERE, "work")
W, H, FPS, SR = 1080, 1920, 30, 48000
MONO = bs.MONO
INK = (24, 26, 40)
KW, STRC, NUMC, FNC = (124, 58, 237), (22, 140, 60), (217, 95, 2), (37, 99, 235)
YEL, GREEN, RED, WHITE, COBALT = (255, 214, 10), (40, 200, 110), (240, 60, 70), (255, 255, 255), (70, 140, 255)
HL = (255, 226, 110)

SCENES = [(0.0, "hook"), (3.5, "signal"), (17.0, "vote"), (31.0, "warn"), (37.0, "elif"), (45.5, "quiz")]
END0 = 53.0
TOTAL = END0 + es.DUR


# ------------------------------------------------------------------ helpers
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back(t, s=1.8):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def pop(age, d=0.3):
    return 0.0 if age <= 0 else back(age / d)


def paste(base, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, base.width - x), min(im.height, base.height - y)
    if ex > sx and ey > sy:
        base.alpha_composite(im.crop((sx, sy, ex, ey)), (x + sx, y + sy))


def scene_at(t):
    cur = SCENES[0]
    for s in SCENES:
        if t >= s[0]:
            cur = s
    return cur


# ------------------------------------------------------------------ light neon cobalt motion grid
GRID = 96


@lru_cache(None)
def grid_tile():
    yy, xx = np.mgrid[0:H + GRID, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    base = np.clip(1 - r * 1.1, 0, 1)[..., None] * np.array([10, 22, 70], np.float32) + np.array([4, 7, 22])
    lines = Image.new("L", (W, H + GRID), 0)
    d = ImageDraw.Draw(lines)
    for x in range(0, W + 1, GRID):
        d.line((x, 0, x, H + GRID), fill=255, width=2)
    for y in range(0, H + GRID + 1, GRID):
        d.line((0, y, W, y), fill=255, width=2)
    core = np.asarray(lines).astype(np.float32) / 255
    halo = np.asarray(lines.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255
    neon = (core * 0.55 + halo * 1.6) * (0.35 + 0.65 * np.clip(1 - r * 0.9, 0, 1))
    return base + neon[..., None] * np.array([40, 110, 255], np.float32)      # same as EP 07


def background(t):
    off = int(t * 36) % GRID
    a = grid_tile()[off:off + H].copy()
    yb = (t % 4.0) / 4.0 * (H + 600) - 300
    a += np.exp(-((np.arange(H) - yb) / 140.0) ** 2)[:, None, None] * np.array([20, 45, 120], np.float32) * 0.6
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(4)
    for _ in range(60):
        x, y0, sp, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 60), rng.uniform(1.5, 3.5)
        d.ellipse((x, (y0 - t * sp) % H, x + s, (y0 - t * sp) % H + s), fill=(150, 190, 255, int(rng.uniform(60, 160))))
    return img


# ------------------------------------------------------------------ white label boxes (reference text style)
KEYWORDS = {"if", "elif", "else", "print", "and", "or", "not"}


def colours(line):
    cols, i = [], 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            j = line.find('"', i + 1)
            j = len(line) if j < 0 else j + 1
            cols += [STRC] * (j - i)
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            w = line[i:j]
            c = KW if w in ("if", "elif", "else", "and", "or", "not") else FNC if w in ("print", "ruko", "chalo") else INK
            cols += [c] * (j - i)
            i = j
        elif ch.isdigit():
            cols.append(NUMC)
            i += 1
        else:
            cols.append(INK)
            i += 1
    return cols


def label(st, t, t0, text, x, y, size=54, active=False, flash=0.0, cps=26, fill=None):
    """white box wipes in from the left (0.22 s), then the code types on; returns the box rect"""
    if t < t0:
        return None
    f = mb.font(MONO, size)
    lead = len(text) - len(text.lstrip(" "))
    body = text.lstrip(" ")
    x += f.getlength(" " * lead)
    pad_x, pad_y = 18, int(size * 0.32)
    w = f.getlength(body) + 2 * pad_x
    h = size + 2 * pad_y
    p = ease((t - t0) / 0.22)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.rectangle((x + 7, y - h / 2 + 9, x + 7 + w * p, y + h / 2 + 9), fill=(0, 0, 30, 110))   # hard drop shadow
    col = fill or (HL if active else WHITE)
    if flash > 0:
        col = (255, 255, int(255 - 115 * flash))
    d.rectangle((x, y - h / 2, x + w * p, y + h / 2), fill=col)
    if active:
        d.rectangle((x - 10, y - h / 2, x - 4, y + h / 2), fill=YEL)
    n = 0 if t < t0 + 0.2 else min(len(body), int((t - t0 - 0.2) * cps) + 1)
    cols = colours(body)
    cx = x + pad_x
    for k in range(n):
        d.text((cx, y + 2), body[k], font=f, fill=cols[k], anchor="lm")
        cx += f.getlength(body[k])
    if 0 < n < len(body):
        d.rectangle((cx + 2, y - size * 0.42, cx + 6, y + size * 0.42), fill=INK)
    st.alpha_composite(lay)
    return (x, y - h / 2, x + w, y + h / 2)


def badge(st, t, t0, text, col, x, y, size=46):
    if t < t0:
        return
    f = mb.font(MONO, size)
    w = int(f.getlength(text)) + 50
    im = Image.new("RGBA", (w, int(size * 1.7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, im.height - 3), 16, fill=col)
    d.text((w / 2, im.height / 2 + 1), text, font=f, fill=WHITE, anchor="mm")
    paste(st, im, x + w / 2, y, pop(t - t0, 0.25))


def arrow(st, t, t0, x0, y0, x1, y1, col=YEL, dur=0.3, width=7):
    p = ease((t - t0) / dur)
    if p <= 0:
        return
    d = ImageDraw.Draw(st)
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    d.line((x0, y0, xe, ye), fill=col, width=width)
    if p > 0.7:
        ang = math.atan2(y1 - y0, x1 - x0)
        a1, a2 = ang + 2.6, ang - 2.6
        d.polygon([(xe, ye), (xe + 26 * math.cos(a1), ye + 26 * math.sin(a1)),
                   (xe + 26 * math.cos(a2), ye + 26 * math.sin(a2))], fill=col)


def output_box(st, t, t0, text, y=1180, col=GREEN):
    if t < t0:
        return
    im = Image.new("RGBA", (760, 130))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, 757, 127), 22, fill=(10, 16, 40), outline=col, width=5)
    d.text((34, 66), "Output:", font=mb.font(bs.CAP, 40), fill=(170, 185, 220), anchor="lm")
    d.text((230, 66), text, font=mb.font(MONO, 54), fill=col, anchor="lm")
    paste(st, im, 470, y, pop(t - t0, 0.3))


# ------------------------------------------------------------------ flat road scene (traffic analogy)
CARD = (60, 860, 1020, 1480)


@lru_cache(None)
def road_card():
    x0, y0, x1, y1 = CARD
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGBA", (w, h))
    sky = np.linspace(0, 1, int(h * 0.55))[:, None]
    top, bot = np.array([110, 190, 250]), np.array([185, 228, 255])
    skyarr = (top * (1 - sky[..., None]) + bot * sky[..., None]).astype(np.uint8)
    skyimg = Image.fromarray(np.repeat(skyarr, w, axis=1)).convert("RGBA")
    im.paste(skyimg, (0, 0))
    d = ImageDraw.Draw(im)
    gy = int(h * 0.55)
    for cx, r, c in ((120, 70, (60, 140, 60)), (230, 50, (70, 160, 70)), (820, 60, (60, 140, 60))):
        d.ellipse((cx - r, gy - r * 0.8, cx + r, gy + r * 0.8), fill=c)
    d.rectangle((0, gy, w, gy + 50), fill=(140, 170, 40))
    d.rectangle((0, gy + 50, w, gy + 62), fill=(225, 215, 160))
    d.rectangle((0, gy + 62, w, h), fill=(120, 116, 112))
    for x in range(20, w, 170):
        d.rectangle((x, gy + 190, x + 100, gy + 202), fill=(235, 235, 235))
    d.rectangle((560, gy + 62, 572, gy + 110), fill=(250, 250, 250))       # stop line hint
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=255)
    im.putalpha(mask)
    return im


def draw_light(d, ox, oy, state, t):
    pole_x = ox + 640
    gy = oy + int((CARD[3] - CARD[1]) * 0.55)
    d.rectangle((pole_x - 8, oy + 150, pole_x + 8, gy + 90), fill=(55, 65, 85))
    d.rounded_rectangle((pole_x - 50, oy + 40, pole_x + 50, oy + 230), 14, fill=(50, 60, 80))
    for k, (cy, on_col, off_col) in enumerate(((oy + 90, (245, 70, 70), (110, 50, 55)),
                                               (oy + 180, (70, 230, 120), (45, 95, 70)))):
        on = (state == "red" and k == 0) or (state == "green" and k == 1)
        if on:
            g = 10 + 4 * math.sin(t * 10)
            d.ellipse((pole_x - 36 - g, cy - 36 - g, pole_x + 36 + g, cy + 36 + g), fill=on_col[:3] + (70,))
        d.ellipse((pole_x - 34, cy - 34, pole_x + 34, cy + 34), fill=on_col if on else off_col)


def draw_cycle(lay, x, y, spin):
    """flat cyclist: two spoked wheels, frame, pedalling rider (spin = wheel angle)"""
    d = ImageDraw.Draw(lay)
    gy = y + 82                                    # ground line
    rw = 46
    rear, front = (x + 52, gy - rw), (x + 214, gy - rw)
    crank = (x + 128, gy - rw)
    d.ellipse((x + 10, gy - 6, x + 260, gy + 10), fill=(0, 0, 0, 60))
    for cx, cy in (rear, front):                    # wheels
        d.ellipse((cx - rw, cy - rw, cx + rw, cy + rw), outline=(35, 35, 45), width=9)
        for k in range(6):
            a = spin + k * math.pi / 3
            d.line((cx, cy, cx + (rw - 6) * math.cos(a), cy + (rw - 6) * math.sin(a)), fill=(150, 155, 165), width=3)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(70, 70, 80))
    seat, head_t = (x + 108, gy - 128), (x + 196, gy - 120)
    frame = (0, 170, 200)
    for a_, b_ in ((rear, crank), (crank, seat), (seat, rear), (seat, head_t), (crank, head_t), (head_t, front)):
        d.line((a_, b_), fill=frame, width=10)
    d.rounded_rectangle((seat[0] - 26, seat[1] - 10, seat[0] + 18, seat[1] + 2), 5, fill=(40, 40, 50))
    bar = (head_t[0] + 6, head_t[1] - 22)
    d.line((head_t, bar), fill=(40, 40, 50), width=7)
    d.line((bar[0] - 18, bar[1], bar[0] + 10, bar[1]), fill=(40, 40, 50), width=8)
    # rider
    hip = (seat[0] - 2, seat[1] - 14)
    sh = (x + 168, gy - 214)
    for side, ph in ((0, 0.0), (1, math.pi)):       # legs pedalling (back leg drawn darker)
        pa = spin * 1.6 + ph
        foot = (crank[0] + 24 * math.cos(pa), crank[1] + 24 * math.sin(pa))
        knee = ((hip[0] + foot[0]) / 2 + 26, (hip[1] + foot[1]) / 2 - 22)
        col = (40, 60, 120) if side else (60, 90, 170)
        d.line((hip, knee, foot), fill=col, width=16, joint="curve")
        d.line((foot[0] - 14, foot[1], foot[0] + 14, foot[1]), fill=(30, 30, 30), width=8)
    d.line((hip, sh), fill=(255, 190, 40), width=30)               # shirt
    d.line((sh, (bar[0] - 8, bar[1])), fill=(240, 200, 160), width=11)   # arm
    d.line((sh, (sh[0] + 8, sh[1] - 14)), fill=(240, 200, 160), width=12)                     # neck
    d.ellipse((sh[0] - 10, sh[1] - 56, sh[0] + 36, sh[1] - 10), fill=(240, 200, 160))        # head
    d.chord((sh[0] - 14, sh[1] - 64, sh[0] + 40, sh[1] - 16), 180, 360, fill=(230, 60, 60))  # helmet



SIG = dict(card=6.5, car_in=7.0, stop=9.0, green=11.8, go=12.4, off=14.6)


def car_x(t):
    s = SIG
    if t < s["car_in"]:
        return -300
    if t < s["stop"]:
        return -300 + (330 - -300) * (1 - (1 - (t - s["car_in"]) / (s["stop"] - s["car_in"])) ** 3)
    if t < s["go"]:
        return 330
    q = (t - s["go"]) / (s["off"] - s["go"])
    return 330 + 950 * q * q


def draw_signal_scene(st, t):
    lines = [(3.8, 'if signal == "laal":'), (4.6, "    ruko()"), (5.4, "else:"), (6.2, "    chalo()")]
    red = t < SIG["green"]
    act = {0: red and t >= SIG["stop"], 1: red and t >= SIG["stop"], 2: not red, 3: not red}
    for k, (t0, txt) in enumerate(lines):
        label(st, t, t0, txt, 120, 380 + k * 100, 56, active=act[k])
    if t >= SIG["card"]:
        q = ease((t - SIG["card"]) / 0.45)
        x0, y0, x1, y1 = CARD
        card = road_card().copy()
        cd = ImageDraw.Draw(card)
        draw_light(cd, 0, 0, "red" if red else "green", t)
        gy = int((y1 - y0) * 0.55)
        draw_cycle(card, car_x(t), gy + 105, car_x(t) / 48)
        sh = Image.new("RGBA", (W, H))
        ImageDraw.Draw(sh).rounded_rectangle((x0 + 8, y0 + 18, x1 + 8, y1 + 18), 34, fill=(0, 0, 30, 120))
        st.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        paste(st, card, (x0 + x1) / 2, (y0 + y1) / 2 + 220 * (1 - q), 0.92 + 0.08 * q, q)


# ------------------------------------------------------------------ other scenes
def draw_vote(st, t):
    age_txt = "age = 16" if t < 24.0 else "age = 20"
    t_age = 17.3 if t < 24.0 else 24.0
    flash = clamp(1 - (t - 24.0) / 0.4) if 24.0 <= t < 24.4 else 0
    first = t < 24.0
    lines = [(t_age, age_txt), (17.9, "if age >= 18:"), (18.5, '    print("Vote do!")'), (19.1, "else:"),
             (19.7, '    print("Abhi nahi")')]
    act = [False, not first and t >= 25.6, not first and t >= 25.6, first and t >= 21.2, first and t >= 21.2]
    for k, (t0, txt) in enumerate(lines):
        label(st, t, t0, txt, 120, 360 + k * 95, 52, active=act[k], flash=flash if k == 0 else 0)
    if first:
        label(st, t, 20.6, "16 >= 18", 140, 900, 52, fill=(235, 240, 255))
        arrow(st, t, 20.85, 470, 900, 600, 900)
        badge(st, t, 21.0, "False", RED, 630, 900)
        output_box(st, t, 21.8, "Abhi nahi", 1120, (255, 140, 120))
    else:
        label(st, t, 25.0, "20 >= 18", 140, 900, 52, fill=(235, 240, 255))
        arrow(st, t, 25.25, 470, 900, 600, 900)
        badge(st, t, 25.4, "True", GREEN, 630, 900)
        output_box(st, t, 26.2, "Vote do!", 1120)
        sparkles(st, t, 26.3, 470, 1120)


def sparkles(st, t, t0, cx, cy):
    a = t - t0
    if not 0 <= a < 1.2:
        return
    d = ImageDraw.Draw(st)
    r = np.random.default_rng(int(t0 * 10))
    for k in range(10):
        x, y = cx + r.uniform(-360, 360), cy + r.uniform(-90, 90)
        q = back(clamp((a - 0.05 * k) / 0.25)) * (1 - ease((a - 0.8) / 0.4))
        if q <= 0:
            continue
        s = r.uniform(18, 34) * q
        d.polygon([(x + (s if j % 2 == 0 else s * .3) * math.cos(-math.pi / 2 + j * math.pi / 4 + a * 3),
                    y + (s if j % 2 == 0 else s * .3) * math.sin(-math.pi / 2 + j * math.pi / 4 + a * 3))
                   for j in range(8)], fill=(255, 236, 140, 255))


def draw_warn(st, t):
    r1 = label(st, t, 31.3, "if age >= 18:", 120, 480, 60)
    r2 = label(st, t, 31.8, '    print("Vote do!")', 120, 590, 60)
    d = ImageDraw.Draw(st)
    if t >= 33.3 and r1:      # ring around the colon
        p = clamp((t - 33.3) / 0.3)
        x = r1[2] - 34
        d.arc((x - 30, 480 - 36, x + 30, 480 + 30), -90, -90 + 360 * p, fill=RED, width=7)
    if t >= 33.8 and r2:      # indent bracket
        p = ease((t - 33.8) / 0.3)
        f = mb.font(MONO, 60)
        x0, x1 = 120, 120 + f.getlength("    ")
        yb = 650
        d.line((x0, yb, x0 + (x1 - x0) * p, yb), fill=RED, width=7)
        d.line((x0, yb - 18, x0, yb), fill=RED, width=7)
        if p > 0.9:
            d.line((x1, yb - 18, x1, yb), fill=RED, width=7)
            d.text(((x0 + x1) / 2, yb + 34), "4 space", font=mb.font(bs.CAP, 34), fill=WHITE, anchor="mm",
                   stroke_width=4, stroke_fill=(0, 0, 0))
    if t >= 32.6:      # warning callout (white box, yellow triangle - like the reference, our words)
        a = t - 32.6
        im = Image.new("RGBA", (900, 300))
        cd = ImageDraw.Draw(im)
        cd.rectangle((0, 0, 899, 299), fill=WHITE)
        cd.rectangle((0, 0, 899, 12), fill=YEL)
        cd.polygon([(110, 70), (190, 215), (30, 215)], fill=YEL)
        cd.text((110, 175), "!", font=mb.font(bs.CAP, 90), fill=INK, anchor="mm")
        cd.text((230, 90), "DHYAN DO!", font=mb.font(bs.CAP, 64), fill=RED, anchor="lm")
        cd.text((230, 170), "Line ke end mein  :  (colon)", font=mb.font(bs.CAP, 36), fill=INK, anchor="lm")
        cd.text((230, 225), "aur andar 4 space ka gap!", font=mb.font(bs.CAP, 36), fill=INK, anchor="lm")
        shake = 10 * math.sin(a * 50) * math.exp(-a * 6)
        paste(st, im, 540 + shake, 940, pop(a, 0.3))


def draw_elif(st, t):
    lines = ["marks = 75", "if marks >= 90:", '    print("A")', "elif marks >= 60:", '    print("B")', "else:",
             '    print("C")']
    act = {4: t >= 41.8, 3: t >= 41.4}
    for k, txt in enumerate(lines):
        label(st, t, 37.3 + 0.45 * k, txt, 120, 340 + k * 84, 48, active=act.get(k, False))
    badge(st, t, 40.6, "False", RED, 640, 340 + 1 * 84)
    badge(st, t, 41.4, "True", GREEN, 700, 340 + 3 * 84)
    output_box(st, t, 42.2, "B", 1060)


OPTIONS = [(48.0, "A", "Even"), (48.3, "B", "Odd"), (48.6, "C", "Error")]
COUNT0, REVEAL = 49.0, 52.0


def draw_quiz(st, t):
    a = t - 45.6
    if a >= 0:
        s = 1 + 1.3 * (1 - ease(a / 0.18)) if a < 0.18 else 1
        paste(st, mb.outlined("QUIZ TIME!", mb.font(mb.BALOO, 130, "ExtraBold"), YEL, 10, (10, 10, 30), 8,
                              (150, 95, 0)), 540, 290, s, clamp(a / 0.06), -4)
    for k, txt in enumerate(["x = 7", "if x % 2 == 0:", '    print("Even")', "else:", '    print("Odd")']):
        label(st, t, 46.2 + 0.35 * k, txt, 120, 460 + k * 84, 48, active=(t >= REVEAL and k >= 3))
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == "B")
        fill = WHITE if state is None else ((200, 255, 215) if state else (255, 210, 210))
        r = label(st, t, t0, f"{letter})  {txt}", 260, 960 + k * 110, 52, fill=fill)
        if state is not None and r:
            paste(st, bs.icon_check(64, state), r[2] + 50, 960 + k * 110, pop(t - REVEAL, 0.25))
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (220 * S, 220 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 210 * S, 210 * S), outline=(40, 60, 120), width=14 * S, fill=(10, 16, 40))
        d.arc((10 * S, 10 * S, 210 * S, 210 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)), fill=YEL,
              width=14 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((110 * S, 112 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 110 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        paste(st, im.resize((220, 220), Image.LANCZOS), 540, 1400,
              1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8) * (t < REVEAL))


HOOK_CHIPS = [(1.0, "if", 200, 1180), (1.15, "else:", 470, 1290), (1.3, "elif", 230, 1420), (1.45, ">= 18", 480, 1530)]


def draw_hook(st, t):
    label(st, t, 0.1, "PYTHON", 300, 520, 96, cps=30)
    label(st, t, 0.45, "IF - ELSE", 230, 670, 120, active=True, cps=30)
    if t > 0.9:
        rb = mb.ribbon([("CODE KO DECISION SIKHAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 54, "ExtraBold"),
                       98, 32, fill=(255, 90, 95))
        paste(st, rb, 540, 860, pop(t - 0.9), 1, 2)
    for t0, txt, x, y in HOOK_CHIPS:
        if t >= t0:
            label(st, t, t0, txt, x - 80, y + 8 * math.sin(t * 4 + x), 60, cps=40)
    if "mh" not in _C:
        _C["mh"] = mb.mascot(430)
    paste(st, _C["mh"], 840, 1340, pop(t - 1.0, 0.4))


_C = {}
REACT = [(9.2, "Laal hai = RUKO!", RED), (12.2, "Hara = CHALO!", GREEN), (21.3, "16 < 18 = else!", RED),
         (26.4, "Ab vote kar sakte ho!", GREEN), (34.0, "Yeh bhoolna mat!", RED), (42.4, "elif = doosra mauka!", GREEN),
         (52.05, "7 odd hai!", GREEN)]
MASCOT_POS = {"signal": (930, 640, 230), "vote": (930, 1450, 280), "warn": (930, 1450, 280),
              "elif": (930, 1450, 280), "quiz": (930, 1480, 260)}


def draw_mascot(fr, t, name):
    if name not in MASCOT_POS:
        return
    x, y, hgt = MASCOT_POS[name]
    key = f"m{hgt}"
    if key not in _C:
        _C[key] = mb.mascot(hgt)
    s0 = [s for s, n in SCENES if n == name][0]
    s = pop(t - s0 - 0.6, 0.4)
    react = None
    for tr, txt, col in REACT:
        if 0 <= t - tr < 1.8:
            react = (tr, txt, col)
    bob, rot = 8 * math.sin(t * 3), 0
    if react:
        a = t - react[0]
        if react[2] == GREEN:
            bob -= 30 * abs(math.sin(a * 10)) * math.exp(-a * 5)
        else:
            rot = 10 * math.sin(a * 25) * math.exp(-a * 5)
    paste(fr, _C[key], x, y + bob, s, 1, rot)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 44, "ExtraBold"), 20)
        by = y + hgt / 2 + 20 if name == "signal" else y - hgt / 2 - 70
        paste(fr, b, min(1060 - b.width / 2, max(b.width / 2 + 20, x - 60)), by,
              pop(a, 0.22) * (1 - ease((a - 1.6) / 0.2)))


# ------------------------------------------------------------------ frame
GRAIN = [np.random.default_rng(s).normal(0, 3, (H // 2, W // 2)).astype(np.float32) for s in range(5)]


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.3 * r ** 2.4, 0.6, 1)[..., None]


@lru_cache(None)
def hud():
    p = Image.new("RGBA", (560, 64))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, 559, 63), 32, fill=(5, 10, 40, 170), outline=(120, 170, 255, 160), width=2)
    d.text((280, 33), "PYTHON KI PATHSHALA  •  EP 08", font=mb.font(bs.CAP, 28), fill=YEL, anchor="mm")
    return p


def frame(i):
    t = i / FPS
    if t >= END0:
        return np.asarray(es.frame(t - END0).convert("RGB"))
    s0, name = scene_at(t)
    st = Image.new("RGBA", (W, H))
    {"hook": draw_hook, "signal": draw_signal_scene, "vote": draw_vote, "warn": draw_warn, "elif": draw_elif,
     "quiz": draw_quiz}[name](st, t)
    a = t - s0
    fr = background(t)
    # scene entrance: slide up + settle (the old scene wipes out under a white flash)
    dy = int(140 * (1 - ease(a / 0.35))) if s0 > 0 else 0
    fr.alpha_composite(st, (0, dy)) if dy == 0 else fr.alpha_composite(st.crop((0, 0, W, H - dy)), (0, dy))
    draw_mascot(fr, t, name)
    fr.alpha_composite(hud(), (W // 2 - 280, 130))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    if s0 > 0 and a < 0.15:
        arr += (255 - arr) * 0.35 * (1 - a / 0.15)
    for ts, amp0 in ((32.6, 14), (21.0, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.3:
            arr = np.roll(arr, int(amp0 * math.sin(e_ * 80) * (1 - e_ / 0.3)), axis=1)
    arr *= vignette()
    arr += cv2.resize(GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def chain(dur, faster=False):
    """free-wheel / chain ticking of a bicycle"""
    n = int(dur * SR)
    out = np.zeros(n)
    t, k = 0.0, 0
    while t < dur:
        tick = fx.filt(fx.noise(int(0.012 * SR), k), "bandpass", [2500, 8000]) * fx.env_exp(int(0.012 * SR), 300)
        fx.place(out, tick * 0.5, t, 1)
        rate = 9 + (14 * t / dur if faster else 0)
        t += 1 / rate
        k += 1
    return out


def bell():
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    ring = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * dcy) for f, dcy in ((2350, 5), (3480, 7), (4700, 9)))
    trill = 1 + 0.35 * np.sin(2 * np.pi * 22 * tt)
    out = ring * trill * 0.22
    out[int(0.18 * SR):] += (ring * trill * 0.18)[: n - int(0.18 * SR)]
    return out


def engine(dur, rev_up=True):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 55 + (40 * tt / dur if rev_up else 0)
    x = fx.signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * tt))
    return fx.filt(x, "lowpass", 700, 2) * np.minimum(1, tt / 0.1) * np.minimum(1, (dur - tt) / 0.2) * 0.5


def brake():
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    f = 1900 - 500 * tt
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4) * 0.12 + fx.filt(fx.noise(n, 3), "bandpass",
                                                                                     [2000, 6000]) * np.exp(-tt * 6) * 0.1


def horn():
    n = int(0.36 * SR)
    tt = np.arange(n) / SR
    gate = ((tt < 0.13) | (tt > 0.2)).astype(float)
    x = np.sign(np.sin(2 * np.pi * 420 * tt)) + np.sign(np.sin(2 * np.pi * 530 * tt))
    return fx.filt(x, "lowpass", 2200, 2) * gate * 0.18


def box_swish(seed):
    n = int(0.16 * SR)
    tt = np.linspace(0, 1, n)
    return fx.filt(fx.noise(n, seed), "bandpass", [1500, 7000]) * np.sin(np.pi * tt) ** 2 * 0.35


def sfx_label(buf, t0, text, cps=26, seed=0, gain=0.3):
    fx.place(buf, box_swish(seed), t0, 0.8)
    body = text.lstrip(" ")
    for k in range(len(body)):
        if body[k] != " ":
            fx.place(buf, bs.key_click(seed + k), t0 + 0.2 + k / cps, gain)


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.05, 0.7)
    sfx_label(buf, 0.1, "PYTHON", 30, 1)
    sfx_label(buf, 0.45, "IF - ELSE", 30, 2)
    P(buf, fx.pop(), 0.9, 0.6)
    for k, (t0, txt, *_r) in enumerate(HOOK_CHIPS):
        sfx_label(buf, t0, txt, 40, 10 + k, 0.2)
    for s0, n in SCENES[1:]:
        P(buf, fx.whoosh(0.35, int(s0 * 10)), s0 - 0.2, 0.55)
    # signal scene
    for k, (t0, txt) in enumerate([(3.8, 'if signal == "laal":'), (4.6, "    ruko()"), (5.4, "else:"), (6.2, "    chalo()")]):
        sfx_label(buf, t0, txt, 26, 20 + k)
    P(buf, fx.whoosh(0.4, 7), SIG["card"], 0.5)
    P(buf, chain(SIG["stop"] - SIG["car_in"]), SIG["car_in"], 0.8)
    P(buf, brake(), SIG["stop"] - 0.35, 1.0)
    P(buf, fx.ding(), SIG["green"], 0.6)
    P(buf, bell(), SIG["go"] - 0.2, 0.9)
    P(buf, chain(SIG["off"] - SIG["go"], True), SIG["go"], 0.8)
    # vote
    for k, (t0, txt) in enumerate([(17.3, "age = 16"), (17.9, "if age >= 18:"), (18.5, 'print("Vote do!")'),
                                   (19.1, "else:"), (19.7, 'print("Abhi nahi")'), (20.6, "16 >= 18"), (24.0, "age = 20"),
                                   (25.0, "20 >= 18")]):
        sfx_label(buf, t0, txt, 26, 40 + k)
    P(buf, e_buzz(), 21.0, 0.7)
    P(buf, fx.pop(), 21.8, 0.5)
    P(buf, fx.ding(), 25.4, 0.55)
    P(buf, fx.pop(), 26.2, 0.5)
    P(buf, bs.note_pop(1046.5), 26.3, 0.4)
    # warn
    sfx_label(buf, 31.3, "if age >= 18:", 26, 60)
    sfx_label(buf, 31.8, 'print("Vote do!")', 26, 61)
    P(buf, fx.boom(), 32.6, 0.6)
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    P(buf, np.sin(2 * np.pi * 880 * tt) * ((tt % 0.3) < 0.14) * 0.3, 32.65, 1)
    P(buf, fx.pop(), 33.3, 0.5)
    P(buf, fx.pop(), 33.8, 0.5)
    # elif
    for k, txt in enumerate(["marks = 75", "if marks >= 90:", 'print("A")', "elif marks >= 60:", 'print("B")', "else:",
                             'print("C")']):
        sfx_label(buf, 37.3 + 0.45 * k, txt, 26, 70 + k, 0.22)
    P(buf, e_buzz()[: int(0.2 * SR)], 40.6, 0.6)
    P(buf, fx.ding(), 41.4, 0.5)
    P(buf, fx.pop(), 42.2, 0.5)
    # quiz
    P(buf, fx.riser(0.6), 45.0, 0.35)
    P(buf, fx.boom(), 45.6, 0.8)
    for k in range(5):
        P(buf, box_swish(90 + k), 46.2 + 0.35 * k, 0.7)
    for t0, *_r in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    tt = COUNT0
    while tt < REVEAL - 0.05:
        n2 = int(0.05 * SR)
        x = np.arange(n2) / SR
        P(buf, np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 90) * 0.5, tt, 0.6)
        tt += 0.5
    P(buf, fx.ding(), REVEAL, 0.7)
    P(buf, bs.note_pop(1318.5), REVEAL + 0.05, 0.4)
    for tr, txt, col in REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def e_buzz():
    n = int(0.4 * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 150 * tt)) + 0.5 * np.sign(np.sin(2 * np.pi * 112 * tt))
    return fx.filt(x, "lowpass", 1500, 2) * np.minimum(1, (0.4 - tt) / 0.06) * 0.28


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=32.6)
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


def main():
    preview = "--preview" in sys.argv
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    mix = build_audio()
    out = OUT if not preview else os.path.join(HERE, "output", "preview.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", mix, "-c:v", "libx264",
                            "-preset", "veryfast" if preview else "slow", "-crf", "28" if preview else "20",
                            "-maxrate", "7M", "-bufsize", "14M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    step = 3 if preview else 1
    for i in range(0, n, step):
        fb = frame(i).tobytes()
        for _ in range(step):
            enc.stdin.write(fb)
        if i % 150 == 0:
            print(f"  {i / FPS:.1f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
