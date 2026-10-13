#!/usr/bin/env python3
"""Python ki Pathshala EP 05 - Type Casting  (1080x1920 Short, works without a voice-over)

Style decoded from "Type Casting to Mix Types in Python" (Neso Academy, Quick Concepts): lightboard
hand-writing, fixed yellow title box, code written inside an outlined box, a yellow arrow pointing at
the problem with a hand-written note, "Output: Error" with a pulsing warning sign, the same code fixed
in place, a celebration sticker, clean outro.
Built on the EP 02/03 lightboard engine (lighter slate background from EP 03) with new pieces:
a converter machine, the code box, annotation arrows, pulsing warning, confetti, a casting cheat list,
quiz and the Python ki Pathshala end screen.

Usage:  python3 edit12/build_ep05.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit10"))
import build_ep03 as p3   # noqa: E402  (EP 03 module: loads the EP 02 engine, light background, quiz cards)

e = p3.e
mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp = e.paste, e.pop, e.ease, e.clamp


def glowify(im, col=None, r=10, n=1):
    return e.glowify(im, col, r, n)[0]
W, H, SR = e.W, e.H, e.SR
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
PINK = (255, 70, 120)
es.NEXT = "EP 06: OPERATORS"
HAND, CODE = "hand", "code"

# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 12.0, "what"), (12.0, 27.0, "problem"), (27.0, 37.5, "fix"),
          (37.5, 47.5, "rules"), (47.5, 55.0, "quiz")]
END0 = 55.0
TOTAL = END0 + es.DUR

LINE2_ERR = 'msg = "Meri age: " + age'
LINE2_FIX = 'msg = "Meri age: " + str(age)'
CODE_X = 130
WRITES = [
    # what is type casting + converter machine
    (3.45, "what", 100, 420, [("Type Casting kya hai?", WHITE)], 86, HAND),
    (4.75, "what", 100, 525, [("= data ka ", WHITE), ("TYPE", YEL), (" badalna", WHITE)], 80, HAND),
    (9.6, "what", 210, 1260, [('int("20")', None)], 66, CODE),
    (10.5, "what", 590, 1260, [("= 20", GREEN)], 72, HAND),
    # the problem (Neso-style code box + arrow + note)
    (12.6, "problem", CODE_X, 420, [("age = 25", None)], 48, CODE),
    (13.5, "problem", CODE_X, 500, [(LINE2_ERR, None)], 48, CODE),
    (15.0, "problem", CODE_X, 580, [("print(msg)", None)], 48, CODE),
    (17.0, "problem", 150, 790, [("str", ORANGE), (" + ", WHITE), ("int", CYAN), (" = jud nahi sakte!", YEL)], 60, HAND),
    (19.0, "problem", 110, 920, [("Output:", GREEN)], 62, HAND),
    (19.6, "problem", 340, 920, [("TypeError", None)], 56, CODE),
    # the fix
    (27.5, "fix", CODE_X, 420, [("age = 25", None)], 48, CODE),
    (28.2, "fix", CODE_X, 500, [(LINE2_FIX, None)], 44, CODE),
    (29.6, "fix", CODE_X, 580, [("print(msg)", None)], 48, CODE),
    (30.6, "fix", 140, 790, [("str()", GREEN), (" ne 25 ko ", WHITE), ("TEXT", YEL), (" bana diya!", WHITE)], 60, HAND),
    (32.2, "fix", 110, 920, [("Output:", GREEN)], 62, HAND),
    (32.8, "fix", 340, 920, [("Meri age: 25", None)], 56, CODE),
    # casting functions list
    (37.75, "rules", 110, 400, [("3 Casting Functions:", WHITE)], 76, HAND),
]
RULES = [  # (t, y, code, result, hint, hint colour)
    (38.6, 540, 'int("5")', "= 5", "text se number", (195, 200, 212)),
    (40.6, 720, 'float("3.5")', "= 3.5", "text se decimal", (195, 200, 212)),
    (42.6, 900, "str(25)", '= "25"', "number se text", (195, 200, 212)),
]
BONUS = (44.6, 1090)
for t0, y, code, res, hint, hc in RULES:
    WRITES += [(t0 + 0.2, "rules", 195, y, [(code, None)], 58, CODE),
               (t0 + 0.9, "rules", 640, y, [(res, GREEN)], 64, HAND),
               (t0 + 1.2, "rules", 200, y + 72, [(hint, hc)], 50, HAND)]
WRITES += [(BONUS[0], "rules", 110, BONUS[1], [("Bonus: ", ORANGE)], 64, HAND),
           (BONUS[0] + 0.5, "rules", 330, BONUS[1], [("int(3.9)", None)], 58, CODE),
           (BONUS[0] + 1.1, "rules", 640, BONUS[1], [("= 3", GREEN)], 64, HAND),
           (BONUS[0] + 1.4, "rules", 120, BONUS[1] + 72, [("Decimal kat jaata hai, round nahi hota!", RED)], 46, HAND),
           (48.3, "quiz", 160, 610, [('int("7") + 3', None)], 72, CODE),
           (49.1, "quiz", 740, 610, [("= ?", YEL)], 82, HAND)]
NUMS = [(t0, 120, y, str(k + 1)) for k, (t0, y, *_r) in enumerate(RULES)]
REACT = [(20.1, "Error!", RED), (33.3, "Ho gaya!", GREEN), (39.6, "Number ban gaya!", GREEN),
         (41.6, "Point wala!", GREEN), (43.6, "Ab text hai!", GREEN), (46.2, "Dhyan rakhna!", RED),
         (53.65, "7 + 3 = 10!", GREEN)]
CODEBOX = {"problem": 12.25, "fix": 27.2}
ARROW = {"problem": (16.6, LINE2_ERR.index("+")), "fix": (30.2, LINE2_FIX.index("str"))}
WARN_T, PARTY_T = 20.0, 33.0
MACHINE = (6.0, 6.6, 7.4, 8.2)          # appear, chip enters, processing, chip exits
SAVE_T = 46.6
QUIZ_SLAM = 47.7
OPTIONS = [(49.6, "A", "73"), (49.9, "B", "10"), (50.2, "C", "Error")]
COUNT0, REVEAL = 50.6, 53.6


# ------------------------------------------------------------------ new graphics
def rect_path(x0, y0, x1, y1):
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]


def draw_codebox(st, t, t0):
    p = clamp((t - t0) / 0.5)
    if p <= 0:
        return
    lay = Image.new("RGBA", st.size)
    d = ImageDraw.Draw(lay)
    d.rectangle((90, 350, 990, 625), fill=(18, 20, 26, int(150 * p)))
    e.draw_lines(d, rect_path(90, 350, 990, 625), p, WHITE + (255,), 5)
    st.alpha_composite(glowify(lay, None, 8, 1).crop((24, 24, 24 + W, 24 + H)))


def code_x(line, idx, size):
    return CODE_X + mb.font(e.MONO, size).getlength(line[:idx])


def draw_arrow(st, t, board):
    t0, idx = ARROW[board]
    p = ease((t - t0) / 0.35)
    if p <= 0:
        return
    line, size = (LINE2_ERR, 48) if board == "problem" else (LINE2_FIX, 44)
    x = code_x(line, idx, size) + (14 if board == "problem" else 60)
    y0, y1 = 735, 525
    lay = Image.new("RGBA", st.size)
    d = ImageDraw.Draw(lay)
    yy = y0 + (y1 - y0) * p
    col = YEL if board == "problem" else GREEN
    d.line((x, y0, x, yy), fill=col, width=8)
    if p > 0.7:
        d.polygon([(x, y1 - 12), (x - 22, y1 + 26), (x + 22, y1 + 26)], fill=col)
    if board == "fix":      # green highlight behind str(age)
        x0 = code_x(line, idx, size) - 6
        x1 = code_x(line, len(line), size) + 6
        a = int(90 * clamp((t - t0) / 0.3))
        d.rounded_rectangle((x0, 462, x1, 518), 10, fill=(80, 220, 120, a))
    st.alpha_composite(glowify(lay, col, 8, 1).crop((24, 24, 24 + W, 24 + H)))


@e.lru_cache(None)
def warn_icon():
    S = 3
    im = Image.new("RGBA", (240 * S, 240 * S))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40 * S, 60 * S, 200 * S, 200 * S), 0, fill=None)
    d.polygon([(120 * S, 62 * S), (204 * S, 206 * S), (36 * S, 206 * S)], fill=PINK)
    d.rounded_rectangle((112 * S, 110 * S, 128 * S, 168 * S), 8 * S, fill=WHITE)
    d.ellipse((111 * S, 178 * S, 129 * S, 196 * S), fill=WHITE)
    for ang in (-60, -90, -120):            # radiating alarm lines
        a = math.radians(ang)
        cx, cy = 120 * S, 120 * S
        d.line((cx + 95 * S * math.cos(a), cy + 95 * S * math.sin(a), cx + 118 * S * math.cos(a),
                cy + 118 * S * math.sin(a)), fill=PINK, width=10 * S)
    return glowify(im.resize((240, 240), Image.LANCZOS), PINK, 16, 2)


def draw_warn(st, t):
    a = t - WARN_T
    if a < 0:
        return
    s = pop(a, 0.3) * (1 + 0.07 * math.sin(a * 9))
    paste(st, warn_icon(), 540, 1180, s)


CONF_COLS = [YEL, GREEN, PINK, CYAN, ORANGE, (190, 140, 255)]
_r = np.random.default_rng(11)
CONFETTI = [(_r.uniform(-1, 1) * 900, -_r.uniform(600, 1400), _r.uniform(0, 6.28), _r.uniform(-12, 12),
             CONF_COLS[k % 6], _r.uniform(14, 26)) for k in range(70)]


def draw_confetti(st, t, t0, cx=540, cy=1200):
    a = t - t0
    if not 0 <= a < 2.2:
        return
    d = ImageDraw.Draw(st)
    fade = 1 - ease((a - 1.7) / 0.5)
    for vx, vy, ph, spin, col, sz in CONFETTI:
        x = cx + vx * a
        y = cy + vy * a + 0.5 * 1800 * a * a
        ang = ph + spin * a
        w, h = sz, sz * 0.5 * abs(math.cos(ang * 1.7)) + 3
        pts = [(x + w * math.cos(ang) - h * math.sin(ang), y + w * math.sin(ang) + h * math.cos(ang)),
               (x - w * math.cos(ang) - h * math.sin(ang), y - w * math.sin(ang) + h * math.cos(ang)),
               (x - w * math.cos(ang) + h * math.sin(ang), y - w * math.sin(ang) - h * math.cos(ang)),
               (x + w * math.cos(ang) + h * math.sin(ang), y + w * math.sin(ang) - h * math.cos(ang))]
        d.polygon(pts, fill=col + (int(255 * fade),))


def draw_machine(st, t):
    t_in, t_enter, t_proc, t_out = MACHINE
    s = pop(t - t_in, 0.35)
    if s <= 0:
        return
    shake = 6 * math.sin(t * 60) if t_proc <= t < t_out else 0
    mx, my = 540 + shake, 900
    # chips (drawn first so the machine hides them while inside)
    if t >= t_enter:
        q = ease((t - t_enter) / (t_proc - t_enter))
        if q < 1:
            paste(st, p3.code_chip('"20"', ORANGE), -60 + (mx - 120 + 60) * q, my, 1.1)
    if t >= t_out:
        q = ease((t - t_out) / 0.6)
        paste(st, p3.code_chip("20", CYAN), mx + 120 + (300 - 120) * q, my, 1.1 * (0.6 + 0.4 * q))
    m = Image.new("RGBA", (400, 300))
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((4, 30, 396, 296), 30, fill=(32, 36, 46), outline=YEL, width=7)
    d.rectangle((150, 4, 250, 34), fill=(70, 75, 90))
    d.text((200, 135), "int( )", font=mb.font(e.MONO, 74), fill=YEL, anchor="mm")
    for k in range(5):        # status lights
        on = t_proc <= t < t_out and int(t * 12 + k) % 2 == 0
        d.ellipse((60 + k * 60, 225, 90 + k * 60, 255), fill=GREEN if on else (60, 66, 78))
    paste(st, glowify(m, YEL, 10, 1), mx, my, s)
    if t >= t_out + 0.5:
        lab = e._outlined("TEXT  ->  NUMBER", 56, WHITE, (40, 40, 50))
        paste(st, lab, 540, 1100, pop(t - t_out - 0.5, 0.3))


def draw_hook(st, t):
    paste(st, e._outlined("TYPE", 150, WHITE, (40, 40, 50)), 540, 540, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("CASTING", 170, YEL, (150, 95, 0)), 540, 720, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("DATA KA ROOP BADLO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=(255, 90, 95))
    paste(st, rb, 540, 905, pop(t - 0.55), 1, 2)
    # "5" morphs into 5
    if t > 0.9:
        morph = clamp((t - 1.7) / 0.25)
        chip = p3.code_chip('"5"', ORANGE) if morph < 0.5 else p3.code_chip("5", CYAN)
        sc = pop(t - 0.9, 0.3) * (1 + 0.35 * math.sin(math.pi * morph))
        paste(st, chip, 300, 1230, sc * 1.4)
    if "m430" not in e._C:
        e._C["m430"] = mb.mascot(430)
    paste(st, e._C["m430"], 820, 1330, pop(t - 1.0, 0.4))


def render_board(t, board):
    st = Image.new("RGBA", (W, H))
    if board == "hook":
        draw_hook(st, t)
        return st
    if board in CODEBOX:
        draw_codebox(st, t, CODEBOX[board])
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "what":
        draw_machine(st, t)
    elif board in ARROW:
        draw_arrow(st, t, board)
        if board == "problem":
            draw_warn(st, t)
        else:
            draw_confetti(st, t, PARTY_T, 540, 1180)
    elif board == "rules":
        for ev in NUMS:
            e.draw_circle_num(st, t, ev)
        if t >= SAVE_T:
            paste(st, e._outlined("SAVE KAR LO!", 70, YEL, (150, 95, 0)), 420, 1330, pop(t - SAVE_T, 0.3), 1, -3)
    elif board == "quiz":
        p3.draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 980, 1.0 + 0.03 * ease((t - 47.5) / 7.5)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = [(ev[0], ev[3]) for ev in WRITES if ev[1] == board]
    if board == "what":
        ys.append((MACHINE[0], 900))
    if board == "problem":
        ys.append((WARN_T, 1050))
    ys.sort()
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(1010, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.07
    pull = b1 - 2.0 if board != "rules" else SAVE_T - 0.8
    if t > pull:
        q = ease((t - pull) / 0.8)
        cy, zoom = cy + (900 - cy) * q, zoom + (1.0 - zoom) * q
    return cy, zoom


def mascot_layer(st, t, board):
    if board in ("hook", None):
        return
    if "m" not in e._C:
        e._C["m"] = mb.mascot(300)
    t_in = {"what": 8.4, "problem": 15.5, "fix": 28.0, "rules": 39.0, "quiz": 50.4}[board]
    s = pop(t - t_in, 0.4)
    if s <= 0:
        return
    react = None
    for tr, txt, col in REACT:
        if 0 <= t - tr < 1.5:
            react = (tr, txt, col)
    bob, rot = 8 * math.sin(t * 3), 0
    if react:
        a = t - react[0]
        if react[2] == GREEN:
            bob -= 30 * abs(math.sin(a * 10)) * math.exp(-a * 5)
        else:
            rot = 10 * math.sin(a * 25) * math.exp(-a * 5)
    paste(st, e._C["m"], 935, 1580 + bob, s, 1, rot)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 44, "ExtraBold"), 20)
        by = 1470 if board == "rules" else 1355
        paste(st, b, max(b.width / 2 + 20, 1030 - b.width / 2), by, pop(a, 0.22) * (1 - ease((a - 1.3) / 0.2)))


@e.lru_cache(None)
def title_box():
    im = Image.new("RGBA", (560, 150))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(10, 10, 12, 180))
    d.text((28, 48), "Type Casting", font=mb.font(mb.BALOO, 54, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "Data ka roop badlo", font=mb.font(mb.BALOO, 44, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 5"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(150, 155, 165, 220), anchor="lm")
    return im.rotate(90, expand=True)


# ------------------------------------------------------------------ audio
def whirr(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 90 + 40 * np.sin(2 * np.pi * 7 * tt)
    x = fx.signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.5 + fx.noise(n, 5) * 0.15
    return fx.filt(x, "lowpass", 900, 2) * np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.08) * 0.6


def alarm_beeps():
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    gate = ((tt % 0.3) < 0.14).astype(float)
    return np.sin(2 * np.pi * 880 * tt) * gate * np.exp(-tt * 1.5) * 0.35


def popper():
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    burst = fx.filt(fx.noise(n, 8), "bandpass", [1500, 9000]) * np.exp(-tt * 18)
    return burst * 0.9


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, fx.pop(), 0.25, 0.6)
    P(buf, fx.whoosh(0.3, 1), 0.45, 0.5)
    P(buf, fx.pop(), 0.9, 0.5)
    P(buf, fx.whoosh(0.25, 2), 1.5, 0.4)
    P(buf, bs.note_pop(1046.5), 1.7, 0.4)
    P(buf, popper(), 1.7, 0.5)
    for s, en, n in BOARDS[1:]:
        P(buf, e.eraser_swish(), s, 0.55)
        P(buf, e.cap_click(), s + 0.2, 0.5)
    for ev in WRITES:
        nch = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, nch / e.CPS) if ev[6] == HAND else max(0.25, nch / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0 in CODEBOX.values():
        P(buf, e.marker_squeak(0.5, int(t0 * 4)), t0, 1.0)
    for t0, idx in ARROW.values():
        P(buf, e.marker_squeak(0.35, int(t0 * 6)), t0, 1.0)
    for t0, *_ in NUMS:
        P(buf, e.marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    for k, (t0, *_r) in enumerate(RULES):
        P(buf, bs.note_pop([659.25, 783.99, 987.77][k]), t0 + 0.9, 0.4)
    t_in, t_enter, t_proc, t_out = MACHINE
    P(buf, fx.pop(), t_in, 0.6)
    P(buf, fx.whoosh(0.4, 3), t_enter, 0.4)
    P(buf, e.thud(), t_proc - 0.05, 0.7)
    P(buf, whirr(t_out - t_proc), t_proc, 0.8)
    P(buf, fx.ding(), t_out, 0.5)
    P(buf, fx.pop(), t_out + 0.5, 0.5)
    P(buf, fx.boom(), WARN_T, 0.8)
    P(buf, alarm_beeps(), WARN_T + 0.05, 0.9)
    P(buf, e.buzzer(), 19.65, 0.6)
    P(buf, popper(), PARTY_T, 0.9)
    P(buf, e.chime(), PARTY_T + 0.05, 0.8)
    for k in range(6):
        P(buf, fx.pop(), PARTY_T + 0.08 * k, 0.25)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, e.thud(), SAVE_T, 0.4)
    P(buf, fx.riser(0.6), QUIZ_SLAM - 0.6, 0.35)
    P(buf, fx.boom(), QUIZ_SLAM, 0.8)
    for t0, *_ in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    tt = COUNT0
    while tt < REVEAL - 0.05:
        P(buf, e.tick(), tt, 0.6)
        tt += 0.5
    P(buf, e.chime(), REVEAL, 0.9)
    P(buf, fx.boom()[: int(0.5 * SR)], REVEAL, 0.5)
    for tr, txt, col in REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


# ------------------------------------------------------------------ wire into the engine
p3.QUIZ_SLAM, p3.OPTIONS, p3.ANSWER, p3.COUNT0, p3.REVEAL = QUIZ_SLAM, OPTIONS, "B", COUNT0, REVEAL
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP05_TypeCasting.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL, e.WRITES = BOARDS, END0, TOTAL, WRITES
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = WARN_T, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(WARN_T, 0.9), (QUIZ_SLAM, 0.8), (REVEAL, 0.4), (PARTY_T, 0.3)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
e.frame = p3._frame            # plain engine frame (no EP 03 screenshot flash)

if __name__ == "__main__":
    e.main()
