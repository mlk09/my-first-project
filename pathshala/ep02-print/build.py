#!/usr/bin/env python3
"""Renders Python Ki Pathshala EP02 "print() — pehla code" (≈25 s, 9:16).

Style decoded from the "Python Variables + 3 Golden Rules" reference short and
re-themed light: a whiteboard instead of a chalkboard, dark marker text with
red / blue / green keywords and an animated yellow highlighter, handwritten
headings that type on character by character, code written on the board,
hand-drawn arrows that label the parts of the code, a mascot (a snake in a
graduation cap) in the corner that reacts in speech bubbles, a duster that
wipes the board between topics, a green "Output" box with a tick, a
challenge with a 3-2-1 countdown ring, and a framed end board where a cursor
taps LIKE -> LIKED, SHARE and SUBSCRIBE -> SUBSCRIBED.

Everything is drawn procedurally; the music and SFX are synthesised; the
voice comes from make_voice.py. Two versions are written: with voice-over and
music + SFX only.

Run:   python3 pathshala/ep02-print/make_voice.py --models <dir>
       python3 pathshala/ep02-print/build.py [--preview]
Needs: pip install numpy scipy opencv-python-headless pillow soundfile ; ffmpeg.
"""
import argparse
import math
import os
import subprocess
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
WORK = os.path.join(HERE, "work")
FONTS = os.path.join(HERE, "..", "assets", "fonts")
HAND = os.path.join(FONTS, "Kalam-Bold.ttf")
MONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
NAME = "PythonKiPathshala-EP02-print"

W, H, FPS = 1080, 1920, 30
SR = 48000

# ---------------------------------------------------------------- timeline (voice-driven)
VO_AT = {"hook1": 0.15, "hook2": 2.20, "code": 4.75, "explain": 9.10, "output": 13.85,
         "chal1": 17.00, "chal2": 21.25}
DUR = 25.3
SCENES = [("title", 0.0), ("code", 4.6), ("explain", 9.0), ("output", 13.75), ("chal", 16.9), ("end", 21.1)]
CUTS = [s for _, s in SCENES] + [DUR]
WIPE = 0.42                         # duster wipe length, ends on the cut
WIPE_CUTS = [1, 4]                  # title->code, output->challenge
PUNCH_CUTS = [3]                    # explain->output: zoom punch + flash
ZOOM_CUTS = [5]                     # challenge->end: zoom into the framed board

# ---------------------------------------------------------------- palette (light board, dark marker)
BOARD = (248, 247, 242)
INK = (22, 32, 68)                  # navy marker
RED = (214, 40, 52)
BLUE = (28, 92, 210)
GREEN = (24, 140, 70)
ORANGE = (240, 130, 20)
YELLOW = (255, 214, 40)
HILITE = (255, 226, 70)
GRAY = (130, 136, 150)
WHITE = (255, 255, 255)
SNAKE = (96, 186, 72)
SNAKE_D = (36, 104, 44)
WOOD = (176, 118, 64)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def pop(age, dur=0.3, over=0.15):
    if age < 0:
        return 0.0
    x = clamp(age / dur)
    if x >= 1:
        return 1.0
    return 1 + (over * math.sin(math.pi * x) - (1 - x) ** 2.4) if x > 0 else 0.0


def back_out(x, s=2.2):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return SCENES[i][0], t - CUTS[i], i
    return SCENES[-1][0], t - CUTS[-2], len(SCENES) - 1


# ---------------------------------------------------------------- drawing helpers
@lru_cache(None)
def font(size, which="hand"):
    return ImageFont.truetype({"hand": HAND, "mont": MONT, "mono": MONO}[which], size)


def ss(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def with_shadow(im, blur=12, offset=(0, 8), alpha=60, pad=30):
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, INK + (0,))
    sh.putalpha(im.getchannel("A").point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def paste(L, spr, cx, cy, s=1.0, a=1.0, rot=0.0, anchor="c"):
    if a <= 0.01 or s <= 0.01:
        return
    im = spr
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point([int(v * a) for v in range(256)]))
    if anchor == "c":
        x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    else:                                    # "lt": top-left
        x, y = int(cx), int(cy)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(L.width, x + im.width), min(L.height, y + im.height)
    if x1 > x0 and y1 > y0:
        L.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


