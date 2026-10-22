#!/usr/bin/env python3
"""Python ki Pathshala EP 11 - while loop  (1080x1920 Short, works without a voice-over)

Decoded from "Python while loop" (@kushalgyan, 178 s, 720x1280):
  * NEON TUBE title boxes: white glowing rounded outline, cyan glowing bold text, dark see-through fill,
    sliding in from the left with a fade
  * WHITE caption cards with dark bold text that TYPE ON character by character
  * CYAN filled headline boxes (navy text) + navy boxes with a cyan outline (white text), also typed
  * code shown in a phone editor inside a glowing white frame, with touch ripples
  * SQUASH transition: the card collapses vertically into a line and vanishes
  * magenta radial-gradient grid background, red handle tag bottom-left, voice + quiet bed, no SFX
Ours: the same text-box language and transitions on a LIGHT NEON COBALT motion grid (EP 07/08 grid),
original Hinglish content (bottle-filling analogy, live loop tracer, infinite-loop trap, quiz), full SFX.

Usage:  python3 edit18/build_ep11.py [--preview]
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit15"))
import build_ep08 as m   # noqa: E402  EP 08: helpers + light neon cobalt motion grid + encoder

fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste = m.clamp, m.ease, m.pop, m.paste
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
MONO = bs.MONO
es.NEXT = "EP 12: FOR + RANGE()"

CYAN, NAVY, INKD = (0, 229, 255), (8, 18, 58), (22, 24, 40)
YEL, GREEN, RED, WHITE, BLUE = (255, 214, 10), (40, 210, 110), (245, 60, 75), (255, 255, 255), (30, 100, 235)
PINK = (255, 90, 160)

SCENES = [(0.0, "hook"), (3.5, "loopdef"), (9.0, "analogy"), (19.0, "syntax"), (27.0, "code"), (41.0, "trap"),
          (48.0, "quiz")]
END0 = 56.5
TOTAL = END0 + es.DUR
SQ = 0.28                    # squash-transition length
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP11_While_Loop.mp4")
WORK = os.path.join(HERE, "work")
_C = {}


# ------------------------------------------------------------------ glow helper
def glow(im, r=10, boost=1.8, col=None):
    src = im
    if col is not None:
        src = Image.new("RGBA", im.size, col + (0,))
        src.putalpha(im.getchannel("A"))
    g = src.filter(ImageFilter.GaussianBlur(r))
    g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * boost))))
    out = Image.new("RGBA", im.size)
    out.alpha_composite(g)
    out.alpha_composite(im)
    return out


def bfont(size, var="ExtraBold"):
    return mb.font(mb.BALOO, size, var)


# ------------------------------------------------------------------ reference text styles (our build)
@lru_cache(None)
def neon_box(text, size, col=CYAN):
    """white neon-tube outline + glowing coloured text on a dark see-through fill"""
    f = bfont(size)
    tw = f.getlength(text)
    M, padx = 40, int(size * 0.45)
    w, h = int(tw + 2 * padx), int(size * 1.45)
    im = Image.new("RGBA", (w + 2 * M, h + 2 * M))
    box = Image.new("RGBA", im.size)
    d = ImageDraw.Draw(box)
    d.rounded_rectangle((M, M, M + w, M + h), int(size * 0.28), fill=(6, 10, 40, 150))
    tube = Image.new("RGBA", im.size)
    ImageDraw.Draw(tube).rounded_rectangle((M, M, M + w, M + h), int(size * 0.28), outline=(255, 255, 255, 255),
                                           width=max(5, size // 18))
    txt = Image.new("RGBA", im.size)
    ImageDraw.Draw(txt).text((M + w / 2, M + h / 2 + size * 0.04), text, font=f, fill=col + (255,), anchor="mm")
    im.alpha_composite(box)
    im.alpha_composite(glow(tube, 12, 1.6, (200, 225, 255)))
    im.alpha_composite(glow(txt, 9, 1.15, col))
    core = Image.new("RGBA", im.size)
    pale = tuple(int(c + (255 - c) * 0.45) for c in col)
    ImageDraw.Draw(core).text((M + w / 2, M + h / 2 + size * 0.04), text, font=f, fill=pale + (255,), anchor="mm")
    im.alpha_composite(core)
    return im


def neon_title(st, t, t0, text, cx, cy, size, col=CYAN):
    """slide in from the left with a fade, then neon flicker on, then gentle breathing"""
    a = t - t0
    if a < 0:
        return
    im = neon_box(text, size, col)
    p = ease(a / 0.3)
    flick = 0.3 if (0.32 < a < 0.38 or 0.46 < a < 0.5) else 1.0
    breathe = 0.93 + 0.07 * math.sin(t * 5 + cx)
    paste(st, im, cx - 140 * (1 - p), cy, 1.0, p * flick * (breathe if a > 0.6 else 1))


def _layout(lines, size):
    f = bfont(size, "Bold")
    return f, [sum(f.getlength(s) for s, _ in ln) for ln in lines]


@lru_cache(None)
def typed_box(lines, n, style, size):
    """lines = ((("text", colour), ...), ...); n = characters revealed; style white | navy | cyan"""
    f, widths = _layout(lines, size)
    padx, pady, lh = int(size * 0.55), int(size * 0.45), int(size * 1.32)
    w, h = int(max(widths) + 2 * padx), int(len(lines) * lh + 2 * pady - (lh - size * 1.1))
    M = 30
    im = Image.new("RGBA", (w + 2 * M, h + 2 * M))
    d = ImageDraw.Draw(im)
    if style == "white":
        d.rectangle((M + 6, M + 8, M + w + 6, M + h + 8), fill=(0, 0, 30, 120))
        d.rectangle((M, M, M + w, M + h), fill=(255, 255, 255, 255))
    elif style == "cyan":
        d.rectangle((M, M, M + w, M + h), fill=CYAN + (255,))
    else:
        d.rectangle((M, M, M + w, M + h), fill=(8, 16, 56, 225))
    if style != "white":
        im = glow(im, 12, 1.2, CYAN if style == "navy" else (120, 240, 255))
        d = ImageDraw.Draw(im)
        if style == "navy":
            d.rectangle((M, M, M + w, M + h), outline=CYAN + (255,), width=5)
    left = n
    for k, ln in enumerate(lines):
        x, y = M + padx, M + pady + k * lh + size * 0.52
        for s, col in ln:
            if left <= 0:
                break
            part = s[:left]
            d.text((x, y), part, font=f, fill=col, anchor="lm")
            x += f.getlength(part)
            left -= len(s)
    return im


def total_chars(lines):
    return sum(len(s) for ln in lines for s, _ in ln)


def type_box(st, t, t0, lines, cx, cy, style="white", size=48, cps=30):
    a = t - t0
    if a < 0:
        return
    n = int(max(0, a - 0.18) * cps) if cps else 10 ** 6
    n = min(n, total_chars(lines))
    im = typed_box(lines, n, style, size)
    s = 0.86 + 0.14 * ease(a / 0.2)
    paste(st, im, cx, cy, s, ease(a / 0.15))


def stamp(st, t, t0, text, cx, cy, size, col, rot=-6):
    a = t - t0
    if a < 0:
        return
    key = ("stamp", text, size, col)
    if key not in _C:
        f = bfont(size)
        w = int(f.getlength(text)) + 60
        im = Image.new("RGBA", (w, int(size * 1.6)))
        ImageDraw.Draw(im).text((w / 2, im.height / 2), text, font=f, fill=col, anchor="mm", stroke_width=9,
                                stroke_fill=(20, 10, 30))
        _C[key] = glow(im, 10, 1.0, col)
    sc = 1.6 - 0.6 * ease(a / 0.18) if a < 0.18 else 1 + 0.05 * math.exp(-(a - 0.18) * 8)
    paste(st, _C[key], cx, cy, sc, ease(a / 0.1), rot)


def chip(text, col):
    key = ("chip", text, col)
    if key not in _C:
        f = mb.font(MONO, 50)
        w = int(f.getlength(text)) + 50
        im = Image.new("RGBA", (w + 40, 130))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((20, 20, 20 + w, 110), 20, fill=(8, 14, 44), outline=col, width=5)
        d.text((20 + w / 2, 66), text, font=f, fill=col, anchor="mm")
        _C[key] = glow(im, 10, 1.2, col)
    return _C[key]


def pointer(st, t, t0, x, y, col=WHITE):
    """chunky arrow pointing UP at (x, y), bouncing (reference uses white arrows on the headline)"""
    a = t - t0
    if a < 0:
        return
    s = pop(a, 0.25)
    b = 14 * abs(math.sin(a * 6))
    lay = Image.new("RGBA", (120, 150))
    d = ImageDraw.Draw(lay)
    d.polygon([(60, 8), (110, 62), (78, 62), (78, 140), (42, 140), (42, 62), (10, 62)], fill=col,
              outline=(10, 20, 60), width=4)
    paste(st, glow(lay, 8, 1.0, CYAN), x, y + 75 + b, s)


def ripple(st, t, t0, x, y):
    a = t - t0
    if not 0 <= a < 0.6:
        return
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    r = 20 + 90 * ease(a / 0.6)
    al = int(220 * (1 - a / 0.6))
    d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, al), width=6)
    d.ellipse((x - 24, y - 24, x + 24, y + 24), fill=(255, 255, 255, int(al * 0.8)))
    st.alpha_composite(lay)


# ------------------------------------------------------------------ code editor (glowing white frame)
KWS = {"while", "if", "else", "True", "False", "and", "or", "not"}


def dcolours(line):
    cols, i = [], 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            j = line.find('"', i + 1)
            j = len(line) if j < 0 else j + 1
            cols += [(195, 232, 141)] * (j - i)
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            wd = line[i:j]
            c = (220, 130, 255) if wd in KWS else (110, 180, 255) if wd == "print" else (235, 240, 250)
            cols += [c] * (j - i)
            i = j
        elif ch.isdigit():
            cols.append((255, 160, 90))
            i += 1
        else:
            cols.append((140, 220, 255) if ch in "<=>+-:" else (235, 240, 250))
            i += 1
    return cols


ED_X0, ED_X1, LH, CS = 70, 1010, 80, 50


def editor(st, t, t0, y0, code, cps=20, hl=None, strike=None, run_t=None):
    """code = [(t_start, text)], hl = (line, colour), strike = (line, t_start)"""
    a = t - t0
    if a < 0:
        return
    n = len(code)
    y1 = y0 + 76 + n * LH + 26
    im = Image.new("RGBA", (ED_X1 - ED_X0 + 80, y1 - y0 + 80))
    d = ImageDraw.Draw(im)
    X0, Y0, X1, Y1 = 40, 40, im.width - 40, im.height - 40
    frame_l = Image.new("RGBA", im.size)
    ImageDraw.Draw(frame_l).rounded_rectangle((X0, Y0, X1, Y1), 30, outline=(255, 255, 255, 255), width=7)
    d.rounded_rectangle((X0, Y0, X1, Y1), 30, fill=(13, 15, 24, 245))
    im.alpha_composite(glow(frame_l, 14, 1.4, (215, 230, 255)))
    d = ImageDraw.Draw(im)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((X0 + 30 + 34 * k, Y0 + 26, X0 + 52 + 34 * k, Y0 + 48), fill=c)
    d.text((X0 + 150, Y0 + 38), "main.py", font=bfont(30, "Bold"), fill=(150, 160, 190), anchor="lm")
    rb = (X1 - 170, Y0 + 14, X1 - 26, Y0 + 62)
    pressed = run_t is not None and 0 <= t - run_t < 0.25
    d.rounded_rectangle(rb, 14, fill=(30, 170, 90) if not pressed else (90, 240, 150))
    d.text(((rb[0] + rb[2]) / 2, (rb[1] + rb[3]) / 2 + 1), "▶ Run", font=bfont(30), fill=WHITE, anchor="mm")
    d.line((X0 + 4, Y0 + 72, X1 - 4, Y0 + 72), fill=(40, 46, 66), width=2)
    f, fn = mb.font(MONO, CS), mb.font(MONO, 34)
    for k, (ts, txt) in enumerate(code):
        ly = Y0 + 76 + 16 + k * LH + LH / 2
        if hl and hl[0] == k:
            d.rounded_rectangle((X0 + 70, ly - LH / 2 + 6, X1 - 16, ly + LH / 2 - 6), 10, fill=hl[1])
        d.text((X0 + 44, ly), str(k + 1), font=fn, fill=(90, 98, 125), anchor="mm")
        if t < ts:
            continue
        nch = min(len(txt), int((t - ts) * cps) + 1)
        cols, x = dcolours(txt), X0 + 90
        for j in range(nch):
            d.text((x, ly + 2), txt[j], font=f, fill=cols[j], anchor="lm")
            x += f.getlength(txt[j])
        if nch < len(txt):
            d.rectangle((x + 2, ly - 24, x + 6, ly + 24), fill=CYAN)
        if strike and strike[0] == k and t >= strike[1]:
            q = ease((t - strike[1]) / 0.35)
            x_end = X0 + 90 + f.getlength(txt)
            sx = X0 + 90 + f.getlength(txt) - len(txt.lstrip()) * f.getlength("a")
            d.line((sx - 8, ly, sx - 8 + (x_end - sx + 16) * q, ly), fill=RED, width=8)
    paste(st, im, (ED_X0 + ED_X1) / 2, (y0 + y1) / 2, 0.9 + 0.1 * ease(a / 0.3), ease(a / 0.2))


def ed_line_y(y0, k):
    return y0 + 76 + 16 + k * LH + LH / 2


def output_panel(st, t, t0, y0, rows, lines, col=(235, 240, 250), scroll=0.0, alarm=0.0):
    """rows = visible rows; lines = list of (t_appear, text)"""
    a = t - t0
    if a < 0:
        return
    h = 70 + rows * 62 + 20
    im = Image.new("RGBA", (ED_X1 - ED_X0, h))
    d = ImageDraw.Draw(im)
    oc = tuple(int(70 + (245 - 70) * alarm) if i == 0 else int(80 * (1 - alarm) + 60 * alarm) for i in range(3))
    d.rounded_rectangle((0, 0, im.width - 1, h - 1), 24, fill=(6, 8, 14, 240), outline=oc, width=4)
    d.text((30, 36), "Output", font=bfont(34, "Bold"), fill=(150, 160, 190), anchor="lm")
    vis = [txt for ts, txt in lines if t >= ts]
    f = mb.font(MONO, 48)
    body = Image.new("RGBA", (im.width - 40, rows * 62))
    bd = ImageDraw.Draw(body)
    start = max(0, len(vis) - rows)
    off = scroll % 1.0 * 62 if len(vis) > rows else 0
    for k, txt in enumerate(vis[start:]):
        bd.text((20, k * 62 + 31 - off), txt, font=f, fill=col, anchor="lm")
    im.alpha_composite(body, (20, 72))
    paste(st, im, (ED_X0 + ED_X1) / 2, y0 + h / 2, 0.92 + 0.08 * ease(a / 0.25), ease(a / 0.2))


def pill(st, t, t0, text, col, cx, cy, size=40):
    if t < t0:
        return
    f = mb.font(MONO, size)
    w = int(f.getlength(text)) + 56
    im = Image.new("RGBA", (w, int(size * 1.75)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, im.height - 3), 18, fill=col)
    d.text((w / 2, im.height / 2 + 1), text, font=f, fill=WHITE, anchor="mm")
    paste(st, im, cx, cy, pop(t - t0, 0.25))


def loop_arrow(st, t, t_on, ya, yb, x=900, col=YEL):
    """curved arrow on the editor's right edge from line yb back up to ya (pulses when the loop jumps back)"""
    if t < t_on:
        return
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    r = (yb - ya) / 2
    d.arc((x - r * 0.55, ya, x + r * 0.55, yb), -90, 90, fill=col + (255,), width=8)
    d.polygon([(x - 4, ya - 16), (x - 4, ya + 16), (x - 34, ya)], fill=col)
    st.alpha_composite(glow(lay, 8, 1.2, col))


