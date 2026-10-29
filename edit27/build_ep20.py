#!/usr/bin/env python3
"""Python ki Pathshala EP 20 - Sets, in the EP 04/16-19 design  (1080x1920 HD Short)

Same format: dark charcoal grid background for every scene (incl. quiz + end screen), typewriter titles,
yellow ribbons, code editor + terminal with Run, punch-in cuts, big captions, mascot reactions.
Content: duplicate chips fly out and the rest drop into { } braces, set(list), add() ignores a
duplicate (no order / no index), union | and intersection &, recap, quiz len({5,5,5,7}) (no reveal).

Usage:  python3 edit27/build_ep20.py [--preview]
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
es.NEXT = "EP 21: DICTIONARIES"

SCENES = [(0.0, "hook"), (4.0, "dupes"), (10.0, "basic"), (18.5, "add"), (27.0, "ops"), (35.5, "recap"),
          (40.0, "quiz")]
END0 = 45.5
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP20_Sets.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0
ERR_T = -10.0

p4.CODE_FS = 40
p4.EDITOR = {
    "basic": {
        "code": [[("nums = [1, 2, 2, 3, 3, 3]", 10.2)], [("s = set(nums)", 11.6)], [("print(s)", 12.6)]],
        "run": 13.8,
        "term": [("$ python main.py", GREY, 14.0, None), ("{1, 2, 3}", GREEN, 14.3, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 14.3,
    },
    "add": {
        "code": [[("s = {1, 2, 3}", None)], [("s.add(4)", 18.8)], [("s.add(2)", 19.8)], [("print(s)", 20.6)]],
        "run": 21.8,
        "term": [("$ python main.py", GREY, 22.0, None), ("{1, 2, 3, 4}", GREEN, 22.3, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 22.3,
    },
    "ops": {
        "code": [[("a = {1, 2, 3}", 27.2)], [("b = {3, 4}", 27.9)], [("print(a | b)", 28.6)], [("print(a & b)", 29.4)]],
        "run": 30.6,
        "term": [("$ python main.py", GREY, 30.8, None), ("{1, 2, 3, 4}", GREEN, 31.1, None), ("{3}", GREEN, 31.4, None)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 31.4,
    },
}
p4.CAPTIONS = [
    (0.3, "*DUPLICATES* SE PARESHAAN?"), (2.0, "*SET* SE EK LINE MEIN HATAO!"),
    (4.2, "LIST MEIN *DUPLICATES*…"), (6.4, "*SET* MEIN DAALO"), (7.8, "+DUPLICATES GAYAB!+"),
    (9.0, "SET = *UNIQUE* ITEMS"),
    (10.2, "LIST MEIN *REPEAT* NUMBERS"), (11.6, "*set()* MEIN DAALO"), (13.8, "*RUN* KARO"), (14.4, "+SIRF 1, 2, 3!+"),
    (16.0, "*DUPLICATES* APNE AAP GAYAB!"),
    (18.8, "*add()* SE JODO"), (19.8, "2 *DOBARA* ADD KARO?"), (21.8, "*RUN* KARO"), (22.4, "+2 DOBARA NAHI AAYA!+"),
    (24.0, "SET MEIN *ORDER* NAHI HOTA"), (25.5, "ISLIYE *INDEX* NAHI CHALTA!"),
    (27.2, "DO SETS KA *JADOO*"), (28.6, "*|* = DONO KE SAARE"), (29.6, "*&* = JO DONO MEIN COMMON"),
    (30.6, "*RUN* KARO"), (31.5, "+UNION AUR COMMON!+"), (33.0, "*INTERVIEW* MEIN POOCHTE HAIN!"),
    (35.7, "*YAAD* RAKHO!"), (38.4, "*SCREENSHOT* LE LO!"),
    (40.2, "*QUIZ* TIME!"), (42.0, "*len()* KITNA AAYEGA?"), (43.8, "*COMMENT* KARO!"),
]
p4.REACT = [(14.4, "Saaf!", GREEN), (22.4, "Unique!", GREEN), (31.5, "Jadoo!", GREEN)]
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
    p4.type_text(st, t, 0.15, "DUPLICATES HATAO", CAP, 86, WHITE, 540, 560, cps=18)
    p4.type_text(st, t, 1.1, "set( )", MONO, 200, ORANGE, 540, 780, cps=8)
    rb = mb.ribbon([("SIRF EK LINE MEIN!", (20, 20, 20), False)], mb.font(mb.BALOO, 58, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 990, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Sab unique!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 460, 1140, pop(t - 2.8, 0.3))


DUPES = ["apple", "mango", "apple", "kiwi", "mango"]
DUP_X = [160, 350, 540, 730, 920]
KEEP = [0, 1, 3]
OUT_T, SET_T = 6.4, 7.0


def draw_dupes(st, t):
    if t < SET_T + 0.3:
        lay = Image.new("RGBA", st.size)
        p4.type_text(lay, t, 4.2, "list", MONO, 70, ORANGE, 540, 560, cps=12, cursor=False)
        if t > SET_T:
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * (1 - (t - SET_T) / 0.3))))
        st.alpha_composite(lay)
    else:
        p4.type_text(st, t, SET_T + 0.3, "set", MONO, 70, YEL, 540, 560, cps=12, cursor=False)
    for k, it in enumerate(DUPES):
        t0 = 4.5 + 0.15 * k
        if t < t0:
            continue
        dup = k not in KEEP
        x, y = DUP_X[k], 700
        col = YEL
        al = 1.0
        if dup and t >= OUT_T:
            q = ease((t - OUT_T) / 0.5)
            col = RED
            y -= 300 * q
            x += (60 if k % 2 else -60) * q
            al = 1 - q
        elif not dup and t >= SET_T:
            q = ease((t - SET_T - 0.1 * KEEP.index(k)) / 0.45)
            x = DUP_X[k] + (300 + 220 * KEEP.index(k) - DUP_X[k]) * q
            y = 700 + 260 * q
        if al > 0.02:
            paste(st, chip(it, col, 40), x, y, pop(t - t0, 0.25), al)
    if t >= SET_T:
        q = ease((t - SET_T) / 0.35)
        f = mb.font(MONO, 190)
        d = ImageDraw.Draw(st)
        for ch, x in (("{", 150 - 60 * (1 - q)), ("}", 930 + 60 * (1 - q))):
            d.text((x, 950), ch, font=f, fill=YEL + (int(255 * q),), anchor="mm")
    if t > 8.0:
        paste(st, p4.pill("{ } = SET", YEL, 48), 540, 1160, pop(t - 8.0, 0.3))
    if t > 8.8:
        paste(st, p4.pill("NO DUPLICATES!", GREEN, 48), 540, 1290, pop(t - 8.8, 0.3))


RECAP = [(35.8, "set()", "NO DUPLICATES", GREEN), (36.4, "add()", "JODO", YEL), (37.0, "a | b", "UNION", (78, 201, 176)),
         (37.6, "a & b", "COMMON", RED)]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 560 + k * 160
        p4.type_text(st, t, t0, code, MONO, 64, ORANGE, 90, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 420, 525, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((555, y), lab, font=mb.font(CAP, 56), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 38.4:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1240, pop(t - 38.4, 0.3), 1, -3)


QUIZ_CODE = [(40.8, "s = {5, 5, 5, 7}"), (41.5, "print(len(s))")]


def draw_quiz(st, t):
    p4.type_text(st, t, 40.1, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 80, ORANGE, 540, 640 + k * 130, cps=18, cursor=k == len(QUIZ_CODE) - 1)
    if t > 42.4:
        paste(st, p4.pill("4?   ya   2?", YEL, 60), 540, 950, pop(t - 42.4, 0.3))
    if t >= 42.9:
        s_ = 1 + 0.12 * math.sin((t - 42.9) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1150, pop(t - 42.9, 0.3) * s_)
    if t > 43.8:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1330, pop(t - 43.8), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "dupes": draw_dupes, "recap": draw_recap, "quiz": draw_quiz}


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
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 20", (0, 0, 0, 150), 28, YEL)
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
    tc(buf, 0.15, len("DUPLICATES HATAO"), 18, 1, 0.4)
    tc(buf, 1.1, len("set( )"), 8, 20, 0.5)
    for t0 in (2.0, 2.4, 2.8):
        P(buf, fx.pop(), t0, 0.5)
    tc(buf, 4.2, 4, 12, 30, 0.4)
    for k in range(5):
        P(buf, fx.pop(), 4.5 + 0.15 * k, 0.35)
    P(buf, fx.whoosh(0.4, 33), OUT_T, 0.6)
    P(buf, p4.buzzer()[: int(0.2 * SR)], OUT_T, 0.4)
    P(buf, fx.whoosh(0.4, 34), SET_T, 0.5)
    P(buf, bs.thud(), SET_T + 0.4, 0.5)
    for k in range(3):
        P(buf, bs.note_pop(523.3 * 2 ** (k * 4 / 12)), SET_T + 0.45 + 0.1 * k, 0.4)
    P(buf, fx.pop(), 8.0, 0.55)
    P(buf, fx.ding(), 8.8, 0.45)
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
    P(buf, fx.pop(), 38.4, 0.6)
    P(buf, bs.thud(), 38.4, 0.4)
    P(buf, fx.riser(0.6), 39.5, 0.35)
    P(buf, fx.boom(), 40.1, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt), 18, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 42.4, 0.55)
    P(buf, fx.pop(), 42.9, 0.6)
    P(buf, bs.thud(), 42.9, 0.4)
    P(buf, fx.pop(), 43.8, 0.6)
    for tr, txt, col in p4.REACT:
        P(buf, fx.pop(), tr, 0.4)
    P(buf, es.sfx(), END0, 0.9)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.05, power=18.5)
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
