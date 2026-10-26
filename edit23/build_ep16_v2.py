#!/usr/bin/env python3
"""Python ki Pathshala EP 16 - Lists, v2 in the EP 04 input() design  (1080x1920 HD Short)

Same content as build_ep16.py, re-cut in the EP 04 look the user picked:
dark charcoal GRID background (slow scroll) for EVERY scene incl. the quiz and end screen, typewriter
title cards (white Poppins + big orange mono code), yellow ribbon, a real code editor + terminal with Run
button and camera that follows the typing line then the output, punch-in cuts, big bottom captions with
*yellow* keywords, mascot reactions. Fruit names in English; slower pace (about 42 s + end screen).

Usage:  python3 edit23/build_ep16_v2.py [--preview]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit11"))
import build_ep04 as p4   # noqa: E402  EP 04 engine: grid bg, typewriter, editor + terminal, captions

fx, bs, mb, es = p4.fx, p4.bs, p4.mb, p4.es
clamp, ease, pop, paste, glow = p4.clamp, p4.ease, p4.pop, p4.paste, p4.glow
W, H, FPS, SR = p4.W, p4.H, p4.FPS, p4.SR
CAP, MONO = p4.CAP, p4.MONO
WHITE, YEL, GREEN, RED, ORANGE, GREY = p4.WHITE, p4.YEL, p4.GREEN, p4.RED, p4.ORANGE, p4.GREY
es.NEXT = "EP 17: LIST METHODS"

SCENES = [(0.0, "hook"), (4.0, "syntax"), (11.0, "index"), (20.0, "change"), (28.5, "append"), (36.5, "quiz")]
END0 = 42.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP16_Lists.mp4")
WORK = os.path.join(HERE, "work_v2")
LIST_LINE = 'fruits = ["apple","banana","mango"]'
NEVER = 9999.0

p4.CODE_FS = 40
p4.EDITOR = {
    "index": {
        "code": [[(LIST_LINE, 11.3)], [("print(fruits[0])", 13.2)], [("print(fruits[-1])", 14.5)]],
        "run": 15.8,
        "term": [("$ python main.py", GREY, 16.0, None), ("apple", GREEN, 16.4, None), ("mango", GREEN, 16.8, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 16.8,
    },
    "change": {
        "code": [[(LIST_LINE, None)], [('fruits[1] = "grapes"', 20.3)], [("print(fruits)", 21.8)]],
        "run": 23.0,
        "term": [("$ python main.py", GREY, 23.2, None), ("['apple', 'grapes', 'mango']", GREEN, 23.6, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 23.6,
    },
    "append": {
        "code": [[(LIST_LINE, None)], [('fruits.append("orange")', 28.8)], [("print(len(fruits))", 30.4)]],
        "run": 31.7,
        "term": [("$ python main.py", GREY, 31.9, None), ("4", GREEN, 32.3, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 32.3,
    },
}
p4.CAPTIONS = [
    (0.3, "100 *VARIABLES* BANAOGE?"), (1.9, "NAHI! EK *LIST* BANAO!"),
    (4.2, "*LIST* KAISE BANTI HAI?"), (5.4, "ANDAR APNE *ITEMS*"), (7.4, "*SQUARE* BRACKETS = LIST"),
    (8.4, "*COMMA* SE ALAG-ALAG"), (9.6, "EK NAAM, *3* CHEEZEIN!"),
    (11.3, "PEHLE *LIST* BANAO"), (13.2, "INDEX *0* = PEHLA ITEM"), (14.5, "*-1* = AAKHRI ITEM"),
    (15.8, "*RUN* KARO"), (16.5, "+APPLE AUR MANGO!+"), (17.8, "GINTI *0* SE SHURU HOTI HAI!"),
    (20.3, "LIST *BADAL* SAKTI HAI!"), (21.6, "BANANA KI JAGAH *GRAPES*"), (23.0, "*RUN* KARO"),
    (23.7, "+BANANA GAYA, GRAPES AAYA!+"), (25.3, "ISE KEHTE HAIN *MUTABLE*"), (26.8, "*INTERVIEW* MEIN POOCHTE HAIN!"),
    (28.8, "NAYA ITEM *JODNA* HAI?"), (29.8, "*append()* LAGAO"), (31.7, "*RUN* KARO"), (32.4, "+AB 4 ITEMS!+"),
    (33.8, "*len()* = KITNE ITEMS"),
    (36.7, "*QUIZ* TIME!"), (37.9, "LIST AB YE HAI…"), (39.0, "*fruits[-2]* KYA DEGA?"), (40.3, "*COMMENT* KARO!"),
]
p4.REACT = [(16.9, "Wah!", GREEN), (23.8, "Badal gaya!", GREEN), (32.4, "4 items!", GREEN)]
p4.END0 = END0
p4.ERR_T = -10.0


# ------------------------------------------------------------------ grid scenes
def chip(txt, col=YEL, size=50):
    f = mb.font(MONO, size)
    w = int(f.getlength(txt)) + 60
    im = Image.new("RGBA", (w + 30, int(size * 2.0) + 30))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + w, im.height - 15), 22, fill=(20, 21, 26), outline=col, width=6)
    d.text((15 + w / 2, im.height / 2 + 2), txt, font=f, fill=WHITE, anchor="mm")
    return glow(im, col, 10)


def draw_hook(st, t):
    p4.type_text(st, t, 0.15, "100 VARIABLES?", CAP, 92, WHITE, 540, 560, cps=18)
    if t > 1.3:
        q = ease((t - 1.3) / 0.25)
        f = mb.font(CAP, 92)
        w = f.getlength("100 VARIABLES?")
        ImageDraw.Draw(st).line((540 - w / 2 - 10, 565, 540 - w / 2 - 10 + (w + 20) * q, 565), fill=RED, width=14)
    p4.type_text(st, t, 1.7, "list[ ]", MONO, 190, ORANGE, 540, 790, cps=10)
    rb = mb.ribbon([("EK LIST KAAFI HAI!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 1000, pop(t - 2.6), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.9, 0.4))
    if t > 3.2:
        b = mb.bubble("Sab ek jagah!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 470, 1140, pop(t - 3.2, 0.3))


ITEMS = [(5.4, "apple", 190), (5.9, "banana", 540), (6.4, "mango", 890)]


def draw_syntax(st, t):
    p4.type_text(st, t, 4.2, "fruits = [ ]", MONO, 110, ORANGE, 540, 600, cps=12)
    for t0, txt, x in ITEMS:
        if t >= t0:
            a = t - t0
            q = ease(a / 0.4)
            paste(st, chip(f'"{txt}"', YEL, 46), x, 600 + 220 * q - 120 * math.sin(math.pi * q), 0.6 + 0.4 * q)
    if t >= 6.8:
        for k, x in enumerate((358, 722)):
            paste(st, p4.pill(",", YEL, 44), x, 836, pop(t - 6.8 - 0.1 * k, 0.25))
    if t > 7.4:
        paste(st, p4.pill("[ ] = SQUARE BRACKETS", YEL, 46), 540, 1010, pop(t - 7.4, 0.3))
    if t > 8.4:
        paste(st, p4.pill(", = ITEMS ALAG KARO", GREEN, 46), 540, 1150, pop(t - 8.4, 0.3))


QUIZ_ITEMS = ["apple", "grapes", "mango", "orange"]


def draw_quiz(st, t):
    p4.type_text(st, t, 36.6, "QUIZ TIME!", CAP, 110, YEL, 540, 440, cps=14, cursor=False)
    p4.type_text(st, t, 37.2, "print(fruits[-2])", MONO, 76, ORANGE, 540, 640, cps=16)
    for k, it in enumerate(QUIZ_ITEMS):
        t0 = 37.9 + 0.2 * k
        if t >= t0:
            paste(st, chip(it, YEL if k != 2 or t < 39.0 else YEL, 40), 165 + 250 * k, 850, pop(t - t0, 0.3))
        if t >= 38.8 + 0.1 * k:
            ImageDraw.Draw(st).text((165 + 250 * k, 960), str(k - 4), font=mb.font(MONO, 44), fill=(255, 140, 150),
                                    anchor="mm")
    if t >= 39.2:
        s = 1 + 0.12 * math.sin((t - 39.2) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1150, pop(t - 39.2, 0.3) * s)
    if t > 40.3:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1330, pop(t - 40.3), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "syntax": draw_syntax, "quiz": draw_quiz}


# ------------------------------------------------------------------ frame
def scene_at(t):
    k = max(j for j, (s0, _) in enumerate(SCENES) if t >= s0)
    return SCENES[k]


_end = []


def frame(i):
    t = i / FPS
    if t >= END0:
        if not _end:
            es.static_layer = lambda: Image.new("RGBA", (W, H))
            es.mb.wood_frame = lambda *a, **k: None
            _end.append(1)
        fr = p4.background(t).copy()
        fr.alpha_composite(es.frame(t - END0))
        arr = np.asarray(fr.convert("RGB")).astype(np.float32) * p4.vignette()
        return np.clip(arr, 0, 255).astype(np.uint8)
    s0, name = scene_at(t)
    st = Image.new("RGBA", (W, H))
    cy, z = 960, 1.0
    if name in p4.EDITOR:
        p4.draw_editor(st, t, name)
        cy, z = editor_focus(t, name)
    else:
        GRID[name](st, t)
        z = 1.0 + 0.04 * ease((t - s0) / 4)
    a = t - s0
    if s0 > 0 and a < 0.22:
        z *= 1 + 0.12 * (1 - ease(a / 0.22))
    cx = W / 2
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[1, 2] += 860 - cy
    M[0, 2] += W / 2 - cx
    stage = cv2.warpAffine(np.asarray(st), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fr = p4.background(t).copy()
    fr.alpha_composite(Image.fromarray(stage))
    p4.draw_mascot(fr, t)
    p4.draw_caption(fr, t)
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 16", (0, 0, 0, 150), 28, YEL)
    fr.alpha_composite(pill_t, (W // 2 - pill_t.width // 2, 140))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    if s0 > 0 and a < 0.15:
        arr += (255 - arr) * 0.25 * (1 - a / 0.15)
    for ts, amp in ((1.3, 14),):
        e_ = t - ts
        if 0 <= e_ < 0.3:
            arr = np.roll(arr, int(amp * math.sin(e_ * 80) * (1 - e_ / 0.3)), axis=1)
    arr *= p4.vignette()
    arr += cv2.resize(p4.GRAIN[i % 5], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def sfx_track():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    tc = p4.type_clicks
    for s0, _n in SCENES[1:]:
        P(buf, fx.whoosh(0.3, int(s0 * 10)), s0 - 0.2, 0.5)
    P(buf, fx.boom()[: int(0.6 * SR)], 0.05, 0.5)
    tc(buf, 0.15, len("100 VARIABLES?"), 18, 1, 0.4)
    P(buf, fx.whoosh(0.25, 3), 1.3, 0.5)
    P(buf, p4.buzzer(), 1.35, 0.5)
    tc(buf, 1.7, len("list[ ]"), 10, 20, 0.5)
    for t0 in (2.6, 2.9, 3.2):
        P(buf, fx.pop(), t0, 0.5)
    tc(buf, 4.2, len("fruits = [ ]"), 12, 40, 0.45)
    for k, (t0, _txt, _x) in enumerate(ITEMS):
        P(buf, fx.whoosh(0.3, 50 + k), t0, 0.4)
        P(buf, bs.note_pop(523.3 * 2 ** (k * 4 / 12)), t0 + 0.4, 0.45)
    P(buf, fx.pop(), 6.8, 0.4)
    P(buf, fx.pop(), 6.9, 0.4)
    P(buf, fx.pop(), 7.4, 0.55)
    P(buf, fx.pop(), 8.4, 0.55)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for txt, col, t0, user in cfg["term"]:
            P(buf, bs.note_pop(1300), t0, 0.15)
        P(buf, fx.ding(), cfg["ok"], 0.5)
        P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
    P(buf, fx.riser(0.6), 36.0, 0.35)
    P(buf, fx.boom(), 36.6, 0.6)
    tc(buf, 37.2, len("print(fruits[-2])"), 16, 90, 0.45)
    for k in range(4):
        P(buf, fx.pop(), 37.9 + 0.2 * k, 0.4)
    P(buf, fx.pop(), 39.2, 0.6)
    P(buf, bs.thud(), 39.2, 0.4)
    P(buf, fx.pop(), 40.3, 0.6)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=20.0)
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


p4.OUT, p4.WORK, p4.TOTAL = OUT, WORK, TOTAL
p4.frame, p4.build_audio = frame, build_audio

if __name__ == "__main__":
    p4.main()
