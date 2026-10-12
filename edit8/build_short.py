#!/usr/bin/env python3
"""16 s 'ESP32 RFID Smart Door Lock' short, in the Tap-to-Light style: hook payoff in the first
second, pop-in labels with corner frames, punch-in on every card read, ACCESS DENIED (red tint +
shake + triple buzz) vs ACCESS GRANTED (green flash + beep), serial-monitor UID panel, servo whirr
+ bolt clack, door creak into a bright room, blur-zoom cuts, progress bar, end-card CTA.
Original music + SFX synced to timeline.READS.
Usage: python3 edit8/build_short.py [audio] [video]
"""
import importlib.util
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402
from timeline import FPS, N, SHOTS, READS, UID_OK, UID_BAD, DOOR_OPEN, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-rfid-door-lock-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED = (40, 230, 110), (255, 60, 60)
SERVO_T = 270                     # servo starts turning (timeline.unlocked)


def font(p, s):
    return ImageFont.truetype(p, max(8, int(s)))


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def t(f):
    return f / FPS


# ================================================================== audio
def beep(freq, dur, square=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.5 if square else np.sin(2 * np.pi * freq * tt)
    return x * np.minimum(1, tt / 0.003) * np.minimum(1, (dur - tt) / 0.01) * 0.6


def ok_beep():
    return np.concatenate([beep(2700, 0.09), np.zeros(int(0.04 * SR)), beep(3600, 0.16)])


def deny_buzz():
    seg = fx.filt(beep(420, 0.12, square=True), "lowpass", 3000)
    gap = np.zeros(int(0.06 * SR))
    return np.concatenate([seg, gap, seg, gap, seg])


def servo_whirr(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = fx.signal.sawtooth(2 * np.pi * (170 + 25 * np.sin(2 * np.pi * 3 * tt)) * tt)
    x = fx.filt(x, "bandpass", [150, 2500]) + 0.3 * fx.filt(fx.noise(n, 4), "bandpass", [2000, 6000])
    return x * np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.08) * 0.35


def clack():
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 21), "bandpass", [800, 6000]) * np.exp(-tt * 60)
    x += sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) * a for f, a, d in ((1850, 0.5, 30), (3100, 0.3, 40), (520, 0.6, 25)))
    return np.tanh(1.4 * x)


def creak(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = 140 + 60 * np.sin(2 * np.pi * 0.7 * tt) + 30 * np.sin(2 * np.pi * 3.1 * tt)
    pulses = fx.signal.sawtooth(2 * np.pi * np.cumsum(f0) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt) ** 2)
    x = fx.filt(pulses, "bandpass", [300, 2400]) * np.sin(np.pi * tt / dur) ** 0.6
    return x * 0.5


def music(total):
    """118 BPM tense pluck groove; full kit + saw stabs from ACCESS GRANTED onward."""
    bpm, n = 118, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6],
              [196.0, 246.9, 293.7, 392.0], [164.8, 207.7, 246.9, 329.6]]
    roots = [55.0, 43.7, 49.0, 41.2]
    kick = fx.kick() * 0.55
    drop = t(READS[2][0])
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        full = t0 >= drop - 0.05
        tense = t(SHOTS[3]) <= t0 < drop
        for s in range(2):
            fx.place(mel, fx.synth_note(ch[(pos * 2 + s) % 4] * 2, beat / 2 * 1.6, "tri", 8, 3500), t0 + s * beat / 2,
                     0.1 if tense else 0.16)
        if full:
            fx.place(mel, fx.synth_note(ch[0] * 2, beat * 0.4, "saw", 9, 2600), t0 + beat / 2, 0.12)
        if t0 > 0.4:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.7 if full else 0.5)
        if t0 > 0.4 and (full or pos in (0, 2)):
            fx.place(drums, kick, t0, 0.85 if full else 0.65)
        if full and pos in (1, 3):
            fx.place(drums, fx.clap(), t0, 0.32)
        for s in range(4 if full else 2):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / (4 if full else 2), 0.06)
        b += 1
    mix = mel + bass + drums
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.45), 0.0, 0.45)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in (SHOTS[1], SHOTS[2], SHOTS[5]):
        P(buf, fx.pop(), t(s + 4), 0.25)
    for f, r in READS:
        P(buf, fx.whoosh(0.35, f) * 0.5, t(f - 9), 0.35)             # card swish in
        if r == "OK":
            P(buf, ok_beep(), t(f), 0.6)
            P(buf, fx.boom()[: int(0.6 * SR)], t(f + 1), 0.45)
        else:
            P(buf, deny_buzz(), t(f), 0.6)
            P(buf, fx.boom()[: int(0.4 * SR)] * 0.7, t(f), 0.35)
    P(buf, servo_whirr(0.3), t(15), 0.4)                              # hook unlock
    P(buf, clack(), t(20), 0.6)
    P(buf, clack() * 0.7, t(42), 0.4)
    P(buf, servo_whirr(t(12)), t(SERVO_T), 0.6)                       # servo close-up
    P(buf, clack(), t(SERVO_T + 11), 0.8)
    P(buf, creak(t(DOOR_OPEN[1] - DOOR_OPEN[0])), t(DOOR_OPEN[0]), 0.7)
    P(buf, fx.whoosh(0.9, 77), t(DOOR_OPEN[0] + 4), 0.45)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== video