@lru_cache(None)
def text(s, size, color=INK, which="hand", stroke=0, stroke_col=WHITE):
    f = font(size, which)
    x0, y0, x1, y1 = f.getbbox(s, stroke_width=stroke)
    im = Image.new("RGBA", (max(1, x1 - x0 + 10), max(1, y1 - y0 + 10)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((5 - x0, 5 - y0), s, font=f, fill=color + (255,), stroke_width=stroke,
                            stroke_fill=stroke_col + (255,))
    return im


@lru_cache(None)
def pill(s, size, fg=WHITE, bg=RED, padx=30, pady=14, which="mont", border=None, shadow=True):
    t = text(s, size, fg, which)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=bg + (255,),
                                         outline=(border + (255,)) if border else None, width=6 if border else 0)
    im = ss(im, w, h)
    im.alpha_composite(t, (padx, pady))
    return with_shadow(im) if shadow else im


# ---------- handwritten typewriter lines: segments of (text, colour, highlighter?)
def seg_len(segs):
    return sum(len(s) for s, _, _ in segs)


@lru_cache(None)
def hand_line(segs, n, size=70, hl_u=1.0):
    """First n characters of a handwritten line; highlighted segments get a yellow marker swipe."""
    f = font(size)
    total_w = int(sum(f.getlength(s) for s, _, _ in segs)) + 40
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (total_w, asc + desc + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, left = 10, n
    for s, col, hl in segs:
        part = s[:max(0, left)]
        wfull = f.getlength(s)
        if hl and len(part) == len(s) and hl_u > 0:
            # highlighter swipe behind the finished word
            hw = wfull * hl_u
            d.polygon([(x - 6, asc * 0.42 + 12), (x + hw + 6, asc * 0.36 + 12),
                       (x + hw + 4, asc + desc * 0.4 + 12), (x - 8, asc + desc * 0.5 + 12)], fill=HILITE + (190,))
        if part:
            d.text((x, 10), part, font=f, fill=col + (255,))
        x += wfull
        left -= len(s)
    return im


def type_n(t, t0, cps=24.0):
    return int(max(0.0, t - t0) * cps)


def draw_line(L, segs, x, y, t, t0, size=70, cps=24.0, hl_delay=0.15):
    n = type_n(t, t0, cps)
    if n <= 0:
        return 0
    n = min(n, seg_len(segs))
    done_at = t0 + seg_len(segs) / cps
    hl_u = round(ease((t - done_at - hl_delay) / 0.25), 2) if n >= seg_len(segs) else 0.0
    L.alpha_composite(hand_line(segs, n, size, hl_u), (int(x), int(y)))
    return n


# ---------- code on the board
P_FN, P_PAR, P_STR = BLUE, INK, GREEN


@lru_cache(None)
def code_img(tokens, n, size=64):
    f = font(size, "mono")
    w = int(sum(f.getlength(s) for s, _ in tokens)) + 30
    im = Image.new("RGBA", (w, size + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, left = 6, n
    for s, col in tokens:
        part = s[:max(0, left)]
        if part:
            d.text((x, 8), part, font=f, fill=col + (255,))
        x += f.getlength(s)
        left -= len(s)
    return im


def code_x_of(tokens, upto_char, size=64):
    """x offset (px) of a character index inside a code line."""
    f = font(size, "mono")
    s = "".join(t for t, _ in tokens)
    return 6 + f.getlength(s[:upto_char])


# ---------- hand-drawn shapes
def bez(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def marker_arrow(L, p0, p1, u, col=INK, w=7, bend=60):
    """Curved arrow drawn progressively (u 0..1) with an arrowhead at the end."""
    if u <= 0:
        return
    p0, p1 = np.array(p0, float), np.array(p1, float)
    mid = (p0 + p1) / 2
    nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]])
    nrm = nrm / (np.linalg.norm(nrm) + 1e-9) * bend
    pts = bez(p0, mid + nrm, mid + nrm * 0.6, p1)
    k = max(2, int(len(pts) * clamp(u)))
    d = ImageDraw.Draw(L)
    d.line([tuple(p) for p in pts[:k]], fill=col + (255,), width=w, joint="curve")
    if u >= 1:
        a = pts[-1] - pts[-4]
        a = a / (np.linalg.norm(a) + 1e-9)
        b = np.array([-a[1], a[0]])
        tip = pts[-1]
        d.polygon([tuple(tip), tuple(tip - a * 30 + b * 16), tuple(tip - a * 30 - b * 16)], fill=col + (255,))


def marker_rect(L, box, u, col=INK, w=6, r=24, fill=None):
    """Rounded box whose outline is drawn progressively."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(L)
    if fill and u > 0:
        d.rounded_rectangle(box, r, fill=fill + (int(255 * ease(u)),))
    per = 2 * ((x1 - x0) + (y1 - y0))
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    left = per * clamp(u)
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if left <= 0:
            break
        f = min(1, left / seg)
        d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=col + (255,), width=w)
        left -= seg
    if u >= 1:
        d.rounded_rectangle(box, r, outline=col + (255,), width=w)


@lru_cache(None)
def tick_badge(r=46, ok=True):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=(GREEN if ok else RED) + (255,))
    w = int(D * 0.1)
    if ok:
        d.line([(D * 0.27, D * 0.52), (D * 0.44, D * 0.68), (D * 0.74, D * 0.34)], fill=WHITE + (255,), width=w,
               joint="curve")
    else:
        d.line([(D * 0.32, D * 0.32), (D * 0.68, D * 0.68)], fill=WHITE + (255,), width=w)
        d.line([(D * 0.68, D * 0.32), (D * 0.32, D * 0.68)], fill=WHITE + (255,), width=w)
    return with_shadow(ss(im, 2 * r, 2 * r), blur=6, pad=16)


# ---------- mascot: a snake in a graduation cap (original drawing)
@lru_cache(None)
def mascot(blink=False, mood="happy", size=300):
    S = 2
    w, h = size * S, int(size * 1.3) * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = w / 10
    body = bez(np.array([u * 2.2, h - u * 0.9]), np.array([u * 9.5, h - u * 1.2]),
               np.array([u * 1.0, h - u * 5.5]), np.array([u * 5.6, h - u * 7.4]), 60)
    tail = bez(np.array([u * 2.2, h - u * 0.9]), np.array([u * 1.2, h - u * 0.6]),
               np.array([u * 0.6, h - u * 1.3]), np.array([u * 0.9, h - u * 1.9]), 20)
    for pts, wd in ((tail, u * 0.9), (body, u * 1.9)):
        d.line([tuple(p) for p in pts], fill=SNAKE_D + (255,), width=int(wd + u * 0.35), joint="curve")
    for pts, wd in ((tail, u * 0.9), (body, u * 1.9)):
        d.line([tuple(p) for p in pts], fill=SNAKE + (255,), width=int(wd), joint="curve")
    d.line([tuple(p + np.array([u * 0.25, 0])) for p in body[5:50]], fill=(200, 236, 140, 255), width=int(u * 0.55),
           joint="curve")
    # head
    hx, hy = u * 5.7, h - u * 8.0
    d.ellipse((hx - u * 2.3, hy - u * 1.8, hx + u * 2.3, hy + u * 1.8), fill=SNAKE + (255,), outline=SNAKE_D + (255,),
              width=int(u * 0.18))
    for ex in (hx - u * 0.95, hx + u * 0.95):
        if blink:
            d.line([(ex - u * 0.55, hy - u * 0.3), (ex + u * 0.55, hy - u * 0.3)], fill=INK + (255,),
                   width=int(u * 0.2))
        else:
            d.ellipse((ex - u * 0.62, hy - u * 0.95, ex + u * 0.62, hy + u * 0.3), fill=WHITE + (255,),
                      outline=INK + (255,), width=int(u * 0.1))
            d.ellipse((ex - u * 0.28, hy - u * 0.55, ex + u * 0.28, hy + u * 0.1), fill=INK + (255,))
            d.ellipse((ex - u * 0.12, hy - u * 0.5, ex + u * 0.04, hy - u * 0.32), fill=WHITE + (255,))
    if mood == "wow":
        d.ellipse((hx - u * 0.35, hy + u * 0.55, hx + u * 0.35, hy + u * 1.2), fill=INK + (255,))
    else:
        d.arc((hx - u * 0.9, hy - u * 0.1, hx + u * 0.9, hy + u * 1.2), 20, 160, fill=INK + (255,),
              width=int(u * 0.18))
        d.line([(hx, hy + u * 1.15), (hx, hy + u * 1.7)], fill=RED + (255,), width=int(u * 0.14))
    for cx in (hx - u * 1.7, hx + u * 1.7):
        d.ellipse((cx - u * 0.35, hy + u * 0.3, cx + u * 0.35, hy + u * 0.7), fill=(255, 150, 150, 160))
    # graduation cap
    cy = hy - u * 1.75
    d.polygon([(hx - u * 2.6, cy), (hx, cy - u * 0.9), (hx + u * 2.6, cy), (hx, cy + u * 0.9)], fill=INK + (255,))
    d.rectangle((hx - u * 1.3, cy + u * 0.1, hx + u * 1.3, cy + u * 0.85), fill=INK + (255,))
    d.line([(hx, cy), (hx + u * 2.1, cy + u * 0.3), (hx + u * 2.2, cy + u * 1.6)], fill=YELLOW + (255,),
           width=int(u * 0.16))
    d.ellipse((hx + u * 2.0, cy + u * 1.5, hx + u * 2.45, cy + u * 1.95), fill=YELLOW + (255,))
    return with_shadow(ss(im, size, int(size * 1.3)), blur=10, alpha=50)


@lru_cache(None)
def bubble(s, size=34):
    t = text(s, size, INK)
    w, h = t.width + 40, t.height + 24
    S = 2
    im = Image.new("RGBA", ((w + 10) * S, (h + 30) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3 * S, 3 * S, w * S, h * S), 18 * S, fill=WHITE + (255,), outline=INK + (255,), width=4 * S)
    d.polygon([((w - 50) * S, (h - 2) * S), ((w - 18) * S, (h - 2) * S), ((w - 10) * S, (h + 26) * S)],
              fill=WHITE + (255,), outline=INK + (255,))
    d.line([((w - 48) * S, (h - 2) * S), ((w - 20) * S, (h - 2) * S)], fill=WHITE + (255,), width=6 * S)
    im = ss(im, w + 10, h + 30)
    im.alpha_composite(t, (20, 12))
    return with_shadow(im, blur=6, alpha=40, pad=16)


# mascot reactions: (time, text, mood)
REACT = [(0.6, "Hello!", "happy"), (VO_AT["code"] + 2.6, "Yaad rakho!", "happy"),
         (VO_AT["explain"] + 3.2, "Wow!", "wow"), (VO_AT["output"] + 0.3, "Sahi!", "happy"),
         (VO_AT["chal1"] + 1.4, "Try karo!", "happy"), (CUTS[5] + 0.4, "Kal milte hain!", "happy")]


def draw_mascot(L, t, x=920, y=1640, s=1.0):
    blink = (t % 3.1) < 0.12
    mood, msg, age = "happy", None, 9
    for tr, m, md in REACT:
        if t >= tr and t - tr < 1.8:
            msg, mood, age = m, md, t - tr
    bob = 10 * math.sin(t * 3.2)
    squash = 1 + 0.06 * math.exp(-age * 6) if age < 1 else 1
    paste(L, mascot(blink, mood), x, y + bob, s * squash, rot=3 * math.sin(t * 1.7))
    if msg:
        b = bubble(msg)
        paste(L, b, x - 90 - b.width * 0.25, y - 250 + bob, pop(age, 0.25) * s, a=clamp((1.8 - age) / 0.2))


# ---------------------------------------------------------------- board background
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


@lru_cache(None)
def board_base():
    rng = np.random.default_rng(4)
    base = np.array(BOARD, np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
    shade = 1 - 0.05 * (np.hypot((XX - W / 2) / W, (YY - H / 2) / H) * 1.6)[..., None]
    img = base * shade
    # ghost marks of old, half-erased writing
    ghost = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(ghost)
    for _ in range(20):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        pts = [(x + k * rng.uniform(30, 60), y + 25 * math.sin(k * rng.uniform(0.5, 1.5))) for k in range(8)]
        gd.line(pts, fill=int(rng.uniform(25, 55)), width=int(rng.uniform(10, 26)), joint="curve")
    for s in ("print()", "x = 5", "for i in", "# notes", "if a > b:", "def"):
        gd.text((rng.uniform(40, W - 300), rng.uniform(100, H - 200)), s, font=font(int(rng.uniform(50, 80))),
                fill=int(rng.uniform(20, 40)))
    g = np.asarray(ghost.filter(ImageFilter.GaussianBlur(5)), np.float32)[..., None] / 255
    img = img * (1 - g * 0.5) + np.array((170, 178, 196), np.float32) * g * 0.5
    img += rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
    # aluminium frame edge
    edge = np.zeros((H, W, 1), np.float32)
    edge[:14], edge[-14:], edge[:, :14], edge[:, -14:] = 1, 1, 1, 1
    img = img * (1 - edge) + np.array((190, 194, 202), np.float32) * edge
    return np.clip(img, 0, 255).astype(np.uint8)


def board_img():
    im = Image.fromarray(board_base(), "RGB").convert("RGBA")
    # vertical series text on the left edge
    v = text("PYTHON KI PATHSHALA  •  EP 02", 26, GRAY, "mont").rotate(90, expand=True)
    paste(im, v, 38, H / 2)
    return im


def tag(L):
    """Top-left topic box, like the reference's outlined tag."""
    t1 = text("print() Statement", 34, INK)
    t2 = text("+ Pehla Code", 26, RED)
    w = max(t1.width, t2.width) + 36
    box = Image.new("RGBA", (w, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    d.rounded_rectangle((2, 2, w - 3, 97), 12, fill=HILITE + (120,), outline=INK + (255,), width=4)
    box.alpha_composite(t1, (16, 6))
    box.alpha_composite(t2, (18, 54))
    paste(L, box, 70, 64, anchor="lt")


# ---------------------------------------------------------------- scenes
def sc_title(L, t, tl):
    paste(L, text("PYTHON", 96, INK, "mont"), 540, 400, pop(tl, 0.3))
    s = back_out((tl - 0.15) / 0.4)
    paste(L, text("print()", 165, BLUE, "mono", stroke=6, stroke_col=INK), 540, 570, s, rot=-2)
    paste(L, pill("+ PEHLA COMMAND", 46, fg=WHITE, bg=RED, padx=34, pady=14), 540, 740, pop(tl - 0.45), rot=-4)
    # a hand-drawn laptop with "?" -> "Hello!" in a speech bubble
    u = ease((tl - 0.6) / 0.8)
    marker_rect(L, (230, 920, 760, 1230), u, INK, w=8, r=20, fill=WHITE)
    if u >= 1:
        d = ImageDraw.Draw(L)
        d.polygon([(170, 1290), (820, 1290), (760, 1232), (230, 1232)], fill=(220, 224, 232, 255),
                  outline=INK + (255,))
        d.line([(170, 1290), (820, 1290)], fill=INK + (255,), width=8)
        q = "?" if t < VO_AT["hook2"] + 0.3 else ">>> print()"
        col = RED if q == "?" else BLUE
        paste(L, text(q, 150 if q == "?" else 56, col, "mono" if q != "?" else "mont"), 495,
              1065 + (8 * math.sin(t * 9) if q == "?" else 0), pop(tl - 1.4 if q == "?" else t - VO_AT["hook2"] - 0.3))
    # line typed with hook2
    draw_line(L, (("Chalo, apna ", INK, False), ("pehla command", RED, True), (" seekhein!", INK, False)),
              80, 1380, t, VO_AT["hook2"] + 0.1, size=52, cps=26)
    draw_line(L, (("Python ko bolna sikhaana hai? ", INK, False),), 90, 220, t, VO_AT["hook1"] + 0.05, size=54,
              cps=26)


CODE = (("print", P_FN), ("(", P_PAR), ('"Hello World!"', P_STR), (")", P_PAR))
CODE_LEN = sum(len(s) for s, _ in CODE)
CODE_X, CODE_Y = 120, 790
CODE_T0 = VO_AT["code"] + 1.0
CODE_CPS = 16.0
LABELS = [  # (char range in code, label, colour, label pos, appears at)
    ((0, 5), "command", BLUE, (190, 1060), VO_AT["code"] + 2.4),
    ((5, 6), "( ) bracket", INK, (480, 600), VO_AT["code"] + 2.9),
    ((6, 20), '" " text', GREEN, (690, 1080), VO_AT["code"] + 3.4),
]


def draw_code(L, t, n=None, hl_string=0.0):
    n = CODE_LEN if n is None else n
    if hl_string > 0:
        x0 = CODE_X + code_x_of(CODE, 6)
        x1 = CODE_X + code_x_of(CODE, 6) + (code_x_of(CODE, 20) - code_x_of(CODE, 6)) * ease(hl_string)
        ImageDraw.Draw(L).polygon([(x0 - 6, CODE_Y + 30), (x1 + 6, CODE_Y + 24), (x1 + 4, CODE_Y + 94),
                                   (x0 - 8, CODE_Y + 98)], fill=HILITE + (200,))
    L.alpha_composite(code_img(CODE, n), (CODE_X, CODE_Y))


def sc_code(L, t, tl):
    draw_line(L, (("Screen par kuch ", INK, False), ("dikhana", BLUE, False), (" hai?", INK, False)),
              90, 220, t, VO_AT["code"] + 0.05, size=66, cps=26)
    draw_line(L, (("= use karo ", INK, False), ("print()", RED, True)), 90, 320, t, VO_AT["code"] + 2.5, size=66,
              cps=26)
    n = min(CODE_LEN, type_n(t, CODE_T0, CODE_CPS))
    draw_code(L, t, n)
    if 0 < n < CODE_LEN and int(t * 6) % 2:
        x = CODE_X + code_x_of(CODE, n)
        ImageDraw.Draw(L).rectangle((x + 4, CODE_Y + 16, x + 12, CODE_Y + 90), fill=INK + (255,))
    for (a, b), lab, col, (lx, ly), ta in LABELS:
        u = (t - ta) / 0.35
        if u <= 0:
            continue
        cx = CODE_X + (code_x_of(CODE, a) + code_x_of(CODE, b)) / 2
        top = ly < CODE_Y
        marker_arrow(L, (lx + (60 if not top else 40), ly + (-20 if not top else 60)),
                     (cx, CODE_Y + (8 if top else 100)), u, col, w=7, bend=40 if top else -40)
        if u >= 1:
            paste(L, text(lab, 52, col), lx + 60, ly + 20, pop(t - ta - 0.35, 0.25))


TERM = (150, 1110, 930, 1350)
RUN_AT = VO_AT["explain"] + 2.0
OUT_AT = RUN_AT + 0.55


def sc_explain(L, t, tl):
    draw_line(L, (("Jaise yahan likha ", INK, False), ("Hello World!", GREEN, True)), 90, 220, t,
              VO_AT["explain"] + 0.05, size=64, cps=26)
    draw_code(L, t, hl_string=(t - (VO_AT["explain"] + 0.9)) / 0.4)
    # Run button gets clicked
    age = t - (VO_AT["explain"] + 1.3)
    if age > 0:
        press = 1 - 0.12 * math.exp(-((t - RUN_AT) / 0.06) ** 2)
        paste(L, pill("▶  Run", 48, fg=WHITE, bg=GREEN, which="mono", padx=34, pady=14), 800, 1000,
              pop(age) * press)
        if t < RUN_AT + 0.4:
            m = ease((t - (RUN_AT - 0.6)) / 0.5)
            paste(L, cursor(), 980 - 120 * m, 1150 - 100 * m)
    # arrow down to the screen
    marker_arrow(L, (430, 900), (430, TERM[1] - 10), (t - RUN_AT) / 0.3, INK, w=7, bend=30)
    u = (t - RUN_AT - 0.2) / 0.35
    marker_rect(L, TERM, u, INK, w=7, r=22, fill=WHITE)
    if u >= 1:
        L.alpha_composite(text("Screen", 34, GRAY), (TERM[0] + 24, TERM[1] + 14))
        n = type_n(t, OUT_AT, 22)
        if n > 0:
            paste(L, text("Hello World!"[:n], 84, INK, "mono"), TERM[0] + 40, TERM[1] + 80, anchor="lt")
    draw_line(L, (("Python ise ", INK, False), ("screen par", BLUE, False), (" dikhayega!", INK, False)),
              90, 1390, t, VO_AT["explain"] + 2.8, size=54, cps=28)


def sc_output(L, t, tl):
    draw_line(L, (("Dekha! Bas ", INK, False), ("1 LINE", RED, True), (" code!", INK, False)), 90, 230, t,
              VO_AT["output"] + 0.05, size=76, cps=26)
    paste(L, code_img(CODE, CODE_LEN, 62), 540, 560, pop(tl, 0.3))
    marker_arrow(L, (540, 640), (540, 760), (tl - 0.25) / 0.25, INK, w=7, bend=20)
    box = (110, 800, 970, 1080)
    marker_rect(L, box, (tl - 0.4) / 0.3, GREEN, w=9, r=26, fill=(236, 250, 240))
    if tl > 0.7:
        L.alpha_composite(text("Output:", 40, GREEN), (box[0] + 30, box[1] + 22))
        paste(L, text("Hello World!", 96, INK, "mono"), 540, 980, pop(tl - 0.7, 0.3))
        paste(L, tick_badge(56), box[2] - 10, box[1] - 10, pop(tl - 1.0), rot=-10)
    draw_line(L, (("Message ", INK, False), ("screen par!", GREEN, True)), 120, 1180, t, VO_AT["output"] + 1.4,
              size=70, cps=26)
    confetti(L, tl - 0.7, 540, 940)


CHAL_CODE = (("print", P_FN), ("(", P_PAR), ('"', P_STR), ("________", RED), ('"', P_STR), (")", P_PAR))
COUNT_T0 = VO_AT["chal1"] + 2.1


def sc_chal(L, t, tl):
    s = back_out(tl / 0.35)
    shake = 6 * math.sin(tl * 40) * math.exp(-tl * 4)
    paste(L, text("CHALLENGE TIME!", 100, RED, "mont", stroke=5, stroke_col=YELLOW), 540 + shake, 280, s, rot=-3)
    draw_line(L, (("Apna ", INK, False), ("naam", RED, True), (" display karo!", INK, False)), 120, 420, t,
              VO_AT["chal1"] + 1.0, size=66, cps=26)
    blink = 1 if int(t * 3) % 2 else 0.35
    im = code_img(CHAL_CODE, 99, 72)
    paste(L, im, 540, 720, pop(tl - 0.3), a=1.0)
    if blink < 1:
        x0 = 540 - im.width / 2 + code_x_of(CHAL_CODE, 7, 72)
        ImageDraw.Draw(L).rectangle((x0, 690, x0 + code_x_of(CHAL_CODE, 15, 72) - code_x_of(CHAL_CODE, 7, 72), 760),
                                    fill=BOARD + (150,))
    # example answer appears in the box below
    age = t - (VO_AT["chal1"] + 1.8)
    if age > 0:
        marker_rect(L, (170, 840, 910, 990), age / 0.3, BLUE, w=6, r=20, fill=WHITE)
        if age > 0.3:
            L.alpha_composite(text("Ex.", 36, GRAY), (195, 855))
            paste(L, code_img((("print", P_FN), ("(", P_PAR), ('"Rahul"', P_STR), (")", P_PAR)), min(14, int((age - 0.3) * 24)), 58), 560, 925)
    # 3-2-1 countdown ring
    age = t - COUNT_T0
    if age > 0:
        k = min(2, int(age))
        num = str(3 - k) if age < 3 else "✓"
        R = 110
        ring = Image.new("RGBA", (2 * R + 30, 2 * R + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        d.ellipse((15, 15, 2 * R + 15, 2 * R + 15), fill=WHITE + (255,), outline=(220, 220, 228, 255), width=14)
        frac = 1 - (age % 1.0) if age < 3 else 1
        d.arc((15, 15, 2 * R + 15, 2 * R + 15), -90, -90 + 360 * frac, fill=ORANGE + (255,), width=14)
        paste(ring, text(num, 120, INK, "mont" if num != "✓" else "mono"), R + 15, R + 15,
              1 + 0.25 * math.exp(-(age % 1.0) * 8))
        paste(L, ring, 540, 1260, pop(age, 0.25))
        paste(L, text("Comment karo!", 60, INK), 540, 1440, 1, a=ease((age - 0.3) / 0.3))


def sc_end(L, t, tl):
    # framed board (wood frame) like the reference's end card, but light
    fr = (60, 160, 1020, 1800)
    d = ImageDraw.Draw(L)
    d.rounded_rectangle(fr, 22, fill=WOOD + (255,))
    d.rounded_rectangle((fr[0] + 26, fr[1] + 26, fr[2] - 26, fr[3] - 26), 10, fill=(252, 250, 244, 255))
    for k in range(6):
        y = fr[1] + 6 + k * 3
        d.line([(fr[0] + 20, y), (fr[2] - 20, y)], fill=(150, 98, 52, 255), width=1)
    paste(L, text("Python ki", 70, BLUE), 540, 300, pop(tl - 0.1))
    paste(L, text("PATHSHALA", 108, INK, "mont"), 540, 400, pop(tl - 0.2))
    draw_line(L, (("Agar video ", INK, False), ("achha laga...", RED, True)), 170, 500, t, CUTS[5] + 0.4, size=62,
              cps=26)
    taps = [CUTS[5] + 1.3, CUTS[5] + 2.0, CUTS[5] + 2.7]
    ys = [720, 860, 1000]
    btns = [("LIKE", "LIKED!", BLUE, BLUE), ("SHARE", "SHARED!", GREEN, GREEN),
            ("SUBSCRIBE", "SUBSCRIBED", RED, (110, 116, 128))]
    for k, (a, b, c0, c1) in enumerate(btns):
        age = t - (CUTS[5] + 0.6 + k * 0.12)
        if age <= 0:
            continue
        on = t >= taps[k]
        press = 1 - 0.1 * math.exp(-((t - taps[k] - 0.03) / 0.05) ** 2)
        paste(L, end_button(b if on else a, k, c1 if on else c0), 540, ys[k], pop(age) * press)
        if on and t - taps[k] < 0.45:
            rr = (t - taps[k]) * 600
            d.ellipse((540 - rr, ys[k] - rr * 0.3, 540 + rr, ys[k] + rr * 0.3),
                      outline=c1 + (int((1 - (t - taps[k]) / 0.45) * 200),), width=5)
    # cursor travels between buttons
    if t > CUTS[5] + 0.8:
        k = min(2, sum(1 for tp in taps if t > tp + 0.2))
        t0 = (taps[k - 1] + 0.2) if k else CUTS[5] + 0.8
        m = ease((t - t0) / 0.35)
        y0 = ys[k - 1] if k else 1300
        paste(L, cursor(), 700 - 30 * (1 - m), y0 + (ys[k] - y0) * m + 50)
    # next-video card
    age = t - (CUTS[5] + 2.9)
    if age > 0:
        nc = Image.new("RGBA", (480, 130), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nc)
        nd.rounded_rectangle((2, 2, 477, 127), 16, fill=INK + (255,), outline=YELLOW + (255,), width=4)
        nc.alpha_composite(text("NEXT VIDEO", 28, YELLOW, "mont"), (22, 14))
        nc.alpha_composite(text("EP 03: VARIABLES", 40, WHITE, "mont"), (22, 58))
        paste(L, nc, 330 - 300 * (1 - ease_out(age / 0.3)), 1600, 1)


@lru_cache(None)
def end_button(label, k, col):
    w, h = 620, 116
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=col + (255,))
    ic = (w * S * 0.16, h * S / 2)
    r = 26 * S
    if k == 0:   # thumbs up
        d.rounded_rectangle((ic[0] - r, ic[1] - r * 0.1, ic[0] - r * 0.45, ic[1] + r), 6 * S, fill=WHITE + (255,))
        d.rounded_rectangle((ic[0] - r * 0.3, ic[1] - r * 0.15, ic[0] + r, ic[1] + r), 12 * S, fill=WHITE + (255,))
        d.polygon([(ic[0] - r * 0.3, ic[1]), (ic[0] - r * 0.05, ic[1] - r), (ic[0] + r * 0.3, ic[1] - r * 0.85),
                   (ic[0] + r * 0.25, ic[1] - r * 0.1)], fill=WHITE + (255,))
    elif k == 1:  # share nodes
        pts = [(ic[0] + r * 0.7, ic[1] - r * 0.7), (ic[0] - r * 0.7, ic[1]), (ic[0] + r * 0.7, ic[1] + r * 0.7)]
        d.line([pts[0], pts[1], pts[2]], fill=WHITE + (255,), width=6 * S)
        for p in pts:
            d.ellipse((p[0] - 10 * S, p[1] - 10 * S, p[0] + 10 * S, p[1] + 10 * S), fill=WHITE + (255,))
    else:         # bell
        d.chord((ic[0] - r * 0.8, ic[1] - r, ic[0] + r * 0.8, ic[1] + r * 0.9), 180, 360, fill=WHITE + (255,))
        d.rectangle((ic[0] - r * 0.8, ic[1] - r * 0.1, ic[0] + r * 0.8, ic[1] + r * 0.55), fill=WHITE + (255,))
        d.polygon([(ic[0] - r, ic[1] + r * 0.7), (ic[0] + r, ic[1] + r * 0.7), (ic[0] + r * 0.8, ic[1] + r * 0.5),
                   (ic[0] - r * 0.8, ic[1] + r * 0.5)], fill=WHITE + (255,))
        d.ellipse((ic[0] - r * 0.25, ic[1] + r * 0.65, ic[0] + r * 0.25, ic[1] + r), fill=WHITE + (255,))
    im = ss(im, w, h)
    tx = text(label, 54, WHITE, "mont")
    im.alpha_composite(tx, (int(w * 0.58 - tx.width / 2), (h - tx.height) // 2))
    return with_shadow(im, blur=10, alpha=80)


@lru_cache(None)
def cursor(size=86):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = [(0.1, 0.05), (0.1, 0.8), (0.3, 0.62), (0.45, 0.95), (0.58, 0.89), (0.43, 0.57), (0.7, 0.55)]
    ImageDraw.Draw(im).polygon([(x * s, y * s) for x, y in pts], fill=WHITE + (255,), outline=INK + (255,),
                               width=5 * S)
    return with_shadow(ss(im, size, size), blur=5, alpha=80, pad=14)


CONF_COLS = [RED, BLUE, GREEN, YELLOW, ORANGE]


def confetti(L, age, cx, cy, n=60, seed=2, spread=800):
    if age < 0 or age > 1.6:
        return
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(L)
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(0.35, 1.0) * spread
        col = CONF_COLS[rng.integers(len(CONF_COLS))]
        sz = rng.uniform(10, 20)
        x = cx + math.cos(ang) * sp * (1 - math.exp(-age * 4))
        y = cy + math.sin(ang) * sp * (1 - math.exp(-age * 4)) + 650 * age * age
        th = rng.uniform(-8, 8) * age
        pts = [(x + sz * math.cos(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5),
                y + sz * math.sin(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5)) for k in range(4)]
        d.polygon(pts, fill=col + (int(clamp(1.6 - age) * 255),))


SCENE_FN = {"title": sc_title, "code": sc_code, "explain": sc_explain, "output": sc_output, "chal": sc_chal,
            "end": sc_end}


# ---------------------------------------------------------------- duster wipe, camera, flash
@lru_cache(None)
def duster():
    S = 2
    w, h = 300, 150
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S * 0.62), 22 * S, fill=(40, 60, 120, 255))
    d.rounded_rectangle((12 * S, h * S * 0.5, (w - 12) * S, h * S - 1), 10 * S, fill=(70, 70, 76, 255))
    d.text((w * S / 2, h * S * 0.3), "PATHSHALA", font=font(30 * S, "mont"), fill=(255, 255, 255, 230), anchor="mm")
    return with_shadow(ss(im, w, h), blur=10, alpha=90)


def wipe_path(u):
    """Duster position for wipe progress u (zig-zag top -> bottom)."""
    rows = 5
    r = min(rows - 1, int(u * rows))
    f = u * rows - r
    y = 260 + r * (H - 420) / (rows - 1)
    x = -120 + (W + 240) * (f if r % 2 == 0 else 1 - f)
    return x, y + 30 * math.sin(f * math.pi)


def wipe_mask(u):
    """Area already cleaned by the duster (1 = wiped)."""
    rows = 5
    m = np.zeros((H, W), np.float32)
    band = (H - 420) / (rows - 1)
    for r in range(rows):
        f = clamp(u * rows - r)
        if f <= 0:
            break
        y0 = int(0 if r == 0 else 260 + (r - 0.5) * band)
        y1 = int(H if r == rows - 1 else 260 + (r + 0.5) * band)
        if r % 2 == 0:
            m[y0:y1, : int(W * f + 60)] = 1
        else:
            m[y0:y1, int(W * (1 - f) - 60):] = 1
    return cv2.GaussianBlur(m, (0, 0), 18)[..., None]


def camera(t):
    name, tl, i = scene_at(t)
    s = 1.0 + 0.02 * clamp(tl / 4.0)
    for ci in PUNCH_CUTS:
        if 0 <= t - CUTS[ci] < 0.35:
            s += 0.1 * (1 - ease_out((t - CUTS[ci]) / 0.35))
    for ci in ZOOM_CUTS:
        dt = t - CUTS[ci]
        if -0.3 <= dt < 0:
            s += 0.25 * ease((dt + 0.3) / 0.3)
        elif 0 <= dt < 0.3:
            s += 0.12 * (1 - ease_out(dt / 0.3))
    return s


def apply_camera(frame, s):
    if abs(s - 1) < 1e-4:
        return frame
    M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def content(t):
    name, tl, _ = scene_at(t)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](L, t, tl)
    return L


def render(t):
    bg = board_img()
    L = content(t)
    # duster wipe: the outgoing scene is erased before the cut
    for ci in WIPE_CUTS:
        dt = CUTS[ci] - t
        if 0 < dt <= WIPE:
            u = 1 - dt / WIPE
            a = np.asarray(L, np.float32)
            a[..., 3] *= (1 - wipe_mask(u)[..., 0])
            L = Image.fromarray(a.astype(np.uint8), "RGBA")
    bg.alpha_composite(L)
    if scene_at(t)[0] != "end":
        tag(bg)
    draw_mascot(bg, t, *(((900, 1640, 0.8),) if scene_at(t)[0] == "end" else ((920, 1640, 1.0),))[0])
    for ci in WIPE_CUTS:
        dt = CUTS[ci] - t
        if 0 < dt <= WIPE:
            x, y = wipe_path(1 - dt / WIPE)
            paste(bg, duster(), x, y, 1, rot=8 * math.sin(t * 30))
    frame = apply_camera(np.asarray(bg.convert("RGB")), camera(t))
    for ci in PUNCH_CUTS:
        age = t - CUTS[ci]
        if 0 <= age < 0.2:
            a = 0.7 * (1 - age / 0.2) ** 2
            frame = (frame * (1 - a) + 255 * a).astype(np.uint8)
    # progress bar
    p = int(W * t / DUR)
    frame = frame.copy()
    frame[H - 10:, :p] = (np.linspace(np.array(BLUE), np.array(RED), max(p, 1))[None, :p]).astype(np.uint8)
    return np.ascontiguousarray(frame)


def render_idx(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- audio
def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, f0, f1):
    b, a = signal.butter(2, [f0 / (SR / 2), f1 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += g * x[:n]


RNG = np.random.default_rng(5)
BPM = 104
BEAT = 60 / BPM


def nfreq(semi):
    return 440.0 * 2 ** (semi / 12)


def kick():
    n = int(0.3 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)


def snare():
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    return (bp(RNG.normal(0, 1, n), 1200, 6000) * 0.6 + np.sin(2 * np.pi * 190 * tt) * 0.4) * env_exp(n, 0.05)


def hat():
    n = int(0.05 * SR)
    return hp(RNG.normal(0, 1, n), 7500) * env_exp(n, 0.01) * 0.3


def epiano(f, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt + 0.8 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 3))
    return x * env_exp(n, 0.9) * np.minimum(1, np.arange(n) / 200)


# I-V-vi-IV in C: C G Am F  (semitones from A4 for roots)
CHORDS = [(-9, [0, 4, 7]), (-14, [0, 4, 7]), (-12, [0, 3, 7]), (-16, [0, 4, 7])]


def music():
    n = int((DUR + 1) * SR)
    drums, keys, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    K, Sn, Hh = kick(), snare(), hat()
    drop = (VO_AT["output"] - 0.55, CUTS[3])        # silence + riser before "Dekha!"
    for b in range(int(DUR / BEAT) + 2):
        tb = b * BEAT
        if drop[0] <= tb < drop[1]:
            continue
        root, ivs = CHORDS[(b // 4) % 4]
        add(drums, K, tb, 0.8 if b % 4 in (0, 2) else 0.0)
        if b % 2 == 1:
            add(drums, Sn, tb, 0.45)
        for k in (0, 0.5):
            add(drums, Hh, tb + k * BEAT + (0.03 if k else 0), 0.7 if k else 0.4)
        if b % 4 == 0:
            for iv in ivs:
                add(keys, epiano(nfreq(root + 12 + iv), 4 * BEAT), tb, 0.12)
        nb = int(BEAT * SR * 0.9)
        x = lp(np.sign(np.sin(2 * np.pi * nfreq(root - 12) * np.arange(nb) / SR)), 300) * env_exp(nb, 0.25)
        add(bass, x, tb, 0.35)
        # little melody pluck on the off-beats
        if b % 2 == 1:
            add(keys, epiano(nfreq(root + 24 + ivs[(b // 2) % 3]), 0.4) * 0.6, tb + BEAT / 2, 0.08)
    mix = drums + lp(keys, 4000) + bass
    i0, i1 = int(drop[0] * SR), int(drop[1] * SR)
    mix[i0:i1] = 0
    return mix


def tick():
    n = int(0.03 * SR)
    return bp(RNG.normal(0, 1, n), 1500, 5000) * env_exp(n, 0.005) * 0.5


def squeak(dur=0.3):
    """Marker on whiteboard: a scratchy, slightly pitched squeak."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    tone = np.sin(2 * np.pi * np.cumsum(1800 + 500 * np.sin(tt * 30)) / SR) * 0.15
    scratch = bp(RNG.normal(0, 1, n), 2500, 7000) * 0.4
    return (tone + scratch) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.7


def rub(dur):
    """Duster rubbing the board: rhythmic filtered noise."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = bp(RNG.normal(0, 1, n), 300, 2500)
    return x * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 6 * tt))) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.4 * 0.6


def pop_sfx(f0=520):
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f0 + 700 * tt / 0.12) / SR) * env_exp(n, 0.03) * 0.6


def ding():
    n = int(0.8 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1318.5 * tt) + 0.5 * np.sin(2 * np.pi * 1975.5 * tt) + 0.2 * np.sin(2 * np.pi * 2637 * tt)
    return x * env_exp(n, 0.22) * 0.35


def whoosh(dur=0.35):
    n = int(dur * SR)
    x = RNG.normal(0, 1, n)
    seg = n // 12
    out = np.zeros(n)
    for k in range(12):
        f = 600 + 4500 * k / 11
        out[k * seg:(k + 1) * seg] = bp(x[k * seg:(k + 1) * seg], f * 0.7, min(f * 1.4, 20000))[:seg]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5 * 0.7


def riser(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    return hp(RNG.normal(0, 1, n), 1500) * u ** 2 * 0.35 + np.sin(2 * np.pi * np.cumsum(200 + 1400 * u ** 2) / SR) * u ** 1.5 * 0.25


def impact():
    n = int(1.4 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-tt * 10)) / SR) * np.exp(-tt * 3) * 0.9 + \
        hp(RNG.normal(0, 1, n), 3000) * np.exp(-tt * 3.5) * 0.3


def click_sfx():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * tt) * env_exp(n, 0.006) + hp(RNG.normal(0, 1, n), 4000) * env_exp(n, 0.003)) * 0.5


def clock_tick():
    n = int(0.08 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1000 * tt) + 0.5 * np.sin(2 * np.pi * 3000 * tt)) * env_exp(n, 0.01) * 0.6


def bell():
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * tt) * g for f, g in ((880, 1), (1760, 0.5), (2637, 0.3))) * env_exp(n, 0.3) * 0.3


def typing(buf, t0, nchars, cps, g=0.5):
    for k in range(nchars):
        if k % 2 == 0:
            add(buf, tick(), t0 + k / cps, g)


def sfx_track():
    n = int((DUR + 1) * SR)
    s = np.zeros(n)
    # title
    add(s, impact(), 0.0, 0.6)
    add(s, pop_sfx(500), 0.15, 0.5)
    add(s, whoosh(0.3), 0.3, 0.4)
    add(s, pop_sfx(640), 0.45, 0.5)
    add(s, squeak(0.6), 0.6, 0.35)
    typing(s, VO_AT["hook1"] + 0.05, 30, 26, 0.3)
    typing(s, VO_AT["hook2"] + 0.1, 33, 26, 0.3)
    # wipes
    for ci in WIPE_CUTS:
        add(s, rub(WIPE), CUTS[ci] - WIPE, 0.8)
    # code
    typing(s, VO_AT["code"] + 0.05, 28, 26, 0.3)
    typing(s, CODE_T0, CODE_LEN, CODE_CPS, 0.6)
    typing(s, VO_AT["code"] + 2.5, 18, 26, 0.3)
    for *_, ta in LABELS:
        add(s, squeak(0.3), ta, 0.35)
        add(s, pop_sfx(600), ta + 0.35, 0.35)
    # explain
    add(s, squeak(0.35), VO_AT["explain"] + 0.9, 0.3)
    add(s, pop_sfx(520), VO_AT["explain"] + 1.3, 0.4)
    add(s, click_sfx(), RUN_AT, 0.9)
    add(s, whoosh(0.3), RUN_AT, 0.3)
    typing(s, OUT_AT, 12, 22, 0.6)
    add(s, ding(), OUT_AT + 0.6, 0.5)
    # output: riser in the music gap, impact on the reveal
    add(s, riser(0.6), CUTS[3] - 0.6, 0.6)
    add(s, impact(), CUTS[3], 0.9)
    add(s, ding(), CUTS[3] + 0.7, 0.6)
    add(s, pop_sfx(700), CUTS[3] + 1.0, 0.5)
    # challenge
    add(s, impact(), CUTS[4], 0.5)
    add(s, pop_sfx(560), CUTS[4] + 0.3, 0.4)
    for k in range(3):
        add(s, clock_tick(), COUNT_T0 + k, 0.7)
    add(s, ding(), COUNT_T0 + 3, 0.5)
    # end
    add(s, whoosh(0.4), CUTS[5] - 0.3, 0.5)
    for k, tp in enumerate([CUTS[5] + 1.3, CUTS[5] + 2.0, CUTS[5] + 2.7]):
        add(s, click_sfx(), tp, 1.0)
        add(s, pop_sfx(620 + 120 * k), tp + 0.03, 0.4)
        add(s, bell() if k == 2 else ding(), tp + 0.05, 0.5)
    add(s, whoosh(0.3), CUTS[5] + 2.9, 0.3)
    # mascot bubbles
    for tr, *_ in REACT:
        add(s, pop_sfx(760), tr, 0.3)
    return s


def voice_track():
    n = int((DUR + 1) * SR)
    v = np.zeros(n)
    keys = list(VO_AT)
    for i, key in enumerate(keys):
        path = os.path.join(WORK, f"vo_{key}.wav")
        if not os.path.exists(path):
            continue
        a, _ = sf.read(path)
        start = VO_AT[key]
        end = VO_AT[keys[i + 1]] - 0.08 if i + 1 < len(keys) else DUR - 0.2
        rate = (len(a) / SR) / (end - start)
        if rate > 1.0:
            tmp = os.path.join(WORK, f"fit_{key}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"atempo={rate:.4f}", tmp], check=True)
            a, _ = sf.read(tmp)
        add(v, a, start)
        print(f"  vo {key:8s} {start:6.2f}-{start + len(a) / SR:6.2f}s")
    return v


def build_audio(path, with_voice=True):
    m, s = music(), sfx_track()
    v = voice_track() if with_voice else np.zeros_like(m)
    m = m / (np.abs(m).max() + 1e-9)
    s = s / (np.abs(s).max() + 1e-9)
    if v.any():
        env = signal.lfilter([1 - math.exp(-1 / (0.25 * SR))], [1, -math.exp(-1 / (0.25 * SR))], np.abs(v))
        env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
        mix = m * 0.42 * (1 - 0.55 * env) + s * 0.45 * (1 - 0.25 * env) + v / np.abs(v).max() * 0.95
    else:
        mix = m * 0.6 + s * 0.55
    mix = mix[: int(DUR * SR)]
    fade = int(0.25 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    sf.write(path, np.stack([mix, mix], 1).astype(np.float32), SR)


# ---------------------------------------------------------------- thumbnail
def thumbnail(path):
    bg = board_img()
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste(L, text("PYTHON", 110, INK, "mont"), 540, 330)
    paste(L, text("print()", 230, BLUE, "mono", stroke=7, stroke_col=INK), 540, 560, rot=-2)
    paste(L, pill("PEHLA CODE!", 70, fg=WHITE, bg=RED, padx=44, pady=18), 540, 770, rot=-4)
    marker_rect(L, (140, 930, 940, 1200), 1, GREEN, w=10, r=26, fill=(236, 250, 240))
    L.alpha_composite(text("Output:", 44, GREEN), (170, 950))
    paste(L, text("Hello World!", 96, INK, "mono"), 540, 1110)
    paste(L, tick_badge(60), 930, 930, rot=-10)
    paste(L, pill("EP 02  •  25 sec", 50, fg=INK, bg=YELLOW, padx=34, pady=14), 360, 1340, rot=3)
    bg.alpha_composite(L)
    tag(bg)
    draw_mascot(bg, 0.3, 880, 1620, 1.15)
    bg.convert("RGB").save(path, quality=92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    board_base()
    thumbnail(os.path.join(OUT, "thumbnail.jpg"))
    if args.preview:
        ts = np.linspace(0.3, DUR - 0.1, 24)
        sheet = Image.new("RGB", (270 * 8, 480 * 3))
        for k, t in enumerate(ts):
            sheet.paste(Image.fromarray(render(t)).resize((270, 480)), ((k % 8) * 270, (k // 8) * 480))
        sheet.save(os.path.join(WORK, "preview.jpg"), quality=85)
        print("wrote", os.path.join(WORK, "preview.jpg"))
        return
    silent = os.path.join(WORK, "video.mp4")
    nf = int(round(DUR * FPS))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_idx, range(nf), chunksize=4)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                print(f"  frame {k}/{nf}")
    ff.stdin.close()
    ff.wait()
    for suffix, voice in (("", True), ("-music-only", False)):
        wav = os.path.join(WORK, f"mix{suffix}.wav")
        build_audio(wav, voice)
        out = os.path.join(OUT, f"{NAME}{suffix}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                        "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
