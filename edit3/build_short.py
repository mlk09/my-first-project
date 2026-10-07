#!/usr/bin/env python3
"""40 s vertical short: millis() vs delay(), cut in the "How does Swiggy deliver" style.

Timeline (30 fps):
  A   0-104  3D hook (stopwatch + Arduino)                       [edit3/scene3d.py]
  B 105-314  STEP-1 millis(): your Tinkercad clip, counter racing (src 4:09-4:16)
  C 315-464  3D: millis() counter never stops                    [scene3d.py]
  D 465-674  STEP-2 delay(1000): your clip, prints once per second (src 8:50-8:57)
  E 675-899  3D: delay() lane freezes vs millis() lane keeps going [scene3d.py]
  F 900-1079 white result card, the check/cross draw themselves (Swiggy "Order Received")
  G 1080-1199 Follow card
Swiggy-style layer: STEP labels typing on (yellow STEP-n over white bold title), yellow
keyword wheels, light-leak transitions, soft music bed, whoosh/sparkle/tick/click SFX.

Usage: python3 edit3/build_short.py [audio] [video]
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import build_edit as fx  # noqa: E402  synth + sfx helpers

RAW = os.path.join(HERE, "..", "millis() and delay()  in Arduino programming | arduino programming tutorial.mp4")
WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "millis-vs-delay-SHORT.mp4")
W, H, FPS, SR = 1080, 1920, 30, 48000
N = 1200
SEG = {"A": (0, 105), "B": (105, 315), "C": (315, 465), "D": (465, 675), "E": (675, 900), "F": (900, 1080), "G": (1080, 1200)}
CLIPS = {"B": 249.0, "D": 530.0}          # source start seconds for the screen clips
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
YEL, WHT, RED, GRN = (255, 214, 10), (255, 255, 255), (235, 40, 40), (30, 190, 90)

# ---------------- captions per segment
STEPS = {  # seg: (small yellow, big white, first frame offset)
    "A": ("ARDUINO", "millis() vs delay()", 30),
    "B": ("STEP-1", "millis()", 8),
    "D": ("STEP-2", "delay(1000)", 8),
    "E": ("STEP-3", "DIFFERENCE", 8),
}
WHEELS = {  # seg: words that scroll by, one every `every` frames
    "B": (["Board ON", "Time count", "milliseconds"], 60),
    "C": (["Kabhi rukta nahi", "Background mein", "Hamesha chalta"], 48),
    "D": (["1 second WAIT", "Program RUKA", "Kuch nahi hota"], 60),
}


def seg_of(f):
    for k_, (a, b) in SEG.items():
        if a <= f < b:
            return k_, f - a
    return "G", f - SEG["G"][0]


# ================================================================== audio
def soft_chord(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) for f in freqs)
    env = np.minimum(1, t / 0.08) * np.exp(-t * 0.9)
    return x * env / len(freqs)


def sparkle(seed):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for i in range(6):
        st = int(i * 0.045 * SR)
        f = rng.uniform(3000, 6500)
        x[st:] += np.sin(2 * np.pi * f * t[: n - st]) * np.exp(-t[: n - st] * 25) * 0.25
    return x


def click():
    n = int(0.02 * SR)
    return fx.filt(fx.noise(n, 5), "bandpass", [2000, 7000]) * fx.env_exp(n, 250) * 0.6


def tick(hi=True):
    n = int(0.04 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (2400 if hi else 1700) * t) * np.exp(-t * 160) * 0.5


def thud():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-t * 25)) / SR) * np.exp(-t * 9)


def soft_buzz():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    return fx.filt(fx.signal.square(2 * np.pi * 140 * t), "lowpass", 1200, 2) * np.minimum(1, (0.35 - t) / 0.05) * 0.25


def chime():
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
        st = int(i * 0.06 * SR)
        x[st:] += np.sin(2 * np.pi * f * t[: n - st]) * np.exp(-t[: n - st] * 3.5) * 0.25
    return x


def music(total):
    """Calm, bright explainer bed (Swiggy-style): 96 BPM, soft keys + light beat."""
    bpm = 96
    beat = 60 / bpm
    n = int(total * SR)
    keys, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0],
              [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 349.2]]  # Cmaj7 Am7 Fmaj7 G7
    roots = [65.4, 55.0, 43.7, 49.0]
    k_ = fx.kick() * 0.6
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        if pos in (0, 2):
            fx.place(keys, soft_chord(ch, beat * 2.2), t0, 0.55)
        fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 300), t0, 0.7)
        if b >= 4:
            if pos in (0, 2):
                fx.place(drums, k_, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap() * 0.6, t0, 0.5)
        for s in range(2):
            fx.place(drums, fx.hat(b * 2 + s), t0 + s * beat / 2, 0.08 if s else 0.04)
        b += 1
    mix = keys + bass + drums
    fade = int(1.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    n = int(total * SR)
    buf = np.zeros(n)
    P = fx.place
    t = lambda f: f / FPS  # noqa: E731
    for i, key in enumerate(["B", "C", "D", "E", "F", "G"]):          # whoosh on every light-leak
        P(buf, fx.whoosh(0.4, i), max(0, t(SEG[key][0]) - 0.28), 0.5)
    for f in range(0, 105, 15):                                       # stopwatch ticks in the hook
        P(buf, tick(f % 30 == 0), t(f), 0.35)
    P(buf, sparkle(1), t(30), 0.5)
    for seg, (_, _, off) in STEPS.items():                            # STEP labels typing on
        a = SEG[seg][0] + off
        P(buf, sparkle(hash(seg) % 99), t(a), 0.45)
        for j in range(6):
            P(buf, click(), t(a + 4 + j * 2), 0.25)
    for seg, (words, every) in WHEELS.items():                        # keyword wheel steps
        for i in range(1, len(words)):
            P(buf, sparkle(i + 7), t(SEG[seg][0] + i * every), 0.3)
    for f in range(SEG["C"][0], SEG["C"][1], 5):                      # millis counter racing
        P(buf, tick(True), t(f), 0.12)
    for f in range(SEG["D"][0] + 10, SEG["D"][1], 30):                # delay: one tick per second
        P(buf, tick(False), t(f), 0.45)
    for j in range(3):                                                # delay cube hits the wall
        P(buf, thud(), t(SEG["E"][0] + j * 70 + 55), 0.5)
    P(buf, soft_buzz(), t(SEG["F"][0] + 18), 0.6)                     # cross draws
    P(buf, chime(), t(SEG["F"][0] + 70), 0.6)                         # tick draws
    P(buf, fx.ding(), t(SEG["G"][0] + 6), 0.4)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-17:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.9[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== video
def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def font(path, size):
    return ImageFont.truetype(path, size)


def raw_clip(seg):
    """Decode the 7 s screen clip for a segment (25 fps source -> 30 fps)."""
    a, b = SEG[seg]
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(CLIPS[seg]), "-i", RAW, "-t", f"{(b - a) / FPS:.3f}",
                        "-vf", "fps=30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, 720, 1280, 3)
    return fr


BG = None


def background():
    global BG
    if BG is None:
        y = np.linspace(0, 1, H)[:, None, None]
        top, bot = np.array([18, 22, 48]), np.array([8, 10, 22])
        BG = (top * (1 - y) + bot * y).repeat(W, axis=1).astype(np.uint8)
    return BG.copy()


def rounded(img, r=36):
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m


def screen_frame(seg, local, clip):
    src = clip[min(local * len(clip) // (SEG[seg][1] - SEG[seg][0]), len(clip) - 1)]
    crop = src[215:630, 655:1075]                     # code editor + serial monitor (tight, readable)
    z = 1.0 + 0.07 * ease(local / (SEG[seg][1] - SEG[seg][0]))
    cw = int(1000 * z)
    ch = int(crop.shape[0] * cw / crop.shape[1])
    panel = cv2.resize(crop, (cw, ch), interpolation=cv2.INTER_CUBIC)
    frame = background()
    x0, y0 = (W - cw) // 2, 340 - (ch - 988) // 2
    # shadow + rounded panel
    sh = np.zeros((H, W), np.float32)
    cv2.rectangle(sh, (x0 + 10, y0 + 24), (x0 + cw + 10, y0 + ch + 24), 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 24)[..., None] * 0.6
    frame = (frame * (1 - sh)).astype(np.uint8)
    m = rounded(panel)[..., None] / 255.0
    roi = frame[y0:y0 + ch, x0:x0 + cw]
    frame[y0:y0 + ch, x0:x0 + cw] = (panel * m + roi * (1 - m)).astype(np.uint8)
    # animated highlight on the code line that matters (line 8/9 of the editor)
    s = cw / 420.0
    line_y = {"B": 124, "D": 140}[seg]
    u = ease((local - 20) / 14)
    if u > 0:
        lx0, lx1 = x0 + int(40 * s), x0 + int((40 + 260 * u) * s)
        ly0, ly1 = y0 + int((line_y - 10) * s), y0 + int((line_y + 9 + (16 if seg == "D" else 0)) * s)
        cv2.rectangle(frame, (lx0, ly0), (lx1, ly1), YEL, 6, cv2.LINE_AA)
    # arrow from the code down to the serial monitor output
    v = ease((local - 45) / 14)
    if v > 0:
        ax, ay0, ay1 = x0 + int(330 * s), y0 + int((line_y + 30) * s), y0 + int(300 * s)
        cv2.arrowedLine(frame, (ax, ay0), (ax, int(ay0 + (ay1 - ay0) * v)), YEL, 7, cv2.LINE_AA, tipLength=0.18)
    return frame, None


def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    return cv2.addWeighted(im, 1.2, cv2.GaussianBlur(im, (0, 0), 1.6), -0.2, 0)


def card_frame(local):
    """White card, like Swiggy's 'Yay! Order Received'."""
    im = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(im)
    rows = [(640, "delay(1000)", "Program RUK jaata hai", RED, "x", 10),
            (1180, "millis()", "Program CHALTA rehta hai", GRN, "v", 62)]
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
                seg1 = min(1, w * 2)
                d.line((*p0, p0[0] + (p1[0] - p0[0]) * seg1, p0[1] + (p1[1] - p0[1]) * seg1), fill=WHT, width=24)
                if w > 0.5:
                    s2 = (w - 0.5) * 2
                    d.line((*p1, p1[0] + (p2[0] - p1[0]) * s2, p1[1] + (p2[1] - p1[1]) * s2), fill=WHT, width=24)
        a = ease((local - start - 14) / 10)
        if a > 0:
            tc = tuple(int(250 + (c - 250) * a) for c in (30, 30, 40))
            sc_ = tuple(int(250 + (c - 250) * a) for c in col)
            d.text((W // 2, cy + 40), code, font=font(MONO, 84), fill=tc, anchor="mm")
            d.text((W // 2, cy + 140), sub, font=font(BOLD, 56), fill=sc_, anchor="mm")
    return np.array(im)


def cta_frame(local):
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([120, 50, 210]), np.array([30, 150, 160])
    im = Image.fromarray((top * (1 - y) + bot * y).repeat(W, axis=1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    u = ease(local / 12)
    d.text((W // 2, 560), "ARDUINO · CODE KA RAAZ #3", font=font(MONT, 46), fill=(255, 210, 200), anchor="mm")
    bw = int(860 * u)
    if bw > 40:
        d.rounded_rectangle((W // 2 - bw // 2, 820, W // 2 + bw // 2, 990), 85, fill=YEL)
    if u > 0.9:
        d.text((W // 2, 905), "FOLLOW — roz 1 IoT concept", font=font(MONT, 52), fill=(20, 20, 30), anchor="mm")
    a = ease((local - 10) / 10)
    if a > 0:
        d.text((W // 2, 1130), "@The IOT Engineer", font=font(MONT, 70), fill=(255, 255, 255), anchor="mm")
    return np.array(im)


def step_label(frame, seg, local, y=1540):
    small, big, off = STEPS[seg]
    t_ = local - off
    if t_ < 0:
        return
    im = Image.fromarray(frame)
    d = ImageDraw.Draw(im)
    n = min(len(big), max(0, t_ // 2))
    a = min(1.0, t_ / 6)
    d.text((W // 2, y - 70), small, font=font(BOLD, 52), fill=YEL, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    if n:
        shown = big[:n]
        fb = font(BOLD, 92)
        d.text((W // 2, y + 10), shown, font=fb, fill=WHT, anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    frame[:] = (np.array(im) * a + frame * (1 - a)).astype(np.uint8)


def keyword_wheel(frame, seg, local, y=185):
    words, every = WHEELS[seg]
    pos = local / every
    i = int(pos)
    frac = ease((pos - i) * every / 10) if (pos - i) * every < 10 and i > 0 else 1.0
    im = Image.fromarray(frame)
    d = ImageDraw.Draw(im)
    f_ = font(BOLD, 74)
    cur = min(i, len(words) - 1)
    for j in range(len(words)):
        off = j - (cur - (1 - frac))
        if abs(off) > 1.6:
            continue
        alpha = max(0.0, 1 - abs(off) * 0.7)
        col = tuple(int(c * alpha + 20 * (1 - alpha)) for c in YEL)
        size = 74 if abs(off) < 0.5 else 56
        d.text((W // 2, y + off * 95), words[j], font=font(BOLD, size), fill=col, anchor="mm",
               stroke_width=4 if abs(off) < 0.5 else 2, stroke_fill=(0, 0, 0))
    frame[:] = np.array(im)


def light_leak(frame, k):
    """Warm film-burn flash; k in 0..1 (peak at 1)."""
    yy, xx = np.mgrid[0:H:4, 0:W:4]
    cx, cy = W * (0.2 + 0.6 * k), H * 0.35
    g = np.exp(-(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.45)) ** 2))
    g = cv2.resize(g.astype(np.float32), (W, H))[..., None] * k
    warm = np.array([255, 170, 80], np.float32)
    x = frame.astype(np.float32)
    x = x + (warm - x) * g * 0.75 + 255 * (g ** 3) * 0.6
    return np.clip(x, 0, 255).astype(np.uint8)


def build_video():
    clips = {s: raw_clip(s) for s in CLIPS}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "9M", "-bufsize", "18M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(N):
        seg, local = seg_of(f)
        if seg in ("A", "C", "E"):
            fr = load3d(f)
        elif seg in ("B", "D"):
            fr, _ = screen_frame(seg, local, clips[seg])
        elif seg == "F":
            fr = card_frame(local)
        else:
            fr = cta_frame(local)
        if seg in STEPS:
            step_label(fr, seg, local)
        if seg in WHEELS:
            keyword_wheel(fr, seg, local)
        # light-leak transitions straddling every boundary (6 frames each side)
        for key in ("B", "C", "D", "E", "F", "G"):
            d = f - SEG[key][0]
            if -6 <= d < 6:
                fr = light_leak(fr, 1 - abs(d + 0.5) / 6.5)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 100 == 0:
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
