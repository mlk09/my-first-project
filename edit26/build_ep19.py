#!/usr/bin/env python3
"""Python ki Pathshala EP 19 - Nested loops + star pattern, in the EP 04/16/17/18 design  (1080x1920 HD)

Same format: dark charcoal grid background for every scene (incl. quiz + end screen), typewriter titles,
yellow ribbons, code editor + terminal with Run, punch-in cuts, big captions, mascot reactions.
Content: cinema seats (outer loop = rows, inner loop = seats) with a seat-by-seat cursor, print(i, j)
trace, star triangle pattern, recap (rows x cols), quiz: how many times is "Hi" printed? (no reveal).

Usage:  python3 edit26/build_ep19.py [--preview]
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
es.NEXT = "EP 20: SETS"

SCENES = [(0.0, "hook"), (4.0, "seats"), (10.0, "basic"), (19.0, "star"), (29.0, "recap"), (33.5, "quiz")]
END0 = 39.0
TOTAL = END0 + es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP19_Nested_Loops.mp4")
WORK = os.path.join(HERE, "work")
NEVER = 9999.0
ERR_T = -10.0
PAIRS = ["1 1", "1 2", "1 3", "2 1", "2 2", "2 3"]
STARS = ["*", "**", "***", "****"]

p4.CODE_FS = 40
p4.EDITOR = {
    "basic": {
        "code": [[("for i in range(1, 3):", 10.2)], [("    for j in range(1, 4):", 11.4)],
                 [("        print(i, j)", 12.6)]],
        "run": 13.8,
        "term": [("$ python main.py", GREY, 14.0, None)] + [(p, GREEN, 14.3 + 0.4 * k, None) for k, p in enumerate(PAIRS)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 14.3 + 0.4 * 5,
    },
    "star": {
        "code": [[("for i in range(1, 5):", 19.2)], [("    for j in range(i):", 20.3)],
                 [('        print("*", end="")', 21.2)], [("    print()", 22.5)]],
        "run": 23.4,
        "term": [("$ python main.py", GREY, 23.6, None)] + [(p, YEL, 24.0 + 0.45 * k, None) for k, p in enumerate(STARS)],
        "wait": (NEVER, NEVER), "enter": NEVER, "ok": 24.0 + 0.45 * 3,
    },
}
p4.CAPTIONS = [
    (0.3, "LOOP KE *ANDAR* LOOP?"), (2.0, "ISE KEHTE HAIN *NESTED* LOOP!"),
    (4.2, "SOCHO *CINEMA* KI SEATS"), (5.6, "*OUTER* LOOP = ROWS"), (7.0, "*INNER* LOOP = SEATS"),
    (8.6, "HAR ROW MEIN *SAARI* SEATS!"),
    (10.2, "*OUTER* LOOP: i"), (11.4, "*INNER* LOOP: j"), (13.8, "*RUN* KARO"), (14.4, "i = 1 → j CHALA *1, 2, 3*"),
    (15.6, "PHIR i = 2 → j *PHIR SE*!"), (16.9, "+2 × 3 = 6 BAAR!+"),
    (19.2, "AB *STAR* PATTERN!"), (20.3, "INNER LOOP *i* BAAR"), (21.4, "*end* = SAME LINE MEIN"),
    (22.5, "*print()* = NAYI LINE"), (23.4, "*RUN* KARO"), (24.2, "+TRIANGLE BAN GAYA!+"),
    (26.0, "*INTERVIEW* MEIN AATA HAI!"),
    (29.2, "*YAAD* RAKHO!"), (31.6, "*SCREENSHOT* LE LO!"),
    (33.7, "*QUIZ* TIME!"), (35.6, "KITNI BAAR *Hi* AAYEGA?"), (37.3, "*COMMENT* KARO!"),
]
p4.REACT = [(17.0, "6 baar!", GREEN), (25.6, "Wow!", GREEN)]
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
    p4.type_text(st, t, 0.15, "LOOP KE ANDAR", CAP, 92, WHITE, 540, 560, cps=16)
    p4.type_text(st, t, 1.0, "LOOP!", MONO, 200, ORANGE, 540, 780, cps=8)
    rb = mb.ribbon([("CODE SE STAR PATTERN!", (20, 20, 20), False)], mb.font(mb.BALOO, 56, "ExtraBold"), 104, 36,
                   fill=YEL)
    paste(st, rb, 540, 990, pop(t - 2.0), 1, -2)
    if "m" not in p4._C:
        p4._C["m"] = mb.mascot(380)
    paste(st, p4._C["m"], 800, 1230, pop(t - 2.4, 0.4))
    if t > 2.8:
        b = mb.bubble("Loop-ception!", mb.font(mb.BALOO, 46, "ExtraBold"), 22)
        paste(st, b, 460, 1140, pop(t - 2.8, 0.3))


SEAT_X = [330, 500, 670, 840]
SEAT_Y = [700, 860, 1020]
CUR0, CUR_STEP = 6.4, 0.24


def seat(col, lit):
    key = ("seat", col, lit)
    if key not in p4._C:
        im = Image.new("RGBA", (150, 140))
        d = ImageDraw.Draw(im)
        c = col if lit else (70, 74, 86)
        d.rounded_rectangle((20, 14, 130, 92), 18, fill=c)
        d.rounded_rectangle((12, 70, 138, 118), 14, fill=tuple(int(v * 0.8) for v in c))
        p4._C[key] = glow(im, col, 10) if lit else im
    return p4._C[key]


def draw_seats(st, t):
    n_lit = -1 if t < CUR0 else int((t - CUR0) / CUR_STEP)
    for r, y in enumerate(SEAT_Y):
        if t >= 4.3 + 0.15 * r:
            lab = p4.pill(f"row {r + 1}", YEL if n_lit >= r * 4 else GREY, 38)
            paste(st, lab, 140, y, pop(t - 4.3 - 0.15 * r, 0.3))
        for c, x in enumerate(SEAT_X):
            k = r * 4 + c
            if t >= 4.5 + 0.05 * k:
                lit = n_lit >= k
                cur = n_lit == k
                sc = pop(t - 4.5 - 0.05 * k, 0.25) * (1.12 if cur else 1)
                paste(st, seat(GREEN if lit else GREY, lit), x, y, sc)
                if t >= 7.0 and r == 0:
                    ImageDraw.Draw(st).text((x, y - 95), str(c + 1), font=mb.font(CAP, 40), fill=GREEN, anchor="mm")
    if t > 5.6:
        paste(st, p4.pill("OUTER = ROWS", YEL, 44), 300, 1200, pop(t - 5.6, 0.3))
    if t > 7.0:
        paste(st, p4.pill("INNER = SEATS", GREEN, 44), 780, 1200, pop(t - 7.0, 0.3))


RECAP = [(29.3, "outer loop", "ROWS", YEL), (29.9, "inner loop", "COLUMNS", GREEN),
         (30.5, "total", "ROWS × COLS", (78, 201, 176))]


def draw_recap(st, t):
    for k, (t0, code, lab, col) in enumerate(RECAP):
        y = 600 + k * 170
        p4.type_text(st, t, t0, code, MONO, 62, ORANGE, 70, y, cps=26, anchor="lm", cursor=False)
        p4.arrow(st, t, t0 + 0.4, 480, 585, y, RED, 0.25)
        if t > t0 + 0.6:
            ImageDraw.Draw(st).text((615, y), lab, font=mb.font(CAP, 56), fill=col, anchor="lm",
                                    stroke_width=3, stroke_fill=(0, 0, 0))
    if t > 31.6:
        paste(st, mb.outlined("SCREENSHOT LE LO!", mb.font(mb.BALOO, 70, "ExtraBold"), YEL, 8, (10, 10, 10), 6,
                              (150, 95, 0)), 540, 1180, pop(t - 31.6, 0.3), 1, -3)


QUIZ_CODE = [(34.3, "for i in range(3):"), (34.9, "    for j in range(2):"), (35.5, '        print("Hi")')]


def draw_quiz(st, t):
    p4.type_text(st, t, 33.6, "QUIZ TIME!", CAP, 110, YEL, 540, 420, cps=14, cursor=False)
    for k, (t0, txt) in enumerate(QUIZ_CODE):
        p4.type_text(st, t, t0, txt, MONO, 58, ORANGE, 130, 600 + k * 95, cps=24, anchor="lm",
                     cursor=k == len(QUIZ_CODE) - 1)
    if t > 36.2:
        paste(st, p4.pill("KITNI BAAR \"Hi\" ?", YEL, 56), 540, 940, pop(t - 36.2, 0.3))
    if t >= 36.6:
        s_ = 1 + 0.12 * math.sin((t - 36.6) * 8)
        paste(st, mb.outlined("?", mb.font(mb.BALOO, 170, "ExtraBold"), YEL, 8, (10, 10, 10), 6, (150, 95, 0)), 540,
              1140, pop(t - 36.6, 0.3) * s_)
    if t > 37.3:
        rb = mb.ribbon([("COMMENT MEIN BATAO!", (20, 20, 20), False)], mb.font(mb.BALOO, 60, "ExtraBold"), 104, 36,
                       fill=YEL)
        paste(st, rb, 540, 1330, pop(t - 37.3), 1, 2)


def editor_focus(t, name):
    """like EP 04 but without the typing zoom, so the long list line stays inside the frame"""
    run = p4.EDITOR[name]["run"]
    q = ease((t - run + 0.2) / 0.5) if t >= run - 0.2 else 0.0
    return 860 + (p4.TERM_Y0 + 60 - 860) * q, 1.0


GRID = {"hook": draw_hook, "seats": draw_seats, "recap": draw_recap, "quiz": draw_quiz}


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
    pill_t = p4.pill("PYTHON KI PATHSHALA • EP 19", (0, 0, 0, 150), 28, YEL)
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
    tc(buf, 0.15, len("LOOP KE ANDAR"), 16, 1, 0.4)
    tc(buf, 1.0, len("LOOP!"), 8, 20, 0.5)
    for t0 in (2.0, 2.4, 2.8):
        P(buf, fx.pop(), t0, 0.5)
    for r in range(3):
        P(buf, fx.pop(), 4.3 + 0.15 * r, 0.4)
    for k in range(12):
        P(buf, fx.pop(), 4.5 + 0.05 * k, 0.15)
        P(buf, bs.note_pop(523.3 * 2 ** ((k % 4) * 2 / 12) * (1 + 0.25 * (k // 4))), CUR0 + CUR_STEP * k, 0.3)
    P(buf, fx.pop(), 5.6, 0.55)
    P(buf, fx.pop(), 7.0, 0.55)
    for name, cfg in p4.EDITOR.items():
        for line in cfg["code"]:
            for s_, t0 in line:
                if t0 is not None:
                    tc(buf, t0, len(s_.strip()), p4.CODE_CPS, int(t0 * 7), 0.35)
        P(buf, bs.mouse_click(), cfg["run"], 0.9)
        for k, (txt, col, t0, user) in enumerate(cfg["term"]):
            P(buf, bs.note_pop(700 * 2 ** (k * 2 / 12)), t0, 0.3)
        P(buf, fx.ding(), cfg["ok"], 0.5)
        P(buf, bs.note_pop(1046.5), cfg["ok"] + 0.05, 0.3)
    P(buf, p4.fx.boom()[: int(0.5 * SR)], 16.9, 0.4)
    for t0, code, _lab, _col in RECAP:
        tc(buf, t0, len(code), 26, int(t0 * 5), 0.3)
        P(buf, fx.whoosh(0.2, int(t0 * 9)), t0 + 0.4, 0.3)
        P(buf, fx.pop(), t0 + 0.6, 0.45)
    P(buf, fx.pop(), 31.6, 0.6)
    P(buf, bs.thud(), 31.6, 0.4)
    P(buf, fx.riser(0.6), 33.0, 0.35)
    P(buf, fx.boom(), 33.6, 0.6)
    for t0, txt in QUIZ_CODE:
        tc(buf, t0, len(txt.strip()), 24, int(t0 * 11), 0.4)
    P(buf, fx.pop(), 36.2, 0.55)
    P(buf, fx.pop(), 36.6, 0.6)
    P(buf, bs.thud(), 36.6, 0.4)
    P(buf, fx.pop(), 37.3, 0.6)
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
