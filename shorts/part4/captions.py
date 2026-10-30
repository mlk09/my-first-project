"""Part 4 caption PNGs (1080x1920, transparent), colourful horror style, plus the opening PART 4 tag.
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
GOLD = (255, 190, 40, 140)
caps = [
    ([("THEY", WHITE), ("CAME", WHITE), ("OUT", WHITE), ("OF", WHITE), ("THE", WHITE), ("DARK", RED)], RG),
    ([("BOLT", ORA), ("STAYED", WHITE), ("BY", WHITE), ("HER", WHITE), ("SIDE", WHITE)], None),
    ([("BUT", WHITE), ("THEY", WHITE), ("BOWED", YEL), ("TO", WHITE), ("HER", WHITE)], None),
    ([("SHE", WHITE), ("GAVE", WHITE), ("THE", WHITE), ("ORDER...", RED)], RG),
    ([("LOOK", WHITE), ("AT", WHITE), ("HER", WHITE), ("REFLECTION", CYAN)], None),
    ([("SHE", WHITE), ("WAS", WHITE), ("NEVER", WHITE), ("HUMAN", RED)], RG),
    ([("THE", WHITE), ("EAGLE", YEL), ("CHOSE", WHITE), ("BOLT", ORA)], None),
    ([("RUN!", RED)], RG),
    ([("SEE", WHITE), ("YOU", WHITE), ("AT", WHITE), ("11:47...", RED)], RG),
]
for i, (segs, glow) in enumerate(caps):
    text_img(segs, 104, glow=glow).save(f"{OUT}/cap{i+1}.png")

tag = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(tag)
tag.alpha_composite(text_img([("BOLT:", ORA)], 64, y=0.05, stroke=7))
tag.alpha_composite(text_img([("THE", CYAN), ("LAST", YEL), ("TRAM", RED), ("AT", WHITE), ("11:47", YEL)], 80, y=0.05 + 0.04, stroke=8))
f = ImageFont.truetype(BANG, 62); t = "PART 4"; tw = d.textlength(t, font=f)
bx0, by0 = (W - tw) / 2 - 28, int(H * 0.09) + 100
d = ImageDraw.Draw(tag)
d.rounded_rectangle((bx0, by0, bx0 + tw + 56, by0 + 78), 16, fill="#E3101B", outline="white", width=4)
d.text((W / 2, by0 + 41), t, font=f, fill="white", anchor="mm", stroke_width=3, stroke_fill="black")
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