# ------------------------------------------------------------------ bottle (analogy)
BOT = (330, 830, 1340)        # cx, top, bottom
FILL = [(11.0, 0.25), (12.0, 0.5), (13.0, 0.75), (14.0, 1.0)]
STOP_T = 14.6


def level_at(t):
    lv = 0.0
    for ts, v in FILL:
        if t >= ts:
            lv = (v - 0.25) + 0.25 * ease((t - ts) / 0.55)
    return lv


def draw_bottle(st, t, t0):
    a = t - t0
    if a < 0:
        return
    cx, top, bot = BOT
    bw = 300
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    lv = level_at(t)
    body_top = top + 150
    wy = bot - (bot - body_top) * lv
    if lv > 0:
        wl = Image.new("RGBA", (W, H))
        wd = ImageDraw.Draw(wl)
        pts = [(cx - bw / 2 + 8, bot - 8)]
        for k in range(41):
            xx = cx - bw / 2 + 8 + (bw - 16) * k / 40
            pts.append((xx, wy + 8 * math.sin(t * 7 + k * 0.6)))
        pts.append((cx + bw / 2 - 8, bot - 8))
        wd.polygon(pts, fill=(30, 150, 255, 230))
        for k in range(6):
            by = bot - 30 - ((t * 120 + k * 70) % max(20, bot - wy - 30))
            wd.ellipse((cx - 80 + k * 30, by - 7, cx - 66 + k * 30, by + 7), outline=(200, 235, 255, 200), width=3)
        im.alpha_composite(wl)
    d.rounded_rectangle((cx - bw / 2, body_top, cx + bw / 2, bot), 40, outline=WHITE, width=8)
    d.polygon([(cx - bw / 2 + 4, body_top + 40), (cx - 60, top + 70), (cx + 60, top + 70),
               (cx + bw / 2 - 4, body_top + 40)], outline=WHITE, width=8)
    d.rectangle((cx - 70, top, cx + 70, top + 70), fill=(255, 90, 160), outline=WHITE, width=6)
    for k in range(1, 4):
        yk = bot - (bot - body_top) * k / 4
        d.line((cx + bw / 2 - 50, yk, cx + bw / 2 - 10, yk), fill=(200, 210, 240), width=4)
    d.text((cx, (body_top + bot) / 2 + 40), f"{int(round(lv * 100))}%", font=bfont(90), fill=WHITE, anchor="mm",
           stroke_width=6, stroke_fill=(10, 30, 80))
    # tap stream
    if any(ts - 0.1 <= t < ts + 0.55 for ts, _ in FILL):
        d.rectangle((cx - 9, top - 100, cx + 9, wy), fill=(80, 180, 255, 220))
    paste(st, glow(im, 10, 0.8, (120, 190, 255)), W / 2, H / 2, 0.9 + 0.1 * ease(a / 0.3), ease(a / 0.25))


