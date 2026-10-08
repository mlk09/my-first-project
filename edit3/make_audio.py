#!/usr/bin/env python3
"""Synthesises the full soundtrack for "Robot and the Haunted Bag" (no samples).

Like the reference, there is no voice: a cinematic score plus foley and SFX
carry the story. Everything is generated with numpy from oscillators, noise,
Karplus-Strong plucks and simple filters, then mixed to work/audio/mix.wav.

Score (key: D minor -> D major for the friendship ending), 96 bpm:
  0-12   mysterious: low drone, wind, music-box melody, distant owl
  12-30  tiptoe: pizzicato walking bass + celesta motif (Bolt's theme)
  30-50  curious: suspended strings, the melody stops, ticking
  50-64  haunted: theremin, low brass hits, thunder, choir pad
  64-79  chase: double-time pizzicato, toms, staccato strings
  79-97  hide & search: heartbeat, tremolo, theremin sneaking
  97-106 hiccup comedy: pops, slide whistle, plinks
  106-124 sad: slow music box + warm pad
  124-154 friendship: major key, Bolt's theme in full, sparkles
  154-180 walk home + ending sting
"""
import os
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import BEATS, CUTS, DURATION, TRANSITIONS  # noqa: E402

SR = 48000
N = int(SR * DURATION) + SR
rng = np.random.default_rng(7)
BPM = 96
BEAT = 60 / BPM


def buf():
    return np.zeros((2, N), dtype=np.float32)


def add(dst, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    x = np.array(x, dtype=np.float32)
    fi, fo = min(48, len(x) // 4), min(288, len(x) // 4)  # 1 ms in / 6 ms out: no clicks
    if fi:
        x[:fi] *= np.linspace(0, 1, fi)
        x[-fo:] *= np.linspace(1, 0, fo)
    n = min(len(x), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    dst[0, i:i + n] += x[:n] * gain * l * 1.414
    dst[1, i:i + n] += x[:n] * gain * r * 1.414


def tt(d):
    return np.arange(int(d * SR)) / SR


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(n, s, dtype=np.float32)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    e[a:a + d] = np.linspace(1, s, len(e[a:a + d]))
    if r:
        e[-r:] *= np.linspace(1, 0, len(e[-r:]))
    return e


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, max(fc / (SR / 2), 1e-4), "high")
    return signal.lfilter(b, a, x)


def bp(x, f0, f1, order=2):
    b, a = signal.butter(order, [f0 / (SR / 2), min(f1 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def nn(s):
    """'D4', 'F#3', 'Bb2' -> MIDI note number."""
    base = NAMES[s[0]]
    k = 1
    if s[1] == "#":
        base += 1
        k = 2
    elif s[1] == "b":
        base -= 1
        k = 2
    return base + 12 * (int(s[k:]) + 1)


# ------------------------------------------------------------------ instruments


def pluck(f, d=1.2, bright=0.5):
    """Karplus-Strong pizzicato."""
    n = int(d * SR)
    p = max(2, int(SR / f))
    x = rng.uniform(-1, 1, p) * 0.8
    x = lp(x, 2000 + 6000 * bright)
    out = np.zeros(n)
    buf_ = np.array(x, dtype=np.float64)
    for i in range(0, n, p):
        seg = buf_[: min(p, n - i)]
        out[i:i + len(seg)] = seg
        buf_ = 0.5 * (buf_ + np.roll(buf_, 1)) * 0.994
    return out * np.exp(-tt(d) * 2.5)


def musicbox(f, d=1.6):
    t = tt(d)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 6)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 14) + 0.12 * np.sin(2 * np.pi * f * 3.01 * t))
    return x * np.exp(-t * 3.2) * (1 - np.exp(-t * 900))


def celesta(f, d=1.2):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 10)
    return x * np.exp(-t * 4.0) * (1 - np.exp(-t * 600))


def saw(f, t, detune=0.0):
    ph = (f * (1 + detune) * t) % 1.0
    return 2 * ph - 1


def pad(freqs, d, cutoff=1200, a=1.5, r=2.0, vib=0.0):
    t = tt(d)
    x = np.zeros_like(t)
    for f in freqs:
        for dt in (-0.004, 0.0, 0.005):
            x += saw(f * (1 + vib * np.sin(2 * np.pi * 5 * t)), t, dt)
    x = lp(x / (3 * len(freqs)), cutoff, 2)
    return x * env_adsr(len(t), a, 0.5, 0.9, r)


def strings_stacc(f, d=0.22):
    t = tt(d)
    x = sum(saw(f, t, dt) for dt in (-0.003, 0.003)) / 2
    return lp(x, 2400) * env_adsr(len(t), 0.005, 0.08, 0.5, 0.08)


def theremin(path, d, vib=6.0, depth=0.012):
    """path: list of (time, midi) glides."""
    t = tt(d)
    ts = [p[0] for p in path]
    fs = [note_hz(p[1]) for p in path]
    f = np.interp(t, ts, fs)
    f = f * (1 + depth * np.sin(2 * np.pi * vib * t) * np.clip(t * 2, 0, 1))
    ph = np.cumsum(f) / SR
    x = np.sin(2 * np.pi * ph) + 0.15 * np.sin(4 * np.pi * ph)
    return x * env_adsr(len(t), 0.25, 0.2, 0.9, 0.6)


def choir(freqs, d, vowel=(700, 1150)):
    t = tt(d)
    x = np.zeros_like(t)
    for f in freqs:
        for dt in (-0.006, 0.0, 0.007):
            x += saw(f * (1 + 0.006 * np.sin(2 * np.pi * 4.6 * t + dt * 900)), t, dt)
    y = bp(x, vowel[0] * 0.75, vowel[0] * 1.3) + 0.6 * bp(x, vowel[1] * 0.8, vowel[1] * 1.25)
    return y / (2 * len(freqs)) * env_adsr(len(t), 1.2, 0.5, 0.9, 1.8)


def kick(d=0.5, f0=110, f1=42):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 22)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def tom(f=110, d=0.45):
    t = tt(d)
    fr = f * (1 + 0.5 * np.exp(-t * 30))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 8)
    return x + 0.15 * lp(rng.uniform(-1, 1, len(t)), 3000) * np.exp(-t * 30)


