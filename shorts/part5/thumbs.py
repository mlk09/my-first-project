"""Part 5 thumbnails: Bolt among rows of robot copies, and the girl's red eyes.
Usage: thumbs.py <workshop_clip> <girl_clip> <out_dir> <fonts_dir> <series_thumbs.py dir>"""
import sys, subprocess
from PIL import Image, ImageFilter, ImageDraw
C1, C3, OUT, FONTS, LIB = sys.argv[1:6]
src = open(f"{LIB}/series_thumbs.py").read().split("# ---------------- Part 1")[0]   # helpers only
st = {}; sys.argv = [sys.argv[0], "", "", OUT, FONTS]; exec(compile(src, "series_thumbs_helpers", "exec"), st)
grade, vignette, text, series_title = st["grade"], st["vignette"], st["text"], st["series_title"]
WHITE, YEL, RED, RG = st["WHITE"], st["YEL"], st["RED"], st["RG"]

def frame(clip, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", clip, "-frames:v", "1", "-vf", "delogo=x=570:y=1130:w=60:h=60",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (720, 1280), raw)

shop = grade(frame(C1, 39.5), 1.35, 1.2, 1.2)
v = vignette(shop.resize((1080, 1920), Image.LANCZOS), 0.5)
series_title(v, 540, 290, 0.86, 5)
text(v, [("COPIES", RED), ("OF", WHITE)], 130, 540, 1380, glow=RG)
text(v, [("HIM?!", RED)], 150, 540, 1500, glow=RG)
v.convert("RGB").save(f"{OUT}/part5_thumbnail_shorts_1080x1920.png")

bg = vignette(grade(frame(C1, 39.5), 1.25, 1.2, 1.15).resize((1280, 2276), Image.LANCZOS).crop((0, 900, 1280, 1620)).filter(ImageFilter.GaussianBlur(3)), 0.5)
girl = grade(frame(C3, 40.3), 1.1, 1.2, 1.15).crop((60, 200, 660, 800)).resize((560, 560), Image.LANCZOS)
gm = Image.new("L", girl.size, 0); ImageDraw.Draw(gm).rounded_rectangle((0, 0, 560, 560), 34, fill=255)
bg.paste(girl, (30, 120), gm.filter(ImageFilter.GaussianBlur(2)))
series_title(bg, 900, 14, 0.6, 5)
text(bg, [("WELCOME", WHITE), ("HOME...", RED)], 84, 900, 600, 8, glow=RG)
bg.convert("RGB").save(f"{OUT}/part5_thumbnail_1280x720.png")
