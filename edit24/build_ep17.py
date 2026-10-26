#!/usr/bin/env python3
"""Python ki Pathshala EP 17 - List methods, in the EP 04 / EP 16 design  (1080x1920 HD Short)

Same format as EP 16 v2: dark charcoal grid background for every scene (incl. quiz + end screen),
typewriter title cards (white + big orange code), yellow ribbons, code editor + terminal with Run,
punch-in cuts, big bottom captions with *yellow* keywords, mascot reactions, calm pace.
Content: insert(), remove(), pop(), sort() (+ reverse=True tip), recap card, quiz (no reveal).

Usage:  python3 edit24/build_ep17.py [--preview]
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
es.NEXT = "EP 18: TUPLES"

SCENES = [(0.0, "hook"), (4.0, "intro"), (9.0, "insert"), (16.5, "remove"), (24.0, "pop"), (31.5, "sort"),
          (39.0, "recap"), (43.5, "quiz")]
END0 = 49.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP17_List_Methods.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0

p4.CODE_FS = 40
p4.EDITOR = {
    "insert": {
        "code": [[('fruits = ["apple","mango"]', 9.2)], [('fruits.insert(1, "kiwi")', 10.6)], [("print(fruits)", 12.2)]],
        "run": 13.4,
        "term": [("$ python main.py", GREY, 13.6, None), ("['apple', 'kiwi', 'mango']", GREEN, 14.0, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 14.0,
    },
    "remove": {
        "code": [[('fruits = ["apple","kiwi","mango"]', None)], [('fruits.remove("kiwi")', 16.8)],
                 [("print(fruits)", 18.4)]],
        "run": 19.6,
        "term": [("$ python main.py", GREY, 19.8, None), ("['apple', 'mango']", GREEN, 20.2, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 20.2,
    },
    "pop": {
        "code": [[('fruits = ["apple","mango","grapes"]', None)], [("x = fruits.pop()", 24.3)],
                 [("print(x, fruits)", 25.8)]],
        "run": 27.0,
        "term": [("$ python main.py", GREY, 27.2, None), ("grapes ['apple', 'mango']", GREEN, 27.6, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 27.6,
    },
    "sort": {
        "code": [[("nums = [5, 2, 9, 1]", None)], [("nums.sort()", 31.8)], [("print(nums)", 33.0)]],
        "run": 34.2,
        "term": [("$ python main.py", GREY, 34.4, None), ("[1, 2, 5, 9]", GREEN, 34.8, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 34.8,
    },
}
p4.CAPTIONS = [
    (0.3, "LIST KE *4 SUPERPOWERS*"), (2.0, "EK-EK KARKE DEKHO!"),
    (4.2, "*METHOD* = LIST KA KAAM"), (5.9, "*DOT* LAGAO, KAAM KARAO"), (7.4, "LIST + *.METHOD()* = JADOO!"),
    (9.2, "*insert()* = BEECH MEIN JODO"), (10.6, "INDEX *1* PE KIWI"), (13.4, "*RUN* KARO"),
    (14.1, "+KIWI BEECH MEIN AA GAYA!+"),
    (16.8, "*remove()* = NAAM SE HATAO"), (18.4, "KIWI KO HATAO"), (19.6, "*RUN* KARO"), (20.3, "+KIWI GAYAB!+"),
    (21.9, "SIRF *PEHLA* MATCH HATTA HAI"),
    (24.3, "*pop()* = AAKHRI NIKAALO"), (25.8, "AUR WAPAS *DETA* BHI HAI"), (27.0, "*RUN* KARO"),
    (27.7, "+GRAPES BAAHAR!+"), (29.3, "*pop(0)* = PEHLA NIKAALO"),
    (31.8, "*sort()* = CHHOTE SE BADA"), (34.2, "*RUN* KARO"), (34.9, "+1, 2, 5, 9!+"),
    (36.4, "*reverse=True* = ULTA ORDER"),
    (39.2, "*YAAD* RAKHO!"), (41.8, "*SCREENSHOT* LE LO!"),
    (43.7, "*QUIZ* TIME!"), (46.0, "OUTPUT KYA AAYEGA?"), (47.4, "*COMMENT* KARO!"),
]
p4.REACT = [(14.1, "Beech mein!", GREEN), (20.3, "Gayab!", GREEN), (27.7, "Nikal gaya!", GREEN),
            (34.9, "Sorted!", GREEN)]
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
    p4.type_text(st, t, 0.15, "LIST KE", CAP, 96, WHITE, 540, 560, cps=16)
    p4.type_text(st, t, 0.8, ".methods()", MONO, 150, ORANGE, 540, 770, cps=12)
    rb = mb.ribbon([("4 JADOO METHODS!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 980, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Dekho kya kya!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 460, 1140, pop(t - 2.8, 0.3))


INTRO_CHIPS = [(5.0, ".insert()", 280, 820), (5.3, ".remove()", 790, 900), (5.6, ".pop()", 300, 1010),
               (5.9, ".sort()", 780, 1110)]


def draw_intro(st, t):
    p4.type_text(st, t, 4.2, "fruits", MONO, 120, ORANGE, 540, 620, cps=12)
    for k, (t0, txt, x, y) in enumerate(INTRO_CHIPS):
        if t >= t0:
            paste(st, chip(txt, [YEL, RED, (78, 201, 176), GREEN][k], 50), x, y + 10 * math.sin(t * 3 + k),
                  pop(t - t0, 0.3), 1, 3 * math.sin(k + 1))
    if t > 7.2:
        paste(st, p4.pill("DOT  .  LAGAO = KAAM KARAO", YEL, 46), 540, 1260, pop(t - 7.2, 0.3))


RECAP = [(39.3, "insert()", "BEECH MEIN", YEL), (39.9, "remove()", "NAAM SE", RED),
         (40.5, "pop()", "AAKHRI", (78, 201, 176)), (41.1, "sort()", "ORDER", GREEN)]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 560 + k * 160
        p4.type_text(st, t, t0, code, MONO, 64, ORANGE, 90, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 470, 575, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((605, y), lab, font=mb.font(CAP, 56), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 41.8:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1240, pop(t - 41.8, 0.3), 1, -3)


QUIZ_CODE = [(44.3, "a = [3, 1, 2]"), (44.9, "a.append(0)"), (45.4, "a.sort()"), (45.9, "print(a[0])")]


def draw_quiz(st, t):
    p4.type_text(st, t, 43.6, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 66, ORANGE, 230, 600 + k * 100, cps=22, anchor="lm",
                     cursor=k == len(QUIZ_CODE) - 1)
    if t >= 46.3:
        s = 1 + 0.12 * math.sin((t - 46.3) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1130, pop(t - 46.3, 0.3) * s)
    if t > 47.4:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1320, pop(t - 47.4), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "intro": draw_intro, "recap": draw_recap, "quiz": draw_quiz}


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
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 17", (0, 0, 0, 150), 28, YEL)
    fr.alpha_composite(pill_t, (W // 2 - pill_t.width // 2, 140))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    if s0 > 0 and a < 0.15:
        arr += (255 - arr) * 0.25 * (1 - a / 0.15)
    for ts, amp in ((0.8, 0),):
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
    tc(buf, 0.15, len("LIST KE"), 16, 1, 0.4)
    tc(buf, 0.8, len(".methods()"), 12, 20, 0.5)
    for t0 in (2.0, 2.4, 2.8):
        P(buf, fx.pop(), t0, 0.5)
    tc(buf, 4.2, len("fruits"), 12, 40, 0.45)
    for k, (t0, *_r) in enumerate(INTRO_CHIPS):
        P(buf, fx.pop(), t0, 0.45)
        P(buf, bs.note_pop(523.3 * 2 ** (k * 3 / 12)), t0, 0.3)
    P(buf, fx.pop(), 7.2, 0.55)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for txt, col, t0, user in cfg["term"]:
            P(buf, bs.note_pop(1300), t0, 0.15)
        P(buf, fx.ding(), cfg["ok"], 0.5)
        P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
    for t0, code, _lab, _col in RECAP:
        tc(buf, t0, len(code), 26, int(t0 * 5), 0.3)
        P(buf, fx.whoosh(0.2, int(t0 * 9)), t0 + 0.4, 0.3)
        P(buf, fx.pop(), t0 + 0.6, 0.45)
    P(buf, fx.pop(), 41.8, 0.6)
    P(buf, bs.thud(), 41.8, 0.4)
    P(buf, fx.riser(0.6), 43.0, 0.35)
    P(buf, fx.boom(), 43.6, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt), 22, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 46.3, 0.6)
    P(buf, bs.thud(), 46.3, 0.4)
    P(buf, fx.pop(), 47.4, 0.6)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=16.5)
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
