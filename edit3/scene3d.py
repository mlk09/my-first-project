#!/usr/bin/env python3
"""3D inserts for the millis() vs delay() short (Blender, procedural, no assets).

Three stages on one timeline (30 fps); only their frame ranges get rendered:
  A  hook      0-104   Arduino + ticking 3D stopwatch, "millis()" vs "delay()"
  C  counter 315-464   millis() counter that never stops, orbiting green chevrons
  E  lanes   675-899   delay() lane freezes at a red wall; millis() lane keeps going

Reuses the modelling helpers from edit2/scene3d.py.
Run: python3 edit3/scene3d.py [--preview] [--only A|C|E]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit2"))
import scene3d as k  # noqa: E402  (helpers: emit, pbr, text, box, cyl, show, pop, camera, ...)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
RANGES = {"A": (0, 104), "C": (315, 464), "E": (675, 899)}
END = 1200
STAGE_A, STAGE_C, STAGE_E = Vector((0, 0, 0)), Vector((0, 60, 0)), Vector((0, 120, 0))
k.END = END


def arduino_at(pos):
    """edit2's Arduino model is built at k.ARD; temporarily move that anchor."""
    old = k.ARD
    k.ARD = pos
    parts = k.build_arduino()
    k.ARD = old
    return parts


def stopwatch(loc, r=1.1):
    steel = k.pbr("sw_steel", (0.8, 0.82, 0.86), rough=0.18, metal=1.0)
    face = k.emit("sw_face", (0.95, 0.96, 1.0), 1.0)
    red = k.emit("sw_red", (1.0, 0.05, 0.05), 1.4)
    rot = (math.radians(90), 0, 0)
    body = k.cyl("sw_body", r, 0.35, loc, steel, rot=rot, verts=64)
    dial = k.cyl("sw_dial", r * 0.88, 0.05, loc + Vector((0, -0.18, 0)), face, rot=rot, verts=64)
    crown = k.cyl("sw_crown", 0.16, 0.35, loc + Vector((0, 0, r + 0.15)), steel)
    btn = k.cyl("sw_btn", 0.22, 0.12, loc + Vector((0, 0, r + 0.38)), red)
    ticks = []
    for i in range(12):
        a = i / 12 * 2 * math.pi
        p = loc + Vector((math.sin(a) * r * 0.72, -0.21, math.cos(a) * r * 0.72))
        ticks.append(k.box("sw_tick", (0.05, 0.02, 0.16 if i % 3 == 0 else 0.09), p,
                           k.emit("sw_tk", (0.05, 0.05, 0.08), 1.0), rot=(0, a, 0)))
    pivot = bpy.data.objects.new("sw_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = loc + Vector((0, -0.24, 0))
    hand = k.box("sw_hand", (0.05, 0.02, r * 0.7), loc + Vector((0, -0.24, r * 0.3)), red)
    bpy.context.view_layer.update()
    hand.parent = pivot
    hand.matrix_parent_inverse = pivot.matrix_world.inverted()
    return [body, dial, crown, btn, hand] + ticks, pivot


def chevron_ring(center, radius, n, mat, name):
    objs = []
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = center
    for i in range(n):
        a = i / n * 2 * math.pi
        p = center + Vector((math.cos(a) * radius, math.sin(a) * radius, 0))
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.24, depth=0.05, location=p,
                                        rotation=(0, 0, a + math.pi))
        o = bpy.context.object
        o.data.materials.append(mat)
        objs.append(o)
    bpy.context.view_layer.update()
    for o in objs:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    return root, objs


