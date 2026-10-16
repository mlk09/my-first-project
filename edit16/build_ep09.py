#!/usr/bin/env python3
"""Python ki Pathshala EP 09 - elif  (1080x1920 Short, works without a voice-over)

Decoded from "elif statement in Python | #interview" (Learn Technology): an interview-question card
("Explain the use of the elif statement in Python?"), answer bullets fading in one by one, a black code
card that grows line by line, a flat interviewer/candidate illustration, voice only, no cuts.
Theme = EP 02 lightboard (glowing hand-writing, yellow title box, mascot) on the neon cobalt motion
grid from EP 07 / EP 08.
Original content: "Interview Sawaal", a glowing checker that walks the grade code line by line
(False -> next, first True wins, rest SKIP), golden rules, the "Interview TRAP" (wrong order), quiz.

Usage:  python3 edit16/build_ep09.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit14"))
import build_ep07 as p7   # noqa: E402  EP 07 module: EP 02 engine + neon cobalt motion grid + code box

e, p3 = p7.e, p7.p3
mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp, glowify = e.paste, e.pop, e.ease, e.clamp, p7.glowify
W, H, SR = e.W, e.H, e.SR
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
es.NEXT = "EP 10: AND / OR / NOT"
HAND, CODE = "hand", "code"
CX = 120

# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 12.0, "what"), (12.0, 24.0, "flow"), (24.0, 31.0, "rules"),
          (31.0, 39.0, "trap"), (39.0, 47.5, "quiz")]
END0 = 47.5
TOTAL = END0 + es.DUR

FLOW = [(470, "marks = 82"), (545, "if marks >= 90:"), (610, '    print("A")'), (680, "elif marks >= 75:"),
        (745, '    print("B")'), (815, "elif marks >= 50:"), (880, '    print("C")'), (950, "else:"),
        (1015, '    print("Fail")')]
TRAP = [(470, "marks = 95"), (545, "if marks >= 50:"), (610, '    print("C")'), (680, "elif marks >= 90:"),
        (745, '    print("A")')]
QUIZ_CODE = [(540, "temp = 30"), (600, 'if temp > 35: print("Garmi")'), (660, 'elif temp > 25: print("Mast")'),
             (720, 'else: print("Thand")')]

WRITES = [
    (3.75, "what", 110, 520, [("elif kya hota hai?", WHITE)], 84, HAND),
    (5.6, "what", 110, 640, [("= ", WHITE), ("else", ORANGE), (" + ", WHITE), ("if", CYAN)], 84, HAND),
    (7.2, "what", 110, 760, [("Ek ke baad ek ", WHITE), ("CONDITION", YEL), (" check", WHITE)], 56, HAND),
    (8.8, "what", 110, 860, [("Jo pehle ", WHITE), ("TRUE", GREEN), (", wahi chalega!", WHITE)], 60, HAND),
    (24.3, "rules", 110, 400, [("Golden Rules:", YEL)], 80, HAND),
    (25.2, "rules", 190, 560, [("Pehli ", WHITE), ("TRUE", GREEN), (" condition jeetegi", WHITE)], 62, HAND),
    (26.8, "rules", 190, 720, [("Baaki sab ", WHITE), ("SKIP", RED)], 62, HAND),
    (28.2, "rules", 190, 880, [("elif kitne bhi, ", WHITE), ("else", ORANGE), (" optional", WHITE)], 62, HAND),
    (31.25, "trap", 110, 330, [("Interview ", WHITE), ("TRAP!", RED)], 80, HAND),
    (35.2, "trap", 110, 1020, [("Badi condition ", WHITE), ("PEHLE", YEL), (" likho!", WHITE)], 64, HAND),
    (36.7, "trap", 140, 1120, [("90  ->  75  ->  50", None)], 54, CODE),
]
WRITES += [(12.3 + 0.55 * k, "flow", CX, y, [(txt, None)], 44, CODE) for k, (y, txt) in enumerate(FLOW)]
WRITES += [(31.9 + 0.5 * k, "trap", CX, y, [(txt, None)], 44, CODE) for k, (y, txt) in enumerate(TRAP)]
WRITES += [(40.0 + 0.5 * k, "quiz", CX, y, [(txt, None)], 40, CODE) for k, (y, txt) in enumerate(QUIZ_CODE)]
NUMS = [(25.0, 120, 560, "1"), (26.6, 120, 720, "2"), (28.0, 120, 880, "3")]
p7.CODEBOX = {"flow": (12.05, 430, 1055), "trap": (31.6, 430, 785)}
POINT = [(17.2, 545), (18.3, 680)]                 # checker arrow positions (flow)
CHECKS = [(17.6, 545, "82 >= 90", False), (18.7, 680, "82 >= 75", True)]
WIN_LINE = (19.1, 745)
SKIP_T = 19.6
OUT_T = 20.4
TRAP_OUT = 33.8
SAVE_T = 29.4
INTERVIEW_T = 3.35
QUIZ_SLAM = 39.2
OPTIONS = [(42.2, "A", "Garmi"), (42.5, "B", "Mast"), (42.8, "C", "Thand")]
COUNT0, REVEAL = 43.2, 46.2
REACT = [(10.0, "Interview favourite!", GREEN), (17.65, "False, aage chalo", RED), (20.6, "Pehli True jeet gayi!", GREEN),
         (34.0, "95 marks par C?!", RED), (37.0, "Order sahi = jawab sahi", GREEN), (46.25, "30 > 25 = Mast!", GREEN)]


# ------------------------------------------------------------------ graphics
def pill(txt, col, size=44, fg=WHITE, font=None):
    f = font or mb.font(e.MONO, size)
    w = int(f.getlength(txt)) + 50
    im = Image.new("RGBA", (w, int(size * 1.7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, im.height - 3), 16, fill=col)
    d.text((w / 2, im.height / 2 + 1), txt, font=f, fill=fg, anchor="mm")
    return im


def interview_card(st, t):
    a = t - INTERVIEW_T
    if a < 0:
        return
    im = Image.new("RGBA", (560, 120))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 116), 58, fill=(235, 50, 70), outline=WHITE, width=5)
    d.text((280, 62), "INTERVIEW SAWAAL", font=mb.font(mb.BALOO, 54, "ExtraBold"), fill=WHITE, anchor="mm")
    paste(st, glowify(im, (255, 80, 100), 12, 1), 420, 390, pop(a, 0.3), 1, -3)


def draw_flow(st, t):
    d = ImageDraw.Draw(st)
    # checker arrow walking down the code
    if t >= POINT[0][0]:
        y = POINT[0][1]
        if t >= POINT[1][0] - 0.35:
            q = ease((t - POINT[1][0] + 0.35) / 0.35)
            y = POINT[0][1] + (POINT[1][1] - POINT[0][1]) * q
        x = 92 + 6 * math.sin(t * 10)
        lay = Image.new("RGBA", st.size)
        ImageDraw.Draw(lay).polygon([(x - 26, y - 20), (x + 4, y), (x - 26, y + 20)], fill=YEL)
        st.alpha_composite(glowify(lay, YEL, 10, 1).crop((30, 30, 30 + W, 30 + H)))
    for t0, y, txt, ok in CHECKS:
        if t >= t0:
            b = pill(f"{txt}  {'True' if ok else 'False'}", GREEN if ok else RED, 34)
            paste(st, b, 990 - b.width / 2, y, pop(t - t0, 0.25))
    if t >= WIN_LINE[0]:          # winner line glow
        a = int(90 * clamp((t - WIN_LINE[0]) / 0.25))
        hl = Image.new("RGBA", st.size)
        ImageDraw.Draw(hl).rounded_rectangle((CX + 90, WIN_LINE[1] - 34, CX + 470, WIN_LINE[1] + 22), 12,
                                             fill=(80, 220, 120, a))
        st.alpha_composite(hl)
    if t >= SKIP_T:              # dim + stamp the rest
        q = clamp((t - SKIP_T) / 0.3)
        dim = Image.new("RGBA", st.size)
        ImageDraw.Draw(dim).rectangle((84, 785, 996, 1050), fill=(4, 8, 30, int(170 * q)))
        st.alpha_composite(dim)
        stamp = e._outlined("SKIP!", 110, RED, (90, 0, 0))
        paste(st, stamp, 640, 915, pop(t - SKIP_T - 0.1, 0.3), 1, -12)
    if t >= OUT_T:
        o = Image.new("RGBA", (640, 120))
        od = ImageDraw.Draw(o)
        od.rounded_rectangle((2, 2, 637, 117), 24, fill=(10, 30, 20), outline=GREEN, width=5)
        od.text((40, 62), "Output:", font=mb.font(e.HAND, 48), fill=GREEN, anchor="lm")
        od.text((290, 62), "B", font=mb.font(e.MONO, 64), fill=WHITE, anchor="lm")
        paste(st, glowify(o, GREEN, 12, 1), 440, 1160, pop(t - OUT_T, 0.3))
        p7.SPARK_T = OUT_T + 0.1
        p7.draw_sparkles(st, t)
    del d


def draw_trap(st, t):
    if t >= TRAP_OUT:
        b = pill("95 >= 50  True", GREEN, 34)
        paste(st, b, 990 - b.width / 2, 545, pop(t - TRAP_OUT + 0.6, 0.25))
        o = Image.new("RGBA", (640, 120))
        od = ImageDraw.Draw(o)
        od.rounded_rectangle((2, 2, 637, 117), 24, fill=(40, 10, 14), outline=RED, width=5)
        od.text((40, 62), "Output:", font=mb.font(e.HAND, 48), fill=RED, anchor="lm")
        od.text((290, 62), "C", font=mb.font(e.MONO, 64), fill=WHITE, anchor="lm")
        paste(st, glowify(o, RED, 12, 1), 440, 880, pop(t - TRAP_OUT, 0.3))
        paste(st, bs.icon_check(80, False), 820, 880, pop(t - TRAP_OUT - 0.2, 0.25))


HOOK_CHIPS = [(0.9, "if", CYAN, 190, 1180), (1.05, "elif", YEL, 450, 1270), (1.2, "elif", YEL, 220, 1400),
              (1.35, "else", ORANGE, 460, 1500)]


def draw_hook(st, t):
    paste(st, e._outlined("PYTHON", 120, WHITE, (20, 30, 70)), 540, 500, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("ELIF", 210, YEL, (150, 95, 0)), 540, 700, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("INTERVIEW MEIN ZAROOR POOCHTE HAIN!", (20, 20, 20), False)],
                   mb.font(mb.BALOO, 46, "ExtraBold"), 92, 30, fill=(255, 90, 95))
    paste(st, rb, 540, 900, pop(t - 0.55), 1, 2)
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
    if board == "what":
        interview_card(st, t)
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "flow":
        draw_flow(st, t)
    elif board == "trap":
        draw_trap(st, t)
    elif board == "rules":
        for ev in NUMS:
            e.draw_circle_num(st, t, ev)
        if t >= SAVE_T:
            paste(st, e._outlined("SAVE KAR LO!", 70, YEL, (150, 95, 0)), 420, 1050, pop(t - SAVE_T, 0.3), 1, -3)
    elif board == "quiz":
        p3.draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 960, 1.0 + 0.02 * ease((t - 39) / 8.5)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = [(ev[0], ev[3]) for ev in WRITES if ev[1] == board]
    if board == "flow":
        ys += [(POINT[0][0], 600), (OUT_T, 1000)]
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
    t_in = {"what": 9.6, "flow": 17.0, "rules": 25.6, "trap": 33.6, "quiz": 43.0}[board]
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
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(6, 10, 30, 200))
    d.text((28, 48), "Python elif", font=mb.font(mb.BALOO, 56, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "Interview Special", font=mb.font(mb.BALOO, 44, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 9"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(140, 170, 230, 220), anchor="lm")
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
    P(buf, fx.pop(), INTERVIEW_T, 0.7)
    P(buf, e.thud(), INTERVIEW_T, 0.5)
    for ev in WRITES:
        nch = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, nch / e.CPS) if ev[6] == HAND else max(0.25, nch / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, y0, y1 in p7.CODEBOX.values():
        P(buf, e.marker_squeak(0.5, int(t0 * 4)), t0, 1.0)
    for t0, *_r in NUMS:
        P(buf, e.marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    P(buf, fx.whoosh(0.25, 40), POINT[0][0] - 0.1, 0.4)
    P(buf, fx.whoosh(0.3, 41), POINT[1][0] - 0.35, 0.4)
    for t0, y, txt, ok in CHECKS:
        P(buf, fx.ding() if ok else e.buzzer(), t0, 0.5 if ok else 0.6)
    P(buf, bs.note_pop(1046.5), WIN_LINE[0], 0.4)
    P(buf, fx.whoosh(0.35, 42), SKIP_T - 0.1, 0.5)
    P(buf, e.thud(), SKIP_T + 0.1, 0.7)
    P(buf, fx.pop(), OUT_T, 0.6)
    P(buf, e.chime(), OUT_T + 0.1, 0.7)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.4)
    P(buf, fx.ding(), TRAP_OUT - 0.6, 0.4)
    P(buf, fx.boom(), TRAP_OUT, 0.7)
    P(buf, e.buzzer(), TRAP_OUT + 0.2, 0.7)
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
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP09_Elif.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL, e.WRITES = BOARDS, END0, TOTAL, WRITES
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = TRAP_OUT, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(TRAP_OUT, 0.8), (QUIZ_SLAM, 0.8), (REVEAL, 0.4), (SKIP_T + 0.1, 0.4)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
frame = p7.frame        # EP 07 wrapper (drives the moving grid) around the engine frame

if __name__ == "__main__":
    e.main()
