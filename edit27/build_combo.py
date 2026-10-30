#!/usr/bin/env python3
"""'ESP32 Gaming Console: 4 Retro Games on One OLED' combo short, cut from the finished game shorts
(edit22 Flappy Bird, edit23 Chrome Dino, edit24 Snake, edit26 Pong; no new 3D render):
  intro (3 s)  : 'ESP32 GAMING CONSOLE' + the four GAME CAM panels pop into a 2x2 grid, a selector
                 hops across them
  4 x game (4 s): the best gameplay window of each short, its own top caption replaced by a
                 'GAME n/4' band with the game name + 4 progress dots
  vote (3 s)   : the grid again, numbered 1-4, 'Kaunsa game BEST? Comment 1, 2, 3 ya 4!'
  outro (2.5 s): the Like / Share / Subscribe card of the Pong short
Audio: one 140 BPM chiptune bed (edit22 music) + each game's own SFX for its window, whooshes / dings
on the cuts, loudness-normalised to -14 LUFS. 1080x1920, 24 fps, native HD sources, CRF 15.
Usage: python3 edit27/build_combo.py"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-gaming-console-4-games-SHORT.mp4")
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

W, H, FPS, SR = 1080, 1920, 24, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
RAINBOW = [(255, 40, 40), (255, 120, 20), (255, 210, 20), (80, 240, 60), (30, 230, 190), (40, 120, 255),
           (130, 60, 255), (255, 60, 170)]
# (edit dir, video file, first frame, emoji, name, colour)
GAMES = [("edit22", "esp32-oled-flappy-bird-game-SHORT.mp4", 248, "🐦", "FLAPPY BIRD", (255, 205, 40)),
         ("edit23", "esp32-oled-chrome-dino-game-SHORT.mp4", 252, "🦖", "CHROME DINO", (90, 220, 90)),
         ("edit24", "esp32-oled-snake-game-SHORT.mp4", 234, "🐍", "SNAKE", (80, 150, 255)),
         ("edit26", "esp32-oled-pong-2-player-game-SHORT.mp4", 284, "🏓", "2P PONG", (255, 70, 180))]
SEG = 96
INTRO, VOTE, OUTRO = 72, 72, 60
T_GAME = [INTRO + i * SEG for i in range(4)]
T_VOTE = INTRO + 4 * SEG
T_OUTRO = T_VOTE + VOTE
TOTAL = T_OUTRO + OUTRO
PANEL = (20, 296, 1060, 846)                     # GAME CAM card (incl. border) in the source shorts


def font(s):
    return ImageFont.truetype(MONT, max(8, int(s)))


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def pop_s(age, dur=8):
    if age < 0:
        return 0
    u = min(1, age / dur)
    return ease(u) * (1 + 0.25 * math.sin(math.pi * min(1, age / (dur * 0.8))))


def txt(d, xy, s, size, fill, stroke=None, anchor="mm"):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor,
           stroke_width=stroke if stroke is not None else max(4, int(size) // 10), stroke_fill=(0, 0, 0))


def read_frames(path, start, n):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    out = []
    for _ in range(n):
        ok, fr = cap.read()
        if not ok:
            fr = out[-1] if out else np.zeros((H, W, 3), np.uint8)
        else:
            fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        out.append(fr)
    cap.release()
    return out


def zoom(fr, z, dx=0.0):
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
    M[0, 2] += dx
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


def rainbow_bar(fr, p):
    fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
    n = len(RAINBOW)
    for j in range(n):
        fr[0:10, j * W // n: min(p, (j + 1) * W // n)] = RAINBOW[j]


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🎮", 46), (W - 388, 46))


# ------------------------------------------------------------------ media
SRC = {}
TILES = []


def load():
    for i, (ed, vid, f0, *_rest) in enumerate(GAMES):
        SRC[i] = read_frames(os.path.join(ROOT, ed, "output", vid), f0, SEG)
        x0, y0, x1, y1 = PANEL
        TILES.append([Image.fromarray(fr[y0:y1, x0:x1]) for fr in SRC[i][::2]])   # animated grid tiles
    bgf = cv2.cvtColor(cv2.imread(os.path.join(ROOT, "edit26", "work", "frames3d", "0300.png")), cv2.COLOR_BGR2RGB)
    bgf = cv2.resize(bgf, (W, H))
    bg = cv2.GaussianBlur(bgf, (0, 0), 22).astype(np.float32) * 0.45
    SRC["bg"] = bg.astype(np.uint8)
    SRC["outro"] = read_frames(os.path.join(ROOT, "edit26", "output", GAMES[3][1]), 468, OUTRO)


def grid_frame(a, vote=False):
    """2x2 grid of live game tiles over the blurred console; a = local frame."""
    im = Image.fromarray(SRC["bg"]).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    tw, th = 500, 265
    pos = [(30, 560), (550, 560), (30, 1000), (550, 1000)]
    sel = (a // 9) % 4 if not vote else -1
    for i, (x, y) in enumerate(pos):
        s = pop_s(a - 4 - i * 4, 7)
        if s <= 0.02:
            continue
        tile = TILES[i][(a // 1) % len(TILES[i])].resize((int(tw * s), int(th * s)), Image.LANCZOS).convert("RGBA")
        m = Image.new("L", tile.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, tile.width - 1, tile.height - 1), int(24 * s), fill=255)
        cx, cy = x + tw / 2, y + th / 2
        px, py = int(cx - tile.width / 2), int(cy - tile.height / 2)
        lay.paste(tile, (px, py), m)
        col = GAMES[i][5]
        hot = (i == sel) or vote
        d.rounded_rectangle((px - 6, py - 6, px + tile.width + 6, py + tile.height + 6), int(28 * s),
                            outline=(YEL if i == sel else col) + (255,), width=10 if i == sel else 6)
        if s > 0.9:
            ny = py + tile.height + 52
            d.rounded_rectangle((cx - 210, ny - 34, cx + 210, ny + 34), 34, fill=col + (255,), outline=WHT, width=3)
            d.text((cx + 22, ny), GAMES[i][4], font=font(38), fill=INK, anchor="mm")
            lay.alpha_composite(e5.emoji(GAMES[i][3], 48), (int(cx - 195), int(ny - 24)))
            if vote:
                vs = pop_s(a - 10 - i * 5, 6)
                if vs > 0:
                    r = 62 * vs
                    nx, ny_ = px + 66, py + 66                               # number badge inside the tile corner
                    d.ellipse((nx - r, ny_ - r, nx + r, ny_ + r), fill=YEL + (255,), outline=INK, width=6)
                    if vs > 0.9:
                        d.text((nx, ny_), str(i + 1), font=font(80), fill=INK, anchor="mm")
        if hot and not vote and s > 0.9:
            d.polygon([(cx - 26, py - 40), (cx + 26, py - 40), (cx, py - 12)], fill=YEL + (255,))
    badge(lay, d)
    if not vote:
        s = pop_s(a, 6)
        txt(d, (W / 2, 230), "ESP32 GAMING", 104 * s, YEL, stroke=11)
        txt(d, (W / 2 - 40, 350), "CONSOLE", 104 * s, WHT, stroke=11)
        if s > 0.9:
            tw_ = d.textlength("CONSOLE", font=font(104))
            lay.alpha_composite(e5.emoji("🎮", 96), (int(W / 2 - 40 + tw_ / 2 + 12), 300))
        v = pop_s(a - 20, 6)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330 * v, 430, W / 2 + 330 * v, 510), 40, fill=(255, 120, 220, 255))
            if v > 0.9:
                d.text((W / 2, 470), "4 Retro Games on 1 OLED!", font=font(44), fill=INK, anchor="mm")
        w_ = ease((a - 30) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1520), "1 ESP32 + 1 Knob = 4 Games", 58, CYAN, stroke=6)
    else:
        s = pop_s(a, 6)
        txt(d, (W / 2, 230), "Kaunsa game", 96 * s, WHT, stroke=10)
        txt(d, (W / 2 - 40, 350), "BEST hai?", 112 * s, YEL, stroke=12)
        if s > 0.9:
            tw_ = d.textlength("BEST hai?", font=font(112))
            lay.alpha_composite(e5.emoji("🤔", 96), (int(W / 2 - 40 + tw_ / 2 + 12), 298))
        v = ease((a - 26) / 8)
        if v > 0:
            bw = int(960 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1530, W / 2 + bw / 2, 1680), 75, fill=YEL + (255,))
            if v > 0.9:
                d.text((W / 2, 1605), "Comment 1, 2, 3 ya 4! 👇".replace(" 👇", ""), font=font(56), fill=INK, anchor="mm")
                lay.alpha_composite(e5.emoji("👇", 64), (int(W / 2 + 330), 1572))
        if ease((a - 36) / 8) > 0:
            txt(d, (W / 2, 1770), "Code chahiye? Comment \"GAME\"", 50, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def game_frame(i, a):
    """Segment i, local frame a: the source frame with a GAME n/4 band over its own top caption."""
    fr = SRC[i][a].copy()
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    g = Image.new("L", (1, H))
    g.putdata([255 if y < 270 else max(0, int(255 * (1 - (y - 270) / 26))) for y in range(H)])
    band = Image.new("RGBA", (W, H), (10, 12, 22, 255))
    band.putalpha(g.resize((W, H)))
    lay.alpha_composite(band)
    badge(lay, d)
    col = GAMES[i][5]
    s = pop_s(a, 6)
    d.rounded_rectangle((40, 40, 300, 104), 32, fill=col + (255,), outline=WHT, width=3)
    d.text((170, 72), f"GAME {i + 1}/4", font=font(36), fill=INK, anchor="mm")
    txt(d, (W / 2 - 40, 192), GAMES[i][4], 118 * s, col, stroke=12)
    if s > 0.9:
        tw_ = d.textlength(GAMES[i][4], font=font(118))
        lay.alpha_composite(e5.emoji(GAMES[i][3], 104), (int(W / 2 - 40 + tw_ / 2 + 12), 136))
    for k in range(4):                                             # progress dots
        cx = W / 2 - 75 + k * 50
        r = 13 if k == i else 9
        d.ellipse((cx - r, 262 - r, cx + r, 262 + r), fill=(GAMES[k][5] if k <= i else (90, 95, 110)) + (255,))
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


# ------------------------------------------------------------------ audio
def place(buf, x, t, g=1.0):
    fx.place(buf, x, t, g)


def wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    spec = importlib.util.spec_from_file_location("b22", os.path.join(ROOT, "edit22", "build_short.py"))
    b22 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b22)
    mus = b22.music(total + 0.1)
    sfx = np.zeros(int((total + 0.1) * SR))
    for i, (ed, _v, f0, *_r) in enumerate(GAMES):                     # each game's own SFX
        x = wav(os.path.join(ROOT, ed, "work", "sfx.wav"))
        seg = x[int(f0 / FPS * SR): int((f0 + SEG) / FPS * SR)].copy()
        fade = int(0.05 * SR)
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        place(sfx, seg, T_GAME[i] / FPS, 1.0)
    for t0 in T_GAME + [T_VOTE, T_OUTRO]:
        place(sfx, fx.whoosh(0.3, t0) * 0.6, max(0, t0 / FPS - 0.18), 0.5)
    place(sfx, fx.riser(0.4), 0.0, 0.3)
    for k in range(4):                                               # tiles pop in
        place(sfx, fx.pop(), (4 + k * 4) / FPS, 0.4)
        place(sfx, fx.pop(), (T_VOTE + 10 + k * 5) / FPS, 0.35)
    for a in range(18, INTRO - 4, 9):                                # selector hops
        place(sfx, b22.sq(1200, 0.04, 0.25, 0.3), a / FPS, 0.5)
    place(sfx, fx.ding(), (T_VOTE + 26) / FPS, 0.4)
    x = wav(os.path.join(ROOT, "edit26", "work", "sfx.wav"))                 # outro buttons
    place(sfx, x[int(468 / FPS * SR): int(528 / FPS * SR)], T_OUTRO / FPS, 1.0)
    fx.write_wav(os.path.join(WORK, "music.wav"), mus)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx)
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,apad=whole_dur={total:.3f}[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
                    "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")], check=True)


# ------------------------------------------------------------------ video
def build_video():
    load()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-maxrate", "18M", "-bufsize", "36M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(TOTAL):
        if f < INTRO:
            fr = grid_frame(f)
        elif f < T_VOTE:
            i = (f - INTRO) // SEG
            fr = game_frame(i, (f - INTRO) % SEG)
        elif f < T_OUTRO:
            fr = grid_frame(f - T_VOTE, vote=True)
        else:
            im = Image.fromarray(SRC["outro"][f - T_OUTRO]).convert("RGBA")   # channel badge -> console emoji
            lay = Image.new("RGBA", (W, H))
            badge(lay, ImageDraw.Draw(lay))
            im.alpha_composite(lay)
            fr = np.array(im.convert("RGB"))
        for c in T_GAME + [T_VOTE, T_OUTRO]:                          # whip-zoom blur cut
            dd = f - c
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        rainbow_bar(fr, int(W * (f + 1) / TOTAL))
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 48 == 0:
            print(f"  frame {f}/{TOTAL}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    build_audio()
    build_video()