def build(sc):
    k.build_world(sc)
    floor_m = k.pbr("floor3", (0.012, 0.015, 0.03), rough=0.28, metal=0.2)
    ring_m = k.emit("ring3", (0.1, 0.5, 1.0), 4)
    for st in (STAGE_A, STAGE_C, STAGE_E):
        bpy.ops.mesh.primitive_plane_add(size=50, location=st)
        bpy.context.object.data.materials.append(floor_m)
        bpy.ops.mesh.primitive_torus_add(major_radius=3.6, minor_radius=0.015, location=st + Vector((0, 0, 0.005)))
        bpy.context.object.data.materials.append(ring_m)
    S = RANGES
    yel = k.emit("yel3", (1.0, 0.8, 0.05), 1.4)
    grn = k.emit("grn3", (0.05, 1.0, 0.25), 1.4)
    red = k.emit("red3", (1.0, 0.02, 0.03), 1.4)
    wht = k.emit("wht3", (1, 1, 1), 1.2)

    # ---------------- A: hook
    a = STAGE_A
    k.area("A_key", a + Vector((-3, -6, 7)), a, 900, 6)
    k.area("A_rim", a + Vector((6, 3, 3)), a, 500, 4, (0.8, 0.3, 1.0))
    arduino_at(a + Vector((-1.0, 0.8, 0)))
    sw, swp = stopwatch(a + Vector((1.5, -0.3, 1.25)), r=0.95)
    k.interp("LINEAR")
    for f in (0, 104):
        swp.rotation_euler = (0, f * 0.12, 0)
        swp.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    t1 = k.text("A_m", "millis()", 0.75, a + Vector((0.2, -0.6, 4.9)), [grn], extrude=0.02)
    t2 = k.text("A_vs", "vs", 0.45, a + Vector((0.2, -0.6, 4.2)), [wht], extrude=0.01)
    t3 = k.text("A_d", "delay()", 0.75, a + Vector((0.2, -0.6, 3.5)), [red], extrude=0.02)
    for o, f in ((t1, 8), (t2, 16), (t3, 22)):
        k.show(o, [(f, S["A"][1] + 1)])
        k.pop(o, f)

    # ---------------- C: millis() never stops
    c = STAGE_C
    k.area("C_key", c + Vector((-3, -6, 7)), c, 900, 6)
    k.area("C_rim", c + Vector((6, 3, 3)), c, 500, 4, (0.2, 0.6, 1.0))
    arduino_at(c + Vector((0, 0, 0)))
    ring, ring_parts = chevron_ring(c + Vector((0, 0, 0.35)), 2.4, 10, grn, "C_ring")
    k.interp("LINEAR")
    for f in (S["C"][0], S["C"][1]):
        ring.rotation_euler = (0, 0, (f - S["C"][0]) * 0.05)
        ring.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    lbl = k.text("C_lbl", "millis()", 0.5, c + Vector((0, -0.4, 3.6)), [grn], extrude=0.02)
    cnt = k.text("C_cnt", "0 ms", 0.85, c + Vector((0, -0.4, 2.7)), [yel], extrude=0.02)
    sub = k.text("C_sub", "kabhi nahi rukta", 0.32, c + Vector((0, -0.4, 2.05)), [wht], extrude=0.01)
    for o, f in ((lbl, S["C"][0] + 4), (cnt, S["C"][0] + 8), (sub, S["C"][0] + 30)):
        k.show(o, [(f, S["C"][1] + 1)])
        k.pop(o, f)

    # ---------------- E: delay() lane vs millis() lane
    e = STAGE_E
    k.area("E_key", e + Vector((-3, -7, 8)), e, 1000, 7)
    k.area("E_rim", e + Vector((7, 3, 3)), e, 500, 4, (0.8, 0.3, 1.0))
    lane_y = {"delay": 1.7, "millis": -1.3}
    tilt = (math.radians(55), 0, 0)
    track = k.emit("track", (0.15, 0.2, 0.35), 1.0)
    for name, yy in lane_y.items():
        k.box("E_track_" + name, (5.4, 0.6, 0.06), e + Vector((0, yy, 0.05)), track)
    wall = k.box("E_wall", (0.12, 0.8, 1.0), e + Vector((0.2, lane_y["delay"], 0.55)), red)
    hg = k.text("E_wait", "WAIT 1000 ms", 0.36, e + Vector((0.2, lane_y["delay"] - 0.1, 1.5)), [red], extrude=0.01, rot=tilt)
    k.show(hg, [(S["E"][0] + 40, S["E"][0] + 140)])
    k.pop(hg, S["E"][0] + 40)
    lab_d = k.text("E_ld", "delay()  RUKO!", 0.5, e + Vector((0, lane_y["delay"] + 1.7, 1.7)), [red], extrude=0.02, rot=tilt)
    lab_m = k.text("E_lm", "millis()  CHALTE RAHO", 0.46, e + Vector((0, lane_y["millis"] - 1.0, 0.6)), [grn], extrude=0.02, rot=tilt)
    for o, f in ((lab_d, S["E"][0] + 6), (lab_m, S["E"][0] + 14)):
        k.show(o, [(f, S["E"][1] + 1)])
        k.pop(o, f)
    # cubes ("program tasks") moving along each lane, driven by a straight path
    x0, x1 = e.x - 2.6, e.x + 2.6
    stop_u = (e.x + 0.2 - 0.35 - x0) / (x1 - x0)
    for name, yy, col in (("delay", lane_y["delay"], (0.2, 0.5, 1.0)), ("millis", lane_y["millis"], (0.05, 1.0, 0.3))):
        cu = bpy.data.curves.new("E_path_" + name, "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (x0, e.y + yy, 0.3, 1)
        sp.points[1].co = (x1, e.y + yy, 0.3, 1)
        path = bpy.data.objects.new("E_path_" + name, cu)
        bpy.context.collection.objects.link(path)
        mat = k.emit("E_cube_" + name, col, 1.4)
        for j in range(3):
            bpy.ops.mesh.primitive_cube_add(size=0.42)
            cube = bpy.context.object
            cube.name = f"E_{name}{j}"
            cube.data.materials.append(mat)
            fp = cube.constraints.new("FOLLOW_PATH")
            fp.target = path
            fp.use_fixed_location = True
            f0 = S["E"][0] + j * 70
            keys = [(f0, 0.0), (f0 + 120, 1.0)] if name == "millis" else \
                [(f0, 0.0), (f0 + 55, stop_u), (f0 + 115, stop_u), (f0 + 155, 1.0)]
            k.interp("LINEAR")
            for f, u in keys:
                fp.offset_factor = u
                fp.keyframe_insert("offset_factor", frame=f)
            k.interp("BEZIER")
            k.show(cube, [(f0, min(S["E"][1] + 1, f0 + 156))])
    # LED blinking on the millis lane (multitasking)
    for i in range(3):
        led = k.cyl(f"E_led{i}", 0.13, 0.1, e + Vector((-1.8 + i * 1.8, lane_y["millis"] - 0.55, 0.12)),
                    k.emit(f"E_ledm{i}", (1.0, 0.85, 0.1), 1.4))
        on = [(S["E"][0] + 10 + i * 9 + m * 36, S["E"][0] + 28 + i * 9 + m * 36) for m in range(7)]
        k.show(led, on)

    # ---------------- cameras
    cams = [
        k.camera("cA", [(0, a + Vector((-1.2, -10.5, 3.2)), a + Vector((0.2, 0, 2.6))),
                        (104, a + Vector((0.8, -8.6, 3.2)), a + Vector((0.2, 0, 2.6)))], lens_keys=[(0, 30)]),
        k.camera("cC", [(S["C"][0], c + Vector((-3.0, -8.0, 5.0)), c + Vector((0, 0, 1.7))),
                        (S["C"][1], c + Vector((3.0, -7.4, 4.2)), c + Vector((0, 0, 1.8)))], lens_keys=[(S["C"][0], 28)]),
        k.camera("cE", [(S["E"][0], e + Vector((-1.2, -6.0, 8.0)), e + Vector((0, 0.1, 0.3))),
                        (S["E"][1], e + Vector((1.2, -5.2, 7.2)), e + Vector((0, 0.1, 0.3)))], lens_keys=[(S["E"][0], 26)]),
    ]
    for (key, (f0, _)), cam in zip(RANGES.items(), cams):
        sc.timeline_markers.new(cam.name, frame=f0).camera = cam
    sc.camera = cams[0]

    # live counter text for stage C
    def upd(scene, *_):
        f = scene.frame_current
        ms = max(0, int((f - S["C"][0]) * 33.3 * 2.4))
        bpy.data.objects["C_cnt"].data.body = f"{ms} ms"
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", default="ACE")
    ap.add_argument("--step", type=int, default=1)
    args = ap.parse_args(sys.argv[1:])
    k.FRAMES = FRAMES
    os.makedirs(FRAMES, exist_ok=True)
    sc = k.reset()
    sc.frame_end = END
    build(sc)
    k.setup_render(sc, args.preview)
    sc.render.filepath = os.path.join(FRAMES, "")
    for key in args.only:
        a0, a1 = RANGES[key]
        sc.frame_start, sc.frame_end, sc.frame_step = a0, a1, args.step
        bpy.ops.render.render(animation=True)
