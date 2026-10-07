#!/usr/bin/env python3
"""45 s vertical short: INPUT_PULLUP / floating pin (Arduino · Code ka Raaz #4).

Same Swiggy-style system as edit3 (STEP labels, keyword wheels, light leaks, result card),
plus: a recreated Tinkercad screen (code editor, Serial Monitor, Arduino + push-button),
burned-in script subtitles with yellow keywords, glitch hits on the ghost presses,
a top progress bar and a loop cut back to the hook.

Timeline (30 fps):
  A    0-119  3D hook: button nobody touches, "PRESSED?!" flickers          [scene3d.py]
  B  120-359  STEP-1 FLOATING PIN: sim screen, pinMode(2, INPUT), random 0/1
  C  360-659  3D: lone pin hit by noise waves, value jumps 0/1               [scene3d.py]
  D  660-809  3D: pull-up spring snaps it to 5V, value locks at 1           [scene3d.py]
  E  810-1019 STEP-2 INPUT_PULLUP: code edited, steady 1, press -> 0
  F 1020-1229 white result card (cross / tick)
  G 1230-1349 Follow card, last 12 frames cut back to the hook (loop)
Usage: python3 edit4/build_short.py [audio] [video]
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "edit"))
import importlib.util  # noqa: E402
import build_edit as fx  # noqa: E402
_spec = importlib.util.spec_from_file_location("e3_build_short", os.path.join(ROOT, "edit3", "build_short.py"))
e3 = importlib.util.module_from_spec(_spec)  # edit3: music, sfx voices, step labels, wheels, light leak
_spec.loader.exec_module(e3)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "input-pullup-SHORT.mp4")
RAW_ARD = os.path.join(ROOT, "millis() and delay()  in Arduino programming | arduino programming tutorial.mp4")
W, H, FPS, SR = 1080, 1920, 30, 48000
N = 1350
SEG = {"A": (0, 120), "B": (120, 360), "C": (360, 660), "D": (660, 810), "E": (810, 1020),
       "F": (1020, 1230), "G": (1230, 1350)}
ATTACH = 705
PRESS = (930, 975)       # E: button held down (absolute frames)
TYPE = (835, 860)        # E: "_PULLUP" typed
YEL, WHT, RED, GRN = e3.YEL, e3.WHT, e3.RED, e3.GRN
BOLD, MONT = e3.BOLD, e3.MONT
MONO_R = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

STEPS = {"A": ("ARDUINO", "Ghost Button?!", 34),
         "B": ("STEP-1", "FLOATING PIN", 8),
         "E": ("STEP-2", "INPUT_PULLUP", 8)}
WHEELS = {"B": (["Random 0/1", "Bina chhue", "Confused pin"], 80),
          "C": (["Kisi se connected nahi", "Hawa ki noise", "Random value"], 100),
          "D": (["5V se joda", "Pull-up resistor", "STABLE"], 50)}
# burned-in subtitles of the voiceover script: (start s, end s, text); CAPS words turn yellow
SUBS = [(0.0, 2.0, "Button dabaya hi nahi…"), (2.0, 4.0, "phir bhi PRESSED?!"),
        (4.0, 8.0, "Serial Monitor dekho: 0, 1, 1, 0…"), (8.0, 10.3, "bina chhue RANDOM values!"),
        (10.3, 12.0, "Ise kehte hain FLOATING pin"),
        (12.0, 16.5, "Button open = pin kisi se CONNECTED nahi"), (16.5, 19.5, "Hawa ki NOISE, aapki ungli…"),
        (19.5, 22.0, "sab use 0 ya 1 bana dete hain"),
        (22.0, 25.0, "Fix: pin ko 5V ki taraf kheencho"), (25.0, 27.0, "Yahi hai PULL-UP resistor!"),
        (27.0, 29.0, "Code mein bas likho:"), (29.0, 31.5, "pinMode(2, INPUT_PULLUP)"),
        (31.5, 34.0, "Bina dabaye HIGH, dabao toh LOW"),
        (34.0, 37.0, "Ulta lagta hai…"), (37.0, 41.0, "par ekdum STABLE!"),
        (41.0, 43.5, "Follow karo, warna phir bolega…"), (43.5, 45.0, "button dabaya hi nahi…")]

# share timeline/caption tables with the edit3 helpers
e3.SEG, e3.STEPS, e3.WHEELS, e3.N = SEG, STEPS, WHEELS, N
ease, font, light_leak = e3.ease, e3.font, e3.light_leak


def seg_of(f):
    for k_, (a, b) in SEG.items():
        if a <= f < b:
            return k_, f - a
    return "G", f - SEG["G"][0]


# ================================================================== audio
def glitch_burst(seed, dur=0.12):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    x = np.repeat(x[::30], 30)[:n]
    tone = fx.signal.square(2 * np.pi * rng.uniform(300, 900) * np.arange(n) / SR)
    gate = (rng.random(n // 400 + 1) > 0.35).repeat(400)[:n]
    return (x * 0.5 + tone * 0.3) * gate * 0.5


def boing(dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 180 + 90 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 2.5) + 300 * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8) * 0.45


def btn_click(down=True):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 11 if down else 12), "bandpass", [1500, 6000]) * np.exp(-t * 120)
    return x + np.sin(2 * np.pi * (900 if down else 1300) * t) * np.exp(-t * 90) * 0.4


def sfx_track(total):
    n = int(total * SR)
    buf = np.zeros(n)
    P = fx.place
    t = lambda f: f / FPS  # noqa: E731
    for i, key in enumerate(["B", "C", "D", "E", "F", "G"]):
        P(buf, fx.whoosh(0.4, i), max(0, t(SEG[key][0]) - 0.28), 0.5)
    for f in GLITCH_FRAMES:                                     # ghost-press glitches in the hook / loop
        P(buf, glitch_burst(f), t(f), 0.55)
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.6)
    for seg, (_, _, off) in STEPS.items():
        a = SEG[seg][0] + off
        P(buf, e3.sparkle(hash(seg) % 97), t(a), 0.45)
        for j in range(6):
            P(buf, e3.click(), t(a + 4 + j * 2), 0.22)
    for seg, (words, every) in WHEELS.items():
        every = max(every, (SEG[seg][1] - SEG[seg][0]) // len(words))
        for i in range(1, len(words)):
            P(buf, e3.sparkle(i + 7), t(SEG[seg][0] + i * every), 0.3)
    for f in range(SEG["B"][0] + 20, SEG["B"][1], 6):           # serial monitor lines (random 0/1)
        P(buf, e3.tick(rand01(f) == 1), t(f), 0.18)
    hiss = fx.filt(fx.noise(int(t(SEG["C"][1] - SEG["C"][0]) * SR), 21), "bandpass", [2000, 8000])
    hiss *= np.minimum(1, np.linspace(0, 6, len(hiss))) * np.minimum(1, np.linspace(6, 0, len(hiss)))
    P(buf, hiss, t(SEG["C"][0]), 0.06)                          # static under the floating-pin shot
    P(buf, boing(), t(SEG["D"][0] + 10), 0.6)                   # spring stretches to 5V
    P(buf, fx.pop(), t(ATTACH), 0.6)
    P(buf, e3.chime(), t(ATTACH + 10), 0.35)
    for j, f in enumerate(range(TYPE[0], TYPE[1], 4)):          # typing _PULLUP
        P(buf, e3.click(), t(f), 0.4)
    P(buf, btn_click(True), t(PRESS[0]), 0.7)
    P(buf, btn_click(False), t(PRESS[1]), 0.6)
    P(buf, e3.soft_buzz(), t(SEG["F"][0] + 18), 0.6)
    P(buf, e3.chime(), t(SEG["F"][0] + 70), 0.6)
    P(buf, fx.ding(), t(SEG["G"][0] + 6), 0.4)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), e3.music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    voice = os.path.join(WORK, "voice.wav")
    tail = f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]"
    ins = ["-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav")]
    if os.path.exists(voice):
        ins += ["-i", voice]
        fc = ("[2:a]highpass=f=85,equalizer=f=3200:t=q:w=1.2:g=3,"
              "acompressor=threshold=-20dB:ratio=3:attack=4:release=70:makeup=2,"
              "loudnorm=I=-16:TP=-2:LRA=6,aformat=sample_rates=48000:channel_layouts=stereo,asplit[vox][key];"
              "[0:a]loudnorm=I=-21:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
              "[mus][key]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=260[musd];"
              "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.6[s];"
              "[vox][musd][s]amix=inputs=3:normalize=0," + tail)
    else:
        fc = ("[0:a]loudnorm=I=-18:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
              "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.85[s];"
              "[m][s]amix=inputs=2:normalize=0," + tail)
    fx.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[out]",
            "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== helpers
def rand01(f):
    return int((f * 2654435761 >> 7) % 7 > 3)


_rng = np.random.default_rng(7)
GLITCH_FRAMES = sorted(set([int(x) for x in _rng.integers(6, 118, 9)] + [N - 12, N - 7]))


def glitch(frame, f, amt=1.0):
    rng = np.random.default_rng(f)
    out = frame.copy()
    s = int(18 * amt)
    out[..., 0] = np.roll(frame[..., 0], s, axis=1)
    out[..., 2] = np.roll(frame[..., 2], -s, axis=1)
    for _ in range(6):
        y = int(rng.integers(0, H - 80))
        h = int(rng.integers(20, 90))
        out[y:y + h] = np.roll(out[y:y + h], int(rng.integers(-60, 60) * amt), axis=1)
    return out


def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    return cv2.addWeighted(im, 1.2, cv2.GaussianBlur(im, (0, 0), 1.6), -0.2, 0)


# ================================================================== recreated Tinkercad screen
ARD_IMG = None


def arduino_img():
    global ARD_IMG
    if ARD_IMG is None:
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", "300", "-i", RAW_ARD, "-frames:v", "1",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        fr = np.frombuffer(p.stdout, np.uint8).reshape(720, 1280, 3)
        ARD_IMG = Image.fromarray(fr[290:555, 215:560].copy())
    return ARD_IMG


C_KEY, C_FN, C_NUM, C_TXT, C_LN = (163, 62, 162), (0, 112, 192), (0, 140, 140), (40, 40, 48), (160, 160, 170)


def code_lines(seg, f):
    mode = "INPUT"
    if seg == "E":
        n = int(np.clip((f - TYPE[0]) / (TYPE[1] - TYPE[0]), 0, 1) * len("_PULLUP"))
        mode = "INPUT" + "_PULLUP"[:n]
    return [[("void ", C_KEY), ("setup", C_FN), ("()", C_TXT)], [("{", C_TXT)],
            [("  Serial", C_FN), (".", C_TXT), ("begin", C_FN), ("(", C_TXT), ("9600", C_NUM), (");", C_TXT)],
            [("  pinMode", C_FN), ("(", C_TXT), ("2", C_NUM), (", ", C_TXT), (mode, C_NUM), (");", C_TXT)],
            [("}", C_TXT)], [],
            [("void ", C_KEY), ("loop", C_FN), ("()", C_TXT)], [("{", C_TXT)],
            [("  Serial", C_FN), (".", C_TXT), ("println", C_FN), ("(", C_TXT), ("digitalRead", C_FN),
             ("(", C_TXT), ("2", C_NUM), ("));", C_TXT)], [("}", C_TXT)]]


def monitor_lines(seg, f):
    if seg == "B":
        n = max(0, (f - SEG["B"][0] - 20) // 6)
        return [str(rand01(SEG["B"][0] + 20 + i * 6)) for i in range(max(0, n - 7), n)]
    start = TYPE[1] + 15
    if f < start:
        return []
    n = (f - start) // 5
    out = []
    for i in range(max(0, n - 7), n):
        ff = start + i * 5
        out.append("0" if PRESS[0] <= ff < PRESS[1] else "1")
    return out


def sim_panel(seg, f):
    pw, ph = 1000, 1000
    im = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # title bar, Tinkercad-like
    d.rectangle((0, 0, pw, 64), fill=(245, 246, 248))
    for i, c in enumerate(("#ef4444", "#3b82f6", "#22c55e", "#f59e0b")):
        d.rectangle((18 + (i % 2) * 18, 12 + (i // 2) * 18, 32 + (i % 2) * 18, 26 + (i // 2) * 18), fill=c)
    d.text((70, 32), "Tinkercad · Push Button", font=font(BOLD, 28), fill=(60, 60, 70), anchor="lm")
    sim_on = f >= SEG[seg][0] + 6
    d.rounded_rectangle((pw - 260, 12, pw - 20, 52), 8, fill=(34, 197, 94) if sim_on else (59, 130, 246))
    d.text((pw - 140, 32), "Stop Simulation" if sim_on else "Start Simulation", font=font(BOLD, 22), fill=WHT, anchor="mm")
    # circuit area
    d.rectangle((0, 64, pw, 330), fill=(250, 250, 252))
    ard = arduino_img().resize((330, 253))
    im.paste(ard, (60, 72))
    bx, by = 690, 150
    pressed = seg == "E" and PRESS[0] <= f < PRESS[1]
    d.rounded_rectangle((bx, by, bx + 130, by + 130), 10, fill=(40, 40, 46))
    cap = 48 if not pressed else 42
    d.ellipse((bx + 65 - cap, by + 65 - cap, bx + 65 + cap, by + 65 + cap),
              fill=(200, 30, 30) if not pressed else (140, 20, 20), outline=(20, 20, 20), width=3)
    d.line((bx, by + 40, 330, 112), fill=(30, 110, 230), width=7)          # to pin 2
    d.line((bx, by + 95, 300, 112), fill=(20, 20, 20), width=7)            # to GND
    d.text((520, 90), "PIN 2", font=font(BOLD, 24), fill=(30, 110, 230))
    if seg == "B":
        d.text((520, 300), "no resistor!", font=font(BOLD, 24), fill=(220, 40, 40))
    if pressed:  # hand cursor
        hx, hy = bx + 95, by + 95
        d.polygon([(hx, hy), (hx + 34, hy + 52), (hx + 16, hy + 50), (hx + 8, hy + 70)], fill=(20, 20, 20))
    # code editor
    ey = 336
    d.rectangle((0, ey, pw, ey + 40), fill=(245, 246, 248))
    d.text((20, ey + 20), "Text  ▾", font=font(BOLD, 24), fill=(70, 70, 80), anchor="lm")
    d.text((pw - 20, ey + 20), "1 (Arduino Uno R3)", font=font(BOLD, 22), fill=(70, 70, 80), anchor="rm")
    fm = font(MONO_R, 33)
    lh = 40
    for i, line in enumerate(code_lines(seg, f)):
        y = ey + 52 + i * lh
        d.text((50, y), str(i + 1), font=font(MONO_R, 26), fill=C_LN, anchor="ra")
        x = 70
        for tok, col in line:
            d.text((x, y), tok, font=fm, fill=col)
            x += d.textlength(tok, font=fm)
        if seg == "E" and i == 3 and TYPE[0] <= f < TYPE[1] + 10 and (f // 8) % 2 == 0:
            d.line((x + 2, y, x + 2, y + 34), fill=(20, 20, 20), width=3)
    # serial monitor
    my = 790
    d.rectangle((0, my, pw, my + 44), fill=(235, 236, 240))
    d.text((20, my + 22), "▣  Serial Monitor", font=font(BOLD, 26), fill=(60, 60, 70), anchor="lm")
    for i, v in enumerate(monitor_lines(seg, f)):
        col = (220, 40, 40) if seg == "B" else ((30, 160, 80) if v == "1" else (37, 99, 235))
        d.text((24, my + 52 + i * 21), v, font=font(MONO_B, 19), fill=col)
    big = monitor_lines(seg, f)
    if big:
        v = big[-1]
        col = (220, 40, 40) if seg == "B" else ((30, 160, 80) if v == "1" else (37, 99, 235))
        d.text((pw - 120, my + 100), v, font=font(MONO_B, 110), fill=col, anchor="mm")
        if seg == "E":
            d.text((pw - 120, my + 180), "HIGH" if v == "1" else "LOW (pressed)", font=font(BOLD, 24), fill=col, anchor="mm")
    return np.array(im)


def screen_frame(seg, local):
    f = SEG[seg][0] + local
    panel = sim_panel(seg, f)
    z = 1.0 + 0.05 * ease(local / (SEG[seg][1] - SEG[seg][0]))
    pw = int(1000 * z)
    panel = cv2.resize(panel, (pw, pw), interpolation=cv2.INTER_CUBIC)
    frame = e3.background()
    x0, y0 = (W - pw) // 2, 330 - (pw - 1000) // 2
    sh = np.zeros((H, W), np.float32)
    cv2.rectangle(sh, (x0 + 10, y0 + 24), (x0 + pw + 10, y0 + pw + 24), 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 24)[..., None] * 0.6
    frame = (frame * (1 - sh)).astype(np.uint8)
    m = e3.rounded(panel)[..., None] / 255.0
    frame[y0:y0 + pw, x0:x0 + pw] = (panel * m + frame[y0:y0 + pw, x0:x0 + pw] * (1 - m)).astype(np.uint8)
    s = pw / 1000
    u = ease((local - 18) / 12)                                     # highlight pinMode line
    if u > 0:
        ly = y0 + int((336 + 52 + 3 * 40 - 4) * s)
        cv2.rectangle(frame, (x0 + int(62 * s), ly), (x0 + int((62 + 560 * u) * s), ly + int(44 * s)), YEL, 6, cv2.LINE_AA)
    v = ease((local - 40) / 12)                                     # arrow to the monitor
    if v > 0:
        ax, ay0, ay1 = x0 + int(700 * s), y0 + int(560 * s), y0 + int(800 * s)
        cv2.arrowedLine(frame, (ax, ay0), (ax, int(ay0 + (ay1 - ay0) * v)), YEL, 7, cv2.LINE_AA, tipLength=0.2)
    return frame


# ================================================================== cards / overlays
def card_frame(local):
    im = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(im)
    rows = [(640, "pinMode(2, INPUT)", "Floating = RANDOM 0/1", RED, "x", 10),
            (1200, "INPUT_PULLUP", "STABLE: HIGH / dabao = LOW", GRN, "v", 62)]
    for cy, code, sub, col, kind, start in rows:
        u = ease((local - start) / 12)
        r = int(120 * u)
        if r > 2:
            d.ellipse((W // 2 - r, cy - 150 - r, W // 2 + r, cy - 150 + r), fill=col)
        w = ease((local - start - 10) / 10)
        if w > 0:
            c0 = (W // 2, cy - 150)
            if kind == "x":
                L = 55 * w
                d.line((c0[0] - L, c0[1] - L, c0[0] + L, c0[1] + L), fill=WHT, width=22)
                d.line((c0[0] + L, c0[1] - L, c0[0] - L, c0[1] + L), fill=WHT, width=22)
            else:
                p0, p1, p2 = (c0[0] - 60, c0[1] + 5), (c0[0] - 15, c0[1] + 50), (c0[0] + 65, c0[1] - 45)
                s1 = min(1, w * 2)
                d.line((*p0, p0[0] + (p1[0] - p0[0]) * s1, p0[1] + (p1[1] - p0[1]) * s1), fill=WHT, width=24)
                if w > 0.5:
                    s2 = (w - 0.5) * 2
                    d.line((*p1, p1[0] + (p2[0] - p1[0]) * s2, p1[1] + (p2[1] - p1[1]) * s2), fill=WHT, width=24)
        a = ease((local - start - 14) / 10)
        if a > 0:
            tc = tuple(int(250 + (c - 250) * a) for c in (30, 30, 40))
            sc_ = tuple(int(250 + (c - 250) * a) for c in col)
            d.text((W // 2, cy + 40), code, font=font(MONO_B, 74), fill=tc, anchor="mm")
            d.text((W // 2, cy + 140), sub, font=font(BOLD, 54), fill=sc_, anchor="mm")
    return np.array(im)


def cta_frame(local):
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([120, 50, 210]), np.array([30, 150, 160])
    im = Image.fromarray((top * (1 - y) + bot * y).repeat(W, axis=1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    u = ease(local / 12)
    d.text((W // 2, 560), "ARDUINO · CODE KA RAAZ #4", font=font(MONT, 46), fill=(255, 210, 200), anchor="mm")
    bw = int(860 * u)
    if bw > 40:
        d.rounded_rectangle((W // 2 - bw // 2, 820, W // 2 + bw // 2, 990), 85, fill=YEL)
    if u > 0.9:
        d.text((W // 2, 905), "FOLLOW — roz 1 IoT concept", font=font(MONT, 52), fill=(20, 20, 30), anchor="mm")
    a = ease((local - 10) / 10)
    if a > 0:
        d.text((W // 2, 1130), "@The IOT Engineer", font=font(MONT, 70), fill=WHT, anchor="mm")
    return np.array(im)


SUB_FONT = None


def subtitle(frame, f):
    t = f / FPS
    cur = next(((a, b, s) for a, b, s in SUBS if a <= t < b), None)
    if not cur:
        return
    a, _, text = cur
    age = t - a
    sc = 0.75 + 0.25 * ease(age / 0.15) + 0.06 * np.sin(min(1, age / 0.15) * np.pi)
    size = int(66 * sc)
    fnt = font(BOLD, size)
    words = text.split(" ")
    im = Image.fromarray(frame)
    d = ImageDraw.Draw(im)
    widths = [d.textlength(w_ + " ", font=fnt) for w_ in words]
    lines, cur_l, cur_w = [], [], 0
    for w_, wd in zip(words, widths):
        if cur_w + wd > 980 and cur_l:
            lines.append(cur_l)
            cur_l, cur_w = [], 0
        cur_l.append((w_, wd))
        cur_w += wd
    lines.append(cur_l)
    y = 1745 - (len(lines) - 1) * size * 0.6
    for ln in lines:
        x = W / 2 - sum(wd for _, wd in ln) / 2
        for w_, wd in ln:
            core = w_.strip("…!?,.:")
            hot = (core.isupper() and len(core) > 1) or any(ch.isdigit() for ch in core) or "INPUT" in core
            d.text((x, y), w_, font=fnt, fill=YEL if hot else WHT, anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0))
            x += wd
        y += size * 1.15
    frame[:] = np.array(im)


def progress_bar(frame, f):
    w = int(W * (f + 1) / N)
    frame[0:10, :] = (frame[0:10, :] * 0.4).astype(np.uint8)
    frame[0:10, :w] = YEL


# ================================================================== assemble
def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "9M", "-bufsize", "18M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    gl = set(GLITCH_FRAMES)
    for f in range(N):
        seg, local = seg_of(f)
        if seg == "G" and f >= N - 12:            # loop: cut back to the flickering hook
            fr = load3d(local - (SEG["G"][1] - SEG["G"][0] - 12))
        elif seg in ("A", "C", "D"):
            fr = load3d(f)
        elif seg in ("B", "E"):
            fr = screen_frame(seg, local)
        elif seg == "F":
            fr = card_frame(local)
        else:
            fr = cta_frame(local)
        if seg in STEPS:
            e3.step_label(fr, seg, local, y=1490)
        if seg in WHEELS:
            e3.keyword_wheel(fr, seg, local)
        if f in gl or (f - 1) in gl:
            fr = glitch(fr, f, 1.0 if f in gl else 0.5)
        if seg == "D" and 0 <= f - ATTACH < 8:   # snap punch-in when the spring locks
            k = 1 + 0.06 * (1 - (f - ATTACH) / 8)
            M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, k)
            fr = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)
        for key in ("B", "C", "D", "E", "F", "G"):
            d = f - SEG[key][0]
            if -6 <= d < 6:
                fr = light_leak(fr, 1 - abs(d + 0.5) / 6.5)
        subtitle(fr, f)
        progress_bar(fr, f)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 150 == 0:
            print(f"  frame {f}/{N}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["audio", "video"]
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
