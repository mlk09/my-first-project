#!/usr/bin/env python3
"""Python ki Pathshala EP 18 - Tuples, in the EP 04 / EP 16 / EP 17 design  (1080x1920 HD Short)

Same format: dark charcoal grid background for every scene (incl. quiz + end screen), typewriter titles,
yellow ribbons, code editor + terminal with Run, punch-in cuts, big captions, mascot reactions.
Content: list [ ] vs tuple ( ), create + index + len, the TypeError when you try to change it (shake,
red flash, ERROR! stamp), unpacking r, g, b = rgb, recap, quiz t = (5) -> type? (no reveal).

Usage:  python3 edit25/build_ep18.py [--preview]
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
es.NEXT = "EP 19: NESTED LOOPS"

SCENES = [(0.0, "hook"), (4.0, "intro"), (9.5, "create"), (17.0, "error"), (26.0, "unpack"), (34.0, "recap"),
          (38.5, "quiz")]
END0 = 44.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP18_Tuples.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0
ERR_T = 19.5

p4.CODE_FS = 40
p4.EDITOR = {
    "create": {
        "code": [[("point = (10, 20)", 9.7)], [("print(point[0])", 11.0)], [("print(len(point))", 12.2)]],
        "run": 13.4,
        "term": [("$ python main.py", GREY, 13.6, None), ("10", GREEN, 14.0, None), ("2", GREEN, 14.3, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 14.3,
    },
    "error": {
        "code": [[("point = (10, 20)", None)], [("point[0] = 99", 17.3)]],
        "run": 18.6,
        "term": [("$ python main.py", GREY, 18.8, None), ("TypeError: 'tuple' object does", RED, ERR_T, None),
                 ("not support item assignment", RED, ERR_T, None)],
        "wait": (NEVER, NEVER), "enter": NEVER,
    },
    "unpack": {
        "code": [[("rgb = (255, 0, 0)", 26.3)], [("r, g, b = rgb", 27.6)], [("print(r, g, b)", 28.6)]],
        "run": 29.6,
        "term": [("$ python main.py", GREY, 29.8, None), ("255 0 0", GREEN, 30.1, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 30.1,
    },
}
p4.CAPTIONS = [
    (0.3, "AISI *LIST* JO…"), (2.0, "KABHI *BADAL* NAHI SAKTI!"),
    (4.2, "*LIST* = SQUARE BRACKETS [ ]"), (5.9, "*TUPLE* = ROUND BRACKETS ( )"), (7.6, "TUPLE = *LOCKED* LIST"),
    (9.7, "*TUPLE* BANAO ( ) SE"), (11.0, "INDEX *LIST* JAISA HI"), (13.4, "*RUN* KARO"), (14.1, "+10 AUR 2!+"),
    (15.6, "PADHNA *ALLOWED* HAI"),
    (17.3, "AB *BADALNE* KI KOSHISH…"), (18.6, "*RUN* KARO"), (19.6, "-ERROR!-"), (20.9, "*TUPLE* BADAL NAHI SAKTA!"),
    (22.4, "ISE KEHTE HAIN *IMMUTABLE*"), (24.0, "*INTERVIEW* FAVOURITE!"),
    (26.3, "TUPLE KA *JADOO*: UNPACKING"), (27.8, "EK LINE MEIN *3* VARIABLES"), (29.6, "*RUN* KARO"),
    (30.2, "+255 0 0!+"), (31.7, "*FIXED* DATA KE LIYE BEST"),
    (34.2, "*YAAD* RAKHO!"), (36.6, "*SCREENSHOT* LE LO!"),
    (38.7, "*QUIZ* TIME!"), (40.6, "YE *TUPLE* HAI YA NAHI?"), (42.3, "*COMMENT* KARO!"),
]
p4.REACT = [(14.2, "Easy!", GREEN), (ERR_T + 0.1, "Oops!", RED), (30.2, "Jadoo!", GREEN)]
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
    p4.type_text(st, t, 0.15, "AISI LIST JO", CAP, 92, WHITE, 540, 560, cps=16)
    p4.type_text(st, t, 1.0, "tuple( )", MONO, 170, ORANGE, 540, 770, cps=10)
    rb = mb.ribbon([("KABHI BADAL NAHI SAKTI!", (20, 20, 20), False)], mb.font(mb.BALOO, 56, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 980, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Lock ho gayi!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 460, 1140, pop(t - 2.8, 0.3))


def lock_icon(t, t0):
    im = Image.new("RGBA", (120, 140))
    d = ImageDraw.Draw(im)
    lift = 18 * (1 - ease((t - t0) / 0.3))
    d.arc((25, 8 - lift, 95, 78 - lift), 180, 360, fill=RED, width=12)
    d.line((31, 43 - lift, 31, 62), fill=RED, width=12)
    d.line((89, 43 - lift, 89, 62), fill=RED, width=12)
    d.rounded_rectangle((12, 58, 108, 134), 14, fill=RED)
    d.ellipse((52, 80, 68, 96), fill=(20, 21, 26))
    d.rectangle((57, 92, 63, 114), fill=(20, 21, 26))
    return glow(im, RED, 10)


def draw_intro(st, t):
    p4.type_text(st, t, 4.2, 'list  = ["a", "b"]', MONO, 70, ORANGE, 540, 600, cps=16)
    p4.type_text(st, t, 5.9, 'tuple = ("a", "b")', MONO, 70, ORANGE, 540, 760, cps=16)
    if t > 5.0:
        paste(st, p4.pill("[ ] = BADAL SAKTI", GREEN, 46), 540, 960, pop(t - 5.0, 0.3))
    if t > 7.0:
        paste(st, p4.pill("( ) = FIXED / LOCKED", RED, 46, WHITE), 470, 1100, pop(t - 7.0, 0.3))
        paste(st, lock_icon(t, 7.3), 860, 1095, pop(t - 7.3, 0.3))


RECAP = [(34.3, "list [ ]", "BADAL SAKTI", GREEN), (34.9, "tuple ( )", "FIXED", RED),
         (35.5, "a, b = t", "UNPACKING", YEL)]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 600 + k * 170
        p4.type_text(st, t, t0, code, MONO, 64, ORANGE, 80, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 480, 585, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((615, y), lab, font=mb.font(CAP, 56), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 36.6:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1180, pop(t - 36.6, 0.3), 1, -3)


QUIZ_CODE = [(39.3, "t = (5)"), (40.0, "print(type(t))")]


def draw_quiz(st, t):
    p4.type_text(st, t, 38.6, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 80, ORANGE, 540, 640 + k * 130, cps=18,
                     cursor=k == len(QUIZ_CODE) - 1)
    if t > 40.9:
        paste(st, p4.pill("tuple?   ya   int?", YEL, 56), 540, 950, pop(t - 40.9, 0.3))
    if t >= 41.4:
        s_ = 1 + 0.12 * math.sin((t - 41.4) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1150, pop(t - 41.4, 0.3) * s_)
    if t > 42.3:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1330, pop(t - 42.3), 1, 2)


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
    if name == "error" and t >= ERR_T:
        paste(fr, mb.outlined("ERROR!", mb.font(mb.BALOO, 150, "ExtraBold"), RED, 10, (10, 10, 10), 8,
                              (120, 0, 0)), 540, 1170, pop(t - ERR_T, 0.25), 1, -6)
    p4.draw_mascot(fr, t)
    p4.draw_caption(fr, t)
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 18", (0, 0, 0, 150), 28, YEL)
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
    tc(buf, 0.15, len("AISI LIST JO"), 16, 1, 0.4)
    tc(buf, 1.0, len("tuple( )"), 10, 20, 0.5)
    for t0 in (2.0, 2.4, 2.8):
        P(buf, fx.pop(), t0, 0.5)
    tc(buf, 4.2, 18, 16, 40, 0.4)
    tc(buf, 5.9, 18, 16, 60, 0.4)
    P(buf, fx.pop(), 5.0, 0.55)
    P(buf, fx.pop(), 7.0, 0.55)
    P(buf, bs.thud(), 7.3, 0.6)
    P(buf, bs.icon_check if False else fx.ding(), 7.45, 0.3)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for txt, col, t0, user in cfg["term"]:
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
    P(buf, fx.pop(), 36.6, 0.6)
    P(buf, bs.thud(), 36.6, 0.4)
    P(buf, fx.riser(0.6), 38.0, 0.35)
    P(buf, fx.boom(), 38.6, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt), 18, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 40.9, 0.55)
    P(buf, fx.pop(), 41.4, 0.6)
    P(buf, bs.thud(), 41.4, 0.4)
    P(buf, fx.pop(), 42.3, 0.6)
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
