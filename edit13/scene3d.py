#!/usr/bin/env python3
"""Photoreal ESP32 + OLED robot eyes (Blender, procedural, units = cm). Re-uses the ESP32 + 1.3"
OLED breadboard from edit10 (same channel look); adds a red TTP223 touch-sensor module, a diffused
RGB LED whose colour follows timeline.led() and a buzzer on a mini breadboard, and a finger that taps
the touch pad at timeline.TAPS. The OLED shows the eyes from edit13/make_screens.py. 24 fps, 468 frames.
Run: python3 edit13/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, finger, led  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
MB = Vector((1.0, -6.2, 0))                    # mini breadboard centre
PAD = MB + Vector((-1.4, 0, 1.05))             # TTP223 touch pad centre
R90 = (math.radians(90), 0, 0)


def build_side():
    k.box("mini_bb", (6.4, 3.4, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (6.4, 3.4), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    # TTP223 module: red pcb with a round copper pad
    k.box("ttp_pcb", (2.4, 2.4, 0.12), PAD + Vector((0, 0, -0.06)), k.pbr("ttp_red", (0.7, 0.04, 0.03), 0.35))
    k.cyl("ttp_pad", 0.85, 0.02, PAD + Vector((0, 0, 0.01)), k.pbr("ttp_cu", (0.95, 0.65, 0.35), 0.25, 1.0), verts=48)
    k.box("ttp_chip", (0.35, 0.25, 0.08), PAD + Vector((0.8, -0.85, 0.04)), bpy.data.materials["esp_blk"])
    k.text("ttp_lbl", "TOUCH", 0.22, PAD + Vector((0, -1.0, 0.012)), [k.emit("ttp_t", (0.95, 0.95, 0.95), 0.9)], extrude=0.0)
    # RGB LED (diffused) whose colour is keyed every frame
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
        p.inputs["Roughness"].default_value = 0.35
        p.inputs["Transmission Weight"].default_value = 0.4
        return p
    m = k.node_mat("rgb_led", b)
    c = MB + Vector((1.2, 0.2, 0.9))
    k.cyl("rgb_body", 0.32, 0.55, c + Vector((0, 0, 0.9)), m, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32, location=c + Vector((0, 0, 1.17)), segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(m)
    for dx in (-0.19, -0.06, 0.06, 0.19):
        k.box("rgb_leg", (0.04, 0.04, 0.65), c + Vector((dx, 0, 0.33)), bpy.data.materials["steel"])
    bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.4, 1.8)))
    g = bpy.context.object
    g.data.shadow_soft_size = 0.25
    p = m.node_tree.nodes["P"]
    k.interp("CONSTANT")
    for f in range(-1, N + 1):
        r, gg, bb, s = led(max(f, 0))
        p.inputs["Emission Color"].default_value = (r, gg, bb, 1)
        p.inputs["Emission Strength"].default_value = s * 2.2
        p.inputs["Base Color"].default_value = (0.2 + 0.8 * r, 0.2 + 0.8 * gg, 0.2 + 0.8 * bb, 1) if s else (0.9, 0.9, 0.9, 1)
        p.inputs["Base Color"].keyframe_insert("default_value", frame=f)
        p.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
        p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        g.data.color = (r, gg, bb) if s else (1, 1, 1)
        g.data.energy = 1.2 * s
        g.data.keyframe_insert("color", frame=f)
        g.data.keyframe_insert("energy", frame=f)
    k.interp("BEZIER")
    k.cyl("buzzer", 0.62, 0.95, MB + Vector((2.6, 0.2, 1.38)), bpy.data.materials["esp_blk"], verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, MB + Vector((2.6, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    ends = [(PAD + Vector((-0.6, 1.2, -0.1)), (1.0, 0.8, 0.05)), (PAD + Vector((0, 1.2, -0.1)), (0.85, 0.1, 0.05)),
            (PAD + Vector((0.6, 1.2, -0.1)), (0.04, 0.04, 0.04)), (c + Vector((0, 0.6, 0)), (0.1, 0.6, 0.2)),
            (c + Vector((0.2, 0.6, 0)), (0.15, 0.35, 0.95)), (MB + Vector((2.6, 0.9, 0.9)), (0.95, 0.95, 0.95))]
    for i, (a, col) in enumerate(ends):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.8, 1.8)), e + Vector((0, -1.4, 1.8)), e), col, r=0.05)


def build_finger():
    skin = k.pbr("skin", (0.78, 0.52, 0.4), rough=0.5)
    nail = k.pbr("nail", (0.92, 0.75, 0.7), rough=0.25)
    root = bpy.data.objects.new("finger_root", None)
    bpy.context.collection.objects.link(root)
    parts = []
    tip = Vector((0, 0, 0.75))
    parts.append(k.cyl("finger", 0.75, 9.0, tip + Vector((0, -4.3, 2.2)), skin, rot=(math.radians(62), 0, 0), verts=32))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, location=tip, segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    s = bpy.context.object
    s.data.materials.append(skin)
    parts.append(s)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=tip + Vector((0, -0.25, 0.55)), segments=24, ring_count=12)
    nl = bpy.context.object
    nl.scale = (1, 1.3, 0.25)
    nl.rotation_euler = (math.radians(-28), 0, 0)
    nl.data.materials.append(nail)
    parts.append(nl)
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        u = finger(max(f, 0))
        root.location = PAD + Vector((0, -0.2, -0.6)) + Vector((0, -5.0, 7.0)) * (1 - u)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    vis = [(SHOTS[3] - 4, SHOTS[5])]
    for o in parts:
        k.show(o, vis)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (0, -3, 1), 65000, 35)
    k.area("fill", (45, -35, 40), (0, -3, 1), 20000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (0, 0, 2), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    build_side()
    build_finger()

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        c.data.clip_start = 0.1
        c.data.clip_end = 2000
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    Sh = SHOTS
    scr = b10.M + Vector((0, -0.25, 0.23))
    mid = Vector((0.5, -2.8, 1.0))
    both = (scr + PAD) / 2
    cams = [
        cam("s0", [(Sh[0], scr + Vector((0.0, -4.6, 4.8)), scr), (Sh[1], scr + Vector((0.3, -4.0, 4.2)), scr)], 50, scr, 2.8),
        cam("s1", [(Sh[1], Vector((0.5, -9.5, 22)), mid), (Sh[2], Vector((0.5, -8.5, 20)), mid)], 32, mid, 8.0),
        cam("s2", [(Sh[2], scr + Vector((-0.4, -5.2, 5.4)), scr), (Sh[3], scr + Vector((0.4, -4.8, 5.0)), scr)], 50, scr, 2.8),
        cam("s3", [(Sh[3], Vector((-4, -19, 10)), both), (Sh[4], Vector((-2, -17, 9)), both)], 36, both, 4.0),
        cam("s4", [(Sh[4], Vector((5, -18, 10)), both), (Sh[5], Vector((3, -16, 9)), both)], 36, both, 4.0),
        cam("s5", [(Sh[5], scr + Vector((0.2, -5.0, 5.4)), scr), (Sh[6], scr + Vector((0.1, -4.2, 4.6)), scr)], 50, scr, 2.8),
        cam("s6", [(Sh[6], Vector((-6, -16, 13)), mid), (N, Vector((-7, -18, 14)), mid)], 34, mid, 5.6),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        f = scene.frame_current
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(OLED, f"{min(max(f, 0), N - 1):04d}.png"), check_existing=True)
        bpy.data.materials["oled_scr"].node_tree.nodes["oled_tex"].image = imgs[f]
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=N - 1)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=FRAMES)
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(args.out, exist_ok=True)
    sc = k.reset()
    sc.render.fps = FPS
    build(sc)
    k.setup_render(sc, args.preview)
    sc.render.use_persistent_data = False
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 8, 6, 3
    cy.samples = 8 if args.preview else 14
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
