#!/usr/bin/env python3
"""Re-edit the HC-SR04 "Code mein ÷2 kyun?" short in the style of the reference
ultrasonic-sensor short (fast punch-in zooms, whip-zoom transitions, 1-3 word
pop captions with colour keywords, anime speed lines / shockwave hits, emoji
stickers, a driving music bed with sidechain ducking, and whoosh/pop/boom/ding SFX).

Everything (music + SFX) is synthesised here, so the output is copyright-clean.

Usage:  python3 edit/build_edit.py
Needs:  ffmpeg, python3 with numpy, scipy, opencv-python-headless, pillow
Edit the SHOTS / CAPTIONS / FX tables below to retime or reword things.
All times in those tables are in SOURCE-clip seconds (as seen in the raw file).
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "IoT-Short-Ultrasonic-Divide2-Canva-28sec.mp4")
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "IoT-Short-Ultrasonic-Divide2-EDITED.mp4")
FONT = os.path.join(HERE, "assets", "fonts", "Montserrat-Black.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS, SR = 1080, 1920, 30, 48000
ROI_Y = 820        # where the camera's point of interest lands on screen
CAPTION_Y = 1450   # vertical centre of captions

# ---------------------------------------------------------------- pacing ----
# Voice sections of the raw clip (pauses found from the RMS envelope). The gaps
# between them are tightened to ~2 frames, like the reference's zero-air pacing.
KEEP = [(0.30, 3.60), (3.73, 8.37), (8.57, 14.03), (14.23, 18.60),
        (18.80, 24.47), (24.63, 27.83)]
KEEP = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in KEEP]


def out_t(src):
    """Map a source time to the tightened output timeline."""
    acc = 0.0
    for a, b in KEEP:
        if src < a:
            return acc
        if src <= b:
            return acc + src - a
        acc += b - a
    return acc


DUR = sum(b - a for a, b in KEEP)

# ----------------------------------------------------------------- camera ---
# (src_start, zoom_from, zoom_to, roi_x, roi_y) - each row is a "shot".
# A new row = whip-zoom transition + whoosh.
SHOTS = [
    (0.00, 1.38, 1.30, 540, 360),    # hook: title being written (twist-in)
    (1.25, 1.24, 1.32, 540, 420),    # title + subtitle
    (3.73, 1.90, 2.02, 330, 790),    # sensor box being drawn
    (5.30, 1.30, 1.38, 540, 740),    # wall drawn (box + wall in frame)
    (8.57, 1.80, 1.92, 700, 600),    # 20 cm arrow
    (10.20, 1.36, 1.44, 560, 760),   # waves going out
    (12.10, 1.22, 1.30, 540, 820),   # full diagram, echo coming back
    (14.23, 1.22, 1.30, 540, 1185),  # "Sensor ne naapa = 40 cm"
    (16.30, 1.12, 1.18, 540, 920),   # punch-out: 20 cm drawing vs 40 cm reading
    (18.80, 1.22, 1.28, 540, 1322),  # "par deewar sirf 20 cm pe hai!"
    (20.10, 1.30, 1.37, 540, 1416),  # formula
    (22.30, 2.40, 2.58, 800, 1416),  # slam into the ÷2
    (23.37, 1.42, 1.50, 490, 1529),  # "wave DO BAAR chali!"
    (24.63, 1.42, 1.52, 540, 1640),  # push onto the Follow CTA
]

# --------------------------------------------------------------- captions ---
Y, R, B, G, Wh = (255, 225, 26), (255, 42, 42), (47, 128, 255), (57, 231, 95), (255, 255, 255)
# (src_t0, src_t1, lines, emoji[, y])   line = [(text, colour, size_mult), ...]
CAPTIONS = [
    (0.30, 1.25, [[("CODE MEIN", Wh, 1.0)]], None),
    (1.25, 2.35, [[("÷2", Y, 1.6)], [("KYUN?", Wh, 1.0)]], "🤔"),
    (2.35, 3.60, [[("SAB", Wh, 0.85), ("COPY-PASTE", R, 0.85)], [("KARTE HAIN...", Wh, 0.85)]], None),
    (3.73, 5.30, [[("ULTRASONIC", B, 1.0)], [("SENSOR", Wh, 0.9)]], None),
    (5.30, 6.40, [[("HC-SR04", Y, 1.15)]], None),
    (6.40, 8.37, [[("DEEWAR", Wh, 1.15)]], "🧱"),
    (8.57, 10.20, [[("20 CM", Y, 1.4)]], "📏"),
    (10.20, 12.10, [[("SOUND", Wh, 0.9)], [("WAVE", B, 1.3)]], "🔊"),
    (12.10, 14.03, [[("ECHO", R, 1.4)], [("WAPAS!", Wh, 0.9)]], None),
    (14.23, 16.30, [[("SENSOR NE", Wh, 0.95)], [("NAAPA", Y, 1.2)]], None),
    (16.30, 18.60, [[("40 CM", R, 1.7)]], "😳"),
    (18.80, 20.10, [[("PAR DEEWAR", Wh, 1.0)]], None),
    (20.10, 21.20, [[("SIRF", Wh, 0.9)], [("20 CM!", Y, 1.4)]], None),
    (21.20, 22.30, [[("TIME × 343", Wh, 1.0)]], "⏱️"),
    (22.30, 23.37, [[("÷ 2", Y, 2.0)]], None),
    (23.37, 24.47, [[("WAVE", Wh, 0.95), ("DO BAAR", R, 1.0)], [("CHALI!", Wh, 1.2)]], None, 1650),
    (24.63, 26.20, [[("FOLLOW", Y, 1.2)]], None, 1490),
    (26.20, 27.83, [[("ROZ 1", Wh, 0.8), ("IOT CONCEPT", B, 0.8)]], None, 1490),
]

# ------------------------------------------------------------- big FX hits ---
SPEEDLINES = [(1.25, 0.50)]          # (src_t, dur) anime burst on the hook question
SHOCKWAVES = [(22.30, 0.40)]         # ring of spikes around the ÷2
FLASHES = [(16.30, 0.15), (24.63, 0.20)]
SHAKES = [(16.30, 0.45, 26), (22.30, 0.35, 18), (23.37, 0.25, 10)]  # (t, dur, px)
BOOMS = [16.30, 22.30]
DINGS = [22.30, 24.63]
RISERS = [(15.40, 16.30)]

# ===================================================================== utils
def run(cmd, **kw):
    print("+", " ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True, **kw)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ================================================================ 1. tighten
def tighten():
    parts, cat = [], ""
    for i, (a, b) in enumerate(KEEP):
        d = b - a
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.012,afade=t=out:st={d - 0.012:.3f}:d=0.012[a{i}]")
        cat += f"[v{i}][a{i}]"
    parts.append(f"{cat}concat=n={len(KEEP)}:v=1:a=1[v][a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(parts),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "12", "-preset", "fast",
         "-r", str(FPS), "-c:a", "pcm_s16le", "-ar", str(SR), os.path.join(WORK, "tight.mov")])
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "tight.mov"), "-vn",
         "-ac", "1", "-ar", str(SR), os.path.join(WORK, "voice.wav")])


# =================================================================== 2. audio
def env_exp(n, rate):
    return np.exp(-np.arange(n) / SR * rate)


def noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n)


def filt(x, kind, f, order=4):
    sos = signal.butter(order, f, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += gain * x


def kick():
    n = int(0.38 * SR)
    t = np.arange(n) / SR
    f = 45 + 120 * np.exp(-t * 32)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    x[:96] += noise(96, 1) * 0.4 * np.linspace(1, 0, 96)
    return np.tanh(1.6 * x)


def clap():
    n = int(0.25 * SR)
    x = filt(noise(n, 2), "bandpass", [900, 3200])
    e = sum(np.roll(env_exp(n, 30), int(d * SR)) * (np.arange(n) >= d * SR) for d in (0, .009, .018))
    return x * e * 0.9


def hat(seed):
    n = int(0.06 * SR)
    return filt(noise(n, seed), "highpass", 7000) * env_exp(n, 70)


def synth_note(freq, dur, kind="saw", decay=10.0, cutoff=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "saw":
        x = signal.sawtooth(2 * np.pi * freq * t) + 0.5 * signal.sawtooth(2 * np.pi * freq * 1.005 * t)
    elif kind == "square":
        x = signal.square(2 * np.pi * freq * t, 0.35)
    else:
        x = signal.sawtooth(2 * np.pi * freq * t, 0.5)
    x *= np.exp(-t * decay) * np.minimum(1, t / 0.003)
    if cutoff:
        x = filt(x, "lowpass", cutoff, 2)
    return x


def music(total):
    bpm = 128
    beat = 60 / bpm
    n = int(total * SR)
    drums = np.zeros(n)
    tonal = np.zeros(n)
    # Am - F - C - G, one chord per bar
    chords = [(110.0, [220.0, 261.63, 329.63]), (87.31, [174.61, 220.0, 261.63]),
              (130.81, [261.63, 329.63, 392.0]), (98.0, [196.0, 246.94, 293.66])]
    k, c = kick(), clap()
    b = 0
    while b * beat < total:
        t = b * beat
        bar, pos = divmod(b, 4)
        root, tones = chords[bar % 4]
        place(drums, k, t, 1.0)
        if pos in (1, 3):
            place(drums, c, t, 0.55)
        for s in range(4):  # 16th hats, accented offbeats
            place(drums, hat(b * 4 + s), t + s * beat / 4, 0.32 if s == 2 else 0.14)
        place(tonal, synth_note(root / 2, beat * 0.45, "saw", 6, 380), t + beat / 2, 0.55)
        for s in range(4):  # plucky arp
            f = tones[[0, 1, 2, 1][s]] * 2
            place(tonal, synth_note(f, beat / 4 * 1.6, "square", 18, 3200), t + s * beat / 4, 0.10)
        b += 1
    # sidechain pump from the kick
    tb = (np.arange(n) / SR) % beat
    pump = 1 - 0.55 * np.exp(-tb * 14)
    mix = drums * 0.9 + tonal * pump
    # filtered intro sweep for the first bar
    intro = int(beat * 4 * SR)
    lp = filt(mix[:intro], "lowpass", 900, 2)
    ramp = np.linspace(0, 1, intro) ** 2
    mix[:intro] = lp * (1 - ramp) + mix[:intro] * ramp
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def whoosh(dur=0.32, seed=0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = noise(n, seed)
    lo = filt(x, "bandpass", [300, 1200])
    hi = filt(x, "bandpass", [1200, 6000])
    e = np.sin(np.pi * t ** 0.7) ** 2
    return (lo * (1 - t) + hi * t) * e * 1.4


def pop():
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    f = 500 + 900 * t / t[-1]
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 70) * 0.8


def boom():
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    f = 42 + 70 * np.exp(-t * 12)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5)
    x += filt(noise(n, 7), "lowpass", 1500) * np.exp(-t * 18) * 0.6
    return np.tanh(1.8 * x)


def ding():
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
            for f, a, d in ((2637, 1.0, 4.0), (5274, 0.35, 7.0), (3951, 0.2, 9.0)))
    return x * np.minimum(1, t / 0.002) * 0.5


def riser(dur):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = filt(noise(n, 9), "highpass", 1500) * t ** 2 * 0.5
    f = 200 + 1400 * t ** 2
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * t ** 2 * 0.25
    return x


def sfx_track(total):
    n = int(total * SR)
    buf = np.zeros(n)
    for i, s in enumerate(SHOTS[1:]):
        place(buf, whoosh(0.30, i), max(0, out_t(s[0]) - 0.22), 0.55)
    place(buf, whoosh(0.5, 99)[::-1], 0, 0.6)  # reverse whoosh into the hook
    big = set(BOOMS) | set(DINGS)
    for c in CAPTIONS:
        if c[0] not in big:
            place(buf, pop(), out_t(c[0]), 0.35)
    for t in BOOMS:
        place(buf, boom(), out_t(t), 0.9)
    for t in DINGS:
        place(buf, ding(), out_t(t), 0.55)
    for a, b in RISERS:
        place(buf, riser(out_t(b) - out_t(a)), out_t(a), 0.7)
    for t, d in SPEEDLINES:
        place(buf, whoosh(0.25, 50), out_t(t) - 0.05, 0.6)
        place(buf, boom()[: int(0.4 * SR)], out_t(t), 0.45)
    return buf


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
         "-i", "pipe:", path], input=pcm.tobytes())


def build_audio():
    total = DUR + 0.05
    write_wav(os.path.join(WORK, "music.wav"), music(total))
    write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total) * 0.9)
    fc = (
        "[0:a]highpass=f=85,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3,"
        "acompressor=threshold=-20dB:ratio=3:attack=4:release=70:makeup=2,"
        "loudnorm=I=-16:TP=-2:LRA=6,aformat=sample_rates=48000:channel_layouts=stereo,asplit[vox][key];"
        "[1:a]loudnorm=I=-19:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
        "[mus][key]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=260[musd];"
        "[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.8[sfx];"
        "[vox][musd][sfx]amix=inputs=3:normalize=0,"
        f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={DUR:.3f}[out]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "voice.wav"),
         "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
         "-filter_complex", fc, "-map", "[out]", "-t", f"{DUR:.3f}",
         os.path.join(WORK, "mix.wav")])


# =================================================================== 3. video
def render_caption(lines, base=96):
    """Bold caps, colour keywords, thick black stroke, soft drop shadow."""
    rows = []
    for line in lines:
        toks = []
        for text, col, mult in line:
            f = ImageFont.truetype(FONT, int(base * mult))
            bb = f.getbbox(text, stroke_width=int(base * mult * 0.12))
            toks.append((text, col, f, bb, int(base * mult * 0.12)))
        gap = int(base * 0.28)
        rw = sum(t[3][2] - t[3][0] for t in toks) + gap * (len(toks) - 1)
        rh = max(t[3][3] - t[3][1] for t in toks)
        rows.append((toks, rw, rh))
    pad = 40
    cw = max(r[1] for r in rows) + pad * 2
    ch = sum(r[2] for r in rows) + int(base * 0.05) * (len(rows) - 1) + pad * 2
    txt = Image.new("RGBA", (cw, ch))
    shadow = Image.new("RGBA", (cw, ch))
    dt, ds = ImageDraw.Draw(txt), ImageDraw.Draw(shadow)
    y = pad
    for toks, rw, rh in rows:
        x = (cw - rw) // 2
        for text, col, f, bb, sw in toks:
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            ty = y + (rh - th) - bb[1]
            dt.text((x - bb[0], ty), text, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
            ds.text((x - bb[0], ty + 9), text, font=f, fill=(0, 0, 0, 170), stroke_width=sw + 2, stroke_fill=(0, 0, 0, 170))
            x += tw + int(base * 0.28)
        y += rh + int(base * 0.05)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    return np.array(Image.alpha_composite(shadow, txt))


def render_emoji(ch, size=170):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox()) if im.getbbox() else im
    return np.array(im.resize((size, int(size * im.height / max(1, im.width))), Image.LANCZOS))


def pop_scale(age):
    keys = [(0, 0.55), (0.07, 1.13), (0.14, 0.96), (0.2, 1.0)]
    if age >= keys[-1][0]:
        return 1.0
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if age <= t1:
            return v0 + (v1 - v0) * (age - t0) / (t1 - t0)
    return 1.0


def blit(frame, rgba, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    h, w = rgba.shape[:2]
    if angle:
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rgba = cv2.warpAffine(rgba, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x0, y0 = int(cx - nw / 2), int(cy - nh / 2)
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sub = img[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0].astype(np.float32)
    a = sub[..., 3:4] / 255.0 * alpha
    dst = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (dst * (1 - a) + sub[..., :3] * a).astype(np.uint8)


def camera_at(t, shots):
    """Return (zoom, roi_x, roi_y, blur, twist) for output time t."""
    k = max(i for i, s in enumerate(shots) if s[0] <= t + 1e-9)
    s0, z0, z1, cx, cy = shots[k]
    s1 = shots[k + 1][0] if k + 1 < len(shots) else DUR
    p = (t - s0) / max(1e-6, s1 - s0)
    z = z0 + (z1 - z0) * (0.5 - 0.5 * np.cos(np.pi * min(1, p)))
    blur, twist = 0.0, 0.0
    TR_OUT, TR_IN = 0.10, 0.17
    if k + 1 < len(shots) and t > s1 - TR_OUT:          # whip out of this shot
        u = (t - (s1 - TR_OUT)) / TR_OUT
        z *= 1 + 0.30 * u * u
        blur = u
    if k > 0 and t - s0 < TR_IN:                          # settle into the new shot
        u = 1 - (t - s0) / TR_IN
        z *= 1 + 0.28 * u * u
        blur = max(blur, u)
    if k == 0 and t < 0.30:                               # twist-in hook
        u = 1 - t / 0.30
        z *= 1 + 0.9 * u * u
        blur = max(blur, u)
        twist = 28 * u * u
    return z, cx, cy, blur, twist


def warp(frame, z, cx, cy, twist=0.0, dx=0.0, dy=0.0):
    # clamp so the scaled frame always covers the screen
    x0 = min(max(cx - (W / 2) / z, 0), W - W / z)
    y0 = min(max(cy - ROI_Y / z, 0), H - H / z)
    ox, oy = x0 + (W / 2) / z, y0 + ROI_Y / z     # source point that lands on (W/2, ROI_Y)
    M = cv2.getRotationMatrix2D((ox, oy), twist, z)
    M[0, 2] += W / 2 - ox + dx
    M[1, 2] += ROI_Y - oy + dy
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)


def speedlines(frame, age, dur, cx, cy, seed):
    u = age / dur
    rng = np.random.default_rng(seed)
    ov = np.zeros_like(frame)
    mask = np.zeros(frame.shape[:2], np.uint8)
    for _ in range(46):
        th = rng.uniform(0, 2 * np.pi)
        r_in = rng.uniform(380, 640) * (1 + 0.25 * u)
        r_out = 1700
        wdt = rng.uniform(0.02, 0.05)
        pts = np.array([[cx + r_in * np.cos(th), cy + r_in * 1.25 * np.sin(th)],
                        [cx + r_out * np.cos(th - wdt), cy + r_out * 1.25 * np.sin(th - wdt)],
                        [cx + r_out * np.cos(th + wdt), cy + r_out * 1.25 * np.sin(th + wdt)]], np.int32)
        col = (90, 225, 255) if rng.random() < 0.75 else (255, 255, 255)
        cv2.fillPoly(ov, [pts], col, lineType=cv2.LINE_AA)
        cv2.fillPoly(mask, [pts], 255, lineType=cv2.LINE_AA)
    a = (mask[..., None] / 255.0) * (0.95 * (1 - u ** 3))
    frame[:] = (frame * (1 - a) + ov * a).astype(np.uint8)


def shockwave(frame, age, dur, cx, cy):
    u = age / dur
    r = 150 + 520 * (1 - (1 - u) ** 3)
    ov = frame.copy()
    for i in range(28):
        th = 2 * np.pi * i / 28 + 0.1 * (i % 3)
        ln = 70 * (1 - u) + 15
        p1 = (int(cx + r * np.cos(th)), int(cy + r * np.sin(th)))
        p2 = (int(cx + (r + ln) * np.cos(th)), int(cy + (r + ln) * np.sin(th)))
        cv2.line(ov, p1, p2, (90, 225, 255), 11, cv2.LINE_AA)
    cv2.circle(ov, (int(cx), int(cy)), int(r * 0.92), (255, 255, 255), 5, cv2.LINE_AA)
    a = 1 - u
    frame[:] = cv2.addWeighted(ov, a, frame, 1 - a, 0)


def build_video():
    shots = [(out_t(s[0]), *s[1:]) for s in SHOTS]
    caps = []
    for t0, t1, lines, emo, *y in CAPTIONS:
        img = render_caption(lines)
        caps.append((out_t(t0), out_t(t1), img, render_emoji(emo) if emo else None, y[0] if y else CAPTION_Y))
    sl = [(out_t(t), d) for t, d in SPEEDLINES]
    sw = [(out_t(t), d) for t, d in SHOCKWAVES]
    fl = [(out_t(t), d) for t, d in FLASHES]
    sh = [(out_t(t), d, a) for t, d, a in SHAKES]

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(WORK, "tight.mov"),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:"], stdout=subprocess.PIPE)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:",
                            "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    fsize = W * H * 3
    i = 0
    while True:
        raw = dec.stdout.read(fsize)
        if len(raw) < fsize:
            break
        src = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        t = i / FPS

        z, cx, cy, blur, twist = camera_at(t, shots)
        # beat bump on every caption change
        for c0, *_ in caps:
            if 0 <= t - c0 < 0.18:
                z *= 1 + 0.045 * (1 - (t - c0) / 0.18)
        dx = dy = 0.0
        for t0, d, amp in sh:
            if 0 <= t - t0 < d:
                k = amp * (1 - (t - t0) / d) ** 2
                dx += k * np.sin(t * 97.0)
                dy += k * np.cos(t * 83.0)

        if blur > 0.05:   # radial zoom blur = average of slightly different zooms
            n = 7
            acc = np.zeros((H, W, 3), np.float32)
            for j in range(n):
                acc += warp(src, z * (1 + 0.06 * blur * j / (n - 1)), cx, cy, twist, dx, dy)
            frame = (acc / n).astype(np.uint8)
        else:
            frame = warp(src, z, cx, cy, twist, dx, dy)

        for t0, d in sl:
            if 0 <= t - t0 < d:
                speedlines(frame, t - t0, d, W / 2, CAPTION_Y - 40, i // 2)
        for t0, d in sw:
            if 0 <= t - t0 < d:
                shockwave(frame, t - t0, d, W / 2, CAPTION_Y)

        for c0, c1, img, emo, cy_cap in caps:
            if c0 <= t < c1:
                age = t - c0
                s = pop_scale(age)
                blit(frame, img, W / 2, cy_cap + (1 - s) * 30, s, min(1, age / 0.04))
                if emo is not None:
                    ea = max(0, age - 0.08)
                    es = pop_scale(ea) if age >= 0.08 else 0
                    ey = cy_cap - img.shape[0] / 2 - 70 + 8 * np.sin(age * 9)
                    blit(frame, emo, W / 2 + img.shape[1] * 0.30, ey, es, 1.0, 10 * np.sin(age * 7))

        for t0, d in fl:
            if 0 <= t - t0 < d:
                a = 0.85 * (1 - (t - t0) / d)
                frame = cv2.addWeighted(np.full_like(frame, 255), a, frame, 1 - a, 0)

        enc.stdin.write(frame.tobytes())
        i += 1
        if i % 60 == 0:
            print(f"  frame {i}  ({t:.1f}s)", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    steps = sys.argv[1:] or ["tighten", "audio", "video"]
    if "tighten" in steps:
        tighten()
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
