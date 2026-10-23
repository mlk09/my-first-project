#!/usr/bin/env python3
"""Python ki Pathshala EP 14 - Strings + 5 string methods  (1080x1920 HD Short)

Decoded from 4 reference stills:
  1  (HTPMR) black, MULTICOLOUR title "Python"(yellow->cyan) "String"(red) "Methods"(green); a dark editor
     with mac dots and a long cheat-sheet: "Hello World".method()  -->  result, one per numbered line
  2-4 (CodeGurukul) a CAROUSEL: navy background with faint blurred maths/code SYMBOLS (sum, pi, { }, </>, /),
     brand badge top-left + slide counter "2/5" top-right, an outlined cyan TAG pill ("CLEAN UP", "SPLIT",
     "JOIN"), a HUGE white method name (".strip()") with a short cyan UNDERLINE bar, a code card with mac
     dots and the output as a blue "# comment"
Ours: same look as EP 13 with ONE background everywhere (navy + grid + moving floor + triangles + symbol
watermark), carousel slides with a swipe transition, a live visual for every method, a cheat-sheet,
a tricky question and the end screen on the same background. Original Hinglish content.

Usage:  python3 edit21/build_ep14.py [--preview]
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
sys.path.insert(0, os.path.join(HERE, "..", "edit20"))
import build_ep13 as e13   # noqa: E402  EP 13: background, comic text, end screen, EP 12/11/08 helpers

b, p11, m = e13.b, e13.p11, e13.m
fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste, glow = m.clamp, m.ease, m.pop, m.paste, b.glow
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
inter, MONO = b.inter, b.MONO
es.NEXT = "EP 15: STRING SLICING"
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

WHITE, YEL, GREEN, RED, ORANGE, CYAN = e13.WHITE, e13.YEL, e13.GREEN, e13.RED, e13.ORANGE, e13.CYAN
TAGC, COMMENT, STRC = (40, 200, 255), (100, 170, 255), (255, 190, 120)

SCENES = [(0.0, "hook"), (3.8, "what"), (13.0, "s1"), (20.0, "s2"), (26.5, "s3"), (33.0, "s4"), (39.5, "s5"),
          (46.0, "cheat"), (51.0, "tricky")]
END0 = 60.5
TOTAL = END0 + es.DUR
SWIPE = 0.35
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP14_Strings.mp4")
WORK = os.path.join(HERE, "work")
_C = {}


# ------------------------------------------------------------------ ONE background (+ symbol watermark)
@lru_cache(None)
def symbols_layer():
    im = Image.new("RGBA", (W, H + 400))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(14)
    syms = ["∑", "π", "{ }", "</>", "÷", "√", "==", "&&", "//", "( )", "#", "+", "%", "[ ]", "≠"]
    for k in range(34):
        s = syms[k % len(syms)]
        x, y, sz = rng.uniform(0, W), rng.uniform(0, H + 400), int(rng.uniform(60, 120))
        d.text((x, y), s, font=mb.font(DEJAVU, sz), fill=(120, 160, 230, int(rng.uniform(16, 30))), anchor="mm")
    return im.filter(ImageFilter.GaussianBlur(3))


def bg14(t):
    fr = e13.bg13(t)
    off = int(t * 14) % 400
    fr.alpha_composite(symbols_layer().crop((0, off, W, off + H)))
    return fr


# ------------------------------------------------------------------ reference text styles
@lru_cache(None)
def multi_title():
    """ref 1: 'Python' yellow->cyan gradient, 'String' red, 'Methods' green"""
    f1, f2 = inter(150, "ExtraBold"), inter(190, "ExtraBold")
    w1, w2 = f1.getlength("Python "), f1.getlength("String")
    w = int(max(w1 + w2, f2.getlength("Methods"))) + 80
    im = Image.new("RGBA", (w, 430))
    x0 = (w - w1 - w2) / 2
    mask = Image.new("L", im.size)
    ImageDraw.Draw(mask).text((x0, 110), "Python", font=f1, fill=255, anchor="lm")
    grad = np.zeros((im.height, w, 4), np.uint8)
    xs = np.linspace(0, 1, w)[None, :]
    grad[..., 0] = (255 * (1 - xs) + 40 * xs).astype(np.uint8)
    grad[..., 1] = (215 * (1 - xs) + 220 * xs).astype(np.uint8)
    grad[..., 2] = (40 * (1 - xs) + 240 * xs).astype(np.uint8)
    grad[..., 3] = np.asarray(mask)
    im.alpha_composite(Image.fromarray(grad))
    d = ImageDraw.Draw(im)
    d.text((x0 + w1, 110), "String", font=f1, fill=(255, 70, 70), anchor="lm")
    d.text((w / 2, 310), "Methods", font=f2, fill=(70, 230, 80), anchor="mm")
    return glow(im, 12, 0.8, (255, 255, 255))


@lru_cache(None)
def tag_pill(txt):
    f = inter(46, "ExtraBold")
    w = int(f.getlength(txt)) + 70
    im = Image.new("RGBA", (w + 30, 110))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, w + 15, 95), 40, fill=(6, 30, 60, 200), outline=TAGC, width=4)
    d.text((w / 2 + 15, 56), txt, font=f, fill=TAGC, anchor="mm")
    return glow(im, 8, 0.8, TAGC)


@lru_cache(None)
def method_title(txt, size=150):
    f = inter(size, "ExtraBold")
    w = int(f.getlength(txt)) + 40
    im = Image.new("RGBA", (w, int(size * 1.3)))
    ImageDraw.Draw(im).text((10, im.height / 2), txt, font=f, fill=(238, 242, 255), anchor="lm")
    return glow(im, 10, 0.5, (130, 170, 255))


def slide_head(st, t, t0, tag, title, n, title2=None):
    """badge + counter + tag pill + huge method name (left aligned) + growing cyan underline"""
    a = t - t0
    if a < 0:
        return
    al = ease(a / 0.25)
    badge = brand_badge()
    paste(st, badge, 60 + badge.width / 2, 200, 1, al)
    cnt = b.big_num(f"{n}/5", (150, 165, 200), 40)
    paste(st, cnt, 1000 - cnt.width / 2, 200, 1, al)
    tp = tag_pill(tag)
    paste(st, tp, 45 + tp.width / 2 + 40 * (1 - ease(a / 0.3)), 320, 1, al)
    mt = method_title(title)
    paste(st, mt, 50 + mt.width / 2, 470, pop(a - 0.15, 0.35))
    yb = 560
    if title2:
        mt2 = method_title(title2)
        paste(st, mt2, 50 + mt2.width / 2, 650, pop(a - 0.3, 0.35))
        yb = 740
    q = ease((a - 0.45) / 0.35)
    if q > 0:
        lay = Image.new("RGBA", (W, H))
        ImageDraw.Draw(lay).rectangle((60, yb, 60 + 220 * q, yb + 12), fill=TAGC + (255,))
        st.alpha_composite(glow(lay, 8, 1.0, TAGC))


@lru_cache(None)
def brand_badge():
    im = Image.new("RGBA", (470, 80))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 4, 72, 76), 16, fill=TAGC)
    d.text((36, 41), "Py", font=inter(36, "ExtraBold"), fill=(6, 20, 40), anchor="mm")
    d.text((92, 41), "Python ki Pathshala", font=inter(36, "SemiBold"), fill=(225, 232, 248), anchor="lm")
    return im


# ------------------------------------------------------------------ code card (mac dots, comment output)
def tok(line):
    cols, i = [], 0
    if line.lstrip().startswith("#"):
        return [COMMENT] * len(line)
    while i < len(line):
        ch = line[i]
        if ch in "\"'":
            j = line.find(ch, i + 1)
            j = len(line) if j < 0 else j + 1
            cols += [STRC] * (j - i)
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            wd = line[i:j]
            prev = line[i - 1] if i else ""
            c = (230, 220, 140) if wd == "print" else (120, 220, 255) if prev == "." else (235, 238, 248)
            cols += [c] * (j - i)
            i = j
        elif ch.isdigit():
            cols.append((181, 220, 168))
            i += 1
        else:
            cols.append((210, 215, 230))
            i += 1
    return cols


def code_card(st, t, lines, y0, size=44, lh=70, cps=28):
    """lines = [(t, text)]; a line starting with '#' pops in (output) instead of typing"""
    if t < lines[0][0] - 0.35:
        return
    q = ease((t - lines[0][0] + 0.35) / 0.3)
    y1 = y0 + 70 + len(lines) * lh + 10
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((60, y0, 1020, y1), 24, fill=(10, 18, 42, int(230 * q)), outline=(60, 80, 130, int(220 * q)),
                        width=3)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((90 + 34 * k, y0 + 24, 110 + 34 * k, y0 + 44), fill=c + (int(255 * q),))
    st.alpha_composite(lay)
    f = mb.font(MONO, size)
    d = ImageDraw.Draw(st)
    for k, (ts, txt) in enumerate(lines):
        if t < ts:
            continue
        y = y0 + 70 + k * lh + lh / 2 - 6
        if txt.startswith("#"):
            im = Image.new("RGBA", (int(f.getlength(txt)) + 40, lh + 20))
            ImageDraw.Draw(im).text((20, im.height / 2), txt, font=f, fill=COMMENT, anchor="lm")
            paste(st, glow(im, 8, 0.9, COMMENT), 90 + im.width / 2 - 20 + 30 * (1 - ease((t - ts) / 0.25)), y, 1,
                  ease((t - ts) / 0.2))
            continue
        n = min(len(txt), int((t - ts) * cps) + 1)
        cols, x = tok(txt), 92
        for j in range(n):
            d.text((x, y), txt[j], font=f, fill=cols[j], anchor="lm")
            x += f.getlength(txt[j])
        if n < len(txt):
            d.rectangle((x + 3, y - 24, x + 7, y + 24), fill=WHITE)


# ------------------------------------------------------------------ tiles (live visuals)
@lru_cache(None)
def tile(ch, col, w=86, h=100, dashed=False):
    im = Image.new("RGBA", (w + 30, h + 30))
    d = ImageDraw.Draw(im)
    if dashed:
        for k in range(0, w, 16):
            d.line((15 + k, 15, 15 + min(k + 8, w), 15), fill=col + (220,), width=4)
            d.line((15 + k, 15 + h, 15 + min(k + 8, w), 15 + h), fill=col + (220,), width=4)
        for k in range(0, h, 16):
            d.line((15, 15 + k, 15, 15 + min(k + 8, h)), fill=col + (220,), width=4)
            d.line((15 + w, 15 + k, 15 + w, 15 + min(k + 8, h)), fill=col + (220,), width=4)
        d.text((15 + w / 2, 15 + h / 2), "␣", font=mb.font(DEJAVU, 40), fill=col, anchor="mm")
        return im
    d.rounded_rectangle((15, 15, 15 + w, 15 + h), 18, fill=(10, 24, 56, 240), outline=col, width=5)
    d.text((15 + w / 2, 15 + h / 2 + 2), ch, font=mb.font(MONO, int(h * 0.55)), fill=WHITE, anchor="mm")
    return glow(im, 10, 0.9, col)


@lru_cache(None)
def word_chip(txt, col, size=54):
    f = mb.font(MONO, size)
    w = int(f.getlength(txt)) + 50
    im = Image.new("RGBA", (w + 30, int(size * 1.9) + 30))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + w, im.height - 15), 20, fill=(10, 24, 56, 240), outline=col, width=5)
    d.text((15 + w / 2, im.height / 2 + 2), txt, font=f, fill=WHITE, anchor="mm")
    return glow(im, 10, 0.9, col)


VIS_Y = 1140


def vis_strip(st, t, t0, t_go):
    """'  Rohan  ' -> spaces (dashed tiles) zip out, letters slide together"""
    if t < t0:
        return
    chars = list("  Rohan  ")
    q = ease((t - t_go) / 0.5)
    step = 96
    n = len(chars)
    for k, ch in enumerate(chars):
        sp = ch == " "
        x_full = 470 - step * (n - 1) / 2 + step * k
        x_tight = 470 - step * 4 / 2 + step * (k - 2)
        x = x_full + (x_tight - x_full) * q if not sp else x_full + (-300 if k < 2 else 300) * q
        al = 1 - q if sp else 1
        paste(st, tile(ch, (120, 140, 180) if sp else CYAN, dashed=sp), x, VIS_Y, pop(t - t0 - 0.05 * k, 0.25) *
              (1 - 0.5 * q if sp else 1), al)


def vis_upper(st, t, t0, t_go):
    if t < t0:
        return
    for k, ch in enumerate("chai"):
        tk = t_go + 0.15 * k
        flip = clamp((t - tk) / 0.25)
        s_y = abs(math.cos(math.pi * flip))
        c = ch.upper() if flip > 0.5 else ch
        im = tile(c, YEL if flip > 0.5 else CYAN, 110, 120)
        im = im.resize((im.width, max(2, int(im.height * max(0.05, s_y)))), Image.BICUBIC)
        paste(st, im, 470 - 195 + 130 * k, VIS_Y, pop(t - t0 - 0.06 * k, 0.25))


def vis_replace(st, t, t0, t_go):
    if t < t0:
        return
    words = ["chai", "garam", "hai"]
    xs = [240, 520, 760]
    for k, wd in enumerate(words):
        if k == 0:
            flip = clamp((t - t_go) / 0.35)
            s_y = abs(math.cos(math.pi * flip))
            wd2, col = ("coffee", YEL) if flip > 0.5 else (wd, CYAN)
            im = word_chip(wd2, col)
            im = im.resize((im.width, max(2, int(im.height * max(0.05, s_y)))), Image.BICUBIC)
            paste(st, im, xs[k] - (30 if flip > 0.5 else 0), VIS_Y, pop(t - t0, 0.25))
            if flip >= 1:
                b.sparkle_burst(st, t, t_go + 0.35, xs[k] - 30, VIS_Y, 10, YEL, 120)
        else:
            paste(st, word_chip(wd, CYAN), xs[k] + (30 if t >= t_go + 0.17 else 0) * ease((t - t_go - 0.17) / 0.2),
                  VIS_Y, pop(t - t0 - 0.08 * k, 0.25))


def vis_split(st, t, t0, t_go):
    if t < t0:
        return
    q = ease((t - t_go) / 0.45)
    if q <= 0:
        paste(st, word_chip("aam,kela,seb", CYAN, 54), 470, VIS_Y, pop(t - t0, 0.3))
        return
    parts = ["aam", "kela", "seb"]
    full = [300, 470, 640]
    spread = [190, 470, 750]
    for k, p in enumerate(parts):
        x = full[k] + (spread[k] - full[k]) * q
        paste(st, word_chip(p, GREEN, 54), x, VIS_Y + (-30 if k == 1 else 0) * math.sin(math.pi * q), 1)
    if q < 1:
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        for xx in (385, 555):
            d.line((xx, VIS_Y - 70, xx + 12, VIS_Y, xx - 8, VIS_Y + 70), fill=(255, 255, 255, int(255 * (1 - q))),
                   width=6)
        st.alpha_composite(lay)


def vis_join(st, t, t0, t_go):
    if t < t0:
        return
    q = ease((t - t_go) / 0.45)
    parts = ["24", "10", "2026"]
    spread = [210, 460, 760]
    tight = [300, 440, 620]
    for k, p in enumerate(parts):
        x = spread[k] + (tight[k] - spread[k]) * q
        paste(st, word_chip(p, CYAN if q < 1 else GREEN, 54), x, VIS_Y, pop(t - t0 - 0.08 * k, 0.25))
    if q >= 0.9:
        for k, xx in enumerate((370, 515)):
            paste(st, b.big_num("-", YEL, 80), xx, VIS_Y - 4, pop(t - t_go - 0.45 - 0.08 * k, 0.25))


# ------------------------------------------------------------------ scenes
HOOK_CHIPS = [(1.2, ".strip()", 230, 1060), (1.35, ".upper()", 820, 1130), (1.5, ".replace()", 260, 1260),
              (1.65, ".split()", 800, 1340), (1.8, ".join()", 360, 1430)]


def draw_hook(st, t):
    im = b.sweep(multi_title(), t, 1.0, 0.7)
    paste(st, im, 540, 640, pop(t - 0.1, 0.4))
    for k, (t0, txt, x, y) in enumerate(HOOK_CHIPS):
        paste(st, word_chip(txt, [CYAN, YEL, ORANGE, GREEN, (255, 105, 190)][k], 46), x,
              y + 12 * math.sin(t * 3 + k), pop(t - t0, 0.3), 1, 4 * math.sin(k + 1))
    b.caption(st, t, 2.3, [("5 methods, ", WHITE), ("1 minute!", YEL)], 540, 1600, 64)


WHAT_CODE = [(5.0, 'naam = "Python"')]
BEADS_T = 6.2
IDX_T = 8.0
QUOTE_T = 10.2


def draw_what(st, t):
    tp = tag_pill("BASICS")
    paste(st, tp, 45 + tp.width / 2, 320, pop(t - 3.95, 0.3))
    mt = method_title("String kya hai?", 120)
    paste(st, mt, 50 + mt.width / 2, 450, pop(t - 4.1, 0.35))
    code_card(st, t, WHAT_CODE, 560, 52, 80)
    # beads on a thread (characters ki maala)
    if t >= BEADS_T:
        q = ease((t - BEADS_T) / 0.4)
        lay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay)
        pts = [(x, 940 + 40 * math.sin((x - 90) / 900 * math.pi)) for x in np.linspace(90, 90 + 900 * q, 40)]
        d.line(pts, fill=(255, 255, 255, 230), width=5)
        st.alpha_composite(glow(lay, 6, 0.8, (200, 220, 255)))
        for k, ch in enumerate("Python"):
            x = 160 + 150 * k
            y = 940 + 40 * math.sin((x - 90) / 900 * math.pi)
            paste(st, tile(ch, [YEL, CYAN, GREEN, ORANGE, (255, 105, 190), RED][k], 110, 120), x, y,
                  pop(t - BEADS_T - 0.25 - 0.12 * k, 0.3))
            if t >= IDX_T + 0.1 * k:
                paste(st, b.big_num(str(k), (150, 180, 230), 46), x, y + 110, pop(t - IDX_T - 0.1 * k, 0.25))
    b.caption(st, t, IDX_T + 0.8, [("String = ", WHITE), ("characters ki maala!", YEL)], 470, 1170, 56)
    if t >= QUOTE_T:
        paste(st, word_chip("'chai'", GREEN, 52), 280, 1320, pop(t - QUOTE_T, 0.3))
        paste(st, word_chip('"chai"', GREEN, 52), 620, 1320, pop(t - QUOTE_T - 0.2, 0.3))
        b.caption(st, t, QUOTE_T + 0.6, [("Dono quotes chalte hain!", (200, 215, 240))], 450, 1440, 46)


SLIDES = {
    "s1": dict(t=13.0, tag="CLEAN UP", title=".strip()", n=1, code=[(14.0, 'naam = "  Rohan  "'),
              (15.0, "print(naam.strip())"), (16.1, '# "Rohan"')], vis=vis_strip, go=17.0,
              cap=[("Aage-peeche ke ", WHITE), ("spaces", YEL), (" saaf!", WHITE)], cap_t=18.0),
    "s2": dict(t=20.0, tag="CAPS", title=".upper()", n=2, code=[(21.0, 'dish = "chai"'),
              (21.8, "print(dish.upper())"), (22.8, '# "CHAI"')], vis=vis_upper, go=23.4,
              cap=[(".lower()", CYAN), (" = sab chhote!", WHITE)], cap_t=24.6),
    "s3": dict(t=26.5, tag="REPLACE", title=".replace()", n=3, code=[(27.5, 's = "chai garam hai"'),
              (28.4, 'print(s.replace("chai", "coffee"))'), (29.7, '# "coffee garam hai"')], vis=vis_replace,
              go=30.3, cap=[("Ek word ", WHITE), ("badlo", YEL), (", baaki same!", WHITE)], cap_t=31.2, size=42),
    "s4": dict(t=33.0, tag="SPLIT", title=".split()", n=4, code=[(34.0, 'fruits = "aam,kela,seb"'),
              (34.9, 'print(fruits.split(","))'), (36.0, "# ['aam', 'kela', 'seb']")], vis=vis_split, go=36.6,
              cap=[("Text ", WHITE), ("→ list", YEL), (" ban gayi!", WHITE)], cap_t=37.6),
    "s5": dict(t=39.5, tag="JOIN", title=".join()", n=5, code=[(40.5, 'd = ["24", "10", "2026"]'),
              (41.4, 'print("-".join(d))'), (42.4, '# "24-10-2026"')], vis=vis_join, go=43.0,
              cap=[("List ", WHITE), ("→ ek string", YEL), ("!", WHITE)], cap_t=44.0),
}


def draw_slide(st, t, name):
    s = SLIDES[name]
    slide_head(st, t, s["t"] + 0.1, s["tag"], s["title"], s["n"])
    code_card(st, t, s["code"], 640, s.get("size", 48), 80)
    s["vis"](st, t, s["code"][-1][0] - 0.2, s["go"])
    b.caption(st, t, s["cap_t"], s["cap"], 440, 1300, 54)


CHEAT = [(46.9, '"  hi  ".strip()    --> "hi"'), (47.3, '"chai".upper()      --> "CHAI"'),
         (47.7, '"CHAI".lower()      --> "chai"'), (48.1, '"tea".replace("t","p") --> "pea"'),
         (48.5, '"a,b".split(",")    --> [\'a\', \'b\']'), (48.9, '"-".join(["a","b"]) --> "a-b"')]
SAVE_T = 49.6


def draw_cheat(st, t):
    paste(st, multi_title(), 540, 380, 0.6 * pop(t - 46.1, 0.35))
    x0, y0, y1 = 50, 600, 600 + 80 + len(CHEAT) * 72
    q = ease((t - 46.5) / 0.3)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, 1030, y1), 22, fill=(14, 16, 22, int(235 * q)), outline=(70, 75, 90, int(200 * q)),
                        width=3)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((80 + 34 * k, y0 + 24, 100 + 34 * k, y0 + 44), fill=c + (int(255 * q),))
    st.alpha_composite(lay)
    f, fn = mb.font(MONO, 34), mb.font(bs.MONO_R, 30)
    for k, (ts, txt) in enumerate(CHEAT):
        if t < ts:
            continue
        y = y0 + 80 + k * 72 + 30
        im = Image.new("RGBA", (980, 72))
        dd = ImageDraw.Draw(im)
        dd.text((30, 36), str(k + 1), font=fn, fill=(110, 115, 130), anchor="mm")
        code, res = txt.split("-->")
        dd.text((70, 36), code.rstrip(), font=f, fill=(240, 220, 120), anchor="lm")
        dd.text((70 + f.getlength(code), 36), "-->", font=f, fill=(170, 175, 190), anchor="lm")
        dd.text((70 + f.getlength(code + "--> "), 36), res.strip(), font=f, fill=WHITE, anchor="lm")
        paste(st, im, x0 + 490 + 60 * (1 - ease((t - ts) / 0.25)), y, 1, ease((t - ts) / 0.2))
    p11.stamp(st, t, SAVE_T, "SAVE KAR LO!", 400, 1360, 80, YEL, -5)


TRK = [(52.2, 's = "  py-thon  "'), (52.9, "s = s.strip()"), (53.5, 's = s.replace("-", "")'),
       (54.3, "print(s.upper())")]
OPTIONS = [(55.0, "A", "PYTHON"), (55.3, "B", "PY-THON"), (55.6, "C", '"  PYTHON  "')]
ANSWER = "A"
COUNT0, REVEAL = 56.0, 59.0


def draw_tricky(st, t):
    paste(st, e13.comic("TRICKY SAWAAL!", e13.PINK, 104), 540, 330, pop(t - 51.2, 0.3), 1, -2)
    code_card(st, t, TRK, 450, 44, 70)
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, e13.option_card(letter, txt, state), 400, 1010 + k * 140, sc,
              1 if (t < REVEAL or letter == ANSWER) else 0.55)
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (200 * S, 200 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 190 * S, 190 * S), fill=(8, 14, 40, 230), outline=(60, 70, 110), width=12 * S)
        d.arc((10 * S, 10 * S, 190 * S, 190 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)), fill=YEL,
              width=12 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((100 * S, 104 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 100 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        paste(st, im.resize((200, 200), Image.LANCZOS), 900, 1010, 1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8))
    if t >= REVEAL + 0.4:
        b.caption(st, t, REVEAL + 0.4, [("strip → replace → ", WHITE), ("upper", YEL)], 440, 1480, 48)
    elif t >= COUNT0 + 0.2:
        b.caption(st, t, COUNT0 + 0.2, [("Comment karo!", YEL)], 400, 1480, 54)


def draw_any(st, t, name):
    if name in SLIDES:
        draw_slide(st, t, name)
    else:
        {"hook": draw_hook, "what": draw_what, "cheat": draw_cheat, "tricky": draw_tricky}[name](st, t)


p11.MASCOT_IN = {"what": 6.6, "s1": 17.2, "s2": 23.6, "s3": 30.5, "s4": 36.8, "s5": 43.2, "cheat": 49.0,
                 "tricky": 56.3}
p11.REACT = [(IDX_T + 0.2, "Ginti 0 se!", GREEN), (17.5, "Saaf-suthra!", GREEN), (24.0, "CHAI!", GREEN),
             (30.7, "Coffee time!", GREEN), (37.0, "3 tukde!", GREEN), (43.5, "Jud gaye!", GREEN),
             (SAVE_T + 0.1, "Screenshot lo!", GREEN), (REVEAL + 0.05, "PYTHON!", GREEN)]


# ------------------------------------------------------------------ frame (carousel swipe between slides)
def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return k, SCENES[k]


_FROZEN = {}


def end_frame(t):
    if not e13._end_ready:
        es.static_layer = lambda: Image.new("RGBA", (W, H))
        es.mb.wood_frame = lambda *a, **k: None
        e13._end_ready.append(1)
    fr = bg14(END0 + t)
    fr.alpha_composite(es.frame(t))
    return fr


def frame(i, t=None):
    t = i / FPS if t is None else t
    if t >= END0:
        fr = end_frame(t - END0)
    else:
        k, (s0, name) = scene_at(t)
        a = t - s0
        fr = bg14(t)
        st = Image.new("RGBA", (W, H))
        draw_any(st, t, name)
        if k > 0 and a < SWIPE:        # carousel swipe: old slide pushes out left, new one slides in from right
            q = ease(a / SWIPE)
            key = SCENES[k - 1][1]
            if key not in _FROZEN:
                old = Image.new("RGBA", (W, H))
                draw_any(old, s0 - 0.001, key)
                _FROZEN[key] = old
            old = _FROZEN[key]
            dx = int(W * q)
            blur = old.filter(ImageFilter.BoxBlur(int(10 * math.sin(math.pi * q)))) if 0 < q < 1 else old
            fr.alpha_composite(blur.crop((dx, 0, W, H)), (0, 0)) if dx < W else None
            new = st.filter(ImageFilter.BoxBlur(int(10 * math.sin(math.pi * q)))) if q < 1 else st
            if dx > 0:
                fr.alpha_composite(new.crop((0, 0, dx, H)), (W - dx, 0))
        else:
            fr.alpha_composite(st)
            p11.draw_mascot(fr, t, name)
    fr.alpha_composite(p11.handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    for tp, amt in ((1.0, 0.04), (REVEAL, 0.05)):
        e_ = t - tp
        if 0 <= e_ < 0.4:
            z = 1 + amt * math.exp(-e_ * 9)
            arr = cv2.warpAffine(arr, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for ts, amp in ((REVEAL, 6), (36.6, 8)):
        e_ = t - ts
        if 0 <= e_ < 0.35:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.35)), axis=1)
    for tf in (3.8, 46.0, 51.0, REVEAL, END0):
        e_ = t - tf
        if 0 <= e_ < 0.15:
            arr += (255 - arr) * 0.25 * (1 - e_ / 0.15)
    arr *= m.vignette()
    arr += cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.6
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
type_clicks, e_chime, swipe = p11.type_clicks, p11.e_chime, b.swipe


def zip_sfx():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    teeth = (np.sin(2 * np.pi * (60 + 500 * tt / 0.45) * tt * 10) > 0.6).astype(float)
    return fx.filt(fx.noise(n, 3) * teeth, "bandpass", [1500, 7000]) * 0.5


def flip_click(k):
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (1200 + 200 * k) * tt) * np.exp(-tt * 70) * 0.4


def snap():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    return (fx.noise(n, 9) * np.exp(-tt * 40) * 0.7 + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 25) * 0.4)


def clack():
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 900 * tt) + 0.5 * np.sin(2 * np.pi * 2300 * tt)) * np.exp(-tt * 50) * 0.35


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.boom(), 0.1, 0.7)
    P(buf, fx.whoosh(0.4, 1), 0.0, 0.5)
    P(buf, swipe(2), 1.0, 0.5)
    for k, (t0, *_r) in enumerate(HOOK_CHIPS):
        P(buf, fx.pop(), t0, 0.4)
        P(buf, bs.note_pop(660 + 110 * k), t0, 0.25)
    P(buf, fx.pop(), 2.3, 0.4)
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.4, int(s0 * 5)), s0 - 0.05, 0.6)
        P(buf, swipe(int(s0 * 7)), s0, 0.4)
    # what
    P(buf, fx.pop(), 3.95, 0.5)
    type_clicks(buf, WHAT_CODE[0][0], len(WHAT_CODE[0][1]), 28, 50, 0.24)
    for k in range(6):
        P(buf, bs.note_pop(523.3 * 2 ** (k * 2 / 12)), BEADS_T + 0.25 + 0.12 * k, 0.35)
    for k in range(6):
        P(buf, fx.pop(), IDX_T + 0.1 * k, 0.25)
    P(buf, fx.pop(), QUOTE_T, 0.45)
    P(buf, fx.pop(), QUOTE_T + 0.2, 0.45)
    # slides
    for name, s in SLIDES.items():
        P(buf, fx.pop(), s["t"] + 0.25, 0.5)
        P(buf, swipe(int(s["t"] * 3)), s["t"] + 0.55, 0.4)
        for ts, txt in s["code"]:
            if txt.startswith("#"):
                P(buf, fx.pop(), ts, 0.45)
                P(buf, bs.note_pop(1046.5), ts, 0.3)
            else:
                type_clicks(buf, ts, len(txt), 28, int(ts * 31), 0.22)
        P(buf, fx.pop(), s["cap_t"], 0.3)
    P(buf, zip_sfx(), SLIDES["s1"]["go"], 0.9)
    P(buf, fx.ding(), SLIDES["s1"]["go"] + 0.5, 0.4)
    for k in range(4):
        P(buf, flip_click(k), SLIDES["s2"]["go"] + 0.15 * k + 0.12, 0.8)
    P(buf, fx.ding(), SLIDES["s2"]["go"] + 0.75, 0.4)
    P(buf, fx.whoosh(0.3, 33), SLIDES["s3"]["go"], 0.5)
    P(buf, e_chime(), SLIDES["s3"]["go"] + 0.35, 0.5)
    P(buf, snap(), SLIDES["s4"]["go"], 0.9)
    P(buf, fx.boom()[: int(0.4 * SR)], SLIDES["s4"]["go"], 0.4)
    P(buf, fx.whoosh(0.3, 44), SLIDES["s5"]["go"], 0.4)
    P(buf, clack(), SLIDES["s5"]["go"] + 0.42, 0.9)
    P(buf, clack(), SLIDES["s5"]["go"] + 0.5, 0.7)
    P(buf, fx.ding(), SLIDES["s5"]["go"] + 0.6, 0.4)
    # cheat sheet
    P(buf, fx.boom()[: int(0.4 * SR)], 46.1, 0.5)
    for k, (ts, _txt) in enumerate(CHEAT):
        P(buf, swipe(int(ts * 11)), ts, 0.4)
        P(buf, bs.note_pop(587.3 * 2 ** (k * 2 / 12)), ts, 0.25)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.45)
    # tricky
    P(buf, fx.riser(0.6), 50.6, 0.35)
    P(buf, fx.boom(), 51.2, 0.7)
    for ts, txt in TRK:
        type_clicks(buf, ts, len(txt), 28, int(ts * 13), 0.22)
    for t0, *_r in OPTIONS:
        P(buf, fx.pop(), t0, 0.55)
    tt = COUNT0
    while tt < REVEAL - 0.05:
        n2 = int(0.05 * SR)
        x = np.arange(n2) / SR
        P(buf, np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 90) * 0.5, tt, 0.6)
        tt += 0.5
    P(buf, fx.ding(), REVEAL, 0.7)
    P(buf, e_chime(), REVEAL + 0.05, 0.6)
    for tr, txt, col in p11.REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=46.0)
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


m.OUT, m.WORK, m.TOTAL, m.END0 = OUT, WORK, TOTAL, END0
m.frame, m.build_audio = frame, build_audio

if __name__ == "__main__":
    m.main()
