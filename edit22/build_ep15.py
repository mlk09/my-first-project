#!/usr/bin/env python3
"""Python ki Pathshala EP 15 - String Slicing  (1080x1920 HD Short)

No new reference: built in the EP 14 look (one background everywhere: navy + grid + moving floor +
triangles + symbol watermark; carousel slides with brand badge, n/5 counter, cyan tag pill, huge white
title with cyan underline, mac-dot code card with blue # output; swipe transitions; cheat sheet; tricky
question and end screen on the same background).
Content (original, Hinglish): PYTHON letter tiles with index 0..5 and -6..-1, s[0] / s[-1], a glowing
KNIFE cut for s[0:4] (stop not included), shortcuts s[:3] / s[3:], negative s[-3:], reverse s[::-1],
cheat sheet, tricky s[1:7:2].

Usage:  python3 edit22/build_ep15.py [--preview]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit21"))
import build_ep14 as e14   # noqa: E402  EP 14: background, slide head, code card, tiles, EP 13/12/11/08 helpers

e13, b, p11, m = e14.e13, e14.b, e14.p11, e14.m
fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste, glow = m.clamp, m.ease, m.pop, m.paste, b.glow
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
inter, MONO = b.inter, b.MONO
es.NEXT = "EP 16: LISTS"
WHITE, YEL, GREEN, RED, ORANGE, CYAN = e14.WHITE, e14.YEL, e14.GREEN, e14.RED, e14.ORANGE, e14.CYAN
TAGC = e14.TAGC

SCENES = [(0.0, "hook"), (3.6, "s1"), (12.5, "s2"), (21.5, "s3"), (30.0, "s4"), (37.5, "s5"), (45.5, "cheat"),
          (50.5, "tricky")]
END0 = 60.5
TOTAL = END0 + es.DUR
SWIPE = e14.SWIPE
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP15_String_Slicing.mp4")
WORK = os.path.join(HERE, "work")
WORD = "PYTHON"
COLS = [YEL, CYAN, GREEN, ORANGE, (255, 105, 190), RED]
STEP = 140
_C = {}


# ------------------------------------------------------------------ letter tiles with index numbers
def tx(k, n=6, step=STEP, cx=540):
    return cx - step * (n - 1) / 2 + step * k


def tiles(st, t, t0, y, *, idx_t=None, neg_t=None, hi=None, dim=None, lifts=None, cuts=None, rev=None,
          res_y=None, res_cx=470):
    """PYTHON tiles. hi = {k: (t, colour)}, dim = (t, set), lifts = [(t, [k...], cx)] -> copies fly to the
    result row, cuts = [(t, boundary index)], rev = t (reverse animation)."""
    if t < t0:
        return
    for k, ch in enumerate(WORD):
        x, yy = tx(k), y
        if rev is not None and t >= rev:
            q = ease((t - rev - 0.08 * k) / 0.7)
            x0, x1 = tx(k), tx(5 - k)
            x = x0 + (x1 - x0) * q
            yy = y - (160 if k % 2 == 0 else -160) * math.sin(math.pi * q)
        col = COLS[k]
        if hi and k in hi and t >= hi[k][0]:
            col = hi[k][1]
        al = 1.0
        if dim and t >= dim[0] and k in dim[1]:
            al = 1 - 0.65 * ease((t - dim[0]) / 0.25)
        sc = pop(t - t0 - 0.07 * k, 0.3)
        if hi and k in hi and 0 <= t - hi[k][0] < 0.4:
            sc *= 1 + 0.15 * math.sin(math.pi * (t - hi[k][0]) / 0.4)
        paste(st, e14.tile(ch, col, 110, 120), x, yy, sc, al)
        if idx_t is not None and t >= idx_t + 0.08 * k and rev is None:
            paste(st, b.big_num(str(k), (150, 190, 240), 44), x, y - 95, pop(t - idx_t - 0.08 * k, 0.25))
        if neg_t is not None and t >= neg_t + 0.08 * (5 - k) and rev is None:
            paste(st, b.big_num(str(k - 6), (255, 150, 150), 40), x, y + 95, pop(t - neg_t - 0.08 * (5 - k), 0.25))
    for tc, bnd in cuts or []:
        a = t - tc
        if a < 0:
            continue
        xb = tx(bnd) - STEP / 2
        q = ease(a / 0.18)
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        d.line((xb, y - 120, xb, y - 120 + 240 * q), fill=(255, 255, 255, 255), width=7)
        if a < 0.35:
            d.polygon([(xb - 14, y - 130 + 240 * q - 40), (xb + 14, y - 130 + 240 * q - 40), (xb, y - 120 + 240 * q)],
                      fill=(255, 255, 255, 255))
        st.alpha_composite(glow(lay, 10, 1.4, CYAN))
    for tl, ks, cx in lifts or []:
        for j, k in enumerate(ks):
            a = t - tl - 0.12 * j
            if a < 0:
                continue
            q = ease(a / 0.45)
            x1 = cx - 125 * (len(ks) - 1) / 2 + 125 * j
            x = tx(k) + (x1 - tx(k)) * q
            yy = y + (res_y - y) * q - 120 * math.sin(math.pi * q)
            paste(st, e14.tile(WORD[k], GREEN, 100, 110), x, yy, 1)
            if q >= 1:
                b.sparkle_burst(st, t, tl + 0.12 * j + 0.45, x, yy, 6, GREEN, 70)


def slide(st, t, t0, tag, title, n, code, size=48, lh=80):
    e14.slide_head(st, t, t0 + 0.1, tag, title, n)
    e14.code_card(st, t, code, 640, size, lh)


# ------------------------------------------------------------------ scenes
def draw_hook(st, t):
    paste(st, e13.title_word("String", WHITE, 150), 540, 420, pop(t - 0.1, 0.35))
    paste(st, b.sweep(e13.title_word("Slicing", (255, 70, 80), 170), t, 1.0, 0.6), 540, 600, pop(t - 0.3, 0.35))
    paste(st, b.big_num("s[ : ]", GREEN, 150), 540, 800, pop(t - 0.6, 0.35))
    tiles(st, t, 1.0, 1100, cuts=[(2.0, 2), (2.3, 4)], hi={2: (2.4, GREEN), 3: (2.4, GREEN)}, dim=(2.4, {0, 1, 4, 5}))
    b.caption(st, t, 2.6, [("String ko ", WHITE), ("pizza", YEL), (" ki tarah kaato!", WHITE)], 540, 1330, 58)


S1_CODE = [(4.6, 's = "PYTHON"'), (5.4, "print(s[0])"), (6.2, '# "P"'), (6.8, "print(s[-1])"), (7.6, '# "N"')]


def draw_s1(st, t):
    slide(st, t, 3.6, "INDEX", "s[0]   s[-1]", 1, S1_CODE, 46, 64)
    tiles(st, t, 4.8, 1180, idx_t=5.2, neg_t=7.0, hi={0: (6.2, YEL), 5: (7.6, (255, 105, 190))})
    b.caption(st, t, 8.6, [("Aage se ", WHITE), ("0", YEL), (", peeche se ", WHITE), ("-1", (255, 120, 170)),
                           ("!", WHITE)], 390, 1440, 46)


S2_CODE = [(13.5, 's = "PYTHON"'), (14.3, "print(s[0:4])"), (16.6, '# "PYTH"')]


def draw_s2(st, t):
    slide(st, t, 12.5, "SLICE", "s[start:stop]", 2, S2_CODE)
    tiles(st, t, 13.8, 1110, idx_t=14.2, cuts=[(15.3, 0), (15.7, 4)], dim=(16.0, {4, 5}),
          lifts=[(16.2, [0, 1, 2, 3], 470)], res_y=1320)
    if t >= 16.0:
        paste(st, b.big_num("stop", RED, 40), tx(4), 1215, pop(t - 16.0, 0.25))
    b.caption(st, t, 17.6, [("Index ", WHITE), ("4", YEL), (" shamil NAHI!", WHITE)], 390, 1470, 46)


S3_CODE = [(22.5, 's = "PYTHON"'), (23.2, "print(s[:3])"), (24.2, '# "PYT"'), (25.4, "print(s[3:])"),
           (26.4, '# "HON"')]


def draw_s3(st, t):
    slide(st, t, 21.5, "SHORTCUT", "s[:3]   s[3:]", 3, S3_CODE, 46, 64)
    tiles(st, t, 22.8, 1180, idx_t=23.0, cuts=[(23.8, 3)], hi={k: (24.2, GREEN) for k in range(3)},
          lifts=[(24.2, [0, 1, 2], 260), (26.4, [3, 4, 5], 680)], res_y=1360)
    b.caption(st, t, 27.4, [("Khaali", YEL), (" = shuru se / end tak", WHITE)], 390, 1490, 46)


S4_CODE = [(31.0, 's = "PYTHON"'), (31.7, "print(s[-3:])"), (33.0, '# "HON"')]


def draw_s4(st, t):
    slide(st, t, 30.0, "ULTA INDEX", "s[-3:]", 4, S4_CODE)
    tiles(st, t, 31.2, 1110, neg_t=31.5, cuts=[(32.4, 3)], dim=(32.8, {0, 1, 2}),
          lifts=[(33.0, [3, 4, 5], 470)], res_y=1330)
    b.caption(st, t, 34.2, [("Last ", WHITE), ("3", YEL), (" letters, bina ginti ke!", WHITE)], 390, 1470, 46)


S5_CODE = [(38.5, 's = "PYTHON"'), (39.2, "print(s[::-1])"), (40.6, '# "NOHTYP"')]
REV_T = 40.6


def draw_s5(st, t):
    slide(st, t, 37.5, "MAGIC", "s[::-1]", 5, S5_CODE)
    tiles(st, t, 38.8, 1150, rev=REV_T)
    if t >= REV_T + 1.0:
        b.sparkle_burst(st, t, REV_T + 1.0, 540, 1150, 14, YEL, 420)
    b.caption(st, t, 41.8, [("String ", WHITE), ("ULTA", YEL), (" ho gaya!", WHITE)], 440, 1420, 60)


CHEAT = [(46.3, 's[0]      --> "P"'), (46.7, 's[-1]     --> "N"'), (47.1, 's[0:4]    --> "PYTH"'),
         (47.5, 's[:3]     --> "PYT"'), (47.9, 's[3:]     --> "HON"'), (48.3, 's[::-1]   --> "NOHTYP"')]
SAVE_T = 49.1


def draw_cheat(st, t):
    paste(st, e13.comic("CHEAT SHEET", e13.PINK, 110), 540, 360, pop(t - 45.6, 0.3), 1, -2)
    paste(st, b.big_num('s = "PYTHON"', (255, 190, 120), 54), 540, 520, pop(t - 45.9, 0.3))
    x0, y0, y1 = 70, 600, 600 + 80 + len(CHEAT) * 80
    q = ease((t - 46.0) / 0.3)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, 1010, y1), 22, fill=(14, 16, 22, int(235 * q)), outline=(70, 75, 90, int(200 * q)),
                        width=3)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((100 + 34 * k, y0 + 24, 120 + 34 * k, y0 + 44), fill=c + (int(255 * q),))
    st.alpha_composite(lay)
    f, fn = mb.font(MONO, 44), mb.font(bs.MONO_R, 32)
    for k, (ts, txt) in enumerate(CHEAT):
        if t < ts:
            continue
        y = y0 + 80 + k * 80 + 30
        im = Image.new("RGBA", (930, 80))
        dd = ImageDraw.Draw(im)
        dd.text((32, 40), str(k + 1), font=fn, fill=(110, 115, 130), anchor="mm")
        code, res = txt.split("-->")
        dd.text((75, 40), code.rstrip(), font=f, fill=(120, 220, 255), anchor="lm")
        dd.text((75 + f.getlength(code), 40), "-->", font=f, fill=(170, 175, 190), anchor="lm")
        dd.text((75 + f.getlength(code + "--> "), 40), res.strip(), font=f, fill=WHITE, anchor="lm")
        paste(st, im, x0 + 470 + 60 * (1 - ease((t - ts) / 0.25)), y, 1, ease((t - ts) / 0.2))
    p11.stamp(st, t, SAVE_T, "SAVE KAR LO!", 400, 1360, 80, YEL, -5)


TRK = [(51.6, 's = "PATHSHALA"'), (52.4, "print(s[1:7:2])")]
TWORD = "PATHSHALA"
OPTIONS = [(54.6, "A", '"AHH"'), (54.9, "B", '"ATHS"'), (55.2, "C", '"AHL"')]
ANSWER = "A"
COUNT0, REVEAL = 56.0, 59.0


def draw_tricky(st, t):
    paste(st, e13.comic("TRICKY SAWAAL!", e13.PINK, 104), 540, 330, pop(t - 50.7, 0.3), 1, -2)
    e14.code_card(st, t, TRK, 440, 48, 76)
    for k, ch in enumerate(TWORD):
        x = 540 - 105 * 4 + 105 * k
        t0 = 53.0 + 0.05 * k
        if t < t0:
            continue
        col = (90, 120, 180)
        if t >= REVEAL + 0.3 and k in (1, 3, 5):
            col = GREEN
        sc = pop(t - t0, 0.25)
        if t >= REVEAL + 0.3 and k in (1, 3, 5) and t - REVEAL - 0.3 < 0.4:
            sc *= 1 + 0.2 * math.sin(math.pi * (t - REVEAL - 0.3) / 0.4)
        paste(st, e14.tile(ch, col, 86, 96), x, 790, sc)
        paste(st, b.big_num(str(k), (150, 190, 240), 34), x, 870, pop(t - t0 - 0.2, 0.25))
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, e13.option_card(letter, txt, state), 400, 1010 + k * 140, sc,
              1 if (t < REVEAL or letter == ANSWER) else 0.55)
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (200 * S, 200 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 190 * S, 190 * S), fill=(8, 14, 40, 230), outline=(60, 70, 110), width=12 * S)
        d.arc((10 * S, 10 * S, 190 * S, 190 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)), fill=YEL,
              width=12 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((100 * S, 104 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 100 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        paste(st, im.resize((200, 200), Image.LANCZOS), 900, 1010, 1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8))
    if t >= REVEAL + 0.4:
        b.caption(st, t, REVEAL + 0.4, [("Index ", WHITE), ("1, 3, 5", YEL), (" → A H H", WHITE)], 390, 1480, 46)
    elif t >= COUNT0 + 0.2:
        b.caption(st, t, COUNT0 + 0.2, [("Comment karo!", YEL)], 400, 1480, 54)


DRAW = {"hook": draw_hook, "s1": draw_s1, "s2": draw_s2, "s3": draw_s3, "s4": draw_s4, "s5": draw_s5,
        "cheat": draw_cheat, "tricky": draw_tricky}
p11.MASCOT_IN = {"s1": 8.0, "s2": 16.8, "s3": 24.6, "s4": 33.3, "s5": 41.0, "cheat": 48.5, "tricky": 56.3}
p11.REACT = [(9.0, "0 aur -1!", GREEN), (17.8, "Skip!", GREEN), (34.4, "Smart!", GREEN),
             (41.9, "Magic!", GREEN), (SAVE_T + 0.1, "Save!", GREEN), (REVEAL + 0.05, "A sahi!", GREEN)]


# ------------------------------------------------------------------ frame (carousel swipe, one background)
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
    fr.alpha_composite(es.frame(t))
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
        if k > 0 and a < SWIPE:
            q = ease(a / SWIPE)
            key = SCENES[k - 1][1]
            if key not in _FROZEN:
                old = Image.new("RGBA", (W, H))
                DRAW[key](old, s0 - 0.001)
                _FROZEN[key] = old
            old = _FROZEN[key]
            dx = int(W * q)
            r = int(10 * math.sin(math.pi * q))
            if dx < W:
                fr.alpha_composite((old.filter(ImageFilter.BoxBlur(r)) if r else old).crop((dx, 0, W, H)), (0, 0))
            if dx > 0:
                fr.alpha_composite((st.filter(ImageFilter.BoxBlur(r)) if r else st).crop((0, 0, dx, H)), (W - dx, 0))
        else:
            fr.alpha_composite(st)
            p11.draw_mascot(fr, t, name)
    fr.alpha_composite(p11.handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    for tp, amt in ((2.0, 0.04), (REV_T + 0.9, 0.04), (REVEAL, 0.05)):
        e_ = t - tp
        if 0 <= e_ < 0.4:
            z = 1 + amt * math.exp(-e_ * 9)
            arr = cv2.warpAffine(arr, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for ts, amp in ((2.0, 8), (15.7, 6), (REVEAL, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.3:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.3)), axis=1)
    for tf in (SCENES[1][0], 45.5, 50.5, REVEAL, END0):
        e_ = t - tf
        if 0 <= e_ < 0.15:
            arr += (255 - arr) * 0.25 * (1 - e_ / 0.15)
    arr *= m.vignette()
    arr += cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.6
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
type_clicks, e_chime, swipe = p11.type_clicks, p11.e_chime, b.swipe


def knife():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    sw = fx.filt(fx.noise(n, 21), "highpass", 3000) * np.exp(-tt * 12) * 0.5
    ring = (np.sin(2 * np.pi * 3520 * tt) + 0.6 * np.sin(2 * np.pi * 5280 * tt)) * np.exp(-tt * 9) * 0.12
    return sw + ring


def swirl():
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    f = 300 + 1500 * tt
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt) * 0.12 + fx.whoosh(1.0, 61)[:n] * 0.5


def code_sfx(buf, code, cps=28, seed=0):
    for ts, txt in code:
        if txt.startswith("#"):
            fx.place(buf, fx.pop(), ts, 0.45)
            fx.place(buf, bs.note_pop(1046.5), ts, 0.3)
        else:
            type_clicks(buf, ts, len(txt), cps, seed + int(ts * 31), 0.22)


def lift_sfx(buf, tl, n, base=523.3):
    for j in range(n):
        fx.place(buf, fx.whoosh(0.18, int(tl * 10) + j), tl + 0.12 * j, 0.25)
        fx.place(buf, bs.note_pop(base * 2 ** (j * 2 / 12)), tl + 0.12 * j + 0.45, 0.4)


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.1, 0.6)
    P(buf, fx.pop(), 0.3, 0.5)
    P(buf, swipe(1), 1.0, 0.5)
    for k in range(6):
        P(buf, fx.pop(), 1.0 + 0.07 * k, 0.25)
    for tc in (2.0, 2.3):
        P(buf, knife(), tc, 0.9)
    P(buf, fx.ding(), 2.4, 0.35)
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.4, int(s0 * 5)), s0 - 0.05, 0.6)
        P(buf, swipe(int(s0 * 7)), s0, 0.4)
    for code in (S1_CODE, S2_CODE, S3_CODE, S4_CODE, S5_CODE, TRK):
        code_sfx(buf, code)
    for t0 in (3.7, 12.6, 21.6, 30.1, 37.6):
        P(buf, fx.pop(), t0 + 0.25, 0.5)
    # s1
    for k in range(6):
        P(buf, bs.note_pop(523.3 * 2 ** (k * 2 / 12)), 5.2 + 0.08 * k, 0.25)
        P(buf, bs.note_pop(784 * 2 ** (-k * 2 / 12)), 7.0 + 0.08 * k, 0.2)
    P(buf, fx.ding(), 6.2, 0.35)
    P(buf, fx.ding(), 7.6, 0.35)
    # s2
    for tc in (15.3, 15.7):
        P(buf, knife(), tc, 1.0)
    P(buf, m.e_buzz()[: int(0.2 * SR)], 16.0, 0.4)
    lift_sfx(buf, 16.2, 4)
    # s3
    P(buf, knife(), 23.8, 0.9)
    lift_sfx(buf, 24.2, 3)
    lift_sfx(buf, 26.4, 3, 659.3)
    # s4
    for k in range(6):
        P(buf, bs.note_pop(784 * 2 ** (-k * 2 / 12)), 31.5 + 0.08 * k, 0.2)
    P(buf, knife(), 32.4, 0.9)
    lift_sfx(buf, 33.0, 3)
    # s5
    P(buf, swirl(), REV_T, 0.9)
    P(buf, e_chime(), REV_T + 0.95, 0.6)
    # cheat
    P(buf, fx.boom()[: int(0.4 * SR)], 45.6, 0.5)
    for k, (ts, _txt) in enumerate(CHEAT):
        P(buf, swipe(int(ts * 11)), ts, 0.4)
        P(buf, bs.note_pop(587.3 * 2 ** (k * 2 / 12)), ts, 0.25)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.45)
    # tricky
    P(buf, fx.riser(0.6), 50.1, 0.35)
    P(buf, fx.boom(), 50.7, 0.7)
    for k in range(9):
        P(buf, fx.pop(), 53.0 + 0.05 * k, 0.15)
    for t0, *_r in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    tt = COUNT0
    while tt < REVEAL - 0.05:
        n2 = int(0.05 * SR)
        x = np.arange(n2) / SR
        P(buf, np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 90) * 0.5, tt, 0.6)
        tt += 0.5
    P(buf, fx.ding(), REVEAL, 0.7)
    P(buf, e_chime(), REVEAL + 0.05, 0.6)
    for k in range(3):
        P(buf, bs.note_pop(659.3 * 2 ** (k * 4 / 12)), REVEAL + 0.3 + 0.1 * k, 0.35)
    for tr, txt, col in p11.REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=45.5)
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
