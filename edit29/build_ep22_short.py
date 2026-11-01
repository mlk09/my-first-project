#!/usr/bin/env python3
"""EP 22 Functions - SHORT cut (about 24.5 s) of build_ep22.py.

Same frames, re-timed: the hook plays at normal speed, then the Maggi recipe, def + call and the
NameError scenes play faster. The video jumps straight from the error scene to the quiz (the loop
and recap scenes are dropped), and the end screen is compressed. SFX are moved with the same time
map; anything in a dropped part is skipped. The music is rebuilt for the new length.

Usage:  python3 edit29/build_ep22_short.py
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep22 as e   # noqa: E402

m, fx, bs, es, p4 = e.p4, e.fx, e.bs, e.es, e.p4
# (src_start, src_end, speed)
SEGS = [(0.0, 3.2, 1.0), (3.2, 10.5, 1.8), (10.5, 19.5, 1.6), (19.5, 26.5, 1.6), (40.0, 45.5, 1.3),
        (e.END0, e.END0 + es.DUR - 0.01, 1.56)]
MAP = []
o = 0.0
for a, b, sp in SEGS:
    MAP.append((o, o + (b - a) / sp, a, sp))
    o += (b - a) / sp
TOTAL = o
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP22_Functions_Short.mp4")
WORK = os.path.join(HERE, "work_short")


def src_of(t):
    for o0, o1, a, sp in MAP:
        if t < o1:
            return a + (t - o0) * sp
    return SEGS[-1][1]


def out_of(t):
    """src time -> (out time, speed) or None if the moment was cut"""
    for o0, o1, a, sp in MAP:
        if a <= t < a + (o1 - o0) * sp:
            return o0 + (t - a) / sp, sp
    return None


def frame(i):
    return e.frame(i, src_of(i / e.FPS))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    fx.write_wav(os.path.join(WORK, "music.wav"), bs.music(TOTAL, drop=0.05, power=out_of(e.ERR_T)[0]))
    events = []
    place0 = fx.place
    fx.place = lambda buf, sig, t, gain=1.0: events.append((sig, t, gain))
    try:
        e.sfx_track()
    finally:
        fx.place = place0
    buf = np.zeros(int((TOTAL + 1) * e.SR))
    for sig, t, gain in events:
        r = out_of(t)
        if r is None:
            continue
        ot, sp = r
        if t >= e.END0 - 1e-3 and len(sig) > e.SR:           # end-screen sfx: compress with the picture
            n = int(len(sig) / sp)
            sig = np.interp(np.linspace(0, len(sig) - 1, n), np.arange(len(sig)), sig)
        place0(buf, sig, ot, gain)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf[: int(TOTAL * e.SR)] * 0.8)
    out = os.path.join(WORK, "mix.wav")
    fc = ("[0:a]loudnorm=I=-18:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[sfx];"
          "[mus][sfx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i",
                    os.path.join(WORK, "sfx.wav"), "-filter_complex", fc, "-map", "[out]", "-t", f"{TOTAL:.3f}", out],
                   check=True)
    return out


p4.OUT, p4.WORK, p4.TOTAL = OUT, WORK, TOTAL
p4.frame, p4.build_audio = frame, build_audio

if __name__ == "__main__":
    print(f"total {TOTAL:.2f}s")
    p4.main()
