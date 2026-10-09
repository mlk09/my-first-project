#!/usr/bin/env python3
"""Python ki Pathshala EP 02 - Variables + 3 Golden Rules  (1080x1920 Short, no voice-over)

Style decoded from "3 Rules for Naming Variables in Python" (Neso Academy, Quick Concepts):
glass lightboard on pure black, glowing marker hand-writing that builds a numbered list,
a fixed yellow title box, red / green dots for wrong / right examples, a clean outro card.
Pushed further: write-on animation with a glowing nib, camera that follows the pen, eraser
wipes, a drawn "dabba" (box) analogy, a quiz with countdown, mascot reactions, music + SFX,
and the animated Python ki Pathshala end screen.

Usage:  python3 edit9/build_ep02.py [--preview]
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
_argv, sys.argv = sys.argv, sys.argv[:1]      # make_endscreen reads argv at import
import build_edit as fx        # noqa: E402
import build_short as bs       # noqa: E402  (code colours, check icons, music)
import make_brand as mb        # noqa: E402  (fonts, mascot, title text)
import make_endscreen as es    # noqa: E402  (animated end screen)
sys.argv = _argv
es.NEXT = "EP 03: DATA TYPES"

OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP02_Variables.mp4")
WORK = os.path.join(HERE, "work")
W, H, FPS, SR = 1080, 1920, 30, 48000

HAND = mb.CHALK                                   # Kalam Bold - marker hand-writing
MONO = bs.MONO
WHITE, YEL, GREEN, RED, CYAN, ORANGE = (245, 245, 240), (255, 214, 77), (91, 227, 125), (255, 90, 95), \
    (110, 200, 255), (255, 160, 80)
GREY = (150, 155, 165)

# ------------------------------------------------------------------ timeline
BOARDS = [  # (start, end, name)
    (0.0, 3.2, "hook"),
    (3.2, 15.8, "dabba"),
    (15.8, 19.0, "rules_title"),
    (19.0, 43.0, "rules"),
    (43.0, 51.0, "quiz"),
]
END0 = 51.0
TOTAL = END0 + es.DUR
WIPE = 0.5          # eraser wipe length at each board change
CPS = 17.0          # hand-writing speed (chars / second)

# write events: (t, board, x, y, segments, size, font)   segments = [(text, colour), ...]
#  font "hand" | "code"  ;  x = left edge, y = text centre
WRITES = [
    # --- dabba board
    (3.45, "dabba", 100, 420, [("Variable kya hai?", WHITE)], 86, "hand"),
    (4.75, "dabba", 100, 525, [("= ek naam wala ", WHITE), ("DABBA", YEL)], 80, "hand"),
    (7.9, "dabba", 130, 1140, [('name = "Rahul"', None)], 66, "code"),
    (8.95, "dabba", 130, 1235, [("age = 20", None)], 66, "code"),
    (10.4, "dabba", 130, 1330, [("print(name, age)", None)], 66, "code"),
    # --- rules title
    (16.1, "rules_title", 120, 720, [("Par naam rakhne ke", WHITE)], 82, "hand"),
    # --- rules board (Neso-style accumulating list)
    (19.3, "rules", 195, 430, [("Shuru ", WHITE), ("LETTER", YEL), (" ya ", WHITE), ("_", YEL), (" se", WHITE)], 72, "hand"),
    (21.2, "rules", 195, 525, [("Ex.", GREEN)], 60, "hand"),
    (21.4, "rules", 305, 525, [("1st_name", None)], 58, "code"),
    (22.7, "rules", 305, 610, [("first_name", None)], 58, "code"),
    (26.4, "rules", 195, 760, [("Sirf ", WHITE), ("letters", YEL), (", ", WHITE), ("numbers", YEL), (", ", WHITE),
                               ("_", YEL)], 70, "hand"),
    (28.6, "rules", 195, 855, [("Ex.", GREEN)], 60, "hand"),
    (28.8, "rules", 305, 855, [("my-age", None)], 58, "code"),
    (30.1, "rules", 305, 940, [("my_age", None)], 58, "code"),
    (33.4, "rules", 195, 1090, [("SPACE", YEL), (" allowed ", WHITE), ("NAHI", RED)], 72, "hand"),
    (35.0, "rules", 195, 1185, [("Ex.", GREEN)], 60, "hand"),
    (35.2, "rules", 305, 1185, [("roll no", None)], 58, "code"),
    (36.5, "rules", 305, 1270, [("roll_no", None)], 58, "code"),
    (38.8, "rules", 110, 1405, [("Bonus: ", ORANGE), ("Age", YEL), (" \u2260 ", WHITE), ("age", YEL)], 72, "hand"),
    (40.4, "rules", 110, 1490, [("(Python case-sensitive hai)", GREY)], 48, "hand"),
    # --- quiz
    (44.0, "quiz", 120, 610, [("Kaunsa naam ", WHITE), ("SAHI", GREEN), (" hai?", WHITE)], 82, "hand"),
]
NUMS = [(19.05, 125, 430, "1"), (26.15, 125, 760, "2"), (33.15, 125, 1090, "3")]      # circled numbers
DOTS = [(22.25, 720, 525, False), (23.6, 720, 610, True), (29.55, 720, 855, False),
        (30.95, 720, 940, True), (36.05, 720, 1185, False), (37.35, 720, 1270, True)]
REACT = [(22.3, "Galat!", RED), (23.65, "Sahi!", GREEN), (29.6, "Hyphen nahi!", RED), (31.0, "Sahi!", GREEN),
         (36.1, "Space nahi!", RED), (37.4, "Perfect!", GREEN), (49.15, "Sahi jawab!", GREEN)]
BOXES = [(5.9, 300, 880, "name", '"Rahul"', ORANGE, 6.75), (6.6, 750, 880, "age", "20", CYAN, 7.35)]
OUTPUT_T = 11.65
SLAM_RULES = 17.15
QUIZ_SLAM = 43.2
OPTIONS = [(45.0, "A", "2pac"), (45.3, "B", "my name"), (45.6, "C", "total_marks")]
COUNT0, REVEAL = 46.2, 49.2
TITLEBOX_T = 3.3


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


def glowify(im, col=None, r=10, strength=2):
    """neon marker glow behind an RGBA image"""
    pad = r * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad))
    a = Image.new("L", out.size)
    a.paste(im.getchannel("A"), (pad, pad))
    g = Image.new("RGBA", out.size, (col or (255, 255, 255)) + (0,))
    g.putalpha(a.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * 0.75)))
    for _ in range(strength):
        out.alpha_composite(g)
    out.alpha_composite(im, (pad, pad))
    return out, pad


# ------------------------------------------------------------------ text rendering (cached)
@lru_cache(None)
def write_img(segs, size, kind):
    """returns (img, pad, char_x) - char_x[i] = x where char i ends (for write-on)"""
    if kind == "code":
        f = mb.font(MONO, size)
        text = "".join(s for s, _ in segs)
        cols = []
        for tok, col in bs.tokens(text):
            cols += [col] * len(tok)
    else:
        f = mb.font(HAND, size)
        text = "".join(s for s, _ in segs)
        cols = [c for s, c in segs for _ in s]
    asc, desc = f.getmetrics()
    w = int(f.getlength(text)) + 20
    im = Image.new("RGBA", (w, asc + desc + 20))
    d = ImageDraw.Draw(im)
    x, xs = 10, []
    for ch, col in zip(text, cols):
        d.text((x, 10), ch, font=f, fill=col + (255,))
        x += f.getlength(ch)
        xs.append(x)
    # marker texture: tiny alpha breakup
    a = np.asarray(im.getchannel("A")).astype(np.float32)
    a *= 0.88 + 0.12 * np.random.default_rng(len(text)).random(a.shape)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    g, pad = glowify(im, None, 9, 1)
    return g, pad, xs


def draw_write(st, t, ev, cam_scale=1.0):
    t0, _, x, y, segs, size, kind = ev
    segs = tuple(segs)
    img, pad, xs = write_img(segs, size, kind)
    n = len(xs)
    dur = max(0.25, n / CPS) if kind == "hand" else max(0.25, n / (CPS * 1.3))
    p = clamp((t - t0) / dur)
    if p <= 0:
        return None
    k = p * n
    i = int(k)
    xcut = xs[min(i, n - 1)] if i >= n else (xs[i - 1] if i else 10) + (xs[min(i, n - 1)] - (xs[i - 1] if i else 10)) * (k - i)
    vis = img.crop((0, 0, int(xcut + pad + 6), img.height))
    st.alpha_composite(vis, (int(x - pad), int(y - img.height / 2)))
    if p < 1:      # glowing nib at the pen tip
        return (x + xcut - 10, y + size * 0.15)
    return None


def nib(st, pos, t):
    if pos is None:
        return
    x, y = pos
    lay = Image.new("RGBA", (120, 120))
    d = ImageDraw.Draw(lay)
    d.ellipse((40, 40, 80, 80), fill=(255, 255, 255, 200))
    lay = lay.filter(ImageFilter.GaussianBlur(9))
    ImageDraw.Draw(lay).ellipse((54, 54, 66, 66), fill=(255, 255, 255, 255))
    st.alpha_composite(lay, (int(x - 60 + 3 * math.sin(t * 40)), int(y - 60)))


@lru_cache(None)
def circle_num(n):
    S = 3
    im = Image.new("RGBA", (110 * S, 110 * S))
    d = ImageDraw.Draw(im)
    d.ellipse((8 * S, 8 * S, 102 * S, 102 * S), outline=WHITE, width=6 * S)
    d.text((55 * S, 57 * S), n, font=mb.font(HAND, 62 * S), fill=YEL, anchor="mm")
    im = im.resize((110, 110), Image.LANCZOS)
    return glowify(im, None, 8, 1)[0]


def draw_circle_num(st, t, ev):
    t0, x, y, n = ev
    p = clamp((t - t0) / 0.35)
    if p <= 0:
        return
    im = circle_num(n)
    if p < 1:     # reveal as a sweeping arc
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).pieslice((-40, -40, im.width + 40, im.height + 40), -90, -90 + 360 * p, fill=255)
        im = im.copy()
        im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(m))))
    paste(st, im, x, y)


@lru_cache(None)
def dot(ok, size=64):
    return glowify(bs.icon_check(size, ok), GREEN if ok else RED, 10, 2)[0]


# ------------------------------------------------------------------ board graphics
BOX_W, BOX_H = 330, 240


def box_lines(cx, cy):
    """3D open box as line segments (back rim first, then front face)"""
    w, h, dx, dy = BOX_W, BOX_H, 60, -50
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    back = [((x0 + dx, y0 + dy), (x1 + dx, y0 + dy)), ((x1 + dx, y0 + dy), (x1 + dx, y1 + dy)),
            ((x0, y0), (x0 + dx, y0 + dy)), ((x1, y0), (x1 + dx, y0 + dy)), ((x1, y1), (x1 + dx, y1 + dy))]
    front = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return back, front, (x0, y0, x1, y1)


def draw_lines(d, lines, p, col, width):
    total = sum(math.dist(a, b) for a, b in lines)
    left = total * p
    for a, b in lines:
        L = math.dist(a, b)
        if left <= 0:
            break
        f = min(1, left / L)
        d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=col, width=width)
        left -= L


@lru_cache(None)
def value_card(txt, col):
    f = mb.font(MONO, 56)
    w = int(f.getlength(txt)) + 60
    im = Image.new("RGBA", (w, 100))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, 97), 22, fill=(25, 27, 32), outline=col, width=5)
    d.text((w / 2, 50), txt, font=f, fill=col, anchor="mm")
    return glowify(im, col, 10, 1)[0]


def draw_box(st, t, ev):
    t0, cx, cy, label, val, col, tdrop = ev
    p = clamp((t - t0) / 0.6)
    if p <= 0:
        return
    back_l, front_l, (x0, y0, x1, y1) = box_lines(cx, cy)
    lay = Image.new("RGBA", st.size)
    d = ImageDraw.Draw(lay)
    draw_lines(d, back_l, clamp(p * 1.6), WHITE + (200,), 7)
    # value card dropping in (drawn before the front face so it sits "inside")
    if t >= tdrop - 0.45:
        q = clamp((t - tdrop + 0.45) / 0.45)
        yy = (cy - 1000) + (cy - 70 - (cy - 1000)) * q ** 2
        if q >= 1:
            a = t - tdrop
            yy = cy - 70 - 22 * abs(math.sin(a * 14)) * math.exp(-a * 6)
        paste(lay, value_card(val, col), cx + 20, yy)
    # front face (opaque so the card looks inside)
    if p > 0.3:
        fa = int(235 * clamp((p - 0.3) / 0.3))
        d.rectangle((x0, y0, x1, y1), fill=(14, 15, 18, fa))
    draw_lines(d, front_l, clamp(p * 1.6 - 0.6), WHITE + (255,), 7)
    if p > 0.75:
        tag = mb.font(MONO, 50)
        d.rounded_rectangle((cx - 95, cy + 20, cx + 95, cy + 90), 14, fill=(255, 214, 77, 255))
        d.text((cx, cy + 55), label, font=tag, fill=(20, 20, 20), anchor="mm")
    g = lay.filter(ImageFilter.GaussianBlur(8))
    st.alpha_composite(g)
    st.alpha_composite(lay)


def draw_output(st, t):
    a = t - OUTPUT_T
    if a < 0:
        return
    s = pop(a, 0.35)
    im = Image.new("RGBA", (720, 120))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, 717, 117), 26, fill=(14, 40, 24), outline=GREEN, width=5)
    d.text((40, 60), "Output:", font=mb.font(HAND, 46), fill=GREY, anchor="lm")
    d.text((250, 62), "Rahul 20", font=mb.font(MONO, 60), fill=GREEN, anchor="lm")
    paste(st, glowify(im, GREEN, 12, 1)[0], 440, 1465, s)


def slam_text(st, t, t0, txt, y, size, fill, edge, rot=-3):
    a = t - t0
    if a < -0.02:
        return
    s = 1 + 1.4 * (1 - ease(a / 0.18)) if a < 0.18 else 1 + 0.02 * math.sin(a * 6)
    im = mb.outlined(txt, mb.font(mb.BALOO, size, "ExtraBold"), fill, 10, (10, 10, 10), 8, edge)
    paste(st, im, 540, y, s, clamp(a / 0.06), rot)


@lru_cache(None)
def _outlined(txt, size, fill, edge):
    return mb.outlined(txt, mb.font(mb.BALOO, size, "ExtraBold"), fill, 10, (10, 10, 10), 8, edge)


def warning_icon(st, t, t0, cx, cy):
    s = pop(t - t0, 0.35)
    if s <= 0:
        return
    S = 3
    im = Image.new("RGBA", (200 * S, 180 * S))
    d = ImageDraw.Draw(im)
    d.polygon([(100 * S, 8 * S), (192 * S, 170 * S), (8 * S, 170 * S)], fill=YEL)
    d.text((100 * S, 115 * S), "!", font=mb.font(mb.BALOO, 120 * S, "ExtraBold"), fill=(20, 20, 20), anchor="mm")
    im = im.resize((200, 180), Image.LANCZOS)
    paste(st, glowify(im, YEL, 14, 1)[0], cx, cy, s * (1 + 0.05 * math.sin(t * 8)))


def option_card(letter, txt, state):
    col = {None: (90, 95, 110), True: GREEN, False: RED}[state]
    im = Image.new("RGBA", (760, 130))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 756, 126), 30, fill=(20, 22, 27), outline=col, width=6)
    d.ellipse((24, 22, 110, 108), fill=col)
    d.text((67, 66), letter, font=mb.font(mb.BALOO, 58, "ExtraBold"), fill=(15, 15, 15), anchor="mm")
    d.text((150, 66), txt, font=mb.font(MONO, 56), fill=WHITE, anchor="lm")
    if state is not None:
        paste(im, bs.icon_check(70, state), 690, 65)
    return glowify(im, col, 10, 1)[0] if state is not None else im


def draw_quiz(st, t):
    slam_text(st, t, QUIZ_SLAM, "QUIZ TIME!", 420, 150, YEL, (140, 90, 0), -4)
    for k, (t0, letter, txt) in enumerate(OPTIONS):
        state = None if t < REVEAL else (letter == "C")
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == "C":
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, option_card(letter, txt, state), 540, 820 + k * 170, sc, 1 if (t < REVEAL or letter == "C") else 0.55)
    # countdown ring
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (220 * S, 220 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 210 * S, 210 * S), outline=(60, 60, 70), width=14 * S)
        frac = clamp(rem / (REVEAL - COUNT0))
        d.arc((10 * S, 10 * S, 210 * S, 210 * S), -90, -90 + 360 * frac, fill=YEL, width=14 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((110 * S, 112 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 110 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        im = im.resize((220, 220), Image.LANCZOS)
        ph = (t - COUNT0) % 1
        paste(st, im, 540, 1385, 1 + 0.08 * math.exp(-ph * 8) * (t < REVEAL))
    if t >= COUNT0 + 0.2:
        paste(st, _outlined("Comment karo!", 64, WHITE, (40, 40, 40)), 540, 1560, pop(t - COUNT0 - 0.2), 1, 2)


def draw_hook(st, t):
    paste(st, _outlined("PYTHON", 120, WHITE, (40, 40, 50)), 540, 560, pop(t - 0.05), 1, -2)
    paste(st, _outlined("VARIABLES", 168, YEL, (150, 95, 0)), 540, 760, pop(t - 0.25, 0.35), 1, -2)
    rb = mb.ribbon([("+ 3 GOLDEN RULES", (20, 20, 20), False)], mb.font(mb.BALOO, 64, "ExtraBold"), 110, 40,
                   fill=(255, 90, 95))
    paste(st, rb, 540, 960, pop(t - 0.55), 1, 2)
    # dabba with "?" bouncing
    if t > 0.7:
        lay = Image.new("RGBA", st.size)
        back_l, front_l, (x0, y0, x1, y1) = box_lines(400, 1290)
        d = ImageDraw.Draw(lay)
        p = clamp((t - 0.7) / 0.5)
        draw_lines(d, back_l, p, WHITE + (210,), 7)
        d.rectangle((x0, y0, x1, y1), fill=(14, 15, 18, int(230 * p)))
        draw_lines(d, front_l, p, WHITE + (255,), 7)
        st.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
        st.alpha_composite(lay)
        q = _outlined("?", 170, YEL, (150, 95, 0))
        paste(st, q, 410, 1110 - 30 * abs(math.sin(t * 5)), pop(t - 1.0))
    paste(st, mb.mascot(430) if "m430" not in _C else _C["m430"], 830, 1340, pop(t - 0.9, 0.4))


_C = {}


# ------------------------------------------------------------------ static layers
@lru_cache(None)
def board_bg():
    """black glass: faint blue-grey gradient, diagonal reflections, dust, vignette"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .42) / H) ** 2)
    base = np.clip(1 - r * 1.25, 0, 1)[..., None] * np.array([20, 22, 28], np.float32) + 6
    refl = np.zeros((H, W), np.float32)
    for k, (off, wid, a) in enumerate(((-300, 160, 7), (250, 90, 5), (700, 220, 4))):
        dline = (xx * 0.6 - yy * 0.8 + off)
        refl += a * np.exp(-(dline / wid) ** 2)
    base += refl[..., None]
    rng = np.random.default_rng(2)
    base += rng.normal(0, 1.6, (H, W, 1))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(140):   # dust specks on the glass
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, 3)
        d.ellipse((x, y, x + s, y + s), fill=(255, 255, 255, int(rng.uniform(15, 50))))
    return im


