#!/usr/bin/env python3
"""JARVIS Part 3 (20 s, 2D neon): 'Jarvis ne mujhe PEHCHAAN liya!' - ESP32-CAM face recognition. Hook with the
JARVIS orb, ESP32-CAM board reveal (camera = aankhein), a camera-feed panel that scans the Boss's face -> green box
'BOSS 98%' + 'Welcome back, Boss!', then a friend's face -> red flashing 'UNKNOWN' + 'Alert! Ye kaun hai?', CTA +
Part 4 tease, then the Like / Share / big SUBSCRIBE page. Usage: python3 edit41/build.py [preview FRAMES OUT]"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


b31 = _load("b31", os.path.join(ROOT, "edit31", "build.py"))
j2d = _load("j2d", os.path.join(ROOT, "edit38", "jarvis2d.py"))
b = b31.b
fx, e5, font, txt, pop_s, ease, head = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head
MONT, BOLD, INK, WHT, YEL, CYAN, GRN = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN
RED, PINK = (255, 60, 70), (255, 90, 200)
W, H, FPS, SR = 1080, 1920, 24, 48000
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-jarvis-part3-face-recognition-SHORT.mp4")
S_CAM, S_BOSS, S_FRIEND, S_CTA = 60, 120, 240, 360
CLIP, OUTRO = 408, 72
TOTAL = CLIP + OUTRO                                   # 480 = 20 s
BOSS_HIT, FRIEND_HIT = S_BOSS + 44, S_FRIEND + 44      # recognition result frames
PX0, PY0, PS = 90, 400, 900                            # camera-feed panel


def t(f):
    return f / FPS


# ------------------------------------------------------------------ ESP32-CAM board
def draw_cam_board(lay, f, cx, cy, s):
    d = ImageDraw.Draw(lay)
    bw, bh = 400 * s, 600 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 22 * s, fill=(28, 30, 36, 255), outline=(80, 86, 100, 255), width=max(2, int(5 * s)))
    for i in range(8):                                                     # header pins both sides
        for sx in (x0 + 14 * s, x0 + bw - 34 * s):
            d.rectangle((sx, y0 + 150 * s + i * 52 * s, sx + 20 * s, y0 + 170 * s + i * 52 * s), fill=(220, 180, 60, 255))
    d.rounded_rectangle((cx - 120 * s, y0 + 330 * s, cx + 120 * s, y0 + 560 * s), 10 * s, fill=(200, 205, 215, 255))
    d.text((cx, y0 + 420 * s), "ESP32", font=font(MONT, max(10, int(46 * s))), fill=(30, 34, 44, 255), anchor="mm")
    d.text((cx, y0 + 475 * s), "WiFi + AI", font=font(BOLD, max(8, int(28 * s))), fill=(70, 74, 90, 255), anchor="mm")
    d.rounded_rectangle((cx - 90 * s, y0 + 60 * s, cx + 90 * s, y0 + 250 * s), 14 * s, fill=(15, 15, 18, 255))   # camera module
    r = 70 * s
    lc = (cx, y0 + 150 * s)
    d.ellipse((lc[0] - r, lc[1] - r, lc[0] + r, lc[1] + r), fill=(8, 8, 12, 255), outline=(110, 115, 130, 255), width=max(2, int(6 * s)))
    g = Image.new("RGBA", lay.size)
    ImageDraw.Draw(g).ellipse((lc[0] - r * 0.6, lc[1] - r * 0.6, lc[0] + r * 0.6, lc[1] + r * 0.6), fill=(40, 120, 255, 200))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(max(1, 10 * s))))
    d = ImageDraw.Draw(lay)
    d.ellipse((lc[0] - r * 0.25, lc[1] - r * 0.45, lc[0] - r * 0.02, lc[1] - r * 0.22), fill=(255, 255, 255, 220))
    led = (f // 6) % 2 == 0
    d.ellipse((x0 + bw - 70 * s, y0 + 280 * s, x0 + bw - 50 * s, y0 + 300 * s), fill=(255, 60, 60, 255) if led else (90, 20, 20, 255))
    return {"lens": lc, "esp": (cx, y0 + 440 * s), "sd": (cx, y0 + bh - 20 * s)}


# ------------------------------------------------------------------ camera feed panel
def cam_panel(lay, f, who, f0, hit):
    u = pop_s(f - f0, 6)
    if u <= 0.05:
        return
    g = Image.new("RGBA", (PS, PS), (10, 18, 30, 255))
    gd = ImageDraw.Draw(g)
    for y in range(0, PS, 6):                                               # scanlines + grid
        gd.line((0, y, PS, y), fill=(20, 34, 52, 255))
    face = e5.emoji("🧔" if who == "boss" else "👱", 560)
    sway = int(14 * math.sin(f * 0.12))
    g.alpha_composite(face, ((PS - 560) // 2 + sway, 170))
    a = f - f0
    res = f >= hit
    col = (GRN if who == "boss" else RED) if res else CYAN
    bx0, by0, bx1, by1 = (PS - 560) // 2 + sway - 20, 150, (PS + 560) // 2 + sway + 20, 760
    if not res:                                                             # scanning: sweeping line + mesh dots
        yy = 170 + ((a * 18) % 560)
        gd.line((bx0, yy, bx1, yy), fill=CYAN + (255,), width=6)
        rng = np.random.default_rng(3)
        for k in range(40):
            px, py = rng.uniform(bx0 + 60, bx1 - 60), rng.uniform(220, 700)
            if py < yy:
                gd.ellipse((px - 5, py - 5, px + 5, py + 5), fill=CYAN + (230,))
    else:
        blink = who != "boss" and (f // 4) % 2 == 0
        if who != "boss":
            tint = Image.new("RGBA", (PS, PS), (255, 0, 30, 70 if blink else 30))
            g.alpha_composite(tint)
    L, wdt = 90, 10
    gd = ImageDraw.Draw(g)
    for (x, y, dx, dy) in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        gd.line((x, y, x + dx * L, y), fill=col + (255,), width=wdt)
        gd.line((x, y, x, y + dy * L), fill=col + (255,), width=wdt)
    if res:
        label = "BOSS  98%" if who == "boss" else "UNKNOWN!"
        tw = gd.textlength(label, font=font(MONT, 56)) + 60
        gd.rounded_rectangle((PS / 2 - tw / 2, by1 + 20, PS / 2 + tw / 2, by1 + 110), 30, fill=col + (255,))
        gd.text((PS / 2, by1 + 65), label, font=font(MONT, 56), fill=INK if who == "boss" else WHT, anchor="mm")
    else:
        gd.text((PS / 2, by1 + 65), "Scanning" + "." * (1 + (a // 6) % 3), font=font(MONT, 52), fill=CYAN + (255,), anchor="mm")
    gd.rounded_rectangle((24, 24, 230, 80), 28, fill=(230, 30, 40, 255))
    gd.ellipse((40, 40, 64, 64), fill=WHT if (f // 6) % 2 == 0 else (255, 160, 160))
    gd.text((145, 52), "LIVE", font=font(MONT, 36), fill=WHT, anchor="mm")
    gd.text((PS - 30, 52), "ESP32-CAM", font=font(MONT, 34), fill=(180, 200, 230), anchor="rm")
    s = PS * u
    g = g.resize((int(s), int(s)), Image.LANCZOS)
    m = Image.new("L", g.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), int(40 * u), fill=255)
    x0, y0 = int(W / 2 - s / 2), int(PY0 + PS / 2 - s / 2)
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 14, x0 + s, y0 + s + 14), 40, fill=(0, 0, 0, 170))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    lay.paste(g, (x0, y0), m)
    ImageDraw.Draw(lay).rounded_rectangle((x0, y0, x0 + s, y0 + s), int(40 * u), outline=col + (255,), width=8)


# ------------------------------------------------------------------ text
LINES = [(S_BOSS + 4, BOSS_HIT + 2, "Jarvis", "Scan kar raha hoon...", (60, 200, 255), "🤖", "🔍"),
         (BOSS_HIT + 2, S_FRIEND, "Jarvis", "Welcome back, Boss!", (60, 200, 255), "🤖", "😎"),
         (S_FRIEND + 4, FRIEND_HIT + 2, "Tum", "Jarvis, ye mera dost hai", (37, 211, 102), "🧑", ""),
         (FRIEND_HIT + 2, S_CTA, "Jarvis", "Alert! Main isko nahi jaanta!", (255, 80, 90), "🤖", "🚨")]


def subtitle(lay, f):
    for (a, z, who, line, col, em, tail) in LINES:
        if not (a <= f < z):
            continue
        u = pop_s(f - a, 5)
        if u <= 0.05:
            return
        d = ImageDraw.Draw(lay)
        fs = 50
        text = f"{who}: {line}"
        while d.textlength(text, font=font(MONT, fs)) > 800 and fs > 34:
            fs -= 2
        fnt = font(MONT, fs)
        tw = d.textlength(text, font=fnt) + 150 + (60 if tail else 0)
        x0, y0 = W / 2 - tw / 2 * u, 1360
        sh = Image.new("RGBA", (W, H))
        ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, W - x0, y0 + 120), 50, fill=(0, 0, 0, 160))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((x0, y0, W - x0, y0 + 110), 50, fill=(10, 14, 22, 240), outline=col + (255,), width=6)
        if u > 0.9:
            lay.alpha_composite(e5.emoji(em, 64), (int(x0 + 28), int(y0 + 23)))
            d.text((x0 + 110, y0 + 55), who + ":", font=fnt, fill=col, anchor="lm")
            wl = d.textlength(who + ": ", font=fnt)
            d.text((x0 + 110 + wl, y0 + 55), line, font=fnt, fill=WHT, anchor="lm")
            if tail:
                lay.alpha_composite(e5.emoji(tail, 54), (int(x0 + 110 + wl + d.textlength(line, font=fnt) + 10), int(y0 + 28)))
        return


def header(lay, f):
    d = ImageDraw.Draw(lay)
    if f < S_CAM:
        head(lay, d, "JARVIS Part 3", 190, 100, CYAN, "👀", 1 + 0.03 * math.sin(f * 0.6))
        head(lay, d, "Ab Jarvis dekh bhi sakta hai!", 300, 64, YEL, "😱", pop_s(f - 6, 5))
    elif f < S_BOSS:
        head(lay, d, "ESP32-CAM = Aankhein", 200, 84, YEL, "📷", pop_s(f - S_CAM, 5))
        d.text((W / 2, 300), "Face Recognition  •  WiFi  •  Rs 500", font=font(BOLD, 42), fill=(200, 210, 230), anchor="mm")
    elif f < S_FRIEND:
        if f < BOSS_HIT:
            head(lay, d, "Test 1: Mera chehra", 210, 86, YEL, "🧔", pop_s(f - S_BOSS, 5))
        else:
            head(lay, d, "Pehchaan liya!", 210, 104, GRN, "✅", pop_s(f - BOSS_HIT, 5))
    elif f < S_CTA:
        if f < FRIEND_HIT:
            head(lay, d, "Test 2: Dost ka chehra", 210, 82, YEL, "👱", pop_s(f - S_FRIEND, 5))
        else:
            head(lay, d, "ANJAAN AADMI!", 210, 104, RED, "🚨", pop_s(f - FRIEND_HIT, 5))
    else:
        head(lay, d, "Comment \"JARVIS\" = Code FREE", 190, 68, YEL, "👇", pop_s(f - S_CTA, 5))
        v = ease((f - S_CTA - 4) / 6)
        if v > 0:
            bw = int(860 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 270, W / 2 + bw / 2, 350), 40, fill=(130, 60, 255, 255))
            if v > 0.9:
                d.text((W / 2, 310), "Part 4: Jarvis darwaza kholega 🔓"[:-2], font=font(MONT, 40), fill=WHT, anchor="mm")


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("👀", 46), (W - 388, 46))


def orb_state(f):
    if S_BOSS + 4 <= f < BOSS_HIT or S_FRIEND + 4 <= f < FRIEND_HIT:
        return "think"
    if BOSS_HIT <= f < BOSS_HIT + 30 or FRIEND_HIT <= f < FRIEND_HIT + 30:
        return "speak"
    if f < S_CAM:
        return "idle"
    return "listen" if S_FRIEND <= f < S_FRIEND + 4 else "idle"


def frame(f):
    im = Image.fromarray(np.clip(j2d.background(0), 0, 255).astype(np.uint8)).convert("RGBA")
    if f >= FRIEND_HIT and f < S_CTA and (f // 4) % 2 == 0:                  # red alarm wash
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 0, 30, 40)))
    lay = Image.new("RGBA", (W, H))
    st = orb_state(f)
    j2d.orb_state = lambda ff, st=st: (st, ff)
    if f < S_CAM:
        j2d.draw_orb(lay, W / 2, 900, 330, f)
    elif f < S_BOSS:
        a = f - S_CAM
        pts = draw_cam_board(lay, f, W / 2, 940, 1.15)
        d = ImageDraw.Draw(lay)
        b.tag(lay, d, pts["lens"], (W / 2 + 300, 520), "OV2640 Camera", "= Aankhein", ease((a - 6) / 10))
        b.tag(lay, d, pts["esp"], (W / 2 - 290, 1400), "ESP32", "= Dimaag", ease((a - 18) / 10))
    elif f < S_FRIEND:
        cam_panel(lay, f, "boss", S_BOSS, BOSS_HIT)
    elif f < S_CTA:
        cam_panel(lay, f, "friend", S_FRIEND, FRIEND_HIT)
    else:
        cam_panel(lay, f, "friend", S_FRIEND, FRIEND_HIT)
    if S_BOSS <= f < S_CTA:
        j2d.draw_orb(lay, 160, 1610, 110, f)
        ImageDraw.Draw(lay).text((160, 1752), "JARVIS", font=font(MONT, 30), fill=CYAN, anchor="mm")
    im.alpha_composite(lay)
    lay = Image.new("RGBA", (W, H))
    sh = Image.new("L", (1, H))
    sh.putdata([int(170 * max(0, 1 - y_ / 380)) for y_ in range(H)])
    top = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    top.putalpha(sh.resize((W, H)))
    im.alpha_composite(top)
    header(lay, f)
    badge(lay, ImageDraw.Draw(lay))
    subtitle(lay, f)
    im.alpha_composite(lay)
    out = np.array(im.convert("RGB"))
    for s_ in (S_CAM, S_BOSS, BOSS_HIT, S_FRIEND, FRIEND_HIT, S_CTA):
        a = f - s_
        if 0 <= a < 5:
            out = b.zoom(out, 1 + 0.05 * (1 - a / 5) ** 2)
    b.rainbow_bar(out, int(W * (f + 1) / TOTAL))
    return out


# ------------------------------------------------------------------ audio
def beep(freq, dur, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * tt) * np.minimum(1, tt / 0.004) * np.minimum(1, (dur - tt) / 0.02) * vol


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), j2d.pad(total + 0.05))
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.7 * SR)], 0.0, 0.5)
    P(buf, fx.riser(0.6), 0.0, 0.25)
    for s_ in (S_CAM, S_BOSS, S_FRIEND, S_CTA):
        P(buf, fx.whoosh(0.3, s_) * 0.6, max(0, t(s_) - 0.15), 0.4)
    for f0, hit in ((S_BOSS, BOSS_HIT), (S_FRIEND, FRIEND_HIT)):
        for k in range(f0 + 6, hit, 4):                                        # scanning ticks
            P(buf, beep(1600 + 30 * ((k - f0) // 4), 0.03, 0.3), t(k), 0.35)
    P(buf, np.concatenate([beep(1319, 0.09, 0.45), beep(1760, 0.22, 0.45)]), t(BOSS_HIT), 0.65)   # match
    P(buf, j2d.bleeps(10, 7), t(BOSS_HIT) + 0.3, 0.35)
    for k in range(6):                                                         # alarm
        P(buf, beep(880 if k % 2 == 0 else 660, 0.18, 0.4), t(FRIEND_HIT) + k * 0.2, 0.45)
    P(buf, j2d.bleeps(10, 9), t(FRIEND_HIT) + 1.3, 0.35)
    P(buf, b.fanfare8()[: int(0.9 * SR)] * 0.5, t(S_CTA), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(CLIP) - 0.2, 0.45)
    for a_ in b31.BTN_POP:
        P(buf, fx.pop(), t(CLIP + a_), 0.35)
    for a_ in b31.BTN_PRESS:
        P(buf, b.ok_beep()[: int(0.09 * SR)] * 0.6, t(CLIP + a_), 0.4)
    P(buf, fx.ding(), t(CLIP + b31.BTN_PRESS[2] + 1), 0.5)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    last = None
    for f in range(TOTAL):
        if f < CLIP:
            fr = frame(f)
            last = fr
        else:
            fr = b31.outro(f - CLIP, last, "Jarvis pasand aaya?", badge=badge, dim=0.55, sub_big=True)
            if f - CLIP < 4:
                k = 1 - (f - CLIP) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k), 1 + 0.05 * k)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f)).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for k_, im_ in enumerate(ims):
            c.paste(im_, (k_ * 360, 0))
        c.save(sys.argv[3])
    else:
        build_audio()
        build_video()
