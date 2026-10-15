#!/usr/bin/env python3
"""Soundtrack for Part 2: voices, two-phase original score, SFX. Everything synthesised here.

Phase A (0-113 s) spooky mystery; Phase B (113-155 s) friendship and celebration;
then the twist (155-180 s). Writes work/mix.wav and work/sync.json (mouth
envelopes for lip-flap, word timings for captions).
"""
import json
import os
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit3"))
sys.path.insert(0, os.path.join(HERE, "..", "short1"))
sys.path.insert(0, HERE)
import make_audio as M  # noqa: E402
import make_short_audio as V  # noqa: E402  (tts, robotize, ghostify)
from timeline_p2 import CARDS, DURATION, FPS, LINES, NARRATOR  # noqa: E402

SR = 48000
N = int(SR * DURATION) + SR
WORK = os.path.join(HERE, "work")
rng = np.random.default_rng(11)


def buf():
    return np.zeros((2, N), np.float32)


def put(b, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or len(x) == 0:
        return
    x = np.array(x, np.float32)
    f = min(240, len(x) // 4)
    if f:
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    n = min(len(x), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
    b[0, i:i + n] += x[:n] * g * l
    b[1, i:i + n] += x[:n] * g * r


def granny_voice(text, deep=False):
    import subprocess
    path = os.path.join(WORK, "g.wav")
    subprocess.run(["espeak-ng", "-v", "en-us+f2", "-p", "58", "-s", "140", "-a", "170", "-w", path, text],
                   check=True)
    sr, x = wavfile.read(path)
    x = signal.resample_poly(x.astype(np.float32) / 32768, 320, 147)
    nz = np.where(np.abs(x) > 0.01)[0]
    x = x[max(0, nz[0] - 200): nz[-1] + 2000]
    t = np.arange(len(x)) / SR
    x = x * (0.85 + 0.15 * np.sin(2 * np.pi * 5.5 * t))          # old-voice tremolo
    x = x + 0.012 * M.hp(rng.uniform(-1, 1, len(x)), 3000) * (np.abs(x) > 0.05)  # crackle
    if deep:  # the giant shadow: an octave down, booming
        x = signal.resample_poly(x, 2, 1)
        x = M.lp(x, 2500) * 1.4
        for k, g in ((int(0.13 * SR), 0.5), (int(0.29 * SR), 0.3)):
            x = x + g * np.concatenate([np.zeros(k), x[:-k]])
    for k, g in ((int(0.05 * SR), 0.2),):
        x = x + g * np.concatenate([np.zeros(k), x[:-k]])
    return x / (np.max(np.abs(x)) + 1e-9)


OLD = {c["text"]: c["t1"] - c["t0"] for c in json.load(open(os.path.join(WORK, "sync_espeak.json")))["captions"]} \
    if os.path.exists(os.path.join(WORK, "sync_espeak.json")) else {}


def voice_for(who, text):
    import voices_kokoro as K  # clear neural voices; each line fitted to its old length
    return K.speak(who, text, OLD.get(text))


def voice_for_espeak(who, text):
    if who == "bolt":
        return V.robotize(V.tts(text, "bolt"))
    if who == "boo":
        return V.ghostify(V.tts(text, "boo"))
    return granny_voice(text, deep=(who == "shadow"))


def word_times(text, x, t0):
    return V.word_times(text, x, t0)


# ------------------------------------------------------------------ score
def phase_a(m):
    nh = lambda s: M.note_hz(M.nn(s))  # noqa: E731
    put(m, M.pad([nh("D2"), nh("A2")], 15.0, cutoff=500, a=3, r=2), 0.0, 0.45)
    for i, n in enumerate(["A4", "D5", "F5", "E5", "D5", "A4"]):  # music box opening
        put(m, M.musicbox(nh(n)), 4.6 + i * 0.6, 0.2, 0.3 * np.sin(i))
    put(m, M.brass_hit([nh("D2"), nh("A2"), nh("D3")], 3.0), 9.0, 0.55)
    put(m, M.boom(4.0), 9.0, 0.5)
    put(m, M.choir([nh("D4"), nh("F4"), nh("A4")], 6.0, (500, 900)), 9.0, 0.2)
    # 15-21: happy candy pile, pizzicato
    k, t = 0, 15.0
    while t < 20.8:
        put(m, M.pluck(nh(["D3", "A2", "F3", "A2"][k % 4]), 0.6, 0.45), t, 0.42, -0.2)
        if k % 2:
            put(m, M.celesta(nh(["D5", "F5", "A5", "G5"][(k // 2) % 4])), t, 0.22, 0.25)
        k += 1
        t += M.BEAT / 2
    # 21-29: midnight bells, fog, yawn
    for i in range(4):
        b = M.tom(nh("D2"), 2.5) * 0.6 + M.musicbox(nh("D3"), 2.5) * 0.6
        put(m, b, 21.3 + i * 0.9, 0.55)
    put(m, M.pad([nh("D2"), nh("Ab2")], 8.0, cutoff=600, a=2, r=1), 21.0, 0.35)
    # 29-37: silence beat, then the vanishing (sparse plinks) and the shock
    put(m, M.brass_hit([nh("D3"), nh("F3"), nh("Ab3")], 1.6), 33.0, 0.5)
    # 37-65: theremin mystery + tiptoe
    put(m, M.theremin([(0, M.nn("A4")), (2, M.nn("D5")), (3.5, M.nn("C#5")), (6, M.nn("F5")),
                       (8, M.nn("E5")), (11, M.nn("A4"))], 12.0), 37.0, 0.14)
    put(m, M.pad([nh("D2"), nh("A2"), nh("F3")], 28.0, cutoff=700, a=2, r=2), 37.0, 0.3)
    k, t = 0, 42.6
    while t < 60.6:
        if not 46.0 <= t < 48.0:
            put(m, M.pluck(nh(["D3", "E3", "F3", "A2", "Bb2", "A2", "G2", "A2"][k % 8]), 0.5, 0.4), t, 0.35)
        k += 1
        t += M.BEAT / 2
    put(m, M.brass_hit([nh("D2"), nh("Ab2")], 2.0), 57.0, 0.5)
    # 65-81: inside, heartbeat, the shadow sting
    put(m, M.pad([nh("D2"), nh("Eb3")], 16.0, cutoff=500, a=2, r=1), 65.0, 0.35)
    t = 67.4
    while t < 80.8:
        put(m, M.heartbeat(), t, 0.45)
        t += 0.85 if t < 72 else 0.55
    put(m, M.riser(2.0), 70.4, 0.4)
    put(m, M.brass_hit([nh("D2"), nh("F2"), nh("Ab2"), nh("B2")], 2.6), 72.5, 0.7)
    put(m, M.choir([nh("D4"), nh("Ab4")], 5.0, (600, 1000)), 72.5, 0.25)
    # 81-108: reveal is cosy and funny, then sad
    for i, n in enumerate(["D5", "F#5", "A5", "D6", "F#6"]):  # harp-ish gliss
        put(m, M.pluck(nh(n), 1.2, 0.8), 81.0 + i * 0.06, 0.3)
    put(m, M.pad(M.chord_tones(M.nn("G2"), "M"), 10.0, cutoff=1100, a=1, r=1.5), 81.0, 0.22)
    sad = [("D5", 0), ("C5", 1), ("Bb4", 2), ("A4", 3.5), ("G4", 5), ("A4", 6), ("F4", 7.5), ("E4", 9),
           ("D4", 10.5), ("F4", 12.5), ("E4", 13.5), ("D4", 15)]
    for n, b in sad:
        put(m, M.musicbox(nh(n), 2.4), 91.6 + b, 0.24)
    for st, (r_, q) in ((91.0, ("Bb2", "M")), (95.5, ("G2", "m")), (100.0, ("A2", "M")), (104.0, ("D2", "m"))):
        put(m, M.pad(M.chord_tones(M.nn(r_), q), 4.6, cutoff=700, a=1.5, r=1.5), st, 0.3)
    put(m, M.sparkle(1.5, 2200, 8, seed=9), 108.2, 0.35)
    put(m, M.riser(3.0), 110.0, 0.4)


def phase_b(m):
    nh = lambda s: M.note_hz(M.nn(s))  # noqa: E731
    prog = [("D3", "M"), ("B2", "m"), ("G2", "M"), ("A2", "M")]
    theme = ["D5", "F#5", "A5", "G5", "F#5", "E5", "D5", "A4", "B4", "D5", "E5", "F#5",
             "G5", "F#5", "E5", "D5", "B4", "C#5", "D5", None, "A5", "B5", "A5", "F#5",
             "G5", "A5", "B5", "D6", "C#6", "A5", "D6", None]
    put(m, M.brass_hit([nh("D3"), nh("F#3"), nh("A3"), nh("D4")], 2.5), 113.0, 0.55)
    put(m, M.boom(3.0), 113.0, 0.4)
    t, k = 115.0, 0
    while t < 155.0:
        root, q = prog[(k // 2) % 4]
        dense = 137.0 <= t < 145.0
        put(m, M.pad(M.chord_tones(M.nn(root), q) + [nh(root) * 2], 2 * M.BEAT * 2 + 0.6, cutoff=1700, a=0.4, r=0.6),
            t, 0.22)
        for b in range(4):
            tb = t + b * M.BEAT
            put(m, M.pluck(nh(root) * (1 if b % 2 == 0 else 1.5), 0.5, 0.5), tb, 0.42, -0.2)
            put(m, M.kick(0.35, 90, 45), tb, 0.45 if b % 2 == 0 else 0.25)
            if b % 2 == 1:
                put(m, 0.3 * M.hp(rng.uniform(-1, 1, int(0.12 * SR)), 3000) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30), tb, 1.0)
            if dense:
                put(m, M.tom(140, 0.25), tb + M.BEAT / 2, 0.3, 0.4)
        t += 2 * M.BEAT
        k += 1
    for rep in range(2):
        start = 115.4 + rep * len(theme) * M.BEAT / 2
        for i, n in enumerate(theme):
            tm = start + i * M.BEAT / 2
            if n and tm < 154.6:
                put(m, M.celesta(nh(n)), tm, 0.3, 0.25 * np.sin(i))
                put(m, M.strings_stacc(nh(n), 0.3), tm, 0.14)
    put(m, M.riser(2.5), 134.5, 0.4)
    put(m, M.brass_hit([nh("D3"), nh("F#3"), nh("A3")], 2.0), 137.0, 0.45)
    put(m, M.pad(M.chord_tones(M.nn("G2"), "M7"), 6.0, cutoff=1300, a=1, r=2), 149.0, 0.28)


def twist(m):
    nh = lambda s: M.note_hz(M.nn(s))  # noqa: E731
    put(m, M.pad([nh("D2"), nh("Eb3")], 5.0, cutoff=700, a=0.3, r=0.5), 155.2, 0.3)
    put(m, M.pad([nh("D1"), nh("Ab1")], 6.5, cutoff=300, a=1.5, r=1.0), 164.0, 0.6)
    put(m, M.theremin([(0, M.nn("D5")), (2, M.nn("Eb5")), (4, M.nn("D5"))], 5.5), 164.3, 0.13)
    put(m, M.brass_hit([nh("D3"), nh("F#3"), nh("A3"), nh("D4")], 3.5), 170.0, 0.55)
    put(m, M.boom(4.0), 170.0, 0.45)
    for i, n in enumerate(["D6", "F#6", "A6", "D7"]):
        put(m, M.musicbox(nh(n), 2.5), 177.6 + i * 0.14, 0.22)


# ------------------------------------------------------------------ SFX
def sfx(s):
    d = DURATION + 0.5
    wind = M.bp(rng.uniform(-1, 1, int(d * SR)), 180, 900)
    tt = np.arange(len(wind)) / SR
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * tt) * np.sin(2 * np.pi * 0.023 * tt + 1)
    inside = 1 - 0.8 * ((tt > 67) & (tt < 113))
    put(s, wind * lfo * inside, 0.0, 0.28)
    st = M.hp(rng.uniform(-1, 1, int(0.9 * SR)), 1500)
    put(s, st, 3.2, 0.2)  # glitch card static
    put(s, M.whoosh(1.0), 3.4, 0.4)
    put(s, M.sparkle(0.8, 3000, 4, seed=1), 4.6, 0.3)  # wink
    for t0, p in ((7.0, -0.6), (23.6, 0.5), (49.5, -0.7), (55.0, 0.6)):
        put(s, M.owl(), t0, 0.22, p)
    for t0 in (15.6, 17.0, 18.4):  # candy into the basket
        put(s, M.pop(1400), t0, 0.35)
    for k in range(12):  # candies vanishing
        put(s, M.pop(rng.uniform(900, 2200)), 29.4 + k * 0.28, 0.4, rng.uniform(-0.6, 0.6))
        put(s, M.sparkle(0.7, 3200, 2, seed=k + 20), 29.45 + k * 0.28, 0.12)
    put(s, M.beep(1760, 0.08), 33.2, 0.3)
    put(s, M.hic(), 35.6, 0.7)
    for k in range(10):  # footprints lighting + distant heavy footsteps
        put(s, M.celesta(M.note_hz(M.nn("A5") + [0, 3, 7, 10, 12][k % 5]), 0.4), 37.4 + k * 0.42, 0.1)
        put(s, M.kick(0.3, 60, 35), 37.6 + k * 0.84 if k < 5 else 99, 0.3)
    for a, b in ((48.0, 53.0), (61.0, 61.0)):
        pass
    put(s, M.wheel_roll(5.0, 0.8), 48.0, 0.4)
    put(s, M.bp(rng.uniform(-1, 1, int(1.2 * SR)), 300, 1200) * np.hanning(int(1.2 * SR)), 53.5, 0.45)  # branch scrape
    put(s, M.slide_whistle(600, 1600, 0.4), 54.6, 0.3)
    for k, f in enumerate((660, 880, 660, 880)):  # Bolt's beep-giggle
        put(s, M.beep(f, 0.07), 55.6 + k * 0.1, 0.3)
    put(s, M.thunder(5.0), 57.05, 0.85)
    creak_t = np.arange(int(2.2 * SR)) / SR
    creak = np.sin(2 * np.pi * np.cumsum(180 + 60 * np.sin(2 * np.pi * 3 * creak_t)) / SR)
    creak = M.bp(np.sign(creak) * 0.5 + 0.3 * rng.uniform(-1, 1, len(creak)), 200, 1500) * np.hanning(len(creak))
    put(s, creak, 61.6, 0.5)  # door creak
    put(s, M.pop(300), 63.0, 0.5)  # gulp
    put(s, M.beep(523, 0.15, sq=False), 63.2, 0.25)
    for k in range(6):  # wrappers crinkle underfoot
        put(s, M.hp(rng.uniform(-1, 1, int(0.15 * SR)), 2500) * np.hanning(int(0.15 * SR)), 68.0 + k * 0.7, 0.18)
    put(s, M.whoosh(0.6), 80.7, 0.5)  # whip pan reveal
    put(s, M.sparkle(1.2, 2600, 6, seed=3), 81.2, 0.3)
    for k in range(10):  # knitting needles click
        put(s, M.hp(rng.uniform(-1, 1, int(0.03 * SR)), 4000), 82.0 + k * 0.32, 0.15)
    put(s, M.sparkle(0.8, 3000, 4, seed=4), 105.0, 0.2)  # Boo's tear
    put(s, M.servo(0.4, 400, 900), 108.1, 0.5)
    for k in range(9):  # montage: Boo hiccups candy
        put(s, M.hic() * 0.6, 115.3 + k * 0.42, 0.4)
        put(s, M.pop(rng.uniform(1000, 2400)), 115.45 + k * 0.42, 0.3)
    for k in range(5):  # wisplings giggle
        put(s, V.ghostify(V.tts("hihihi", "boo", pitch=99)), 119.2 + k * 0.6, 0.18, -0.6 + k * 0.3)
    put(s, M.whoosh(1.5), 123.0, 0.4)
    put(s, M.sparkle(4.0, 2200, 16, seed=5), 123.2, 0.2)
    put(s, M.boom(0.8) * 0.5, 127.2, 0.3)  # pumpkins gasp: faces snap dark
    for i in range(10):  # pumpkins light up happy in a wave
        put(s, M.celesta(M.note_hz(M.nn("D5") + [0, 4, 7, 12, 16][i % 5]), 0.5), 133.5 + i * 0.2, 0.14)
    put(s, M.sparkle(5.0, 2000, 24, seed=6), 137.0, 0.2)
    put(s, M.sparkle(3.0, 2400, 12, seed=7), 144.8, 0.25)
    for k, f in enumerate((1046, 1320, 1568, 2093)):
        put(s, M.beep(f, 0.09), 146.0 + k * 0.1, 0.25)
    rs = np.arange(int(0.5 * SR)) / SR  # record scratch
    scratch = M.bp(rng.uniform(-1, 1, len(rs)), 400, 3000) * np.sin(2 * np.pi * 9 * rs) ** 2
    put(s, scratch, 160.0, 0.6)
    put(s, M.wheel_roll(6.0, 0.6) * 0.0, 164.0, 0.0)
    for k in range(4):  # huge footsteps in the dark
        put(s, M.kick(0.5, 55, 30), 164.6 + k * 0.9, 0.55)
    put(s, M.hp(rng.uniform(-1, 1, int(0.25 * SR)), 1200) * np.exp(-np.arange(int(0.25 * SR)) / SR * 12), 168.5, 0.9)  # CRUNCH
    put(s, M.boom(1.0) * 0.6, 168.5, 0.5)
    put(s, M.pop(700), 175.9, 0.6)  # candy on Bolt's head: POOF
    put(s, M.sparkle(0.6, 3000, 3, seed=8), 175.95, 0.3)
    put(s, V.ghostify(V.tts("hehehe", "boo", pitch=90)), 177.3, 0.25)
    for c, kind in __import__("timeline_p2").TRANSITIONS.items():
        if kind in ("whip", "trunk"):
            put(s, M.whoosh(0.5), c - 0.3, 0.35)
    for t0, _, _ in CARDS:  # trailer card hits
        put(s, M.boom(1.5) * 0.7, t0, 0.4)


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.join(HERE, "..", "short1", "work"), exist_ok=True)
    vo = buf()
    nfr = int(DURATION * FPS) + 1
    env = {w: np.zeros(nfr) for w in ("bolt", "boo", "granny")}
    caps = []
    for t0, who, text in LINES:
        x = voice_for(who, text)
        put(vo, x, t0, 0.95, {"bolt": -0.1, "boo": 0.1}.get(who, 0.0))
        caps.append({"who": who, "t0": t0, "t1": t0 + len(x) / SR, "text": text,
                     "words": word_times(text, x, t0)})
        e = env["granny" if who == "shadow" else who]
        hop = SR // FPS
        for k in range(0, len(x), hop):
            f = int(t0 * FPS) + k // hop
            if f < nfr:
                e[f] = max(e[f], float(np.sqrt(np.mean(x[k:k + hop] ** 2))))
    import voices_kokoro as K
    narr = []
    for t0, t_end, text in NARRATOR:
        x = K.narrate(text, t_end - t0)
        put(vo, x, t0, 1.0)
        narr.append({"t0": t0, "t1": t0 + len(x) / SR, "text": text})
        if t0 + len(x) / SR > t_end + 0.05:
            print("  NARRATION TOO LONG:", round(t0 + len(x) / SR - t_end, 2), text)
    for w in env:
        e = env[w] / (env[w].max() + 1e-9)
        env[w] = np.convolve(e, [0.25, 0.5, 0.25], "same").clip(0, 1)
    mus, fx = buf(), buf()
    phase_a(mus)
    phase_b(mus)
    twist(mus)
    # silence before reveals (the reference's trick): duck the music
    duck = np.ones(N)
    for a, b, g in ((28.8, 29.4, 0.15), (159.95, 164.0, 0.05), (72.3, 72.5, 0.2)):
        duck[int(a * SR):int(b * SR)] = g
    duck = M.lp(duck, 6)
    # keep dialogue clear: music dips under every line
    vo_env = M.lp(np.abs(vo[0]) + np.abs(vo[1]), 8)
    dip = 1 - 0.45 * np.clip(vo_env / (vo_env.max() * 0.15 + 1e-9), 0, 1)
    sfx(fx)
    mus = M.reverb(mus, 2.4, 0.3) * duck * dip
    fx = M.reverb(fx, 1.2, 0.15)
    mix = (vo * 1.0 + mus * 0.75 + fx * 0.7)[:, : int(DURATION * SR)]
    mix[:, -int(2.0 * SR):] *= np.linspace(1, 0, int(2.0 * SR)) ** 1.5
    mix /= np.max(np.abs(mix)) * 1.05
    wavfile.write(os.path.join(WORK, "mix.wav"), SR, (mix.T * 32767).astype(np.int16))
    m2 = mus[:, : int(DURATION * SR)]
    wavfile.write(os.path.join(WORK, "music.wav"), SR, (m2.T / (np.abs(m2).max() + 1e-9) * 32767).astype(np.int16))
    if OLD:  # the 3D frames were animated from the original envelopes: keep them
        env = {k: np.array(v) for k, v in json.load(open(os.path.join(WORK, "sync_espeak.json")))["env"].items()}
    json.dump({"env": {k: v.round(3).tolist() for k, v in env.items()}, "captions": caps, "narration": narr},
              open(os.path.join(WORK, "sync.json"), "w"))
    for c in caps:
        print(f'{c["t0"]:6.1f}-{c["t1"]:6.1f} {c["who"]:6s} {c["text"]}')


if __name__ == "__main__":
    main()
