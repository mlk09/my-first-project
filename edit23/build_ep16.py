#!/usr/bin/env python3
"""Python ki Pathshala EP 16 - Lists in 30 SECONDS  (1080x1920 HD Short, high-retention cut)

Decoded from 2 reference stills:
  1  interview Q&A card: light-blue flat background, RED handwritten question ("Explain the difference
     between a list and a tuple"), black handwritten answer (mutable vs immutable), cartoon interviewer
  2  dark navy, LETTER-SPACED neon CYAN headline "list_name = [ ]", glowing YELLOW code line, cyan captions
Ours (own style): the series' single background (navy + grid + moving floor + triangles + symbol
watermark) for EVERY scene incl. quiz and end screen; letter-spaced neon headlines + glowing yellow code
(ref 2); a handwritten "interview fact" card (ref 1, our colours); a live shopping-bag list (boxes inside
glowing [ ] brackets) for index / change / append; whip transitions every ~5 s, something new every
1.5-2 s, comment-bait quiz without reveal, 3.5 s end screen -> 30 s total.

Usage:  python3 edit23/build_ep16.py [--preview]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit22"))
import build_ep15 as e15   # noqa: E402  EP 15 -> EP 14/13/12/11/08 helpers + background

e14, e13, b, p11, m = e15.e14, e15.e13, e15.b, e15.p11, e15.m
fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste, glow = m.clamp, m.ease, m.pop, m.paste, b.glow
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
inter, MONO = b.inter, b.MONO
es.NEXT = "EP 17: LIST METHODS"
WHITE, YEL, GREEN, RED, ORANGE, CYAN = e14.WHITE, e14.YEL, e14.GREEN, e14.RED, e14.ORANGE, e14.CYAN
NEON = (60, 235, 255)
CODEY = (255, 222, 90)

SCENES = [(0.0, "hook"), (2.4, "syntax"), (8.0, "index"), (13.0, "change"), (18.5, "append"), (23.0, "quiz")]
END0 = 26.5
END_DUR = 3.5
TOTAL = END0 + END_DUR
WHIP = 0.22
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP16_Lists_30s.mp4")
WORK = os.path.join(HERE, "work")
_C = {}


# ------------------------------------------------------------------ text styles
def spaced(txt, col, size, track=0.18, font=None):
    """ref 2: letter-spaced neon headline"""
    key = ("sp", txt, col, size)
    if key not in _C:
        f = font or mb.font(MONO, size)
        gap = size * track
        w = int(sum(f.getlength(c) for c in txt) + gap * (len(txt) - 1)) + 80
        im = Image.new("RGBA", (w, int(size * 1.6)))
        d = ImageDraw.Draw(im)
        x = 40
        for c in txt:
            d.text((x, im.height / 2), c, font=f, fill=col, anchor="lm")
            x += f.getlength(c) + gap
        _C[key] = glow(im, 14, 1.6, col)
    return _C[key]


def code_line(st, t, t0, txt, cy, size=50, cps=34):
    """ref 2: glowing yellow code, typed, centred"""
    if t < t0:
        return
    n = min(len(txt), int((t - t0) * cps) + 1)
    f = mb.font(MONO, size)
    full = f.getlength(txt)
    im = Image.new("RGBA", (int(full) + 80, int(size * 1.7)))
    d = ImageDraw.Draw(im)
    d.text((40, im.height / 2), txt[:n], font=f, fill=CODEY, anchor="lm")
    if n < len(txt) or int(t * 3) % 2 == 0:
        x = 40 + f.getlength(txt[:n])
        d.rectangle((x + 3, im.height / 2 - size * 0.5, x + 8, im.height / 2 + size * 0.5), fill=WHITE)
    paste(st, glow(im, 10, 1.1, CODEY), 540, cy, 1)


def cyan_caption(st, t, t0, txt, cy, size=48, x=None):
    a = t - t0
    if a < 0:
        return
    im = spaced(txt, NEON, size, 0.06, inter(size, "Bold"))
    paste(st, im, x or 540, cy + 30 * (1 - ease(a / 0.25)), 1, ease(a / 0.2))


# ------------------------------------------------------------------ the shopping-bag list
BOX_Y = 1000


def box_img(txt, col, w=230, h=130):
    key = ("bx", txt, col, w)
    if key not in _C:
        im = Image.new("RGBA", (w + 40, h + 40))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((20, 20, 20 + w, 20 + h), 24, fill=(10, 24, 60, 240), outline=col, width=6)
        d.text((20 + w / 2, 20 + h / 2 + 2), txt, font=mb.font(MONO, 50 if len(txt) <= 5 else 42), fill=WHITE,
               anchor="mm")
        _C[key] = glow(im, 12, 1.1, col)
    return _C[key]


def layout(n):
    w = 230 if n <= 3 else 196
    step = 270 if n <= 3 else 215
    xs = [540 - step * (n - 1) / 2 + step * k for k in range(n)]
    return xs, w


def brackets(st, t, t0, n_t=None):
    a = t - t0
    if a < 0:
        return
    q = ease(a / 0.25)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    for side in (-1, 1):
        x = 540 + side * (500 - 160 * (1 - q))
        d.line((x, BOX_Y - 110, x, BOX_Y + 110), fill=NEON + (255,), width=10)
        d.line((x, BOX_Y - 110, x - side * 34, BOX_Y - 110), fill=NEON + (255,), width=10)
        d.line((x, BOX_Y + 110, x - side * 34, BOX_Y + 110), fill=NEON + (255,), width=10)
    st.alpha_composite(glow(lay, 14, 1.5, NEON))


def bag(st, t, items, *, t_in=None, hi=None, idx_t=None, neg=None, flip=None, add=None, q_mark=None):
    """items = current list; hi = {k: t}; flip = (k, t, new); add = (t, new) -> relayout to n+1"""
    n = len(items)
    xs3, w3 = layout(n)
    xs, w = xs3, w3
    rel = 1.0
    if add is not None:
        rel = ease((t - add[0]) / 0.45) if t >= add[0] else 0.0
        xs4, w4 = layout(n + 1)
        xs = [a + (b2 - a) * rel for a, b2 in zip(xs3, xs4[:n])]
        w = int(w3 + (w4 - w3) * rel)
    for k, it in enumerate(items):
        col = (90, 140, 230)
        sc = 1.0 if t_in is None else pop(t - t_in - 0.2 * k, 0.3)
        y = BOX_Y
        if hi and k in hi and t >= hi[k]:
            col = YEL
            a = t - hi[k]
            y -= 40 * math.sin(math.pi * clamp(a / 0.5))
        txt = it
        if flip and k == flip[0] and t >= flip[1]:
            fq = clamp((t - flip[1]) / 0.3)
            if fq > 0.5:
                txt, col = flip[2], GREEN
            im = box_img(txt, col, w)
            im = im.resize((im.width, max(2, int(im.height * max(0.05, abs(math.cos(math.pi * fq)))))), Image.BICUBIC)
            paste(st, im, xs[k], y, sc)
            if fq >= 1:
                b.sparkle_burst(st, t, flip[1] + 0.3, xs[k], y, 10, GREEN, 140)
        else:
            paste(st, box_img(txt, col, w), xs[k], y, sc)
        if idx_t is not None and t >= idx_t + 0.1 * k:
            paste(st, b.big_num(str(k), (150, 200, 255), 46), xs[k], BOX_Y + 110, pop(t - idx_t - 0.1 * k, 0.25))
        if neg is not None and t >= neg + 0.1 * (n - 1 - k):
            paste(st, b.big_num(str(k - n), (255, 150, 170), 40), xs[k], BOX_Y - 112,
                  pop(t - neg - 0.1 * (n - 1 - k), 0.25))
    if add is not None and t >= add[0]:
        xs4, w4 = layout(n + 1)
        a = t - add[0]
        q = ease(a / 0.5)
        x = 1200 + (xs4[n] - 1200) * q
        paste(st, box_img(add[1], GREEN, w4), x, BOX_Y - 60 * math.sin(math.pi * q), 1)
        if a >= 0.5:
            b.sparkle_burst(st, t, add[0] + 0.5, xs4[n], BOX_Y, 10, GREEN, 140)
    if q_mark is not None and t >= q_mark:
        k = n - 2 if add is None else n - 1
        xs_q = layout(n + (1 if add is not None else 0))[0]
        s = 1 + 0.12 * math.sin((t - q_mark) * 8)
        paste(st, e13.comic("?", e13.PINK, 150), xs_q[k], BOX_Y - 190, pop(t - q_mark, 0.3) * s)


def out_chip(st, t, t0, txt, cy=1320):
    if t < t0:
        return
    paste(st, b.big_num("Output:", (150, 170, 210), 40), 300, cy, ease((t - t0) / 0.2))
    paste(st, b.big_num(txt, GREEN, 80), 600, cy, pop(t - t0, 0.3))


# ------------------------------------------------------------------ interview card (ref 1, our colours)
def interview_card(st, t, t0, cy=1420):
    a = t - t0
    if a < 0:
        return
    key = "icard"
    if key not in _C:
        im = Image.new("RGBA", (740, 250))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((10, 14, 730, 244), 26, fill=(0, 0, 0, 90))
        d.rounded_rectangle((4, 4, 724, 234), 26, fill=(235, 246, 255))
        hf = mb.font(mb.CHALK, 46)
        d.text((36, 58), "Interview: List vs Tuple?", font=hf, fill=(225, 30, 45), anchor="lm")
        d.text((36, 128), "List = badal sakti hai", font=mb.font(mb.CHALK, 44), fill=(20, 24, 40), anchor="lm")
        d.text((36, 190), "Tuple = fixed (EP 18)", font=mb.font(mb.CHALK, 44), fill=(20, 24, 40), anchor="lm")
        _C[key] = im
    paste(st, _C[key], 440, cy + 60 * (1 - ease(a / 0.3)), pop(a, 0.35), 1, -2 * (1 - ease(a / 0.4)))


# ------------------------------------------------------------------ scenes
VARS = [f"marks{k} = {v}" for k, v in zip(range(1, 41), [90, 85, 77, 64, 98, 71, 55, 88] * 5)]


def draw_hook(st, t):
    # flood of variables scrolling up
    if t < 1.5:
        f = mb.font(MONO, 44)
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        off = t * 1400
        for k, txt in enumerate(VARS):
            y = 1700 + k * 70 - off
            if 560 < y < 1750:
                d.text((140 + (k % 3) * 20, y), txt, font=f, fill=(200, 210, 235, 200), anchor="lm")
        al = 1 - ease((t - 1.1) / 0.3)
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
        st.alpha_composite(lay)
    paste(st, e13.comic("100 VARIABLES?", RED, 120), 540, 420, pop(t - 0.1, 0.3), 1, -3)
    if t >= 0.9:
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        q = ease((t - 0.9) / 0.2)
        d.line((250, 700, 250 + 580 * q, 700 + 580 * q), fill=RED + (255,), width=26)
        d.line((830, 700, 830 - 580 * q, 700 + 580 * q), fill=RED + (255,), width=26)
        al = 1 - ease((t - 1.3) / 0.25)
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
        st.alpha_composite(glow(lay, 14, 1.0, RED))
    paste(st, e13.comic("NAHI!", YEL, 170), 540, 900, pop(t - 1.3, 0.25), 1, 4)
    paste(st, spaced("EK LIST!", NEON, 130, 0.2, inter(130, "ExtraBold")), 540, 1180, pop(t - 1.6, 0.3))


SYN_CODE = 'thaila = ["aam", "kela", "seb"]'


def draw_syntax(st, t):
    paste(st, spaced("list = [ ]", NEON, 96), 540, 380, pop(t - 2.5, 0.3))
    code_line(st, t, 3.3, SYN_CODE, 600, 46, 34)
    brackets(st, t, 4.4)
    bag(st, t, ["aam", "kela", "seb"], t_in=4.6)
    cyan_caption(st, t, 5.7, "[ ] = square brackets", 1220, 58)
    cyan_caption(st, t, 6.5, ", = items alag karo", 1310, 58)


def draw_index(st, t):
    paste(st, spaced("INDEX", NEON, 110, 0.25, inter(110, "ExtraBold")), 540, 380, pop(t - 8.1, 0.3))
    code_line(st, t, 8.3, "print(thaila[0])" if t < 10.5 else "print(thaila[-1])", 600, 54, 34)
    brackets(st, t, 0)
    bag(st, t, ["aam", "kela", "seb"], idx_t=8.5, neg=10.6 if t >= 10.6 else None,
        hi={0: 9.2} if t < 10.5 else {2: 11.2})
    out_chip(st, t, 9.4 if t < 10.5 else 11.4, '"aam"' if t < 10.5 else '"seb"')
    cyan_caption(st, t, 12.0, "Aage 0, peeche -1", 1440, 58)


CHG = 'thaila[1] = "angoor"'
FLIP_T = 14.4


def draw_change(st, t):
    paste(st, spaced("BADLO", NEON, 110, 0.25, inter(110, "ExtraBold")), 540, 380, pop(t - 13.1, 0.3))
    code_line(st, t, 13.3, CHG, 600, 52, 34)
    brackets(st, t, 0)
    bag(st, t, ["aam", "kela", "seb"], flip=(1, FLIP_T, "angoor"))
    p11.stamp(st, t, 15.2, "MUTABLE!", 540, 1230, 90, GREEN, -5)
    interview_card(st, t, 16.1)


APP = 'thaila.append("chai")'
ADD_T = 19.8
LEN_T = 21.2


def draw_append(st, t):
    paste(st, spaced("JODO", NEON, 110, 0.25, inter(110, "ExtraBold")), 540, 380, pop(t - 18.6, 0.3))
    code_line(st, t, 18.8, APP if t < LEN_T - 0.2 else "print(len(thaila))", 600, 50, 34)
    brackets(st, t, 0)
    bag(st, t, ["aam", "angoor", "seb"], add=(ADD_T, "chai"))
    if t >= LEN_T + 0.3:
        paste(st, b.big_num("4", YEL, 170), 540, 1300, pop(t - LEN_T - 0.3, 0.3))
        b.sparkle_burst(st, t, LEN_T + 0.3, 540, 1300, 12, YEL, 160)
    cyan_caption(st, t, 22.0, "Ab 4 cheezein!", 1450, 60)


def draw_quiz(st, t):
    paste(st, e13.comic("QUIZ!", e13.PINK, 150), 540, 380, pop(t - 23.1, 0.3), 1, -3)
    code_line(st, t, 23.3, "print(thaila[-2])", 600, 56, 34)
    brackets(st, t, 0)
    bag(st, t, ["aam", "angoor", "seb", "chai"], q_mark=23.9)
    paste(st, e13.comic("COMMENT KARO!", YEL, 100), 540, 1290, pop(t - 24.4, 0.3) * (1 + 0.04 * math.sin(t * 9)),
          1, 2)
    cyan_caption(st, t, 25.0, "Answer pin hoga!", 1430, 56, 440)


DRAW = {"hook": draw_hook, "syntax": draw_syntax, "index": draw_index, "change": draw_change,
        "append": draw_append, "quiz": draw_quiz}
p11.MASCOT_IN = {"syntax": 5.2, "index": 9.0, "change": 14.6, "append": 20.2, "quiz": 24.0}
p11.REACT = [(5.3, "Shopping bag!", GREEN), (9.5, "Pehla = 0", GREEN), (14.8, "Badal gaya!", GREEN),
             (20.4, "Naya item!", GREEN), (24.6, "Socho!", GREEN)]


# ------------------------------------------------------------------ frame (whip transitions)
def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return k, SCENES[k]


_FROZEN = {}


def end_frame(t):
    if not e13._end_ready:
        es.static_layer = lambda: Image.new("RGBA", (W, H))
        es.mb.wood_frame = lambda *a, **k: None
        e13._end_ready.append(1)
    fr = e14.bg14(END0 + t)
    fr.alpha_composite(es.frame(min(t * 1.25, es.DUR - 0.01)))   # end card at 1.25x -> 3.5 s
    return fr


def frame(i, t=None):
    t = i / FPS if t is None else t
    if t >= END0:
        fr = end_frame(t - END0)
    else:
        k, (s0, name) = scene_at(t)
        a = t - s0
        fr = e14.bg14(t)
        st = Image.new("RGBA", (W, H))
        DRAW[name](st, t)
        if k > 0 and a < WHIP:          # whip pan: old content slides out, new in, heavy horizontal blur
            q = ease(a / WHIP)
            key = SCENES[k - 1][1]
            if key not in _FROZEN:
                old = Image.new("RGBA", (W, H))
                DRAW[key](old, s0 - 0.001)
                _FROZEN[key] = old
            r = int(28 * math.sin(math.pi * q))
            kern = np.zeros((1, max(1, r * 2 + 1)), np.float32)
            kern[:] = 1.0 / kern.size
            for img, dx in ((_FROZEN[key], -int(W * q)), (st, int(W * (1 - q)))):
                arr = cv2.filter2D(np.asarray(img), -1, kern) if r else np.asarray(img)
                im = Image.fromarray(arr)
                if -W < dx < W:
                    fr.alpha_composite(im.crop((max(0, -dx), 0, min(W, W - dx), H)), (max(0, dx), 0))
        else:
            fr.alpha_composite(st)
            p11.draw_mascot(fr, t, name)
    fr.alpha_composite(p11.handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    for tp, amt in ((0.9, 0.06), (1.6, 0.05), (FLIP_T + 0.3, 0.04), (LEN_T + 0.3, 0.05), (23.9, 0.04)):
        e_ = t - tp
        if 0 <= e_ < 0.35:
            z = 1 + amt * math.exp(-e_ * 10)
            arr = cv2.warpAffine(arr, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for ts, amp in ((0.9, 14), (15.2, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.3:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.3)), axis=1)
    for tf in [s for s, _ in SCENES[1:]] + [END0]:
        e_ = t - tf
        if 0 <= e_ < 0.12:
            arr += (255 - arr) * 0.22 * (1 - e_ / 0.12)
    arr *= m.vignette()
    arr += cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.5
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
type_clicks, e_chime, swipe = p11.type_clicks, p11.e_chime, b.swipe


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    for k in range(16):
        P(buf, bs.key_click(500 + k), 0.05 + k * 0.06, 0.25)
    P(buf, fx.boom()[: int(0.4 * SR)], 0.1, 0.6)
    P(buf, fx.boom(), 0.9, 0.8)
    P(buf, m.e_buzz(), 0.92, 0.6)
    P(buf, fx.pop(), 1.3, 0.6)
    P(buf, fx.whoosh(0.3, 2), 1.45, 0.5)
    P(buf, e_chime(), 1.65, 0.6)
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.3, int(s0 * 9)), s0 - 0.08, 0.7)
    for t0, txt in ((3.3, SYN_CODE), (8.3, "print(thaila[0])"), (10.5, "print(thaila[-1])"), (13.3, CHG),
                    (18.8, APP), (LEN_T - 0.2, "print(len(thaila))"), (23.3, "print(thaila[-2])")):
        type_clicks(buf, t0, len(txt), 34, int(t0 * 17), 0.2)
    for t0 in (2.5, 8.1, 13.1, 18.6):
        P(buf, fx.pop(), t0, 0.5)
        P(buf, bs.note_pop(880), t0, 0.25)
    P(buf, fx.whoosh(0.25, 30), 4.4, 0.5)
    P(buf, bs.thud(), 4.62, 0.5)
    for k in range(3):
        P(buf, fx.pop(), 4.6 + 0.2 * k, 0.45)
        P(buf, bs.note_pop(523.3 * 2 ** (k * 4 / 12)), 4.6 + 0.2 * k, 0.35)
    for t0 in (5.7, 6.5, 12.0, 22.0, 25.0):
        P(buf, swipe(int(t0 * 13)), t0, 0.4)
    for k in range(3):
        P(buf, fx.pop(), 8.5 + 0.1 * k, 0.25)
    P(buf, fx.ding(), 9.2, 0.45)
    P(buf, fx.pop(), 9.4, 0.4)
    for k in range(3):
        P(buf, fx.pop(), 10.6 + 0.1 * k, 0.22)
    P(buf, fx.ding(), 11.2, 0.45)
    P(buf, fx.pop(), 11.4, 0.4)
    P(buf, fx.whoosh(0.3, 40), FLIP_T - 0.05, 0.5)
    P(buf, e_chime(), FLIP_T + 0.3, 0.6)
    P(buf, fx.boom()[: int(0.5 * SR)], 15.2, 0.5)
    P(buf, bs.thud(), 15.2, 0.4)
    P(buf, fx.whoosh(0.3, 41), 16.1, 0.45)
    P(buf, fx.pop(), 16.3, 0.4)
    P(buf, fx.whoosh(0.5, 42), ADD_T, 0.6)
    P(buf, fx.pop(), ADD_T + 0.5, 0.5)
    P(buf, e_chime(), ADD_T + 0.5, 0.5)
    P(buf, fx.boom()[: int(0.4 * SR)], LEN_T + 0.3, 0.5)
    P(buf, fx.ding(), LEN_T + 0.3, 0.5)
    P(buf, fx.riser(0.5), 22.6, 0.35)
    P(buf, fx.boom(), 23.1, 0.7)
    P(buf, fx.pop(), 23.9, 0.5)
    P(buf, fx.pop(), 24.4, 0.5)
    for tr, txt, col in p11.REACT:
        P(buf, fx.pop(), tr, 0.3)
    end = es.sfx()
    # end card runs at 1.25x: squeeze its SFX in time to match
    n = int(len(end) / 1.25)
    end = np.interp(np.linspace(0, len(end) - 1, n), np.arange(len(end)), end)
    P(buf, end, END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=1.3)
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


m.OUT, m.WORK, m.TOTAL, m.END0 = OUT, WORK, TOTAL, END0
m.frame, m.build_audio = frame, build_audio

if __name__ == "__main__":
    m.main()
