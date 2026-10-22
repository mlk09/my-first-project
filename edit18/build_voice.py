#!/usr/bin/env python3
"""Voice-over version of the RGB colour-mixer short: the video is re-timed to the ElevenLabs voice
instead of squeezing the voice. Voice lines (speech chunks from silence detection, grouped by the
script) are laid out at natural pace (SPEED, long pauses cut to PAUSE); every shot is stretched so
its line fits, with extra anchors so the colour hits land on the words (R / G / B flashes on
'sirf ek LED', 16 MILLION on 'ek crore saath lakh rang', red / green / white on 'Red', 'Green',
'White', the knob press on 'party mode'). Rendered frames are cross-blended for the slow parts;
overlays, SFX and music follow the same time map; music + SFX duck under the voice.
Usage: python3 edit18/build_voice.py <voice.mp3> [profile: v1 | monika]"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("b18", os.path.join(HERE, "build_short.py"))
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)
FPS, N, SHOTS, PRESS = b.FPS, b.N, b.SHOTS, b.PRESS
SR = 48000
SPEED = 1.1                                # voice tempo (pitch kept); per-profile override below
PAUSE = 0.15
GAP = 0.3                                  # silence between lines
EXTRA = {5: 1.6}                           # let PARTY mode play out before the end card
PROFILES = {   # speech chunks (seconds in the voice file) grouped into the 8 script lines
    "v1": [
        [(0.00, 0.63), (1.26, 2.03), (3.08, 3.38), (4.08, 5.35)],        # sirf ek LED ... aur ... 1 crore 60 lakh rang
        [(6.05, 8.31), (8.67, 9.24)],                                     # ESP32, OLED, aur ek knob. Bas itna chahiye
        [(10.23, 10.44), (10.98, 11.66), (12.50, 12.67), (13.23, 13.78), (14.58, 14.88)],   # Red.. Green.. Yellow.. White
        [(15.26, 15.95), (16.61, 16.95), (17.36, 18.21)],                 # ab knob ghumao .. har click pe naya rang
        [(18.62, 20.26), (20.72, 22.65)],                                 # brightness kam-zyada. PWM ka kamaal
        [(23.10, 23.73), (24.47, 25.20)],                                 # aur knob dabao .. party mode
        [(25.81, 27.29), (27.78, 28.34), (28.74, 29.39)],                 # code + circuit free. comment RGB
        [(30.04, 30.84), (31.06, 33.37)],                                 # like share subscribe
    ],
    "monika": [
        [(0.00, 1.05), (1.23, 2.42), (2.84, 5.61)],
        [(6.07, 7.30), (7.58, 8.50), (8.77, 9.45), (9.78, 10.76)],
        [(11.19, 11.70), (11.97, 12.74), (13.03, 13.53), (13.80, 14.85), (15.12, 15.65)],
        [(15.98, 16.92), (17.17, 17.70), (17.89, 19.62)],
        [(19.91, 21.78), (22.08, 24.25)],
        [(24.56, 25.39), (25.73, 26.52)],
        [(26.83, 28.55), (28.84, 30.37)],
        [(30.67, 34.32)],
    ],
}
PROFILE = sys.argv[2] if len(sys.argv) > 2 else "v1"
LINES = PROFILES[PROFILE]
SPEED = {"monika": 1.15}.get(PROFILE, SPEED)
# (line, chunk) of the words the colour hits land on: hook 16 MILLION, Red, plus Green, White, party mode
KEYS = {"v1": {"million": (0, 3), "red": (2, 0), "green": (2, 1), "white": (2, 4), "party": (5, 1)},
        "monika": {"million": (0, 2), "red": (2, 0), "green": (2, 1), "white": (2, 4), "party": (5, 1)}}[PROFILE]


def layout():
    """Place every chunk; return [(line, chunk, out_start, src_a, src_b)], end time."""
    t, out = 0.25, []
    for i, chunks in enumerate(LINES):
        for j, (a, b_) in enumerate(chunks):
            out.append((i, j, t, a, b_))
            t += (b_ - a + 0.06) / SPEED + (PAUSE if j < len(chunks) - 1 else 0)
        t += GAP + EXTRA.get(i, 0.0)
    return out, t


PLACED, VEND = layout()


def at(i, j):
    return next(p[2] for p in PLACED if p[0] == i and p[1] == j)


def line_start(i):
    return at(i, 0)


# (source frame, output seconds) anchors, strictly increasing in both
ANCH = [(0, 0.0), (4, line_start(0) + 0.02), (b.DROP, at(*KEYS["million"]) + 0.05)]
for i in range(1, 7):
    ANCH.append((SHOTS[i], line_start(i) - 0.12))
    if i == 2:                                                       # mix: hits on Red / Green / White
        ANCH += [(SHOTS[2] + 4, at(*KEYS["red"]) + 0.05), (SHOTS[2] + 22, at(*KEYS["green"]) + 0.3),
                 (SHOTS[2] + 40, at(*KEYS["white"]) + 0.02)]
    if i == 5:
        ANCH[-1] = (SHOTS[5], line_start(5) - 0.12)
        ANCH.append((PRESS, at(*KEYS["party"]) + 0.02))                         # knob press on 'party mode'
ANCH.append((N, line_start(7) - 0.15))
TOTAL_S = max(VEND + 0.4, ANCH[-1][1] + (b.TOTAL - N) / FPS)
ANCH.append((b.TOTAL, TOTAL_S))
for (f0, t0), (f1, t1) in zip(ANCH, ANCH[1:]):
    assert f1 > f0 and t1 > t0, (f0, t0, f1, t1)
SF = np.array([a for a, _ in ANCH], float)
ST = np.array([t for _, t in ANCH], float)
OUT_FRAMES = int(round(TOTAL_S * FPS))
OUT = os.path.join(HERE, "output", "esp32-oled-rgb-color-mixer-VOICE-SHORT.mp4" if PROFILE == "v1" else
                   f"esp32-oled-rgb-color-mixer-VOICE-{PROFILE}-SHORT.mp4")


def src_of(sec):
    return float(np.interp(sec, ST, SF))


def sec_of(f):
    return float(np.interp(f, SF, ST))


def voice_track(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    v = np.frombuffer(raw, np.float32)
    trk = np.zeros(int((TOTAL_S + 0.5) * SR), np.float32)
    fade = int(0.008 * SR)
    for _, _, t0, a, b_ in PLACED:
        seg = v[int(max(0, a - 0.03) * SR):int((b_ + 0.03) * SR)].copy()
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        if SPEED != 1.0:
            seg = tempo(seg)
        j = int(t0 * SR)
        trk[j:j + len(seg)] += seg[:len(trk) - j]
    return trk


def tempo(seg):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={SPEED}", "-f", "f32le", "-"], input=seg.tobytes(), check=True, capture_output=True)
    return np.frombuffer(p.stdout, np.float32)


def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", path],
                   input=x.astype(np.float32).tobytes(), check=True)


def build_audio(voice):
    b.t = sec_of                                                     # all SFX / music cue times follow the map
    total = TOTAL_S + 0.05
    b.fx.write_wav(os.path.join(b.WORK, "music_v.wav"), b.music(total))
    b.fx.write_wav(os.path.join(b.WORK, "sfx_v.wav"), b.sfx_track(total))
    write_wav(os.path.join(b.WORK, "voice_v.wav"), voice_track(voice))
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.8[s];"
          "[2:a]loudnorm=I=-16:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v1][v2];"
          "[m][s]amix=inputs=2:normalize=0[bg];"
          "[bg][v1]sidechaincompress=threshold=0.025:ratio=8:attack=12:release=280[duck];"
          "[duck][v2]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,apad=whole_dur={TOTAL_S:.3f}[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(b.WORK, "music_v.wav"),
                    "-i", os.path.join(b.WORK, "sfx_v.wav"), "-i", os.path.join(b.WORK, "voice_v.wav"),
                    "-filter_complex", fc, "-map", "[out]", "-t", f"{TOTAL_S:.3f}",
                    os.path.join(b.WORK, "mix_v.wav")], check=True)


def frame3d(s):
    """Cross-blend the two nearest rendered frames for a fractional source frame."""
    f0 = int(math.floor(s))
    w = s - f0
    a = b.load3d(min(f0, N - 1))
    if w < 0.05 or f0 + 1 >= N:
        return a
    c = b.load3d(f0 + 1)
    return cv2.addWeighted(a, 1 - w, c, w, 0)


def build_video():
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{b.W}x{b.H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(b.WORK, "mix_v.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    W, H = b.W, b.H
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1)[..., None].astype(np.float32)
    hits = [f0 for f0, _ in b.HOOK_HITS + b.MIX_HITS] + [b.DROP, PRESS]
    for o in range(OUT_FRAMES):
        s = src_of(o / FPS)
        f = int(round(s))
        if s >= N:
            fr = b.outro(int(s - N))
            if s - N < 4:
                k_ = 1 - (s - N) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 20 * k_), 1 + 0.06 * k_)
            fr[0:10, :] = b.YEL
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = frame3d(s)
        z = 1.0
        for h0 in hits:
            a = s - h0
            if 0 <= a < 8:
                z += (0.06 if h0 in (b.DROP, PRESS) else 0.035) * (1 - a / 8) ** 2
        if PRESS <= s < SHOTS[6]:
            z += 0.012 * abs(math.sin((s - PRESS) * math.pi / 6))
        if z > 1.0:
            fr = b.zoom(fr, z)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        c = np.array(b.led_col(f), np.float32)
        k_ = 0.16 if b.mode(f) == "party" else 0.1
        x = x * (1 - k_ * vig) + c * k_ * vig
        fr = b.overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for sh in SHOTS[1:]:
            dd = s - sh
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (o + 1) / OUT_FRAMES)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = b.YEL
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if o % 48 == 0:
            print(f"  frame {o}/{OUT_FRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    for (f0, t0) in ANCH:
        print(f"src {f0:4d} -> {t0:6.2f} s")
    print("lines:", [round(line_start(i), 2) for i in range(len(LINES))], "voice end", round(VEND, 2), "total", round(TOTAL_S, 2))
    if len(sys.argv) > 1 and sys.argv[1].endswith((".mp3", ".wav")):
        build_audio(sys.argv[1])
        build_video()
