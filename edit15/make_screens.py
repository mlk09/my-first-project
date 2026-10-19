#!/usr/bin/env python3
"""SH1106 OLED frames for the Rock-Paper-Scissors robot (own design, 128x64 1-bit): pixel-art hand
icons (rock / paper / scissors), PICK screen while the knob turns, big 3-2-1 countdown, YOU vs BOT
reveal with a result banner and the score, and a CHAMPION screen. Also writes the three 'robot box'
face textures (white card with the emoji + label). Upscaled 8x with pixel gaps."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, CHOICES, EMO, ROUNDS, phase, round_at, knob_choice, winner, score  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
TEX = os.path.join(HERE, "work", "tex")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TEX, exist_ok=True)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else MONO, sz)


def icon(d, c, cx, cy, s=1.0):
    """1-bit hand icons, ~22 px tall at s=1."""
    if c == 0:                                             # rock: fist
        d.rounded_rectangle((cx - 10 * s, cy - 8 * s, cx + 10 * s, cy + 10 * s), radius=6 * s, fill=1)
        for k in range(4):
            x = cx - 9 * s + k * 5 * s
            d.line((x + 4 * s, cy - 8 * s, x + 4 * s, cy - 2 * s), fill=0)
        d.rounded_rectangle((cx - 13 * s, cy - 2 * s, cx - 7 * s, cy + 6 * s), radius=3 * s, fill=1)
    elif c == 1:                                           # paper: open hand
        d.rounded_rectangle((cx - 8 * s, cy - 2 * s, cx + 8 * s, cy + 11 * s), radius=4 * s, fill=1)
        for k in range(4):
            x = cx - 7 * s + k * 4.7 * s
            d.rounded_rectangle((x, cy - 12 * s + abs(k - 1.5) * 2 * s, x + 3 * s, cy), radius=1.5 * s, fill=1)
        d.rounded_rectangle((cx + 7 * s, cy - 2 * s, cx + 14 * s, cy + 3 * s), radius=2 * s, fill=1)
    else:                                                  # scissors: V fingers
        d.rounded_rectangle((cx - 8 * s, cy, cx + 8 * s, cy + 11 * s), radius=5 * s, fill=1)
        d.line((cx - 3 * s, cy + 2 * s, cx - 9 * s, cy - 12 * s), fill=1, width=int(4 * s))
        d.line((cx + 3 * s, cy + 2 * s, cx + 9 * s, cy - 12 * s), fill=1, width=int(4 * s))


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    ph, n = phase(fr)
    i, _ = round_at(fr)
    bot, you = score(fr)
    if ph in ("hook", "idle"):
        d.text((64, 9), "ROCK PAPER SCISSORS", font=f(8, True), fill=1, anchor="mm")
        for k in range(3):
            icon(d, k, 24 + k * 40, 40, 0.9)
        return im
    if ph == "champ":
        d.rectangle((0, 0, 127, 15), fill=1)
        d.text((64, 8), "YOU WIN THE GAME!", font=f(9, True), fill=0, anchor="mm")
        d.text((64, 36), f"{bot} : {you}", font=f(22, True), fill=1, anchor="mm")
        d.text((64, 57), "CHAMPION", font=f(10, True), fill=1, anchor="mm")
        return im
    d.text((2, 1), f"R{i + 1}", font=f(9, True), fill=1)
    d.text((126, 1), f"BOT {bot}:{you} YOU", font=f(8), fill=1, anchor="ra")
    if ph == "select":
        d.text((32, 36), "PICK", font=f(11, True), fill=1, anchor="mm")
        icon(d, knob_choice(fr), 86, 38, 1.1)
        d.text((86, 60), CHOICES[knob_choice(fr)], font=f(7), fill=1, anchor="mm")
        return im
    _, p, b = ROUNDS[i]
    if ph == "count":
        d.text((64, 38), str(n), font=f(34, True), fill=1, anchor="mm")
        return im
    icon(d, p, 26, 32, 1.0)                                # result
    icon(d, b, 102, 32, 1.0)
    d.text((64, 30), "VS", font=f(10, True), fill=1, anchor="mm")
    w = winner(i)
    msg = {"YOU": "YOU WIN!", "BOT": "BOT WINS!", "TIE": "TIE!"}[w]
    d.rectangle((0, 50, 127, 63), fill=1)
    d.text((64, 57), msg, font=f(10, True), fill=0, anchor="mm")
    return im


for fr in range(N):
    im = screen(fr)
    big = Image.new("RGB", (CW * S, CH * S), (2, 3, 6))
    px = im.load()
    d = ImageDraw.Draw(big)
    for yy in range(CH):
        for xx in range(CW):
            if px[xx, yy]:
                d.rectangle((xx * S, yy * S, xx * S + S - 2, yy * S + S - 2), fill=(185, 235, 255))
    big.save(os.path.join(OUT, f"{fr:04d}.png"))

# robot box faces: 512x640 white cards with emoji + label
for c in CHOICES:
    card = Image.new("RGB", (512, 640), (246, 246, 242))
    d = ImageDraw.Draw(card)
    d.rectangle((14, 14, 497, 625), outline=(30, 30, 35), width=6)
    em = Image.new("RGBA", (150, 150))
    ImageDraw.Draw(em).text((8, 8), EMO[c], font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    em = em.crop(em.getbbox()).resize((330, 330), Image.LANCZOS)
    card.paste(em, (91, 90), em)
    d.text((256, 540), c, font=ImageFont.truetype(MONT, 64 if c != "SCISSORS" else 54), fill=(20, 20, 25), anchor="mm")
    card.save(os.path.join(TEX, f"face_{c.lower()}.png"))
print("oled frames in", OUT, "| faces in", TEX)
