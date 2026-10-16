#!/usr/bin/env python3
"""EP04 "input(): user se baat karo" in the EP03 glass-board theme (Facebook reel, ≈55 s).

Content follows the EP04 Input short (edit11 on claude/great-mayer-mbbsdw), re-made
on the glass board with the shared engine (pathshala/glassboard.py): the thumbnail
opens the video, the code is typed into a glowing editor with the camera following
the cursor, the terminal waits for the user, a TypeError gets a red flash and is
fixed with int(), and a recap card ends in "SCREENSHOT LE LO!".

Run:   python3 pathshala/ep04-input/make_voice.py --models <dir>     (optional)
       python3 pathshala/ep04-input/build.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import glassboard as G  # noqa: E402
from glassboard import (CHALK, CYAN, DIM, GREEN, NAVY, ORANGE, PINK, RED, YEL, Line, arrow, chip, circled,  # noqa: E402
                        clamp, ease, ease_out, glow_box, gtext, keycap, panel, paste, pop, reg, solid_pill, write)
from PIL import ImageDraw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, WORK = os.path.join(HERE, "output"), os.path.join(HERE, "work")
NAME = "PythonKiPathshala-EP04-Input"
TITLE1, TITLE2 = "PYTHON input()", "user se baat karo • 1 short"
EP_LABEL, NEXT_TITLE = "EP 04", "EP 05: TYPE CASTING"
THUMB_BUBBLE = "Naam kya hai?"

VO_AT = {"v01": 0.10, "v02": 3.70, "v03": 9.10, "v04": 12.40, "v05": 16.30, "v06": 21.10, "v07": 26.10,
         "v08": 30.70, "v09": 35.60, "v10": 41.90, "v11": 44.60, "v12": 49.10}
DUR = 54.0
SCENES = [("hook", 0.0), ("prompt", 3.6), ("run", 9.0), ("string", 21.0), ("bug", 26.0), ("recap", 44.5),
          ("end", 49.0)]
WIPE_CUTS = [1, 2, 3, 4, 5]
FOLLOW = {"run": 1.12, "bug": 1.12, "recap": 1.08}

# code colours
FN, STR, VAR, OP, NUM = YEL, GREEN, CYAN, DIM, ORANGE

# ---------------------------------------------------------------- run scene (Naam kya hai?)
ED = (50, 300, 1030, 640)           # editor panel
TERM = (50, 700, 1030, 1150)        # terminal panel
R_L1 = Line([("name", VAR), (" = ", OP), ("input", FN), ("(", OP), ('"Naam kya hai? "', STR), (")", OP)],
            90, 395, VO_AT["v03"] + 0.3, 40, cps=18)
R_L2 = Line([("print", FN), ("(", OP), ('"Namaste"', STR), (", ", OP), ("name", VAR), (")", OP)],
            90, 465, R_L1.end + 0.15, 40, cps=18)
R_RUN = VO_AT["v04"] + 0.4
R_T1 = Line([("$ python main.py", DIM)], 90, 790, R_RUN + 0.35, 38, cps=40)
R_ASK = R_T1.end + 0.15
R_TYPE = VO_AT["v05"] + 0.6
reg(R_TYPE, 90 + G.text_w("Naam kya hai? ", 40, "mono"), 860, "Aman", 40, "mono", cps=5)
R_ENTER = R_TYPE + 4 / 5 + 0.25
R_OUT = R_ENTER + 0.35

# ---------------------------------------------------------------- bug scene (age + 1)
B_L1 = Line([("age", VAR), (" = ", OP), ("input", FN), ("(", OP), ('"Age? "', STR), (")", OP)],
            90, 395, VO_AT["v07"] + 0.3, 44, cps=16)
B_L2 = Line([("print", FN), ("(", OP), ("age", VAR), (" + ", OP), ("1", NUM), (")", OP)], 90, 470,
            B_L1.end + 0.15, 44, cps=16)
B_RUN = B_L2.end + 0.35
B_T1 = Line([("$ python main.py", DIM)], 90, 790, B_RUN + 0.3, 38, cps=40)
B_TYPE = B_T1.end + 0.5
reg(B_TYPE, 90 + G.text_w("Age? ", 40, "mono"), 860, "20", 40, "mono", cps=5)
B_ENTER = B_TYPE + 0.65
ERR = B_ENTER + 0.3
VO_AT["v08"] = ERR + 0.05             # "Error!" is said on the hit
FIX = VO_AT["v09"] + 0.2
FIX_INT = reg(FIX + 0.3, 90 + G.text_w("age = ", 44, "mono"), 395, "int(", 44, "mono", cps=10)
FIX_CLOSE = reg(FIX_INT + 0.1, 90 + G.text_w('age = int(input("Age? ")', 44, "mono"), 395, ")", 44, "mono", cps=10)
F_RUN = FIX_CLOSE + 0.45
F_T1 = Line([("$ python main.py", DIM)], 90, 790, F_RUN + 0.3, 38, cps=40)
F_TYPE = F_T1.end + 0.35
reg(F_TYPE, 90 + G.text_w("Age? ", 40, "mono"), 860, "20", 40, "mono", cps=5)
F_ENTER = F_TYPE + 0.6
F_OUT = F_ENTER + 0.35
FLOAT_AT = VO_AT["v10"] + 0.2

# ---------------------------------------------------------------- recap
RECAP = [("input()", "TEXT", CYAN, 44.9), ("int(input())", "NUMBER", YEL, 45.9), ("float(input())", "DECIMAL", GREEN,
                                                                                  46.9)]
for _k, (_code, _lab, _col, _tt) in enumerate(RECAP):
    reg(_tt, 150, 420 + _k * 230, _code, 50, "mono", cps=22)
reg(44.55, 110, 260, "YAAD RAKHO:", 66, "mont", cps=20)
SHOT = 48.0

HINTS = [(0.4, "Naam kya hai?", "happy"), (VO_AT["v02"] + 1.0, "Sawaal + jawab!", "happy"),
         (R_ASK + 0.3, "Wait kar raha hai...", "wow"), (R_OUT + 0.1, "Namaste!", "happy"),
         (VO_AT["v06"] + 1.2, "Hamesha string!", "wow"), (ERR + 0.1, "Oops!", "wow"),
         (F_OUT + 0.1, "Perfect! 21", "happy"), (FLOAT_AT + 0.3, "3.5 = float()", "happy"),
         (49.6, "Kal milte hain!", "happy")]
QUIET = [(SHOT - 0.3, SHOT + 1.5)]
FLASHES = [(ERR, 0.55, 0.3, (255, 40, 40)), (SHOT, 0.95, 0.3, (255, 255, 255)), (R_OUT, 0.25, 0.15, (120, 255, 170)),
           (F_OUT, 0.25, 0.15, (120, 255, 170))]
PUNCHES = [(ERR, 0.12), (SHOT, 0.06), (21.0, 0.05)]
SHAKES = [(ERR, 30)]
MUSIC_GAPS = [(ERR - 0.6, ERR)]
NO_FOLLOW = [(ERR - 0.2, FIX)]


# ---------------------------------------------------------------- scenes
def sc_hook(L, t, tl):
    write(L, t, 0.15, 150, 380, "PYTHON MEIN", 86, CHALK, "mont", cps=20)
    if t > 0.75:
        k = min(7, int((t - 0.75) * 14))
        paste(L, gtext("input()"[:k] + ("|" if int(t * 4) % 2 else " "), 170, ORANGE, "mono"), 540, 600, 1)
    paste(L, solid_pill("USER SE BAAT KARO!", 54, NAVY, YEL), 540, 810, pop(tl - 1.4), rot=-4)
    chips = [("?", CYAN, 230, 1080), ("Aman", GREEN, 800, 1040), ('"20"', PINK, 300, 1300), ("ENTER", YEL, 760, 1280)]
    for k, (s, c, x, y) in enumerate(chips):
        a = t * 1.6 + k * 1.7
        paste(L, chip(s, c, 60), x + 16 * math.sin(a), y + 20 * math.cos(a * 0.8), pop(tl - 1.7 - k * 0.12),
              rot=6 * math.sin(a * 0.7))


P_LINE = [("input", FN), ("(", OP), ('"Prompt"', STR), (")", OP)]
P_X = 540 - G.text_w('input("Prompt")', 80, "mono") / 2
P_OBJ = Line(P_LINE, P_X, 380, VO_AT["v02"] + 0.2, 80, cps=14)
reg(0.15, 150, 380, "PYTHON MEIN", 86, "mont", cps=20)
reg(21.2, 110, 470, "input()", 96, "mono", cps=14)


def sc_prompt(L, t, tl):
    P_OBJ.draw(L, t)
    xq = P_OBJ.x_of(2) + G.text_w('"Prompt"', 80, "mono") / 2
    arrow(L, (xq, 500), (xq, 640), (t - P_OBJ.end - 0.1) / 0.25, YEL)
    paste(L, solid_pill("SAWAAL jo screen pe dikhega", 46, NAVY, YEL), 540, 720, pop(t - P_OBJ.end - 0.4))
    a2 = t - (VO_AT["v02"] + 3.4)
    arrow(L, (540, 790), (540, 900), a2 / 0.25, GREEN)
    paste(L, solid_pill("User ka JAWAB = variable mein", 46, NAVY, GREEN), 540, 980, pop(a2 - 0.3))
    if a2 > 0.8:
        glow_box(L, (190, 1110, 890, 1290), CYAN, ease((a2 - 0.8) / 0.4), w=4, fill_a=25)
        if a2 > 1.2:
            paste(L, gtext("Program RUKTA hai", 56, CHALK), 540, 1170, pop(a2 - 1.2))
            paste(L, gtext("jab tak user ENTER na dabaye", 40, DIM), 540, 1240, pop(a2 - 1.4))


def terminal_prompt(L, t, t_ask, prompt, typed_at, typed, enter_at, out_at, out_text, out_col, ok=True):
    if t <= t_ask:
        return
    L.alpha_composite(gtext(prompt, 40, CHALK, "mono"), (82, 852))
    xw = 90 + G.text_w(prompt, 40, "mono")
    if t < typed_at:
        if int(t * 3) % 2:
            ImageDraw.Draw(L).rectangle((xw, 860, xw + 20, 905), fill=CHALK + (255,))
        paste(L, solid_pill("waiting...", 30, NAVY, YEL), 900, 880, 1 + 0.06 * math.sin(t * 8))
    else:
        write(L, t, typed_at, xw, 860, typed, 40, ORANGE, "mono", cps=5)
    if typed_at < t < enter_at + 0.5:
        press = 1 - 0.12 * math.exp(-((t - enter_at) / 0.06) ** 2)
        paste(L, keycap(), 840, 1060, pop(t - (enter_at - 0.5)) * press)
    if t > out_at:
        paste(L, gtext(out_text, 44, out_col, "mono"), 82, 922, pop(t - out_at, 0.2), anchor="lt")
        if ok:
            paste(L, G.E2.tick_badge(30, True), 100 + G.text_w(out_text, 44, "mono") + 40, 950, pop(t - out_at - 0.1))


def cursor_to(L, t, at, x, y):
    if at - 0.6 < t < at + 0.35:
        m = ease((t - (at - 0.6)) / 0.5)
        paste(L, G.E2.cursor(), x + 160 * (1 - m), y + 140 * (1 - m))


def sc_run(L, t, tl):
    panel(L, ED, "main.py", G.scene_start("run") + 0.05, t, CYAN, run_at=R_RUN)
    if tl > 0.35:
        R_L1.draw(L, t)
        R_L2.draw(L, t)
        L.alpha_composite(gtext("1\n", 30, DIM, "mono"), (62, 400))
        L.alpha_composite(gtext("2", 30, DIM, "mono"), (62, 470))
    cursor_to(L, t, R_RUN, ED[2] - 90, ED[1] + 32)
    panel(L, TERM, "TERMINAL", R_RUN + 0.05, t, GREEN)
    if t > R_RUN + 0.4:
        R_T1.draw(L, t)
        terminal_prompt(L, t, R_ASK, "Naam kya hai? ", R_TYPE, "Aman", R_ENTER, R_OUT, "Namaste Aman", GREEN)


def sc_string(L, t, tl):
    s0 = G.scene_start("string")
    write(L, t, s0 + 0.2, 110, 470, "input()", 96, ORANGE, "mono", cps=14)
    xa = 110 + G.text_w("input()", 96, "mono") + 20
    arrow(L, (xa, 535), (xa + 140, 535), (t - s0 - 0.8) / 0.25, RED, 8)
    paste(L, gtext("STRING", 96, RED, "mont"), xa + 160, 470, pop(t - s0 - 1.0), anchor="lt")
    paste(L, gtext("hamesha!", 60, CHALK), 540, 680, pop(t - s0 - 1.5))
    a = t - (VO_AT["v06"] + 2.6)
    glow_box(L, (230, 820, 850, 1020), YEL, ease(a / 0.35), w=5, fill_a=30)
    if a > 0.35:
        paste(L, gtext('20  =  "20"', 90, YEL, "mono"), 540, 920, pop(a - 0.35))
        paste(L, gtext("number bhi TEXT ban gaya", 46, DIM), 540, 1090, pop(a - 0.8))


def sc_bug(L, t, tl):
    panel(L, ED, "main.py", G.scene_start("bug") + 0.05, t, CYAN, run_at=B_RUN if t < FIX else F_RUN)
    if tl > 0.35:
        if t < FIX + 0.3:
            B_L1.draw(L, t)
        else:   # line 1 with int( ... ) inserted and highlighted
            xi = 90 + G.text_w("age = ", 44, "mono")
            wi = G.text_w("int(", 44, "mono")
            L.alpha_composite(gtext("age = ", 44, VAR, "mono"), (82, 387))
            L.alpha_composite(gtext('input("Age? ")', 44, CHALK, "mono"), (int(xi + wi) - 8, 387))
            d = ImageDraw.Draw(L)
            u = ease((t - FIX - 0.3) / 0.4)
            d.rounded_rectangle((xi - 4, 388, xi + wi * u + 4, 448), 8, fill=YEL + (70,))
            write(L, t, FIX + 0.3, xi, 395, "int(", 44, YEL, "mono", cps=10)
            xc = 90 + G.text_w('age = int(input("Age? ")', 44, "mono")
            if t > FIX_INT + 0.1:
                d.rounded_rectangle((xc - 4, 388, xc + G.text_w(")", 44, "mono") + 4, 448), 8, fill=YEL + (70,))
            write(L, t, FIX_INT + 0.1, xc, 395, ")", 44, YEL, "mono", cps=10)
        B_L2.draw(L, t)
    if t < FIX:
        cursor_to(L, t, B_RUN, ED[2] - 90, ED[1] + 32)
        panel(L, TERM, "TERMINAL", B_RUN + 0.05, t, RED if t > ERR else GREEN)
        if t > B_RUN + 0.35:
            B_T1.draw(L, t)
            terminal_prompt(L, t, B_T1.end + 0.1, "Age? ", B_TYPE, "20", B_ENTER, 1e9, "", RED, ok=False)
            if t > ERR:
                L.alpha_composite(gtext("TypeError: can only concatenate", 34, RED, "mono"), (82, 930))
                L.alpha_composite(gtext('str (not "int") to str', 34, RED, "mono"), (82, 985))
                s = 1 + 1.8 * (1 - ease_out((t - ERR) / 0.2))
                paste(L, solid_pill("ERROR!", 90, (255, 255, 255), (220, 40, 40)), 540, 1290, s, rot=-6)
                paste(L, gtext("STRING + NUMBER  =  NO!", 52, CHALK), 540, 1440, pop(t - ERR - 0.8))
    else:
        cursor_to(L, t, F_RUN, ED[2] - 90, ED[1] + 32)
        panel(L, TERM, "TERMINAL", FIX + 0.05, t, GREEN)
        if t > F_RUN + 0.35:
            F_T1.draw(L, t)
            terminal_prompt(L, t, F_T1.end + 0.1, "Age? ", F_TYPE, "20", F_ENTER, F_OUT, "21", GREEN)
        if t > F_OUT + 0.3:
            paste(L, gtext("Ab yeh NUMBER hai!", 60, YEL), 540, 1240, pop(t - F_OUT - 0.3))
        if t > FLOAT_AT:
            paste(L, solid_pill("3.5 ke liye:  float(input())", 42, NAVY, GREEN, "mono"), 470, 1350,
                  pop(t - FLOAT_AT))


def sc_recap(L, t, tl):
    write(L, t, G.scene_start("recap") + 0.05, 110, 260, "YAAD RAKHO:", 66, YEL, "mont", cps=20)
    for k, (code, lab, col, tt) in enumerate(RECAP):
        y = 420 + k * 230
        if t > tt - 0.2:
            circled(L, k + 1, 100, y + 30, col, pop(t - tt + 0.2, 0.25))
        if write(L, t, tt, 150, y, code, 50, CHALK, "mono", cps=22):
            done = tt + len(code) / 22
            arrow(L, (170, y + 85), (260, y + 140), (t - done) / 0.2, RED, 6)
            paste(L, gtext(lab, 66, col, "mont"), 280, y + 100, pop(t - done - 0.2), anchor="lt")
    a = t - SHOT
    if a > 0:
        paste(L, solid_pill("SCREENSHOT LE LO!", 58, NAVY, YEL), 540, 1240, 1 + 1.6 * (1 - ease_out(a / 0.2)),
              rot=-4)


SCENE_FN = {"hook": sc_hook, "prompt": sc_prompt, "run": sc_run, "string": sc_string, "bug": sc_bug,
            "recap": sc_recap, "end": G.sc_end}


def thumb(L):
    paste(L, gtext("PYTHON MEIN", 96, CHALK, "mont"), 540, 400)
    paste(L, gtext("input()", 190, ORANGE, "mono"), 540, 600)
    paste(L, solid_pill("USER SE BAAT KARO!", 58, NAVY, YEL), 540, 820, rot=-4)
    paste(L, gtext("Naam kya hai?  →  Aman", 54, GREEN, "mono"), 540, 1000)
    paste(L, solid_pill("EP 04", 60, (255, 255, 255), (220, 40, 50)), 300, 1220, rot=-6)


def sfx(s):
    add, E2 = G.add, G.E2
    add(s, G.thud(), 1.4, 0.5)
    for k in range(4):
        add(s, E2.pop_sfx(520 + 80 * k), 1.7 + k * 0.12, 0.35)
    add(s, E2.pop_sfx(600), P_OBJ.end + 0.4, 0.4)
    add(s, E2.pop_sfx(700), VO_AT["v02"] + 3.7, 0.4)
    for at in (R_RUN, B_RUN, F_RUN):
        add(s, E2.click_sfx(), at, 1.0)
        add(s, G.blip(900), at + 0.35, 0.5)
    for at in (R_ENTER, B_ENTER, F_ENTER):
        add(s, G.thud(), at, 0.8)
    add(s, E2.ding(), R_OUT, 0.7)
    add(s, E2.ding(), F_OUT, 0.7)
    add(s, E2.bell(), F_OUT + 0.15, 0.4)
    s0 = G.scene_start("string")
    add(s, E2.whoosh(0.3), s0 + 0.8, 0.4)
    add(s, G.thud(), s0 + 1.0, 0.7)
    add(s, G.thud(), VO_AT["v06"] + 2.95, 0.6)
    add(s, E2.riser(0.6), ERR - 0.6, 0.6)
    add(s, E2.impact(), ERR, 1.0)
    add(s, G.buzzer(), ERR + 0.02, 0.8)
    add(s, G.glitch(), ERR + 0.05, 0.6)
    add(s, E2.pop_sfx(560), FLOAT_AT, 0.4)
    for code, lab, col, tt in RECAP:
        add(s, G.thud(), tt + len(code) / 22 + 0.2, 0.5)
    add(s, E2.riser(0.8), SHOT - 0.8, 0.5)
    add(s, G.shutter(), SHOT, 1.0)


if __name__ == "__main__":
    G.run(sys.modules[__name__])
