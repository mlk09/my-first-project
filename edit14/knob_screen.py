#!/usr/bin/env python3
"""Projects the knob centre through the shot camera for every frame -> work/knob_xy.json
(1080x1920 pixel coords), so the edit can draw the rotation arrow right on the knob."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
_spec = importlib.util.spec_from_file_location("s14", os.path.join(HERE, "scene3d.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)
import bpy  # noqa: E402,F401
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402
from timeline import N  # noqa: E402

sc = m.k.reset()
m.build(sc)
m.k.setup_render(sc, False)
kp = m.KNOB + Vector((0, -0.2, 0.3))
xy = []
for f in range(N):
    sc.frame_set(f)
    co = world_to_camera_view(sc, sc.camera, kp)
    xy.append((round(co.x * 1080), round((1 - co.y) * 1920)))
json.dump(xy, open(os.path.join(HERE, "work", "knob_xy.json"), "w"))
print("wrote knob_xy.json")
