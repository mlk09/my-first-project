#!/usr/bin/env python3
"""Python ki Pathshala EP 06 - Operators  (1080x1920 Short, works without a voice-over)

Structure decoded from "Python Operators | Learn Python" (Learn Technology): title, one-line
definition, a small example, then a "Types -" list that builds up bullet by bullet on one
continuous board, voice only, subscribe button at the end.
Theme = EP 02 (Variables): black glass lightboard, glowing hand-writing, yellow title box, mascot.
New pieces: operand / operator / result diagram, 5-family operator sheet with mascot examples,
"/ vs // vs %" trick board, quiz and the Python ki Pathshala end screen.

Usage:  python3 edit13/build_ep06.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit9"))
sys.path.insert(0, os.path.join(HERE, "..", "edit10"))
import build_ep02 as e   # noqa: E402  EP 02 engine (black lightboard theme)
_bg, _vig = e.board_bg, e.vignette
import build_ep03 as p3  # noqa: E402  quiz cards + chips (it swaps the background, restored below)
e.board_bg, e.vignette = _bg, _vig

mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp = e.paste, e.pop, e.ease, e.clamp
W, H, SR = e.W, e.H, e.SR
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
PURPLE, PINK = (190, 140, 255), (255, 110, 170)
es.NEXT = "EP 07: F-STRINGS"
HAND, CODE = "hand", "code"


def glowify(im, col=None, r=10, n=1):
    return e.glowify(im, col, r, n)[0]


# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 12.0, "what"), (12.0, 15.0, "types"), (15.0, 44.0, "sheet"),
          (44.0, 50.5, "trick"), (50.5, 57.5, "quiz")]
END0 = 57.5
TOTAL = END0 + es.DUR

FAMILIES = [  # (t, y, title, colour, operators, example bubble)
    (15.3, 410, "Arithmetic", CYAN, "+  -  *  /  //  %  **", "7 // 2 = 3"),
    (20.6, 600, "Assignment", ORANGE, "=  +=  -=  *=  /=", "x += 5  matlab  x = x + 5"),
    (25.9, 790, "Comparison", YEL, "==  !=  >  <  >=  <=", "5 > 3  =  True"),
    (31.2, 980, "Logical", GREEN, "and   or   not", "True and False = False"),
    (36.5, 1170, "Membership", PINK, "in   not in", '"a" in "apple" = True'),
]
WRITES = [
    (3.45, "what", 100, 420, [("Operator kya hai?", WHITE)], 86, HAND),
    (4.75, "what", 100, 525, [("= data par ", WHITE), ("KAAM", YEL), (" karne", WHITE)], 78, HAND),
    (5.6, "what", 140, 615, [("wala symbol", WHITE)], 78, HAND),
    (12.25, "types", 120, 640, [("Python mein operators ke", WHITE)], 70, HAND),
    (44.25, "trick", 100, 400, [("Sabse ", WHITE), ("CONFUSING", RED), (" teen:", WHITE)], 80, HAND),
    (51.3, "quiz", 300, 610, [("10 % 3", None)], 80, CODE),
    (52.0, "quiz", 650, 610, [("= ?", YEL)], 82, HAND),
]
for t0, y, title, col, ops, ex in FAMILIES:
    WRITES += [(t0 + 0.2, "sheet", 190, y, [(title, col)], 66, HAND),
               (t0 + 1.1, "sheet", 200, y + 78, [(ops, None)], 46, CODE)]
TRICK = [(45.6, 600, "7 / 2", "3.5", "divide (decimal)"), (46.9, 780, "7 // 2", "3", "floor divide (poora)"),
         (48.2, 960, "7 % 2", "1", "remainder (bacha hua)")]
for t0, y, code, res, lab in TRICK:
    WRITES += [(t0, "trick", 130, y, [(code, None)], 66, CODE),
               (t0 + 0.45, "trick", 450, y, [("= ", WHITE), (res, GREEN)], 72, HAND),
               (t0 + 0.75, "trick", 140, y + 80, [(lab, (195, 200, 212))], 48, HAND)]
NUMS = [(t0, 120, y, str(k + 1)) for k, (t0, y, *_r) in enumerate(FAMILIES)]
REACT = [(t0 + 2.4, ex, col) for t0, y, title, col, ops, ex in FAMILIES] + [(56.15, "10 mein 3 teen baar, 1 bacha!", GREEN)]
EQ = (6.3, 7.0, 7.6, 8.8)          # 10, +, 5 appear ; result
SLAM = 13.5
SAVE_T = 42.2
QUIZ_SLAM = 50.7
OPTIONS = [(52.6, "A", "3"), (52.9, "B", "1"), (53.2, "C", "3.33")]
COUNT0, REVEAL = 53.1, 56.1


# ------------------------------------------------------------------ graphics
def token_chip(txt, col, size=78):
    f = mb.font(e.MONO, size)
    w = int(f.getlength(txt)) + 70
    im = Image.new("RGBA", (w, int(size * 1.7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, w - 4, im.height - 4), 26, fill=(18, 19, 24), outline=col, width=6)
    d.text((w / 2, im.height / 2), txt, font=f, fill=col, anchor="mm")
    return glowify(im, col, 12, 1)


def draw_equation(st, t):
    t10, tplus, t5, tres = EQ
    xs = {"10": 250, "+": 450, "5": 620, "=": 770, "15": 910}
    y = 900
    paste(st, token_chip("10", CYAN), xs["10"], y, pop(t - t10, 0.3))
    paste(st, token_chip("+", YEL), xs["+"], y, pop(t - tplus, 0.3) * (1 + 0.06 * math.sin(t * 6) * (t > tplus)))
    paste(st, token_chip("5", CYAN), xs["5"], y, pop(t - t5, 0.3))
    d = ImageDraw.Draw(st)
    f = mb.font(e.HAND, 50)
    if t > tplus + 0.4:     # labels with little arrows
        a = int(255 * clamp((t - tplus - 0.4) / 0.25))
        for x, lab, col, up in ((xs["10"], "operand", CYAN, False), (xs["+"], "OPERATOR", YEL, True),
                                (xs["5"], "operand", CYAN, False)):
            yy = y + 150 if not up else y - 150
            d.text((x, yy), lab, font=f, fill=col + (a,), anchor="mm")
            ya, yb = (y + 70, yy - 32) if not up else (y - 70, yy + 32)
            d.line((x, ya, x, yb), fill=col + (a,), width=5)
    if t > tres:
        d.text((xs["="], y), "=", font=mb.font(e.MONO, 90), fill=WHITE, anchor="mm")
        paste(st, token_chip("15", GREEN, 90), xs["15"], y, pop(t - tres, 0.35))


def draw_types(st, t):
    e.slam_text(st, t, SLAM, "5 TYPES!", 860, 150, YEL, (150, 95, 0))
    pos = [(290, 1060), (790, 1060), (290, 1200), (790, 1200), (540, 1340)]
    for k, ((t0, y, title, col, *_r), (x, yy)) in enumerate(zip(FAMILIES, pos)):
        paste(st, p3.chip(title.upper(), col), x, yy + 6 * math.sin(t * 3 + k), pop(t - (SLAM + 0.35 + 0.15 * k), 0.3))


HOOK_OPS = [(0.9, "+", YEL, 170, 1150), (1.0, "-", CYAN, 380, 1230), (1.1, "*", ORANGE, 210, 1360),
            (1.2, "/", GREEN, 430, 1420), (1.3, "%", PINK, 250, 1560), (1.4, "==", PURPLE, 480, 1600),
            (1.5, "and", RED, 160, 1720)]


def draw_hook(st, t):
    paste(st, e._outlined("PYTHON", 120, WHITE, (40, 40, 50)), 540, 520, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("OPERATORS", 160, YEL, (150, 95, 0)), 540, 710, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("5 TYPES  •  1 SHORT", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=(255, 90, 95))
    paste(st, rb, 540, 900, pop(t - 0.55), 1, 2)
    for t0, txt, col, x, y in HOOK_OPS:
        paste(st, token_chip(txt, col, 64), x, y + 10 * math.sin(t * 4 + x), pop(t - t0, 0.3), 1, 5 * math.sin(x))
    if "m430" not in e._C:
        e._C["m430"] = mb.mascot(430)
    paste(st, e._C["m430"], 840, 1350, pop(t - 1.0, 0.4))


def render_board(t, board):
    st = Image.new("RGBA", (W, H))
    if board == "hook":
        draw_hook(st, t)
        return st
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "what":
        draw_equation(st, t)
    elif board == "types":
        draw_types(st, t)
    elif board == "sheet":
        for ev in NUMS:
            e.draw_circle_num(st, t, ev)
        if t >= SAVE_T:
            paste(st, e._outlined("SAVE KAR LO!", 70, YEL, (150, 95, 0)), 420, 1400, pop(t - SAVE_T, 0.3), 1, -3)
    elif board == "trick":
        for t0, y, *_r in TRICK:
            if t >= t0 + 0.45:
                paste(st, bs.icon_check(60, True), 700, y, pop(t - t0 - 0.45, 0.25))
    elif board == "quiz":
        p3.draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 980, 1.0 + 0.03 * ease((t - 50.5) / 7)
    if board == "types":
        return 900, 1.03 + 0.03 * ease((t - 12) / 3)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = [(ev[0], ev[3]) for ev in WRITES if ev[1] == board]
    if board == "what":
        ys.append((EQ[0], 900))
    ys.sort()
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(1010, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.07
    pull = b1 - 2.0 if board != "sheet" else SAVE_T - 0.8
    if t > pull:
        q = ease((t - pull) / 0.8)
        cy, zoom = cy + (900 - cy) * q, zoom + (1.0 - zoom) * q
    return cy, zoom


def mascot_layer(st, t, board):
    if board in ("hook", None):
        return
    if "m" not in e._C:
        e._C["m"] = mb.mascot(300)
    t_in = {"what": 9.2, "types": 12.2, "sheet": 17.0, "trick": 45.0, "quiz": 53.4}[board]
    s = pop(t - t_in, 0.4)
    if s <= 0:
        return
    react = None
    for tr, txt, col in REACT:
        if 0 <= t - tr < 2.2:
            react = (tr, txt, col)
    bob = 8 * math.sin(t * 3)
    if react:
        a = t - react[0]
        bob -= 30 * abs(math.sin(a * 10)) * math.exp(-a * 5)
    paste(st, e._C["m"], 935, 1580 + bob, s)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 44, "ExtraBold"), 20)
        by = 1430 if board == "sheet" else 1355
        paste(st, b, max(b.width / 2 + 20, 1030 - b.width / 2), by, pop(a, 0.22) * (1 - ease((a - 2.0) / 0.2)))


@e.lru_cache(None)
def title_box():
    im = Image.new("RGBA", (560, 150))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(10, 10, 12, 180))
    d.text((28, 48), "Python Operators", font=mb.font(mb.BALOO, 52, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "5 Types, 1 Short", font=mb.font(mb.BALOO, 46, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 6"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(120, 125, 135, 200), anchor="lm")
    return im.rotate(90, expand=True)


# ------------------------------------------------------------------ audio
def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, fx.pop(), 0.25, 0.6)
    P(buf, fx.whoosh(0.3, 1), 0.45, 0.5)
    for k, (t0, *_r) in enumerate(HOOK_OPS):
        P(buf, fx.pop(), t0, 0.35)
        P(buf, bs.note_pop(600 + 90 * k), t0, 0.2)
    for s, en, n in BOARDS[1:]:
        P(buf, e.eraser_swish(), s, 0.55)
        P(buf, e.cap_click(), s + 0.2, 0.5)
    for ev in WRITES:
        nch = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, nch / e.CPS) if ev[6] == HAND else max(0.25, nch / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, *_r in NUMS:
        P(buf, e.marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    t10, tplus, t5, tres = EQ
    for tt in (t10, tplus, t5):
        P(buf, fx.pop(), tt, 0.6)
    P(buf, bs.thud(), tplus, 0.4)
    P(buf, fx.whoosh(0.3, 4), tres - 0.25, 0.4)
    P(buf, fx.ding(), tres, 0.55)
    P(buf, fx.riser(1.0), SLAM - 1.0, 0.45)
    P(buf, fx.boom(), SLAM, 1.0)
    for k in range(5):
        P(buf, fx.pop(), SLAM + 0.35 + 0.15 * k, 0.5)
    for k, (tr, *_r) in enumerate(REACT[:-1]):
        P(buf, bs.note_pop([523.25, 587.33, 659.25, 783.99, 880.0][k]), tr, 0.4)
        P(buf, fx.pop(), tr, 0.3)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.4)
    for k, (t0, *_r) in enumerate(TRICK):
        P(buf, fx.ding(), t0 + 0.45, 0.35)
        P(buf, bs.note_pop([659.25, 783.99, 987.77][k]), t0 + 0.45, 0.3)
    P(buf, fx.riser(0.6), QUIZ_SLAM - 0.6, 0.35)
    P(buf, fx.boom(), QUIZ_SLAM, 0.8)
    for t0, *_r in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    tt = COUNT0
    while tt < REVEAL - 0.05:
        P(buf, e.tick(), tt, 0.6)
        tt += 0.5
    P(buf, e.chime(), REVEAL, 0.9)
    P(buf, fx.boom()[: int(0.5 * SR)], REVEAL, 0.5)
    P(buf, es.sfx(), END0, 0.9)
    return buf


# ------------------------------------------------------------------ wire into the engine
p3.QUIZ_SLAM, p3.OPTIONS, p3.ANSWER, p3.COUNT0, p3.REVEAL = QUIZ_SLAM, OPTIONS, "B", COUNT0, REVEAL
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP06_Operators.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL, e.WRITES = BOARDS, END0, TOTAL, WRITES
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = SLAM, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(SLAM, 1.0), (QUIZ_SLAM, 0.8), (REVEAL, 0.4)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
e.frame = p3._frame

if __name__ == "__main__":
    e.main()
