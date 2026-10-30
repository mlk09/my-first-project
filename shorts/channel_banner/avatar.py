"""YouTube profile picture (800x800, shown as a circle): Bolt's red-eyed face, orange ring, SPOOKY TALES.
Usage: avatar.py <face_frame_720x1280.png> <out.png> <fonts_dir>"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, OUT, FONTS = sys.argv[1:4]
N = 800
face = Image.open(SRC).convert("RGB")
face = ImageEnhance.Contrast(face).enhance(1.25); face = ImageEnhance.Color(face).enhance(1.25)
face = ImageEnhance.Brightness(face).enhance(1.05).filter(ImageFilter.UnsharpMask(3, 120, 2))
crop = face.crop((0, 300, 720, 1020)).resize((620, 620), Image.LANCZOS)
base = face.crop((0, 300, 720, 1020)).resize((N, N)).filter(ImageFilter.GaussianBlur(30)).point(lambda p: int(p * 0.35))
base.paste(crop, (90, 40)); crop = base   #
yy, xx = np.ogrid[:N, :N]
r = np.sqrt((xx - N / 2) ** 2 + (yy - N / 2) ** 2) / (N / 2)
vig = np.clip(1 - 0.8 * np.clip(r - 0.55, 0, 1) ** 1.2, 0, 1)
img = Image.fromarray((np.asarray(crop).astype(np.float32) * vig[..., None]).astype(np.uint8)).convert("RGBA")

# bottom label band, kept inside the circle
d = ImageDraw.Draw(img)
band = Image.new("RGBA", (N, N)); bd = ImageDraw.Draw(band)
bd.rectangle((0, 600, N, N), fill=(10, 6, 20, 200))
img.alpha_composite(band.filter(ImageFilter.GaussianBlur(14)))
f = ImageFont.truetype(f"{FONTS}/Bangers-Regular.ttf", 92)
d = ImageDraw.Draw(img)
segs = [("SPOOKY", "#FF9A1F"), ("TALES", "#FFE81F")]
sp = d.textlength(" ", font=f); ws = [d.textlength(t, font=f) for t, _ in segs]; x = (N - sum(ws) - sp) / 2
glow = Image.new("RGBA", (N, N)); gd = ImageDraw.Draw(glow); gx = x
for (t, c), w in zip(segs, ws):
    gd.text((gx, 622), t, font=f, fill=(255, 120, 20, 170), stroke_width=18, stroke_fill=(255, 120, 20, 170)); gx += w + sp
img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
d = ImageDraw.Draw(img)
for (t, c), w in zip(segs, ws):
    d.text((x, 622), t, font=f, fill=c, stroke_width=8, stroke_fill="black"); x += w + sp

# orange ring with a dark inner edge
ring = Image.new("RGBA", (N, N)); rd = ImageDraw.Draw(ring)
rd.ellipse((6, 6, N - 6, N - 6), outline="#FF7A1A", width=34)
rd.ellipse((38, 38, N - 38, N - 38), outline=(0, 0, 0, 200), width=8)
img.alpha_composite(ring)
mask = Image.new("L", (N, N), 0); ImageDraw.Draw(mask).ellipse((0, 0, N - 1, N - 1), fill=255)
out = Image.new("RGBA", (N, N), (0, 0, 0, 0)); out.paste(img, (0, 0), mask)
out.save(OUT)
