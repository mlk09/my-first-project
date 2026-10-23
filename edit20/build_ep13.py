#!/usr/bin/env python3
"""Python ki Pathshala EP 13 - break, continue, pass  (1080x1920 HD Short)

Decoded from the 5 reference stills:
  1/2  dark charcoal GRID background with floating OUTLINE TRIANGLES; huge bold white sans title with the
       keyword in colour ("break," red, "continue" orange glow); a white rounded PILL TRACK with glowing
       GREEN BALLS running round it = loop iterations; a RED 3-D WALL slams through the track (break); a
       YELLOW ball HOPS over on an arrow arc (continue = skip one step)
  3/4  black PERSPECTIVE FLOOR GRID, chunky slanted COMIC lettering: pink "BREAK" / red arrow down /
       yellow "LOOP"  -  pink "CONTINUE" / arrow / yellow "SKIP ONE STEP"
  5    VS Code style code with a blue SELECTION BAR on the running line
Ours: EP 12 look (navy, typed code, sparkles, zoom punches) with ONE background for the whole short -
navy + faint flat grid + moving perspective floor + drifting triangles + bokeh, used on every scene
INCLUDING the tricky question and the like/share/subscribe end screen. Original Hinglish content.

Usage:  python3 edit20/build_ep13.py [--preview]
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit19"))
import build_ep12 as b   # noqa: E402  EP 12: navy base, typing, sparkles, EP 11 helpers, EP 08 encoder

p11, m = b.p11, b.m
fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste, glow = m.clamp, m.ease, m.pop, m.paste, b.glow
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
inter, MONO = b.inter, b.MONO
es.NEXT = "EP 14: STRINGS"

WHITE, YEL, GREEN, RED, ORANGE, CYAN = (255, 255, 255), (255, 214, 10), (60, 225, 110), (245, 60, 75), \
    (255, 150, 40), (60, 220, 255)
PINK = (255, 105, 190)
BALL_G, BALL_Y = (70, 235, 120), (255, 225, 60)

SCENES = [(0.0, "hook"), (3.8, "brk"), (17.0, "cont"), (29.0, "pas"), (37.5, "summary"), (42.5, "tricky")]
END0 = 55.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP13_Break_Continue_Pass.mp4")
WORK = os.path.join(HERE, "work")
_C = {}


# ------------------------------------------------------------------ ONE background for the whole video
@lru_cache(None)
def flat_grid():
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for x in range(0, W + 1, 90):
        d.line((x, 0, x, H), fill=255, width=2)
    for y in range(0, H + 1, 90):
        d.line((0, y, W, y), fill=255, width=2)
    return np.asarray(im).astype(np.float32) / 255


VP = (540, 1180)                 # vanishing point of the floor


def floor_grid(t):
    im = Image.new("L", (W // 2, H // 2), 0)
    d = ImageDraw.Draw(im)
    vx, vy = VP[0] / 2, VP[1] / 2
    for k in range(-9, 10):
        d.line((vx + k * 12, vy, vx + k * 150, H / 2), fill=255, width=1)
    ph = (t * 0.6) % 1.0
    for k in range(14):
        z = (k + ph) / 14
        y = vy + (H / 2 - vy) * z ** 2.2
        d.line((0, y, W / 2, y), fill=int(255 * min(1, z * 2.5)), width=1)
    a = np.asarray(im).astype(np.float32) / 255
    a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    fade = np.clip((np.arange(H, dtype=np.float32) - VP[1]) / 500, 0, 1)[:, None]
    return a * fade


@lru_cache(None)
def tri_sprite(s, filled):
    im = Image.new("RGBA", (s * 2 + 8, s * 2 + 8))
    d = ImageDraw.Draw(im)
    c = s + 4
    pts = [(c + s * math.cos(a), c + s * math.sin(a)) for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6)]
    if filled:
        d.polygon(pts, fill=(170, 185, 210, 255))
    else:
        d.line(pts + [pts[0]], fill=(200, 210, 230, 255), width=4, joint="curve")
    return im


def bg13(t):
    a = b.navy_base().copy()
    a += flat_grid()[..., None] * np.array([18, 26, 40], np.float32)
    a += floor_grid(t)[..., None] * np.array([60, 80, 120], np.float32)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(13)
    for k in range(9):
        x0, y0, sp, s = rng.uniform(40, W - 40), rng.uniform(0, H), rng.uniform(8, 22), int(rng.uniform(12, 24))
        y = (y0 - t * sp) % (H + 80) - 40
        x = x0 + 25 * math.sin(t * 0.5 + k)
        paste(img, tri_sprite(s, k % 3 == 0), x, y, 1, 0.45, (t * rng.uniform(-30, 30) + k * 40) % 360)
    rng = np.random.default_rng(12)
    for _ in range(12):
        x0, y0, sp, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(10, 35), rng.uniform(10, 30)
        y = (y0 - t * sp) % (H + 100) - 50
        paste(img, b.bokeh_sprite(int(r)), x0 + 30 * math.sin(t * 0.4 + y0), y, 1, rng.uniform(0.06, 0.16))
    return img


# ------------------------------------------------------------------ text styles
@lru_cache(None)
def title_word(txt, col, size):
    f = inter(size, "ExtraBold")
    w = int(f.getlength(txt)) + 60
    im = Image.new("RGBA", (w, int(size * 1.35)))
    ImageDraw.Draw(im).text((w / 2, im.height / 2), txt, font=f, fill=col, anchor="mm")
    return glow(im, 12, 0.7 if col == WHITE else 1.3, col if col != WHITE else (140, 170, 255))


@lru_cache(None)
def comic(txt, col, size):
    """chunky slanted comic lettering (ref 3/4): fill + dark outline + hard drop shadow, sheared"""
    f = mb.font(os.path.join(os.path.dirname(bs.CAP), "Poppins-Black.ttf"), size)
    w, h = int(f.getlength(txt)) + 120, int(size * 1.6)
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.text((w / 2 + 10, h / 2 + 12), txt, font=f, fill=(10, 10, 20), anchor="mm", stroke_width=12,
           stroke_fill=(10, 10, 20))
    d.text((w / 2, h / 2), txt, font=f, fill=col, anchor="mm", stroke_width=10, stroke_fill=(25, 12, 35))
    sh = 0.22
    im = im.transform((w + int(h * sh), h), Image.AFFINE, (1, sh, -h * sh, 0, 1, 0), Image.BICUBIC)
    return im


def comic_card(st, t, t0, top, bottom, dur=1.8):
    """BREAK / red arrow / LOOP KHATAM - punches in, holds, then flies up and out"""
    a = t - t0
    if not 0 <= a < dur:
        return
    out = ease((a - (dur - 0.3)) / 0.3)
    dy, al = -260 * out, 1 - out
    paste(st, comic(top, PINK, 150), 540, 700 + dy, pop(a, 0.3), al, -3)
    q = ease((a - 0.3) / 0.35)
    if q > 0:
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        y0, y1 = 850 + dy, 850 + dy + 240 * q
        d.line((540, y0, 540, y1), fill=RED + (int(255 * al),), width=12)
        if q > 0.6:
            d.polygon([(540, y1 + 40), (490, y1 - 20), (590, y1 - 20)], fill=RED + (int(255 * al),))
        st.alpha_composite(glow(lay, 10, 1.0, RED))
    paste(st, comic(bottom, YEL, 120), 540, 1250 + dy, pop(a - 0.55, 0.3), al, 2)


def header(st, t, t0, word, col, sub):
    a = t - t0
    if a < 0:
        return
    paste(st, title_word(word, col, 110), 540, 330, pop(a, 0.35), 1)
    b.caption(st, t, t0 + 0.2, [(sub, (215, 225, 245))], 540, 430, 46, "SemiBold")


# ------------------------------------------------------------------ code with VS Code selection bar (ref 5)
KW = {"for", "in", "if", "break", "continue", "pass"}
PAL = {"kw": (197, 134, 220), "fn": (230, 220, 140), "num": (181, 220, 168), "id": (130, 205, 255),
       "pun": (225, 225, 230)}


def colours(line):
    cols, i = [], 0
    while i < len(line):
        ch = line[i]
        if ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            wd = line[i:j]
            c = PAL["kw"] if wd in KW else PAL["fn"] if wd in ("range", "print") else PAL["id"]
            if wd in ("break", "continue", "pass"):
                c = {"break": RED, "continue": ORANGE, "pass": CYAN}[wd]
            cols += [c] * (j - i)
            i = j
        elif ch.isdigit():
            cols.append(PAL["num"])
            i += 1
        else:
            cols.append(PAL["pun"])
            i += 1
    return cols


CS, CLH, CX = 50, 74, 110


def code_block(st, t, lines, y0, cps=26, sel=None, flash=None):
    """lines = [(t_start, text)]; sel = (line, rgb) selection bar; flash = (line, t0) keyword flash"""
    f = mb.font(MONO, CS)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if t >= lines[0][0] - 0.3:
        q = ease((t - lines[0][0] + 0.3) / 0.3)
        d.rounded_rectangle((60, y0 - 50, 1020, y0 + len(lines) * CLH + 20), 26, fill=(8, 14, 30, int(200 * q)),
                            outline=(70, 100, 160, int(200 * q)), width=3)
    if sel is not None and t >= lines[-1][0]:
        k, col = sel
        y = y0 + k * CLH
        d.rectangle((64, y - CLH / 2 + 4, 1016, y + CLH / 2 - 4), fill=col)
    st.alpha_composite(lay)
    d = ImageDraw.Draw(st)
    for k, (ts, txt) in enumerate(lines):
        if t < ts:
            continue
        n = min(len(txt), int((t - ts) * cps) + 1)
        cols, x, y = colours(txt), CX, y0 + k * CLH
        for j in range(n):
            d.text((x, y), txt[j], font=f, fill=cols[j], anchor="lm")
            x += f.getlength(txt[j])
        if n < len(txt) or (k == len(lines) - 1 and t < ts + len(txt) / cps + 0.6):
            if n < len(txt) or int(t * 2.4) % 2 == 0:
                d.rectangle((x + 3, y - 26, x + 8, y + 26), fill=WHITE)
    if flash and t >= flash[1]:
        a = t - flash[1]
        if a < 0.8:
            k = flash[0]
            txt = lines[k][1].strip()
            x0 = CX + f.getlength(lines[k][1][:len(lines[k][1]) - len(lines[k][1].lstrip())])
            im = Image.new("RGBA", (int(f.getlength(txt)) + 40, 90))
            col = colours(txt)[0]
            ImageDraw.Draw(im).text((20, 45), txt, font=f, fill=col, anchor="lm")
            paste(st, glow(im, 14, 2.0, col), x0 + im.width / 2 - 20, y0 + k * CLH, 1 + 0.25 * math.exp(-a * 6))


# ------------------------------------------------------------------ ball track (ref 1/2)
TR = (110, 960, 970, 1160)       # pill track x0, y0, x1, y1
R_T = (TR[3] - TR[1]) / 2
GATE_X = 540
V = 160.0                         # px / s


def track_len():
    return 2 * (TR[2] - TR[0] - 2 * R_T) + 2 * math.pi * R_T


def track_pos(p):
    """arc-length p measured from the gate (bottom straight, x = GATE_X) going right, counter-clockwise"""
    L = track_len()
    p %= L
    xr, xl = TR[2] - R_T, TR[0] + R_T
    yb, yt, cy = TR[3], TR[1], (TR[1] + TR[3]) / 2
    seg1 = xr - GATE_X
    if p < seg1:
        return GATE_X + p, yb
    p -= seg1
    if p < math.pi * R_T:
        a = p / R_T
        return xr + R_T * math.sin(a), cy + R_T * math.cos(a)
    p -= math.pi * R_T
    if p < xr - xl:
        return xr - p, yt
    p -= xr - xl
    if p < math.pi * R_T:
        a = p / R_T
        return xl - R_T * math.sin(a), cy - R_T * math.cos(a)
    p -= math.pi * R_T
    return xl + p, yb


@lru_cache(None)
def track_img():
    im = Image.new("RGBA", (W, H))
    ImageDraw.Draw(im).rounded_rectangle(TR, int(R_T), outline=(240, 245, 255, 255), width=8)
    return glow(im, 12, 1.0, (190, 210, 255))


@lru_cache(None)
def ball_img(col, label, dim):
    im = Image.new("RGBA", (110, 110))
    d = ImageDraw.Draw(im)
    c = tuple(int(v * (0.35 if dim else 1)) for v in col)
    d.ellipse((20, 20, 90, 90), fill=c)
    d.ellipse((34, 28, 56, 46), fill=(255, 255, 255, 90 if not dim else 30))
    if label:
        d.text((55, 57), label, font=inter(30, "Bold"), fill=(15, 40, 25) if not dim else (40, 50, 60), anchor="mm")
    return glow(im, 12, 0.0 if dim else 1.2, c)


def ball_state(t, times, stop_t=None):
    """per ball: arc position (ball k crosses the gate at times[k]); everything freezes at stop_t"""
    tt = min(t, stop_t) if stop_t is not None else t
    return [V * (tt - tk) for tk in times]


def draw_track(st, t, t_in, times, labels, stop_t=None, hop=None, ghost=None):
    """hop = ball index that jumps over (continue); ghost = gate drawn as dashed cyan (pass)"""
    a = t - t_in
    if a < 0:
        return
    al = ease(a / 0.3)
    paste(st, track_img(), W / 2, H / 2, 1, al)
    if ghost is not None and t >= ghost:
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        for y in range(TR[3] - 90, TR[3] + 70, 22):
            d.line((GATE_X, y, GATE_X, y + 12), fill=CYAN + (230,), width=7)
        st.alpha_composite(glow(lay, 8, 1.0, CYAN))
    ps = ball_state(t, times, stop_t)
    for k, p in enumerate(ps):
        if p < -(GATE_X - TR[0]) - 30:          # still waiting off the track
            continue
        x, y = track_pos(p) if p >= 0 else (GATE_X + p, TR[3])
        crossed = p >= 0
        col = BALL_G
        dim = not crossed
        if stop_t is not None and t >= stop_t and k >= len([q for q in ps if q > 0]):
            dim = True
        if hop is not None and k == hop:
            col = BALL_Y
            if 0 <= p < 330:                    # hop over on an arc
                u = p / 330
                x, y = GATE_X - 120 + 330 * u + 120 * (1 - u) * 0, TR[3] - 230 * math.sin(math.pi * u)
                x = GATE_X - 60 + 300 * u
                lay = Image.new("RGBA", (W, H))
                d = ImageDraw.Draw(lay)
                pts = [(GATE_X - 60 + 300 * v, TR[3] - 230 * math.sin(math.pi * v)) for v in np.linspace(0, 1, 30)]
                d.line(pts, fill=(255, 255, 255, 220), width=6)
                ex, ey = pts[-1]
                d.polygon([(ex + 4, ey + 6), (ex - 22, ey - 18), (ex - 26, ey + 12)], fill=WHITE)
                st.alpha_composite(lay)
            dim = p < -10
        paste(st, ball_img(col, labels[k], dim), x, y, pop(a - 0.1 - 0.04 * k, 0.3))


def wall(st, t, t0):
    """red 3-D slab slamming down through the track at the gate"""
    a = t - t0
    if a < 0:
        return
    q = ease(a / 0.18)
    y_bot = TR[3] + 70
    y_top = y_bot - 380
    drop = -700 * (1 - q)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    x, wdt, dep = GATE_X - 10, 46, 70
    front = [(x, y_top + drop + 60), (x + wdt, y_top + drop), (x + wdt, y_bot + drop - 60), (x, y_bot + drop)]
    side = [(x + wdt, y_top + drop), (x + wdt + dep, y_top + drop + 30), (x + wdt + dep, y_bot + drop - 30),
            (x + wdt, y_bot + drop - 60)]
    d.polygon(side, fill=(150, 20, 30))
    d.polygon(front, fill=(235, 45, 55))
    d.line(front + [front[0]], fill=(255, 120, 120), width=3)
    st.alpha_composite(glow(lay, 14, 0.8, RED))


def out_chips(st, t, items, y=1270):
    """items = [(t, text, colour)] -> row of glowing output chips"""
    vis = [it for it in items if t >= it[0]]
    if not vis:
        return
    n = len(items)
    gap = 130
    x0 = 590 - gap * (n - 1) / 2
    paste(st, b.big_num("Output:", (150, 170, 210), 38), 150, y, 1)
    for k, (ts, txt, col) in enumerate(items):
        if t >= ts:
            paste(st, b.big_num(txt, col, 80), x0 + k * gap, y, pop(t - ts, 0.25))
            b.sparkle_burst(st, t, ts, x0 + k * gap, y, 8, col, 80)


# ------------------------------------------------------------------ scenes
def draw_hook(st, t):
    for t0, txt, col, y in ((0.1, "break,", RED, 430), (0.4, "continue,", WHITE, 600), (0.7, "pass", CYAN, 770)):
        im = b.sweep(title_word(txt, col, 160), t, t0 + 0.9, 0.6)
        paste(st, im, 540, y, pop(t - t0, 0.35))
    times = [0.4 + 0.42 * k for k in range(-6, 3)]
    draw_track(st, t, 0.9, times, [""] * len(times), stop_t=HOOK_WALL)
    wall(st, t, HOOK_WALL)
    b.caption(st, t, 2.6, [("Loop ka ", WHITE), ("remote control", YEL), ("!", WHITE)], 540, 1430, 60)


HOOK_WALL = 2.3

BRK_CODE = [(6.0, "for num in range(1, 11):"), (7.0, "    if num == 5:"), (7.7, "        break"),
            (8.4, "    print(num)")]
BRK_T = [9.6 + 0.6 * k for k in range(10)]
BRK_STOP = BRK_T[4] - 0.08
BRK_STAMP = BRK_STOP + 0.35


def sel_for(t, times, stop=None, skip=None, pas=None):
    """VS Code selection bar position during the trace"""
    if t < times[0] - 0.35:
        return None
    if stop is not None and t >= stop:
        return (2, (150, 30, 45, 170))
    for k in range(len(times) - 1, -1, -1):
        if t >= times[k] - 0.35:
            ph = t - (times[k] - 0.35)
            if skip is not None and k == skip and ph >= 0.2:
                return (2, (160, 90, 20, 170))
            if pas is not None and k == pas and 0.15 <= ph < 0.3:
                return (2, (20, 110, 140, 170))
            return (0, (38, 79, 140, 200)) if ph < 0.15 else (1, (38, 79, 140, 200)) if ph < 0.3 else \
                (3, (38, 79, 140, 200))
    return None


def draw_brk(st, t):
    comic_card(st, t, 3.85, "BREAK", "LOOP KHATAM!")
    header(st, t, 5.7, "break", RED, "loop ko turant ROKO")
    sel = sel_for(t, BRK_T[:5], stop=BRK_STOP)
    code_block(st, t, BRK_CODE, 560, 26, sel, (2, BRK_STOP))
    draw_track(st, t, 8.9, BRK_T, [str(k + 1) for k in range(10)], stop_t=BRK_STOP)
    wall(st, t, BRK_STOP)
    out_chips(st, t, [(BRK_T[k] + 0.05, str(k + 1), GREEN) for k in range(4)], 1270)
    p11.stamp(st, t, BRK_STAMP, "LOOP KHATAM!", 420, 1490, 80, RED, -5)


CON_CODE = [(19.0, "for num in range(1, 6):"), (19.9, "    if num == 3:"), (20.6, "        continue"),
            (21.4, "    print(num)")]
CON_T = [22.4 + 0.7 * k for k in range(5)]


def draw_cont(st, t):
    comic_card(st, t, 17.05, "CONTINUE", "EK STEP SKIP!")
    header(st, t, 18.7, "continue", ORANGE, "bas yeh round SKIP")
    code_block(st, t, CON_CODE, 560, 26, sel_for(t, CON_T, skip=2), (2, CON_T[2] - 0.15))
    draw_track(st, t, 21.8, CON_T, [str(k + 1) for k in range(5)], hop=2)
    items = [(CON_T[k] + 0.05, str(k + 1), GREEN) for k in (0, 1, 3, 4)]
    out_chips(st, t, items, 1270)
    if t >= CON_T[2]:
        paste(st, b.big_num("3 skip!", ORANGE, 52), 420, 1380, pop(t - CON_T[2], 0.25))
    b.caption(st, t, 26.0, [("Loop ", WHITE), ("chalta rahega", YEL), ("!", WHITE)], 420, 1560, 54)


PAS_CODE = [(31.0, "for num in range(1, 4):"), (31.9, "    if num == 2:"), (32.6, "        pass"),
            (33.1, "    print(num)")]
PAS_T = [34.0 + 0.7 * k for k in range(3)]


def draw_pas(st, t):
    comic_card(st, t, 29.05, "PASS", "KUCH NAHI KARO")
    header(st, t, 30.7, "pass", CYAN, "khaali jagah bharne ke liye")
    code_block(st, t, PAS_CODE, 560, 28, sel_for(t, PAS_T, pas=1), (2, PAS_T[1] - 0.2))
    draw_track(st, t, 33.6, PAS_T, ["1", "2", "3"], ghost=PAS_T[1] - 0.5)
    out_chips(st, t, [(PAS_T[k] + 0.05, str(k + 1), GREEN) for k in range(3)], 1270)
    b.caption(st, t, 36.0, [("2 bhi print hua! ", WHITE), ("pass = kuch nahi", CYAN)], 420, 1500, 42)


SUM = [(38.0, "break", RED, "loop KHATAM"), (38.5, "continue", ORANGE, "ek round SKIP"),
       (39.0, "pass", CYAN, "KUCH NAHI")]
SAVE_T = 40.6


def sum_row(word, col, txt):
    key = ("sum", word)
    if key not in _C:
        im = Image.new("RGBA", (920, 170))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((20, 20, 900, 150), 30, fill=(8, 16, 40, 235), outline=col, width=6)
        d.text((60, 86), word, font=mb.font(MONO, 60), fill=col, anchor="lm")
        d.text((420, 86), "→", font=inter(60, "Bold"), fill=WHITE, anchor="lm")
        d.text((500, 86), txt, font=inter(52, "ExtraBold"), fill=WHITE, anchor="lm")
        _C[key] = glow(im, 14, 1.0, col)
    return _C[key]


def draw_summary(st, t):
    paste(st, comic("YAAD RAKHO!", YEL, 110), 540, 380, pop(t - 37.6, 0.3), 1, -2)
    for k, (t0, word, col, txt) in enumerate(SUM):
        paste(st, sum_row(word, col, txt), 540 - 200 * (1 - ease((t - t0) / 0.3)), 640 + k * 210, 1,
              ease((t - t0) / 0.25))
    p11.stamp(st, t, SAVE_T, "SAVE KAR LO!", 400, 1340, 80, YEL, -5)


TRK = [(43.6, "for i in range(1, 8):"), (44.2, "    if i % 2 == 0:"), (44.8, "        continue"),
       (45.3, "    if i == 5:"), (45.8, "        break"), (46.3, "    print(i)")]
OPTIONS = [(46.9, "A", "1 3"), (47.2, "B", "1 3 5"), (47.5, "C", "1 3 5 7")]
ANSWER = "A"
COUNT0, REVEAL = 47.9, 50.9


def option_card(letter, txt, state):
    key = ("o13", letter, state)
    if key not in _C:
        im = Image.new("RGBA", (640, 130))
        d = ImageDraw.Draw(im)
        col = (110, 150, 230) if state is None else GREEN if state else (70, 80, 100)
        d.rounded_rectangle((15, 15, 625, 115), 24, fill=(8, 16, 40, 235), outline=col, width=5)
        d.ellipse((32, 30, 102, 100), fill=col)
        d.text((67, 66), letter, font=mb.font(mb.BALOO, 44, "ExtraBold"), fill=(10, 20, 40), anchor="mm")
        d.text((130, 67), txt, font=mb.font(MONO, 50), fill=WHITE if state is not False else (120, 130, 150),
               anchor="lm")
        if state:
            d.line([(560, 66), (578, 86), (610, 44)], fill=GREEN, width=10, joint="curve")
        _C[key] = glow(im, 12, 0.9, col) if state is not False else im
    return _C[key]


def draw_tricky(st, t):
    paste(st, comic("TRICKY SAWAAL!", PINK, 104), 540, 330, pop(t - 42.7, 0.3), 1, -2)
    code_block(st, t, TRK, 520, 30)
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, option_card(letter, txt, state), 400, 1110 + k * 140, sc,
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
        paste(st, im.resize((200, 200), Image.LANCZOS), 900, 1110, 1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8))
    if t >= REVEAL + 0.4:
        b.caption(st, t, REVEAL + 0.4, [("2, 4, 6 ", WHITE), ("continue", ORANGE), (" · 5 pe ", WHITE),
                                        ("break", RED)], 470, 1560, 46)
    elif t >= COUNT0 + 0.2:
        b.caption(st, t, COUNT0 + 0.2, [("Comment karo!", YEL)], 400, 1560, 54)


DRAW = {"hook": draw_hook, "brk": draw_brk, "cont": draw_cont, "pas": draw_pas, "summary": draw_summary,
        "tricky": draw_tricky}
p11.MASCOT_IN = {"brk": 10.0, "cont": 23.0, "pas": 34.3, "summary": 39.5, "tricky": 48.2}
p11.REACT = [(BRK_STOP + 0.1, "5 aate hi STOP!", RED), (CON_T[2] + 0.1, "3 ko jump!", GREEN),
             (PAS_T[1] + 0.1, "Kuch nahi hua!", GREEN), (SAVE_T + 0.1, "Screenshot lo!", GREEN),
             (REVEAL + 0.05, "Sirf 1 aur 3!", GREEN)]


# ------------------------------------------------------------------ end screen on the SAME background
_end_ready = []


def end_frame(t):
    if not _end_ready:
        es.static_layer = lambda: Image.new("RGBA", (W, H))
        es.mb.wood_frame = lambda *a, **k: None
        _end_ready.append(1)
    fr = bg13(END0 + t)
    fr.alpha_composite(es.frame(t))
    return fr


def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return k, SCENES[k]


def frame(i):
    t = i / FPS
    if t >= END0:
        fr = end_frame(t - END0)
    else:
        k, (s0, name) = scene_at(t)
        a = t - s0
        fr = bg13(t)
        st = Image.new("RGBA", (W, H))
        DRAW[name](st, t)
        if k > 0 and a < 0.3:            # zoom-in entrance
            z = 1.12 - 0.12 * ease(a / 0.3)
            st = st.resize((int(W * z), int(H * z)), Image.BICUBIC).crop(
                (int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
            st.putalpha(st.getchannel("A").point(lambda v: int(v * ease(a / 0.3))))
        fr.alpha_composite(st)
        p11.draw_mascot(fr, t, name)
    fr.alpha_composite(p11.handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    for tp, amt in ((HOOK_WALL, 0.05), (BRK_STOP, 0.05), (REVEAL, 0.05)):
        e_ = t - tp
        if 0 <= e_ < 0.4:
            z = 1 + amt * math.exp(-e_ * 9)
            arr = cv2.warpAffine(arr, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for ts, amp in ((HOOK_WALL, 14), (BRK_STOP, 16), (REVEAL, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.35:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.35)), axis=1)
    for tf in [s for s, _ in SCENES[1:]] + [REVEAL, END0]:
        e_ = t - tf
        if 0 <= e_ < 0.15:
            arr += (255 - arr) * 0.28 * (1 - e_ / 0.15)
    arr *= m.vignette()
    arr += cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.6
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
type_clicks, e_chime, swipe = p11.type_clicks, p11.e_chime, b.swipe


def clank():
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * d0) for f0, d0 in ((180, 7), (431, 9), (1190, 14), (2390, 20)))
    return s * 0.22


def boing():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    f = 300 + 900 * tt / 0.45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4) * (1 + 0.3 * np.sin(2 * np.pi * 18 * tt)) * 0.3


def shimmer():
    n = int(0.7 * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f0 * tt) for f0 in (1568, 1976, 2349, 2794))
    return s * np.sin(np.pi * tt / 0.7) * 0.06


def roll(dur, seed):
    n = int(dur * SR)
    return fx.filt(fx.noise(n, seed), "lowpass", 600) * 0.15


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    for k, t0 in enumerate((0.1, 0.4, 0.7)):
        P(buf, fx.boom()[: int(0.4 * SR)], t0, 0.45)
        P(buf, fx.pop(), t0, 0.5)
    P(buf, roll(1.4, 3), 0.9, 0.7)
    P(buf, fx.whoosh(0.3, 4), HOOK_WALL - 0.2, 0.5)
    P(buf, fx.boom(), HOOK_WALL, 0.8)
    P(buf, clank(), HOOK_WALL, 0.8)
    P(buf, swipe(5), 2.6, 0.5)
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.45, int(s0 * 3)), s0 - 0.15, 0.55)
    for t0 in (3.85, 17.05, 29.05):          # comic cards
        P(buf, fx.boom()[: int(0.5 * SR)], t0, 0.6)
        P(buf, fx.pop(), t0, 0.5)
        P(buf, fx.whoosh(0.25, int(t0 * 7)), t0 + 0.3, 0.4)
        P(buf, fx.pop(), t0 + 0.55, 0.45)
        P(buf, fx.whoosh(0.3, int(t0 * 9)), t0 + 1.5, 0.4)
    for t0 in (5.7, 18.7, 30.7):
        P(buf, fx.pop(), t0, 0.5)
        P(buf, bs.note_pop(784), t0, 0.3)
    for code, cps in ((BRK_CODE, 26), (CON_CODE, 26), (PAS_CODE, 28), (TRK, 30)):
        for k, (ts, txt) in enumerate(code):
            type_clicks(buf, ts, len(txt.strip()), cps, int(ts * 37), 0.22)
    scale = [523.3, 587.3, 659.3, 698.5, 784.0, 880.0, 987.8, 1046.5]
    # break
    P(buf, roll(BRK_STOP - 8.9, 11), 8.9, 0.6)
    for k in range(4):
        P(buf, bs.note_pop(scale[k]), BRK_T[k], 0.45)
        P(buf, fx.pop(), BRK_T[k], 0.25)
    P(buf, fx.boom(), BRK_STOP, 0.9)
    P(buf, clank(), BRK_STOP, 1.0)
    P(buf, m.e_buzz(), BRK_STOP + 0.1, 0.5)
    P(buf, bs.thud(), BRK_STAMP, 0.5)
    # continue
    P(buf, roll(CON_T[-1] + 0.6 - 21.8, 12), 21.8, 0.6)
    for k in (0, 1, 3, 4):
        P(buf, bs.note_pop(scale[k]), CON_T[k], 0.45)
    P(buf, fx.whoosh(0.4, 21), CON_T[2] - 0.1, 0.5)
    P(buf, boing(), CON_T[2], 0.8)
    # pass
    P(buf, roll(PAS_T[-1] + 0.6 - 33.6, 13), 33.6, 0.6)
    P(buf, shimmer(), PAS_T[1] - 0.5, 0.9)
    for k in range(3):
        P(buf, bs.note_pop(scale[k]), PAS_T[k], 0.45)
    P(buf, fx.pop(), 36.0, 0.35)
    # summary
    P(buf, fx.boom()[: int(0.5 * SR)], 37.6, 0.55)
    for t0, *_r in SUM:
        P(buf, swipe(int(t0 * 10)), t0, 0.6)
        P(buf, fx.pop(), t0 + 0.15, 0.4)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.45)
    # tricky
    P(buf, fx.riser(0.6), 42.1, 0.35)
    P(buf, fx.boom(), 42.7, 0.7)
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
    for tr, txt, col in p11.REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=BRK_STOP)
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
