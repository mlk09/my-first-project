"""Book promo card (5 s, 30 fps PNG frames, 1080x1920): the user's end-card image kept inside the Shorts
safe area (clear of the right-hand like/comment buttons and the bottom title), slow zoom-in, and
three caption steps across the top. Usage: bookcard.py <endcard_image> <out_dir> <fonts_dir>"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, OUT, FONTS = sys.argv[1:4]
W, H, FPS, DUR = 1080, 1920, 30, 5.0
CARD_H, CX, CY = 1220, 450, 950          # card box: x 107..793, y 340..1560 (right buttons start ~x 900)
card0 = Image.open(SRC).convert("RGB")
bg = card0.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(45))
bg = ImageEnhance.Brightness(bg).enhance(0.6).convert("RGBA")
card = card0.resize((int(card0.width * CARD_H / card0.height), CARD_H), Image.LANCZOS)
mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 34, fill=255)
framed = Image.new("RGBA", (card.width + 16, card.height + 16), (0, 0, 0, 0))
ImageDraw.Draw(framed).rounded_rectangle((0, 0, framed.width - 1, framed.height - 1), 42, fill="white")
framed.paste(card, (8, 8), mask)
shadow = Image.new("RGBA", (framed.width + 80, framed.height + 80), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle((40, 52, 40 + framed.width, 52 + framed.height), 42, fill=(0, 0, 0, 150))
shadow = shadow.filter(ImageFilter.GaussianBlur(18))

MONT = f"{FONTS}/Montserrat.ttf"
def font(size):
    f = ImageFont.truetype(MONT, size); f.set_variation_by_name("Black"); return f
YEL, WHITE, ORA, PURP, PINK = "#FFD21F", "#FFFFFF", "#FF7A1A", "#B98CFF", "#FF5FA2"
STEPS = [   # (start, [lines as (text, colour) segments])
    (0.15, [[("Ye book ", WHITE), ("Amazon", YEL), (" par", WHITE)], [("search karein:", WHITE)]]),
    (1.75, [[("AI for Kids", ORA)], [("with Zuri & Sixby", PURP)]]),
    (3.35, [[("Ages 6-12", PINK), (" • ", WHITE), ("Kindle eBook", YEL)], [("Link channel bio mein hai!", WHITE)]]),
]
def caption(lines, scale):
    lay = Image.new("RGBA", (W, 300)); d = ImageDraw.Draw(lay)
    sizes = [56, 56]; y = 20
    for li, segs in enumerate(lines):
        f = font(int(sizes[li] * scale))
        tw = sum(d.textlength(t, font=f) for t, _ in segs); x = (W - tw) / 2
        for t, c in segs:
            d.text((x, y), t, font=f, fill=c, stroke_width=max(2, int(8 * scale)), stroke_fill="#1B1340"); x += d.textlength(t, font=f)
        y += int(sizes[li] * 1.22 * scale) + 6
    return lay
def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)

n = int(DUR * FPS)
for i in range(n):
    t = i / FPS
    fr = bg.copy()
    z = 1.0 + 0.06 * ease(t / DUR) + 0.04 * (1 - ease(t / 0.35))      # gentle pop-in, then slow zoom-in
    fw, fh = int(framed.width * z * 0.96), int(framed.height * z * 0.96)
    sh = shadow.resize((int(shadow.width * z * 0.96), int(shadow.height * z * 0.96)))
    fr.alpha_composite(sh, (CX - sh.width // 2, CY - sh.height // 2 + 6))
    fr.alpha_composite(framed.resize((fw, fh), Image.LANCZOS), (CX - fw // 2, CY - fh // 2))
    k = max(j for j, (st, _) in enumerate(STEPS) if t >= st) if t >= STEPS[0][0] else None
    if k is not None:
        st, lines = STEPS[k]
        pop = 0.85 + 0.15 * ease((t - st) / 0.18)
        cap = caption(lines, pop)
        a = ease((t - st) / 0.15)
        if a < 1:
            cap.putalpha(cap.getchannel("A").point(lambda p: int(p * a)))
        fr.alpha_composite(cap, (0, 128))
    fr.convert("RGB").save(f"{OUT}/bk_{i:03d}.png")
print("frames", n)
