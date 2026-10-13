#!/usr/bin/env python3
"""SH1106 OLED screen frames (own design): 128x64 1-bit pixel art per video frame, upscaled to a
1024x512 texture with visible pixel gaps. Boot logo -> 'HELLO!' -> I2C scan to 0x3C -> packet
fields -> bouncing-ball + bar-graph demo -> channel logo."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import N, SHOTS, BOOT, SCAN, FOUND, PACKET, ADDR, scan_addr, packet_step  # noqa: E402

OUT = os.path.join(HERE, "work", "oled")
os.makedirs(OUT, exist_ok=True)
PIX = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CW, CH, S = 128, 64, 8


def f(sz, big=False):
    return ImageFont.truetype(BIG if big else PIX, sz)


def header(d, title):
    d.rectangle((0, 0, 127, 11), fill=1)
    d.text((64, 6), title, font=f(9), fill=0, anchor="mm")


def screen(fr):
    im = Image.new("1", (CW, CH), 0)
    d = ImageDraw.Draw(im)
    if fr < BOOT:
        return im
    if fr < 30:                                      # boot: logo wipes in
        u = min(1, (fr - BOOT) / 10)
        d.rounded_rectangle((4, 6, 123, 57), 6, outline=1)
        d.text((64, 24), "ESP32", font=f(18, True), fill=1, anchor="mm")
        d.text((64, 44), "I2C  OLED", font=f(10), fill=1, anchor="mm")
        d.rectangle((int(4 + 119 * u), 6, 123, 57), fill=0)
        return im
    if fr < SHOTS[1]:                                # HELLO!
        n = min(6, (fr - 30) // 2 + 1)
        d.text((64, 30), "HELLO!"[:n], font=f(26, True), fill=1, anchor="mm")
        return im
    if fr < SHOTS[3]:                                # idle dashboard while we look at the board / wires
        header(d, "I2C BUS")
        d.text((4, 18), "SDA  GPIO21", font=f(10), fill=1)
        d.text((4, 31), "SCL  GPIO22", font=f(10), fill=1)
        d.text((4, 46), "400 kHz", font=f(10), fill=1)
        k = (fr // 3) % 16
        for i in range(16):
            x = 70 + i * 3
            d.line((x, 60, x, 60 - (6 if (i + k) % 4 < 2 else 1)), fill=1)
        return im
    if fr < SHOTS[4]:                                # address scan
        header(d, "SCANNING BUS")
        a = scan_addr(fr)
        found = fr >= FOUND
        d.text((64, 32), f"0x{a:02X}", font=f(22, True), fill=1, anchor="mm")
        d.rectangle((8, 50, 119, 58), outline=1)
        d.rectangle((8, 50, 8 + int(111 * a / 0x7F), 58), fill=1)
        if found and (fr - FOUND) % 8 < 6:
            d.rectangle((0, 12, 127, 63), fill=1)
            d.text((64, 26), "FOUND!", font=f(16, True), fill=0, anchor="mm")
            d.text((64, 48), f"0x{ADDR:02X}", font=f(16, True), fill=0, anchor="mm")
        return im
    if fr < SHOTS[5]:                                # packet anatomy
        header(d, "I2C PACKET")
        st = packet_step(fr)
        w = 25
        for i, name in enumerate(PACKET):
            x0 = 1 + i * w
            if i == st:
                d.rectangle((x0, 18, x0 + w - 2, 34), fill=1)
            else:
                d.rectangle((x0, 18, x0 + w - 2, 34), outline=1)
            d.text((x0 + w / 2 - 1, 26), {"START": "STRT"}.get(name, name), font=f(7), fill=0 if i == st else 1, anchor="mm")
        info = ["S: SDA falls", f"0x{ADDR:02X} + W", "OLED: ACK", "pixel bytes", "P: SDA rises"]
        if st >= 0:
            d.text((64, 46), info[st], font=f(10), fill=1, anchor="mm")
        d.text((64, 58), f"step {st + 1}/5", font=f(8), fill=1, anchor="mm")
        return im
    if fr < SHOTS[6]:                                # demo: bouncing ball + live bars
        t = fr - SHOTS[5]
        bx = 6 + abs((t * 5) % 220 - 110) * 0.55
        by = 14 + abs((t * 3) % 60 - 30) * 1.2
        d.rectangle((0, 0, 127, 63), outline=1)
        d.ellipse((bx - 4, by - 4, bx + 4, by + 4), fill=1)
        for i in range(10):
            h = 6 + 18 * abs(math.sin(t * 0.3 + i * 0.7))
            d.rectangle((70 + i * 5, 60 - h, 72 + i * 5, 60), fill=1)
        d.text((4, 4), "DEMO", font=f(8), fill=1)
        return im
    header(d, "The IOT Engineer")                     # end
    d.text((64, 34), "I2C", font=f(20, True), fill=1, anchor="mm")
    d.text((64, 54), "SDA + SCL", font=f(10), fill=1, anchor="mm")
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
print("oled frames in", OUT)
