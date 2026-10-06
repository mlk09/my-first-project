#!/usr/bin/env python3
"""Final assembly for the Serial.begin(9600) short.

1. use the cleaned, pause-tightened voiceover from prep_voice.py
2. synthesise a cinematic tech music bed + SFX synced to the 3D shots
3. composite the Blender frames: upscale to 1080x1920, bloom, grade, vignette,
   grain, the reference-style title card, a diagonal split-wipe, whip-blur cuts,
   a red alarm flash and screen shake on the mismatch
4. mux with the mixed audio

Usage:  python3 edit2/build_final.py [audio] [video]
Run edit2/scene3d.py first (renders edit2/work/frames/0000.png ...).
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import build_edit as fx  # noqa: E402  (reuse synth + sfx helpers from the first edit)

WORK = os.path.join(HERE, "work")
FRAMES = os.path.join(WORK, "frames")
OUT = os.path.join(HERE, "output", "SerialBegin-3D-EDIT.mp4")
W, H, FPS, SR = 1080, 1920, 30, 48000
TITLE_FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# Voice + shot timing come from prep_voice.py (cleaned, pause-tightened voiceover).
import json  # noqa: E402
_T = json.load(open(os.path.join(WORK, "timing.json")))
S = _T["shots"]            # shot starts (frames), same as scene3d.py
N_FRAMES = _T["end"]
DUR = N_FRAMES / FPS


def t(f):
    return f / FPS


# ================================================================== audio
def pad_chord(freqs, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum(fx.signal.sawtooth(2 * np.pi * f * d * tt) for f in freqs for d in (0.997, 1.0, 1.004))
    x = fx.filt(x, "lowpass", 1400, 2)
    env = np.minimum(1, tt / 0.35) * np.minimum(1, (dur - tt) / 0.4)
    return x * env / (len(freqs) * 3)


def music(total):
    """Dark cinematic-tech bed: pads, pulsing sub, soft kick, 16th arp, sidechain pump."""
    bpm = 105
    beat = 60 / bpm
    n = int(total * SR)
    pads, pulse, drums, arp = (np.zeros(n) for _ in range(4))
    # Dm - Bb - F - C
    chords = [(73.42, [293.66, 349.23, 440.0]), (58.27, [233.08, 293.66, 349.23]),
              (87.31, [349.23, 440.0, 523.25]), (65.41, [261.63, 329.63, 392.0])]
    bar = beat * 4
    k = fx.kick()
    b = 0
    while b * beat < total:
        tb = b * beat
        bi, pos = divmod(b, 4)
        root, tones = chords[bi % 4]
        if pos == 0:
            fx.place(pads, pad_chord(tones, bar + 0.3), tb, 1.0)
        if pos in (0, 2) and tb > bar:          # soft kick from bar 2
            fx.place(drums, k, tb, 0.7)
        for s in range(2):                       # 8th-note sub pulse
            fx.place(pulse, fx.synth_note(root, beat * 0.45, "saw", 7, 220), tb + s * beat / 2, 0.6)
        if tb > bar * 2:                         # arp joins from bar 3
            for s in range(4):
                f = tones[[0, 2, 1, 2][s]] * 2
                fx.place(arp, fx.synth_note(f, beat / 4 * 1.5, "square", 20, 2600), tb + s * beat / 4, 0.09)
        for s in range(4):
            fx.place(drums, fx.hat(b * 4 + s), tb + s * beat / 4, 0.10 if s % 2 else 0.05)
        b += 1
    tb = (np.arange(n) / SR) % beat
    pump = 1 - 0.45 * np.exp(-tb * 10)
    mix = pads * 0.9 + (pulse + arp) * pump + drums * 0.8
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def blip(freq, dur=0.06):
    nn = int(dur * SR)
    tt = np.arange(nn) / SR
    return fx.signal.square(2 * np.pi * freq * tt, 0.5) * np.exp(-tt * 45) * 0.35


def buzzer():
    nn = int(0.55 * SR)
    tt = np.arange(nn) / SR
    x = fx.signal.square(2 * np.pi * 110 * tt) + 0.6 * fx.signal.square(2 * np.pi * 165 * tt)
    return fx.filt(x, "lowpass", 1800, 2) * np.minimum(1, (0.55 - tt) / 0.08) * 0.35


def glitch(seed):
    nn = int(0.18 * SR)
    x = fx.noise(nn, seed)
    x = np.repeat(x[::40], 40)[:nn]           # bit-crushed
    gate = (np.random.default_rng(seed).random(nn // 600 + 1) > 0.4).repeat(600)[:nn]
    return x * gate * 0.25


def key_click(seed):
    nn = int(0.03 * SR)
    return fx.filt(fx.noise(nn, seed), "bandpass", [1500, 6000]) * fx.env_exp(nn, 160) * 0.6


def chime():
    nn = int(1.6 * SR)
    tt = np.arange(nn) / SR
    x = np.zeros(nn)
    for i, f in enumerate((1046.5, 1318.5, 1568.0)):
        st = int(i * 0.07 * SR)
        e = np.exp(-tt[: nn - st] * 3.5)
        x[st:] += np.sin(2 * np.pi * f * tt[: nn - st]) * e * 0.33
    return x


def tick():
    nn = int(0.03 * SR)
    return fx.filt(fx.noise(nn, 3), "highpass", 3000) * fx.env_exp(nn, 200) * 0.5


def sfx_track(total):
    nn = int(total * SR)
    buf = np.zeros(nn)
    P = fx.place
    P(buf, fx.boom(), 0.0, 0.8)                                  # opening impact
    P(buf, fx.riser(t(S[1]) - 1.2), 1.2, 0.6)                   # riser into the crash zoom
    for i, f in enumerate(S[1:]):                                # whoosh on every cut
        P(buf, fx.whoosh(0.35, i + 1), max(0, t(f) - 0.25), 0.55)
    P(buf, fx.pop(), t(S[0] + 6), 0.5)
    P(buf, fx.pop(), t(22), 0.5)
    for f in (S[1] + 25, S[1] + 35):                             # TX / RX
        P(buf, fx.pop(), t(f), 0.45)
    pattern = "10110010011010110" * 2
    for i, ch in enumerate(pattern):                             # data blips as bits launch
        if S[2] - 40 + i * 6 < S[3]:
            P(buf, blip(1500 if ch == "1" else 950), t(S[2] - 40 + i * 6), 0.45)
    P(buf, fx.pop(), t(S[2] + 32), 0.5)
    P(buf, fx.ding(), t(S[2] + 32), 0.35)
    P(buf, fx.pop(), t(S[2] + 38), 0.4)
    for f in range(S[3] + 4, S[4], 8):                           # in-sync clock ticks
        P(buf, tick(), t(f), 0.35)
    for i in range(11):
        P(buf, key_click(40 + i), t(S[3] + 15 + i * 2), 0.3)
    P(buf, fx.boom()[: int(0.5 * SR)], t(S[3] + 38), 0.5)       # X on the clock wire
    for f in range(S[4], S[5], 3):                               # frantic fast ticks (115200)
        P(buf, tick(), t(f), 0.25)
    for i, f in enumerate((S[4] + 18, S[4] + 38, S[4] + 58)):   # garbage text glitches
        P(buf, glitch(i), t(f), 0.6)
    P(buf, buzzer(), t(S[5] + 3), 0.7)                           # mismatch!
    P(buf, fx.boom(), t(S[5] + 3), 0.85)
    P(buf, fx.pop(), t(S[6] + 30), 0.45)                         # dial label flips to 9600
    for i, f in enumerate(range(S[6] + 60, S[6] + 104, 4)):      # typing "Hello World!"
        P(buf, key_click(i), t(f), 0.45)
    P(buf, chime(), t(S[6] + 115), 0.6)                           # tick
    P(buf, fx.riser(1.0), t(S[7]) - 1.0, 0.35)
    P(buf, fx.boom()[: int(0.6 * SR)], t(S[7] + 6), 0.5)
    P(buf, fx.pop(), t(S[7] + 6), 0.5)
    P(buf, fx.ding(), t(S[8] + 10), 0.4)
    return buf


def build_audio():
    total = DUR + 0.05
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total) * 0.9)
    fc = (
        "[0:a]highpass=f=85,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3,"
        "acompressor=threshold=-20dB:ratio=3:attack=4:release=70:makeup=2,"
        "loudnorm=I=-16:TP=-2:LRA=6,aformat=sample_rates=48000:channel_layouts=stereo,asplit[vox][key];"
        "[1:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
        "[mus][key]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=260[musd];"
        "[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.8[sfx];"
        "[vox][musd][sfx]amix=inputs=3:normalize=0,"
        f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={DUR:.3f}[out]"
    )
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "voice.wav"),
            "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{DUR:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== video
def title_card():
    """Reference-style title: white bold caps line + black text on a yellow box."""
    im = Image.new("RGBA", (W, 330))
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(TITLE_FONT, 66)
    f2 = ImageFont.truetype(TITLE_FONT, 74)
    d.text((W // 2, 80), "SERIAL.BEGIN(9600)", font=f1, fill=(255, 255, 255), anchor="mm",
           stroke_width=4, stroke_fill=(0, 0, 0))
    l2 = "YE 9600 KYA HAI?"
    w2 = d.textlength(l2, font=f2)
    d.rectangle((W // 2 - w2 / 2 - 22, 128, W // 2 + w2 / 2 + 22, 222), fill=(255, 230, 0))
    d.text((W // 2, 176), l2, font=f2, fill=(0, 0, 0), anchor="mm")
    return np.array(im)


def load(f):
    f = min(max(f, 0), N_FRAMES - 1)
    im = cv2.imread(os.path.join(FRAMES, f"{f:04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)


def grade(im, rng):
    x = im.astype(np.float32) / 255
    # bloom from the bright neon parts
    lum = x.max(axis=2, keepdims=True)
    bright = x * np.clip((lum - 0.6) / 0.4, 0, 1)
    small = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.GaussianBlur(small, (0, 0), 9) + cv2.GaussianBlur(small, (0, 0), 25)
    x = x + cv2.resize(glow, (W, H)) * 0.4
    # sharpen the upscale a touch
    x = cv2.addWeighted(x, 1.25, cv2.GaussianBlur(x, (0, 0), 1.6), -0.25, 0)
    # contrast + teal/magenta tint
    x = np.clip((x - 0.5) * 1.06 + 0.5, 0, 1)
    x *= VIGNETTE
    x += rng.normal(0, 0.012, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.float32)
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


yy, xx = np.mgrid[0:H, 0:W]
VIGNETTE = (1 - 0.35 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2))[..., None].astype(np.float32)


def blit(frame, rgba, y, alpha):
    h = rgba.shape[0]
    sub = frame[y:y + h].astype(np.float32)
    a = rgba[..., 3:4].astype(np.float32) / 255 * alpha
    frame[y:y + h] = (sub * (1 - a) + rgba[..., :3] * a).astype(np.uint8)


def whip(im, strength):
    k = max(1, int(60 * strength))
    kernel = np.zeros((1, k), np.float32)
    kernel[0, :] = 1 / k
    return cv2.filter2D(im, -1, kernel)


def card_flip(im, theta):
    """3D card turn (perspective squeeze around the vertical axis) over black."""
    c, sn = np.cos(theta), np.sin(theta)
    x0, x1 = W / 2 - W / 2 * c, W / 2 + W / 2 * c
    hl, hr = H * (1 - 0.18 * sn), H * (1 + 0.18 * sn)
    dst = np.float32([[x0, (H - hl) / 2], [x1, (H - hr) / 2], [x1, (H + hr) / 2], [x0, (H + hl) / 2]])
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(im, M, (W, H), borderValue=(0, 0, 0))


def spin_whip(im, k):
    """Rotating zoom-in with blur, like the reference's tumbling fly-through cuts."""
    acc = np.zeros(im.shape, np.float32)
    for j in range(5):
        a = 28 * k * k * (1 - j * 0.12)
        z = 1 + 0.35 * k * k * (1 - j * 0.12)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), a, z)
        acc += cv2.warpAffine(im, M, (W, H), borderMode=cv2.BORDER_REFLECT101)
    return (acc / 5).astype(np.uint8)


