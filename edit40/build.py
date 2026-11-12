#!/usr/bin/env python3
"""JARVIS Part 2 (20 s): starts with the user's REAL self-balancing robot clip (PID OFF = falls, PID ON =
stands), then a 2D neon animation in the JARVIS series style shows the voice commands of the Part 2 code
('aage chalo', 'ghoom jao', 'dance karo'): a 2D model of the user's robot (blue chassis, yellow wheels, black
battery box) balances, drives, spins and dances while the JARVIS orb listens / answers. Clear step headers,
big speaker subtitles, CTA + Part 3 tease, then the Like / Share / big SUBSCRIBE page.
Usage: python3 edit40/build.py [preview FRAMES OUT]"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


b31 = _load("b31", os.path.join(ROOT, "edit31", "build.py"))
j2d = _load("j2d", os.path.join(ROOT, "edit38", "jarvis2d.py"))
b = b31.b
fx, e5, font, txt, pop_s, ease, head = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head
MONT, BOLD, INK, WHT, YEL, CYAN, GRN = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN
PINK = (255, 90, 200)
W, H, FPS, SR = 1080, 1920, 24, 48000
SRC = os.path.join(HERE, "work", "src")
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-jarvis-part2-voice-robot-SHORT.mp4")
REAL = list(range(10, 46)) + list(range(150, 186))     # real clip: falls (OFF), then stands (ON)
S_INTRO = len(REAL)                                   # 72
S_FWD, S_SPIN, S_DANCE, S_CTA = 120, 210, 300, 390
CLIP = 408
OUTRO = 72
TOTAL = CLIP + OUTRO                                  # 480 = 20 s
# (scene start, user line, jarvis line, jarvis emoji, user_at, reply_at, move_from, move_to)
CMDS = [(S_FWD, "Jarvis, aage chalo", "Ji Boss! Aage chal raha hoon", "🚀", S_FWD + 4, S_FWD + 34, S_FWD + 38, S_FWD + 84),
        (S_SPIN, "Jarvis, ghoom jao", "Ji Boss! Ghoom raha hoon", "🌀", S_SPIN + 4, S_SPIN + 30, S_SPIN + 34, S_SPIN + 86),
        (S_DANCE, "Jarvis, dance karo", "Boss, ye mera best move hai", "😎", S_DANCE + 4, S_DANCE + 30, S_DANCE + 34, S_DANCE + 88)]
FLOOR = 1150


# ------------------------------------------------------------------ real clip
def real_frame(f):
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, f"{REAL[f]:04d}.png")), cv2.COLOR_BGR2RGB)
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4)


# ------------------------------------------------------------------ 2D robot (side view, like the user's build)
def robot_state(f):
    """x position, lean (deg), wheel angle, spin phase (0..1 of a turn), dance."""
    x, lean, wheel, spin = 470.0, 0.0, 0.0, 0.0
    wob = 1.2 * math.sin(f * 0.35)                       # tiny balancing wobble
    c0 = CMDS[0]
    u = ease((f - c0[6]) / (c0[7] - c0[6]))
    x = 470 + 330 * u                                    # drives forward (to the right)
    if c0[6] <= f < c0[7]:
        lean = 7 * math.sin(math.pi * (f - c0[6]) / (c0[7] - c0[6]))
    wheel = (x - 470) / 50.0
    c1 = CMDS[1]
    if f >= c1[6]:
        spin = ease((f - c1[6]) / (c1[7] - c1[6]))
    c2 = CMDS[2]
    dance = 0.0
    if c2[6] <= f < c2[7]:
        k = (f - c2[6]) / FPS
        dance = 1.0
        x += 60 * math.sin(k * 2 * math.pi * 1.3)
        lean = 10 * math.sin(k * 2 * math.pi * 1.3)
        wheel += 0.9 * math.sin(k * 2 * math.pi * 1.3)
    return x, lean + wob, wheel, spin, dance


def draw_robot(lay, f):
    x, lean, wheel, spin, dance = robot_state(f)
    S = 1.45
    rw, rh = int(260 * S), int(360 * S)
    img = Image.new("RGBA", (rw, rh))
    d = ImageDraw.Draw(img)
    cx, wy, R = rw / 2, rh - 60 * S, 58 * S                # wheel centre at the bottom
    face = abs(math.cos(spin * 2 * math.pi)) if 0 < spin < 1 else 1.0
    bw = 120 * S * (0.45 + 0.55 * face)
    d.rounded_rectangle((cx - bw / 2, wy - 250 * S, cx + bw / 2, wy - 18 * S), 14 * S, fill=(52, 84, 120, 255), outline=(30, 50, 80, 255), width=int(4 * S))
    d.rounded_rectangle((cx - bw / 2 - 6 * S, wy - 290 * S, cx + bw / 2 + 6 * S, wy - 240 * S), 8 * S, fill=(25, 25, 28, 255))
    d.rectangle((cx - bw / 2 + 8 * S, wy - 150 * S, cx + bw / 2 - 8 * S, wy - 115 * S), fill=(235, 235, 230, 255))
    d.rectangle((cx - bw / 2 + 14 * S, wy - 148 * S, cx - bw / 2 + 50 * S, wy - 132 * S), fill=(190, 30, 40, 255))
    led_on = (f // 4) % 2 == 0
    d.ellipse((cx + bw / 2 - 28 * S, wy - 146 * S, cx + bw / 2 - 16 * S, wy - 134 * S), fill=(80, 255, 120, 255) if led_on else (20, 80, 40, 255))
    wx = cx + (bw / 2 - 10 * S if spin < 0.5 or spin >= 1 else -bw / 2 + 10 * S) * (1 - face) * 0.0
    d.ellipse((wx - R, wy - R, wx + R, wy + R), fill=(25, 25, 28, 255))                      # tyre
    d.ellipse((wx - R * 0.62, wy - R * 0.62, wx + R * 0.62, wy + R * 0.62), fill=(250, 210, 30, 255))
    for k in range(5):                                                                       # rotating spokes
        a = wheel + k * 2 * math.pi / 5
        d.line((wx, wy, wx + R * 0.55 * math.cos(a), wy + R * 0.55 * math.sin(a)), fill=(200, 160, 10, 255), width=int(7 * S))
    d.ellipse((wx - R * 0.15, wy - R * 0.15, wx + R * 0.15, wy + R * 0.15), fill=(120, 90, 10, 255))
    img = img.rotate(-lean, center=(cx, wy), resample=Image.BICUBIC)
    sh = Image.new("RGBA", lay.size)                                                          # floor shadow
    ImageDraw.Draw(sh).ellipse((x - 110, FLOOR - 14, x + 110, FLOOR + 14), fill=(0, 0, 0, 160))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    lay.alpha_composite(img, (int(x - cx), int(FLOOR - wy - R + 4)))
    if dance:                                                                                # music notes
        for k in range(3):
            ph = ((f * 0.04 + k / 3) % 1)
            lay.alpha_composite(e5.emoji("🎵", 60), (int(x - 150 + k * 120), int(FLOOR - 600 - ph * 140)))
    if 0 < spin < 1:
        g = Image.new("RGBA", lay.size)
        gd = ImageDraw.Draw(g)
        for k in range(3):
            r = 230 + k * 30
            a0 = spin * 720 + k * 120
            gd.arc((x - r * 0.75, FLOOR - 300 - r * 0.2, x + r * 0.75, FLOOR - 300 + r * 0.2), a0, a0 + 120, fill=CYAN + (220,), width=10)
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(3)))


def floor(lay):
    d = ImageDraw.Draw(lay)
    for k in range(14):                                                                      # neon floor grid
        y = FLOOR + 6 + k * k * 4
        if y > H:
            break
        d.line((0, y, W, y), fill=(60, 200, 255, max(20, 120 - k * 8)), width=2)
    for k in range(-8, 9):
        d.line((W / 2 + k * 40, FLOOR + 6, W / 2 + k * 260, H), fill=(60, 200, 255, 60), width=2)
    d.line((0, FLOOR + 4, W, FLOOR + 4), fill=(60, 220, 255, 255), width=4)


# ------------------------------------------------------------------ text
def subtitle(lay, f):
    for (s0, ut, jt, je, ua, ra, m0, m1) in CMDS:
        if ua <= f < ra:
            who, line, col, em, f0 = "Tum", ut, (37, 211, 102), "🧑", ua
        elif ra <= f < (s0 + 90 if s0 != S_DANCE else S_CTA):
            who, line, col, em, f0 = "Jarvis", jt, (60, 200, 255), "🤖", ra
        else:
            continue
        u = pop_s(f - f0, 5)
        if u <= 0.05:
            return
        d = ImageDraw.Draw(lay)
        fs = 50
        text = f"{who}: {line}"
        while d.textlength(text, font=font(MONT, fs)) > 820 and fs > 34:
            fs -= 2
        fnt = font(MONT, fs)
        tw = d.textlength(text, font=fnt) + 150 + (60 if who == "Jarvis" else 0)
        x0, y0 = W / 2 - tw / 2 * u, 1190
        sh = Image.new("RGBA", (W, H))
        ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, W - x0, y0 + 120), 50, fill=(0, 0, 0, 160))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((x0, y0, W - x0, y0 + 110), 50, fill=(10, 14, 22, 240), outline=col + (255,), width=6)
        if u > 0.9:
            lay.alpha_composite(e5.emoji(em, 64), (int(x0 + 28), int(y0 + 23)))
            d.text((x0 + 110, y0 + 55), who + ":", font=fnt, fill=col, anchor="lm")
            wl = d.textlength(who + ": ", font=fnt)
            d.text((x0 + 110 + wl, y0 + 55), line, font=fnt, fill=WHT, anchor="lm")
            if who == "Jarvis":
                lay.alpha_composite(e5.emoji(je, 54), (int(x0 + 110 + wl + d.textlength(line, font=fnt) + 10), int(y0 + 28)))
        return


def header(lay, f):
    g = Image.new("RGBA", (W, H))
    ImageDraw.Draw(g).rectangle((0, 0, W, 350), fill=(4, 8, 14, 225))
    lay.alpha_composite(g)
    for y in range(350, 400):
        ImageDraw.Draw(lay).line((0, y, W, y), fill=(4, 8, 14, int(225 * (1 - (y - 350) / 50))))
    d = ImageDraw.Draw(lay)
    if f < 36:
        head(lay, d, "JARVIS Part 2", 180, 92, CYAN, "🤖", 1 + 0.03 * math.sin(f * 0.6))
        head(lay, d, "PID OFF = Gira", 285, 70, (255, 90, 90), "💥", pop_s(f, 5))
    elif f < S_INTRO:
        head(lay, d, "JARVIS Part 2", 180, 92, CYAN, "🤖")
        head(lay, d, "PID ON = Khada", 285, 70, GRN, "✅", pop_s(f - 36, 5))
    elif f < S_FWD:
        head(lay, d, "Ab Jarvis isko chalayega!", 190, 76, YEL, "🗣️", pop_s(f - S_INTRO, 5))
        d.text((W / 2, 290), "Voice Control  •  Bluetooth  •  ESP32", font=font(BOLD, 42), fill=(200, 210, 230), anchor="mm")
    elif f < S_SPIN:
        head(lay, d, "Test 1: \"Aage chalo\"", 210, 86, YEL, "🚀", pop_s(f - S_FWD, 5))
    elif f < S_DANCE:
        head(lay, d, "Test 2: \"Ghoom jao\"", 210, 86, YEL, "🌀", pop_s(f - S_SPIN, 5))
    elif f < S_CTA:
        head(lay, d, "Test 3: \"Dance karo\"", 210, 86, PINK, "😂", pop_s(f - S_DANCE, 5))
    else:
        head(lay, d, "Comment \"JARVIS\" = Code FREE", 190, 68, YEL, "👇", pop_s(f - S_CTA, 5))
        v = ease((f - S_CTA - 4) / 6)
        if v > 0:
            bw = int(820 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 270, W / 2 + bw / 2, 350), 40, fill=(130, 60, 255, 255))
            if v > 0.9:
                d.text((W / 2, 310), "Part 3: Jarvis ko aankhein denge", font=font(MONT, 40), fill=WHT, anchor="mm")


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🤖", 46), (W - 388, 46))


def orb_state(f):
    for (s0, ut, jt, je, ua, ra, m0, m1) in CMDS:
        if ua <= f < ra - 8:
            return "listen"
        if ra - 8 <= f < ra:
            return "think"
        if ra <= f < ra + 30:
            return "speak"
    return "idle"


def draw_small_orb(lay, f):
    st = orb_state(f)
    j2d.DIALOG = []                                                     # drive the orb state ourselves
    j2d.orb_state = lambda ff, st=st: (st, ff)
    j2d.draw_orb(lay, 175, 560, 120, f)
    ImageDraw.Draw(lay).text((175, 712), "JARVIS", font=font(MONT, 34), fill=CYAN, anchor="mm")


def frame(f):
    if f < S_INTRO:
        im = Image.fromarray(real_frame(f)).convert("RGBA")
        lay = Image.new("RGBA", (W, H))
        header(lay, f)
        badge(lay, ImageDraw.Draw(lay))
        im.alpha_composite(lay)
        out = np.array(im.convert("RGB"))
    else:
        im = Image.fromarray(np.clip(j2d.background(0), 0, 255).astype(np.uint8)).convert("RGBA")
        lay = Image.new("RGBA", (W, H))
        floor(lay)
        draw_robot(lay, f)
        draw_small_orb(lay, f)
        im.alpha_composite(lay)
        lay = Image.new("RGBA", (W, H))
        header(lay, f)
        badge(lay, ImageDraw.Draw(lay))
        subtitle(lay, f)
        im.alpha_composite(lay)
        out = np.array(im.convert("RGB"))
        if f - S_INTRO < 6:                                             # flash transition real -> 2D
            k = 1 - (f - S_INTRO) / 6
            out = np.clip(out.astype(np.float32) + 255 * 0.7 * k, 0, 255).astype(np.uint8)
    for s_ in (36, S_INTRO, S_FWD, S_SPIN, S_DANCE, S_CTA):
        a = f - s_
        if 0 <= a < 5:
            out = b.zoom(out, 1 + 0.05 * (1 - a / 5) ** 2)
    b.rainbow_bar(out, int(W * (f + 1) / TOTAL))
    return out


# ------------------------------------------------------------------ audio
def beep(freq, dur, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * tt) * np.minimum(1, tt / 0.004) * np.minimum(1, (dur - tt) / 0.02) * vol


def motor(dur, pitch=140):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = ((tt * pitch) % 1) * 2 - 1 + 0.6 * np.sin(2 * np.pi * pitch * 2 * tt)
    return fx.filt(x, "bandpass", [200, 2500]) * np.minimum(1, tt / 0.08) * np.minimum(1, (dur - tt) / 0.08) * 0.35


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    t = lambda f: f / FPS  # noqa: E731
    fx.write_wav(os.path.join(WORK, "music.wav"), j2d.pad(total + 0.05))
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.45)
    P(buf, fx.boom()[: int(0.4 * SR)] * 0.6, t(24), 0.4)                   # robot hits the mat
    P(buf, np.concatenate([beep(1320, 0.07, 0.4), beep(1760, 0.12, 0.4)]), t(36), 0.45)
    P(buf, fx.riser(0.5), t(S_INTRO) - 0.45, 0.3)
    for s_ in (S_INTRO, S_FWD, S_SPIN, S_DANCE, S_CTA):
        P(buf, fx.whoosh(0.25, s_) * 0.6, max(0, t(s_) - 0.12), 0.35)
    for (s0, ut, jt, je, ua, ra, m0, m1) in CMDS:
        P(buf, fx.pop(), t(ua), 0.3)
        P(buf, np.concatenate([beep(1320, 0.07, 0.4), beep(1760, 0.1, 0.4)]), t(ua + 4), 0.45)
        P(buf, np.concatenate([beep(1760, 0.07, 0.4), beep(2349, 0.12, 0.4)]), t(ra), 0.5)
        P(buf, j2d.bleeps(8, s0), t(ra) + 0.15, 0.3)
        P(buf, motor(t(m1 - m0), 150 if s0 != S_SPIN else 190), t(m0), 0.5)
    k0 = CMDS[2][6]                                                          # dance beat
    for k in range(12):
        P(buf, b.sq([523, 659, 784, 659][k % 4], 0.12, 0.25, 0.35), t(k0) + k * 0.3, 0.45)
    P(buf, b.fanfare8()[: int(0.9 * SR)] * 0.5, t(S_CTA), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(CLIP) - 0.2, 0.45)
    for a_ in b31.BTN_POP:
        P(buf, fx.pop(), t(CLIP + a_), 0.35)
    for a_ in b31.BTN_PRESS:
        P(buf, b.ok_beep()[: int(0.09 * SR)] * 0.6, t(CLIP + a_), 0.4)
    P(buf, fx.ding(), t(CLIP + b31.BTN_PRESS[2] + 1), 0.5)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    last = None
    for f in range(TOTAL):
        if f < CLIP:
            fr = frame(f)
            last = fr
        else:
            fr = b31.outro(f - CLIP, last, "Jarvis pasand aaya?", badge=badge, dim=0.55, sub_big=True)
            if f - CLIP < 4:
                k = 1 - (f - CLIP) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k), 1 + 0.05 * k)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f)).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for k_, im_ in enumerate(ims):
            c.paste(im_, (k_ * 360, 0))
        c.save(sys.argv[3])
    else:
        build_audio()
        build_video()