def boom(d=3.0):
    t = tt(d)
    f = 30 + 60 * np.exp(-t * 4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    n = lp(rng.uniform(-1, 1, len(t)), 400) * np.exp(-t * 2.5) * 0.8
    return (x + n) * (1 - np.exp(-t * 300))


def brass_hit(freqs, d=1.6):
    t = tt(d)
    x = sum(saw(f, t, dt) for f in freqs for dt in (-0.004, 0.004))
    cutoff = 400 + 2600 * np.exp(-t * 3)
    y = np.zeros_like(t)
    # time-varying lowpass in blocks
    blk = 2048
    zi = None
    for i in range(0, len(t), blk):
        b, a = signal.butter(2, cutoff[i] / (SR / 2), "low")
        seg, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi if zi is not None else signal.lfilter_zi(b, a) * 0)
        y[i:i + blk] = seg
    return y / (2 * len(freqs)) * env_adsr(len(t), 0.02, 0.3, 0.6, 0.8)


def noise(d):
    return rng.uniform(-1, 1, int(d * SR))


def whoosh(d=0.8, up=True):
    t = tt(d)
    n = noise(d)
    y = np.zeros_like(n)
    blk = 512
    zi = np.zeros(2)
    for i in range(0, len(n), blk):  # swept band-pass, filter state carried across blocks
        u = i / len(n)
        fc = 300 + 3500 * (u if up else 1 - u)
        bb, aa = signal.butter(1, [fc * 0.6 / (SR / 2), min(fc * 1.6 / (SR / 2), 0.99)], "band")
        y[i:i + blk], zi = signal.lfilter(bb, aa, n[i:i + blk], zi=zi)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return y * e * 1.6


def riser(d=1.5):
    t = tt(d)
    f = 200 * (1 + 4 * (t / d) ** 2)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + 0.5 * hp(noise(d), 2000)
    return x * (t / d) ** 2


