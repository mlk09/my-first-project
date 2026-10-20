#!/usr/bin/env python3
"""Python ki Pathshala EP 10 - and / or / not  (1080x1920 Short, works without a voice-over)

No reference: built in the series look. EP 02 lightboard engine (glowing hand-writing, yellow title box,
mascot) on the animated BLACK GRID (brand/dark_grid.py) used for the re-cut EP 08 / EP 09.
Content: club-entry bouncer rule (and), ID bhool gaye -> Entry band, 3 rules + mini truth table,
Sunday YA chhutti (or), quiz.

Usage:  python3 edit17/build_ep10.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit14"))
sys.path.insert(0, os.path.join(HERE, "..", "brand"))
import build_ep07 as p7   # noqa: E402  EP 07 module: EP 02 engine + code box + sparkles
import dark_grid as dg    # noqa: E402

e, p3 = p7.e, p7.p3
mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp, glowify = e.paste, e.pop, e.ease, e.clamp, p7.glowify
W, H, SR = e.W, e.H, e.SR
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
es.NEXT = "EP 11: WHILE LOOP"
HAND, CODE = "hand", "code"
CX = 120

# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 16.0, "club"), (16.0, 25.5, "rules"), (25.5, 33.5, "ordemo"),
          (33.5, 42.0, "quiz")]
END0 = 42.0
TOTAL = END0 + es.DUR

CLUB = [(720, "age = 20"), (785, "has_id = True"), (850, "if age >= 18 and has_id:"),
        (915, '    print("Entry")'), (980, 'else: print("Band")')]
ORC = [(520, 'day = "Sunday"'), (585, "holiday = False"), (650, 'if day == "Sunday" or holiday:'),
       (715, '    print("Late utho!")')]
QUIZ_CODE = [(560, "x = 5"), (630, "print(x > 3 and x > 10)")]

WRITES = [
    (3.9, "club", 110, 500, [("Entry tabhi milegi jab:", WHITE)], 64, HAND),
    (5.2, "club", 110, 600, [("Age 18+ ", WHITE), ("AND", CYAN), (" ID card", WHITE)], 70, HAND),
    (16.3, "rules", 110, 400, [("Yaad rakho:", YEL)], 80, HAND),
    (17.0, "rules", 110, 540, [("and", CYAN), (" = dono sach chahiye", WHITE)], 62, HAND),
    (18.6, "rules", 110, 690, [("or", ORANGE), (" = ek bhi sach chalega", WHITE)], 62, HAND),
    (20.2, "rules", 110, 840, [("not", RED), (" = ulta kar deta hai", WHITE)], 62, HAND),
    (21.8, "rules", 140, 990, [("True and False  -> False", None)], 44, CODE),
    (22.5, "rules", 140, 1060, [("True or  False  -> True", None)], 44, CODE),
    (23.2, "rules", 140, 1130, [("not True        -> False", None)], 44, CODE),
    (25.8, "ordemo", 110, 400, [("Sunday ", YEL), ("YA", ORANGE), (" chhutti?", WHITE)], 76, HAND),
]
WRITES += [(7.2 + 0.5 * k, "club", CX, y, [(txt, None)], 44, CODE) for k, (y, txt) in enumerate(CLUB)]
WRITES += [(26.8 + 0.5 * k, "ordemo", CX, y, [(txt, None)], 44, CODE) for k, (y, txt) in enumerate(ORC)]
WRITES += [(34.5 + 0.5 * k, "quiz", CX, y, [(txt, None)], 46, CODE) for k, (y, txt) in enumerate(QUIZ_CODE)]
p7.CODEBOX = {"club": (6.95, 680, 1015), "ordemo": (26.55, 480, 750)}

CLUB_CHECKS = [(10.2, 278, 1100, "age >= 18  True", GREEN), (10.8, 805, 1100, "has_id  True", GREEN)]
AND_T = 10.8                     # "and" joins the two pills
OUT_T = 11.6                     # Output: Entry (green)
ID_FAIL = 13.4                   # has_id -> False, output flips to Entry band
OR_CHECKS = [(29.3, 330, 830, 'day == "Sunday"  True', GREEN), (29.9, 820, 830, "holiday  False", RED)]
OR_T = 29.9
OR_OUT = 30.8
SAVE_T = 24.2
CARD_T = 3.35
QUIZ_SLAM = 33.7
OPTIONS = [(36.7, "A", "True"), (37.0, "B", "False"), (37.3, "C", "Error")]
COUNT0, REVEAL = 37.7, 40.7
REACT = [(5.6, "Bouncer ka rule!", GREEN), (11.75, "Dono True = Entry!", GREEN), (13.6, "ID nahi = NO entry!", RED),
         (31.0, "Ek bhi True = kaafi!", GREEN), (40.75, "5 > 10 False hai!", GREEN)]


# ------------------------------------------------------------------ graphics
def pill(txt, col, size=36, fg=WHITE):
    f = mb.font(e.MONO, size)
    w = int(f.getlength(txt)) + 50
    im = Image.new("RGBA", (w, int(size * 1.7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, im.height - 3), 16, fill=col)
    d.text((w / 2, im.height / 2 + 1), txt, font=f, fill=fg, anchor="mm")
    return im


def club_card(st, t):
    a = t - CARD_T
    if a < 0:
        return
    im = Image.new("RGBA", (560, 120))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 116), 58, fill=(130, 60, 230), outline=WHITE, width=5)
    d.text((280, 62), "CLUB ENTRY", font=mb.font(mb.BALOO, 58, "ExtraBold"), fill=WHITE, anchor="mm")
    paste(st, glowify(im, (170, 110, 255), 12, 1), 420, 390, pop(a, 0.3), 1, -3)


def out_box(st, t, t0, txt, col, bg, y):
    o = Image.new("RGBA", (640, 120))
    od = ImageDraw.Draw(o)
    od.rounded_rectangle((2, 2, 637, 117), 24, fill=bg, outline=col, width=5)
    od.text((40, 62), "Output:", font=mb.font(e.HAND, 48), fill=col, anchor="lm")
    od.text((260, 62), txt, font=mb.font(e.MONO, 52), fill=WHITE, anchor="lm")
    paste(st, glowify(o, col, 12, 1), 440, y, pop(t - t0, 0.3))


def join_word(st, t, t0, word, col, x, y):
    if t >= t0:
        paste(st, e._outlined(word, 60, col, (20, 20, 30)), x, y, pop(t - t0, 0.3))


def draw_club(st, t):
    for t0, x, y, txt, col in CLUB_CHECKS:
        if t >= t0:
            if t >= ID_FAIL and "has_id" in txt:
                txt, col = "has_id  False", RED
            paste(st, pill(txt, col, 37), x, y, pop(t - t0, 0.25))
    join_word(st, t, AND_T + 0.15, "and", CYAN, 540, 1100)
    if ID_FAIL <= t:             # flip has_id to False on the code line
        a = t - ID_FAIL
        lay = Image.new("RGBA", st.size)
        ld = ImageDraw.Draw(lay)
        q = ease(clamp(a / 0.3))
        ld.line((CX + 255, 787, CX + 255 + 120 * q, 787), fill=RED, width=6)
        st.alpha_composite(lay)
        paste(st, pill("False", RED, 40), 600, 785, pop(a - 0.2, 0.25), 1, -4)
    if t >= ID_FAIL + 0.5:
        out_box(st, t, ID_FAIL + 0.5, "Entry band", RED, (40, 10, 14), 1225)
        paste(st, bs.icon_check(80, False), 820, 1225, pop(t - ID_FAIL - 0.7, 0.25))
    elif t >= OUT_T:
        out_box(st, t, OUT_T, "Entry", GREEN, (10, 30, 20), 1225)
        paste(st, bs.icon_check(80, True), 820, 1225, pop(t - OUT_T - 0.2, 0.25))
        p7.SPARK_T = OUT_T + 0.1
        p7.draw_sparkles(st, t)


def draw_ordemo(st, t):
    for t0, x, y, txt, col in OR_CHECKS:
        if t >= t0:
            paste(st, pill(txt, col, 34), x, y, pop(t - t0, 0.25))
    join_word(st, t, OR_T + 0.15, "or", ORANGE, 610, 830)
    if t >= OR_OUT:
        out_box(st, t, OR_OUT, "Late utho!", GREEN, (10, 30, 20), 960)
        p7.SPARK_T = OR_OUT + 0.1
        p7.draw_sparkles(st, t)


HOOK_CHIPS = [(0.9, "and", CYAN, 200, 1180), (1.05, "or", ORANGE, 440, 1270), (1.2, "not", RED, 210, 1400),
              (1.35, "True", GREEN, 450, 1500)]


def draw_hook(st, t):
    paste(st, e._outlined("PYTHON", 120, WHITE, (20, 20, 40)), 540, 480, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("AND OR NOT", 150, YEL, (150, 95, 0)), 540, 670, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("SIRF 3 WORDS = SMART CODE!", (20, 20, 20), False)],
                   mb.font(mb.BALOO, 50, "ExtraBold"), 92, 30, fill=(255, 90, 95))
    paste(st, rb, 540, 880, pop(t - 0.55), 1, 2)
    for t0, txt, col, x, y in HOOK_CHIPS:
        paste(st, p3.code_chip(txt, col), x, y + 10 * math.sin(t * 4 + x), pop(t - t0, 0.3), 1, 4 * math.sin(x))
    if "m430" not in e._C:
        e._C["m430"] = mb.mascot(430)
    paste(st, e._C["m430"], 840, 1350, pop(t - 1.0, 0.4))


def render_board(t, board):
    st = Image.new("RGBA", (W, H))
    if board == "hook":
        draw_hook(st, t)
        return st
    if board in p7.CODEBOX:
        p7.draw_codebox(st, t, board)
    if board == "club":
        club_card(st, t)
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "club":
        draw_club(st, t)
    elif board == "ordemo":
        draw_ordemo(st, t)
    elif board == "rules":
        if t >= SAVE_T:
            paste(st, e._outlined("SAVE KAR LO!", 70, YEL, (150, 95, 0)), 420, 1250, pop(t - SAVE_T, 0.3), 1, -3)
    elif board == "quiz":
        p3.draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 960, 1.0 + 0.02 * ease((t - QUIZ_SLAM) / 8.5)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = [(ev[0], ev[3]) for ev in WRITES if ev[1] == board]
    if board == "club":
        ys += [(CLUB_CHECKS[0][0], 1000), (OUT_T, 1050)]
    if board == "ordemo":
        ys += [(OR_OUT, 850)]
    ys.sort()
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(960, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.05
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
    t_in = {"club": 5.4, "rules": 17.4, "ordemo": 28.0, "quiz": 37.5}[board]
    s = pop(t - t_in, 0.4)
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
    paste(st, e._C["m"], 935, 1580 + bob, s, 1, rot)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 44, "ExtraBold"), 20)
        paste(st, b, max(b.width / 2 + 20, 1030 - b.width / 2), 1355, pop(a, 0.22) * (1 - ease((a - 1.6) / 0.2)))


@e.lru_cache(None)
def title_box():
    im = Image.new("RGBA", (560, 150))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(10, 10, 14, 210))
    d.text((28, 48), "and / or / not", font=mb.font(mb.BALOO, 56, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "Logical Operators", font=mb.font(mb.BALOO, 44, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  1 0"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(170, 170, 185, 220), anchor="lm")
    return im.rotate(90, expand=True)


# ------------------------------------------------------------------ audio
def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, fx.pop(), 0.25, 0.6)
    P(buf, fx.whoosh(0.3, 1), 0.45, 0.5)
    for k, (t0, *_r) in enumerate(HOOK_CHIPS):
        P(buf, fx.pop(), t0, 0.4)
        P(buf, bs.note_pop(700 + 120 * k), t0, 0.25)
    for s, en, n in BOARDS[1:]:
        P(buf, e.eraser_swish(), s, 0.55)
        P(buf, e.cap_click(), s + 0.2, 0.5)
    P(buf, fx.pop(), CARD_T, 0.7)
    P(buf, e.thud(), CARD_T, 0.5)
    for ev in WRITES:
        nch = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, nch / e.CPS) if ev[6] == HAND else max(0.25, nch / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, y0, y1 in p7.CODEBOX.values():
        P(buf, e.marker_squeak(0.5, int(t0 * 4)), t0, 1.0)
    for t0, *_r in CLUB_CHECKS + OR_CHECKS:
        P(buf, fx.pop(), t0, 0.5)
    for t0, *_r, col in CLUB_CHECKS + OR_CHECKS:
        P(buf, fx.ding() if col == GREEN else e.buzzer(), t0 + 0.05, 0.4 if col == GREEN else 0.5)
    P(buf, fx.whoosh(0.3, 50), AND_T + 0.05, 0.45)
    P(buf, fx.whoosh(0.3, 51), OR_T + 0.05, 0.45)
    P(buf, fx.pop(), OUT_T, 0.6)
    P(buf, e.chime(), OUT_T + 0.1, 0.7)
    P(buf, fx.whoosh(0.35, 52), ID_FAIL - 0.1, 0.5)
    P(buf, fx.boom(), ID_FAIL + 0.5, 0.7)
    P(buf, e.buzzer(), ID_FAIL + 0.6, 0.7)
    P(buf, fx.pop(), OR_OUT, 0.6)
    P(buf, e.chime(), OR_OUT + 0.1, 0.7)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.4)
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
    for tr, txt, col in REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


# ------------------------------------------------------------------ wire into the engine
p3.QUIZ_SLAM, p3.OPTIONS, p3.ANSWER, p3.COUNT0, p3.REVEAL = QUIZ_SLAM, OPTIONS, "B", COUNT0, REVEAL
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP10_And_Or_Not.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL, e.WRITES = BOARDS, END0, TOTAL, WRITES
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = ID_FAIL + 0.5, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(ID_FAIL + 0.5, 0.8), (QUIZ_SLAM, 0.8), (REVEAL, 0.4)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
e.board_bg = lambda: dg.background(p7._T[0])      # animated black grid
frame = p7.frame        # EP 07 wrapper (drives the background clock) around the engine frame

if __name__ == "__main__":
    e.main()