# ------------------------------------------------------------------ scenes
C = lambda s, c=INKD: (s, c)   # noqa: E731


def draw_hook(st, t):
    neon_title(st, t, 0.1, "PYTHON", 540, 470, 90)
    neon_title(st, t, 0.4, "while loop", 540, 680, 150, YEL)
    type_box(st, t, 0.95, ((C("1 LINE = 100 BAAR KAAM!", NAVY),),), 540, 880, "cyan", 60, 0)
    for k, (t0, txt, col, x, y) in enumerate(HOOK_CHIPS):
        if t >= t0:
            paste(st, chip(txt, col), x, y + 10 * math.sin(t * 4 + k), pop(t - t0, 0.3), 1, 4 * math.sin(k + 1))
    if "m430" not in _C:
        _C["m430"] = mb.mascot(430)
    paste(st, _C["m430"], 840, 1360, pop(t - 1.2, 0.4))
    # x100 counter spinning up
    if t >= 1.6:
        n = min(100, int((t - 1.6) * 90) + 1)
        stamp(st, t, 1.6, f"x{n}", 840, 1660, 80, YEL, -8)


HOOK_CHIPS = [(1.2, "while", PINK, 220, 1130), (1.35, "i <= 5", CYAN, 250, 1290), (1.5, "i += 1", YEL, 220, 1450)]

