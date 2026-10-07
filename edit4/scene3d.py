#!/usr/bin/env python3
"""3D inserts for "INPUT_PULLUP" short (Arduino · Code ka Raaz #4). Procedural, no assets.

Stages on one 30 fps timeline (only these ranges are rendered):
  A hook      0-119   push-button wired to an Arduino, nobody touches it, "PRESSED?!" flickers
  C floating 360-659  a lone header pin + loose wire, noise waves hit it, its value jumps 0/1
  D pull-up  660-809  a glowing spring pulls the pin up to a 5V rail, value locks at 1
Run: python3 edit4/scene3d.py [--preview] [--only ACD] [--step N]
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit2"))
import scene3d as k  # noqa: E402  helpers from the Serial.begin video
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
RANGES = {"A": (0, 120), "C": (360, 660), "D": (660, 810)}
END = 1350
k.END = END
STAGE_A, STAGE_C = Vector((0, 0, 0)), Vector((0, 60, 0))
ATTACH = 705          # frame the pull-up spring reaches the 5V rail


def arduino_at(pos):
    old = k.ARD
    k.ARD = pos
    parts = k.build_arduino()
    k.ARD = old
    return parts


def push_button(loc, cap_col=(0.9, 0.08, 0.08)):
    body = k.pbr("btn_body", (0.03, 0.03, 0.035), rough=0.45)
    metal = k.pbr("btn_metal", (0.75, 0.76, 0.8), rough=0.25, metal=1.0)
    cap = k.pbr("btn_cap", cap_col, rough=0.3, em=cap_col, ems=0.15)
    k.box("btn_base", (1.3, 1.3, 0.45), loc + Vector((0, 0, 0.23)), body)
    k.box("btn_plate", (1.0, 1.0, 0.06), loc + Vector((0, 0, 0.48)), metal)
    c = k.cyl("btn_cap", 0.38, 0.36, loc + Vector((0, 0, 0.68)), cap, verts=48)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("btn_leg", (0.08, 0.04, 0.35), loc + Vector((sx * 0.55, sy * 0.68, -0.05)), metal)
    return c


def wire(name, pts, col, r=0.05):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(k.pbr(name + "m", col, rough=0.35))
    return o


def header_pin(loc, h=2.2):
    gold = k.pbr("pin_gold", (0.95, 0.72, 0.3), rough=0.2, metal=1.0)
    plastic = k.pbr("pin_plastic", (0.02, 0.02, 0.025), rough=0.5)
    k.box("pin_base", (0.7, 0.7, 0.5), loc + Vector((0, 0, 0.25)), plastic)
    k.box("pin_shaft", (0.16, 0.16, h), loc + Vector((0, 0, 0.5 + h / 2)), gold)
    return loc + Vector((0, 0, 0.5 + h))


def helix(name, a, b, turns=9, radius=0.18):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    n = turns * 16
    sp.points.add(n)
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        ang = t * turns * 2 * math.pi
        sp.points[i].co = (p.x + math.cos(ang) * radius, p.y + math.sin(ang) * radius, p.z, 1)
    cu.bevel_depth = 0.035
    cu.bevel_resolution = 3
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(k.emit(name + "m", (0.1, 1.0, 0.4), 1.4))
    return o


def build(sc):
    k.build_world(sc)
    floor_m = k.pbr("floor4", (0.012, 0.015, 0.03), rough=0.28, metal=0.2)
    ring_m = k.emit("ring4", (0.1, 0.5, 1.0), 4)
    for st in (STAGE_A, STAGE_C):
        bpy.ops.mesh.primitive_plane_add(size=50, location=st)
        bpy.context.object.data.materials.append(floor_m)
        bpy.ops.mesh.primitive_torus_add(major_radius=3.4, minor_radius=0.015, location=st + Vector((0, 0, 0.005)))
        bpy.context.object.data.materials.append(ring_m)
    red = k.emit("red4", (1.0, 0.02, 0.03), 1.4)
    yel = k.emit("yel4", (1.0, 0.8, 0.05), 1.4)
    grn = k.emit("grn4", (0.05, 1.0, 0.25), 1.4)
    wht = k.emit("wht4", (1, 1, 1), 1.2)

    # ---------------- A: hook, ghost presses
    a = STAGE_A
    k.area("A_key", a + Vector((-3, -6, 7)), a, 900, 6)
    k.area("A_rim", a + Vector((6, 3, 3)), a, 500, 4, (0.8, 0.3, 1.0))
    arduino_at(a + Vector((-1.4, 1.0, 0)))
    push_button(a + Vector((1.5, -0.4, 0)))
    wire("A_w1", [a + Vector((1.2, 0.2, 0.3)), a + Vector((0.4, 1.0, 0.8)), a + Vector((-0.6, 1.9, 0.45))], (0.1, 0.4, 1.0))
    wire("A_w2", [a + Vector((1.9, 0.2, 0.3)), a + Vector((1.2, 1.6, 0.9)), a + Vector((-1.6, 1.9, 0.45))], (0.05, 0.05, 0.05))
    pr = k.text("A_pressed", "PRESSED?!", 0.72, a + Vector((0.4, -0.7, 2.9)), [red], extrude=0.02)
    rnd = random.Random(4)
    on, f = [], 8
    while f < 120:
        d = rnd.randint(3, 9)
        on.append((f, min(120, f + d)))
        f += d + rnd.randint(2, 7)
    k.show(pr, on)
    q = k.text("A_q", "kisi ne dabaya?", 0.36, a + Vector((0.4, -0.7, 2.25)), [wht], extrude=0.01)
    k.show(q, [(40, 121)])
    k.pop(q, 40)

    # ---------------- C: floating pin + D: pull-up spring
    c = STAGE_C
    k.area("C_key", c + Vector((-3, -6, 7)), c, 900, 6)
    k.area("C_rim", c + Vector((6, 3, 3)), c, 500, 4, (0.2, 0.6, 1.0))
    top = header_pin(c + Vector((0, 0, 0)))
    wire("C_loose", [top + Vector((0, 0, 0)), top + Vector((0.6, -0.2, 0.7)), top + Vector((1.4, -0.4, 0.4))],
         (0.1, 0.4, 1.0), r=0.045)
    lbl = k.text("C_lbl", "PIN 2", 0.38, c + Vector((-1.2, -0.5, 1.3)), [wht], extrude=0.01)
    k.show(lbl, [(RANGES["C"][0], RANGES["D"][1] + 1)])
    val = k.text("C_val", "0", 1.5, c + Vector((-1.4, -0.4, 3.0)), [yel], extrude=0.03)
    fl = k.text("C_fl", "FLOATING", 0.5, c + Vector((0, -0.4, 4.7)), [red], extrude=0.02)
    k.show(fl, [(RANGES["C"][0] + 20, RANGES["D"][0])])
    k.show(val, [(RANGES["C"][0], ATTACH)])
    one = k.text("D_one", "1", 1.5, c + Vector((-1.4, -0.4, 3.0)), [grn], extrude=0.03)
    k.show(one, [(ATTACH, RANGES["D"][1] + 1)])
    k.pop(one, ATTACH, over=1.3)
    k.pop(fl, RANGES["C"][0] + 20)
    # noise waves rushing at the pin from both sides
    for i in range(10):
        side = -1 if i % 2 else 1
        bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.03,
                                         location=top + Vector((side * 3.0, 0, -0.6)),
                                         rotation=(0, math.radians(90), 0))
        ring = bpy.context.object
        ring.data.materials.append(k.emit(f"C_wave{i}", (0.8, 0.3, 1.0) if i % 3 else (0.2, 0.8, 1.0), 1.4))
        f0 = RANGES["C"][0] + 10 + i * 28
        k.interp("LINEAR")
        for ff, x, s in ((f0, side * 3.0, 0.4), (f0 + 26, side * 0.2, 1.4)):
            ring.location = top + Vector((x, 0, -0.6))
            ring.scale = (s, s, s)
            ring.keyframe_insert("location", frame=ff)
            ring.keyframe_insert("scale", frame=ff)
        k.interp("BEZIER")
        k.show(ring, [(f0, f0 + 27)])
    # 5V rail and the pull-up spring
    rail_z = top.z + 2.4
    rail = k.box("D_rail", (3.2, 0.5, 0.25), Vector((c.x, c.y, rail_z)), k.emit("D_railm", (1.0, 0.15, 0.1), 1.4))
    v5 = k.text("D_5v", "5V", 0.5, Vector((c.x - 2.0, c.y - 0.3, rail_z)), [red], extrude=0.02)
    for o in (rail, v5):
        k.show(o, [(RANGES["D"][0], RANGES["D"][1] + 1)])
        k.pop(o, RANGES["D"][0])
    spring = helix("D_spring", Vector((top.x, top.y, top.z)), Vector((top.x, top.y, rail_z - 0.12)))
    k.show(spring, [(RANGES["D"][0] + 10, RANGES["D"][1] + 1)])
    spring.data.bevel_factor_end = 0.0
    spring.data.keyframe_insert("bevel_factor_end", frame=RANGES["D"][0] + 10)
    spring.data.bevel_factor_end = 1.0
    spring.data.keyframe_insert("bevel_factor_end", frame=ATTACH)
    pu = k.text("D_pu", "PULL-UP", 0.42, c + Vector((1.6, -0.4, 4.1)), [grn], extrude=0.02)
    st = k.text("D_st", "STABLE!", 0.36, c + Vector((1.6, -0.4, 3.55)), [grn], extrude=0.02)
    k.show(pu, [(ATTACH, RANGES["D"][1] + 1)])
    k.pop(pu, ATTACH)
    k.show(st, [(ATTACH + 12, RANGES["D"][1] + 1)])
    k.pop(st, ATTACH + 12)

    # ---------------- cameras
    cams = [
        k.camera("cA", [(0, a + Vector((-0.8, -6.6, 3.6)), a + Vector((0.3, 0.3, 1.5))),
                        (119, a + Vector((0.8, -5.4, 3.2)), a + Vector((0.4, 0.3, 1.6)))], lens_keys=[(0, 30)]),
        k.camera("cC", [(RANGES["C"][0], c + Vector((-2.2, -6.2, 3.3)), c + Vector((0, 0, 2.7))),
                        (RANGES["C"][1], c + Vector((1.8, -5.6, 3.1)), c + Vector((0, 0, 2.8)))], lens_keys=[(RANGES["C"][0], 30)]),
        k.camera("cD", [(RANGES["D"][0], c + Vector((1.2, -7.6, 4.4)), c + Vector((0, 0, 3.6))),
                        (RANGES["D"][1], c + Vector((-0.8, -7.0, 4.2)), c + Vector((0, 0, 3.7)))], lens_keys=[(RANGES["D"][0], 28)]),
    ]
    for (_, (f0, _e)), cam in zip(RANGES.items(), cams):
        sc.timeline_markers.new(cam.name, frame=f0).camera = cam
    sc.camera = cams[0]

    def upd(scene, *_):
        f = scene.frame_current
        t = bpy.data.objects["C_val"]
        t.data.body = "01"[(f * 7919 // 3) % 5 > 1]
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", default="ACD")
    ap.add_argument("--step", type=int, default=1)
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(FRAMES, exist_ok=True)
    sc = k.reset()
    sc.frame_end = END
    build(sc)
    k.setup_render(sc, args.preview)
    sc.render.filepath = os.path.join(FRAMES, "")
    for key in args.only:
        a0, a1 = RANGES[key]
        sc.frame_start, sc.frame_end, sc.frame_step = a0, a1 - 1, args.step
        bpy.ops.render.render(animation=True)
