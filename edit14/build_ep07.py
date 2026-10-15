#!/usr/bin/env python3
"""Python ki Pathshala EP 07 - f-strings  (1080x1920 Short, works without a voice-over)

Structure decoded from "Easy Python String Formatting with f-strings" (freeCodeCamp): the "old way"
(+ and str()) shown next to the "f-string way", the cursor highlighting each variable and its {braces},
then the output in a terminal; one continuous take, a fixed title banner, voice only.
Theme = EP 02 (lightboard hand-writing, yellow title box, mascot) on a MOVING NEON COBALT GRID.
New pieces: red circles on every "+", values flying into the {braces}, 3 f-string tricks, quiz,
Python ki Pathshala end screen.

Usage:  python3 edit14/build_ep07.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit9"))
sys.path.insert(0, os.path.join(HERE, "..", "edit10"))
import build_ep02 as e   # noqa: E402  EP 02 engine
import build_ep03 as p3  # noqa: E402  quiz cards + chips

mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp = e.paste, e.pop, e.ease, e.clamp
W, H, SR, FPS = e.W, e.H, e.SR, e.FPS
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
COBALT = (40, 110, 255)
es.NEXT = "EP 08: IF-ELSE"
HAND, CODE = "hand", "code"


def glowify(im, col=None, r=10, n=1):
    return e.glowify(im, col, r, n)[0]


# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 14.0, "old"), (14.0, 27.0, "new"), (27.0, 42.0, "tricks"),
          (42.0, 50.6, "quiz")]
END0 = 50.6
TOTAL = END0 + es.DUR
CX = 120                                   # code left edge inside the box
OLD1 = 'print("Naam: " + naam +'
OLD2 = '      ", Marks: " + str(marks))'
NEW = 'print(f"Naam: {naam}, Marks: {marks}")'
WRITES = [
    (3.45, "old", 100, 360, [("Purana tareeka:", RED)], 76, HAND),
    (3.95, "old", CX, 480, [('naam = "Riya"', None)], 44, CODE),
    (4.7, "old", CX, 550, [("marks = 95", None)], 44, CODE),
    (5.4, "old", CX, 620, [(OLD1, None)], 40, CODE),
    (6.5, "old", CX, 685, [(OLD2, None)], 40, CODE),
    (9.6, "old", 110, 880, [("Itne ", WHITE), ("+", RED), (" aur ", WHITE), ("str()", RED), ("?", WHITE)], 70, HAND),
    (10.6, "old", 110, 965, [("Thak gaye!", YEL)], 70, HAND),
    (14.25, "new", 100, 360, [("f-string tareeka:", GREEN)], 76, HAND),
    (14.75, "new", CX, 480, [('naam = "Riya"', None)], 44, CODE),
    (15.3, "new", CX, 550, [("marks = 95", None)], 44, CODE),
    (15.9, "new", CX, 635, [(NEW, None)], 38, CODE),
    (17.6, "new", 300, 860, [("quotes se pehle ", WHITE), ("f", YEL)], 60, HAND),
    (22.0, "new", 110, 1060, [("Output:", GREEN)], 62, HAND),
    (22.6, "new", 340, 1060, [("Naam: Riya, Marks: 95", None)], 46, CODE),
    (27.25, "tricks", 110, 400, [("f-string ke ", WHITE), ("3 JADOO", YEL), (":", WHITE)], 78, HAND),
    (42.8, "quiz", 160, 560, [("x = 4", None)], 66, CODE),
    (43.5, "quiz", 160, 660, [('print(f"{x * 2}")', None)], 62, CODE),
]
TRICKS = [  # (t, y, code, result, hint)
    (28.2, 560, 'f"{2 + 3}"', "5", "andar MATH bhi chalta hai"),
    (31.6, 760, 'f"{9.5:.2f}"', "9.50", "decimal ki ginti control"),
    (35.0, 960, 'f"{naam.upper()}"', "RIYA", "function bhi call karo"),
]
for t0, y, code, res, hint in TRICKS:
    WRITES += [(t0 + 0.2, "tricks", 195, y, [(code, None)], 52, CODE),
               (t0 + 1.2, "tricks", 700, y, [("= ", WHITE), (res, GREEN)], 64, HAND),
               (t0 + 1.6, "tricks", 200, y + 75, [(hint, (195, 205, 225))], 48, HAND)]
NUMS = [(t0, 120, y, str(k + 1)) for k, (t0, y, *_r) in enumerate(TRICKS)]
REACT = [(8.0, "Uff! Bahut lamba", RED), (24.0, "Kitna easy!", GREEN), (29.7, "Math andar!", GREEN),
         (33.1, "Do decimal!", GREEN), (36.5, "Capital ho gaya!", GREEN), (48.65, "{} ke andar x*2 = 8!", GREEN)]
CODEBOX = {"old": (3.75, 430, 725), "new": (14.55, 430, 675)}
PLUS_T = 8.6                     # red circles on every "+"
F_T, FLY_T = 17.2, 19.0          # yellow ring on f, values fly into {braces}
SPARK_T = 23.2
SAVE_T = 39.4
QUIZ_SLAM = 42.2
OPTIONS = [(44.6, "A", "x * 2"), (44.9, "B", "8"), (45.2, "C", "{x * 2}")]
COUNT0, REVEAL = 45.6, 48.6


# ------------------------------------------------------------------ neon cobalt motion grid
_T = [0.0]
GRID = 96


@e.lru_cache(None)
def grid_tile():
    yy, xx = np.mgrid[0:H + GRID, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    base = np.clip(1 - r * 1.1, 0, 1)[..., None] * np.array([10, 22, 70], np.float32) + np.array([4, 7, 22])
    lines = Image.new("L", (W, H + GRID), 0)
    d = ImageDraw.Draw(lines)
    for x in range(0, W + 1, GRID):
        d.line((x, 0, x, H + GRID), fill=255, width=2)
    for y in range(0, H + GRID + 1, GRID):
        d.line((0, y, W, y), fill=255, width=2)
    core = np.asarray(lines).astype(np.float32) / 255
    halo = np.asarray(lines.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255
    fade = (0.35 + 0.65 * np.clip(1 - r * 0.9, 0, 1))
    neon = (core * 0.55 + halo * 1.6) * fade
    img = base + neon[..., None] * np.array(COBALT, np.float32)
    return np.clip(img, 0, 255).astype(np.float32)


def board_bg():
    t = _T[0]
    off = int(t * 36) % GRID
    a = grid_tile()[off:off + H].copy()
    # a bright scan band sweeping down the grid every 4 s
    yb = (t % 4.0) / 4.0 * (H + 600) - 300
    band = np.exp(-((np.arange(H) - yb) / 140.0) ** 2)[:, None, None]
    a += band * np.array([20, 45, 120], np.float32) * 0.6
    # dust / sparkle points drifting up
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(4)
    for _ in range(60):
        x, y0, sp, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 60), rng.uniform(1.5, 3.5)
        y = (y0 - t * sp) % H
        d.ellipse((x, y, x + s, y + s), fill=(150, 190, 255, int(rng.uniform(60, 160))))
    return img


@e.lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.35 * r ** 2.4, 0.55, 1)[..., None]


# ------------------------------------------------------------------ board graphics
def rect_path(x0, y0, x1, y1):
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]


def draw_codebox(st, t, board):
    t0, y0, y1 = CODEBOX[board]
    p = clamp((t - t0) / 0.5)
    if p <= 0:
        return
    lay = Image.new("RGBA", st.size)
    d = ImageDraw.Draw(lay)
    d.rectangle((80, y0, 1000, y1), fill=(6, 10, 28, int(200 * p)))
    e.draw_lines(d, rect_path(80, y0, 1000, y1), p, WHITE + (255,), 5)
    st.alpha_composite(glowify(lay, None, 8, 1).crop((24, 24, 24 + W, 24 + H)))


def cx_of(line, idx, size):
    return CX + mb.font(e.MONO, size).getlength(line[:idx])


def draw_plus_rings(st, t):
    a = t - PLUS_T
    if a < 0:
        return
    d = ImageDraw.Draw(st)
    spots = [(OLD1, i, 620, 40) for i, ch in enumerate(OLD1) if ch == "+"] + \
            [(OLD2, i, 685, 40) for i, ch in enumerate(OLD2) if ch == "+"]
    for k, (line, i, y, size) in enumerate(spots):
        p = clamp((a - 0.12 * k) / 0.25)
        if p <= 0:
            continue
        x = cx_of(line, i, size) + 12
        r = 30
        d.arc((x - r, y - r - 12, x + r, y + r - 12), -90, -90 + 360 * p, fill=RED, width=6)
    s_line, s_idx = OLD2, OLD2.index("str")
    p = clamp((a - 0.6) / 0.3)
    if p > 0:
        x0 = cx_of(s_line, s_idx, 40) - 8
        x1 = cx_of(s_line, s_idx + 3, 40) + 8
        d.rounded_rectangle((x0, 685 - 44, x1, 685 + 12), 12, outline=RED, width=5)


def draw_new_marks(st, t):
    d = ImageDraw.Draw(st)
    size, y = 38, 635
    a = t - F_T
    if a >= 0:     # ring on the f + arrow down to the note
        x = cx_of(NEW, NEW.index('f"'), size) + 11
        p = clamp(a / 0.3)
        d.arc((x - 30, y - 50, x + 30, y + 10), -90, -90 + 360 * p, fill=YEL, width=6)
        if a > 0.3:
            q = ease((a - 0.3) / 0.3)
            d.line((x, y + 14, x, y + 14 + 150 * q), fill=YEL, width=6)
            if q > 0.8:
                d.polygon([(x, y + 16), (x - 16, y + 44), (x + 16, y + 44)], fill=YEL)
    b = t - FLY_T
    if b >= 0:     # {braces} light up, then the values fly in
        for k, (var, val, src_y) in enumerate((("{naam}", '"Riya"', 480), ("{marks}", "95", 550))):
            i = NEW.index(var)
            x0, x1 = cx_of(NEW, i, size) - 4, cx_of(NEW, i + len(var), size) + 4
            al = int(70 * clamp((b - 0.4 * k) / 0.25))
            hl = Image.new("RGBA", st.size)
            ImageDraw.Draw(hl).rounded_rectangle((x0, y - 28, x1, y + 26), 10, fill=(110, 200, 255, al),
                                                 outline=CYAN + (min(255, al * 4),), width=3)
            st.alpha_composite(hl)
            q = clamp((b - 0.4 * k - 0.3) / 0.6)
            if 0 < q < 1:
                sx = cx_of('naam = "Riya"', 7, 44) + 60 if k == 0 else cx_of("marks = 95", 8, 44) + 25
                tx = (x0 + x1) / 2
                xq = sx + (tx - sx) * ease(q)
                yq = src_y + (y - 14 - src_y) * ease(q) - 90 * math.sin(math.pi * q)
                paste(st, p3.code_chip(val, ORANGE if k == 0 else CYAN), xq, yq, 0.75)


def draw_sparkles(st, t):
    a = t - SPARK_T
    if not 0 <= a < 1.2:
        return
    d = ImageDraw.Draw(st)
    r = np.random.default_rng(6)
    for k in range(10):
        x, y = r.uniform(340, 960), r.uniform(1000, 1120)
        q = e.back(clamp((a - 0.05 * k) / 0.25)) * (1 - ease((a - 0.8) / 0.4))
        if q <= 0:
            continue
        s = r.uniform(18, 34) * q
        pts = []
        for j in range(8):
            rr = s if j % 2 == 0 else s * 0.3
            ang = -math.pi / 2 + j * math.pi / 4 + a * 3
            pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
        d.polygon(pts, fill=(255, 236, 140, 255))


HOOK_CHIPS = [(0.9, 'f"..."', YEL, 230, 1180), (1.05, "{naam}", CYAN, 470, 1290), (1.2, "{marks}", CYAN, 220, 1420),
              (1.35, ":.2f", ORANGE, 470, 1530)]


def draw_hook(st, t):
    paste(st, e._outlined("PYTHON", 120, WHITE, (20, 30, 70)), 540, 500, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("f-STRINGS", 170, YEL, (150, 95, 0)), 540, 690, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("PRINT KA SHORTCUT!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=(255, 90, 95))
    paste(st, rb, 540, 890, pop(t - 0.55), 1, 2)
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
    if board in CODEBOX:
        draw_codebox(st, t, board)
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "old":
        draw_plus_rings(st, t)
    elif board == "new":
        draw_new_marks(st, t)
        draw_sparkles(st, t)
    elif board == "tricks":
        for ev in NUMS:
            e.draw_circle_num(st, t, ev)
        if t >= SAVE_T:
            paste(st, e._outlined("SAVE KAR LO!", 70, YEL, (150, 95, 0)), 420, 1200, pop(t - SAVE_T, 0.3), 1, -3)
    elif board == "quiz":
        p3.draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 980, 1.0 + 0.03 * ease((t - 42) / 8.6)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = sorted([(ev[0], ev[3]) for ev in WRITES if ev[1] == board])
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(960, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.05
    pull = b1 - 2.0 if board != "tricks" else SAVE_T - 0.8
    if t > pull:
        q = ease((t - pull) / 0.8)
        cy, zoom = cy + (900 - cy) * q, zoom + (1.0 - zoom) * q
    return cy, zoom


def mascot_layer(st, t, board):
    if board in ("hook", None):
        return
    if "m" not in e._C:
        e._C["m"] = mb.mascot(300)
    t_in = {"old": 7.6, "new": 16.5, "tricks": 28.6, "quiz": 45.0}[board]
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
    d.text((28, 48), "Python f-strings", font=mb.font(mb.BALOO, 54, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "Print ka shortcut", font=mb.font(mb.BALOO, 44, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 7"
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
    for ev in WRITES:
        nch = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, nch / e.CPS) if ev[6] == HAND else max(0.25, nch / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, y0, y1 in CODEBOX.values():
        P(buf, e.marker_squeak(0.5, int(t0 * 4)), t0, 1.0)
    for t0, *_r in NUMS:
        P(buf, e.marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    nplus = OLD1.count("+") + OLD2.count("+")
    for k in range(nplus):
        P(buf, e.buzzer()[: int(0.12 * SR)], PLUS_T + 0.12 * k, 0.45)
    P(buf, e.buzzer(), PLUS_T + 0.6, 0.5)
    P(buf, e.marker_squeak(0.3, 91), F_T, 1.0)
    P(buf, fx.pop(), F_T, 0.5)
    for k in range(2):
        P(buf, fx.whoosh(0.4, 30 + k), FLY_T + 0.3 + 0.4 * k, 0.45)
        P(buf, fx.pop(), FLY_T + 0.9 + 0.4 * k, 0.55)
    P(buf, fx.ding(), 22.6, 0.4)
    P(buf, e.chime(), SPARK_T, 0.7)
    for k, (t0, *_r) in enumerate(TRICKS):
        P(buf, fx.ding(), t0 + 1.2, 0.35)
        P(buf, bs.note_pop([659.25, 783.99, 987.77][k]), t0 + 1.2, 0.35)
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
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP07_fStrings.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL, e.WRITES = BOARDS, END0, TOTAL, WRITES
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = PLUS_T, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(PLUS_T + 0.6, 0.5), (QUIZ_SLAM, 0.8), (REVEAL, 0.4)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
e.board_bg, e.vignette = board_bg, vignette
_engine_frame = p3._frame


def frame(i):
    _T[0] = i / FPS
    return _engine_frame(i)


e.frame = frame

if __name__ == "__main__":
    e.main()
