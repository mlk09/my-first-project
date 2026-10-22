#!/usr/bin/env python3
"""EP 12 for loop + range(), VOICE-OVER version.

Same video as build_ep12.py with the ElevenLabs voice-over (assets/voiceoverForloop.mp3) laid in:
  * the 11 voice lines are cut at their pauses and each one is placed on its scene cue
  * the tricky scene is held 1.7 s longer so line 10 finishes before the end screen
  * the music ducks under the voice (sidechain), SFX sit ~3 dB lower, voice is cleaned + levelled
  * final master -14 LUFS

Usage:  python3 edit19/build_ep12_voice.py [--audio-only]
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep12 as b   # noqa: E402

m, fx, bs = b.m, b.fx, b.bs
VOICE = os.path.join(HERE, "assets", "voiceoverForloop.mp3")

# (start, end) of each line inside the mp3 (from silencedetect) -> cue time in the video
LINES = [
    ((0.00, 2.70), 0.20),     # 1 ek se das tak ginti
    ((3.32, 8.21), 3.70),     # 2 menu chai poha vada
    ((8.91, 14.24), 8.65),    # 3 pehle chai... har item
    ((16.12, 20.48), 14.90),  # 4 ab range ... stop
    ((21.67, 24.37), 19.75),  # 5 run karo 1 2 3 4 5
    ((24.80, 27.77), 22.85),  # 6 chhe nahi aaya
    ((30.22, 33.74), 28.90),  # 7 range paanch
    ((34.86, 41.68), 32.60),  # 8 step ... save kar lo
    ((42.81, 48.02), 40.20),  # 9 tricky sawaal
    ((51.03, 55.52), 48.55),  # 10 sahi jawaab A
    ((56.27, 59.81), 53.45),  # 11 like share subscribe
]
EXTRA = 1.7
b.END0 = b.END0 + EXTRA
b.TOTAL = b.END0 + b.es.DUR
OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP12_For_Loop_VO.mp4")
WORK = os.path.join(HERE, "work_vo")


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    music = bs.music(b.TOTAL, drop=0.35, power=b.SIX_T)
    fx.write_wav(os.path.join(WORK, "music.wav"), music)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), b.sfx_track() * 0.8)
    # voice: cut each line, delay it to its cue, clean + level it
    parts, labels = [], []
    for k, ((s, e), cue) in enumerate(LINES):
        parts.append(f"[2:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                     f"afade=t=out:st={max(0.0, e - s - 0.05):.3f}:d=0.05,adelay={int(cue * 1000)}:all=1[v{k}]")
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
                    "-t", f"{b.TOTAL:.3f}", out], check=True)
    return out


m.OUT, m.WORK, m.TOTAL, m.END0 = OUT, WORK, b.TOTAL, b.END0
m.build_audio = build_audio

if __name__ == "__main__":
    if "--audio-only" in sys.argv:
        print(build_audio())
    else:
        m.main()