def sparkle(d=1.5, base=1800, n=10, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(int(d * SR))
    for k in range(n):
        f = base * 2 ** (r.integers(0, 12) / 12) * r.choice((1, 2))
        s = celesta(f, 0.6) * 0.5
        i = int(k / n * (d - 0.6) * SR)
        out[i:i + len(s)] += s[: len(out) - i]
    return out


def beep(f, d=0.12, sq=True):
    t = tt(d)
    x = np.sign(np.sin(2 * np.pi * f * t)) if sq else np.sin(2 * np.pi * f * t)
    return lp(x, 4000) * env_adsr(len(t), 0.003, 0.02, 0.8, 0.03) * 0.5


def servo(d=0.35, f0=300, f1=600):
    t = tt(d)
    f = np.linspace(f0, f1, len(t))
    x = saw(1, np.cumsum(f) / SR)
    x = bp(x + 0.3 * noise(d), 200, 3000)
    return x * env_adsr(len(t), 0.02, 0.05, 0.8, 0.08) * 0.35


def owl(d=1.4):
    out = np.zeros(int(d * SR))
    for st, dur, f in ((0.0, 0.25, 380), (0.4, 0.55, 360)):
        t = tt(dur)
        x = np.sin(2 * np.pi * f * t * (1 - 0.06 * t / dur)) * np.sin(np.pi * t / dur) ** 1.5
        x = x + 0.2 * bp(noise(dur), 300, 900) * np.sin(np.pi * t / dur)
        i = int(st * SR)
        out[i:i + len(x)] += x
    return out


def ghost_wooo(d=3.2):
    t = tt(d)
    f = note_hz(nn("A3")) * (1 + 0.35 * np.sin(np.pi * t / d)) * (1 + 0.02 * np.sin(2 * np.pi * 5.5 * t))
    x = saw(1, np.cumsum(f) / SR)
    y = bp(x, 400, 900) * 1.4 + 0.5 * bp(x, 900, 1400)
    y += 0.35 * bp(noise(d), 500, 2500) * np.sin(np.pi * t / d)
    return y * env_adsr(len(t), 0.4, 0.3, 0.85, 0.9)


def hic(d=0.35):
    t = tt(d)
    f = 520 * (1 + 0.8 * np.exp(-t * 18))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    return x + 0.4 * bp(noise(d), 800, 3000) * np.exp(-t * 40)


def pop(f=900):
    t = tt(0.12)
    fr = f * (1 + 2 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 35)


def slide_whistle(f0, f1, d=0.7):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))
    return x * env_adsr(len(t), 0.03, 0.1, 0.8, 0.1) * 0.5


def thunder(d=5.0):
    t = tt(d)
    n = noise(d)
    x = lp(n, 160) * 3 + 0.4 * lp(n, 900) * np.exp(-t * 3)
    crack = hp(noise(0.25), 1200) * np.exp(-tt(0.25) * 18)
    x[: len(crack)] += crack * 1.2
    e = (1 - np.exp(-t * 40)) * np.exp(-t * 0.8) * (1 + 0.6 * np.sin(2 * np.pi * 1.3 * t) ** 2)
    return x * e


def heartbeat():
    return np.concatenate([kick(0.18, 70, 40) * 0.9, np.zeros(int(0.09 * SR)), kick(0.25, 62, 38) * 0.7])


def wheel_roll(d, speed=1.0):
    t = tt(d)
    n = noise(d)
    x = bp(n, 120, 700) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 6 * speed * t)))
    return x * env_adsr(len(t), 0.2, 0.1, 1, 0.3) * 0.35


# ------------------------------------------------------------------ the score


def chord_tones(root, quality):
    iv = {"m": (0, 3, 7), "M": (0, 4, 7), "sus": (0, 5, 7), "dim": (0, 3, 6), "m7": (0, 3, 7, 10),
          "M7": (0, 4, 7, 11), "aug": (0, 4, 8)}[quality]
    return [note_hz(root + i) for i in iv]


