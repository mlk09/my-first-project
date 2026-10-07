#!/usr/bin/env python3
"""14 s ESP32 water-level product-demo short, cut like the viral reference:
hard cuts every ~1.7 s, slow camera moves, no talking, sound tells the story
(tap water, sensor pings, LED blips, 4 kHz buzzer at FULL) — plus our own layer:
clean product-ad callouts, a live % chip, a Wi-Fi phone alert and an end card.

Usage: python3 edit5/build_short.py [audio] [video]
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-water-level-SHORT.mp4")
W, H, FPS, SR = 1080, 1920, 24, 48000
N = 336
SHOTS = [0, 41, 82, 123, 164, 205, 246, 300]
FILL0, FILL1 = 30, 240
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
CYAN, YEL, RED, GRN, WHT, INK = (60, 200, 255), (255, 200, 30), (240, 50, 50), (40, 210, 100), (255, 255, 255), (15, 18, 26)


def pct(f):
    if f <= FILL0:
        return 8.0
    if f >= FILL1:
        return 100.0
    u = (f - FILL0) / (FILL1 - FILL0)
    return 8 + 92 * (1 - (1 - u) ** 1.6)


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def font(p, s):
    return ImageFont.truetype(p, s)


# ================================================================== audio
def water_pour(dur):
    n = int(dur * SR)
    x = fx.filt(fx.noise(n, 31), "bandpass", [300, 4000])
    rng = np.random.default_rng(5)
    t = np.arange(n) / SR
    gurgle = np.zeros(n)
    for _ in range(int(dur * 9)):               # bubbles
        st = int(rng.uniform(0, dur - 0.1) * SR)
        m = int(0.06 * SR)
        tt = np.arange(m) / SR
        f0 = rng.uniform(500, 1400)
        gurgle[st:st + m] += np.sin(2 * np.pi * np.cumsum(f0 + 900 * tt / 0.06) / SR) * np.exp(-tt * 50) * 0.5
    pitch_rise = 1 - 0.35 * t / dur             # tank filling -> brighter, fuller
    x = fx.filt(x * pitch_rise, "highpass", 200)
    env = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.2)
    return (x * 0.5 + gurgle) * env


def ping():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (5200 - 18000 * t) * t) * np.exp(-t * 90) * 0.4


def blip(freq):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t)) * np.exp(-t * 35) * 0.5


def buzzer_beep():
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    x = fx.signal.square(2 * np.pi * 4000 * t, 0.5) * 0.25
    return x * np.minimum(1, t / 0.004) * np.minimum(1, (0.11 - t) / 0.004)


def notify():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, f in enumerate((1318.5, 1760.0)):
        st = int(i * 0.12 * SR)
        x[st:] += np.sin(2 * np.pi * f * t[: n - st]) * np.exp(-t[: n - st] * 6) * 0.35
    return x


def music(total):
    """Bright product-demo bed: 112 BPM, plucked major-7 arps, soft kick + shaker."""
    bpm, n = 112, int(total * SR)
    beat = 60 / bpm
    arp, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [293.7, 349.2, 440.0, 523.3],
              [220.0, 261.6, 329.6, 392.0], [246.9, 293.7, 349.2, 440.0]]
    roots = [65.4, 73.4, 55.0, 61.7]
    kick = fx.kick() * 0.5
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in range(4):
            fx.place(arp, fx.synth_note(ch[(pos * 2 + s) % 4] * 2, beat / 4 * 1.8, "tri", 9, 4000), t0 + s * beat / 4, 0.18)
        fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 260), t0, 0.7)
        if pos in (0, 2):
            fx.place(drums, kick, t0, 0.8)
        for s in range(4):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 4, 0.07 if s % 2 else 0.035)
        b += 1
    mix = arp + bass + drums
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    n = int(total * SR)
    buf = np.zeros(n)
    P = fx.place
    t = lambda f: f / FPS  # noqa: E731
    P(buf, water_pour(t(FILL1 - FILL0)), t(FILL0), 0.7)
    for i in range(8):                                        # sensor pings (shot 2)
        P(buf, ping(), t(44 + i * 5), 0.5)
    f_y = next(f for f in range(N) if pct(f) >= 50)
    f_r = next(f for f in range(N) if pct(f) >= 90)
    P(buf, blip(880), t(2), 0.4)                              # green on
    P(buf, blip(1175), t(f_y), 0.5)                           # yellow on
    P(buf, blip(1568), t(f_r), 0.5)                           # red on
    for j in range(10):                                       # buzzer: beep-beep at FULL (like the reference)
        P(buf, buzzer_beep(), t(FILL1) + j * 0.22, 0.55)
    for s in SHOTS[1:]:                                       # soft whoosh on the cuts
        P(buf, fx.whoosh(0.25, s) * 0.5, max(0, t(s) - 0.15), 0.35)
    P(buf, notify(), t(SHOTS[6] + 8), 0.7)                    # phone alert
    P(buf, fx.ding(), t(SHOTS[7] + 4), 0.35)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[s];"
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
    x = im.astype(np.float32) / 255                          # bloom on LEDs / OLED / pings
    bright = x * np.clip((x.max(2, keepdims=True) - 0.7) / 0.3, 0, 1)
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 8), (W, H)) * 0.5
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def emoji(ch, size):
    im = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(im).text((8, 8), ch, font=font(EMOJI, 109), embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def pill(d, cx, cy, text, sub=None, accent=CYAN, scale=1.0):
    f1 = font(MONT, int(48 * scale))
    w = d.textlength(text, font=f1) + 80 * scale
    if sub:
        w = max(w, d.textlength(sub, font=font(BOLD, int(34 * scale))) + 80 * scale)
    h = 96 * scale if not sub else 150 * scale
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(28 * scale), fill=(255, 255, 255, 235))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx - w / 2 + 14 * scale, cy + h / 2), int(8 * scale), fill=accent)
    if sub:
        d.text((cx + 6 * scale, cy - 26 * scale), text, font=f1, fill=INK, anchor="mm")
        d.text((cx + 6 * scale, cy + 34 * scale), sub, font=font(BOLD, int(34 * scale)), fill=(70, 80, 95), anchor="mm")
    else:
        d.text((cx + 6 * scale, cy), text, font=f1, fill=INK, anchor="mm")


CALLOUTS = {  # shot: (title, sub, accent, y)
    0: ("ESP32 WATER LEVEL", "Smart Tank Monitor 💧", CYAN, 230),
    1: ("HC-SR04", "Ultrasonic se distance naapo", CYAN, 1560),
    2: ("50% PAAR", "Yellow LED ON", YEL, 1560),
    3: ("OLED DISPLAY", "Live level %", CYAN, 1560),
    4: ("GREEN · YELLOW · RED", "Low · Half · Full", GRN, 1560),
    5: ("100% FULL!", "Buzzer ON 🔔", RED, 1560),
}


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i in CALLOUTS:
        title, sub, acc, y = CALLOUTS[i]
        u = ease(local / 7)
        sub_txt = sub.replace("💧", "").replace("🔔", "").strip()
        if u > 0:
            pill(d, W / 2, y + (1 - u) * 60, title, sub_txt, acc, 0.6 + 0.4 * u)
            em = "💧" if "💧" in sub else "🔔" if "🔔" in sub else None
            if em and u > 0.8:
                e = emoji(em, 90)
                lay.alpha_composite(e, (int(W / 2 + 330), int(y - 120)))
    if 1 <= i <= 5:                                     # live % chip (top-right)
        p = int(round(pct(f)))
        col = CYAN if p < 50 else YEL if p < 90 else RED
        d.rounded_rectangle((W - 330, 60, W - 40, 170), 30, fill=(10, 12, 18, 210))
        e = emoji("💧", 54)
        lay.alpha_composite(e, (W - 270 - e.width // 2, 115 - e.height // 2))
        d.text((W - 135, 115), f"{p}%", font=font(MONT, 72), fill=col, anchor="mm")
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def phone_frame(f):
    """Shot 7: wide shot defocused + a phone sliding in with the ESP32 Wi-Fi alert."""
    local = f - SHOTS[6]
    base = load3d(f)
    k = min(1, local / 8)
    base = cv2.GaussianBlur(base, (0, 0), 1 + 14 * k)
    base = (base * (1 - 0.35 * k)).astype(np.uint8)
    im = Image.fromarray(base).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    u = ease((local - 2) / 10)
    px, py = W // 2, int(1050 + (1 - u) * 1100)
    pw, ph = 620, 1180
    d.rounded_rectangle((px - pw // 2, py - ph // 2, px + pw // 2, py + ph // 2), 80, fill=(20, 22, 28, 255))
    d.rounded_rectangle((px - pw // 2 + 18, py - ph // 2 + 18, px + pw // 2 - 18, py + ph // 2 - 18), 66, fill=(32, 60, 110, 255))
    d.rounded_rectangle((px - 90, py - ph // 2 + 30, px + 90, py - ph // 2 + 70), 20, fill=(10, 10, 12, 255))
    d.text((px, py - ph // 2 + 150), "10:42", font=font(MONT, 110), fill=WHT, anchor="mm")
    v = ease((local - 10) / 8)                         # notification card drops in
    if v > 0:
        ny = py - 160 + (1 - v) * -120
        d.rounded_rectangle((px - 270, ny - 110, px + 270, ny + 110), 34, fill=(245, 246, 250, int(255 * v)))
        d.rounded_rectangle((px - 245, ny - 85, px - 165, ny - 5), 18, fill=(30, 140, 255, int(255 * v)))
        e = emoji("💧", 44)
        lay.alpha_composite(e, (int(px - 205 - e.width / 2), int(ny - 45 - e.height / 2)))
        d.text((px - 145, ny - 72), "SMART TANK · ESP32", font=font(BOLD, 26), fill=(90, 95, 110), anchor="lm")
        d.text((px - 145, ny - 28), "Tank FULL!", font=font(MONT, 38), fill=INK, anchor="lm")
        d.text((px - 245, ny + 40), "Motor OFF · Level 100%", font=font(BOLD, 34), fill=(60, 66, 80), anchor="lm")
        d.text((px - 245, ny + 82), "via Wi-Fi", font=font(BOLD, 28), fill=(30, 140, 255), anchor="lm")
    w2 = ease((local - 22) / 8)
    if w2 > 0:
        pill(d, W / 2, 300, "IoT ALERT", "ESP32 Wi-Fi se phone par", (30, 140, 255), 0.6 + 0.4 * w2)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def end_frame(f):
    local = f - SHOTS[7]
    base = load3d(f)
    im = Image.fromarray(base).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    g = Image.new("L", (1, H))
    g.putdata([int(200 * max(0, 1 - y / 700)) for y in range(H)])
    lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    u = ease(local / 8)
    d.text((W / 2, 170), "ESP32 WATER LEVEL", font=font(MONT, int(80 * (0.8 + 0.2 * u))), fill=WHT, anchor="mm",
           stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((W / 2, 275), "INDICATOR", font=font(MONT, int(80 * (0.8 + 0.2 * u))), fill=CYAN, anchor="mm",
           stroke_width=6, stroke_fill=(0, 0, 0))
    v = ease((local - 8) / 8)
    if v > 0:
        bw = int(880 * v)
        d.rounded_rectangle((W / 2 - bw / 2, 1530, W / 2 + bw / 2, 1680), 75, fill=YEL)
        if v > 0.9:
            d.text((W / 2, 1605), "Code chahiye? Comment \"TANK\"", font=font(MONT, 40), fill=INK, anchor="mm")
    w = ease((local - 16) / 8)
    if w > 0:
        d.text((W / 2, 1760), "@The IOT Engineer", font=font(MONT, 60), fill=WHT, anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0))
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(N):
        i, local = shot_of(f)
        if i == 6:
            fr = phone_frame(f)
        elif i == 7:
            fr = end_frame(f)
        else:
            fr = overlay(load3d(f), f)
            if f >= FILL1 and (f - FILL1) % 5 < 2 and i == 5:   # red pulse with the buzzer
                fr = cv2.addWeighted(fr, 0.85, np.full_like(fr, (255, 40, 40)), 0.15, 0)
        if 0 <= local < 3 and i > 0:                            # quick punch-in on every cut
            z = 1 + 0.04 * (1 - local / 3)
            M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
            fr = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)
        fr[0:8, :] = (fr[0:8, :] * 0.4).astype(np.uint8)
        fr[0:8, : int(W * (f + 1) / N)] = CYAN
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
