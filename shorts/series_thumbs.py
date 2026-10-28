"""Series thumbnails for "BOLT: The Last Tram at 11:47" (Part 1 and Part 2), vertical 1080x1920 + wide 1280x720.
Usage: series_thumbs.py <part1_frame_1280x720.png> <part2_clip.mp4> <out_dir> <fonts_dir>"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from rembg import new_session, remove
P1, P2, OUT, FONTS = sys.argv[1:5]
BANG = f"{FONTS}/Bangers-Regular.ttf"
WHITE, YEL, CYAN, RED, ORA = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF2E3A", "#FF9A1F"
RG = (255, 30, 40, 160)

def grade(im, b=1.05, c=1.25, s=1.15):
    im = ImageEnhance.Brightness(im).enhance(b); im = ImageEnhance.Contrast(im).enhance(c)
    return ImageEnhance.Color(im).enhance(s).filter(ImageFilter.UnsharpMask(3, 110, 2))

def vignette(im, strength=0.75):
    w, h = im.size; y, x = np.ogrid[:h, :w]
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    m = np.clip(1 - strength * np.clip(r - 0.35, 0, 1) ** 1.4, 0, 1)
    return Image.fromarray((np.asarray(im.convert("RGB")).astype(np.float32) * m[..., None]).astype(np.uint8)).convert("RGBA")

def text(canvas, segs, size, cx, y, stroke=10, glow=None):
    d = ImageDraw.Draw(canvas); f = ImageFont.truetype(BANG, size)
    sp = d.textlength(" ", font=f); ws = [d.textlength(t, font=f) for t, _ in segs]
    x0 = cx - (sum(ws) + sp * (len(segs) - 1)) / 2
    def layer(fill_fn, dy, extra):
        lay = Image.new("RGBA", canvas.size); ld = ImageDraw.Draw(lay); x = x0
        for (t, c), w in zip(segs, ws):
            col = fill_fn(c); ld.text((x, y + dy), t, font=f, fill=col, stroke_width=stroke + extra, stroke_fill=col); x += w + sp
        return lay
    canvas.alpha_composite(layer(lambda c: (0, 0, 0, 200), 12, 0).filter(ImageFilter.GaussianBlur(10)))
    if glow: canvas.alpha_composite(layer(lambda c: glow, 0, 10).filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(canvas); x = x0
    for (t, c), w in zip(segs, ws):
        d.text((x, y), t, font=f, fill=c, stroke_width=stroke, stroke_fill="black"); x += w + sp

def badge(canvas, label, cx, y, size):
    d = ImageDraw.Draw(canvas); f = ImageFont.truetype(BANG, size); tw = d.textlength(label, font=f)
    d.rounded_rectangle((cx - tw / 2 - 28, y, cx + tw / 2 + 28, y + size * 1.2), 16, fill="#E3101B", outline="white", width=4)
    d.text((cx, y + size * 0.62), label, font=f, fill="white", anchor="mm", stroke_width=3, stroke_fill="black")

def series_title(canvas, cx, y, s, part):
    """BOLT: / THE LAST TRAM / AT 11:47 / [PART n]  — returns the y below the block."""
    text(canvas, [("BOLT:", ORA)], int(118 * s), cx, y, max(6, int(10 * s)), glow=(255, 140, 20, 140))
    y += int(128 * s)
    text(canvas, [("THE", CYAN), ("LAST", YEL), ("TRAM", RED)], int(140 * s), cx, y, max(6, int(10 * s)))
    text(canvas, [("AT", WHITE), ("11:47", YEL)], int(108 * s), cx, y + int(150 * s), max(6, int(9 * s)), glow=(255, 200, 40, 120))
    badge(canvas, f"PART {part}", cx, y + int(272 * s), int(70 * s))
    return y + int(272 * s + 84 * s)

def rain(canvas, alpha=0.5):
    import random; random.seed(3); w, h = canvas.size
    lay = Image.new("L", (w, h)); d = ImageDraw.Draw(lay)
    for _ in range(int(w * h / 4000)):
        x, y0, L = random.uniform(0, w), random.uniform(0, h), random.uniform(40, 120)
        d.line([(x, y0), (x + 0.13 * L, y0 + L)], fill=int(200 * random.uniform(0.4, 1)), width=2)
    lay = lay.filter(ImageFilter.GaussianBlur(0.8)).point(lambda p: int(p * alpha))
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), 235)] * 3, lay)))

# ---------------- Part 1: robot, eagle, biker, green tram ----------------
src1 = Image.open(P1).convert("RGB")                      # recoloured 1280x720 frame
v = vignette(grade(src1.crop((300, 0, 705, 720)).resize((1080, 1920), Image.LANCZOS), 1.25, 1.15, 1.25), 0.6)
rain(v, 0.45)
series_title(v, 540, 290, 0.86, 1)
text(v, [("HE", WHITE), ("WAITED", WHITE)], 118, 540, 1390, glow=RG)
text(v, [("40", ORA), ("YEARS...", RED)], 130, 540, 1505, glow=RG)
v.convert("RGB").save(f"{OUT}/part1_thumbnail_shorts_1080x1920.png")

h = vignette(grade(src1.crop((10, 0, 900, 500)).resize((1280, 720), Image.LANCZOS), 1.25, 1.15, 1.25), 0.5)
rain(h, 0.4)
series_title(h, 640, 8, 0.55, 1)
text(h, [("HE", WHITE), ("WAITED", WHITE), ("40", ORA), ("YEARS...", RED)], 76, 640, 615, 8, glow=RG)
h.convert("RGB").save(f"{OUT}/part1_thumbnail_1280x720.png")

# ---------------- Part 2: red-eyed robot + eagle at the controls ----------------
def frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", P2, "-frames:v", "1", "-vf", "delogo=x=570:y=1130:w=60:h=60",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (720, 1280), raw)
face = grade(frame(9.2), 1.0, 1.3, 1.2)
eagle_src = frame(22.5)
crop = eagle_src.crop((180, 420, 640, 920))
eagle = grade(crop, 1.1, 1.15, 1.1).convert("RGBA")
eagle.putalpha(remove(crop, session=new_session("isnet-general-use"), only_mask=True))
eagle = eagle.crop(eagle.getbbox())

v = vignette(face.resize((1080, 1920), Image.LANCZOS), 0.8)
e = eagle.resize((int(eagle.width * 1.25), int(eagle.height * 1.25)), Image.LANCZOS)
v.alpha_composite(e, (1080 - e.width + 40, 1250 - e.height // 2))
series_title(v, 540, 290, 0.86, 2)
text(v, [("THE", WHITE), ("EAGLE", YEL)], 118, 540, 1390, glow=RG)
text(v, [("WAS", WHITE), ("DRIVING?!", RED)], 118, 540, 1505, glow=RG)
v.convert("RGB").save(f"{OUT}/part2_thumbnail_shorts_1080x1920.png")

bg = vignette(grade(eagle_src, 0.55, 1.1, 0.9).resize((1280, 2276)).crop((0, 600, 1280, 1320)).filter(ImageFilter.GaussianBlur(6)), 0.6)
fc = face.crop((0, 300, 720, 1020)).resize((600, 600), Image.LANCZOS)
fm = Image.new("L", fc.size, 0); ImageDraw.Draw(fm).rounded_rectangle((0, 0, 600, 600), 40, fill=255)
bg.paste(fc, (30, 90), fm.filter(ImageFilter.GaussianBlur(3)))
e2 = eagle.resize((int(eagle.width * 0.9), int(eagle.height * 0.9)), Image.LANCZOS)
bg.alpha_composite(e2, (1280 - e2.width - 10, 720 - e2.height))
series_title(bg, 900, 14, 0.6, 2)
text(bg, [("EAGLE", YEL), ("DRIVER?!", RED)], 84, 540, 600, 8, glow=RG)
bg.convert("RGB").save(f"{OUT}/part2_thumbnail_1280x720.png")
