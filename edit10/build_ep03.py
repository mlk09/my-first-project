#!/usr/bin/env python3
"""Python ki Pathshala EP 03 - Data Types cheat sheet  (1080x1920 Short, no voice-over needed)

Same lightboard style as EP 02 (decoded from the Neso Academy short): glowing hand-writing on black
glass, fixed yellow title box, an accumulating numbered list, mascot reactions, eraser wipes.
Reuses the EP 02 engine (edit9/build_ep02.py) and swaps in new content:
  hook -> "data ki KISM" with two drawn dabbe + type() -> "9 TYPES, 4 FAMILY" -> cheat sheet
  (Numbers / Sequence / Mapping / Set + Bool) -> "Screenshot le lo!" flash -> quiz -> end screen

Usage:  python3 edit10/build_ep03.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit9"))
import build_ep02 as e   # noqa: E402  (engine: rendering, camera, wipes, audio helpers)

mb, bs, es, fx = e.mb, e.bs, e.es, e.fx
paste, pop, ease, clamp, glowify = e.paste, e.pop, e.ease, e.clamp, e.glowify
W, H, SR = e.W, e.H, e.SR
WHITE, YEL, GREEN, RED, CYAN, ORANGE, GREY = e.WHITE, e.YEL, e.GREEN, e.RED, e.CYAN, e.ORANGE, e.GREY
PURPLE = (190, 140, 255)
es.NEXT = "EP 04: INPUT()"

# ------------------------------------------------------------------ timeline
BOARDS = [(0.0, 3.2, "hook"), (3.2, 12.6, "kism"), (12.6, 15.6, "families"), (15.6, 44.0, "sheet"),
          (44.0, 51.5, "quiz")]
END0 = 51.5
TOTAL = END0 + es.DUR

HAND, CODE = "hand", "code"
ROWS = [  # (t_name, y, name, example, hint, family colour)
    (17.0, 480, "int", "20", "Poore number!", CYAN),
    (19.2, 555, "float", "3.14", "Point wala number!", CYAN),
    (21.4, 630, "complex", "2+3j", "j = imaginary part", CYAN),
    (24.9, 810, "str", '"Hello"', "Quotes mein text!", ORANGE),
    (27.1, 885, "list", "[1, 2, 3]", "Badal sakti hai!", ORANGE),
    (29.4, 960, "tuple", "(1, 2, 3)", "Fixed! Badlegi nahi", ORANGE),
    (32.9, 1140, "dict", '{"naam": "Riya"}', "Key : Value jodi!", PURPLE),
    (36.7, 1320, "set", "{1, 2, 3}", "Duplicate allowed nahi!", GREEN),
    (38.9, 1395, "bool", "True / False", "Haan ya Na!", GREEN),
]
FAMILIES = [  # (t, y, number, title, colour)
    (15.9, 400, "1", "NUMBERS", CYAN), (23.8, 730, "2", "SEQUENCE", ORANGE),
    (31.8, 1060, "3", "MAPPING", PURPLE), (35.5, 1240, "4", "SET + BOOL", GREEN),
]
WRITES = [
    (3.45, "kism", 100, 420, [("Data Type kya hai?", WHITE)], 86, HAND),
    (4.75, "kism", 100, 525, [("= data ki ", WHITE), ("KISM", YEL)], 80, HAND),
    (8.2, "kism", 130, 1140, [("type(20)", None)], 66, CODE),
    (9.3, "kism", 130, 1235, [('type("Riya")', None)], 66, CODE),
    (12.85, "families", 120, 640, [("Python ke zaroori types:", WHITE)], 74, HAND),
    (44.9, "quiz", 120, 610, [("3.0", CYAN), (" ka type kya hai?", WHITE)], 82, HAND),
]
for t0, y, name, ex, hint, col in ROWS:
    WRITES.append((t0, "sheet", 205, y, [(name, YEL)], 60, HAND))
    WRITES.append((t0 + 0.35, "sheet", 440, y, [(ex, None)], 50, CODE))
for t0, y, n, title, col in FAMILIES:
    WRITES.append((t0 + 0.2, "sheet", 190, y, [(title, col)], 66, HAND))
NUMS = [(t0, 120, y, n) for t0, y, n, title, col in FAMILIES]
REACT = [(t0 + 0.9, hint, GREEN) for t0, y, name, ex, hint, col in ROWS] + [(50.25, "Point hai = float!", GREEN)]
BOXES = [(5.9, 300, 880, "int", "20", CYAN, 6.75), (6.6, 750, 880, "str", '"Riya"', ORANGE, 7.35)]
OUTPUT_T = 10.5
SLAM = 13.9
FAMILY_CHIPS = [(14.3, "NUMBERS", CYAN), (14.5, "SEQUENCE", ORANGE), (14.7, "MAPPING", PURPLE),
                (14.9, "SET + BOOL", GREEN)]
SNAP = 41.6           # "Screenshot le lo!" + camera flash
QUIZ_SLAM = 44.2
OPTIONS = [(46.0, "A", "int"), (46.3, "B", "float"), (46.6, "C", "str")]
ANSWER = "B"
COUNT0, REVEAL = 47.2, 50.2


# ------------------------------------------------------------------ drawing
def draw_output(st, t):
    a = t - OUTPUT_T
    if a < 0:
        return
    im = Image.new("RGBA", (720, 190))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, 717, 187), 26, fill=(14, 40, 24), outline=GREEN, width=5)
    d.text((36, 52), "Output:", font=mb.font(e.HAND, 44), fill=GREY, anchor="lm")
    f = mb.font(e.MONO, 50)
    d.text((240, 55), "<class 'int'>", font=f, fill=GREEN, anchor="lm")
    if a > 0.45:
        d.text((240, 130), "<class 'str'>", font=f, fill=GREEN, anchor="lm")
    paste(st, glowify(im, GREEN, 12, 1)[0], 440, 1420, pop(a, 0.35))


def chip(txt, col):
    f = mb.font(mb.BALOO, 50, "ExtraBold")
    w = int(f.getlength(txt)) + 70
    im = Image.new("RGBA", (w, 100))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, w - 4, 96), 48, fill=(16, 17, 21), outline=col, width=6)
    d.text((w / 2, 52), txt, font=f, fill=col, anchor="mm")
    return glowify(im, col, 10, 1)[0]


def draw_families(st, t):
    e.slam_text(st, t, SLAM, "9 TYPES, 4 FAMILY!", 860, 112, YEL, (150, 95, 0))
    pos = [(310, 1100), (770, 1100), (310, 1250), (770, 1250)]
    for (t0, txt, col), (x, y) in zip(FAMILY_CHIPS, pos):
        paste(st, chip(txt, col), x, y + 6 * math.sin(t * 3 + x), pop(t - t0, 0.3))


def draw_snap(st, t):
    a = t - SNAP
    if a < 0:
        return
    im = e._outlined("SCREENSHOT LE LO!", 62, YEL, (150, 95, 0))
    paste(st, im, 420, 1505, pop(a, 0.3), 1, -3)


def option_card(letter, txt, state):
    col = {None: (90, 95, 110), True: GREEN, False: RED}[state]
    im = Image.new("RGBA", (760, 130))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 756, 126), 30, fill=(20, 22, 27), outline=col, width=6)
    d.ellipse((24, 22, 110, 108), fill=col)
    d.text((67, 66), letter, font=mb.font(mb.BALOO, 58, "ExtraBold"), fill=(15, 15, 15), anchor="mm")
    d.text((150, 66), txt, font=mb.font(e.MONO, 56), fill=WHITE, anchor="lm")
    if state is not None:
        paste(im, bs.icon_check(70, state), 690, 65)
    return glowify(im, col, 10, 1)[0] if state is not None else im


def draw_quiz(st, t):
    e.slam_text(st, t, QUIZ_SLAM, "QUIZ TIME!", 420, 150, YEL, (140, 90, 0), -4)
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, option_card(letter, txt, state), 540, 820 + k * 170, sc,
              1 if (t < REVEAL or letter == ANSWER) else 0.55)
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (220 * S, 220 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 210 * S, 210 * S), outline=(60, 60, 70), width=14 * S)
        d.arc((10 * S, 10 * S, 210 * S, 210 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)), fill=YEL,
              width=14 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((110 * S, 112 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 110 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        im = im.resize((220, 220), Image.LANCZOS)
        ph = (t - COUNT0) % 1
        paste(st, im, 540, 1385, 1 + 0.08 * math.exp(-ph * 8) * (t < REVEAL))
    if t >= COUNT0 + 0.2:
        paste(st, e._outlined("Comment karo!", 64, WHITE, (40, 40, 40)), 540, 1560, pop(t - COUNT0 - 0.2), 1, 2)


HOOK_CHIPS = [(0.9, "20", CYAN, 190, 1180), (1.05, "3.14", CYAN, 470, 1260), (1.2, '"Hi"', ORANGE, 230, 1390),
              (1.35, "[1, 2]", ORANGE, 520, 1440), (1.5, "True", GREEN, 260, 1560), (1.65, "{ }", PURPLE, 560, 1600)]


def code_chip(txt, col):
    f = mb.font(e.MONO, 54)
    w = int(f.getlength(txt)) + 50
    im = Image.new("RGBA", (w, 96))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, w - 4, 92), 22, fill=(18, 19, 24), outline=col, width=5)
    d.text((w / 2, 48), txt, font=f, fill=col, anchor="mm")
    return glowify(im, col, 10, 1)[0]


def draw_hook(st, t):
    paste(st, e._outlined("PYTHON", 120, WHITE, (40, 40, 50)), 540, 520, pop(t - 0.05), 1, -2)
    paste(st, e._outlined("DATA TYPES", 158, YEL, (150, 95, 0)), 540, 715, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("9 TYPES  •  1 CHEAT SHEET", (20, 20, 20), False)], mb.font(mb.BALOO, 56, "ExtraBold"), 104, 36,
                   fill=(255, 90, 95))
    paste(st, rb, 540, 905, pop(t - 0.55), 1, 2)
    for t0, txt, col, x, y in HOOK_CHIPS:
        paste(st, code_chip(txt, col), x, y + 10 * math.sin(t * 4 + x), pop(t - t0, 0.3), 1, 4 * math.sin(x))
    if "m430" not in e._C:
        e._C["m430"] = mb.mascot(430)
    paste(st, e._C["m430"], 860, 1370, pop(t - 0.9, 0.4))


def render_board(t, board):
    st = Image.new("RGBA", (W, H))
    if board == "hook":
        draw_hook(st, t)
        return st
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            nibpos = e.draw_write(st, t, ev) or nibpos
    if board == "kism":
        for bx in BOXES:
            e.draw_box(st, t, bx)
        draw_output(st, t)
    elif board == "families":
        draw_families(st, t)
    elif board == "sheet":
        for ev in NUMS:
            e.draw_circle_num(st, t, ev)
        draw_snap(st, t)
    elif board == "quiz":
        draw_quiz(st, t)
    e.nib(st, nibpos, t)
    return st


def focus(t, board):
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 980, 1.0 + 0.03 * ease((t - 44) / 7.5)
    if board == "families":
        return 900, 1.03 + 0.03 * ease((t - 12.6) / 3)
    b0, b1 = [(s, en) for s, en, n in BOARDS if n == board][0]
    ys = sorted([(ev[0], ev[3]) for ev in WRITES if ev[1] == board] +
                ([(bx[0], bx[2]) for bx in BOXES] + [(OUTPUT_T, 1420)] if board == "kism" else []))
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(1010, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.07
    pull = (SNAP - 0.8) if board == "sheet" else b1 - 2.2      # show the full cheat sheet for the screenshot
    if t > pull:
        q = ease((t - pull) / 0.8)
        cy, zoom = cy + (930 - cy) * q, zoom + (1.0 - zoom) * q
    return cy, zoom


def mascot_layer(st, t, board):
    if board in ("hook", None):
        return
    if "m" not in e._C:
        e._C["m"] = mb.mascot(300)
    t_in = {"kism": 9.0, "families": 12.7, "sheet": 17.5, "quiz": 46.8}[board]
    s = pop(t - t_in, 0.4)
    if s <= 0:
        return
    react = None
    for tr, txt, col in REACT:
        if 0 <= t - tr < 1.5:
            react = (tr, txt, col)
    bob = 8 * math.sin(t * 3)
    if react:
        a = t - react[0]
        bob -= 30 * abs(math.sin(a * 10)) * math.exp(-a * 5)
    paste(st, e._C["m"], 935, 1580 + bob, s)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 44, "ExtraBold"), 20)
        by = 1470 if board == "sheet" else 1355
        paste(st, b, max(b.width / 2 + 20, 1030 - b.width / 2), by, pop(a, 0.22) * (1 - ease((a - 1.3) / 0.2)))


@e.lru_cache(None)
def title_box():
    im = Image.new("RGBA", (560, 150))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(10, 10, 12, 180))
    d.text((28, 48), "Python Data Types", font=mb.font(mb.BALOO, 52, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "Cheat Sheet", font=mb.font(mb.BALOO, 46, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)[0]


@e.lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 3"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(120, 125, 135, 200), anchor="lm")
    return im.rotate(90, expand=True)


@e.lru_cache(None)
def board_bg():
    """lighter slate glass (instead of EP 02's near-black) - white marker text still reads clearly"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .42) / H) ** 2)
    base = np.clip(1 - r * 0.9, 0, 1)[..., None] * np.array([38, 44, 56], np.float32) + np.array([40, 46, 58])
    refl = np.zeros((H, W), np.float32)
    for off, wid, a in ((-300, 160, 9), (250, 90, 7), (700, 220, 6)):
        refl += a * np.exp(-((xx * 0.6 - yy * 0.8 + off) / wid) ** 2)
    base += refl[..., None]
    rng = np.random.default_rng(2)
    base += rng.normal(0, 1.6, (H, W, 1))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, 3)
        d.ellipse((x, y, x + s, y + s), fill=(255, 255, 255, int(rng.uniform(15, 50))))
    return im


