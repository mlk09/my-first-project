import random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
OUT, FONTS, FRAME = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
BANG = f"{FONTS}/Bangers-Regular.ttf"; CREEP = f"{FONTS}/Creepster-Regular.ttf"

# --- rain textures: vertically tileable, stacked twice for scrolling ---
def rain(name, n, lmin, lmax, wid, alpha, slant, blur):
    random.seed(name)
    tile = Image.new("L", (W, H), 0); d = ImageDraw.Draw(tile)
    for _ in range(n):
        x, y, L = random.uniform(-100, W+100), random.uniform(0, H), random.uniform(lmin, lmax)
        a = int(alpha*random.uniform(0.5, 1))
        for dy in (0, -H, H):  # wrap so the tile seams vanish
            d.line([(x, y+dy), (x+slant*L, y+L+dy)], fill=a, width=wid)
    tile = tile.filter(ImageFilter.GaussianBlur(blur))
    big = Image.new("L", (W, 2*H)); big.paste(tile, (0, 0)); big.paste(tile, (0, H))
    big.save(f"{OUT}/{name}.png")
rain("rain_far", 1400, 25, 60, 1, 120, 0.12, 0.6)
rain("rain_near", 260, 90, 190, 3, 170, 0.14, 1.2)

# --- colourful captions: list of (word, colour) segments ---
def text_img(segs, size, font=BANG, stroke=9, y=0.66, name=None):
    img = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font, size)
    space = d.textlength(" ", font=f)
    widths = [d.textlength(t, font=f) for t, _ in segs]
    total = sum(widths) + space*(len(segs)-1)
    x = (W-total)/2; yy = int(H*y)
    # soft shadow
    sh = Image.new("RGBA", (W, H)); sd = ImageDraw.Draw(sh); xs = x
    for (t, c), w in zip(segs, widths):
        sd.text((xs, yy+10), t, font=f, fill=(0,0,0,170), stroke_width=stroke, stroke_fill=(0,0,0,170)); xs += w+space
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(img)
    for (t, c), w in zip(segs, widths):
        d.text((x, yy), t, font=f, fill=c, stroke_width=stroke, stroke_fill="black"); x += w+space
    if name: img.save(f"{OUT}/{name}.png")
    return img

WHITE, YEL, CYAN, ORA, RED, LIME, PINK = "#FFFFFF", "#FFE81F", "#2EE6FF", "#FF9A1F", "#FF2E3A", "#7CFF4F", "#FF4FD8"
caps = [
  [("EVERY","#FFFFFF"),("NIGHT",WHITE),("AT",WHITE),("11:47",YEL)],
  [("THE",WHITE),("LAST",CYAN),("TRAM",CYAN),("ARRIVES",WHITE)],
  [("HE",WHITE),("WAITED",WHITE),("40",ORA),("YEARS",ORA)],
  [("BUT",WHITE),("TONIGHT...",RED)],
  [("SOMEONE",LIME),("ELSE",LIME),("WANTS",WHITE),("IN",PINK)],
  [("NOT",WHITE),("THIS",YEL),("TIME.",RED)],
]
for i, c in enumerate(caps): text_img(c, 104, name=f"cap{i+1}")

# --- brand block: yellow banner + red "EVIL ROBOT" + yellow "STORY 2" ---
def brand(canvas, cx, top, scale=1.0, sub="STORY 2"):
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(CREEP, int(150*scale))
    tw = d.textlength("EVIL ROBOT", font=f); bb = d.textbbox((0,0), "EVIL ROBOT", font=f)
    pad = int(34*scale); bw, bh = tw+2*pad, bb[3]-bb[1]+2*pad
    banner = Image.new("RGBA", (int(bw), int(bh)), YEL)
    canvas.alpha_composite(Image.new("RGBA", banner.size, (0,0,0,140)).filter(ImageFilter.GaussianBlur(10)), (int(cx-bw/2)+10, top+12))
    canvas.alpha_composite(banner, (int(cx-bw/2), top))
    d = ImageDraw.Draw(canvas)
    d.text((cx-tw/2, top+pad-bb[1]), "EVIL ROBOT", font=f, fill="#E3101B", stroke_width=max(2,int(3*scale)), stroke_fill="#5A0006")
    fs = ImageFont.truetype(BANG, int(150*scale))
    sw = d.textlength(sub, font=fs)
    d.text((cx-sw/2, top+bh+int(22*scale)), sub, font=fs, fill=YEL, stroke_width=int(10*scale), stroke_fill="black")
    return top+bh+int(22*scale)+int(170*scale)

end = Image.new("RGBA", (W, H)); brand(end, W//2, int(H*0.33))
d = ImageDraw.Draw(end); f = ImageFont.truetype(BANG, 72); t = "FOLLOW FOR STORY 3"
d.text(((W-d.textlength(t, font=f))/2, int(H*0.33)+520), t, font=f, fill=CYAN, stroke_width=7, stroke_fill="black")
end.save(f"{OUT}/endcard.png")

# --- thumbnails ---
def grade(im):
    im = ImageEnhance.Brightness(im).enhance(1.35); im = ImageEnhance.Contrast(im).enhance(1.15)
    im = ImageEnhance.Color(im).enhance(1.3);  return im.filter(ImageFilter.UnsharpMask(3, 120, 2))
src = Image.open(FRAME).convert("RGB")  # 1280x720
v = grade(src.crop((300, 0, 705, 720)).resize((W, H), Image.LANCZOS)).convert("RGBA")
rl = Image.open(f"{OUT}/rain_near.png").crop((0,300,W,300+H))
v.alpha_composite(Image.merge("RGBA", (*[Image.new("L",(W,H),230)]*3, rl.point(lambda p: int(p*0.55)))))
brand(v, W//2, 110)
text_img([("HE",WHITE),("WON'T",WHITE),("MISS",YEL),("IT",YEL),("AGAIN",RED)], 112, y=0.80, name=None)
v.alpha_composite(text_img([("HE",WHITE),("WON'T",WHITE),("MISS",YEL),("IT",YEL),("AGAIN",RED)], 112, y=0.80))
v.convert("RGB").save(f"{OUT}/thumbnail_shorts_1080x1920.png")

h = grade(src.crop((0, 0, 1120, 630)).resize((1280, 720), Image.LANCZOS)).convert("RGBA")
hb = Image.new("RGBA", (1280, 720)); brand(hb, 400, 40, scale=0.62)
h.alpha_composite(hb); h.convert("RGB").save(f"{OUT}/thumbnail_1280x720.png")