def score():
    m = buf()
    # ---- 0-12: drone + music box (Bolt's theme in minor)
    drone = pad([note_hz(nn("D2")), note_hz(nn("A2"))], 13.0, cutoff=500, a=3, r=2)
    add(m, drone, 0.0, 0.5)
    theme_minor = ["D5", "F5", "A5", "G5", "F5", "E5", "D5", "A4", "Bb4", "D5", "C#5", "A4"]
    for i, n in enumerate(theme_minor):
        add(m, musicbox(note_hz(nn(n))), 1.2 + i * BEAT * 0.75, 0.22, pan=0.3 * np.sin(i))
    add(m, choir([note_hz(nn("D4")), note_hz(nn("F4")), note_hz(nn("A4"))], 6.5, (500, 900)), 5.6, 0.18)
    add(m, brass_hit([note_hz(nn("D2")), note_hz(nn("A2")), note_hz(nn("D3"))], 3.0), 6.0, 0.55)
    add(m, boom(4.0), 6.0, 0.5)
    # ---- 12-30: tiptoe pizzicato walk + celesta theme
    t0 = 12.0
    bass = ["D3", "A2", "F3", "A2", "D3", "A2", "G3", "A2", "Bb2", "F2", "A2", "E2"]
    walk_len = 30.4 - t0
    nb = int(walk_len / (BEAT / 2))
    for k in range(nb):
        t = t0 + k * BEAT / 2
        if 21.0 <= t < 23.6:  # owl scare: band stops
            continue
        n = bass[k % len(bass)]
        add(m, pluck(note_hz(nn(n)), 0.8, 0.4), t, 0.5, pan=-0.2)
        if k % 4 == 2:
            add(m, pluck(note_hz(nn(n) + 12), 0.5, 0.7), t, 0.22, pan=0.3)
    cel = ["D5", "E5", "F5", "A5", None, "G5", "F5", "E5", "D5", None, "A4", None,
           "F5", "G5", "A5", "D6", None, "C6", "A5", "G5", "A5", None, None, None]
    for k, n in enumerate(cel):
        t = 13.0 + k * BEAT / 2
        if n and not (20.8 <= t < 23.8):
            add(m, celesta(note_hz(nn(n))), t, 0.28, pan=0.25)
    for k, n in enumerate(cel):
        t = 23.7 + k * BEAT / 2
        if n and t < 30.3:
            add(m, celesta(note_hz(nn(n))), t, 0.24, pan=-0.25)
    add(m, pad(chord_tones(nn("D3"), "m"), 18.6, cutoff=900, a=2, r=1.5), 12.0, 0.18)
    add(m, brass_hit([note_hz(nn("C#3")), note_hz(nn("G3"))], 1.5), 21.0, 0.35)
    # ---- 30-50: curious, suspended
    add(m, pad(chord_tones(nn("D3"), "sus") + [note_hz(nn("A4"))], 14.5, cutoff=1400, a=2, r=2), 30.4, 0.22)
    for k in range(int(13.5 / BEAT)):
        add(m, beep(2400, 0.02, sq=False), 30.6 + k * BEAT, 0.12, pan=0.5 * ((-1) ** k))
    for k, n in enumerate(["A5", None, "B5", None, "C6", None, "B5"]):
        if n:
            add(m, musicbox(note_hz(nn(n))), 35.6 + k * 0.45, 0.2)
    add(m, theremin([(0, nn("A4")), (2.5, nn("Bb4")), (4.0, nn("A4"))], 4.5, 5, 0.008), 39.5, 0.12)
    add(m, pad(chord_tones(nn("Bb2"), "aug"), 6.5, cutoff=800, a=3, r=0.5), 43.5, 0.25)
    # ---- 50-64: HAUNTED
    add(m, riser(1.6), 48.4, 0.35)
    add(m, brass_hit([note_hz(nn("D2")), note_hz(nn("F2")), note_hz(nn("Ab2"))], 2.4), 50.0, 0.7)
    add(m, choir([note_hz(nn("D4")), note_hz(nn("F4")), note_hz(nn("Ab4"))], 14.0, (600, 1000)), 50.2, 0.32)
    add(m, theremin([(0, nn("D5")), (1.2, nn("A5")), (2.4, nn("Ab5")), (3.4, nn("F5")), (5.0, nn("D5")),
                     (6.4, nn("Bb4")), (8, nn("A4"))], 8.6), 52.6, 0.22)
    add(m, pad([note_hz(nn("D1")), note_hz(nn("Ab1"))], 14.6, cutoff=300, a=1, r=1), 50.0, 0.6)
    for k in range(int(9 / (BEAT))):
        add(m, tom(70, 0.5), 55.0 + k * BEAT, 0.35)
    add(m, brass_hit([note_hz(nn("D2")), note_hz(nn("Ab2")), note_hz(nn("D3"))], 2.0), 59.5, 0.6)
    add(m, boom(3.5), 59.5, 0.45)
    # ---- 64-79: CHASE (double time)
    add(m, brass_hit([note_hz(nn("D3")), note_hz(nn("F3")), note_hz(nn("A3"))], 1.2), 64.6, 0.6)
    sb = BEAT / 4
    chase_bass = ["D3", "D3", "F3", "D3", "G3", "D3", "Ab3", "G3"]
    k = 0
    t = 65.0
    while t < 78.6:
        n = chase_bass[k % 8]
        add(m, pluck(note_hz(nn(n)), 0.35, 0.8), t, 0.42, pan=-0.3)
        if k % 2 == 0:
            add(m, strings_stacc(note_hz(nn(n) + 12)), t, 0.3, pan=0.3)
        if k % 4 == 0:
            add(m, kick(0.4), t, 0.55)
        if k % 8 == 4:
            add(m, tom(140, 0.3), t, 0.4, pan=0.4)
        if k % 8 == 6:
            add(m, tom(100, 0.3), t, 0.4, pan=-0.4)
        k += 1
        t += sb
    chase_mel = ["D5", "F5", "E5", "D5", "A5", "G5", "F5", "E5", "D5", "F5", "A5", "D6", "C#6", "A5", "F5", "E5"]
    for i, n in enumerate(chase_mel * 2):
        tm = 65.0 + i * BEAT / 2
        if tm < 78.4:
            add(m, strings_stacc(note_hz(nn(n)), 0.26), tm, 0.26, pan=0.15)
    add(m, pad(chord_tones(nn("D3"), "m"), 14.2, cutoff=1600, a=0.3, r=0.6), 64.8, 0.2)
    add(m, brass_hit([note_hz(nn("D2")), note_hz(nn("A2"))], 2.2), 78.5, 0.5)
    # ---- 79-97: hide & search
    k = 0
    t = 79.2
    while t < 96.8:
        add(m, heartbeat(), t, 0.5)
        t += 0.85 if t < 90 else 0.6
    add(m, pad([note_hz(nn("D2")), note_hz(nn("Eb3"))], 18.0, cutoff=600, a=2, r=1), 79.0, 0.3)
    add(m, theremin([(0, nn("F4")), (2, nn("A4")), (3.5, nn("G#4")), (5, nn("D5")), (7, nn("C#5")),
                     (9, nn("F4"))], 9.5), 83.0, 0.13)
    trem = pad(chord_tones(nn("D4"), "dim"), 7.0, cutoff=2500, a=3, r=0.3) * \
        (0.6 + 0.4 * np.sin(2 * np.pi * 12 * tt(7.0)))
    add(m, trem, 90.0, 0.22)
    add(m, riser(3.5), 93.4, 0.45)
    # ---- 97-106: the hiccup gag
    for k, n in enumerate(["C6", "E6", "G6", "C7"]):
        add(m, pluck(note_hz(nn(n)), 0.5, 0.9), 98.3 + k * 0.12, 0.3)
    bounce = ["G4", "C5", "G4", "E5", "G4", "C5", "D5", "B4"]
    for k, n in enumerate(bounce * 2):
        add(m, pluck(note_hz(nn(n)), 0.4, 0.6), 99.2 + k * BEAT / 2, 0.3, pan=0.2 * ((-1) ** k))
        if k % 2 == 0:
            add(m, pluck(note_hz(nn("C3") + (0 if k % 4 == 0 else 7)), 0.6, 0.4), 99.2 + k * BEAT / 2, 0.35)
    # ---- 106-124: sad / lonely
    sad = [("D5", 0), ("C5", 1), ("Bb4", 2), ("A4", 3.5), ("G4", 5), ("A4", 6), ("F4", 7.5), ("E4", 9),
           ("D4", 10.5), ("F4", 12.5), ("E4", 13.5), ("C#4", 15), ("D4", 16.5)]
    for n, b in sad:
        add(m, musicbox(note_hz(nn(n)), 2.4), 106.6 + b, 0.26)
    for st, ch in ((106.0, ("Bb2", "M")), (110.0, ("G2", "m")), (114.0, ("A2", "M")), (118.0, ("D2", "m"))):
        add(m, pad(chord_tones(nn(ch[0]), ch[1]) + [note_hz(nn(ch[0]) + 12)], 4.6, cutoff=700, a=1.5, r=1.5), st, 0.3)
    add(m, pad(chord_tones(nn("G2"), "M"), 6.4, cutoff=900, a=2, r=1.5), 118.5, 0.25)
    # ---- 124-154: friendship (D major), Bolt's theme in full
    prog = [("D3", "M"), ("B2", "m"), ("G2", "M"), ("A2", "M")]
    t = 124.0
    k = 0
    while t < 154.0:
        root, q = prog[(k // 2) % 4]
        add(m, pad(chord_tones(nn(root), q) + [note_hz(nn(root) + 12)], 2 * BEAT * 2 + 0.6,
                   cutoff=1500 if t > 134 else 1000, a=0.6, r=0.6), t, 0.22)
        if t >= 129.4:
            for b in range(4):
                tb = t + b * BEAT
                add(m, pluck(note_hz(nn(root) - (0 if b % 2 == 0 else -7)), 0.6, 0.45), tb, 0.4, pan=-0.2)
                if t >= 140 and b % 2 == 0:
                    add(m, kick(0.35, 90, 45), tb, 0.35)
                if t >= 140 and b % 2 == 1:
                    add(m, 0.25 * hp(noise(0.12), 3000) * np.exp(-tt(0.12) * 30), tb, 1.0)
        t += 2 * BEAT * 2 / 2
        k += 1
    theme_major = ["D5", "F#5", "A5", "G5", "F#5", "E5", "D5", "A4", "B4", "D5", "E5", "F#5",
                   "G5", "F#5", "E5", "D5", "B4", "C#5", "D5", None, "A5", "B5", "A5", "F#5",
                   "G5", "A5", "B5", "D6", "C#6", "A5", "D6", None]
    for rep_ in range(3):
        start = 129.4 + rep_ * len(theme_major) * BEAT / 2
        for i, n in enumerate(theme_major):
            tm = start + i * BEAT / 2
            if n and tm < 153.6:
                inst = celesta if rep_ != 1 else musicbox
                add(m, inst(note_hz(nn(n))), tm, 0.3, pan=0.25 * np.sin(i))
                if rep_ == 2:
                    add(m, strings_stacc(note_hz(nn(n)), 0.3), tm, 0.12)
    # ---- 154-180: walk home + ending
    t = 154.0
    k = 0
    walk = ["D3", "A2", "B2", "F#2", "G2", "D2", "G2", "A2"]
    while t < 170.5:
        n = walk[k % 8]
        add(m, pluck(note_hz(nn(n)), 0.7, 0.4), t, 0.45, pan=-0.2)
        if k % 2 == 1:
            add(m, pluck(note_hz(nn(n) + 19), 0.4, 0.7), t, 0.18, pan=0.3)
        k += 1
        t += BEAT / 2
    for i, n in enumerate(theme_major[:24]):
        tm = 155.0 + i * BEAT / 2
        if n and tm < 170.4:
            add(m, celesta(note_hz(nn(n))), tm, 0.26, pan=-0.2)
    add(m, pad(chord_tones(nn("D3"), "M"), 9.0, cutoff=1300, a=1.5, r=2), 154.0, 0.2)
    add(m, pad(chord_tones(nn("G2"), "M"), 8.0, cutoff=1300, a=1.5, r=2), 162.0, 0.2)
    # THE END...? sting: big chord, then a spooky question at the wink
    add(m, brass_hit([note_hz(nn("D3")), note_hz(nn("F#3")), note_hz(nn("A3")), note_hz(nn("D4"))], 3.5), 171.0, 0.5)
    add(m, pad(chord_tones(nn("D3"), "M") + [note_hz(nn("D5"))], 4.5, cutoff=2000, a=0.1, r=2.5), 171.0, 0.25)
    add(m, theremin([(0, nn("A4")), (1.2, nn("Bb4")), (2.2, nn("D5"))], 3.2), 174.2, 0.16)
    for k, n in enumerate(["D6", "F6", "A6", "D7"]):
        add(m, musicbox(note_hz(nn(n)), 2.5), 175.6 + k * 0.14, 0.22)
    add(m, pad([note_hz(nn("D2")), note_hz(nn("Ab2"))], 4.0, cutoff=500, a=0.5, r=2.5), 176.0, 0.3)
    return m


# ------------------------------------------------------------------ SFX + foley


def sfx():
    s = buf()
    # wind bed all through, gusting
    d = DURATION + 0.5
    wind = noise(d)
    t = tt(d)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t) * np.sin(2 * np.pi * 0.023 * t + 1)
    wind = bp(wind, 180, 900) * lfo * 0.6 + bp(noise(d), 1500, 3200) * lfo ** 3 * 0.1
    calm = np.interp(t, [0, 120, 128, 180], [1.0, 1.0, 0.45, 0.4])
    add(s, wind * calm, 0.0, 0.32)
    # crickets in the calm parts
    for k in range(260):
        tc = rng.uniform(0, DURATION)
        if 50 < tc < 106:
            continue
        ch = np.sin(2 * np.pi * 4300 * tt(0.05)) * np.abs(np.sin(2 * np.pi * 60 * tt(0.05)))
        add(s, ch * np.hanning(len(ch)), tc, 0.03, pan=rng.uniform(-0.9, 0.9))
    add(s, owl(), 2.5, 0.22, pan=-0.6)
    add(s, owl(), 9.2, 0.15, pan=0.7)
    add(s, owl(), 21.05, 0.4, pan=-0.3)
    # bat flutters
    for t0 in (0.6, 68.8, 166.6):
        for k in range(14):
            fl = bp(noise(0.05), 600, 2500) * np.hanning(int(0.05 * SR))
            add(s, fl, t0 + k * 0.09 + rng.uniform(0, 0.03), 0.2, pan=-0.8 + k * 0.12)
    # Bolt rolling + servo sounds
    for a, b, sp in ((12.0, 21.0, 1.0), (23.5, 30.6, 1.0), (39.2, 41.3, 0.6), (65.6, 78.5, 1.8),
                     (118.0, 122.0, 0.8), (155.5, 168.5, 1.0)):
        add(s, wheel_roll(b - a, sp), a, 0.45)
    for tb, f0, f1 in ((14.0, 400, 700), (17.6, 500, 800), (32.0, 300, 500), (35.6, 500, 900),
                       (41.4, 300, 600), (43.4, 600, 350), (93.2, 300, 800), (100.5, 700, 400),
                       (122.2, 300, 650), (129.8, 400, 700), (148.7, 400, 900), (150.0, 400, 900)):
        add(s, servo(0.35, f0, f1), tb, 0.6)
    # Bolt beeps (his "voice")
    beeps = {16.0: (880, 1320), 19.0: (1046, 880, 1175), 21.1: (1760, 2093, 2637),
             35.6: (660, 990), 37.2: (880, 1320), 44.6: (1568, 2093), 47.0: (2093, 2637, 3136),
             56.0: (1400, 1300, 1400, 1300), 64.7: (2349, 2093, 1760, 2349), 81.5: (700, 660),
             90.6: (1975, 2349), 101.6: (660, 880, 1046), 102.4: (880, 1320),
             119.5: (660, 784), 123.4: (784, 988, 1175), 126.2: (880, 1175, 1320, 1760),
             131.4: (1046, 1320, 1568, 2093), 146.0: (1320, 1760), 151.0: (1046, 1320, 1568),
             163.0: (880, 1175), 172.5: (784, 988, 1175)}
    for tb, fs in beeps.items():
        for k, f in enumerate(fs):
            add(s, beep(f, 0.09), tb + k * 0.1, 0.32, pan=0.1)
    # story SFX
    add(s, whoosh(1.2), 5.4, 0.4)
    st = hp(noise(0.7), 1500) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 23 * tt(0.7))))
    add(s, st, 6.0, 0.22)  # TV static under the raw-clip glitch
    add(s, boom(4), 6.05, 0.35)
    add(s, pop(1300) * 0.7, 44.3, 0.45)
    add(s, bp(noise(0.3), 300, 2000) * np.exp(-tt(0.3) * 12), 44.4, 0.5)  # bag rustle
    add(s, bp(noise(0.4), 250, 1800) * np.exp(-tt(0.4) * 9), 45.8, 0.6)
    add(s, slide_whistle(600, 1400, 0.4), 47.0, 0.35)
    add(s, bp(noise(1.5), 200, 1500) * env_adsr(int(1.5 * SR), 0.3, 0.2, 0.8, 0.6), 50.0, 0.35)
    add(s, whoosh(1.5, up=True), 50.2, 0.35)
    add(s, hp(noise(0.4), 3000) * np.exp(-tt(0.4) * 10), 51.5, 0.25)  # eyes snap open
    add(s, thunder(5.5), 52.15, 0.9)
    add(s, ghost_wooo(3.4), 59.5, 0.55)
    for i in range(17):  # pumpkins igniting (whoomp)
        w = bp(noise(0.35), 150, 900) * np.exp(-tt(0.35) * 9)
        add(s, w, 59.3 + i * 0.28, 0.25, pan=-0.7 + i * 0.08)
    add(s, whoosh(0.7), 64.3, 0.5)
    add(s, servo(0.5, 300, 1500), 64.9, 0.5)
    add(s, whoosh(0.6), 67.7, 0.4)
    add(s, whoosh(0.6), 73.7, 0.4)
    add(s, bp(noise(0.25), 400, 2500) * np.exp(-tt(0.25) * 14), 78.4, 0.5)  # skid
    for k in range(9):  # bag swooshing around while searching
        add(s, whoosh(1.0, up=bool(k % 2)) * 0.6, 80.0 + k * 1.2, 0.25, pan=np.sin(k))
    add(s, whoosh(1.4), 93.0, 0.5)
    add(s, hic(), 97.5, 0.8)
    add(s, boom(1.0) * 0.5, 97.5, 0.3)
    for k in range(28):  # candy spray
        add(s, pop(rng.uniform(900, 2400)), 98.0 + k * 0.035 + rng.uniform(0, 0.02), 0.25,
            pan=rng.uniform(-0.8, 0.8))
        tl = 98.4 + k * 0.035 + rng.uniform(0.2, 0.7)
        add(s, pop(rng.uniform(2500, 4000)) * 0.5, tl, 0.18, pan=rng.uniform(-0.8, 0.8))
    add(s, slide_whistle(1600, 500, 0.8), 100.6, 0.3)
    add(s, pop(700), 101.5, 0.6)  # bonk on the head
    add(s, sparkle(1.2, 2400, 6, seed=1), 101.6, 0.25)
    add(s, bp(noise(1.2), 300, 1200) * env_adsr(int(1.2 * SR), 0.1, 0.2, 0.6, 0.8), 106.2, 0.25)
    add(s, sparkle(0.8, 3000, 4, seed=2) * 0.5, 109.2, 0.25)  # tear glint
    add(s, sparkle(2.2, 1600, 12, seed=3), 124.2, 0.3)
    add(s, sparkle(3.0, 2000, 18, seed=4), 130.3, 0.3)
    add(s, bp(noise(0.5), 200, 900) * np.exp(-tt(0.5) * 6), 130.9, 0.4)  # squishy hug
    add(s, sparkle(5.5, 2200, 30, seed=5), 134.2, 0.25)
    add(s, whoosh(1.5), 140.0, 0.45)
    add(s, sparkle(6.0, 1800, 28, seed=6), 140.6, 0.2)
    for k in range(5):
        add(s, whoosh(1.0, up=bool(k % 2)) * 0.6, 142.0 + k * 0.9, 0.3, pan=np.sin(k * 1.3))
    add(s, pop(400) * 0.8, 148.5, 0.4)
    add(s, sparkle(2.0, 2600, 10, seed=7), 146.2, 0.3)
    for k in range(13):  # windows lighting up
        add(s, celesta(note_hz(nn("D6") + [0, 4, 7, 12, 16][k % 5]), 0.6), 156.6 + k * 0.25, 0.12)
    add(s, whoosh(1.0), 170.6, 0.35)
    add(s, sparkle(1.0, 3200, 4, seed=8), 175.5, 0.3)  # the wink
    add(s, slide_whistle(900, 1500, 0.25), 175.55, 0.25)
    # transitions
    for c, kind in TRANSITIONS.items():
        if kind == "trunk":
            add(s, whoosh(0.9) * 0.8, c - 0.45, 0.35)
        if kind == "whip":
            add(s, whoosh(0.5), c - 0.3, 0.45)
        elif kind == "dip":
            add(s, whoosh(1.2, up=False) * 0.6, c - 0.7, 0.25)
    return s


