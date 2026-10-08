#!/usr/bin/env python3
"""Cut the snake mascot out of the original channel art -> assets/mascot.png"""
import cv2
import numpy as np
from PIL import Image

im = np.asarray(Image.open("assets/original_banner.jpg").convert("RGB")).astype(np.int32)
x0, y0, x1, y1 = 1130, 150, 1570, 925
c = im[y0:y1, x0:x1]
r, g, b = c[..., 0], c[..., 1], c[..., 2]
luma = 0.3 * r + 0.59 * g + 0.11 * b
bg = (g > r + 8) & (g > b + 5) & (luma < 75)          # dark chalkboard green
fg = cv2.morphologyEx((~bg).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (23, 23)))
h, w = m.shape
ff = m.copy()
cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255)
m = m | cv2.bitwise_not(ff)                               # fill holes
m = cv2.GaussianBlur(cv2.erode(m, np.ones((3, 3), np.uint8)), (5, 5), 0)
ys, xs = np.nonzero(m)
out = np.dstack([c.astype(np.uint8), m])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
Image.fromarray(out, "RGBA").save("assets/mascot.png")
print("mascot", out.shape)
