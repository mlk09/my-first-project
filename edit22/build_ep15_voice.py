#!/usr/bin/env python3
"""EP 15 String Slicing - VOICE-OVER version (assets/voiceoverSlicing.mp3, 64.8 s).

The ElevenLabs take runs longer than the 60 s cut, so instead of squeezing the voice the VIDEO CLOCK is
time-warped: every scene is stretched (or tightened) so its animation lands on the matching words
(spaces zip out on "saaf!", tiles flip on "CHAI!", chai becomes coffee on "coffee!", ...).
SFX are moved with the same warp, music ducks under the voice, master -14 LUFS.

Usage:  python3 edit22/build_ep15_voice.py [--audio-only]
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep15 as e   # noqa: E402

m, fx, bs = e.m, e.fx, e.bs
VOICE = os.path.join(HERE, "assets", "voiceoverSlicing.mp3")

# (source time in the 60 s cut, output time)
WARP = [(0.0, 0.0), (2.0, 4.4), (3.6, 7.6), (4.8, 9.5), (5.2, 11.5), (6.2, 13.4), (7.0, 14.6), (7.6, 15.3),
        (8.6, 15.8), (12.5, 16.25), (14.3, 18.1), (15.3, 20.2), (16.2, 21.6), (17.6, 23.5), (21.5, 25.6),
        (24.2, 27.4), (26.4, 29.4), (27.4, 30.4), (30.0, 31.2), (33.0, 33.6), (34.2, 34.8), (37.5, 36.2),
        (40.6, 39.9), (41.8, 41.1), (45.5, 41.6), (49.1, 43.5), (50.5, 44.6), (52.4, 46.3), (55.2, 48.9),
        (56.0, 50.4), (59.0, 53.4), (60.5, 58.8), (65.5, 68.2)]
SRC, DST = np.array([a for a, _ in WARP]), np.array([b for _, b in WARP])
TOTAL = float(DST[-1])

# voice: everything up to "Comment karo!" plays straight; the answer + outro start after a 2.6 s countdown gap
LINES = [((0.00, 50.43), 0.2), ((50.43, 64.76), 53.23)]
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP15_String_Slicing_VO.mp4")
WORK = os.path.join(HERE, "work_vo")


def src_of(t_out):
    return float(np.interp(t_out, DST, SRC))


def out_of(t_src):
    return float(np.interp(t_src, SRC, DST))


def frame(i):
    return e.frame(i, src_of(i / e.FPS))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=out_of(45.5))
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