@e.lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.25 * r ** 2.4, 0.7, 1)[..., None]


# ------------------------------------------------------------------ audio
def shutter():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    c1 = fx.filt(fx.noise(n, 77), "bandpass", [1500, 8000]) * np.exp(-tt * 60)
    c2 = np.roll(c1, int(0.08 * SR)) * 0.7
    return (c1 + c2) * 0.8


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, fx.pop(), 0.25, 0.6)
    P(buf, fx.whoosh(0.3, 1), 0.45, 0.5)
    for t0, *_ in HOOK_CHIPS:
        P(buf, fx.pop(), t0, 0.4)
        P(buf, bs.note_pop(700 + 120 * HOOK_CHIPS.index((t0, *_))), t0, 0.25)
    for s, en, n in BOARDS[1:]:
        P(buf, e.eraser_swish(), s, 0.55)
        P(buf, e.cap_click(), s + 0.2, 0.5)
    for ev in WRITES:
        n = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, n / e.CPS) if ev[6] == HAND else max(0.25, n / (e.CPS * 1.3))
        P(buf, e.marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, *_ in NUMS:
        P(buf, e.marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    for k, (t0, *_rest) in enumerate(ROWS):
        P(buf, bs.note_pop([523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5, 1174.66][k]),
          t0 + 0.9, 0.35)
        P(buf, fx.pop(), t0 + 0.9, 0.3)
    for t0, cx, cy, label, val, col, tdrop in BOXES:
        P(buf, e.marker_squeak(0.6, int(t0 * 3)), t0, 1.0)
        P(buf, fx.whoosh(0.35, int(tdrop)), tdrop - 0.4, 0.35)
        P(buf, e.thud(), tdrop, 0.8)
    P(buf, fx.pop(), OUTPUT_T, 0.6)
    P(buf, fx.ding(), OUTPUT_T + 0.05, 0.45)
    P(buf, fx.pop(), OUTPUT_T + 0.45, 0.5)
    P(buf, fx.riser(1.0), SLAM - 1.0, 0.45)
    P(buf, fx.boom(), SLAM, 1.0)
    for t0, *_ in FAMILY_CHIPS:
        P(buf, fx.pop(), t0, 0.55)
    P(buf, fx.whoosh(0.3, 9), SNAP - 0.25, 0.4)
    P(buf, shutter(), SNAP + 0.1, 1.0)
    P(buf, fx.ding(), SNAP + 0.3, 0.35)
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
    P(buf, es.sfx(), END0, 0.9)
    return buf


# ------------------------------------------------------------------ wire into the EP 02 engine
e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP03_DataTypes.mp4")
e.WORK = os.path.join(HERE, "work")
e.BOARDS, e.END0, e.TOTAL = BOARDS, END0, TOTAL
e.WRITES, e.BOXES, e.OUTPUT_T = WRITES, BOXES, OUTPUT_T
e.SLAM_RULES, e.QUIZ_SLAM, e.COUNT0, e.REVEAL, e.TITLEBOX_T = SLAM, QUIZ_SLAM, COUNT0, REVEAL, 3.3
e.SHAKES = [(SLAM, 1.0), (QUIZ_SLAM, 0.8), (REVEAL, 0.4), (SNAP + 0.1, 0.25)]
e.render_board, e.focus, e.mascot_layer = render_board, focus, mascot_layer
e.title_box, e.side_text, e.sfx_track = title_box, side_text, sfx_track
e.board_bg, e.vignette = board_bg, vignette

_frame = e.frame


def frame(i):
    """engine frame + white camera flash for the screenshot moment"""
    a = _frame(i)
    t = i / e.FPS
    d = t - (SNAP + 0.1)
    if 0 <= d < 0.35:
        a = np.clip(a.astype(np.float32) + (255 - a.astype(np.float32)) * 0.85 * (1 - d / 0.35), 0, 255).astype(np.uint8)
    return a


e.frame = frame
del ImageFilter

if __name__ == "__main__":
    e.main()
