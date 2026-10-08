#!/usr/bin/env python3
"""1080x1920 cover / thumbnail for Python Basics EP 01 (same look as the short)."""
import os

from PIL import Image

import build_short as b

OUT = os.path.join(b.HERE, "thumbnail", "thumbnail.jpg")


def main():
    fr = b.background(3.0, b.PURPLE)
    st = Image.new("RGBA", (b.W, b.H))
    b.rays(st, 540, 1000, 0.3, b.PY_YEL, n=20, alpha=60)
    fr.alpha_composite(st)
    for k, (c, x) in enumerate(zip(b.hook_cards(), (195, 540, 885))):
        b.paste(fr, c, x, 640, 0.8, 1, (-8, 0, 8)[k])
    b.paste(fr, b.text_img("PYTHON", b.BLACK, 210, b.PY_YEL, 12, b.PY_BLUE, glow=b.PY_YEL), 540, 1000)
    b.paste(fr, b.text_img("KYA HAI?", b.BLACK, 170, b.WHITE, 10, (0, 0, 0), glow=b.ORANGE), 540, 1200, 1, 1, -3)
    tag = b.rrect(560, 96, 48, b.YEL).copy()
    b.paste(tag, b.text_img("SIRF 30 SECOND", b.CAP, 50, (15, 15, 15)), tag.width / 2, tag.height / 2 + 3)
    b.paste(fr, tag, 540, 1390)
    pill = b.rrect(440, 70, 35, (0, 0, 0, 160), (255, 255, 255, 70), 2).copy()
    b.paste(pill, b.text_img("PYTHON BASICS • EP 01", b.CAP, 32, b.YEL), pill.width / 2, pill.height / 2 + 2)
    b.paste(fr, pill, 540, 300)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fr.convert("RGB").save(OUT, quality=92)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
