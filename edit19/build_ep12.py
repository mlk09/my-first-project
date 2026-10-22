#!/usr/bin/env python3
"""Python ki Pathshala EP 12 - for loop + range()  (1080x1920 Short, works without a voice-over)

Decoded from two "Python for loop" shorts:
  forloop2 (@Time-To-Program): deep NAVY gradient, clean white sans title ("For Loop / Python") at the top,
    code TYPED character by character with a blinking cursor (orange for/in, magenta range/print), then the
    output numbers appear one by one, big and centred; the title GLIDES to the centre and back between parts.
  forloop1 (@CodewithPatel): CRUMPLED WHITE PAPER background, chunky GREEN title with a black outline +
    "Tricky Question" in outlined white, a VS Code window, and a white UNDERLINE BAR that slides under the
    token being talked about. Facecam, voice, faint bed, no cuts.
Ours: navy + glide + live typing for the basics, the paper "tricky sawaal" look for the quiz, original
Hinglish content (chai-poha-vada menu, range start/stop, number-line hops, step), plus on-screen FX
(bokeh, light sweeps, sparkles, hop trails, zoom punches, shakes, paper slide-in) and full SFX.

Usage:  python3 edit19/build_ep12.py [--preview]
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
sys.path.insert(0, os.path.join(HERE, "..", "edit18"))
import build_ep11 as p11   # noqa: E402  EP 11: glow/stamp/pill helpers, mascot, (EP 08 encoder via p11.m)

m = p11.m
fx, bs, mb, es = m.fx, m.bs, m.mb, m.es
clamp, ease, pop, paste, glow = m.clamp, m.ease, m.pop, m.paste, p11.glow
W, H, FPS, SR = m.W, m.H, m.FPS, m.SR
es.NEXT = "EP 13: BREAK & CONTINUE"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
MONO = bs.MONO

WHITE, YEL, GREEN, RED, NAVY = (255, 255, 255), (255, 214, 10), (40, 210, 110), (245, 60, 75), (8, 18, 58)
ORANGE, MAGENTA, LBLUE, STRG = (255, 145, 45), (235, 70, 235), (150, 205, 255), (130, 225, 130)

SCENES = [(0.0, "hook"), (3.6, "menu"), (14.0, "range"), (28.0, "steps"), (39.5, "tricky")]
END0 = 51.5
TOTAL = END0 + es.DUR
GLIDE = 0.9
PAPER_IN = 0.6
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP12_For_Loop.mp4")
WORK = os.path.join(HERE, "work")
_C = {}


def inter(size, w="SemiBold"):
    return mb.font(INTER.format(w), size)


# ------------------------------------------------------------------ backgrounds
@lru_cache(None)
def navy_base():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .42) / (H * .8)) ** 2)
    q = np.clip(r * 1.25, 0, 1)[..., None]
    return np.array([14, 44, 82], np.float32) * (1 - q) + np.array([1, 13, 30], np.float32) * q


@lru_cache(None)
def bokeh_sprite(r):
    s = int(r * 2 + 4)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 1.6
    im = np.zeros((s, s, 4), np.uint8)
    im[..., :3] = (120, 180, 255)
    im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im)


def navy_bg(t):
    a = navy_base().copy()
    # slow diagonal light sweep every 7 s
    ph = (t % 7.0) / 7.0
    yy, xx = np.mgrid[0:H:8, 0:W:8].astype(np.float32)
    band = np.exp(-(((xx + yy * 0.5) - (ph * 2600 - 600)) / 160.0) ** 2) * 14
    a += cv2.resize(band, (W, H))[..., None] * np.array([0.6, 0.8, 1.0], np.float32)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(12)
    for _ in range(22):
        x0, y0, sp, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(10, 35), rng.uniform(10, 34)
        al = rng.uniform(0.08, 0.22) * (0.7 + 0.3 * math.sin(t * rng.uniform(0.8, 2) + x0))
        y = (y0 - t * sp) % (H + 100) - 50
        x = x0 + 30 * math.sin(t * 0.4 + y0)
        paste(img, bokeh_sprite(int(r)), x, y, 1, al)
    return img


@lru_cache(None)
def paper_tex():
    """procedural crumpled white paper: faceted shading + darker creases + fine fibre noise"""
    lw, lh = 270, 480
    rng = np.random.default_rng(7)
    seeds = rng.uniform(0, 1, (140, 2)) * (lw, lh)
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    d = np.stack([(xx - sx) ** 2 + (yy - sy) ** 2 for sx, sy in seeds])
    lab = d.argmin(0)
    shade = rng.uniform(0.955, 1.0, len(seeds))[lab]
    grad = np.zeros_like(shade)
    tilt = rng.normal(0, 1, (len(seeds), 2))
    grad += (tilt[lab, 0] * (xx - seeds[lab, 0]) + tilt[lab, 1] * (yy - seeds[lab, 1])) * 0.0005
    edge = (np.diff(lab, axis=0, prepend=lab[:1]) != 0) | (np.diff(lab, axis=1, prepend=lab[:, :1]) != 0)
    s = shade + grad - edge * 0.03
    s = cv2.resize(s.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    s = cv2.GaussianBlur(s, (0, 0), 2.4)
    s += np.random.default_rng(8).normal(0, 0.012, (H, W)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.07 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 4
    img = np.clip(s * vig, 0, 1.05)[..., None] * np.array([246, 246, 244], np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


# ------------------------------------------------------------------ text pieces
def header_img(scale):
    key = ("hdr", round(scale, 2))
    if key not in _C:
        f1, f2 = inter(int(92 * scale), "SemiBold"), inter(int(70 * scale), "Medium")
        w = int(max(f1.getlength("for loop"), f2.getlength("+ range()")) + 60)
        im = Image.new("RGBA", (w, int(200 * scale) + 40))
        d = ImageDraw.Draw(im)
        d.text((w / 2, 20 + 50 * scale), "for loop", font=f1, fill=WHITE, anchor="mm")
        x = w / 2 - f2.getlength("+ range()") / 2
        d.text((x, 20 + 150 * scale), "+ ", font=f2, fill=WHITE, anchor="lm")
        d.text((x + f2.getlength("+ "), 20 + 150 * scale), "range()", font=f2, fill=MAGENTA, anchor="lm")
        _C[key] = glow(im, int(10 * scale), 0.5, (120, 170, 255))
        if len(_C) > 400:
            _C.clear()
    return _C[key]


def sweep(im, t, t0, dur=0.6):
    """light shimmer passing across a text image (special effect)"""
    a = (t - t0) / dur
    if not 0 <= a <= 1:
        return im
    w, h = im.size
    xx = np.arange(w, dtype=np.float32)[None, :]
    yy = np.arange(h, dtype=np.float32)[:, None]
    band = np.exp(-(((xx + yy * 0.4) - (a * (w + h) - h * 0.2)) / 40.0) ** 2)
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] += band[..., None] * 160 * (arr[..., 3:4] / 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


PAL_NAVY = {"kw": ORANGE, "fn": MAGENTA, "num": WHITE, "str": STRG, "id": WHITE, "pun": WHITE}
PAL_VS = {"kw": (197, 134, 192), "fn": (220, 220, 170), "num": (181, 206, 168), "str": (206, 145, 120),
          "id": (156, 220, 254), "pun": (212, 212, 212)}


def tok_colours(line, pal):
    cols, i = [], 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            j = line.find('"', i + 1)
            j = len(line) if j < 0 else j + 1
            cols += [pal["str"]] * (j - i)
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            wd = line[i:j]
            cols += [pal["kw"] if wd in ("for", "in") else pal["fn"] if wd in ("range", "print") else pal["id"]] * (j - i)
            i = j
        elif ch.isdigit():
            cols.append(pal["num"])
            i += 1
        else:
            cols.append(pal["pun"])
            i += 1
    return cols


def typed(st, t, t0, text, x, y, size, cps=24, pal=PAL_NAVY, cursor=True, nxt=None):
    """ref-2 typing: character by character, blinking cursor; returns list of char x positions"""
    f = mb.font(MONO, size)
    xs, cx = [], x
    for ch in text:
        xs.append(cx)
        cx += f.getlength(ch)
    xs.append(cx)
    if t < t0:
        return xs
    n = min(len(text), int((t - t0) * cps) + 1)
    d = ImageDraw.Draw(st)
    cols = tok_colours(text, pal)
    for k in range(n):
        d.text((xs[k], y), text[k], font=f, fill=cols[k], anchor="lm")
    done = n >= len(text)
    show = cursor and (not done or (nxt is None or t < nxt)) and (not done or int(t * 2.4) % 2 == 0)
    if show:
        cx = xs[n]
        lay = Image.new("RGBA", (40, int(size * 1.3)))
        ImageDraw.Draw(lay).rectangle((16, 4, 21, lay.height - 4), fill=WHITE)
        paste(st, glow(lay, 6, 1.0, (160, 200, 255)), cx + 2, y)
    return xs


def caption(st, t, t0, parts, cx, cy, size=58, w="Bold"):
    """clean white sans caption that rises + fades in, with a highlight word colour"""
    a = t - t0
    if a < 0:
        return
    f = inter(size, w)
    tw = sum(f.getlength(s) for s, _ in parts)
    im = Image.new("RGBA", (int(tw) + 60, int(size * 1.6)))
    d = ImageDraw.Draw(im)
    x = 30
    for s, c in parts:
        d.text((x, im.height / 2), s, font=f, fill=c, anchor="lm")
        x += f.getlength(s)
    im = glow(im, 8, 0.6, (60, 100, 200))
    paste(st, im, cx, cy + 30 * (1 - ease(a / 0.35)), 1, ease(a / 0.3))


def big_num(txt, col=LBLUE, size=96):
    key = ("num", txt, col, size)
    if key not in _C:
        f = mb.font(bs.MONO_R, size)
        w = int(f.getlength(txt)) + 60
        im = Image.new("RGBA", (w, int(size * 1.5)))
        ImageDraw.Draw(im).text((w / 2, im.height / 2), txt, font=f, fill=col, anchor="mm")
        _C[key] = glow(im, 10, 0.9, col)
    return _C[key]


def sparkle_burst(st, t, t0, cx, cy, n=10, col=YEL, rad=120):
    a = t - t0
    if not 0 <= a < 0.7:
        return
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    for k in range(n):
        ang = k * 2 * math.pi / n + t0
        r = rad * ease(a / 0.5)
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        s = 10 * (1 - a / 0.7)
        al = int(255 * (1 - a / 0.7))
        d.polygon([(x, y - s * 2), (x + s * 0.5, y), (x, y + s * 2), (x - s * 0.5, y)], fill=col + (al,))
        d.polygon([(x - s * 2, y), (x, y + s * 0.5), (x + s * 2, y), (x, y - s * 0.5)], fill=col + (al,))
    st.alpha_composite(glow(lay, 6, 1.0, col))


def underline(st, t, marks, y, col=WHITE, h=10):
    """ref-1 white underline bar that slides from token to token. marks = [(t, x0, x1)]"""
    if not marks or t < marks[0][0]:
        return
    cur = marks[0]
    x0, x1 = cur[1], cur[2]
    for k in range(1, len(marks)):
        ts, a0, a1 = marks[k]
        if t >= ts:
            q = ease((t - ts) / 0.28)
            px0, px1 = marks[k - 1][1], marks[k - 1][2]
            x0, x1 = px0 + (a0 - px0) * q, px1 + (a1 - px1) * q
    grow = ease((t - marks[0][0]) / 0.25)
    mid = (x0 + x1) / 2
    x0, x1 = mid - (mid - x0) * grow, mid + (x1 - mid) * grow
    lay = Image.new("RGBA", (W, H))
    ImageDraw.Draw(lay).rounded_rectangle((x0 - 4, y, x1 + 4, y + h), h // 2, fill=col + (255,))
    st.alpha_composite(glow(lay, 8, 1.0, col))


def hop_line(st, t, t0, y, lo, hi, hits, x0=110, x1=970, col=YEL, crossed=None, lc=(200, 215, 240)):
    """number line lo..hi-1 with a glowing ball hopping across the hit values (special effect)"""
    a = t - t0
    if a < 0:
        return
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    n = hi - lo
    step = (x1 - x0) / max(1, n - 1)
    q = ease(a / 0.3)
    d.line((x0 - 20, y, x0 - 20 + (x1 - x0 + 40) * q, y), fill=lc + (255,), width=5)
    fnt = mb.font(bs.MONO_R, 40)
    for k in range(n):
        xx = x0 + k * step
        d.line((xx, y - 14, xx, y + 14), fill=lc + (int(255 * q),), width=4)
        d.text((xx, y + 48), str(lo + k), font=fnt, fill=lc + (int(255 * q),), anchor="mm")
    st.alpha_composite(lay)
    # hops
    hop = 0.45
    for j, (th, v) in enumerate(hits):
        if t < th:
            break
        xx = x0 + (v - lo) * step
        dot = Image.new("RGBA", (70, 70))
        ImageDraw.Draw(dot).ellipse((15, 15, 55, 55), fill=col)
        paste(st, glow(dot, 10, 1.4, col), xx, y, pop(t - th, 0.25))
        paste(st, big_num(str(v), col, 64), xx, y - 80, pop(t - th, 0.25))
        if j + 1 < len(hits) and hits[j + 1][0] - hop <= t < hits[j + 1][0]:
            nx = x0 + (hits[j + 1][1] - lo) * step
            p = (t - (hits[j + 1][0] - hop)) / hop
            bx = xx + (nx - xx) * p
            by = y - 150 * math.sin(math.pi * p)
            trail = Image.new("RGBA", (W, H))
            td = ImageDraw.Draw(trail)
            pts = [(xx + (nx - xx) * u, y - 150 * math.sin(math.pi * u)) for u in np.linspace(0, p, 20)]
            td.line(pts, fill=col + (200,), width=6)
            td.ellipse((bx - 16, by - 16, bx + 16, by + 16), fill=col)
            st.alpha_composite(glow(trail, 8, 1.2, col))
    if crossed and t >= crossed[0]:
        xx = x1 + step * 0.8
        paste(st, big_num(str(crossed[1]), RED, 64), xx, y - 80, pop(t - crossed[0], 0.25))
        q2 = ease((t - crossed[0] - 0.2) / 0.25)
        dd = ImageDraw.Draw(st)
        dd.line((xx - 40, y - 120, xx - 40 + 80 * q2, y - 40), fill=RED, width=8)


def menu_card(txt, active):
    key = ("menu", txt, active)
    if key not in _C:
        im = Image.new("RGBA", (300, 170))
        d = ImageDraw.Draw(im)
        col = YEL if active else (90, 130, 200)
        d.rounded_rectangle((20, 20, 280, 150), 26, fill=(10, 30, 70, 235), outline=col, width=6)
        d.text((150, 86), txt, font=inter(52, "Bold"), fill=WHITE, anchor="mm")
        _C[key] = glow(im, 12, 1.2 if active else 0.5, col)
    return _C[key]


# ------------------------------------------------------------------ scenes (navy)
HOOK_COUNT = 1.5


def draw_hook(st, t):
    a = t
    im = sweep(header_img(2.0), t, 1.0, 0.7)
    paste(st, im, 540, 640 - 260 * (1 - ease(a / 0.45)), 0.8 + 0.2 * ease(a / 0.45), ease(a / 0.3))
    caption(st, t, 0.9, [("1 se 10 tak ginti,", WHITE)], 540, 920, 64)
    caption(st, t, 1.2, [("sirf ", WHITE), ("2 lines", YEL), (" mein!", WHITE)], 540, 1010, 64)
    if t >= HOOK_COUNT:
        n = min(10, int((t - HOOK_COUNT) * 7) + 1)
        k_t = HOOK_COUNT + (n - 1) / 7
        paste(st, big_num(str(n), YEL, 190), 330, 1300, 1 + 0.25 * math.exp(-(t - k_t) * 12))
        sparkle_burst(st, t, HOOK_COUNT + 9 / 7, 330, 1300, 12, YEL, 170)
    if "m430" not in _C:
        _C["m430"] = mb.mascot(430)
    paste(st, _C["m430"], 820, 1400, pop(t - 1.4, 0.4))


MENU_CODE = [(4.3, 'menu = ["chai", "poha", "vada"]'), (5.6, "for item in menu:"), (6.4, "    print(item)")]
MENU_ITEMS = ["chai", "poha", "vada"]
CARD_T = [7.3, 7.5, 7.7]
ITER_M = [8.2, 9.3, 10.4]


def draw_menu(st, t):
    for k, (ts, txt) in enumerate(MENU_CODE):
        nxt = MENU_CODE[k + 1][0] if k + 1 < len(MENU_CODE) else 7.2
        typed(st, t, ts, txt, 90, 520 + k * 78, 46, 28, nxt=nxt)
    cur = None
    for k, ts in enumerate(ITER_M):
        if t >= ts:
            cur = k
    for k, (ts, txt) in enumerate(zip(CARD_T, MENU_ITEMS)):
        if t >= ts:
            sc = pop(t - ts, 0.3) * (1.08 if cur == k else 1.0)
            paste(st, menu_card(txt, cur == k), 210 + 330 * k, 860 + (-14 if cur == k else 0), sc)
    if cur is not None:
        ts = ITER_M[cur]
        p11.pill(st, t, ts, f'item = "{MENU_ITEMS[cur]}"', (130, 60, 230), 540, 1010, 40)
        sparkle_burst(st, t, ts, 210 + 330 * cur, 860, 8, YEL, 120)
    for k, ts in enumerate(ITER_M):
        if t >= ts + 0.3:
            paste(st, big_num(MENU_ITEMS[k], LBLUE, 76), 540, 1110 + k * 90, pop(t - ts - 0.3, 0.25))
    caption(st, t, 11.6, [("Har item ke liye loop ", WHITE), ("EK", YEL), (" baar!", WHITE)], 450, 1440, 52)


R_LINE1, R_LINE2 = "for i in range(1, 6):", "    print(i)"
R_T1, R_T2 = 14.9, 15.85
R_X, R_Y1, R_Y2, R_SIZE = 110, 560, 650, 64
UL_START, UL_STOP = 17.0, 18.3
RUN_T = 19.6
OUT_R = [20.0 + 0.55 * k for k in range(5)]
SIX_T = 22.9
RULE_T = 24.3


def draw_range(st, t):
    xs = typed(st, t, R_T1, R_LINE1, R_X, R_Y1, R_SIZE, 26, nxt=R_T2)
    typed(st, t, R_T2, R_LINE2, R_X, R_Y2, R_SIZE, 26, nxt=RUN_T)
    i1, i6 = R_LINE1.index("1"), R_LINE1.index("6")
    underline(st, t, [(UL_START, xs[i1], xs[i1 + 1]), (UL_STOP, xs[i6], xs[i6 + 1])], R_Y1 + 40)
    if t >= UL_START + 0.2:
        p11.pill(st, t, UL_START + 0.2, "start", (25, 160, 85), xs[i1] - 30, R_Y1 - 90, 36)
    if t >= UL_STOP + 0.2:
        p11.pill(st, t, UL_STOP + 0.2, "stop", (220, 45, 60), xs[i6] + 70, R_Y1 - 90, 36)
    cur = None
    for k, ts in enumerate(OUT_R):
        if t >= ts:
            cur = k
            paste(st, big_num(str(k + 1)), 540, 840 + k * 105, pop(t - ts, 0.25))
            sparkle_burst(st, t, ts, 540, 840 + k * 105, 8, LBLUE, 90)
    if cur is not None and t < SIX_T:
        p11.pill(st, t, OUT_R[0], f"i = {cur + 1}", (130, 60, 230), 860, 840 + cur * 105, 40)
    if t >= SIX_T:
        paste(st, big_num("6?", RED, 96), 540, 840 + 5 * 105, pop(t - SIX_T, 0.25))
        q = ease((t - SIX_T - 0.25) / 0.25)
        d = ImageDraw.Draw(st)
        d.line((470, 840 + 5 * 105 - 50, 470 + 140 * q, 840 + 5 * 105 + 50 * (2 * q - 1)), fill=RED, width=10)
    if t >= RULE_T:
        p11.type_box(st, t, RULE_T, ((("range(1, 6)", (120, 230, 255)), (" = 1 se 5", WHITE)),
                                     (("Last number ", WHITE), ("shamil NAHI!", YEL))), 420, 1500, "navy", 46, 34)


S_A_T, S_B_T = 28.9, 32.6
HITS_A = [(29.9 + 0.55 * k, k) for k in range(5)]
HITS_B = [(33.7 + 0.6 * k, 2 * k) for k in range(5)]
SAVE_T = 36.9


def draw_steps(st, t):
    typed(st, t, S_A_T, "for i in range(5):", 110, 520, 58, 26, nxt=S_B_T)
    caption(st, t, S_A_T + 0.75, [("0 se shuru", YEL), (", 5 tak nahi", WHITE)], 540, 610, 48)
    hop_line(st, t, S_A_T + 0.6, 800, 0, 6, HITS_A, 150, 930, LBLUE)
    typed(st, t, S_B_T, "for i in range(0, 10, 2):", 80, 1010, 54, 28, nxt=SAVE_T + 2)
    caption(st, t, S_B_T + 0.95, [("step = 2", YEL), (" ka jump!", WHITE)], 540, 1100, 48)
    hop_line(st, t, S_B_T + 0.8, 1290, 0, 10, HITS_B, 110, 970, YEL)
    p11.stamp(st, t, SAVE_T, "SAVE KAR LO!", 380, 1500, 74, YEL, -5)


# ------------------------------------------------------------------ tricky (paper, ref-1 look)
TRICK = "for i in range(2, 10, 3):"
TRICK2 = "    print(i)"
TK_T1, TK_T2 = 40.8, 41.8
UL_TK = [(42.5, "2"), (43.2, "10"), (43.9, "3")]
OPTIONS = [(44.6, "A", "2 5 8"), (44.9, "B", "2 5 8 11"), (45.2, "C", "3 6 9")]
ANSWER = "A"
COUNT0, REVEAL = 45.6, 48.6
HITS_T = [(49.0 + 0.5 * k, v) for k, v in enumerate((2, 5, 8))]


@lru_cache(None)
def green_title():
    f = mb.font(mb.BALOO, 120, "ExtraBold")
    txt = "for loop....."
    w = int(f.getlength(txt)) + 80
    im = Image.new("RGBA", (w, 190))
    d = ImageDraw.Draw(im)
    d.text((w / 2 + 8, 103), txt, font=f, fill=(0, 0, 0, 120), anchor="mm", stroke_width=12, stroke_fill=(0, 0, 0, 120))
    d.text((w / 2, 95), txt, font=f, fill=(46, 220, 70), anchor="mm", stroke_width=11, stroke_fill=(12, 14, 12))
    return im


@lru_cache(None)
def white_title():
    f = mb.font(mb.BALOO, 96, "ExtraBold")
    txt = "TRICKY SAWAAL!"
    w = int(f.getlength(txt)) + 80
    im = Image.new("RGBA", (w, 160))
    d = ImageDraw.Draw(im)
    d.text((w / 2 + 7, 87), txt, font=f, fill=(0, 0, 0, 110), anchor="mm", stroke_width=11, stroke_fill=(0, 0, 0, 110))
    d.text((w / 2, 80), txt, font=f, fill=WHITE, anchor="mm", stroke_width=10, stroke_fill=(12, 14, 12))
    return im


VS = (60, 590, 1020, 930)


def vscode(st, t, t0):
    a = t - t0
    if a < 0:
        return None
    x0, y0, x1, y1 = VS
    im = Image.new("RGBA", (x1 - x0 + 60, y1 - y0 + 60))
    d = ImageDraw.Draw(im)
    X0, Y0, X1, Y1 = 30, 30, im.width - 30, im.height - 30
    d.rounded_rectangle((X0 + 6, Y0 + 12, X1 + 6, Y1 + 12), 30, fill=(0, 0, 0, 90))
    d.rounded_rectangle((X0, Y0, X1, Y1), 30, fill=(24, 24, 28))
    d.rectangle((X0, Y0 + 60, X0 + 70, Y1 - 30), fill=(30, 30, 36))
    lx, ly = X0 + 34, Y0 + 32
    d.polygon([(lx - 14, ly - 4), (lx + 6, ly - 16), (lx + 14, ly - 12), (lx + 14, ly + 12), (lx + 6, ly + 16),
               (lx - 14, ly + 4)], fill=(40, 140, 240))
    fm = inter(26, "Medium")
    x = X0 + 80
    for wd in ("File", "Edit", "Selection", "View", "Go", "Run", "Terminal", "Help"):
        d.text((x, Y0 + 32), wd, font=fm, fill=(200, 200, 205), anchor="lm")
        x += fm.getlength(wd) + 26
    d.rectangle((X0 + 70, Y0 + 62, X0 + 330, Y0 + 116), fill=(30, 30, 36))
    d.text((X0 + 100, Y0 + 89), "pathshala.py  ×", font=inter(28, "Medium"), fill=(220, 220, 225), anchor="lm")
    ic = (120, 120, 130)
    for k in range(3):
        ix, iy = X0 + 35, Y0 + 150 + 62 * k
        if k == 0:
            d.rectangle((ix - 13, iy - 15, ix + 13, iy + 15), outline=ic, width=3)
        elif k == 1:
            d.ellipse((ix - 14, iy - 14, ix + 6, iy + 6), outline=ic, width=3)
            d.line((ix + 3, iy + 3, ix + 14, iy + 14), fill=ic, width=4)
        elif k == 2:
            d.polygon([(ix, iy - 15), (ix + 15, iy), (ix, iy + 15), (ix - 15, iy)], outline=ic, width=3)
        else:
            d.polygon([(ix - 10, iy - 14), (ix + 14, iy), (ix - 10, iy + 14)], outline=ic, width=3)
    fn = mb.font(bs.MONO_R, 34)
    for k in range(4):
        d.text((X0 + 130, Y0 + 170 + 66 * k), str(k + 1), font=fn, fill=(110, 115, 130), anchor="mm")
    paste(st, im, (x0 + x1) / 2, (y0 + y1) / 2 + 40 * (1 - ease(a / 0.35)), 1, ease(a / 0.3))
    return X0 + 190 + x0 - 30, Y0 + 170 + y0 - 30


def paper_option(letter, txt, state):
    key = ("popt", letter, txt, state)
    if key not in _C:
        im = Image.new("RGBA", (720, 150))
        d = ImageDraw.Draw(im)
        col = (20, 20, 24) if state is None else (30, 170, 70) if state else (170, 170, 175)
        d.rounded_rectangle((26, 30, 706, 136), 24, fill=(0, 0, 0, 70))
        d.rounded_rectangle((20, 20, 700, 126), 24, fill=WHITE, outline=col, width=6)
        d.ellipse((40, 36, 114, 110), fill=col if state is not False else (200, 200, 205))
        d.text((77, 73), letter, font=mb.font(mb.BALOO, 46, "ExtraBold"), fill=WHITE, anchor="mm")
        d.text((140, 74), txt, font=mb.font(MONO, 52), fill=(20, 22, 30) if state is not False else (150, 150, 155),
               anchor="lm")
        if state:
            d.line([(628, 74), (646, 94), (680, 52)], fill=(30, 170, 70), width=10, joint="curve")
        _C[key] = im
    return _C[key]


def draw_tricky(st, t):
    a = t - SCENES[4][0] - PAPER_IN
    paste(st, green_title(), 540, 330, pop(a, 0.35), 1, -2 * (1 - ease(a / 0.4)))
    paste(st, white_title(), 540, 470, pop(a - 0.3, 0.35), 1, 2 * (1 - ease((a - 0.3) / 0.4)))
    org = vscode(st, t, 40.4)
    if org:
        cx, cy = org
        xs = typed(st, t, TK_T1, TRICK, cx, cy, 48, 30, PAL_VS, nxt=TK_T2)
        typed(st, t, TK_T2, TRICK2, cx, cy + 66, 48, 30, PAL_VS, nxt=COUNT0)
        marks = []
        for ts, tok in UL_TK:
            i0 = TRICK.index(tok, TRICK.index("(") if tok != "3" else TRICK.rindex(" "))
            marks.append((ts, xs[i0], xs[i0 + len(tok)]))
        underline(st, t, marks, cy + 32, (250, 250, 250), 9)
        labels = [("start", (30, 150, 70)), ("stop", (210, 50, 60)), ("step", (120, 60, 220))]
        for (ts, tok), (lab, col), mk in zip(UL_TK, labels, marks):
            if t >= ts + 0.15:
                p11.pill(st, t, ts + 0.15, lab + ' = ' + tok, col, 230 + 310 * UL_TK.index((ts, tok)), VS[3] + 60, 36)
    for t0, letter, txt in OPTIONS:
        k = "ABC".index(letter)
        state = None if t < REVEAL else (letter == ANSWER)
        sc = pop(t - t0, 0.3)
        if t >= REVEAL and letter == ANSWER:
            sc *= 1 + 0.06 * math.exp(-(t - REVEAL) * 4) * math.sin((t - REVEAL) * 20) + 0.03
        paste(st, paper_option(letter, txt, state), 450, 1110 + k * 135, sc)
    if COUNT0 <= t < REVEAL + 0.3:
        rem = REVEAL - t
        S = 2
        im = Image.new("RGBA", (200 * S, 200 * S))
        d = ImageDraw.Draw(im)
        d.ellipse((10 * S, 10 * S, 190 * S, 190 * S), fill=(20, 20, 24), outline=(200, 200, 205), width=12 * S)
        d.arc((10 * S, 10 * S, 190 * S, 190 * S), -90, -90 + 360 * clamp(rem / (REVEAL - COUNT0)),
              fill=(46, 220, 70), width=12 * S)
        n = max(1, math.ceil(rem)) if rem > 0 else 0
        d.text((100 * S, 104 * S), str(n) if n else "!", font=mb.font(mb.BALOO, 100 * S, "ExtraBold"), fill=WHITE,
               anchor="mm")
        paste(st, im.resize((200, 200), Image.LANCZOS), 930, 1110, 1 + 0.08 * math.exp(-((t - COUNT0) % 1) * 8))
    if t >= REVEAL + 0.3:
        hop_line(st, t, REVEAL + 0.3, 1600, 2, 11, HITS_T, 100, 650, (30, 160, 70), (HITS_T[-1][0] + 0.5, 11), (40, 42, 50))


# ------------------------------------------------------------------ frame
DRAW = {"hook": draw_hook, "menu": draw_menu, "range": draw_range, "steps": draw_steps, "tricky": draw_tricky}
p11.MASCOT_IN = {"menu": 7.0, "range": 20.5, "steps": 30.5, "tricky": 45.8}
p11.REACT = [(11.7, "3 items = 3 baar!", GREEN), (SIX_T + 0.05, "6 nahi aaya!", RED),
             (RULE_T + 1.0, "Stop wala skip!", GREEN), (HITS_B[-1][0] + 0.2, "2-2 ka jump!", GREEN),
             (REVEAL + 0.05, "11 nahi, 10 se pehle!", GREEN)]


def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return k, SCENES[k]


def header_pose(t):
    """(y, scale, content_alpha) for the ref-2 title glide"""
    if t < SCENES[1][0]:
        return None
    s1 = SCENES[1][0]
    if t < s1 + 0.6:
        q = ease((t - s1) / 0.6)
        return 640 + (270 - 640) * q, 2.0 + (1.0 - 2.0) * q, 1.0
    for s0, n in SCENES[2:4]:
        a = t - s0
        if 0 <= a < GLIDE:
            q = math.sin(math.pi * a / GLIDE)
            return 270 + (820 - 270) * q, 1.0 + 0.7 * q, 0.0
    return 270, 1.0, 1.0


def frame(i):
    t = i / FPS
    if t >= END0:
        return np.asarray(es.frame(t - END0).convert("RGB"))
    k, (s0, name) = scene_at(t)
    a = t - s0
    if name == "tricky" and a >= PAPER_IN:
        fr = paper_tex().copy()
        st = Image.new("RGBA", (W, H))
        draw_tricky(st, t)
        fr.alpha_composite(st)
        p11.draw_mascot(fr, t, "tricky")
    else:
        fr = navy_bg(t)
        pose = header_pose(t)
        st = Image.new("RGBA", (W, H))
        if name == "tricky":            # navy scene frozen under the incoming paper
            draw_steps(st, s0 - 0.001)
        elif name == "hook" or pose is None or pose[2] > 0:
            DRAW[name](st, t)
        if pose is not None and name not in ("hook",):
            ca = pose[2]
            # content fades in after a glide
            for sg, _n in SCENES[2:4]:
                if sg + GLIDE <= t < sg + GLIDE + 0.3:
                    ca = ease((t - sg - GLIDE) / 0.3)
            if name == "tricky":
                ca = 1 - ease(a / PAPER_IN)
            if ca < 1:
                st.putalpha(st.getchannel("A").point(lambda v: int(v * ca)))
        if name == "hook" and t >= SCENES[1][0]:
            pass
        fr.alpha_composite(st)
        if pose is not None:
            paste(fr, header_img(round(pose[1], 2)), 540, pose[0])
        if name not in ("hook", "tricky"):
            p11.draw_mascot(fr, t, name)
        if name == "tricky":                 # paper sheet slides up over the navy (with shadow, slight tilt)
            q = ease(a / PAPER_IN)
            sheet = paper_tex()
            y = int(H * (1 - q))
            sh = Image.new("RGBA", (W, 60))
            ImageDraw.Draw(sh).rectangle((0, 30, W, 60), fill=(0, 0, 0, 120))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (0, max(0, y - 50)))
            paste(fr, sheet, W / 2, y + H / 2, 1.0, 1.0, 3 * (1 - q))
    fr.alpha_composite(p11.handle_tag(), (0, 1800))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    # zoom punches on big moments (special effect)
    for tp, amt in ((HOOK_COUNT + 9 / 7, 0.05), (OUT_R[-1], 0.03), (REVEAL, 0.05)):
        e_ = t - tp
        if 0 <= e_ < 0.4:
            z = 1 + amt * math.exp(-e_ * 9)
            arr = cv2.warpAffine(arr, np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]]), (W, H),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for ts, amp in ((SIX_T, 12), (REVEAL, 6)):
        e_ = t - ts
        if 0 <= e_ < 0.35:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.35)), axis=1)
    for tf in (SCENES[1][0], SCENES[4][0] + PAPER_IN, REVEAL):      # soft white flash
        e_ = t - tf
        if 0 <= e_ < 0.15:
            arr += (255 - arr) * 0.3 * (1 - e_ / 0.15)
    arr *= m.vignette()
    arr += cv2.resize(m.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.7
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
type_clicks, e_chime = p11.type_clicks, p11.e_chime


def rustle(dur, seed):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    crackle = fx.noise(n, seed) * (np.random.default_rng(seed).random(n) < 0.02) * 2.5
    s = fx.filt(fx.noise(n, seed + 1) * 0.5 + crackle, "bandpass", [1200, 9000])
    return s * np.sin(np.pi * tt / dur) * 0.4


def swipe(seed):
    n = int(0.22 * SR)
    tt = np.linspace(0, 1, n)
    return fx.filt(fx.noise(n, seed), "bandpass", [2500, 9000]) * np.sin(np.pi * tt) ** 2 * 0.3


def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    P(buf, fx.whoosh(0.5, 1), 0.0, 0.6)
    P(buf, fx.boom(), 0.35, 0.7)
    P(buf, swipe(2), 1.0, 0.6)
    for k, t0 in enumerate((0.9, 1.2)):
        P(buf, fx.whoosh(0.25, 3 + k), t0, 0.35)
    for k in range(10):
        P(buf, bs.note_pop(392 * 2 ** (k / 12 * 1.2)), HOOK_COUNT + k / 7, 0.3)
        P(buf, fx.pop(), HOOK_COUNT + k / 7, 0.25)
    P(buf, fx.ding(), HOOK_COUNT + 9 / 7, 0.45)
    P(buf, e_chime(), HOOK_COUNT + 9 / 7 + 0.05, 0.4)
    # glides / transitions
    P(buf, fx.whoosh(0.5, 10), SCENES[1][0], 0.55)
    for s0, _n in SCENES[2:4]:
        P(buf, fx.whoosh(0.45, int(s0)), s0, 0.5)
        P(buf, fx.whoosh(0.45, int(s0) + 1), s0 + GLIDE * 0.5, 0.45)
    P(buf, rustle(0.8, 77), SCENES[4][0] - 0.05, 0.9)
    P(buf, bs.thud(), SCENES[4][0] + PAPER_IN, 0.5)
    # menu
    for k, (ts, txt) in enumerate(MENU_CODE):
        type_clicks(buf, ts, len(txt), 28, 20 + 40 * k, 0.24)
    for k, ts in enumerate(CARD_T):
        P(buf, fx.pop(), ts, 0.45)
    for k, ts in enumerate(ITER_M):
        P(buf, fx.whoosh(0.2, 30 + k), ts - 0.1, 0.3)
        P(buf, bs.note_pop(587.3 * 2 ** (k * 4 / 12)), ts + 0.3, 0.45)
    P(buf, fx.pop(), 11.6, 0.4)
    # range
    type_clicks(buf, R_T1, len(R_LINE1), 26, 200, 0.26)
    type_clicks(buf, R_T2, len(R_LINE2.strip()), 26, 240, 0.26)
    for ts in (UL_START, UL_STOP):
        P(buf, swipe(int(ts * 10)), ts, 0.7)
        P(buf, fx.pop(), ts + 0.2, 0.4)
    P(buf, bs.mouse_click(), RUN_T, 0.7)
    scale = [523.3, 587.3, 659.3, 784.0, 880.0]
    for k, ts in enumerate(OUT_R):
        P(buf, bs.note_pop(scale[k]), ts, 0.5)
        P(buf, fx.pop(), ts, 0.3)
    P(buf, fx.boom(), SIX_T, 0.6)
    P(buf, m.e_buzz(), SIX_T + 0.05, 0.6)
    P(buf, m.box_swish(250), RULE_T, 0.7)
    type_clicks(buf, RULE_T + 0.18, 35, 34, 260, 0.18)
    # steps
    type_clicks(buf, S_A_T, 18, 26, 300, 0.24)
    type_clicks(buf, S_B_T, 25, 28, 340, 0.24)
    for k, (th, v) in enumerate(HITS_A):
        P(buf, fx.whoosh(0.18, 360 + k), th - 0.4, 0.2)
        P(buf, bs.note_pop(440 * 2 ** (k * 2 / 12)), th, 0.4)
    for k, (th, v) in enumerate(HITS_B):
        P(buf, fx.whoosh(0.2, 380 + k), th - 0.45, 0.25)
        P(buf, bs.note_pop(523.3 * 2 ** (k * 3 / 12)), th, 0.45)
    P(buf, fx.pop(), SAVE_T, 0.6)
    P(buf, bs.thud(), SAVE_T, 0.45)
    # tricky
    P(buf, fx.boom(), SCENES[4][0] + PAPER_IN, 0.6)
    P(buf, fx.pop(), SCENES[4][0] + PAPER_IN + 0.3, 0.5)
    P(buf, fx.whoosh(0.3, 400), 40.4, 0.4)
    type_clicks(buf, TK_T1, len(TRICK), 30, 410, 0.24)
    type_clicks(buf, TK_T2, len(TRICK2.strip()), 30, 450, 0.24)
    for ts, _tok in UL_TK:
        P(buf, swipe(int(ts * 10)), ts, 0.7)
        P(buf, fx.pop(), ts + 0.15, 0.35)
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
    for k, (th, v) in enumerate(HITS_T):
        P(buf, bs.note_pop(659.3 * 2 ** (k * 4 / 12)), th, 0.45)
    P(buf, m.e_buzz()[: int(0.25 * SR)], HITS_T[-1][0] + 0.5, 0.45)
    for tr, txt, col in p11.REACT:
        P(buf, fx.pop(), tr, 0.35)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.35, power=SIX_T)
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


# ------------------------------------------------------------------ wire into the EP 08 encoder
m.OUT, m.WORK, m.TOTAL, m.END0 = OUT, WORK, TOTAL, END0
m.frame, m.build_audio = frame, build_audio

if __name__ == "__main__":
    m.main()
