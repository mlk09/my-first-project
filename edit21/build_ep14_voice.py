#!/usr/bin/env python3
"""EP 14 Strings + methods - VOICE-OVER version (assets/voiceoverStrings.mp3, 57 s).

The ElevenLabs take runs longer than the 60 s cut, so instead of squeezing the voice the VIDEO CLOCK is
time-warped: every scene is stretched (or tightened) so its animation lands on the matching words
(spaces zip out on "saaf!", tiles flip on "CHAI!", chai becomes coffee on "coffee!", ...).
SFX are moved with the same warp, music ducks under the voice, master -14 LUFS.

Usage:  python3 edit21/build_ep14_voice.py [--audio-only]
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep14 as e   # noqa: E402

m, fx, bs = e.m, e.fx, e.bs
VOICE = os.path.join(HERE, "assets", "voiceoverStrings.mp3")

# (source time in the 60 s cut, output time)
WARP = [(0.0, 0.0), (3.8, 4.4), (6.2, 5.8), (8.0, 9.1), (10.2, 13.3), (13.0, 16.0), (17.0, 19.6), (20.0, 21.4),
        (23.4, 23.3), (24.6, 25.0), (26.5, 26.7), (30.3, 30.2), (33.0, 31.6), (36.6, 33.4), (37.6, 34.4),
        (39.5, 36.0), (43.0, 39.4), (44.0, 40.4), (46.0, 41.9), (49.6, 44.0), (51.0, 45.2), (55.6, 48.5),
        (56.0, 49.6), (59.0, 52.6), (60.5, 55.0), (65.5, 60.0)]
SRC, DST = np.array([a for a, _ in WARP]), np.array([b for _, b in WARP])
TOTAL = float(DST[-1])

# voice lines: (start, end) inside the mp3 -> start time in the output
LINES = [((0.00, 4.08), 0.2), ((4.65, 9.12), 4.5), ((9.62, 16.33), 9.05), ((16.97, 21.22), 16.1),
         ((21.76, 26.79), 21.5), ((27.38, 31.50), 26.8), ((31.98, 36.09), 31.7), ((36.56, 42.18), 36.1),
         ((42.48, 44.80), 42.5), ((45.27, 49.67), 45.3), ((50.17, 52.33), 52.1), ((52.67, 57.00), 55.1)]
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP14_Strings_VO.mp4")
WORK = os.path.join(HERE, "work_vo")


def src_of(t_out):
    return float(np.interp(t_out, DST, SRC))


def out_of(t_src):
    return float(np.interp(t_src, SRC, DST))


def frame(i):
    return e.frame(i, src_of(i / e.FPS))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=out_of(46.0))
    fx.write_wav(os.path.join(WORK, "music.wav"), music)
    # SFX: same events, moved with the warp
    place0 = fx.place
    fx.place = lambda buf, sig, t, gain=1.0: place0(buf, sig, out_of(t), gain)
    total0, e.TOTAL = e.TOTAL, TOTAL
    try:
        sfx = e.sfx_track()
    finally:
        fx.place, e.TOTAL = place0, total0
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx * 0.8)
    parts, labels = [], []
    for k, ((s, en), cue) in enumerate(LINES):
        parts.append(f"[2:a]atrim={s:.3f}:{en:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                     f"afade=t=out:st={max(0.0, en - s - 0.05):.3f}:d=0.05,adelay={int(cue * 1000)}:all=1[v{k}]")
        labels.append(f"[v{k}]")
    fc = ";".join(parts) + ";" + "".join(labels) + (
        f"amix=inputs={len(LINES)}:normalize=0,highpass=f=85,"
        "acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=2,"
        "loudnorm=I=-16:TP=-2:LRA=7,aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
        "asplit=2[voice][key];"
        "[0:a]loudnorm=I=-20:TP=-4,aformat=sample_rates=48000:channel_layouts=stereo[mus0];"
        "[mus0][key]sidechaincompress=threshold=0.03:ratio=8:attack=30:release=350:makeup=1[mus];"
        "[1:a]volume=-3dB,aformat=sample_rates=48000:channel_layouts=stereo[sfx];"
        "[mus][sfx][voice]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
    out = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i",
                    os.path.join(WORK, "sfx.wav"), "-i", VOICE, "-filter_complex", fc, "-map", "[out]",
                    "-t", f"{TOTAL:.3f}", out], check=True)
    return out


m.OUT, m.WORK, m.TOTAL = OUT, WORK, TOTAL
m.frame, m.build_audio = frame, build_audio

if __name__ == "__main__":
    if "--audio-only" in sys.argv:
        print(build_audio())
    else:
        m.main()