LOOPDEF = ((C("Loop matlab: "), C("ek hi code", BLUE)),
           (C("ko "), C("baar-baar", RED), C(" chalana,")),
           (C("bina baar-baar likhe!"),))


def draw_loopdef(st, t):
    neon_title(st, t, 3.85, "Loop", 540, 470, 120)
    type_box(st, t, 4.4, LOOPDEF, 540, 720, "white", 54, 30)
    type_box(st, t, 6.6, ((C("Bina loop: ", WHITE), C("100 lines", RED)),), 400, 1000, "navy", 50, 34)
    type_box(st, t, 7.4, ((C("Loop se: ", WHITE), C("sirf 3 lines!", GREEN)),), 400, 1140, "navy", 50, 34)
    if t >= 7.25:
        lay = Image.new("RGBA", (W, H))
        q = ease((t - 7.25) / 0.25)
        ImageDraw.Draw(lay).line((420, 1000, 420 + 240 * q, 1000), fill=RED, width=8)
        st.alpha_composite(lay)


def draw_analogy(st, t):
    neon_title(st, t, 9.35, "Jab tak...", 540, 440, 110)
    type_box(st, t, 9.9, ((C("JAB TAK", RED), C(" bottle full nahi,", NAVY)), (C("paani bharte raho!", NAVY),)),
             540, 610, "cyan", 54, 32)
    draw_bottle(st, t, 10.6)
    for k, (ts, v) in enumerate(FILL):
        full = v >= 1.0
        pill(st, t, ts + 0.15, "full? HAAN" if full else "full? Nahi", GREEN if full else RED, 800, 900 + k * 100, 38)
    stamp(st, t, STOP_T, "STOP!", 800, 1300, 120, RED, -8)
    type_box(st, t, 15.6, ((C("while", CYAN), C(" = ", WHITE), C("JAB TAK", YEL), C(" condition", WHITE)),
                           (C("True", GREEN), C(", kaam chalta rahega!", WHITE))), 420, 1510, "navy", 44, 34)


