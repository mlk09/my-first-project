#!/usr/bin/env python3
"""EP 13 break, continue, pass - VOICE-OVER version (assets/voiceoverBreakContinuePass.mp3, 72.8 s).

The ElevenLabs take runs longer than the 60 s cut, so instead of squeezing the voice the VIDEO CLOCK is
time-warped: every scene is stretched (or tightened) so its animation lands on the matching words
(e.g. the red wall slams on "dhadaam!", ball 3 hops on "teen ko jump!", each summary row on its line).
SFX are moved with the same warp, music ducks under the voice, master -14 LUFS.

Usage:  python3 edit20/build_ep13_voice.py [--audio-only]
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep13 as e   # noqa: E402

m, fx, bs = e.m, e.fx, e.bs
VOICE = os.path.join(HERE, "assets", "voiceoverBreakContinuePass.mp3")

# (source time in the 60 s cut, output time)
WARP = [(0.0, 0.0), (3.85, 5.6), (6.0, 9.0), (9.5, 14.1), (11.45, 16.7), (11.92, 19.1), (17.05, 22.2),
        (19.0, 25.5), (22.3, 28.3), (23.75, 29.8), (25.25, 31.9), (29.05, 35.6), (31.0, 38.7), (35.5, 43.0),
        (37.5, 44.4), (38.0, 45.3), (38.5, 47.35), (39.0, 49.6), (40.6, 51.5), (42.6, 52.3), (46.8, 55.7),
        (47.9, 58.3), (50.9, 61.3), (55.0, 67.6), (60.0, 72.6)]
SRC, DST = np.array([a for a, _ in WARP]), np.array([b for _, b in WARP])
TOTAL = float(DST[-1])

# voice lines: (start, end) inside the mp3 -> start time in the output
LINES = [((0.00, 5.28), 0.2), ((5.89, 9.05), 5.7), ((9.60, 14.43), 9.0), ((14.93, 22.83), 14.1),
         ((23.44, 26.63), 22.2), ((27.09, 29.75), 25.5), ((30.25, 37.35), 28.3), ((37.99, 40.93), 35.6),
         ((41.51, 47.01), 38.7), ((47.59, 55.31), 44.4), ((55.89, 61.81), 52.3), ((62.37, 68.36), 61.4),
         ((68.86, 72.83), 67.7)]
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP13_Break_Continue_Pass_VO.mp4")
WORK = os.path.join(HERE, "work_vo")


def src_of(t_out):
    return float(np.interp(t_out, DST, SRC))


def out_of(t_src):
    return float(np.interp(t_src, SRC, DST))


def frame(i):
    return e.frame(i, src_of(i / e.FPS))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(TOTAL, drop=0.1, power=out_of(e.BRK_STOP))
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
