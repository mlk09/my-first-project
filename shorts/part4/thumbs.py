"""Part 4 thumbnails: the girl's cracked porcelain face with a red robot eye.
Usage: thumbs.py <army_clip> <face_clip> <out_dir> <fonts_dir> <series_thumbs.py dir>"""
import sys, subprocess
from PIL import Image, ImageFilter, ImageDraw
C1_ARMY, C2, OUT, FONTS, LIB = sys.argv[1:6]
sys.argv = [sys.argv[0], "", "", OUT, FONTS]          # series_thumbs helpers read argv at import
sys.path.insert(0, LIB)
import importlib.util
spec = importlib.util.spec_from_file_location("st", f"{LIB}/series_thumbs.py")
src = open(f"{LIB}/series_thumbs.py").read().split("# ---------------- Part 1")[0]   # helpers only
st = {}; exec(compile(src, "series_thumbs_helpers", "exec"), st)
grade, vignette, text, series_title = st["grade"], st["vignette"], st["text"], st["series_title"]
WHITE, YEL, RED, RG = st["WHITE"], st["YEL"], st["RED"], st["RG"]

def frame(clip, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", clip, "-frames:v", "1", "-vf", "delogo=x=384:y=765:w=36:h=36",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (480, 864), raw)

face = grade(frame(C2, 36.9), 1.1, 1.25, 1.2)            # half porcelain, half metal, red eye
big = face.resize((1080, 1944), Image.LANCZOS).filter(ImageFilter.UnsharpMask(4, 120, 2))
canvas = big.resize((1080, 1920)).filter(ImageFilter.GaussianBlur(40)).point(lambda p: int(p * 0.45))
canvas.paste(big.crop((0, 0, 1080, 1920 - 360)), (0, 360))      # push the face down so the title sits above it
fade = Image.linear_gradient("L").resize((1080, 160))
canvas.paste(big.crop((0, 0, 1080, 160)).filter(ImageFilter.GaussianBlur(20)), (0, 360), Image.eval(fade, lambda p: 255 - p))
v = vignette(canvas, 0.55)
series_title(v, 540, 290, 0.86, 4)
text(v, [("SHE", WHITE), ("WAS", WHITE), ("NEVER", WHITE)], 112, 540, 1400, glow=RG)
text(v, [("HUMAN?!", RED)], 146, 540, 1505, glow=RG)
v.convert("RGB").save(f"{OUT}/part4_thumbnail_shorts_1080x1920.png")

bg = vignette(grade(frame(C1_ARMY, 33.5), 1.15, 1.2, 1.2).resize((1280, 2304), Image.LANCZOS).crop((0, 500, 1280, 1220)).filter(ImageFilter.GaussianBlur(3)), 0.5)
fc = face.crop((0, 140, 480, 620)).resize((560, 560), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 110, 2))
fm = Image.new("L", fc.size, 0); ImageDraw.Draw(fm).rounded_rectangle((0, 0, 560, 560), 34, fill=255)
bg.paste(fc, (30, 120), fm.filter(ImageFilter.GaussianBlur(2)))
series_title(bg, 900, 14, 0.6, 4)
text(bg, [("SHE", WHITE), ("WAS", WHITE), ("NEVER", WHITE), ("HUMAN?!", RED)], 72, 900, 600, 8, glow=RG)
bg.convert("RGB").save(f"{OUT}/part4_thumbnail_1280x720.png")
