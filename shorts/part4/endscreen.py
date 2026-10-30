"""Animated end screen: title, LIKE/SHARE/SUBSCRIBE pills, a tapping hand and the channel handle.
Usage: endscreen.py <out_dir> <fonts_dir>   -> writes es_000.png ... (30 fps, DUR seconds)"""
import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT, FONTS = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 3.6
BANG = f"{FONTS}/Bangers-Regular.ttf"
MONT = ImageFont.truetype(f"{FONTS}/Montserrat.ttf", 84); MONT.set_variation_by_name("Black")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
TAP_LIKE, TAP_SUB = 1.55, 2.30          # seconds into the end screen (sync click SFX to these)

def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    return im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
THUMB, BELL, HAND = emoji("\U0001F44D", 96), emoji("\U0001F514", 96), emoji("\U0001F446", 170)

def ease_out_back(x):
    x = min(max(x, 0), 1); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def pill(label, color, icon, dark):
    pw, ph = 780, 176
    im = Image.new("RGBA", (pw + 40, ph + 50))
    sh = Image.new("RGBA", im.size); ImageDraw.Draw(sh).rounded_rectangle((20, 34, 20 + pw, 34 + ph), ph // 2, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 22, 20 + pw, 22 + ph), ph // 2, fill=dark)            # 3D lip
    d.rounded_rectangle((20, 10, 20 + pw, 10 + ph), ph // 2, fill=color)
    gl = Image.new("RGBA", im.size); ImageDraw.Draw(gl).rounded_rectangle((70, 20, pw - 30, 4 + ph // 2), ph // 4, fill=(255, 255, 255, 45))
    im.alpha_composite(gl); d = ImageDraw.Draw(im)                                   # gloss
    tw = d.textlength(label, font=MONT); iw = 100
    x = 20 + (pw - (iw + 26 + tw)) / 2; cy = 10 + ph // 2
    if icon == "arrow":
        d.line((x + 18, cy + 30, x + 78, cy - 30), fill="white", width=14)
        d.line((x + 34, cy - 30, x + 80, cy - 30), fill="white", width=14); d.line((x + 78, cy - 32, x + 78, cy + 14), fill="white", width=14)
    else:
        im.alpha_composite(icon, (int(x), cy - 48))
    d.text((x + iw + 26, cy + 4), label, font=MONT, fill="white", anchor="lm", stroke_width=4, stroke_fill=(0, 0, 0, 120))
    return im

BLUE, BLUE_D = (30, 136, 255), (16, 86, 190)
GREEN, GREEN_D = (40, 190, 80), (22, 128, 52)
RED, RED_D = (240, 58, 50), (170, 30, 26)
GREY, GREY_D = (110, 110, 118), (70, 70, 76)
P_LIKE, P_LIKED = pill("LIKE", BLUE, THUMB, BLUE_D), pill("LIKED", BLUE_D, THUMB, (10, 60, 140))
P_SHARE = pill("SHARE", GREEN, "arrow", GREEN_D)
P_SUB, P_SUBD = pill("SUBSCRIBE", RED, BELL, RED_D), pill("SUBSCRIBED", GREY, BELL, GREY_D)
YS = [720, 950, 1180]                     # pill centres
APPEAR = [0.35, 0.55, 0.75]

def text_line(segs, font, size, y, stroke=10):
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im); f = ImageFont.truetype(font, size)
    sp = d.textlength(" ", font=f); ws = [d.textlength(t, font=f) for t, _ in segs]
    x = (W - sum(ws) - sp * (len(segs) - 1)) / 2
    for (t, c), w in zip(segs, ws):
        d.text((x, y), t, font=f, fill=c, stroke_width=stroke, stroke_fill="black"); x += w + sp
    return im
TITLE = text_line([("BOLT:", "#FF9A1F")], BANG, 90, 110, 8)
TITLE.alpha_composite(text_line([("THE", "#2EE6FF"), ("LAST", "#FFE81F"), ("TRAM", "#FF2E3A")], BANG, 130, 200))
TITLE.alpha_composite(text_line([("AT", "#FFFFFF"), ("11:47", "#FFE81F")], BANG, 84, 335, 8))
TITLE.alpha_composite(text_line([("EXCITED", "#FFFFFF"), ("FOR", "#FFFFFF"), ("PART 5?", "#FF2E3A")], BANG, 92, 460, 9))
HANDLE = text_line([("@BoltsSpookyTales", "#FFE81F")], "/usr/share/fonts/opentype/inter/Inter-Black.otf", 72, 1350, 8)

def press(t, tap):            # quick squash when tapped
    x = (t - tap) / 0.18
    return 1 - 0.08 * math.sin(math.pi * x) if 0 <= x <= 1 else 1

def hand_pos(t):
    """Fingertip target over time: enter -> LIKE -> SUBSCRIBE."""
    path = [(1.0, (1150, 1700)), (1.45, (760, YS[0] + 20)), (TAP_LIKE + 0.25, (760, YS[0] + 20)),
            (2.15, (800, YS[2] + 20)), (DUR, (800, YS[2] + 20))]
    if t <= path[0][0]: return path[0][1]
    for (ta, a), (tb, b) in zip(path, path[1:]):
        if t <= tb:
            u = (t - ta) / (tb - ta); u = u * u * (3 - 2 * u)
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    return path[-1][1]

for i in range(int(DUR * FPS)):
    t = i / FPS
    fr = Image.new("RGBA", (W, H))
    a = min(1, t / 0.35)
    fr.alpha_composite(Image.blend(Image.new("RGBA", (W, H)), TITLE, a))
    for k, (y, t0) in enumerate(zip(YS, APPEAR)):
        sc = ease_out_back((t - t0) / 0.35)
        if sc <= 0.01: continue
        if k == 0: base = P_LIKED if t >= TAP_LIKE + 0.06 else P_LIKE; sc *= press(t, TAP_LIKE)
        elif k == 1: base = P_SHARE
        else: base = P_SUBD if t >= TAP_SUB + 0.06 else P_SUB; sc *= press(t, TAP_SUB)
        pw = max(1, int(base.width * sc)); ph = max(1, int(base.height * sc))
        fr.alpha_composite(base.resize((pw, ph), Image.LANCZOS), (W // 2 - pw // 2, y - ph // 2))
    if t >= 0.95:
        fr.alpha_composite(Image.blend(Image.new("RGBA", (W, H)), HANDLE, min(1, (t - 0.95) / 0.3)))
    if t >= 1.0:
        x, y = hand_pos(t)
        tapping = any(0 <= t - tp <= 0.18 for tp in (TAP_LIKE, TAP_SUB))
        hs = 0.88 if tapping else 1.0
        hd = HAND.resize((int(HAND.width * hs), int(HAND.height * hs)), Image.LANCZOS)
        fr.alpha_composite(hd, (int(x - hd.width * 0.42), int(y - hd.height * 0.04)))
        for tp in (TAP_LIKE, TAP_SUB):           # ripple ring on tap
            u = (t - tp) / 0.35
            if 0 <= u <= 1:
                rg = Image.new("RGBA", (W, H)); r = 20 + 70 * u
                ImageDraw.Draw(rg).ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, int(220 * (1 - u))), width=8)
                fr.alpha_composite(rg)
    fr.save(f"{OUT}/es_{i:03d}.png")
print("frames", int(DUR * FPS))
