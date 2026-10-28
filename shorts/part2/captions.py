"""Part 2 caption PNGs (1080x1920, transparent), colourful horror style, plus the opening PART 2 tag.
Usage: captions.py <out_dir> <fonts_dir>"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT, FONTS = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
BANG = f"{FONTS}/Bangers-Regular.ttf"
WHITE, YEL, CYAN, ORA, RED, LIME, PINK = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF9A1F", "#FF2E3A", "#7CFF4F", "#FF4FD8"

def text_img(segs, size, y=0.66, stroke=9, glow=None):
    img = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(img); f = ImageFont.truetype(BANG, size)
    sp = d.textlength(" ", font=f); ws = [d.textlength(t, font=f) for t, _ in segs]
    x0 = (W - sum(ws) - sp * (len(segs) - 1)) / 2; yy = int(H * y)
    sh = Image.new("RGBA", (W, H)); sd = ImageDraw.Draw(sh); x = x0
    for (t, c), w in zip(segs, ws):
        sd.text((x, yy + 10), t, font=f, fill=(0, 0, 0, 190), stroke_width=stroke, stroke_fill=(0, 0, 0, 190)); x += w + sp
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    if glow:   # soft red halo behind the words for the horror beats
        g = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(g); x = x0
        for (t, c), w in zip(segs, ws):
            gd.text((x, yy), t, font=f, fill=glow, stroke_width=stroke + 8, stroke_fill=glow); x += w + sp
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img); x = x0
    for (t, c), w in zip(segs, ws):
        d.text((x, yy), t, font=f, fill=c, stroke_width=stroke, stroke_fill="black"); x += w + sp
    return img

RG = (255, 30, 40, 150)
caps = [
    ([("THE", WHITE), ("TRAM", WHITE), ("WAS", WHITE), ("EMPTY...", RED)], None),
    ([("BUT", WHITE), ("HE", WHITE), ("WASN'T", WHITE), ("ALONE", RED)], RG),
    ([("THE", WHITE), ("HUNTERS", ORA), ("FOUND", WHITE), ("HIM", WHITE)], None),
    ([("THEN", WHITE), ("THE", WHITE), ("EAGLE", YEL), ("STRUCK", RED)], None),
    ([("IT", WHITE), ("WAS", WHITE), ("PROTECTING", LIME), ("HIM", WHITE)], None),
    ([("THE", WHITE), ("EAGLE", YEL), ("WAS", WHITE), ("DRIVING", RED)], RG),
    ([("THEN", WHITE), ("IT", WHITE), ("VANISHED", PINK)], RG),
    ([("LAST", WHITE), ("TRAM", WHITE), ("·", WHITE), ("11:47", YEL), ("·", WHITE), ("1986", RED)], None),
]
for i, (segs, glow) in enumerate(caps):
    text_img(segs, 104, glow=glow).save(f"{OUT}/cap{i+1}.png")

tag = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(tag)
tag.alpha_composite(text_img([("THE", CYAN), ("LAST", YEL), ("TRAM", RED)], 92, y=0.075, stroke=8))
f = ImageFont.truetype(BANG, 70); t = "PART 2"; tw = d.textlength(t, font=f)
bx0, by0 = (W - tw) / 2 - 30, int(H * 0.075) + 112
d = ImageDraw.Draw(tag)
d.rounded_rectangle((bx0, by0, bx0 + tw + 60, by0 + 88), 18, fill="#E3101B", outline="white", width=4)
d.text((W / 2, by0 + 46), t, font=f, fill="white", anchor="mm", stroke_width=3, stroke_fill="black")
tag.save(f"{OUT}/tag.png")

# --- rain layers: vertically tileable, stacked twice for scrolling ---
import random
def rain(name, n, lmin, lmax, wid, alpha, slant, blur):
    random.seed(name)
    tile = Image.new("L", (W, H), 0); d = ImageDraw.Draw(tile)
    for _ in range(n):
        x, y, L = random.uniform(-100, W + 100), random.uniform(0, H), random.uniform(lmin, lmax)
        a = int(alpha * random.uniform(0.5, 1))
        for dy in (0, -H, H):
            d.line([(x, y + dy), (x + slant * L, y + L + dy)], fill=a, width=wid)
    tile = tile.filter(ImageFilter.GaussianBlur(blur))
    big = Image.new("L", (W, 2 * H)); big.paste(tile, (0, 0)); big.paste(tile, (0, H))
    big.save(f"{OUT}/{name}.png")
rain("rain_far", 1200, 25, 60, 1, 110, 0.12, 0.6)
rain("rain_near", 220, 90, 190, 3, 150, 0.14, 1.2)
