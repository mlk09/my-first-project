"""YouTube channel banner (2560x1440) for @BoltsSpookyTales. Everything that matters sits inside the
1546x423 centre safe area (x 507..2053, y 508..931) that every device shows.
Usage: banner.py <bolt_frame_1280x720.png> <out.jpg> <fonts_dir> <street_1280x720.png> <eagle_720x1280.png> <recolor_dir>"""
import sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, OUT, FONTS, STREET, EAGLE, RECOLOR_DIR = sys.argv[1:7]
W, H = 2560, 1440
SX0, SY0, SX1, SY1 = 507, 508, 2053, 931
BANG = f"{FONTS}/Bangers-Regular.ttf"
MONT = f"{FONTS}/Montserrat.ttf"
WHITE, YEL, CYAN, RED, ORA = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF2E3A", "#FF9A1F"

# scene: street, lamps and green tram as a soft backdrop; Bolt and the eagle are cut out and placed
# inside the 423 px strip so phones (centre only) and laptops (full-width strip) both see them whole
from rembg import new_session, remove
src = Image.open(SRC).convert("RGB")                                   # recoloured 1280x720 frame
def pop(im):
    im = ImageEnhance.Brightness(im).enhance(1.2); im = ImageEnhance.Contrast(im).enhance(1.15)
    return ImageEnhance.Color(im).enhance(1.25).filter(ImageFilter.UnsharpMask(3, 90, 2))
# backdrop: robot-free street with the tram, recoloured to the series look (golden light, green tram)
sys.path.insert(0, RECOLOR_DIR)
from recolor import recolor
street = Image.fromarray(recolor(np.asarray(Image.open(STREET).convert("RGB")), 420, 470))
street = pop(street).resize((2720, 1530), Image.LANCZOS).crop((223, 0, 223 + W, H))   # whole tram, just left of the text
wx, wy = 2240, 1273                                                   # hide the Gemini sparkle
street.paste(street.crop((wx - 80, wy - 80, wx + 80, wy + 80)).filter(ImageFilter.GaussianBlur(30)), (wx - 80, wy - 80))
canvas = ImageEnhance.Brightness(street.filter(ImageFilter.GaussianBlur(4))).enhance(0.72)
img = canvas.convert("RGBA")
sess = new_session("isnet-general-use")
def cutout(box, scale_to_h):
    c = pop(src.crop(box)); m = remove(c, session=sess, only_mask=True)
    c = c.convert("RGBA"); c.putalpha(m); c = c.crop(c.getbbox())
    return c.resize((int(c.width * scale_to_h / c.height), scale_to_h), Image.LANCZOS)
bolt = cutout((372, 245, 532, 602), 400)
ea = Image.open(EAGLE).convert("RGB").crop((40, 160, 540, 465))
em = remove(ea, session=sess, only_mask=True); ea = pop(ea).convert("RGBA"); ea.putalpha(em); ea = ea.crop(ea.getbbox())
eagle = ea.resize((330, int(ea.height * 330 / ea.width)), Image.LANCZOS)
def place(im, x, y):
    sh = Image.new("RGBA", (W, H)); a = im.getchannel("A").point(lambda p: int(p * 0.6))
    sh.paste(Image.new("RGBA", im.size, (0, 0, 0, 255)), (x + 10, y + 14), a)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    glow = Image.new("RGBA", (W, H)); glow.paste(Image.new("RGBA", im.size, (255, 170, 60, 255)), (x, y), im.getchannel("A"))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22)).point(lambda p: p) if False else Image.blend(Image.new("RGBA", (W, H)), glow.filter(ImageFilter.GaussianBlur(22)), 0.35))
    img.alpha_composite(im, (x, y))
place(bolt, 990 - bolt.width // 2, 925 - bolt.height)                  # feet just above the strip's bottom edge
place(eagle, 560, 525)

# darken behind the text block (right half of the safe area) so it reads over the tram
grad = np.zeros((H, W), np.float32)
xs = np.clip((np.arange(W) - 1050) / 220, 0, 1)
grad[:] = xs[None, :] * 0.5
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

TX = 1610; TW = 2020 - 1200         # text block centre and max width (inside the safe area, right of Bolt)
t1 = [("BOLT'S", ORA), ("SPOOKY", CYAN), ("TALES", RED)]
text(t1, fit(BANG, t1, TW, 150), TX, 545, 9, glow=(255, 120, 20, 120))
t2 = [("THE", CYAN), ("LAST", YEL), ("TRAM", RED), ("AT", WHITE), ("11:47", YEL)]
text(t2, fit(BANG, t2, TW - 120, 100), TX, 700, 7)

text([("Spooky robot stories", WHITE), ("•", ORA), ("Horror Shorts", WHITE)], mont(42, "ExtraBold"), TX, 838, 5, shadow=True)
img.convert("RGB").save(OUT, quality=92, optimize=True)
print("saved", OUT)