SYN = ((C("while condition:", NAVY),), (C("    code", NAVY),))
SYN_INFO = [(20.6, (C("1. ", YEL), C("Pehle keyword: ", WHITE), C("while", PINK)), 230, 640),
            (22.2, (C("2. ", YEL), C("Condition ke baad colon ", WHITE), C(":", YEL)), 610, 640),
            (23.8, (C("3. ", YEL), C("4 space ka gap, phir code", WHITE)), 250, 730)]
SAVE_T = 25.6


def draw_syntax(st, t):
    neon_title(st, t, 19.35, "Syntax", 540, 440, 110)
    type_box(st, t, 19.9, SYN, 540, 660, "cyan", 72, 26)
    for k, (ts, line, px, py) in enumerate(SYN_INFO):
        if t >= ts:
            pointer(st, t, ts, px, py)
            type_box(st, t, ts + 0.15, (line,), 520, 940 + k * 150, "navy", 46, 36)
    stamp(st, t, SAVE_T, "SAVE KAR LO!", 340, 1440, 66, YEL, -5)


CODE = [(27.7, "i = 1"), (28.3, "while i <= 5:"), (29.2, "    print(i)"), (30.0, "    i = i + 1")]
ED_Y = 380
RUN_T = 31.0
ITER = [31.5, 32.7, 33.7, 34.55, 35.3]
END_CHECK = 36.05
DONE_T = 36.45


def iter_state(t):
    """-> (current loop index or None, phase 0 while / 1 print / 2 inc)"""
    for k in range(len(ITER) - 1, -1, -1):
        if t >= ITER[k]:
            if k == len(ITER) - 1 and t >= END_CHECK:
                return None, None
            nxt = ITER[k + 1] if k + 1 < len(ITER) else END_CHECK
            span = nxt - ITER[k]
            ph = 0 if t < ITER[k] + span * 0.3 else 1 if t < ITER[k] + span * 0.62 else 2
            return k, ph
    return None, None


def draw_code(st, t):
    hl = None
    k, ph = iter_state(t)
    if k is not None:
        hl = (1 + ph, (255, 214, 10, 70))
    if END_CHECK <= t < DONE_T + 1.2:
        hl = (1, (245, 60, 75, 90))
    editor(st, t, 27.35, ED_Y, CODE, 20, hl, None, RUN_T)
    ripple(st, t, RUN_T, ED_X1 - 58, ED_Y + 38 + 40 - 2)
    # i variable badge
    if t >= RUN_T + 0.3:
        iv = 1
        for j, ts in enumerate(ITER):
            nxt = ITER[j + 1] if j + 1 < len(ITER) else END_CHECK
            if t >= ts + (nxt - ts) * 0.62:
                iv = j + 2
        pill(st, t, RUN_T + 0.3, f"i = {iv}", (130, 60, 230), 800, ed_line_y(ED_Y, 0), 40)
    if k is not None:
        i = k + 1
        pill(st, t, ITER[k], f"{i} <= 5  True", (25, 160, 85), 540, 870, 40)
        if ph == 2:
            loop_arrow(st, t, ITER[k], ed_line_y(ED_Y, 1), ed_line_y(ED_Y, 3), 905)
    if t >= END_CHECK:
        pill(st, t, END_CHECK, "6 <= 5  False", (220, 45, 60), 540, 870, 40)
    outs = [(ts + ((ITER[j + 1] if j + 1 < len(ITER) else END_CHECK) - ts) * 0.3, str(j + 1))
            for j, ts in enumerate(ITER)]
    output_panel(st, t, RUN_T + 0.2, 930, 5, outs)
    stamp(st, t, DONE_T, "LOOP KHATAM!", 540, 1130, 100, GREEN, -6)
    type_box(st, t, 37.6, ((C("Condition "), C("False", RED), C(" hote hi")), (C("loop ruk jaata hai!"),)),
             410, 1450, "white", 48, 32)


TRAP = [(41.9, "i = 1"), (42.2, "while i <= 5:"), (42.5, "    print(i)"), (42.8, "    i = i + 1")]
STRIKE_T = 43.4
TRAP_RUN = 44.0
INF_T = 44.7


