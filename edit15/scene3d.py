#!/usr/bin/env python3
"""Photoreal ESP32 + OLED Rock-Paper-Scissors robot (Blender, procedural, units = cm). Re-uses the
ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds an SG90 servo carrying a white box
with ROCK / PAPER / SCISSORS faces (servo angle = timeline.servo()), a KY-040 knob the player turns to
pick (timeline.knob(), dips when pressed), and a green / red result LED pair + buzzer. The OLED shows
edit15/make_screens.py. 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, knob, pressed, servo, led  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX15 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
SV = Vector((8.6, 0.6, 0))                     # servo base centre
BOXC = SV + Vector((0, 0, 4.6))                # box centre
BOX = 3.4
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def face_mat(name):
    def b(nt):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX15, f"face_{name}.png"))
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = 0.45
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        return p
    return k.node_mat(f"face_{name}_m", b)


def build_robot():
    def sb(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.0, 0.07, 0.55, 1)
        p.inputs["Roughness"].default_value = 0.25
        p.inputs["Coat Weight"].default_value = 0.4
        return p
    body = k.node_mat("servo_body", sb)
    k.box("stand", (4.0, 4.0, 0.6), SV + Vector((0, 0, 0.3)), k.pbr("stand_m", (0.12, 0.55, 0.2), 0.5))
    k.box("sv_body", (1.2, 2.3, 2.25), SV + Vector((0, 0, 1.72)), body)
    k.box("sv_tabs", (1.2, 3.2, 0.25), SV + Vector((0, 0, 2.35)), body)
    k.cyl("sv_top", 0.6, 0.35, SV + Vector((0, 0, 2.95)), body, verts=32)
    k.text("sv_lbl", "SG90", 0.38, SV + Vector((-0.61, 0, 1.6)), [k.emit("sv_t", (0.9, 0.9, 0.95), 1.0)], extrude=0.0,
           rot=(math.radians(90), 0, math.radians(-90)))
    root = bpy.data.objects.new("box_root", None)
    bpy.context.collection.objects.link(root)
    root.location = BOXC
    before = set(bpy.data.objects)
    k.box("rps_box", (BOX, BOX, BOX * 1.25), Vector((0, 0, 0)), k.pbr("box_white", (0.95, 0.95, 0.93), 0.5))
    h = BOX * 1.25
    faces = (("rock", Vector((0, -BOX / 2 - 0.005, 0)), (math.radians(90), 0, 0)),
             ("paper", Vector((BOX / 2 + 0.005, 0, 0)), (math.radians(90), 0, math.radians(90))),
             ("scissors", Vector((-BOX / 2 - 0.005, 0, 0)), (math.radians(90), 0, math.radians(-90))))
    for name, loc, rot in faces:
        b10.plane(f"face_{name}", (BOX * 0.92, h * 0.92), loc, face_mat(name), rot=rot)
    k.cyl("horn", 0.9, 0.12, Vector((0, 0, -h / 2 - 0.1)), k.pbr("horn_m", (0.95, 0.95, 0.93), 0.35), verts=32)
    parts = [o for o in bpy.data.objects if o not in before]
    for o in parts:
        o.location = o.location + BOXC
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        root.rotation_euler = (0, 0, math.radians(servo(max(f, 0))))
        root.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    for i, col in enumerate(((0.35, 0.18, 0.08), (0.85, 0.1, 0.05), (0.98, 0.55, 0.05))):
        a = SV + Vector((0.65, -0.2 + i * 0.2, 1.0))
        e = Vector((b10.E.x + 2.6 + i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_sv{i}", b10.bez(a, a + Vector((-1.5, 0, -0.3)), e + Vector((1.5, 2.0, 1.2)), e), col, r=0.05)


def build_controls():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    k.box("ky_pcb", (2.0, 2.6, 0.12), ENC + Vector((0, 0, 0.5)), k.pbr("ky_pcb_m", (0.02, 0.02, 0.025), 0.4))
    k.box("ky_body", (1.25, 1.25, 0.65), ENC + Vector((0, -0.2, 0.9)), steel)
    k.cyl("ky_bush", 0.45, 0.35, ENC + Vector((0, -0.2, 1.4)), steel, verts=32)
    root = bpy.data.objects.new("knob_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)
    k.cyl("knob", 0.85, 1.3, Vector((0, 0, 0)), k.pbr("knob_m", (0.04, 0.04, 0.045), 0.45), verts=48)
    for j in range(24):
        a = j * 2 * math.pi / 24
        k.box("rib", (0.08, 0.12, 1.2), Vector((0.86 * math.cos(a), 0.86 * math.sin(a), 0)), blk, rot=(0, 0, a))
    k.cyl("knob_cap", 0.72, 0.04, Vector((0, 0, 0.66)), k.pbr("cap_m", (0.75, 0.76, 0.78), 0.25, 1.0), verts=48)
    k.box("knob_mark", (0.14, 0.55, 0.02), Vector((0, 0.42, 0.69)), k.emit("mark_m", (1.0, 1.0, 1.0), 1.2))
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        ff = max(f, 0)
        root.rotation_euler = (0, 0, math.radians(-knob(ff)))
        root.location = KNOB + Vector((0, -0.2, -0.25 if pressed(ff) else 0.0))
        root.keyframe_insert("rotation_euler", frame=f)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    for name, x, col in (("led_g", 0.6, (0.1, 1.0, 0.2)), ("led_r", 1.6, (1.0, 0.06, 0.03))):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.name = "P"
            p.inputs["Base Color"].default_value = (*[0.02 + 0.2 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.35
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        c = MB + Vector((x, 0.3, 0.9))
        k.cyl(name + "_rim", 0.33, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        k.cyl(name + "_body", 0.29, 0.5, c + Vector((0, 0, 0.88)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.29, location=c + Vector((0, 0, 1.13)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), steel)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.7)))
        g = bpy.context.object
        g.name = name + "_glow"
        g.data.color = col
        g.data.shadow_soft_size = 0.2
        g.data.energy = 0.0
    k.cyl("buzzer", 0.62, 0.95, MB + Vector((3.0, 0.2, 1.38)), blk, verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, MB + Vector((3.0, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    ends = [(ENC + Vector((-0.4, 1.4, 0)), (1.0, 0.8, 0.05)), (ENC + Vector((0, 1.4, 0)), (0.1, 0.35, 0.95)),
            (ENC + Vector((0.4, 1.4, 0)), (0.95, 0.95, 0.95)), (MB + Vector((0.6, 1.3, 0.9)), (0.1, 0.7, 0.2)),
            (MB + Vector((1.6, 1.3, 0.9)), (0.85, 0.1, 0.05)), (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
    for i, (a, col) in enumerate(ends):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (3, -2, 2), 60000, 35)
    k.area("fill", (45, -35, 40), (3, -2, 2), 20000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (3, 0, 3), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    build_robot()
    build_controls()

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
    mid = Vector((3.2, -2.0, 1.8))
    game = Vector((5.2, -1.2, 2.6))                   # OLED + box together
    cams = [
        cam("s0", [(Sh[0], BOXC + Vector((-1.5, -12, 1.5)), BOXC + Vector((0, 0, -0.4))),
                   (Sh[1], BOXC + Vector((-0.8, -10.5, 1.2)), BOXC + Vector((0, 0, -0.4)))], 45, BOXC, 2.8),
        cam("s1", [(Sh[1], Vector((3.2, -12, 25)), mid), (Sh[2], Vector((3.2, -11, 23)), mid)], 32, mid, 8.0),
        cam("s2", [(Sh[2], Vector((1.0, -20, 9)), game), (Sh[3], Vector((2.5, -19, 8.5)), game)], 36, game, 5.6),
        cam("s3", [(Sh[3], Vector((10, -19, 8)), game), (Sh[4], Vector((8.5, -18, 7.5)), game)], 36, game, 5.6),
        cam("s4", [(Sh[4], scr + Vector((-0.3, -5.8, 6.0)), scr), (Sh[5], scr + Vector((0.2, -5.2, 5.4)), scr)], 50, scr, 2.8),
        cam("s5", [(Sh[5], Vector((-1.0, -20, 10)), game), (Sh[6], Vector((0.5, -18.5, 9)), game)], 36, game, 5.6),
        cam("s6", [(Sh[6], Vector((-4, -21, 15)), mid), (N, Vector((-5, -23, 16)), mid)], 34, mid, 5.6),
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
        state = led(min(max(f, 0), N - 1))                 # per frame (keyframes interpolate in Blender 5)
        for name, on in (("led_g", state == "green"), ("led_r", state == "red")):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
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
