"""Apply the v3 recolour to the 1280x720 thumbnail source frame. Usage: thumb_recolor.py <in.png> <out.png>"""
import sys, numpy as np, cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import process
from recolor import recolor
from robot import paint_orange
src = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB)
box = (372, 245, 532, 602)                  # robot in the 1280x720 frame at 8.0s
m = process.mask_step(src, box)
out = paint_orange(recolor(src, 560, 600), m)
eyes, _ = process.find_eyes(src, m)
out = process.draw_eyes(out, eyes)
cv2.imwrite(sys.argv[2], cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
print("eyes", [tuple(round(v) for v in e) for e in eyes])
