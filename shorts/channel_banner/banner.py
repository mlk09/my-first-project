"""YouTube channel banner (2560x1440) for @BoltsSpookyTales. Everything that matters sits inside the
1546x423 centre safe area (x 507..2053, y 508..931) that every device shows.
Usage: banner.py <scene_1280x720.png> <out.jpg> <fonts_dir>"""
import sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, OUT, FONTS = sys.argv[1:4]
W, H = 2560, 1440
SX0, SY0, SX1, SY1 = 507, 508, 2053, 931
BANG = f"{FONTS}/Bangers-Regular.ttf"
MONT = f"{FONTS}/Montserrat.ttf"
WHITE, YEL, CYAN, RED, ORA = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF2E3A", "#FF9A1F"

# scene: Bolt + eagle + biker + green tram, shifted down so the eagle and Bolt's head share the desktop strip
scene = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
scene = ImageEnhance.Brightness(scene).enhance(1.2); scene = ImageEnhance.Contrast(scene).enhance(1.15)
scene = ImageEnhance.Color(scene).enhance(1.2).filter(ImageFilter.UnsharpMask(3, 90, 2))
canvas = scene.filter(ImageFilter.GaussianBlur(30)).point(lambda p: int(p * 0.5))
canvas.paste(scene.crop((0, 0, W, H - 210)), (0, 210))
fade = Image.linear_gradient("L").resize((W, 140))
canvas.paste(canvas.crop((0, 0, W, 140)), (0, 210), Image.eval(fade, lambda p: 255 - p))
wx, wy = 2320, 1200 + 210
patch = canvas.crop((wx - 90, wy - 90, wx + 90, wy + 90)).filter(ImageFilter.GaussianBlur(25))
canvas.paste(patch, (wx - 90, wy - 90))
img = canvas.convert("RGBA")

# darken behind the text block (right half of the safe area) so it reads over the tram
grad = np.zeros((H, W), np.float32)
xs = np.clip((np.arange(W) - 1000) / 260, 0, 1)
grad[:] = xs[None, :] * 0.62
ys = np.abs(np.arange(H) - 720) / 520
grad *= np.clip(1.25 - ys, 0, 1)[:, None]
dark = Image.fromarray((grad * 255).astype(np.uint8))
img = Image.composite(Image.new("RGBA", (W, H), (8, 6, 20, 255)), img, dark)

# vignette + rain
yy, xx = np.ogrid[:H, :W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vig = np.clip(1 - 0.7 * np.clip(r - 0.45, 0, 1) ** 1.3, 0, 1)
img = Image.fromarray((np.asarray(img.convert("RGB")).astype(np.float32) * vig[..., None]).astype(np.uint8)).convert("RGBA")
random.seed(5); rain = Image.new("L", (W, H)); d = ImageDraw.Draw(rain)
for _ in range(2600):
    x, y, L = random.uniform(0, W), random.uniform(0, H), random.uniform(40, 130)
    d.line([(x, y), (x + 0.13 * L, y + L)], fill=int(170 * random.uniform(0.35, 1)), width=2)
rain = rain.filter(ImageFilter.GaussianBlur(0.9)).point(lambda p: int(p * 0.45))
img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 236)] * 3, rain)))

def mont(size, style="Black"):
    f = ImageFont.truetype(MONT, size); f.set_variation_by_name(style); return f
def text(segs, font, cx, y, stroke, glow=None, shadow=True):
    d = ImageDraw.Draw(img); sp = d.textlength(" ", font=font); ws = [d.textlength(t, font=font) for t, _ in segs]
    x0 = cx - (sum(ws) + sp * (len(segs) - 1)) / 2
    def layer(fill, dy, extra):
        lay = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(lay); x = x0
        for (t, c), w in zip(segs, ws):
            col = fill or c; ld.text((x, y + dy), t, font=font, fill=col, stroke_width=stroke + extra, stroke_fill=col); x += w + sp
        return lay
    if shadow: img.alpha_composite(layer((0, 0, 0, 210), 14, 0).filter(ImageFilter.GaussianBlur(12)))
    if glow: img.alpha_composite(layer(glow, 0, 12).filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(img); x = x0
    for (t, c), w in zip(segs, ws):
        d.text((x, y), t, font=font, fill=c, stroke_width=stroke, stroke_fill="black"); x += w + sp
    return sum(ws) + sp * (len(segs) - 1)

def fit(fontfile, segs, max_w, start):
    size = start
    while size > 20:
        f = ImageFont.truetype(fontfile, size)
        w = sum(ImageDraw.Draw(img).textlength(t, font=f) for t, _ in segs) + ImageDraw.Draw(img).textlength(" ", font=f) * (len(segs) - 1)
        if w <= max_w: return f
        size -= 2
    return ImageFont.truetype(fontfile, size)

TX = 1600; TW = 2000 - 1180         # text block centre and max width (inside the safe area, right of Bolt)
t1 = [("BOLT'S", ORA), ("SPOOKY", CYAN), ("TALES", RED)]
text(t1, fit(BANG, t1, TW, 150), TX, 545, 9, glow=(255, 120, 20, 120))
t2 = [("THE", CYAN), ("LAST", YEL), ("TRAM", RED), ("AT", WHITE), ("11:47", YEL)]
text(t2, fit(BANG, t2, TW - 120, 100), TX, 700, 7)

text([("Spooky robot stories", WHITE), ("•", ORA), ("Horror Shorts", WHITE)], mont(42, "ExtraBold"), TX, 838, 5, shadow=True)
img.convert("RGB").save(OUT, quality=92, optimize=True)
print("saved", OUT)
