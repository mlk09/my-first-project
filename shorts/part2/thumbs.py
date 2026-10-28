"""Part 2 thumbnails: robot's red-eyed face + the eagle cut out of the driver's-seat shot.
Usage: thumbs.py <src_clip> <out_dir> <fonts_dir>"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from rembg import new_session, remove
SRC, OUT, FONTS = sys.argv[1:4]
BANG = f"{FONTS}/Bangers-Regular.ttf"
WHITE, YEL, CYAN, RED = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF2E3A"

def frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-vf", "delogo=x=570:y=1130:w=60:h=60",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (720, 1280), raw)

def grade(im, b=1.05, c=1.25, s=1.15):
    im = ImageEnhance.Brightness(im).enhance(b); im = ImageEnhance.Contrast(im).enhance(c)
    return ImageEnhance.Color(im).enhance(s).filter(ImageFilter.UnsharpMask(3, 110, 2))

def vignette(im, strength=0.75):
    w, h = im.size; y, x = np.ogrid[:h, :w]
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    m = np.clip(1 - strength * np.clip(r - 0.35, 0, 1) ** 1.4, 0, 1)
    return Image.fromarray((np.asarray(im).astype(np.float32) * m[..., None]).astype(np.uint8))

def text(canvas, segs, size, cx, y, stroke=10, glow=None):
    d = ImageDraw.Draw(canvas); f = ImageFont.truetype(BANG, size)
    sp = d.textlength(" ", font=f); ws = [d.textlength(t, font=f) for t, _ in segs]
    x0 = cx - (sum(ws) + sp * (len(segs) - 1)) / 2
    lay = Image.new("RGBA", canvas.size); ld = ImageDraw.Draw(lay); x = x0
    for (t, c), w in zip(segs, ws):
        ld.text((x, y + 12), t, font=f, fill=(0, 0, 0, 200), stroke_width=stroke, stroke_fill=(0, 0, 0, 200)); x += w + sp
    canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    if glow:
        lay = Image.new("RGBA", canvas.size); ld = ImageDraw.Draw(lay); x = x0
        for (t, c), w in zip(segs, ws):
            ld.text((x, y), t, font=f, fill=glow, stroke_width=stroke + 10, stroke_fill=glow); x += w + sp
        canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(canvas); x = x0
    for (t, c), w in zip(segs, ws):
        d.text((x, y), t, font=f, fill=c, stroke_width=stroke, stroke_fill="black"); x += w + sp

def badge(canvas, label, cx, y, size):
    d = ImageDraw.Draw(canvas); f = ImageFont.truetype(BANG, size); tw = d.textlength(label, font=f)
    d.rounded_rectangle((cx - tw / 2 - 28, y, cx + tw / 2 + 28, y + size * 1.2), 16, fill="#E3101B", outline="white", width=4)
    d.text((cx, y + size * 0.62), label, font=f, fill="white", anchor="mm", stroke_width=3, stroke_fill="black")

face = grade(frame(9.2), b=1.0, c=1.3, s=1.2)                  # robot close-up, red eyes
eagle_src = frame(22.5)
sess = new_session("isnet-general-use")
crop = eagle_src.crop((180, 420, 640, 920))                    # eagle on the driver's seat
em = remove(crop, session=sess, only_mask=True)
eagle = grade(crop, 1.1, 1.15, 1.1).convert("RGBA"); eagle.putalpha(em)
eagle = eagle.crop(eagle.getbbox())
RG = (255, 30, 40, 160)

# vertical 1080x1920 (text inside the 4:5 band y 285..1635)
v = vignette(face.resize((1080, 1920), Image.LANCZOS), 0.8).convert("RGBA")
e = eagle.resize((int(eagle.width * 1.25), int(eagle.height * 1.25)), Image.LANCZOS)
v.alpha_composite(e, (1080 - e.width + 40, 1250 - e.height // 2))
text(v, [("THE", CYAN), ("LAST", YEL), ("TRAM", RED)], 150, 540, 300)
badge(v, "PART 2", 540, 470, 80)
text(v, [("THE", WHITE), ("EAGLE", YEL)], 120, 540, 1380, glow=RG)
text(v, [("WAS", WHITE), ("DRIVING?!", RED)], 120, 540, 1505, glow=RG)
v.convert("RGB").save(f"{OUT}/thumbnail_shorts_1080x1920.png")

# wide 1280x720: face left, eagle right, title centred
bg = vignette(grade(eagle_src, 0.55, 1.1, 0.9).resize((1280, 2276)).crop((0, 600, 1280, 1320)).filter(ImageFilter.GaussianBlur(6)), 0.6).convert("RGBA")
fc = face.crop((0, 300, 720, 1020)).resize((620, 620), Image.LANCZOS)
fm = Image.new("L", fc.size, 0); ImageDraw.Draw(fm).rounded_rectangle((0, 0, 620, 620), 40, fill=255)
bg.paste(fc, (30, 70), fm.filter(ImageFilter.GaussianBlur(3)))
e2 = eagle.resize((int(eagle.width * 0.95), int(eagle.height * 0.95)), Image.LANCZOS)
bg.alpha_composite(e2, (1280 - e2.width - 10, 720 - e2.height))
text(bg, [("THE", CYAN), ("LAST", YEL), ("TRAM", RED)], 104, 900, 40, 8)
badge(bg, "PART 2", 900, 170, 58)
text(bg, [("EAGLE", YEL), ("DRIVER?!", RED)], 86, 560, 590, 8, glow=RG)
bg.convert("RGB").save(f"{OUT}/thumbnail_1280x720.png")
