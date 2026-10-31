#!/usr/bin/env python3
"""Python ki Pathshala EP 22 - Functions (def), in the EP 04/16-21 design  (1080x1920 HD Short)

Same format: dark charcoal grid background for every scene (incl. quiz + end screen), typewriter titles,
yellow ribbons, code editor + terminal with Run, punch-in cuts, big captions, mascot reactions.
Content: Maggi recipe analogy (write once, cook many times), def + call 3x, NameError when called
before def (red flash + ERROR!), function called from a loop, recap, quiz: def without a call (no reveal).

Usage:  python3 edit29/build_ep22.py [--preview]
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
es.NEXT = "EP 23: RETURN"

SCENES = [(0.0, "hook"), (4.0, "recipe"), (10.5, "basic"), (19.5, "error"), (28.0, "loop"), (35.5, "recap"),
          (40.0, "quiz")]
END0 = 45.5
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP22_Functions.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0
ERR_T = 22.0

p4.CODE_FS = 40
p4.EDITOR = {
    "basic": {
        "code": [[("def namaste():", 10.7)], [('    print("Namaste ji!")', 11.7)], [("namaste()", 13.2)],
                 [("namaste()", 13.8)], [("namaste()", 14.4)]],
        "run": 15.4,
        "term": [("$ python main.py", GREY, 15.6, None), ("Namaste ji!", GREEN, 15.9, None),
                 ("Namaste ji!", GREEN, 16.2, None), ("Namaste ji!", GREEN, 16.5, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 16.5,
    },
    "error": {
        "code": [[("chai()", 19.7)], [("def chai():", 20.2)], [('    print("Garam chai!")', 20.7)]],
        "run": 21.4,
        "term": [("$ python main.py", GREY, 21.6, None), ("NameError: name 'chai'", RED, ERR_T, None),
                 ("is not defined", RED, ERR_T, None)],
        "wait": (NEVER, NEVER), "enter": NEVER,
    },
    "loop": {
        "code": [[("def star():", 28.2)], [('    print("*" * 5)', 28.9)], [("for i in range(3):", 29.9)],
                 [("    star()", 30.8)]],
        "run": 31.7,
        "term": [("$ python main.py", GREY, 31.9, None), ("*****", YEL, 32.2, None), ("*****", YEL, 32.5, None),
                 ("*****", YEL, 32.8, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 32.8,
    },
}
p4.CAPTIONS = [
    (0.3, "CODE *BAAR-BAAR* LIKHTE HO?"), (2.0, "*FUNCTION* BANAO, BAS!"),
    (4.2, "SOCHO *MAGGI* KI RECIPE"), (5.8, "*EK* *BAAR* SEEKHO"), (7.2, "*BAAR-BAAR* BANAO!"),
    (8.8, "RECIPE = *FUNCTION*"),
    (10.7, "*def* SE FUNCTION BANAO"), (11.7, "ANDAR *4* *SPACE* KA GAP"), (13.2, "NAAM + *()* = CALL KARO"),
    (15.4, "*RUN* KARO"), (16.0, "+3 BAAR NAMASTE!+"), (17.4, "*EK* *BAAR* LIKHA, *3* *BAAR* CHALA!"),
    (19.7, "PEHLE *CALL*, BAAD MEIN *def*?"), (21.4, "*RUN* KARO"), (22.1, "-ERROR!-"),
    (23.5, "PYTHON *UPAR* *SE* *NEECHE* PADHTA HAI"), (25.3, "PEHLE *def*, PHIR *CALL*!"),
    (28.2, "*LOOP* SE BHI CALL KARO"), (31.7, "*RUN* KARO"), (32.4, "+3 LINE STARS!+"),
    (33.8, "*TIME* AUR *MEHNAT* DONO BACHAO"),
    (35.7, "*YAAD* RAKHO!"), (38.4, "*SCREENSHOT* LE LO!"),
    (40.2, "*QUIZ* TIME!"), (42.0, "OUTPUT KYA AAYEGA?"), (43.8, "*COMMENT* KARO!"),
]
p4.REACT = [(16.0, "3 baar!", GREEN), (ERR_T + 0.1, "Oops!", RED), (32.4, "Stars!", GREEN)]
p4.END0 = END0
p4.ERR_T = ERR_T

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
    p4.type_text(st, t, 0.15, "PYTHON MEIN", CAP, 92, WHITE, 540, 560, cps=16)
    p4.type_text(st, t, 0.9, "def( )", MONO, 200, ORANGE, 540, 780, cps=8)
    rb = mb.ribbon([("EK BAAR LIKHO, BAAR-BAAR CHALAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 46, "ExtraBold"),
                   100, 34, fill=YEL)
    paste(st, rb, 540, 990, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Mehnat bachao!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 450, 1140, pop(t - 2.8, 0.3))


STEPS = ["1. Paani ubaalo", "2. Maggi daalo", "3. Masala daalo", "4. 2 minute!"]
CALL_T = 7.4


def recipe_card(t):
    im = Image.new("RGBA", (620, 420))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 612, 412), 28, fill=(20, 21, 26), outline=YEL, width=6)
    d.text((310, 56), "MAGGI RECIPE", font=mb.font(CAP, 46), fill=YEL, anchor="mm")
    for k, stp in enumerate(STEPS):
        if t >= 4.6 + 0.3 * k:
            d.text((44, 140 + 68 * k), stp, font=mb.font(CAP, 40), fill=WHITE, anchor="lm")
    return glow(im, YEL, 10)


def draw_recipe(st, t):
    paste(st, recipe_card(t), 540, 640, pop(t - 4.3, 0.3))
    for k in range(3):
        t0 = CALL_T + 0.35 * k
        if t >= t0:
            paste(st, chip("bowl " + str(k + 1), GREEN, 40), 240 + 300 * k, 960, pop(t - t0, 0.3))
    if t > 8.8:
        paste(st, p4.pill("RECIPE = FUNCTION", YEL, 50), 540, 1110, pop(t - 8.8, 0.3))
    if t > 9.5:
        paste(st, p4.pill("BANANA = CALL", GREEN, 50), 540, 1240, pop(t - 9.5, 0.3))


RECAP = [(35.8, "def naam():", "BANAO", YEL), (36.4, "naam()", "CALL KARO", GREEN),
         (37.0, "pehle def", "PHIR CALL", RED)]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 600 + k * 170
        p4.type_text(st, t, t0, code, MONO, 60, ORANGE, 60, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 500, 585, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((615, y), lab, font=mb.font(CAP, 54), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 38.4:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1180, pop(t - 38.4, 0.3), 1, -3)


QUIZ_CODE = [(40.8, "def hello():"), (41.4, '    print("Hi")'), (42.0, 'print("Bye")')]


def draw_quiz(st, t):
    p4.type_text(st, t, 40.1, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 70, ORANGE, 200, 610 + k * 110, cps=20, anchor="lm",
                     cursor=k == len(QUIZ_CODE) - 1)
    if t > 42.7:
        paste(st, p4.pill("Hi?  Bye?  ya DONO?", YEL, 54), 540, 990, pop(t - 42.7, 0.3))
    if t >= 43.2:
        s_ = 1 + 0.12 * math.sin((t - 43.2) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1170, pop(t - 43.2, 0.3) * s_)
    if t > 43.8:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1340, pop(t - 43.8), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "recipe": draw_recipe, "recap": draw_recap, "quiz": draw_quiz}


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
    if name == "error" and t >= ERR_T:
        paste(fr, mb.outlined("ERROR!", mb.font(mb.BALOO, 150, "ExtraBold"), RED, 10, (10, 10, 10), 8,
                              (120, 0, 0)), 540, 1170, pop(t - ERR_T, 0.25), 1, -6)
    p4.draw_mascot(fr, t)
    p4.draw_caption(fr, t)
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 22", (0, 0, 0, 150), 28, YEL)
    fr.alpha_composite(pill_t, (W // 2 - pill_t.width // 2, 140))
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    if s0 > 0 and a < 0.15:
        arr += (255 - arr) * 0.25 * (1 - a / 0.15)
    if 0 <= t - ERR_T < 0.3:
        e_ = t - ERR_T
        arr = arr * (1 - 0.35 * (1 - e_ / 0.3)) + np.array([255, 30, 40]) * 0.35 * (1 - e_ / 0.3)
    for ts, amp in ((ERR_T, 22),):
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
    tc(buf, 0.15, len("PYTHON MEIN"), 16, 1, 0.4)
    tc(buf, 0.9, len("def( )"), 8, 20, 0.5)
    for t0 in (2.0, 2.4, 2.8):
        P(buf, fx.pop(), t0, 0.5)
    P(buf, fx.pop(), 4.3, 0.5)
    for k in range(4):
        tc(buf, 4.6 + 0.3 * k, 6, 30, 40 + k * 7, 0.25)
    for k in range(3):
        P(buf, fx.pop(), CALL_T + 0.35 * k, 0.45)
        P(buf, bs.note_pop(523.3 * 2 ** (k * 4 / 12)), CALL_T + 0.35 * k, 0.35)
    P(buf, fx.pop(), 8.8, 0.55)
    P(buf, fx.pop(), 9.5, 0.55)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_.strip()), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for k, (txt, col, t0, user) in enumerate(cfg["term"]):
            P(buf, bs.note_pop(1300 if col != RED else 400), t0, 0.15)
        if "ok" in cfg:
            P(buf, fx.ding(), cfg["ok"], 0.5)
            P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
    P(buf, fx.boom(), ERR_T, 0.9)
    P(buf, p4.buzzer(), ERR_T, 0.8)
    P(buf, p4.glitch(), ERR_T + 0.05, 0.7)
    for t0, code, _lab, _col in RECAP:
        tc(buf, t0, len(code), 26, int(t0 * 5), 0.3)
        P(buf, fx.whoosh(0.2, int(t0 * 9)), t0 + 0.4, 0.3)
        P(buf, fx.pop(), t0 + 0.6, 0.45)
    P(buf, fx.pop(), 38.4, 0.6)
    P(buf, bs.thud(), 38.4, 0.4)
    P(buf, fx.riser(0.6), 39.5, 0.35)
    P(buf, fx.boom(), 40.1, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt.strip()), 20, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 42.7, 0.55)
    P(buf, fx.pop(), 43.2, 0.6)
    P(buf, bs.thud(), 43.2, 0.4)
    P(buf, fx.pop(), 43.8, 0.6)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=ERR_T)
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