FLIP_AT = S[7]
SPIN_AT = (S[3], S[6])


def build_video():
    title = title_card()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:",
                            "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "9M", "-bufsize", "18M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
                           stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    WIPE = 12
    for f in range(N_FRAMES):
        im = load(f)
        # diagonal split-wipe from the hook into the devices (held last hook frame)
        if S[1] <= f < S[1] + WIPE:
            prev = load(S[1] - 1)
            u = (f - S[1] + 1) / WIPE
            u = u * u * (3 - 2 * u)
            edge = (xx * 0.6 + yy) / (W * 0.6 + H)
            m = (edge < u * 1.15).astype(np.float32)[..., None]
            m = cv2.GaussianBlur(m, (0, 0), 3)[..., None]
            im = (im * m + prev * (1 - m)).astype(np.uint8)
            line = np.abs(edge - u * 1.15) < 0.004
            im[line] = (255, 255, 255)
        # whip-blur on the first frames of the plain cuts
        for s in (S[2], S[4], S[5], S[8]):
            if 0 <= f - s < 4:
                im = whip(im, 1 - (f - s) / 4)
        for s in SPIN_AT:
            if 0 <= f - s < 6:
                im = spin_whip(im, 1 - (f - s) / 6)
        if 0 <= f - FLIP_AT < 10:
            k = f - FLIP_AT
            if k < 5:
                im = card_flip(load(FLIP_AT - 1), (k + 1) / 5 * np.pi / 2 * 0.98)
            else:
                im = card_flip(im, -(1 - (k - 4) / 6) * np.pi / 2 * 0.98)
        # mismatch: red alarm flash + 2D shake
        if S[5] + 3 <= f < S[5] + 16:
            k = 1 - (f - S[5] - 3) / 13
            red = np.zeros_like(im)
            red[..., 0] = 255
            im = cv2.addWeighted(im, 1 - 0.35 * k, red, 0.35 * k, 0)
            dx, dy = int(24 * k * np.sin(f * 2.3)), int(24 * k * np.cos(f * 3.1))
            im = cv2.warpAffine(im, np.float32([[1.04, 0, dx - W * 0.02], [0, 1.04, dy - H * 0.02]]), (W, H),
                                borderMode=cv2.BORDER_REFLECT101)
        im = grade(im, rng)
        if f < 82:
            a = min(1, f / 3) * min(1, (82 - f) / 8)
            blit(im, title, 150, a)
        enc.stdin.write(im.tobytes())
        if f % 60 == 0:
            print(f"  frame {f}/{N_FRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    steps = sys.argv[1:] or ["audio", "video"]
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
