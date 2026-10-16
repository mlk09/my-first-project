#!/usr/bin/env python3
"""Photoreal ESP32 + OLED rotary-encoder LED flow (Blender, procedural, units = cm). Re-uses the
ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds a mini breadboard with a KY-040
rotary encoder (knurled knob) and a row of 8 rainbow 5 mm LEDs whose brightness follows
timeline.leds(). The knob turns with timeline.knob() (a rotation arrow is drawn in the edit) and dips at
timeline.PRESS. The OLED shows edit14/make_screens.py. 24 fps, 468 frames.
Run: python3 edit14/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, NLED, knob, leds, pressed  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
MB = Vector((0.5, -6.6, 0))                    # mini breadboard centre
ENC = MB + Vector((-3.6, 0, 0.9))              # encoder pcb base
KNOB = ENC + Vector((0, 0, 2.3))               # knob centre
R90 = (math.radians(90), 0, 0)
RAINBOW = [(1.0, 0.05, 0.03), (1.0, 0.35, 0.02), (1.0, 0.8, 0.02), (0.2, 1.0, 0.1),
           (0.05, 0.9, 0.7), (0.05, 0.35, 1.0), (0.4, 0.1, 1.0), (1.0, 0.1, 0.6)]


def led_x(i):
    return MB.x - 1.2 + i * 0.9


def build_side():
    k.box("mini_bb", (11.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (11.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    # KY-040: black pcb, metal body, knurled knob on a shaft
    k.box("ky_pcb", (2.0, 2.6, 0.12), ENC + Vector((0, 0, 0.5)), k.pbr("ky_pcb_m", (0.02, 0.02, 0.025), 0.4))
    for i in range(5):
        k.box("ky_pin", (0.064, 0.064, 0.55), ENC + Vector((-0.5 + i * 0.254, 1.2, 0.25)), bpy.data.materials["gold"])
    k.box("ky_body", (1.25, 1.25, 0.65), ENC + Vector((0, -0.2, 0.9)), steel)
    k.cyl("ky_bush", 0.45, 0.35, ENC + Vector((0, -0.2, 1.4)), steel, verts=32)
    k.text("ky_lbl", "KY-040", 0.22, ENC + Vector((0, 0.95, 0.57)), [k.emit("ky_t", (0.9, 0.9, 0.9), 0.9)], extrude=0.0)
    knob_root = bpy.data.objects.new("knob_root", None)
    bpy.context.collection.objects.link(knob_root)
    knob_root.location = KNOB + Vector((0, -0.2, 0))
    before = set(bpy.data.objects)
    kc = Vector((0, 0, 0))
    k.cyl("knob", 0.85, 1.3, kc, k.pbr("knob_m", (0.04, 0.04, 0.045), 0.45), verts=48)
    for j in range(24):                                    # knurl ribs
        a = j * 2 * math.pi / 24
        k.box("rib", (0.08, 0.12, 1.2), kc + Vector((0.86 * math.cos(a), 0.86 * math.sin(a), 0)), blk,
              rot=(0, 0, a))
    k.cyl("knob_cap", 0.72, 0.04, kc + Vector((0, 0, 0.66)), k.pbr("cap_m", (0.75, 0.76, 0.78), 0.25, 1.0), verts=48)
    k.box("knob_mark", (0.14, 0.55, 0.02), kc + Vector((0, 0.42, 0.69)), k.emit("mark_m", (1.0, 1.0, 1.0), 1.2))
    parts = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = knob_root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        ff = max(f, 0)
        knob_root.rotation_euler = (0, 0, math.radians(-knob(ff)))
        knob_root.location = KNOB + Vector((0, -0.2, -0.25 if pressed(ff) else 0.0))
        knob_root.keyframe_insert("rotation_euler", frame=f)
        knob_root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    # 8 rainbow LEDs
    for i in range(NLED):
        col = RAINBOW[i]

        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.name = "P"
            p.inputs["Base Color"].default_value = (*[0.02 + 0.16 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.35
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(f"led{i}", b)
        c = Vector((led_x(i), MB.y + 0.3, 0.9))
        k.cyl(f"led{i}_rim", 0.29, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        k.cyl(f"led{i}_body", 0.25, 0.45, c + Vector((0, 0, 0.85)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=c + Vector((0, 0, 1.08)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), steel)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.6)))
        g = bpy.context.object
        g.data.color = col
        g.data.shadow_soft_size = 0.2
        g.name = f"led{i}_glow"
        g.data.energy = 0.0
        k.box("res", (0.18, 0.7, 0.18), c + Vector((0, -1.0, 0.1)), k.pbr("res_m", (0.78, 0.66, 0.48), 0.5))
    # jumpers: 8 LED lines + 3 encoder lines to the ESP32
    for i in range(NLED + 3):
        if i < NLED:
            a = Vector((led_x(i), MB.y + 1.3, 0.9))
            col = RAINBOW[i]
        else:
            a = ENC + Vector((-0.5 + (i - NLED) * 0.254, 1.5, 0))
            col = ((1.0, 0.8, 0.05), (0.1, 0.35, 0.95), (0.95, 0.95, 0.95))[i - NLED]
        e = Vector((b10.E.x - 1.8 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6 + 0.05 * i)), e + Vector((0, -1.2, 1.6 + 0.05 * i)), e),
                      tuple(0.3 + 0.6 * c for c in col), r=0.05)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (0, -3, 1), 55000, 35)
    k.area("fill", (45, -35, 40), (0, -3, 1), 17000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (0, 0, 2), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    build_side()

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
    mid = Vector((0.3, -3.0, 1.0))
    row = Vector((MB.x - 0.5, MB.y, 1.6))
    cams = [
        cam("s0", [(Sh[0], Vector((1, -24, 12)), mid + Vector((0, -2.0, 0))), (Sh[1], Vector((1.5, -22, 11)), mid + Vector((0, -2.0, 0)))], 36, row, 4.0),
        cam("s1", [(Sh[1], Vector((0.3, -10.5, 23)), mid), (Sh[2], Vector((0.3, -9.5, 21)), mid)], 32, mid, 8.0),
        cam("s2", [(Sh[2], KNOB + Vector((5, -8, 3)), KNOB + Vector((0, 0, -1))), (Sh[3], KNOB + Vector((-3, -8.5, 3.2)), KNOB + Vector((0, 0, -1)))], 42, KNOB, 2.8),
        cam("s3", [(Sh[3], Vector((7, -19, 9)), row), (Sh[4], Vector((4, -17, 8)), row)], 36, row, 4.0),
        cam("s4", [(Sh[4], Vector((-7, -18, 9)), row), (Sh[5], Vector((-4, -17, 8)), row)], 36, row, 4.0),
        cam("s5", [(Sh[5], scr + Vector((0.0, -5.4, 5.6)), scr), (Sh[5] + 30, scr + Vector((0.2, -5.0, 5.2)), scr),
                   (Sh[5] + 31, Vector((0, -17, 13)), mid), (Sh[6], Vector((0, -15.5, 12)), mid)], 40, mid, 5.6),
        cam("s6", [(Sh[6], Vector((-6, -18, 14)), mid), (N, Vector((-7, -20, 15)), mid)], 34, mid, 5.6),
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
        lv = leds(min(max(f, 0), N - 1))                     # set per frame (keyframes interpolated in Blender 5)
        for i in range(NLED):
            bpy.data.materials[f"led{i}"].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 * lv[i]
            bpy.data.objects[f"led{i}_glow"].data.energy = 4.0 * lv[i]
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
