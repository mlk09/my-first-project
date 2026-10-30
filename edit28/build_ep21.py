#!/usr/bin/env python3
"""Python ki Pathshala EP 21 - Dictionaries, in the EP 04/16-20 design  (1080x1920 HD Short)

Same format: dark charcoal grid background for every scene (incl. quiz + end screen), typewriter titles,
yellow ribbons, code editor + terminal with Run, punch-in cuts, big captions, mascot reactions.
Content: phonebook analogy (name -> number cards), {key: value} + access by key, add / update,
loop over items(), recap, quiz {"a": 1, "a": 2}["a"] (no reveal).

Usage:  python3 edit28/build_ep21.py [--preview]
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
es.NEXT = "EP 22: FUNCTIONS"

SCENES = [(0.0, "hook"), (4.0, "phone"), (10.5, "basic"), (19.0, "update"), (27.5, "loop"), (36.0, "recap"),
          (40.5, "quiz")]
END0 = 46.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP21_Dictionaries.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0
ERR_T = -10.0

p4.CODE_FS = 38
p4.EDITOR = {
    "basic": {
        "code": [[('marks = {"Aman": 90, "Riya": 85}', 10.7)], [('print(marks["Riya"])', 12.4)],
                 [("print(len(marks))", 13.6)]],
        "run": 14.8,
        "term": [("$ python main.py", GREY, 15.0, None), ("85", GREEN, 15.3, None), ("2", GREEN, 15.6, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 15.6,
    },
    "update": {
        "code": [[('marks = {"Aman": 90, "Riya": 85}', None)], [('marks["Kabir"] = 70', 19.3)],
                 [('marks["Aman"] = 95', 20.5)], [("print(marks)", 21.6)]],
        "run": 22.8,
        "term": [("$ python main.py", GREY, 23.0, None), ("{'Aman': 95, 'Riya': 85,", GREEN, 23.3, None),
                 (" 'Kabir': 70}", GREEN, 23.3, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 23.3,
    },
    "loop": {
        "code": [[('marks = {"Aman": 95, "Riya": 85}', None)], [("for name, m in marks.items():", 27.8)],
                 [("    print(name, m)", 29.4)]],
        "run": 30.6,
        "term": [("$ python main.py", GREY, 30.8, None), ("Aman 95", GREEN, 31.1, None), ("Riya 85", GREEN, 31.4, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 31.4,
    },
}
p4.CAPTIONS = [
    (0.3, "PYTHON KI APNI *PHONEBOOK*!"), (2.0, "ISE KEHTE HAIN *DICTIONARY*"),
    (4.2, "CONTACTS MEIN *NAAM* SE DHOONDHTE HO"), (6.0, "*NAAM* = KEY"), (7.2, "*NUMBER* = VALUE"),
    (8.8, "*KEY* AUR *VALUE* KI JODI!"),
    (10.7, "CURLY *BRACKETS* MEIN JODE"), (12.4, "*INDEX* NAHI, *KEY* SE NIKAALO"), (14.8, "*RUN* KARO"),
    (15.4, "+RIYA KE 85!+"), (16.8, "*len()* = KITNE JODE"),
    (19.3, "NAYI KEY = *NAYA* ENTRY"), (20.5, "PURANI KEY = *UPDATE*"), (22.8, "*RUN* KARO"),
    (23.4, "+KABIR JUDA, AMAN 95!+"), (25.0, "*KEY* HAMESHA UNIQUE HOTI HAI"),
    (27.8, "*items()* = KEY + VALUE"), (29.4, "*LOOP* SE SAB PRINT"), (30.6, "*RUN* KARO"),
    (31.5, "+SAB EK SAATH!+"), (33.2, "*JSON* AUR *API* MEIN ROZ KAAM AATA HAI"),
    (36.2, "*YAAD* RAKHO!"), (38.9, "*SCREENSHOT* LE LO!"),
    (40.7, "*QUIZ* TIME!"), (42.5, "*SAME* *KEY* DO BAAR?"), (44.3, "*COMMENT* KARO!"),
]
p4.REACT = [(15.4, "85!", GREEN), (23.4, "Update!", GREEN), (31.5, "Wah!", GREEN)]
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
    p4.type_text(st, t, 0.15, "PYTHON KI PHONEBOOK", CAP, 80, WHITE, 540, 560, cps=18)
    p4.type_text(st, t, 1.2, "{ key: value }", MONO, 104, ORANGE, 540, 770, cps=12)
    rb = mb.ribbon([("DICTIONARY 1 MINUTE MEIN!", (20, 20, 20), False)], mb.font(mb.BALOO, 54, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 990, pop(t - 2.2), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.5, 0.4))
    if t > 2.9:
        b = mb.bubble("Naam se dhoondho!", mb.font(mb.BALOO, 44, "ExtraBold"), 22)
        paste(st, b, 440, 1140, pop(t - 2.9, 0.3))


CONTACTS = [("Aman", "98xxx 11"), ("Riya", "97xxx 22"), ("Kabir", "99xxx 33")]
FIND_T = 7.9


def contact_card(name, num, hi):
    key = ("card", name, hi)
    if key not in p4._C:
        im = Image.new("RGBA", (860, 150))
        d = ImageDraw.Draw(im)
        col = YEL if hi else (90, 96, 110)
        d.rounded_rectangle((10, 10, 850, 140), 26, fill=(20, 21, 26), outline=col, width=5)
        d.ellipse((34, 32, 120, 118), fill=col)
        d.text((77, 77), name[0], font=mb.font(CAP, 48), fill=(20, 21, 26), anchor="mm")
        d.text((150, 75), name, font=mb.font(CAP, 50), fill=WHITE, anchor="lm")
        d.text((820, 75), num, font=mb.font(MONO, 44), fill=GREEN, anchor="rm")
        p4._C[key] = glow(im, col, 10) if hi else im
    return p4._C[key]


def draw_phone(st, t):
    for k, (nm, num) in enumerate(CONTACTS):
        t0 = 4.4 + 0.25 * k
        if t >= t0:
            hi = k == 1 and t >= FIND_T
            sc = pop(t - t0, 0.3) * (1.06 if hi else 1)
            paste(st, contact_card(nm, num, hi), 540, 520 + 170 * k, sc)
    if t > 6.0:
        paste(st, p4.pill("NAAM = KEY", YEL, 48), 300, 1060, pop(t - 6.0, 0.3))
    if t > 7.2:
        paste(st, p4.pill("NUMBER = VALUE", GREEN, 48), 760, 1060, pop(t - 7.2, 0.3))
    if t > 8.8:
        p4.type_text(st, t, 8.8, '{"Riya": "97xxx 22"}', MONO, 60, ORANGE, 540, 1230, cps=22)


RECAP = [(36.3, 'd["key"]', "NIKAALO", GREEN), (36.9, 'd["new"]=v', "JODO / UPDATE", YEL),
         (37.5, "d.items()", "LOOP", (78, 201, 176)), (38.1, "len(d)", "KITNE JODE", RED)]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 560 + k * 160
        p4.type_text(st, t, t0, code, MONO, 58, ORANGE, 60, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 470, 560, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((590, y), lab, font=mb.font(CAP, 52), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 38.9:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1240, pop(t - 38.9, 0.3), 1, -3)


QUIZ_CODE = [(41.3, 'd = {"a": 1, "a": 2}'), (42.0, 'print(d["a"])')]


def draw_quiz(st, t):
    p4.type_text(st, t, 40.6, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 70, ORANGE, 540, 640 + k * 130, cps=20, cursor=k == len(QUIZ_CODE) - 1)
    if t > 42.9:
        paste(st, p4.pill("1?   2?   ya ERROR?", YEL, 54), 540, 950, pop(t - 42.9, 0.3))
    if t >= 43.4:
        s_ = 1 + 0.12 * math.sin((t - 43.4) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1150, pop(t - 43.4, 0.3) * s_)
    if t > 44.3:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1330, pop(t - 44.3), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "phone": draw_phone, "recap": draw_recap, "quiz": draw_quiz}


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
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 21", (0, 0, 0, 150), 28, YEL)
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
    tc(buf, 0.15, len("PYTHON KI PHONEBOOK"), 18, 1, 0.4)
    tc(buf, 1.2, len("{ key: value }"), 12, 20, 0.5)
    for t0 in (2.2, 2.5, 2.9):
        P(buf, fx.pop(), t0, 0.5)
    for k in range(3):
        P(buf, fx.whoosh(0.2, 40 + k), 4.4 + 0.25 * k, 0.3)
        P(buf, fx.pop(), 4.4 + 0.25 * k, 0.4)
    P(buf, fx.pop(), 6.0, 0.55)
    P(buf, fx.pop(), 7.2, 0.55)
    P(buf, fx.ding(), FIND_T, 0.45)
    tc(buf, 8.8, 20, 22, 50, 0.4)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_.strip()), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for k, (txt, col, t0, user) in enumerate(cfg["term"]):
            P(buf, bs.note_pop(1300), t0, 0.15)
        P(buf, fx.ding(), cfg["ok"], 0.5)
        P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
    for t0, code, _lab, _col in RECAP:
        tc(buf, t0, len(code), 26, int(t0 * 5), 0.3)
        P(buf, fx.whoosh(0.2, int(t0 * 9)), t0 + 0.4, 0.3)
        P(buf, fx.pop(), t0 + 0.6, 0.45)
    P(buf, fx.pop(), 38.9, 0.6)
    P(buf, bs.thud(), 38.9, 0.4)
    P(buf, fx.riser(0.6), 40.0, 0.35)
    P(buf, fx.boom(), 40.6, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt), 20, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 42.9, 0.55)
    P(buf, fx.pop(), 43.4, 0.6)
    P(buf, bs.thud(), 43.4, 0.4)
    P(buf, fx.pop(), 44.3, 0.6)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=19.0)
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
