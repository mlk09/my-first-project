"""Part 3 thumbnails: the girl and Bolt facing a tunnel of red robot eyes.
Usage: thumbs.py <clip_with_red_eyes> <clip_with_girl> <out_dir> <fonts_dir> <series_thumbs.py dir>"""
import sys, subprocess
from PIL import Image, ImageFilter, ImageDraw
C3, C2, OUT, FONTS, LIB = sys.argv[1:6]
sys.argv = [sys.argv[0], "", "", OUT, FONTS]          # series_thumbs helpers read argv at import
sys.path.insert(0, LIB)
import importlib.util
spec = importlib.util.spec_from_file_location("st", f"{LIB}/series_thumbs.py")
src = open(f"{LIB}/series_thumbs.py").read().split("# ---------------- Part 1")[0]   # helpers only
st = {}; exec(compile(src, "series_thumbs_helpers", "exec"), st)
grade, vignette, text, series_title = st["grade"], st["vignette"], st["text"], st["series_title"]
WHITE, YEL, RED, RG = st["WHITE"], st["YEL"], st["RED"], st["RG"]

def frame(clip, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", clip, "-frames:v", "1", "-vf", "delogo=x=570:y=1130:w=60:h=60",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (720, 1280), raw)

army = grade(frame(C3, 36.6), 1.25, 1.2, 1.25)          # girl + Bolt from behind, red eyes everywhere
v = vignette(army.resize((1080, 1920), Image.LANCZOS), 0.55)
series_title(v, 540, 290, 0.86, 3)
text(v, [("WHO", WHITE), ("ELSE", WHITE), ("WAS", WHITE)], 116, 540, 1040, glow=RG)
text(v, [("WAITING?!", RED)], 140, 540, 1160, glow=RG)
v.convert("RGB").save(f"{OUT}/part3_thumbnail_shorts_1080x1920.png")

# wide: red-eye army behind, the smiling girl + Bolt + eagle on the left
bg = vignette(grade(frame(C3, 37.6), 1.3, 1.2, 1.25).resize((1280, 2276), Image.LANCZOS).crop((0, 420, 1280, 1140)), 0.5)
girl = grade(frame(C2, 39.7), 1.0, 1.15, 1.1).crop((0, 120, 720, 1280)).resize((420, 677), Image.LANCZOS)
gm = Image.new("L", girl.size, 0); ImageDraw.Draw(gm).rounded_rectangle((0, 0, girl.width, girl.height), 30, fill=255)
bg.paste(girl, (24, 30), gm.filter(ImageFilter.GaussianBlur(2)))
series_title(bg, 860, 14, 0.6, 3)
text(bg, [("WHO", WHITE), ("ELSE", WHITE), ("WAS", WHITE), ("WAITING?!", RED)], 74, 860, 600, 8, glow=RG)
bg.convert("RGB").save(f"{OUT}/part3_thumbnail_1280x720.png")
