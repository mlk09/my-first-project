#!/usr/bin/env python3
"""Python ki Pathshala EP 01 - re-edit in the style of "How does Swiggy deliver your order?".

Input : Python_ki_Pathshala_EP01_Short_25s.mp4 (your cut, content kept as is)
Output: edit8/output/Python_ki_Pathshala_EP01_FINAL.mp4

Adds, on top of your video (see STYLE_BREAKDOWN.md):
  * punch-in zoom cuts (alternating framing per section + snap zooms on the big hits)
  * warm light-leak flashes on every section change
  * "STEP-N / TITLE" lower thirds with type-on reveal
  * yellow scrolling keyword wheel (Websites -> AI & Chatbots -> Games -> Automation)
  * pop-up stickers: confused mascot with ??? , electric glowing "?", sparkles on POWER!
  * extra SFX: whooshes + shimmer on light leaks, type ticks, pops, crackle
  * the animated Python ki Pathshala end screen (Like / Share / Subscribe) at the end
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "brand"))
sys.path.insert(0, os.path.join(ROOT, "edit"))
sys.path.insert(0, os.path.join(ROOT, "edit7"))
import build_edit as fx        # noqa: E402  sfx helpers
import make_brand as mb        # noqa: E402  fonts, mascot, text helpers
import make_endscreen as es    # noqa: E402  animated end screen

SRC = os.path.join(ROOT, "Python_ki_Pathshala_EP01_Short_25s.mp4")
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP01_FINAL.mp4")
WORK = os.path.join(HERE, "work")
W, H, FPS, SR = 1080, 1920, 30, 48000
SW, SH = 1088, 1920                 # source size
CUT = 23.65                          # drop the old "@The IOT Engineer" end card
END_DUR = es.DUR
TOTAL = CUT + END_DUR

# section boundaries measured in the source (s)
BOUNDS = [0.0, 4.6, 8.9, 14.43, 21.4, CUT]
ZOOM = [1.0, 1.05, 1.06, 1.0, 1.05]          # alternating framing = Swiggy-style jump-cut feel
HITS = [(3.83, 0.13), (12.7, 0.06), (22.87, 0.13)]   # (time, extra zoom) snap punch-ins
LEAKS = [4.6, 8.9, 14.43, 21.4, CUT]            # light-leak flashes
STEPS = [  # (start, end, step, title)
    (4.95, 8.6, "STEP-1", "PROGRAMMING LANGUAGE"),
    (9.25, 14.1, "STEP-2", "ENGLISH JAISI SIMPLE"),
    (14.75, 16.1, "STEP-3", "PYTHON SE KYA BANTA HAI?"),
    (21.75, CUT - 0.1, "STEP-4", "PYTHON KI POWER"),
]
WHEEL = [(16.2, "Websites"), (16.9, "AI & Chatbots"), (18.0, "Games"), (19.0, "Automation")]
WHEEL_END = 21.2
CONFUSED = (2.55, 3.75)      # mascot + ??? on "ek common cheez hai"
SPARK_Q = (8.95, 10.2)       # electric ? on "Iski sabse badi khoobi?"
SPARKLES = 22.87             # sparkles on POWER!
LABEL_Y = 1600


# ------------------------------------------------------------------ small helpers
def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def out_back(t, s=1.7):
    t = min(1.0, max(0.0, t))
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def section(t):
    for k in range(len(BOUNDS) - 1):
        if t < BOUNDS[k + 1]:
            return k
    return len(BOUNDS) - 2


def zoom_at(t):
    k = section(t)
    z = ZOOM[k] + 0.02 * (t - BOUNDS[k]) / (BOUNDS[k + 1] - BOUNDS[k])   # slow drift
    for th, amt in HITS:
        a = t - th
        if 0 <= a < 0.45:
            z += amt * (1 - ease(a / 0.45))
    return z


def frame_src(img, t):
    """crop 1088 -> 1080 and apply the punch-in zoom around the centre"""
    z = zoom_at(t)
    M = cv2.getRotationMatrix2D((SW / 2, SH / 2), 0, z)
    M[0, 2] -= (SW - W) / 2
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ light leak
_rng = np.random.default_rng(4)
YY, XX = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)


def light_leak(t):
    """warm additive leak (orange/pink/yellow blobs sweeping across) or None"""
    best = None
    for c in LEAKS:
        a = (t - c) / 0.42 + 0.5          # 0..1 over the leak
        if 0 <= a <= 1:
            best = (c, a)
    if best is None:
        return None
    c, a = best
    inten = math.sin(a * math.pi) ** 1.5
    seed = int(c * 10)
    leak = np.zeros((H // 4, W // 4, 3), np.float32)
    for k, col in enumerate(((255, 120, 20), (255, 60, 90), (255, 210, 90))):
        r = np.random.default_rng(seed + k)
        x0 = r.uniform(-0.2, 0.3) * W / 4 + a * r.uniform(0.6, 1.2) * W / 4
        y0 = r.uniform(0.1, 0.9) * H / 4
        rad = r.uniform(0.35, 0.6) * W / 4
        g = np.exp(-(((XX - x0) ** 2 + (YY - y0) ** 2) / (2 * rad ** 2)))
        leak += g[..., None] * np.array(col, np.float32)
    leak = cv2.resize(leak, (W, H), interpolation=cv2.INTER_LINEAR)
    return leak * inten * 0.75


# ------------------------------------------------------------------ overlays
def lower_third(lay, t):
    for t0, t1, step, title in STEPS:
        if t0 <= t < t1 + 0.3:
            age, left = t - t0, t1 - t
            out = ease((-left) / 0.3) if left < 0 else 0.0
            fstep = mb.font(mb.BALOO, 46, "ExtraBold")
            ftitle = mb.font(mb.BALOO, 70, "ExtraBold")
            n = int(min(len(title), age * 34))        # type-on reveal
            d = ImageDraw.Draw(lay)
            a = int(255 * (1 - out))
            dy = int(30 * out)
            sa = int(255 * min(1, age / 0.15) * (1 - out))
            d.text((W / 2, LABEL_Y - 50 - dy), step, font=fstep, fill=mb.YEL + (sa,), anchor="mm",
                   stroke_width=4, stroke_fill=(0, 0, 0, sa))
            if n:
                d.text((W / 2, LABEL_Y + 20 - dy), title[:n], font=ftitle, fill=(255, 255, 255, a), anchor="mm",
                       stroke_width=6, stroke_fill=(0, 0, 0, a))
            return


def wheel(lay, t):
    if not (WHEEL[0][0] - 0.2 <= t < WHEEL_END + 0.3):
        return
    pos = sum(ease((t - tk) / 0.28) for tk, _ in WHEEL[1:])   # 0..3, rolls one slot per keyword
    fade = min(1, (t - WHEEL[0][0] + 0.2) / 0.25) * (1 - ease((t - WHEEL_END) / 0.3))
    f = mb.font(mb.BALOO, 68, "ExtraBold")
    d = ImageDraw.Draw(lay)
    for k, (_, word) in enumerate(WHEEL):
        off = k - pos
        if abs(off) > 1.6:
            continue
        y = LABEL_Y + off * 80
        a = int(255 * fade * max(0, 1 - abs(off) * 0.65))
        col = mb.YEL if abs(off) < 0.5 else (255, 230, 150)
        d.text((W / 2, y), word, font=f, fill=col + (a,), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, a))


_CACHE = {}


def confused(lay, t):
    t0, t1 = CONFUSED
    if not t0 <= t < t1:
        return
    if "m" not in _CACHE:
        _CACHE["m"] = mb.mascot(360)
    age = t - t0
    s = out_back(age / 0.3) * (1 - ease((t - t1 + 0.15) / 0.15))
    m = _CACHE["m"].resize((max(1, int(_CACHE["m"].width * s)), max(1, int(_CACHE["m"].height * s))))
    tilt = 6 * math.sin(age * 5)
    m = m.rotate(tilt, Image.BICUBIC, expand=True)
    lay.alpha_composite(m, (int(200 - m.width / 2), int(1640 - m.height / 2)))
    d = ImageDraw.Draw(lay)
    for k, (dx, dy, sz) in enumerate(((-40, -230, 1.0), (30, -280, 1.3), (100, -225, 0.9))):
        q = out_back((age - 0.12 * k) / 0.25)
        if q <= 0:
            continue
        fk = mb.font(mb.BALOO, int(90 * sz * q) + 1, "ExtraBold")
        d.text((200 + dx, 1640 + dy + 8 * math.sin(age * 8 + k)), "?", font=fk, fill=(255, 255, 255),
               anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))


def electric_q(lay, t):
    t0, t1 = SPARK_Q
    if not t0 <= t < t1:
        return
    age = t - t0
    fade = 1 - ease((t - t1 + 0.2) / 0.2)
    s = out_back(age / 0.25)
    size = int(300 * s) + 1
    f = mb.font(mb.BALOO, size, "ExtraBold")
    q = Image.new("RGBA", (520, 560))
    d = ImageDraw.Draw(q)
    d.text((260, 290), "?", font=f, fill=(255, 255, 255, 255), anchor="mm")
    core = q.copy()
    glow = Image.new("RGBA", q.size, (90, 140, 255, 0))
    glow.putalpha(q.getchannel("A").filter(ImageFilter.GaussianBlur(22)))
    out = Image.new("RGBA", q.size)
    for _ in range(3):
        out.alpha_composite(glow)
    # crackling arcs
    r = np.random.default_rng(int(t * 30))
    ad = ImageDraw.Draw(out)
    for _ in range(5):
        x, y = 260 + r.uniform(-90, 90), 290 + r.uniform(-130, 130)
        pts = [(x, y)]
        for _ in range(5):
            x += r.uniform(-40, 40)
            y += r.uniform(-40, 40)
            pts.append((x, y))
        ad.line(pts, fill=(200, 230, 255, 220), width=3)
    out.alpha_composite(core)
    a = np.asarray(out.getchannel("A")).astype(np.float32) * fade
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    lay.alpha_composite(out, (W // 2 - 260, 1530 - 290))


def sparkles(lay, t):
    age = t - SPARKLES
    if not 0 <= age < 0.9:
        return
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(3)
    for k in range(9):
        x, y = r.uniform(120, 960), r.uniform(1050, 1400)
        q = out_back((age - k * 0.04) / 0.2) * (1 - ease((age - 0.55) / 0.35))
        if q <= 0:
            continue
        s = r.uniform(24, 46) * q
        pts = []
        for j in range(8):
            rr = s if j % 2 == 0 else s * 0.3
            ang = -math.pi / 2 + j * math.pi / 4 + age * 3
            pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
        d.polygon(pts, fill=(255, 236, 140, 255))


def overlay(t):
    lay = Image.new("RGBA", (W, H))
    lower_third(lay, t)
    wheel(lay, t)
    confused(lay, t)
    electric_q(lay, t)
    sparkles(lay, t)
    return lay


def composite(base_rgb, t):
    fr = Image.fromarray(base_rgb).convert("RGBA")
    fr.alpha_composite(overlay(t))
    a = np.asarray(fr.convert("RGB")).astype(np.float32)
    leak = light_leak(t)
    if leak is not None:
        a = 255 - (255 - a) * (1 - leak / 255 * 0.6)           # screen blend
    return np.clip(a, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def load_src_audio():
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-t", f"{CUT:.3f}", "-ac", "2", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def shimmer(dur=0.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt + k) for k, f in enumerate((2093, 2637, 3136, 4186)))
    return x * np.exp(-tt * 5) * (1 - np.exp(-tt * 60)) * 0.12


def crackle(dur):
    n = int(dur * SR)
    r = np.random.default_rng(5)
    x = fx.filt(r.normal(0, 1, n), "highpass", 2500) * (r.random(n) > 0.985)
    buzz = np.sign(np.sin(2 * np.pi * 120 * np.arange(n) / SR)) * 0.05
    env = np.minimum(1, np.arange(n) / (0.05 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.15 * SR))
    return (fx.filt(x, "bandpass", [2000, 9000]) * 3 + fx.filt(buzz, "lowpass", 900)) * env


def tick(seed):
    n = int(0.02 * SR)
    return fx.filt(fx.noise(n, seed), "bandpass", [2500, 8000]) * fx.env_exp(n, 220) * 0.5


def extra_sfx():
    buf = np.zeros(int(TOTAL * SR))
    P = fx.place
    for i, c in enumerate(LEAKS):
        P(buf, fx.whoosh(0.4, 50 + i), max(0, c - 0.25), 0.45)
        P(buf, shimmer(), max(0, c - 0.05), 1.0)
    for t0, _, _, title in STEPS:
        P(buf, fx.pop(), t0, 0.4)
        for k in range(len(title)):
            if title[k] != " ":
                P(buf, tick(k), t0 + k / 34, 0.35)
    for tk, _ in WHEEL:
        P(buf, fx.whoosh(0.18, int(tk * 10)), tk - 0.05, 0.3)
        P(buf, fx.pop(), tk, 0.3)
    P(buf, fx.pop(), CONFUSED[0], 0.5)
    for k in range(3):
        P(buf, fx.pop(), CONFUSED[0] + 0.12 * (k + 1), 0.3)
    P(buf, crackle(SPARK_Q[1] - SPARK_Q[0]), SPARK_Q[0], 0.6)
    P(buf, shimmer(1.0), SPARKLES, 1.3)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    src = load_src_audio()
    n = int(TOTAL * SR)
    mix = np.zeros((n, 2), np.float32)
    fo = int(0.35 * SR)
    src[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix[: len(src)] += src
    mix += extra_sfx()[:n, None] * 0.55
    # end screen: its own SFX + a short outro bed in the same key/tempo as the episode music
    import build_short as bs   # edit7 renderer (music synth)
    bed = bs.music(END_DUR + 0.1, drop=0.0, power=99.0) * 0.35
    end = es.sfx() * 0.9
    e0 = int(CUT * SR)
    m = min(len(bed), n - e0)
    mix[e0:e0 + m] += bed[:m, None]
    m = min(len(end), n - e0)
    mix[e0:e0 + m] += end[:m, None]
    pcm = (np.clip(mix / max(1.0, np.max(np.abs(mix))), -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-ar", str(SR), os.path.join(WORK, "mix.wav")],
                   input=pcm.tobytes(), check=True)
    return os.path.join(WORK, "mix.wav")


# ------------------------------------------------------------------ main
def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    mix = build_audio()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", f"{CUT:.3f}", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", mix,
                            "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "14M",
                            "-bufsize", "28M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    fsz = SW * SH * 3
    i = 0
    last = None
    while True:
        raw = dec.stdout.read(fsz)
        if len(raw) < fsz:
            break
        t = i / FPS
        img = np.frombuffer(raw, np.uint8).reshape(SH, SW, 3)
        last = composite(frame_src(img, t), t)
        enc.stdin.write(last.tobytes())
        i += 1
        if i % 90 == 0:
            print(f"  {t:.1f}s", flush=True)
    # end screen, with the light leak carrying over the join
    for j in range(int(END_DUR * FPS)):
        t = CUT + j / FPS
        fr = np.asarray(es.frame(j / FPS).convert("RGB")).astype(np.float32)
        if j < 6 and last is not None:      # 0.2 s crossfade from the last frame
            a = j / 6
            fr = fr * a + last.astype(np.float32) * (1 - a)
        leak = light_leak(t)
        if leak is not None:
            fr = 255 - (255 - fr) * (1 - leak / 255 * 0.6)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