@lru_cache(None)
def side_text():
    f = mb.font(mb.BALOO, 30, "Bold")
    txt = "P Y T H O N   K I   P A T H S H A L A   •   E P  0 2"
    w = int(f.getlength(txt)) + 10
    im = Image.new("RGBA", (w, 46))
    ImageDraw.Draw(im).text((5, 23), txt, font=f, fill=(120, 125, 135, 200), anchor="lm")
    return im.rotate(90, expand=True)


@lru_cache(None)
def title_box():
    im = Image.new("RGBA", (560, 150))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 556, 146), 20, outline=YEL, width=5, fill=(10, 10, 12, 180))
    d.text((28, 48), "Python Variables", font=mb.font(mb.BALOO, 52, "ExtraBold"), fill=YEL, anchor="lm")
    d.text((28, 108), "+ 3 Golden Rules", font=mb.font(mb.BALOO, 46, "ExtraBold"), fill=WHITE, anchor="lm")
    return glowify(im, YEL, 8, 1)[0]


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
    return np.clip(1 - 0.5 * r ** 2.4, 0.4, 1)[..., None]


GRAIN = [np.random.default_rng(s).normal(0, 3.5, (H // 2, W // 2)).astype(np.float32) for s in range(5)]


# ------------------------------------------------------------------ mascot reactions
def mascot_layer(st, t, board):
    if board in ("hook",):
        return
    if "m" not in _C:
        _C["m"] = mb.mascot(300)
    t_in = {"dabba": 9.6, "rules_title": 16.0, "rules": 21.9, "quiz": 45.8}[board]
    s = pop(t - t_in, 0.4)
    if s <= 0:
        return
    react = None
    for tr, txt, col in REACT:
        if 0 <= t - tr < 1.0:
            react = (tr, txt, col)
    bob = 8 * math.sin(t * 3)
    rot = 0
    if react:
        a = t - react[0]
        rot = (10 * math.sin(a * 25) * math.exp(-a * 5)) if react[2] == RED else 0
        bob -= 30 * abs(math.sin(a * 10)) * math.exp(-a * 5) if react[2] == GREEN else 0
    paste(st, _C["m"], 935, 1580 + bob, s, 1, rot)
    if react:
        a = t - react[0]
        b = mb.bubble(react[1], mb.font(mb.BALOO, 46, "ExtraBold"), 20)
        paste(st, b, 830, 1355, pop(a, 0.22) * (1 - ease((a - 0.8) / 0.2)))


# ------------------------------------------------------------------ camera focus
def focus(t, board):
    """(cy, zoom) - the camera follows the pen like the reference reframes on the writer"""
    if board == "hook":
        return 960, 1.0 + 0.05 * ease(t / 3.2)
    if board == "quiz":
        return 980, 1.0 + 0.03 * ease((t - 43) / 8)
    if board == "rules_title":
        return 900, 1.04 + 0.03 * ease((t - 15.8) / 3)
    b0, b1 = [(s, e) for s, e, n in BOARDS if n == board][0]
    ys = [(ev[0], ev[3]) for ev in WRITES if ev[1] == board] + \
         [(bx[0], bx[2]) for bx in BOXES if board == "dabba"] + \
         ([(OUTPUT_T, 1465)] if board == "dabba" else [])
    ys.sort()
    cur, prev, tc = 960, 960, b0
    for te, y in ys:
        if te <= t:
            prev, cur, tc = cur, y, te
    cy = prev + (cur - prev) * ease((t - tc) / 0.7)
    cy = min(1010, max(820, 960 + (cy - 960) * 0.55))
    zoom = 1.07
    if t > b1 - 2.2:              # pull back to show the whole board before the wipe
        q = ease((t - (b1 - 2.2)) / 0.8)
        cy, zoom = cy + (900 - cy) * q, zoom + (1.0 - zoom) * q
    return cy, zoom


# ------------------------------------------------------------------ frame
def board_at(t):
    for s, e, n in BOARDS:
        if s <= t < e:
            return n
    return None


def render_board(t, board):
    st = Image.new("RGBA", (W, H))
    if board == "hook":
        draw_hook(st, t)
        return st
    nibpos = None
    for ev in WRITES:
        if ev[1] == board and t >= ev[0]:
            p = draw_write(st, t, ev)
            nibpos = p or nibpos
    if board == "dabba":
        for bx in BOXES:
            draw_box(st, t, bx)
        draw_output(st, t)
    elif board == "rules_title":
        slam_text(st, t, SLAM_RULES, "3 GOLDEN RULES!", 900, 118, YEL, (150, 95, 0))
        warning_icon(st, t, SLAM_RULES + 0.3, 540, 1150)
    elif board == "rules":
        for ev in NUMS:
            draw_circle_num(st, t, ev)
        for t0, x, y, ok in DOTS:
            paste(st, dot(ok), x, y, pop(t - t0, 0.25))
    elif board == "quiz":
        draw_quiz(st, t)
    nib(st, nibpos, t)
    return st


def camera(img, cy, zoom, dx=0.0, dy=0.0):
    M = cv2.getRotationMatrix2D((W / 2, cy), 0, zoom)
    M[1, 2] += (960 - cy) * 0.5 + dy
    M[0, 2] += dx
    return cv2.warpAffine(np.asarray(img), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


SHAKES = [(SLAM_RULES, 1.0), (QUIZ_SLAM, 0.8), (REVEAL, 0.4)]


def frame(i):
    t = i / FPS
    if t >= END0:
        return np.asarray(es.frame(t - END0).convert("RGB"))
    board = board_at(t)
    st = render_board(t, board)
    cy, z = focus(t, board)
    dx = dy = 0.0
    flash = 0.0
    for ts, s in SHAKES:
        a = t - ts
        if 0 <= a < 0.35:
            amp = 22 * s * (1 - a / 0.35)
            dx += amp * math.sin(a * 90)
            dy += amp * math.cos(a * 70)
            flash = max(flash, 0.45 * s * (1 - a / 0.15)) if a < 0.15 else flash
    stage = camera(st, cy, z, dx, dy)
    # eraser wipe into the next board: new board revealed behind a sweeping felt eraser
    for s, e, n in BOARDS[1:]:
        a = (t - s) / WIPE
        if 0 <= a < 1 and s > 0:
            prev = [b for b in BOARDS if b[1] == s][0][2]
            st2 = render_board(s - 0.001, prev)
            cy2, z2 = focus(s - 0.001, prev)
            old = camera(st2, cy2, z2)
            edge = int(-200 + (W + 400) * ease(a))
            mask = np.zeros((H, W), np.float32)
            xx = np.arange(W)[None, :] + (np.arange(H)[:, None] * 0.25)
            mask = np.clip((edge - xx) / 120, 0, 1)                      # 1 = new board
            stage = (stage.astype(np.float32) * mask[..., None] + old.astype(np.float32) * (1 - mask[..., None]))
            stage = stage.astype(np.uint8)
            _C["eraser"] = (edge, a)
    fr = board_bg().copy()
    if board != "hook" and t >= TITLEBOX_T:
        paste(fr, title_box(), 330, 215, pop(t - TITLEBOX_T, 0.35))
    fr.alpha_composite(side_text(), (14, H // 2 - side_text().height // 2))
    fr.alpha_composite(Image.fromarray(stage))
    mascot_layer(fr, t, board)
    e = _C.pop("eraser", None)
    if e:
        edge, a = e
        er = Image.new("RGBA", (190, 420))
        d = ImageDraw.Draw(er)
        d.rounded_rectangle((0, 0, 189, 419), 30, fill=(70, 72, 80))
        d.rounded_rectangle((0, 300, 189, 419), 30, fill=(235, 235, 240))
        paste(fr, er.rotate(-14, expand=True), edge - 0.25 * 960 + 20, 960, 1, 1)
    a = np.asarray(fr.convert("RGB")).astype(np.float32)
    if flash > 0:
        a += (255 - a) * flash
    a *= vignette()
    a += cv2.resize(GRAIN[i % len(GRAIN)], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def marker_squeak(dur, seed):
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    x = fx.filt(r.normal(0, 1, n), "bandpass", [1400, 5200])
    tt = np.arange(n) / SR
    am = 0.55 + 0.45 * np.sin(2 * np.pi * (14 + 6 * np.sin(2 * np.pi * 1.3 * tt)) * tt) ** 2
    strokes = (r.random(int(dur * 9) + 2) > 0.25).repeat(SR // 9)[:n]
    env = np.minimum(1, tt / 0.03) * np.minimum(1, (dur - tt) / 0.05)
    return x * am * strokes * env * 0.18


def cap_click():
    n = int(0.06 * SR)
    return fx.filt(fx.noise(n, 21), "bandpass", [1800, 7000]) * fx.env_exp(n, 140) * 0.7


def buzzer():
    n = int(0.32 * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 150 * tt)) + 0.5 * np.sign(np.sin(2 * np.pi * 112 * tt))
    return fx.filt(x, "lowpass", 1500, 2) * np.minimum(1, (0.32 - tt) / 0.06) * 0.22


def thud():
    n = int(0.3 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (55 + 110 * np.exp(-tt * 28)) * tt) * np.exp(-tt * 13) * 0.9


def eraser_swish():
    n = int(WIPE * SR)
    tt = np.linspace(0, 1, n)
    x = fx.filt(fx.noise(n, 33), "bandpass", [300, 2500])
    return x * np.sin(np.pi * tt) ** 1.5 * 0.9


def tick():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 90) * 0.5


def chime():
    n = int(1.4 * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for k, f in enumerate((783.99, 987.77, 1174.66, 1567.98)):
        s = int(k * 0.06 * SR)
        x[s:] += np.sin(2 * np.pi * f * tt[: n - s]) * np.exp(-tt[: n - s] * 3.2) * 0.28
    return x


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    # hook
    P(buf, fx.boom(), 0.05, 0.7)
    P(buf, fx.pop(), 0.25, 0.6)
    P(buf, fx.whoosh(0.3, 1), 0.45, 0.5)
    P(buf, fx.pop(), 0.55, 0.5)
    P(buf, fx.pop(), 1.0, 0.5)
    for s, e, n in BOARDS[1:]:
        P(buf, eraser_swish(), s, 0.55)
        P(buf, cap_click(), s + 0.2, 0.5)
    for ev in WRITES:
        n = len("".join(s for s, _ in ev[4]))
        dur = max(0.25, n / CPS) if ev[6] == "hand" else max(0.25, n / (CPS * 1.3))
        P(buf, marker_squeak(dur, int(ev[0] * 10)), ev[0], 1.0)
    for t0, *_ in NUMS:
        P(buf, marker_squeak(0.35, int(t0 * 7)), t0, 1.0)
    for t0, _, _, ok in DOTS:
        P(buf, fx.pop(), t0, 0.5)
        P(buf, fx.ding() if ok else buzzer(), t0 + 0.02, 0.45 if ok else 0.8)
    for t0, cx, cy, label, val, col, tdrop in BOXES:
        P(buf, marker_squeak(0.6, int(t0 * 3)), t0, 1.0)
        P(buf, fx.whoosh(0.35, int(tdrop)), tdrop - 0.4, 0.35)
        P(buf, thud(), tdrop, 0.8)
        P(buf, fx.pop(), tdrop + 0.02, 0.4)
    P(buf, fx.pop(), OUTPUT_T, 0.6)
    P(buf, fx.ding(), OUTPUT_T + 0.05, 0.5)
    P(buf, fx.riser(1.0), SLAM_RULES - 1.0, 0.45)
    P(buf, fx.boom(), SLAM_RULES, 1.0)
    P(buf, fx.pop(), SLAM_RULES + 0.3, 0.5)
    P(buf, fx.riser(0.6), QUIZ_SLAM - 0.6, 0.35)
    P(buf, fx.boom(), QUIZ_SLAM, 0.8)
    for t0, *_ in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    k = 0
    tt = COUNT0
    while tt < REVEAL - 0.05:
        P(buf, tick(), tt, 0.6)
        tt += 0.5
        k += 1
    P(buf, chime(), REVEAL, 0.9)
    P(buf, fx.boom()[: int(0.5 * SR)], REVEAL, 0.5)
    e = es.sfx()
    P(buf, e, END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=SLAM_RULES)
    # second break + re-drop into the quiz
    beat = 60 / 112
    i0, i1 = int((QUIZ_SLAM - beat) * SR), int(QUIZ_SLAM * SR)
    music[i0:i1] *= np.linspace(1, 0.25, i1 - i0)
    fx.write_wav(os.path.join(WORK, "music.wav"), music)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track() * 0.8)
    out = os.path.join(WORK, "mix.wav")
    fc = ("[0:a]loudnorm=I=-17:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[sfx];"
          "[mus][sfx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i",
                    os.path.join(WORK, "sfx.wav"), "-filter_complex", fc, "-map", "[out]", "-t", f"{TOTAL:.3f}", out],
                   check=True)
    return out


# ------------------------------------------------------------------ main
def main():
    preview = "--preview" in sys.argv
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    _C["m430"] = mb.mascot(430)
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