def draw_trap(st, t):
    neon_title(st, t, 41.35, "TRAP!", 540, 420, 110, RED)
    editor(st, t, 41.7, 520, TRAP, 40, (3, (245, 60, 75, 60)) if t >= STRIKE_T else None, (3, STRIKE_T), TRAP_RUN)
    ripple(st, t, TRAP_RUN, ED_X1 - 58, 520 + 78 - 2)
    if t >= STRIKE_T + 0.2:
        type_box(st, t, STRIKE_T + 0.2, ((C("i = i + 1", YEL), C(" bhool gaye?", WHITE)),), 540, 1000, "navy", 46, 40)
    if t >= TRAP_RUN + 0.2:
        n = int((t - TRAP_RUN - 0.2) * 22)
        lines = [(0, "1")] * (n + 1)
        alarm = 0.5 + 0.5 * math.sin(t * 18) if t >= INF_T else 0
        output_panel(st, t, TRAP_RUN + 0.2, 1080, 4, lines, (255, 120, 130), (t - TRAP_RUN) * 22, alarm)
    stamp(st, t, INF_T, "INFINITE LOOP!", 540, 1190, 100, RED, -7)
    type_box(st, t, 46.5, ((C("Increment ", WHITE), C("zaroor", YEL), C(" likho,", WHITE)),
                           (C("warna loop kabhi nahi rukega!", WHITE),)), 430, 1530, "navy", 42, 40)


QUIZ_CODE = [(48.9, "n = 3"), (49.3, "while n > 0:"), (49.8, "    print(n)"), (50.2, "    n = n - 1")]
QUIZ_SLAM = 48.35
OPTIONS = [(51.0, "A", "3 2 1"), (51.3, "B", "1 2 3"), (51.6, "C", "3 2 1 0")]
ANSWER = "A"
COUNT0, REVEAL = 51.9, 54.9


def option_card(letter, txt, state):
    key = ("opt", letter, txt, state)
    if key not in _C:
        im = Image.new("RGBA", (760, 140))
        d = ImageDraw.Draw(im)
        col = CYAN if state is None else GREEN if state else (120, 70, 90)
        d.rounded_rectangle((20, 20, 740, 120), 22, fill=(8, 16, 50, 235), outline=col, width=5)
        d.ellipse((40, 36, 108, 104), fill=col)
        d.text((74, 71), letter, font=bfont(44), fill=NAVY, anchor="mm")
        d.text((140, 72), txt, font=mb.font(MONO, 50), fill=WHITE, anchor="lm")
        if state:
            d.line([(668, 72), (686, 92), (718, 50)], fill=GREEN, width=10, joint="curve")
        _C[key] = glow(im, 10, 1.0, col) if state is not False else im
    return _C[key]


def draw_quiz(st, t):
    stamp(st, t, QUIZ_SLAM, "QUIZ TIME!", 540, 400, 120, YEL, -4)
    editor(st, t, 48.6, 500, QUIZ_CODE, 30)
    type_box(st, t, 50.6, ((C("Output kya hoga?"),),), 540, 980, "white", 50, 40)
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, option_card(letter, txt, state), 470, 1110 + k * 140, sc,
              1 if (t < REVEAL or letter == ANSWER) else 0.5)
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (200 * S, 200 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 190 * S, 190 * S), fill=(8, 14, 44, 230), outline=(60, 70, 110), width=12 * S)
        d.arc((10 * S, 10 * S, 190 * S, 190 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)), fill=YEL,
              width=12 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((100 * S, 104 * S), str(n) if n else "!", font=bfont(100 * S), fill=WHITE, anchor="mm")
        paste(st, im.resize((200, 200), Image.LANCZOS), 940, 1030, 1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8))
    if t >= COUNT0 + 0.2:
        type_box(st, t, COUNT0 + 0.2, ((C("Comment karo!", WHITE),),), 420, 1600, "navy", 46, 0)


DRAW = {"hook": draw_hook, "loopdef": draw_loopdef, "analogy": draw_analogy, "syntax": draw_syntax,
        "code": draw_code, "trap": draw_trap, "quiz": draw_quiz}
REACT = [(8.0, "Mehnat bachao!", GREEN), (14.65, "Full = STOP!", GREEN), (25.65, "Yeh yaad rakhna!", GREEN),
         (DONE_T, "5 baar chala!", GREEN), (INF_T + 0.1, "Kabhi nahi rukega!", RED), (REVEAL + 0.05, "3, 2, 1!", GREEN)]
MASCOT_IN = {"loopdef": 7.6, "analogy": 11.5, "syntax": 20.4, "code": 32.0, "trap": 44.5, "quiz": 52.2}


def draw_mascot(fr, t, name):
    if name not in MASCOT_IN:
        return
    if "m300" not in _C:
        _C["m300"] = mb.mascot(300)
    s = pop(t - MASCOT_IN[name], 0.4)
    if s <= 0:
        return
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
    paste(fr, _C["m300"], 935, 1620 + bob, s, 1, rot)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], bfont(44), 20)
        paste(fr, b, max(b.width / 2 + 20, 1030 - b.width / 2), 1400, pop(a, 0.22) * (1 - ease((a - 1.6) / 0.2)))


@lru_cache(None)
def handle_tag():
    f = bfont(34, "Bold")
    txt = "@PythonKiPathshala"
    w = int(f.getlength(txt)) + 40
    im = Image.new("RGBA", (w, 60))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 59), fill=(235, 30, 50))
    d.text((20, 31), txt, font=f, fill=WHITE, anchor="lm")
    return im