def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.25, cv2.GaussianBlur(im, (0, 0), 1.6), -0.25, 0)
    x = im.astype(np.float32) / 255
    sat = x.max(2, keepdims=True) - x.min(2, keepdims=True)
    bright = x * np.clip((x.max(2, keepdims=True) - 0.7) / 0.3, 0, 1) * np.clip(sat / 0.35, 0, 1)
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 7), (W, H)) * 0.5
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def txt(d, xy, s, size, fill, f=MONT, stroke=None, anchor="mm"):
    d.text(xy, s, font=font(f, size), fill=fill, anchor=anchor,
           stroke_width=stroke if stroke is not None else max(4, int(size) // 10), stroke_fill=(0, 0, 0))


def pop_s(age, dur=8):
    if age < 0:
        return 0
    u = min(1, age / dur)
    return ease(u) * (1 + 0.25 * np.sin(np.pi * min(1, age / (dur * 0.8))))


def corner_frame(d, box, u, col=CYAN, w=8, L=110):
    x0, y0, x1, y1 = box
    ln = L * ease(u)
    if ln < 2:
        return
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * ln, cy), fill=col, width=w)
        d.line((cx, cy, cx, cy + sy * ln), fill=col, width=w)


def label(lay, d, text, sub, local, y=1530, em=None, col=WHT):
    s = pop_s(local - 2)
    if s <= 0:
        return
    txt(d, (W / 2, y), text, 86 * s, col, stroke=8)
    v = ease((local - 9) / 6)
    if v > 0 and sub:
        tw = d.textlength(sub, font=font(BOLD, 46)) + 60
        d.rounded_rectangle((W / 2 - tw / 2, y + 62, W / 2 + tw / 2, y + 132), 35, fill=(0, 0, 0, int(170 * v)))
        d.text((W / 2, y + 97), sub, font=font(BOLD, 46), fill=(235, 240, 255, int(255 * v)), anchor="mm")
    if em and s > 0.9:
        tw = d.textlength(text, font=font(MONT, 86))
        lay.alpha_composite(e5.emoji(em, 92), (int(W / 2 + tw / 2 + 14), int(y - 52)))


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🔐", 46), (W - 388, 46))


def uid_panel(d, f, read_f, ok):
    """Serial-monitor style readout that types itself in after a read."""
    age = f - read_f
    if age < 0:
        return
    lines = ["> Card detected...", f"> UID: {UID_OK if ok else UID_BAD}", "> OWNER  -> UNLOCK" if ok else "> UNKNOWN -> LOCKED"]
    v = ease(age / 5)
    y0 = 1430
    d.rounded_rectangle((90, y0, W - 90, y0 + 230), 26, fill=(8, 12, 18, int(225 * v)), outline=(GRN if ok else RED) + (int(255 * v),), width=4)
    chars = int(age * 3.2)
    for i, ln in enumerate(lines):
        shown = ln[:max(0, chars - sum(len(x) for x in lines[:i]))]
        col = (GRN if ok else RED) if i == 2 else (200, 210, 225)
        d.text((125, y0 + 48 + i * 66), shown, font=font(MONO, 40), fill=col, anchor="lm")


