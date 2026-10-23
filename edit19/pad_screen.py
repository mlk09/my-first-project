#!/usr/bin/env python3
"""Projects the touch-pad centre (and a point 1 cm above it along the pad normal) through the shot
camera for every frame -> work/pad_xy.json (1080x1920 pixel coords + on-screen pad radius), so the
edit can land the finger and the touch ripples right on the pad."""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
_spec = importlib.util.spec_from_file_location("s19", os.path.join(HERE, "scene3d.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402
from timeline import N  # noqa: E402

sc = m.k.reset()
m.build(sc)
m.k.setup_render(sc, False)
t = math.radians(m.TILT)
up = Vector((0, -math.sin(t), math.cos(t)))                 # pad normal
side = Vector((1.0, 0, 0))
out = []
for f in range(N):
    sc.frame_set(f)
    p = world_to_camera_view(sc, sc.camera, m.PAD)
    q = world_to_camera_view(sc, sc.camera, m.PAD + side * 1.0)
    c = (p.x * 1080, (1 - p.y) * 1920)
    r = math.hypot(q.x * 1080 - c[0], (1 - q.y) * 1920 - c[1])
    out.append((round(c[0]), round(c[1]), round(r, 1)))
json.dump(out, open(os.path.join(HERE, "work", "pad_xy.json"), "w"))
print("wrote pad_xy.json")
