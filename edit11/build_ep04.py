#!/usr/bin/env python3
"""Python ki Pathshala EP 04 - input()  (1080x1920 Short, works without a voice-over)

Style decoded from "How to Take User Input in Python (Explained in 30 Seconds)" (ZeroBug):
dark grid title cards with typewriter text (white words, orange code), hard cuts to a code editor
where code is typed live and run in the terminal, short centred caption chunks, a simple
"input -> String" arrow diagram, keyboard sounds.
Pushed further: camera that follows the typing line and the terminal, punch-in cuts, waiting badge,
ENTER keycap, a TypeError moment (shake, buzzer, music break) and its int() fix, recap card,
mascot reactions, music + SFX, and the Python ki Pathshala end screen.

Usage:  python3 edit11/build_ep04.py [--preview]
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
for p in ("brand", "edit", "edit7"):
    sys.path.insert(0, os.path.join(ROOT, p))
_argv, sys.argv = sys.argv, sys.argv[:1]
import build_edit as fx        # noqa: E402
import build_short as bs       # noqa: E402
import make_brand as mb        # noqa: E402
import make_endscreen as es    # noqa: E402
sys.argv = _argv
es.NEXT = "EP 05: TYPE CASTING"
bs.KW_COL.update({"input": (220, 220, 170), "int": (78, 201, 176), "float": (78, 201, 176)})

OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP04_Input.mp4")
WORK = os.path.join(HERE, "work")
W, H, FPS, SR = 1080, 1920, 30, 48000
CAP, MONO, MONO_R = bs.CAP, bs.MONO, bs.MONO_R
WHITE, YEL, GREEN, RED, ORANGE, GREY = (245, 245, 245), (255, 214, 10), (80, 220, 120), (255, 75, 85), \
    (255, 159, 67), (140, 146, 158)

# ------------------------------------------------------------------ timeline
SCENES = [(0.0, "hook"), (3.6, "prompt"), (9.0, "demo"), (21.0, "string"), (26.0, "error"), (35.5, "fix"),
          (44.5, "recap")]
END0 = 49.0
TOTAL = END0 + es.DUR

# captions: (t0, text) - shown until the next one; *word* = highlight colour
CAPTIONS = [
    (0.3, "PROGRAM AAPSE"), (1.5, "*BAAT* KAR SAKTA HAI?"),
    (3.8, "*input()* FUNCTION"), (5.1, "USER SE *SAWAAL* POOCHTA HAI"), (6.6, "AUR *JAWAB* KA"),
    (7.6, "*INTEZAAR* KARTA HAI"),
    (9.3, "PEHLE CODE LIKHO"), (12.3, "*RUN* KARO"), (13.0, "PROGRAM *RUK* GAYA…"), (14.0, "AAPKE *JAWAB* KE LIYE!"),
    (15.0, "NAAM LIKHO"), (16.2, "*ENTER* DABAO"), (16.6, "+NAMASTE AMAN!+"), (18.2, "PROGRAM NE *BAAT* KAR LI!"),
    (21.2, "PAR EK *TWIST* HAI…"), (22.4, "*input()* HAMESHA"), (23.3, "*STRING* DETA HAI!"),
    (24.4, "20 BHI BAN JAATA HAI *\"20\"*"),
    (26.3, "AB *AGE* LETE HAIN"), (27.4, "AUR *+1* KARTE HAIN"), (28.5, "RUN…"), (30.6, "-ERROR!-"),
    (31.8, "*STRING* + *NUMBER*"), (33.0, "-NAHI CHALEGA!-"), (34.3, "TOH FIX KYA HAI?"),
    (35.8, "*int()* LAGAO!"), (37.2, "PHIR *RUN* KARO"), (39.3, "+PERFECT: 21!+"), (40.5, "AB YE *NUMBER* HAI!"),
    (41.8, "DECIMAL KE LIYE"), (42.8, "*float()* USE KARO"),
    (44.7, "*YAAD* RAKHO!"), (46.8, "*SCREENSHOT* LE LO!"),
]

# editor scenes. code lines: list of segments (text, t_reveal) - t_reveal None = already there
CODE_CPS, USER_CPS = 22.0, 5.0
EDITOR = {
    "demo": {
        "code": [[('name = input("Naam kya hai? ")', 9.2)], [('print("Namaste", name)', 10.9)]],
        "run": 12.3,
        "term": [("$ python main.py", GREY, 12.5, None), ("Naam kya hai? ", WHITE, 12.8, ("Aman", 15.0)),
                 ("Namaste Aman", GREEN, 16.5, None)],
        "wait": (13.0, 15.0), "enter": 16.2, "ok": 16.5,
    },
    "error": {
        "code": [[('age = input("Age? ")', 26.2)], [("print(age + 1)", 27.3)]],
        "run": 28.4,
        "term": [("$ python main.py", GREY, 28.6, None), ("Age? ", WHITE, 28.9, ("20", 29.6)),
                 ("TypeError: can only concatenate", RED, 30.6, None), ('str (not "int") to str', RED, 30.6, None)],
        "wait": (29.1, 29.6), "enter": 30.2, "err": 30.6,
    },
    "fix": {
        "code": [[("age = ", None), ("int(", 35.8), ('input("Age? ")', None), (")", 36.4)],
                 [("print(age + 1)", None)]],
        "run": 37.2,
        "term": [("$ python main.py", GREY, 37.4, None), ("Age? ", WHITE, 37.7, ("20", 38.3)), ("21", GREEN, 39.3, None)],
        "wait": (37.9, 38.3), "enter": 38.9, "ok": 39.3, "chip": 42.8, "hl": (35.8, 37.0),
    },
}
ERR_T = 30.6
REACT = [(16.6, "Namaste!", GREEN), (30.7, "Oops!", RED), (39.4, "Perfect!", GREEN)]


# ------------------------------------------------------------------ helpers
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back(t, s=1.8):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def pop(age, d=0.3):
    return 0.0 if age <= 0 else back(age / d)


def paste(base, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, base.width - x), min(im.height, base.height - y)
    if ex > sx and ey > sy:
        base.alpha_composite(im.crop((sx, sy, ex, ey)), (x + sx, y + sy))


def glow(im, col, r=10, n=1):
    pad = r * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad))
    a = Image.new("L", out.size)
    a.paste(im.getchannel("A"), (pad, pad))
    g = Image.new("RGBA", out.size, col + (0,))
    g.putalpha(a.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * 0.8)))
    for _ in range(n):
        out.alpha_composite(g)
    out.alpha_composite(im, (pad, pad))
    return out


def scene_at(t):
    cur = SCENES[0]
    for s in SCENES:
        if t >= s[0]:
            cur = s
    return cur


def nchars(t, t0, cps):
    return 0 if t < t0 else int((t - t0) * cps) + 1


# ------------------------------------------------------------------ background
@lru_cache(None)
def grid_tile():
    im = Image.new("RGB", (W, H + 90), (24, 25, 30))
    d = ImageDraw.Draw(im)
    for x in range(0, W + 1, 90):
        d.line((x, 0, x, H + 90), fill=(42, 44, 52), width=2)
    for y in range(0, H + 91, 90):
        d.line((0, y, W, y), fill=(42, 44, 52), width=2)
    yy, xx = np.mgrid[0:H + 90, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    a = np.asarray(im).astype(np.float32) * (1.15 - 0.55 * np.clip(r, 0, 1))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def background(t):
    off = int(t * 12) % 90
    return grid_tile().crop((0, off, W, off + H))


# ------------------------------------------------------------------ typewriter (grid scenes)
def type_text(st, t, t0, txt, path, size, col, cx, cy, cps=16, anchor="mm", cursor=True):
    n = min(len(txt), nchars(t, t0, cps))
    if n <= 0:
        return
    f = mb.font(path, size) if not isinstance(path, tuple) else mb.font(*path)
    shown = txt[:n]
    d = ImageDraw.Draw(st)
    full_w = f.getlength(txt)
    x0 = cx - full_w / 2 if anchor == "mm" else cx
    d.text((x0, cy), shown, font=f, fill=col, anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
    done = n >= len(txt)
    if cursor and (not done or (t - t0 - len(txt) / cps) % 0.8 < 0.45) and t - t0 - len(txt) / cps < 1.0:
        x = x0 + f.getlength(shown) + 6
        d.rectangle((x, cy - size * 0.45, x + max(4, size // 14), cy + size * 0.45), fill=col)


def arrow(st, t, t0, x0, x1, y, col, dur=0.35):
    p = ease((t - t0) / dur)
    if p <= 0:
        return
    d = ImageDraw.Draw(st)
    xe = x0 + (x1 - x0) * p
    d.line((x0, y, xe, y), fill=col, width=12)
    if p > 0.6:
        d.polygon([(xe + 10, y), (xe - 30, y - 26), (xe - 30, y + 26)], fill=col)


def pill(txt, col, size=46, fg=(15, 15, 15)):
    f = mb.font(CAP, size)
    w = int(f.getlength(txt)) + 70
    im = Image.new("RGBA", (w, int(size * 1.9)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, im.height - 3), im.height // 2, fill=col)
    d.text((w / 2, im.height / 2 + 2), txt, font=f, fill=fg, anchor="mm")
    return im


# ------------------------------------------------------------------ editor
EX0, EY0, EX1, EY1 = 40, 330, 1040, 1330
CODE_Y0, LH, CODE_FS = 480, 74, 44
TERM_Y0, TLH, TERM_FS = 905, 64, 40


@lru_cache(None)
def editor_chrome():
    im = Image.new("RGBA", (W, H))
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle((EX0 + 10, EY0 + 24, EX1 + 10, EY1 + 24), 26, fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((EX0, EY0, EX1, EY1), 26, fill=(30, 31, 34), outline=(62, 65, 74), width=3)
    d.rounded_rectangle((EX0 + 3, EY0 + 3, EX1 - 3, EY0 + 76), 24, fill=(23, 24, 27))
    d.rectangle((EX0 + 3, EY0 + 50, EX1 - 3, EY0 + 76), fill=(23, 24, 27))
    for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((EX0 + 30 + k * 38, EY0 + 28, EX0 + 52 + k * 38, EY0 + 50), fill=c)
    d.rounded_rectangle((EX0 + 170, EY0 + 14, EX0 + 390, EY0 + 76), 10, fill=(30, 31, 34))
    d.text((EX0 + 280, EY0 + 46), "main.py", font=mb.font(MONO_R, 30), fill=WHITE, anchor="mm")
    d.line((EX0 + 3, TERM_Y0 - 80, EX1 - 3, TERM_Y0 - 80), fill=(62, 65, 74), width=3)
    d.text((EX0 + 40, TERM_Y0 - 44), "TERMINAL", font=mb.font(MONO, 26), fill=GREY, anchor="lm")
    return im


def code_text(d, x, y, segs, t):
    """draw a code line built from segments that reveal over time; returns cursor x or None"""
    full = "".join(s for s, _ in segs)
    cols = []
    for tok, col in bs.tokens(full):
        cols += [col] * len(tok)
    f = mb.font(MONO, CODE_FS)
    i, cx, cur = 0, x, None
    for s, t0 in segs:
        n = len(s) if t0 is None else min(len(s), nchars(t, t0, CODE_CPS))
        for k in range(n):
            d.text((cx, y), s[k], font=f, fill=cols[i + k], anchor="ls")
            cx += f.getlength(s[k])
        if t0 is not None and 0 < n < len(s) + 1 and t < t0 + len(s) / CODE_CPS + 0.05:
            cur = cx
        if n < len(s):
            break
        i += len(s)
    return cur, cx


def draw_editor(st, t, name):
    cfg = EDITOR[name]
    st.alpha_composite(editor_chrome())
    d = ImageDraw.Draw(st)
    # run button
    run = cfg["run"]
    pressed = run <= t < run + 0.12
    bx, by = EX1 - 110, EY0 + 45
    d.rounded_rectangle((bx - 72, by - 26, bx + 72, by + 26), 12, fill=(30, 140, 70) if pressed else (39, 174, 96))
    d.polygon([(bx - 44, by - 13), (bx - 44, by + 13), (bx - 22, by)], fill=WHITE)
    d.text((bx + 16, by + 1), "Run", font=mb.font(CAP, 30), fill=WHITE, anchor="mm")
    # int( ) highlight in the fix scene
    if "hl" in cfg and cfg["hl"][0] <= t < cfg["hl"][1] + 2.5:
        a = int(110 * min(1, (t - cfg["hl"][0]) / 0.2))
        f = mb.font(MONO, CODE_FS)
        x0 = EX0 + 110 + f.getlength("age = ")
        d.rounded_rectangle((x0 - 6, CODE_Y0 - 46, x0 + f.getlength("int(") + 4, CODE_Y0 + 14), 10, fill=(255, 214, 10, a))
        x1 = EX0 + 110 + f.getlength('age = int(input("Age? ")')
        d.rounded_rectangle((x1 - 4, CODE_Y0 - 46, x1 + f.getlength(")") + 6, CODE_Y0 + 14), 10, fill=(255, 214, 10, a))
    cursor, cur_line = None, 0
    for k, segs in enumerate(cfg["code"]):
        y = CODE_Y0 + k * LH
        d.text((EX0 + 70, y), str(k + 1), font=mb.font(MONO_R, 34), fill=(110, 118, 129), anchor="rs")
        if any(t0 is None or t >= t0 for _, t0 in segs):
            c, endx = code_text(d, EX0 + 110, y, segs, t)
            if c is not None:
                cursor, cur_line = c, k
    if cursor is not None and (t * 2.5) % 1 < 0.6:
        y = CODE_Y0 + cur_line * LH
        d.rectangle((cursor + 2, y - 40, cursor + 6, y + 8), fill=WHITE)
    # terminal
    f = mb.font(MONO, TERM_FS)
    tcur = None
    row = 0
    for txt, col, t0, user in cfg["term"]:
        if t < t0:
            break
        y = TERM_Y0 + row * TLH
        d.text((EX0 + 40, y), txt, font=f, fill=col, anchor="lm")
        x = EX0 + 40 + f.getlength(txt)
        if user:
            utxt, ut0 = user
            n = min(len(utxt), nchars(t, ut0, USER_CPS))
            d.text((x, y), utxt[:n], font=f, fill=YEL, anchor="lm")
            x += f.getlength(utxt[:n])
            if t < cfg["enter"]:
                tcur = (x, y)
        row += 1
    if tcur and (t * 2) % 1 < 0.6:
        d.rectangle((tcur[0] + 3, tcur[1] - 24, tcur[0] + 26, tcur[1] + 22), fill=(230, 230, 230))
    # waiting badge
    w0, w1 = cfg["wait"]
    if w0 <= t < w1:
        dots = "." * (1 + int((t - w0) * 3) % 3)
        p = pill("waiting" + dots, (255, 214, 10), 34)
        paste(st, p, EX1 - 170, TERM_Y0 + TLH, pop(t - w0, 0.25))
    # ENTER keycap
    te = cfg["enter"]
    if te - 0.15 <= t < te + 0.9:
        k = Image.new("RGBA", (300, 140))
        kd = ImageDraw.Draw(k)
        press = 6 if te <= t < te + 0.12 else 0
        kd.rounded_rectangle((6, 14, 294, 134), 22, fill=(150, 152, 160))
        kd.rounded_rectangle((6, 6 + press, 294, 120 + press), 22, fill=(238, 238, 242))
        kd.text((150, 64 + press), "ENTER", font=mb.font(CAP, 50), fill=(30, 30, 35), anchor="mm")
        a = 1 - ease((t - te - 0.6) / 0.3)
        paste(st, k, 780, EY1 - 130, pop(t - te + 0.15, 0.2), a)
    # success check
    if "ok" in cfg and t >= cfg["ok"]:
        row_ok = len(cfg["term"]) - 1
        paste(st, bs.icon_check(70, True), EX0 + 40 + f.getlength(cfg["term"][-1][0]) + 60,
              TERM_Y0 + row_ok * TLH, pop(t - cfg["ok"], 0.25))
    # float() chip
    if "chip" in cfg and t >= cfg["chip"]:
        c = pill('3.5 ke liye: float(input())', (78, 201, 176), 40)
        paste(st, c, 540, EY1 - 120, pop(t - cfg["chip"], 0.3))
    return cursor, cur_line


def editor_focus(t, name):
    """camera (cy, zoom): follow the typing line, then the terminal"""
    cfg = EDITOR[name]
    run = cfg["run"]
    if t < run - 0.2:
        return CODE_Y0 + 20, 1.12
    q = ease((t - run + 0.2) / 0.5)
    cy, z = CODE_Y0 + 20 + (TERM_Y0 + 60 - CODE_Y0 - 20) * q, 1.12 - 0.08 * q
    if "err" in cfg and t >= cfg["err"]:
        a = t - cfg["err"]
        z += 0.06 * ease(a / 0.25)
        cy += (TERM_Y0 + 2.5 * TLH - cy) * ease(a / 0.25)
    if name == "fix" and t > 41.6:
        q2 = ease((t - 41.6) / 0.6)
        cy, z = cy + (900 - cy) * q2, z + (1.0 - z) * q2
    return cy, z


# ------------------------------------------------------------------ grid scenes
def draw_hook(st, t):
    type_text(st, t, 0.15, "PYTHON MEIN", CAP, 96, WHITE, 540, 560, cps=18)
    type_text(st, t, 0.9, "input()", MONO, 190, ORANGE, 540, 770, cps=10)
    rb = mb.ribbon([("USER SE BAAT KARO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 975, pop(t - 1.6), 1, -2)
    if "m" not in _C:
        _C["m"] = mb.mascot(380)
    paste(st, _C["m"], 800, 1210, pop(t - 1.9, 0.4))
    if t > 2.2:
        b = mb.bubble("Naam kya hai?", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 470, 1120, pop(t - 2.2, 0.3))


def draw_prompt(st, t):
    type_text(st, t, 3.8, 'input("Prompt")', MONO, 104, ORANGE, 540, 680, cps=14)
    f = mb.font(MONO, 104)
    x_p = 540 - f.getlength('input("Prompt")') / 2 + f.getlength('input("') + f.getlength("Prompt") / 2
    if t > 5.1:
        p = ease((t - 5.1) / 0.3)
        d = ImageDraw.Draw(st)
        d.line((x_p, 760, x_p, 760 + 120 * p), fill=YEL, width=8)
        if p > 0.8:
            d.polygon([(x_p, 900), (x_p - 22, 865), (x_p + 22, 865)], fill=YEL)
        paste(st, pill("SAWAAL jo screen pe dikhega", YEL, 42), 540, 960, pop(t - 5.3, 0.3))
    if t > 6.6:
        paste(st, pill("User ka JAWAB = variable mein", GREEN, 42), 540, 1110, pop(t - 6.6, 0.3))


def draw_string(st, t):
    type_text(st, t, 21.2, "input()", MONO, 120, ORANGE, 300, 760, cps=12)
    arrow(st, t, 21.95, 520, 640, 760, RED)
    type_text(st, t, 22.35, "STRING", CAP, 110, RED, 860, 760, cps=12)
    if t > 24.3:
        c = Image.new("RGBA", (560, 200))
        d = ImageDraw.Draw(c)
        d.rounded_rectangle((3, 3, 556, 196), 28, fill=(20, 21, 26), outline=YEL, width=6)
        d.text((115, 102), "20", font=mb.font(MONO, 96), fill=WHITE, anchor="mm")
        d.text((225, 102), "=", font=mb.font(MONO, 80), fill=GREY, anchor="mm")
        d.text((395, 102), '"20"', font=mb.font(MONO, 96), fill=(206, 145, 120), anchor="mm")
        paste(st, glow(c, YEL, 12), 540, 1010, pop(t - 24.3, 0.35), 1, -2)


RECAP = [(44.75, "input()", "TEXT", WHITE), (45.6, "int(input())", "NUMBER", GREEN),
         (46.45, "float(input())", "DECIMAL", (78, 201, 176))]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 600 + k * 170
        type_text(st, t, t0, code, MONO, 62, ORANGE, 90, y, cps=26, anchor="lm", cursor=False)
        arrow(st, t, t0 + 0.5, 640, 745, y, RED, 0.25)
        if t > t0 + 0.7:
            ImageDraw.Draw(st).text((775, y), lab, font=mb.font(CAP, 56), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 46.8:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1180, pop(t - 46.8, 0.3), 1, -3)


# ------------------------------------------------------------------ captions + mascot
@lru_cache(None)
def caption_img(text):
    tags = {"*": YEL, "+": GREEN, "-": RED}
    parts = []
    for tok in text.split(" "):
        c = WHITE
        if tok and tok[0] in tags and tok[-1] in tags or (tok and tok[0] in tags):
            c = tags[tok[0]]
            tok = tok.strip("*+-")
        elif tok and tok[-1] in tags:
            tok = tok.rstrip("*+-")
        parts.append((tok, c))
    # whole-line tags like +NAMASTE AMAN!+
    if text[0] in "+-" and text[-1] == text[0]:
        parts = [(p.strip("+-"), tags[text[0]]) for p, _ in parts]
    size = 76
    f = mb.font(CAP, size)
    sp = f.getlength(" ")
    tw = sum(f.getlength(p) for p, _ in parts) + sp * (len(parts) - 1)
    if tw > 980:
        size = int(size * 980 / tw)
        f = mb.font(CAP, size)
        sp = f.getlength(" ")
        tw = sum(f.getlength(p) for p, _ in parts) + sp * (len(parts) - 1)
    im = Image.new("RGBA", (W, 200))
    d = ImageDraw.Draw(im)
    x = (W - tw) / 2
    for p, c in parts:
        d.text((x, 100), p, font=f, fill=c, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0))
        x += f.getlength(p) + sp
    sh = Image.new("RGBA", im.size)
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .6)))
    out = Image.new("RGBA", im.size)
    out.alpha_composite(sh, (0, 8))
    out.alpha_composite(im)
    return out


def draw_caption(fr, t):
    if t >= END0:
        return
    cur = None
    for k, (t0, txt) in enumerate(CAPTIONS):
        if t >= t0:
            cur = (t0, txt)
    if cur:
        a = t - cur[0]
        s = 0.8 + 0.2 * back(a / 0.2) if a < 0.2 else 1.0
        paste(fr, caption_img(cur[1]), W / 2, 1480 + 18 * (1 - ease(a / 0.15)), s, min(1, a / 0.08))


_C = {}


def draw_mascot(fr, t):
    for tr, txt, col in REACT:
        a = t - tr
        if 0 <= a < 1.6:
            if "ms" not in _C:
                _C["ms"] = mb.mascot(250)
            out = 1 - ease((a - 1.35) / 0.25)
            rot = 10 * math.sin(a * 25) * math.exp(-a * 4) if col == RED else 0
            bob = -30 * abs(math.sin(a * 10)) * math.exp(-a * 4) if col == GREEN else 0
            paste(fr, _C["ms"], 950, 1210 + bob, pop(a, 0.3) * out, 1, rot)
            b = mb.bubble(txt, mb.font(mb.BALOO, 44, "ExtraBold"), 20)
            paste(fr, b, 860, 1040, pop(a - 0.1, 0.25) * out)


# ------------------------------------------------------------------ frame
_rng = np.random.default_rng(9)
GRAIN = [np.random.default_rng(s).normal(0, 3, (H // 2, W // 2)).astype(np.float32) for s in range(5)]


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.3 * r ** 2.4, 0.6, 1)[..., None]


def frame(i):
    t = i / FPS
    if t >= END0:
        return np.asarray(es.frame(t - END0).convert("RGB"))
    s0, name = scene_at(t)
    st = Image.new("RGBA", (W, H))
    cy, z = 960, 1.0
    if name in EDITOR:
        draw_editor(st, t, name)
        cy, z = editor_focus(t, name)
    else:
        {"hook": draw_hook, "prompt": draw_prompt, "string": draw_string, "recap": draw_recap}[name](st, t)
        z = 1.0 + 0.04 * ease((t - s0) / 4)
    # punch-in cut: every scene lands slightly zoomed and settles
    a = t - s0
    if s0 > 0 and a < 0.22:
        z *= 1 + 0.12 * (1 - ease(a / 0.22))
    dx = dy = 0.0
    if 0 <= t - ERR_T < 0.45:
        e = t - ERR_T
        amp = 24 * (1 - e / 0.45)
        dx, dy = amp * math.sin(e * 90), amp * math.cos(e * 70)
    cx = 520 if name in EDITOR else W / 2           # code is left-aligned: keep the gutter in frame
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[1, 2] += (860 - cy) + dy
    M[0, 2] += dx + (W / 2 - cx)
    stage = cv2.warpAffine(np.asarray(st), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fr = background(t).copy()
    fr.alpha_composite(Image.fromarray(stage))
    if name == "error" and t >= ERR_T:
        paste(fr, mb.outlined("ERROR!", mb.font(mb.BALOO, 150, "ExtraBold"), RED, 10, (10, 10, 10), 8, (120, 0, 0)),
              540, 380, pop(t - ERR_T, 0.25) * (1 if t - ERR_T < 4 else 0), 1, -6)
    draw_mascot(fr, t)
    draw_caption(fr, t)
    pill_t = pill("PYTHON KI PATHSHALA • EP 04", (0, 0, 0, 150), 28, YEL)
    fr.alpha_composite(pill_t, (W // 2 - pill_t.width // 2, 140))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    flash = 0.0
    if s0 > 0 and a < 0.15:
        flash = 0.25 * (1 - a / 0.15)
    if 0 <= t - ERR_T < 0.3:
        e = t - ERR_T
        arr = arr * (1 - 0.35 * (1 - e / 0.3)) + np.array([255, 30, 40]) * 0.35 * (1 - e / 0.3)
    if flash:
        arr += (255 - arr) * flash
    arr *= vignette()
    arr += cv2.resize(GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def buzzer():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 140 * tt)) + 0.5 * np.sign(np.sin(2 * np.pi * 105 * tt))
    return fx.filt(x, "lowpass", 1500, 2) * np.minimum(1, (0.45 - tt) / 0.08) * 0.3


def glitch():
    n = int(0.3 * SR)
    x = np.repeat(fx.noise(n, 4)[::50], 50)[:n]
    gate = (np.random.default_rng(3).random(n // 700 + 1) > 0.4).repeat(700)[:n]
    return x * gate * 0.3


def enter_key():
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    click = fx.filt(fx.noise(n, 12), "bandpass", [800, 5000]) * np.exp(-tt * 70)
    body = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 40)
    return click * 0.8 + body * 0.6


def type_clicks(buf, t0, n, cps, seed, gain):
    for k in range(n):
        fx.place(buf, bs.key_click(seed + k), t0 + k / cps, gain)


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    for s0, name in SCENES[1:]:
        P(buf, fx.whoosh(0.3, int(s0 * 10)), s0 - 0.2, 0.5)
    P(buf, fx.boom()[: int(0.6 * SR)], 0.05, 0.5)
    type_clicks(buf, 0.15, len("PYTHON MEIN"), 18, 1, 0.4)
    type_clicks(buf, 0.9, len("input()"), 10, 20, 0.5)
    P(buf, fx.pop(), 1.6, 0.6)
    P(buf, fx.pop(), 1.9, 0.5)
    P(buf, fx.pop(), 2.2, 0.5)
    type_clicks(buf, 3.8, len('input("Prompt")'), 14, 40, 0.45)
    P(buf, fx.pop(), 5.3, 0.55)
    P(buf, fx.pop(), 6.6, 0.55)
    for name, cfg in EDITOR.items():
        for line in cfg["code"]:
            for s, t0 in line:
                if t0 is not None:
                    type_clicks(buf, t0, len(s), CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for txt, col, t0, user in cfg["term"]:
            P(buf, bs.note_pop(1300 if col != RED else 400), t0, 0.15)
            if user:
                type_clicks(buf, user[1], len(user[0]), USER_CPS, int(user[1] * 3), 0.6)
        P(buf, enter_key(), cfg["enter"], 0.9)
        if "ok" in cfg:
            P(buf, fx.ding(), cfg["ok"], 0.5)
            P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
        if "chip" in cfg:
            P(buf, fx.pop(), cfg["chip"], 0.5)
    P(buf, fx.boom(), ERR_T, 0.9)
    P(buf, buzzer(), ERR_T, 0.8)
    P(buf, glitch(), ERR_T + 0.05, 0.7)
    P(buf, fx.riser(0.7), 35.8 - 0.7, 0.3)
    type_clicks(buf, 21.2, len("input()"), 12, 70, 0.45)
    P(buf, fx.whoosh(0.3, 71), 21.9, 0.4)
    type_clicks(buf, 22.35, len("STRING"), 12, 80, 0.45)
    P(buf, fx.pop(), 24.3, 0.6)
    P(buf, bs.thud(), 24.3, 0.5)
    for t0, code, _lab, _col in RECAP:
        type_clicks(buf, t0, len(code), 26, int(t0 * 5), 0.3)
        P(buf, fx.whoosh(0.2, int(t0 * 9)), t0 + 0.45, 0.3)
        P(buf, fx.pop(), t0 + 0.7, 0.45)
    P(buf, fx.pop(), 46.8, 0.6)
    P(buf, bs.thud(), 46.8, 0.4)
    for tr, txt, col in REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=ERR_T)        # one-beat break right before the error hits
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


def main():
    preview = "--preview" in sys.argv
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    mix = build_audio()
    out = OUT if not preview else os.path.join(HERE, "output", "preview.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", mix, "-c:v", "libx264",
                            "-preset", "veryfast" if preview else "slow", "-crf", "28" if preview else "20",
                            "-maxrate", "7M", "-bufsize", "14M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    step = 3 if preview else 1
    for i in range(0, n, step):
        fb = frame(i).tobytes()
        for _ in range(step):
            enc.stdin.write(fb)
        if i % 150 == 0:
            print(f"  {i / FPS:.1f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