@lru_cache(None)
def hud():
    p = Image.new("RGBA", (560, 64))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, 559, 63), 32, fill=(5, 10, 40, 170), outline=(120, 170, 255, 160), width=2)
    d.text((280, 33), "PYTHON KI PATHSHALA  •  EP 11", font=mb.font(bs.CAP, 28), fill=YEL, anchor="mm")
    return p


def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return SCENES[k], (SCENES[k - 1] if k else None)


_FROZEN = {}


def frame(i):
    t = i / FPS
    if t >= END0:
        return np.asarray(es.frame(t - END0).convert("RGB"))
    (s0, name), prev = scene_at(t)
    fr = m.background(t)
    a = t - s0
    if prev is not None and a < SQ:
        # SQUASH transition (reference): old scene collapses into a glowing line
        if s0 not in _FROZEN:
            old = Image.new("RGBA", (W, H))
            DRAW[prev[1]](old, s0 - 0.001)
            _FROZEN[s0] = old
        q = ease(a / SQ)
        hh = max(2, int(H * (1 - q)))
        sq = _FROZEN[s0].resize((int(W * (1 + 0.06 * q)), hh), Image.BICUBIC)
        if sq.width > W:
            cx0 = (sq.width - W) // 2
            sq = sq.crop((cx0, 0, cx0 + W, hh))
        fr.alpha_composite(sq, ((W - sq.width) // 2, int(960 - hh / 2)))
        ln = Image.new("RGBA", (W, H))
        ImageDraw.Draw(ln).rectangle((60 + 400 * q, 955, W - 60 - 400 * q, 965), fill=(220, 240, 255, int(255 * q)))
        fr.alpha_composite(glow(ln, 12, 1.5, CYAN))
    else:
        st = Image.new("RGBA", (W, H))
        DRAW[name](st, t)
        dy = int(120 * (1 - ease((a - SQ) / 0.3))) if prev is not None else 0
        if dy:
            fr.alpha_composite(st.crop((0, 0, W, H - dy)), (0, dy))
        else:
            fr.alpha_composite(st)
        draw_mascot(fr, t, name)
    fr.alpha_composite(hud(), (W // 2 - 280, 120))
    fr.alpha_composite(handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    for ts, amp in ((INF_T, 16), (STOP_T, 8), (QUIZ_SLAM, 10), (REVEAL, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.35:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.35)), axis=1)
    if INF_T <= t < 47.0:          # red alarm pulse
        arr[..., 0] += 40 * (0.5 + 0.5 * math.sin(t * 18))
    arr *= m.vignette()
    arr += m.cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=m.cv2.INTER_NEAREST)[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def neon_buzz(seed):
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    hum = np.sign(np.sin(2 * np.pi * 120 * tt)) * 0.25 + fx.noise(n, seed) * 0.25
    gate = np.ones(n)
    for a0, a1 in ((0.0, 0.03), (0.1, 0.13), (0.2, 0.22)):
        gate[int(a0 * SR):int(a1 * SR)] = 0
    env = np.exp(-tt * 6)
    return fx.filt(hum, "bandpass", [100, 4000]) * gate * env * 0.5


def glug(seed):
    out = np.zeros(int(0.5 * SR))
    rng = np.random.default_rng(seed)
    for k in range(5):
        n = int(0.07 * SR)
        tt = np.arange(n) / SR
        f0 = rng.uniform(260, 420)
        b = np.sin(2 * np.pi * (f0 * tt + 2500 * tt * tt)) * np.exp(-tt * 40)
        s = int(k * 0.09 * SR)
        out[s:s + n] += b * 0.5
    return out


def water(dur, seed):
    n = int(dur * SR)
    return fx.filt(fx.noise(n, seed), "bandpass", [600, 3000]) * 0.18 * np.minimum(1, np.arange(n) / (0.05 * SR))


def type_clicks(buf, t0, n, cps, seed, gain=0.22):
    for k in range(n):
        fx.place(buf, bs.key_click(seed + k), t0 + k / cps, gain)


def alarm(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (880 + 220 * (tt % 0.3 < 0.15)) * tt) * 0.28


def squash_sfx(seed):
    n = int(0.3 * SR)
    tt = np.linspace(0, 1, n)
    s = fx.filt(fx.noise(n, seed), "bandpass", [800, 6000]) * np.sin(np.pi * tt) ** 2 * 0.45
    return s + np.sin(2 * np.pi * (900 - 700 * tt) * tt * 0.3) * 0.0


def box_sfx(buf, t0, lines, cps, seed, gain=0.18):
    fx.place(buf, m.box_swish(seed), t0, 0.8)
    if cps:
        type_clicks(buf, t0 + 0.18, total_chars(lines), cps, seed * 7, gain)


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    # hook
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, neon_buzz(1), 0.1, 0.8)
    P(buf, neon_buzz(2), 0.4, 0.9)
    P(buf, fx.pop(), 0.95, 0.6)
    for k, (t0, *_r) in enumerate(HOOK_CHIPS):
        P(buf, fx.pop(), t0, 0.4)
        P(buf, bs.note_pop(700 + 140 * k), t0, 0.25)
    for k in range(12):
        P(buf, bs.key_click(300 + k), 1.6 + k * 0.09, 0.25)
    P(buf, fx.ding(), 2.7, 0.35)
    # transitions
    for s0, n in SCENES[1:]:
        P(buf, squash_sfx(int(s0 * 10)), s0 - 0.05, 0.7)
        P(buf, fx.whoosh(0.35, int(s0 * 10) + 1), s0 + SQ - 0.05, 0.45)
    # neon titles
    for t0 in (3.85, 9.35, 19.35, 41.35):
        P(buf, neon_buzz(int(t0 * 10)), t0, 0.7)
    # loopdef
    box_sfx(buf, 4.4, LOOPDEF, 30, 41)
    box_sfx(buf, 6.6, ((("Bina loop: 100 lines", 0),),), 34, 42)
    P(buf, m.e_buzz()[: int(0.25 * SR)], 7.25, 0.5)
    box_sfx(buf, 7.4, ((("Loop se: sirf 3 lines!", 0),),), 34, 43)
    P(buf, fx.ding(), 8.0, 0.4)
    # analogy
    box_sfx(buf, 9.9, ((("JAB TAK bottle full nahi,", 0),), (("paani bharte raho!", 0),)), 32, 44)
    P(buf, fx.whoosh(0.4, 9), 10.6, 0.5)
    for k, (ts, v) in enumerate(FILL):
        P(buf, water(0.6, 50 + k), ts - 0.1, 0.8)
        P(buf, glug(60 + k), ts, 0.7)
        P(buf, fx.pop(), ts + 0.15, 0.4)
        P(buf, fx.ding() if v >= 1 else bs.note_pop(520 + 90 * k), ts + 0.2, 0.35 if v >= 1 else 0.3)
    P(buf, fx.boom(), STOP_T, 0.6)
    P(buf, bs.thud(), STOP_T, 0.5)
    box_sfx(buf, 15.6, ((("while = JAB TAK condition", 0),), (("True, kaam chalta rahega!", 0),)), 34, 45)
    # syntax
    box_sfx(buf, 19.9, SYN, 26, 46)
    for k, (ts, line, *_r) in enumerate(SYN_INFO):
        P(buf, fx.pop(), ts, 0.5)
        box_sfx(buf, ts + 0.15, (line,), 36, 47 + k)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.45)
    # code
    P(buf, fx.whoosh(0.3, 70), 27.35, 0.4)
    for k, (ts, txt) in enumerate(CODE):
        type_clicks(buf, ts, len(txt), 20, 80 + 10 * k, 0.26)
    P(buf, bs.mouse_click(), RUN_T, 0.8)
    scale = [523.3, 587.3, 659.3, 784.0, 880.0]
    for k, ts in enumerate(ITER):
        nxt = ITER[k + 1] if k + 1 < len(ITER) else END_CHECK
        P(buf, fx.pop(), ts, 0.35)
        P(buf, bs.note_pop(scale[k]), ts + (nxt - ts) * 0.3, 0.45)
        P(buf, fx.whoosh(0.2, 90 + k), ts + (nxt - ts) * 0.62, 0.3)
    P(buf, m.e_buzz(), END_CHECK, 0.6)
    P(buf, fx.boom()[: int(0.6 * SR)], DONE_T, 0.5)
    P(buf, e_chime(), DONE_T + 0.05, 0.7)
    box_sfx(buf, 37.6, ((("Condition False hote hi", 0),), (("loop ruk jaata hai!", 0),)), 32, 95)
    # trap
    P(buf, fx.whoosh(0.3, 100), 41.7, 0.4)
    for k, (ts, txt) in enumerate(TRAP):
        type_clicks(buf, ts, len(txt), 40, 110 + 10 * k, 0.2)
    P(buf, fx.whoosh(0.3, 120), STRIKE_T, 0.5)
    P(buf, m.e_buzz()[: int(0.25 * SR)], STRIKE_T + 0.2, 0.5)
    box_sfx(buf, STRIKE_T + 0.2, ((("i = i + 1 bhool gaye?", 0),),), 40, 121)
    P(buf, bs.mouse_click(), TRAP_RUN, 0.8)
    tt = TRAP_RUN + 0.2
    while tt < 47.6:
        P(buf, bs.key_click(int(tt * 100)), tt, 0.22)
        tt += 1 / 22
    P(buf, fx.boom(), INF_T, 0.8)
    P(buf, alarm(2.2), INF_T + 0.05, 0.6)
    box_sfx(buf, 46.5, ((("Increment zaroor likho,", 0),), (("warna loop kabhi nahi rukega!", 0),)), 40, 122)
    # quiz
    P(buf, fx.riser(0.6), QUIZ_SLAM - 0.6, 0.35)
    P(buf, fx.boom(), QUIZ_SLAM, 0.8)
    for k, (ts, txt) in enumerate(QUIZ_CODE):
        type_clicks(buf, ts, len(txt), 30, 130 + 10 * k, 0.2)
    box_sfx(buf, 50.6, ((("Output kya hoga?", 0),),), 40, 140)
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
    for tr, txt, col in REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def e_chime():
    out = np.zeros(int(0.9 * SR))
    for k, f0 in enumerate((1046.5, 1318.5, 1568.0)):
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        s = int(k * 0.07 * SR)
        out[s:s + n] += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 6) * 0.3
    return out


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=INF_T)
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


# ------------------------------------------------------------------ wire into the EP 08 encoder
m.OUT, m.WORK, m.TOTAL, m.END0 = OUT, WORK, TOTAL, END0
m.frame, m.build_audio = frame, build_audio

if __name__ == "__main__":
    m.main()