# ------------------------------------------------------------------ mix


def reverb(x, decay=1.8, mix=0.25):
    """Cheap stereo convolution reverb from an exponentially decaying noise IR."""
    n = int(decay * SR)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.9 / decay)
        ir = lp(ir, 5000)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = signal.fftconvolve(x[ch], ir)[: x.shape[1]]
    return x * (1 - mix) + out * mix * 1.2


def main():
    out = os.path.join(HERE, "work", "audio")
    os.makedirs(out, exist_ok=True)
    print("score...")
    mus = reverb(score(), 2.6, 0.32)
    print("sfx...")
    fx = reverb(sfx(), 1.4, 0.18)
    # duck the music a little under big SFX moments
    duck = np.ones(N)
    for t0, t1, g in ((52.1, 54.0, 0.55), (59.4, 62.8, 0.7), (97.4, 98.6, 0.6)):
        i0, i1 = int(t0 * SR), int(t1 * SR)
        duck[i0:i1] = g
    duck = lp(duck, 4)
    mix = mus * 0.9 * duck + fx
    mix = mix[:, : int(DURATION * SR)]
    # fade in/out
    fi, fo = int(0.3 * SR), int(3.5 * SR)
    mix[:, :fi] *= np.linspace(0, 1, fi)
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
    mix /= np.max(np.abs(mix)) * 1.05
    from scipy.io import wavfile
    wavfile.write(os.path.join(out, "mix.wav"), SR, (mix.T * 32767).astype(np.int16))
    wavfile.write(os.path.join(out, "music.wav"), SR, (np.clip(mus[:, : int(DURATION * SR)] / np.max(np.abs(mus)), -1, 1).T * 32767).astype(np.int16))
    print("ok", mix.shape)


if __name__ == "__main__":
    main()
