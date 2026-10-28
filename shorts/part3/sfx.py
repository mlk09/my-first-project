"""Sound effects for Part 3 (48 kHz stereo WAVs). Usage: sfx.py <out_dir>"""
import sys, wave, numpy as np
OUT = sys.argv[1]; SR = 48000
def save(name, x):
    x = np.clip(x, -1, 1); st = np.repeat((x * 32767).astype(np.int16)[:, None], 2, 1)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
t = lambda d: np.arange(int(d * SR)) / SR
# music box: slow, slightly sad melody (A minor), plucked bell tones
notes = [("A5", .45), ("C6", .45), ("E6", .45), ("A5", .45), ("G5", .45), ("E5", .9), ("F5", .45), ("A5", .45), ("C6", .45), ("B5", .45), ("E5", 1.2)]
freq = {"E5": 659.3, "F5": 698.5, "G5": 784.0, "A5": 880.0, "B5": 987.8, "C6": 1046.5, "E6": 1318.5}
mb = np.zeros(int(SR * 7.5)); pos = 0
for n, d in notes:
    tt = t(2.0); f = freq[n]
    tone = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.15 * np.sin(2 * np.pi * 3.01 * f * tt)) * np.exp(-3.2 * tt)
    s0 = int(pos * SR); e = min(len(mb), s0 + len(tone)); mb[s0:e] += tone[: e - s0] * 0.22; pos += d
save("musicbox", mb)
# clock tick-tock
tk = np.zeros(int(SR * 1.6))
for k in range(4):
    tt = t(0.05); s0 = int(k * 0.4 * SR)
    tk[s0:s0 + len(tt)] += 0.5 * np.sin(2 * np.pi * (2400 if k % 2 == 0 else 1900) * tt) * np.exp(-90 * tt)
save("tick", tk)
# power-down: falling hum + clunk
tt = t(1.4); f = 120 * np.exp(-1.8 * tt)
pd = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-1.2 * tt)
pd[:int(0.12 * SR)] += 0.8 * np.sin(2 * np.pi * 70 * t(0.12)) * np.exp(-30 * t(0.12))
save("powerdown", pd)
# mechanical clicking swarm (many robots waking), getting louder
rng = np.random.default_rng(4); dur = 4.0; cl = np.zeros(int(SR * dur))
for k in range(220):
    st = rng.uniform(0, dur - 0.05); tt = t(0.02); s0 = int(st * SR)
    cl[s0:s0 + len(tt)] += (st / dur) ** 1.5 * 0.35 * np.sin(2 * np.pi * rng.uniform(1500, 4000) * tt) * np.exp(-200 * tt)
save("clicks", cl)
# heartbeat, drone, boom, stinger, UI click
hb = np.zeros(int(SR * 4.0))
for k in range(5):
    for off, a in ((0, 0.9), (0.24, 0.65)):
        tt = t(0.25); s0 = int((k * 0.8 + off) * SR); hb[s0:s0 + len(tt)] += a * np.sin(2 * np.pi * 50 * tt) * np.exp(-18 * tt)
save("heart", hb)
tt = t(26.0); save("drone", (0.22 * np.sin(2 * np.pi * 44 * tt) + 0.16 * np.sin(2 * np.pi * 46.5 * tt) + 0.07 * np.sin(2 * np.pi * 131 * tt)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * tt)))
tt = t(2.5); save("boom", 0.9 * np.sin(2 * np.pi * (42 * tt + 40 / 6 * (1 - np.exp(-6 * tt)))) * np.exp(-2.2 * tt))
tt = t(1.8); save("sting", 0.3 * (np.sin(2 * np.pi * 1046 * tt) + np.sin(2 * np.pi * 1109 * tt) + 0.6 * np.sin(2 * np.pi * 523 * tt)) * np.exp(-3 * tt))
tt = t(0.15); save("click", 0.5 * np.sin(2 * np.pi * 1800 * tt) * np.exp(-70 * tt) + 0.3 * np.sin(2 * np.pi * 900 * tt) * np.exp(-40 * tt))