def big_verdict(lay, d, f, read_f, ok):
    s = pop_s(f - read_f - 1, 6)
    if s <= 0:
        return
    word = "ACCESS GRANTED" if ok else "ACCESS DENIED"
    txt(d, (W / 2, 360), word, 100 * s, GRN if ok else RED, stroke=10)
    if s > 0.9:
        lay.alpha_composite(e5.emoji("✅" if ok else "❌", 96), (int(W / 2 - 48), 440))


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i < 6:
        g = Image.new("L", (1, H))
        g.putdata([int(140 * max(0, 1 - y / 560)) for y in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Card dikhao...", 76 * s, WHT, stroke=8)
        s2 = pop_s(local - READS[0][0] - 2, 7)
        if s2 > 0:
            txt(d, (W / 2, 380), "DARWAZA KHULA!", 92 * s2, YEL, stroke=11)
            if s2 > 0.9:
                lay.alpha_composite(e5.emoji("🔓", 110), (W // 2 - 55, 450))
        v = ease((local - 24) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330, 1620, W / 2 + 330, 1720), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1670), "ESP32 + RFID Smart Lock", font=font(MONT, 44), fill=INK, anchor="mm")
    elif i == 1:
        label(lay, d, "Smart Door Lock", "Bina chaabi, sirf RFID card", local, y=300, em="🔐")
    elif i == 2:
        corner_frame(d, (120, 520, 960, 1340), (local - 2) / 8)
        label(lay, d, "ESP32 + MFRC522", "13.56 MHz RFID Reader", local, em="📡")
    elif i in (3, 4):
        read_f, r = READS[1] if i == 3 else READS[2]
        ok = r == "OK"
        if f < read_f + 2:
            label(lay, d, "Anjaan card?" if not ok else "Asli key fob", None, local, y=300, em="🤔" if not ok else "🔑")
        big_verdict(lay, d, f, read_f, ok)
        uid_panel(d, f, read_f, ok)
    elif i == 5:
        label(lay, d, "Servo = Lock", "Bolt khud slide hota hai", local, y=300, em="⚙️")
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y / 700)) for y in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 10) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"LOCK\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 18) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def zoom(fr, z, cx=W / 2, cy=H / 2, dx=0.0):
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[0, 2] += dx
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1)[..., None].astype(np.float32)
    for f in range(N):
        fr = load3d(f)
        z, dx = 1.0, 0.0
        for rf, r in READS:
            a = f - rf
            if 0 <= a < 8:
                z += 0.05 * (1 - a / 8) ** 2                       # punch-in on the read
            if r == "NO" and 0 <= a < 12:
                dx = 18 * np.sin(a * 2.6) * (1 - a / 12)            # head-shake on denied
        if SERVO_T + 11 <= f < SERVO_T + 17:
            z += 0.03 * (1 - (f - SERVO_T - 11) / 6)               # bolt clack thump
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        for rf, r in READS:
            a = f - rf
            if r == "OK" and 0 <= a < 5:
                x += (np.array(GRN, np.float32) * 0.6 + 100 - x) * 0.3 * (1 - a / 5)
            if r == "NO" and 0 <= a < 30:
                k_ = 0.45 * (1 - a / 30) * (0.6 + 0.4 * np.cos(a * 0.8))
                x = x * (1 - k_ * vig) + np.array(RED, np.float32) * k_ * vig
        if f >= DOOR_OPEN[0]:                                      # light spill when the door opens
            u = ease((f - DOOR_OPEN[0]) / 24)
            x += (255 - x) * 0.12 * u * (1 - vig)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / N)                                   # lock-themed progress bar
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = GRN if f >= READS[2][0] else (CYAN if f < READS[1][0] or f >= READS[1][0] + 30 else RED)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 48 == 0:
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
