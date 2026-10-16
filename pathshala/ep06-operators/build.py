#!/usr/bin/env python3
"""EP06 "Python Operators — 5 types in 1 short" in the EP03 glass-board theme (Facebook reel, ≈62 s).

Content follows the EP06 Operators short (edit13 on claude/great-mayer-mbbsdw), re-made
with the shared engine (pathshala/glassboard.py): thumbnail first, "Operator kya hai?"
with a 10 + 5 = 15 chip equation, a "5 TYPES!" slam, the ①-⑤ list built up on the
board with a mascot example per type and "SAVE KAR LO!", the confusing / // % trio,
a 10 % 3 quiz with a countdown, and the LIKE / SHARE / SUBSCRIBE end screen.

Run:   python3 pathshala/ep06-operators/make_voice.py --models <dir>   (optional)
       python3 pathshala/ep06-operators/build.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import glassboard as G  # noqa: E402
from glassboard import (CHALK, CYAN, DIM, GREEN, NAVY, ORANGE, PINK, RED, YEL, arrow, chip, circled, clamp,  # noqa: E402
                        ease, ease_out, glow_box, gtext, paste, pop, reg, solid_pill, underline, write)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, WORK = os.path.join(HERE, "output"), os.path.join(HERE, "work")
NAME = "PythonKiPathshala-EP06-Operators"
TITLE1, TITLE2 = "PYTHON OPERATORS", "5 types • 1 short • 1 board"
EP_LABEL, NEXT_TITLE = "EP 06", "EP 07: F-STRINGS"
THUMB_BUBBLE = "7 // 2 = ?"

VO_AT = {"w01": 0.10, "w02": 3.30, "w03": 6.95, "w04": 12.70, "w05": 15.40, "w06": 21.00, "w07": 26.20,
         "w08": 30.95, "w09": 34.80, "w10": 41.10, "w11a": 48.90, "w11b": 54.00, "w12": 56.80}
DUR = 61.0
SCENES = [("hook", 0.0), ("what", 3.2), ("slam", 12.6), ("list", 15.3), ("confuse", 41.0), ("quiz", 48.8),
          ("end", 56.7)]
WIPE_CUTS = [1, 2, 3, 4, 5]
FOLLOW = {"what": 1.08, "list": 1.15, "confuse": 1.1}
SLAM = 12.6
SHOT = 39.6
COUNT_T0 = 50.9
REVEAL = COUNT_T0 + 3.0

# ---------------------------------------------------------------- the 5 families
FAM = [("Arithmetic", CYAN, "+   -   *   /   //   %   **", "7 // 2  =  3", "w05"),
       ("Assignment", ORANGE, "=   +=   -=   *=   /=", "x += 5  matlab  x = x + 5", "w06"),
       ("Comparison", YEL, "==   !=   >   <   >=   <=", "5 > 3  =  True", "w07"),
       ("Logical", GREEN, "and    or    not", "True and False  =  False", "w08"),
       ("Membership", PINK, "in    not in", '"a" in "apple"  =  True', "w09")]
LIST_TOP, FAM_H = 270, 222
FAM_T = []
for _k, (_name, _col, _sym, _ex, _vo) in enumerate(FAM):
    _y = LIST_TOP + _k * FAM_H
    _th = VO_AT[_vo] + 0.05
    _ts = reg(_th, 175, _y + 6, _name, 64, "hand", cps=16) + 0.1
    _te = reg(_ts, 175, _y + 84, _sym, 44, "mono", cps=26) + 0.4
    _te = max(_te, VO_AT[_vo] + G.vo_len(WORK, _vo) * 0.55)
    reg(_te, 175, _y + 146, _ex, 40, "hand", cps=24)
    FAM_T.append((_y, _th, _ts, _te))

# what scene
reg(VO_AT["w02"] + 0.05, 90, 300, "Operator kya hai?", 74, cps=22)
reg(VO_AT["w02"] + 1.0, 90, 400, "= data par KAAM karne wala symbol", 56, cps=26)
EQ_T = VO_AT["w03"] + 0.4
# confuse scene
reg(41.15, 90, 300, "Sabse CONFUSING teen:", 72, cps=22)
CONF = [("7 / 2", "3.5", "divide (decimal)", 43.0), ("7 // 2", "3", "floor divide (poora)", 45.0),
        ("7 % 2", "1", "remainder (bacha)", 46.9)]
for _k, (_a, _b, _lab, _tt) in enumerate(CONF):
    reg(_tt, 140, 500 + _k * 260, _a, 84, "mono", cps=12)
# quiz
reg(48.95, 120, 470, "10 % 3  =  ?", 96, "mono", cps=10)
QUIZ = [("A", "3"), ("B", "1"), ("C", "3.33")]

HINTS = [(0.4, "Sab operators!", "happy"), (VO_AT["w02"] + 1.4, "Symbol = operator", "happy"),
         (EQ_T + 4.6, "10 + 5 = 15", "happy"), (SLAM + 0.1, "Whoa!", "wow"),
         (FAM_T[0][3] + 0.2, "7 // 2 = 3", "happy"), (FAM_T[1][3] + 0.2, "x += 5", "happy"),
         (FAM_T[2][3] + 0.2, "5 > 3 = True", "wow"), (FAM_T[3][3] + 0.2, "and = dono True", "happy"),
         (FAM_T[4][3] + 0.2, "'a' apple mein!", "happy"), (41.5, "Dhyan se!", "wow"), (49.6, "Socho...", "happy"),
         (REVEAL + 0.1, "Sahi! 1", "happy"), (57.2, "Kal milte hain!", "happy")]
QUIET = [(SHOT - 0.3, SHOT + 1.4)]
FLASHES = [(SLAM, 0.75, 0.22, (255, 255, 255)), (SHOT, 0.95, 0.3, (255, 255, 255)), (REVEAL, 0.35, 0.18, (140, 255, 180))]
PUNCHES = [(SLAM, 0.12), (SHOT, 0.06), (REVEAL, 0.06)]
SHAKES = [(SLAM, 26), (SLAM + 0.35, 18), (REVEAL, 10)]
MUSIC_GAPS = [(SLAM - 0.6, SLAM), (REVEAL - 0.5, REVEAL)]
NO_FOLLOW = [(SHOT - 1.2, SHOT + 2)]


# ---------------------------------------------------------------- scenes
def sc_hook(L, t, tl):
    s = 1 + 0.03 * math.sin(tl * 4)
    paste(L, gtext("PYTHON", 120, CHALK, "mont"), 540, 470, s)
    paste(L, gtext("OPERATORS", 150, YEL, "mont"), 540, 640, s, rot=-2)
    paste(L, solid_pill("5 TYPES  •  1 SHORT", 50, NAVY, CYAN), 540, 810)
    chips = [("+", CYAN, 220, 1010), ("//", ORANGE, 520, 980), ("%", PINK, 830, 1030), ("==", YEL, 300, 1240),
             ("and", GREEN, 780, 1250), ("**", CYAN, 540, 1200)]
    for k, (sym, c, x, y) in enumerate(chips):
        a = t * 1.6 + k * 1.3
        paste(L, chip(sym, c, 70), x + 16 * math.sin(a), y + 20 * math.cos(a * 0.8), 1,
              rot=6 * math.sin(a * 0.7))


def sc_what(L, t, tl):
    write(L, t, VO_AT["w02"] + 0.05, 90, 300, "Operator kya hai?", 74, CHALK, cps=22)
    t2 = VO_AT["w02"] + 1.0
    if write(L, t, t2, 90, 400, "= data par KAAM karne wala symbol", 56, CHALK, cps=26):
        x0 = 90 + G.text_w("= data par ", 56, "hand")
        L.alpha_composite(gtext("KAAM", 56, YEL), (int(x0) - 8, 392))
        underline(L, t, t2 + 33 / 26, x0, 478, G.text_w("KAAM", 56, "hand"), YEL)
    # 10 + 5 = 15
    items = [("10", CYAN, 190, EQ_T + 0.2), ("+", YEL, 380, EQ_T + 0.8), ("5", CYAN, 560, EQ_T + 1.3),
             ("=", DIM, 730, EQ_T + 4.2), ("15", GREEN, 900, EQ_T + 4.6)]
    for s, c, x, ta in items:
        if t > ta:
            paste(L, chip(s, c, 84), x, 780, pop(t - ta))
    if t > EQ_T + 2.0:
        for x in (190, 560):
            arrow(L, (x, 900), (x, 860), (t - EQ_T - 2.0) / 0.2, CYAN, 5)
            paste(L, gtext("operand", 42, CYAN), x, 950, pop(t - EQ_T - 2.2))
    if t > EQ_T + 3.2:
        arrow(L, (380, 640), (380, 690), (t - EQ_T - 3.2) / 0.2, YEL, 5)
        paste(L, gtext("OPERATOR", 52, YEL, "mont"), 380, 600, pop(t - EQ_T - 3.4))
    if t > EQ_T + 5.0:
        glow_box(L, (160, 1080, 920, 1230), GREEN, ease((t - EQ_T - 5.0) / 0.35), w=4, fill_a=25)
        if t > EQ_T + 5.4:
            paste(L, gtext("operand  OPERATOR  operand", 48, CHALK), 540, 1155, pop(t - EQ_T - 5.4))


def sc_slam(L, t, tl):
    write(L, t, SLAM + 0.0, 150, 380, "Python mein operators ke", 60, CHALK, cps=40)
    s = 1 + 2.4 * (1 - ease_out(tl / 0.22))
    paste(L, gtext("5 TYPES!", 170, YEL, "mont"), 540, 640, s, a=clamp(tl / 0.06), rot=-3)
    pos = [(300, 900), (780, 900), (300, 1040), (780, 1040), (540, 1180)]
    for k, ((name, col, *_), (x, y)) in enumerate(zip(FAM, pos)):
        if tl > 0.8 + k * 0.22:
            paste(L, solid_pill(f"{k + 1}  {name.upper()}", 36, NAVY, col), x, y, pop(tl - 0.8 - k * 0.22))
    if tl < 1.2:
        rng = np.random.default_rng(4)
        d = ImageDraw.Draw(L)
        for _ in range(50):
            a = rng.uniform(0, 2 * math.pi)
            r0 = rng.uniform(300, 900) * (1 - math.exp(-tl * 5))
            col = [YEL, CYAN, PINK, GREEN][rng.integers(4)]
            x, y = 540 + math.cos(a) * r0, 640 + math.sin(a) * r0
            d.line([(540 + math.cos(a) * r0 * 0.85, 640 + math.sin(a) * r0 * 0.85), (x, y)],
                   fill=col + (int(255 * clamp(1.2 - tl)),), width=5)


def sc_list(L, t, tl):
    for k, ((name, col, sym, ex, vo), (y, th, ts, te)) in enumerate(zip(FAM, FAM_T)):
        if t > th - 0.3:
            circled(L, k + 1, 120, y + 44, col, pop(t - th + 0.3, 0.25))
        if write(L, t, th, 175, y + 6, name, 64, col, cps=16):
            underline(L, t, th + len(name) / 16, 175, y + 80, G.text_w(name, 64, "hand"), col, width=4)
        write(L, t, ts, 175, y + 84, sym, 44, CHALK, "mono", cps=26)
        write(L, t, te, 175, y + 146, ex, 40, col, cps=24)
    a = t - SHOT
    if a > 0:
        paste(L, solid_pill("SAVE KAR LO!", 64, NAVY, YEL), 560, 1440, 1 + 1.6 * (1 - ease_out(a / 0.2)), rot=-4)


def sc_confuse(L, t, tl):
    if write(L, t, 41.15, 90, 300, "Sabse CONFUSING teen:", 72, CHALK, cps=22):
        x0 = 90 + G.text_w("Sabse ", 72, "hand")
        L.alpha_composite(gtext("CONFUSING", 72, RED), (int(x0) - 8, 292))
    for k, (a_, b_, lab, tt) in enumerate(CONF):
        y = 500 + k * 260
        if write(L, t, tt, 140, y, a_, 84, CHALK, "mono", cps=12):
            done = tt + len(a_) / 12
            if t > done + 0.15:
                paste(L, gtext("=  " + b_, 84, YEL, "mono"), 560, y - 8, pop(t - done - 0.15), anchor="lt")
                paste(L, gtext(lab, 44, DIM), 150, y + 110, pop(t - done - 0.4), anchor="lt")
                paste(L, G.E2.tick_badge(34, True), 930, y + 50, pop(t - done - 0.5))


def sc_quiz(L, t, tl):
    paste(L, gtext("QUIZ TIME!", 130, YEL, "mont"), 540 + 6 * math.sin(tl * 40) * math.exp(-tl * 5), 330,
          G.back_out(tl / 0.35), rot=-3)
    write(L, t, 48.95, 120, 470, "10 % 3  =  ?", 96, CHALK, "mono", cps=10)
    for k, (letter, ans) in enumerate(QUIZ):
        age = t - (49.9 + k * 0.25)
        if age <= 0:
            continue
        y = 720 + k * 150
        right = ans == "1"
        col = (GREEN if right else RED) if t >= REVEAL else CHALK
        glow_box(L, (150, y - 55, 930, y + 55), col, ease(age / 0.3), w=5, r=28,
                 fill_a=60 if (t >= REVEAL and right) else 25)
        if age > 0.25:
            d = ImageDraw.Draw(L)
            d.ellipse((180, y - 32, 244, y + 32), outline=col + (255,), width=4)
            d.text((212, y), letter, font=G.font(40, "mont"), fill=col + (255,), anchor="mm")
            L.alpha_composite(gtext(ans, 64, col, "mono"), (290, int(y - 40)))
            if t >= REVEAL:
                paste(L, G.E2.tick_badge(36, right), 870, y, pop(t - REVEAL - k * 0.08))
    age = t - COUNT_T0
    if 0 < age < 3.0:
        k = min(2, int(age))
        R = 105
        ring = Image.new("RGBA", (2 * R + 30, 2 * R + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        d.ellipse((15, 15, 2 * R + 15, 2 * R + 15), outline=(50, 58, 75, 255), width=12)
        d.arc((15, 15, 2 * R + 15, 2 * R + 15), -90, -90 + 360 * (1 - (age % 1.0)), fill=ORANGE + (255,), width=12)
        d.text((R + 15, R + 15), str(3 - k), font=G.font(120, "mont"), fill=CHALK + (255,), anchor="mm")
        paste(L, ring, 540, 1300, (1 + 0.2 * math.exp(-(age % 1) * 8)) * pop(age, 0.2))
        paste(L, gtext("Comment karo!", 56, CHALK), 540, 1460, 1, a=ease((age - 0.3) / 0.3))
    if t >= REVEAL:
        a = t - REVEAL
        paste(L, gtext("10 mein 3, teen baar", 64, GREEN), 540, 1270, pop(a - 0.3))
        paste(L, gtext("aur  1  bacha!", 64, YEL), 540, 1370, pop(a - 0.6))


SCENE_FN = {"hook": sc_hook, "what": sc_what, "slam": sc_slam, "list": sc_list, "confuse": sc_confuse,
            "quiz": sc_quiz, "end": G.sc_end}


def thumb(L):
    paste(L, gtext("PYTHON", 120, CHALK, "mont"), 540, 450)
    paste(L, gtext("OPERATORS", 150, YEL, "mont"), 540, 620, rot=-2)
    paste(L, solid_pill("5 TYPES  •  1 SHORT", 50, NAVY, CYAN), 540, 790)
    paste(L, gtext("7 / 2   7 // 2   7 % 2", 62, CHALK, "mono"), 540, 960)
    for k, (sym, c, x, y) in enumerate([("+", CYAN, 240, 1140), ("//", ORANGE, 540, 1110), ("%", PINK, 830, 1150),
                                        ("==", YEL, 330, 1330), ("and", GREEN, 740, 1330)]):
        paste(L, chip(sym, c, 70), x, y)
    paste(L, solid_pill("EP 06", 60, (255, 255, 255), (220, 40, 50)), 230, 1520, rot=-6)


def sfx(s):
    add, E2 = G.add, G.E2
    for k in range(6):
        add(s, E2.pop_sfx(520 + 70 * k), 0.3 + k * 0.1, 0.3)
    notes = [(0.2, 523), (0.8, 659), (1.3, 784), (4.2, 880), (4.6, 1047)]
    for dt, f in notes:
        add(s, E2.pop_sfx(f), EQ_T + dt, 0.5)
    add(s, E2.ding(), EQ_T + 4.65, 0.7)
    add(s, G.thud(), EQ_T + 3.4, 0.5)
    add(s, E2.riser(0.6), SLAM - 0.6, 0.7)
    add(s, E2.impact(), SLAM, 1.0)
    add(s, E2.impact(), SLAM + 0.35, 0.6)
    for k in range(5):
        add(s, E2.pop_sfx(500 + 90 * k), SLAM + 0.8 + k * 0.22, 0.4)
    for k, (y, th, ts, te) in enumerate(FAM_T):
        add(s, G.thud(), th, 0.6)
        add(s, E2.pop_sfx(600 + 100 * k), te, 0.35)
    add(s, E2.riser(0.9), SHOT - 0.9, 0.5)
    add(s, G.shutter(), SHOT, 1.0)
    add(s, E2.impact(), SHOT, 0.4)
    for a_, b_, lab, tt in CONF:
        add(s, E2.ding(), tt + len(a_) / 12 + 0.15, 0.5)
    add(s, E2.impact(), 48.8, 0.5)
    for k in range(3):
        add(s, E2.pop_sfx(560), 49.9 + k * 0.25, 0.35)
        add(s, E2.clock_tick(), COUNT_T0 + k, 0.7)
    add(s, E2.riser(0.5), REVEAL - 0.5, 0.5)
    add(s, E2.impact(), REVEAL, 0.6)
    add(s, E2.ding(), REVEAL + 0.05, 0.7)


if __name__ == "__main__":
    G.run(sys.modules[__name__])
