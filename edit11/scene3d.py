#!/usr/bin/env python3
"""Photoreal ESP32 + OLED ultrasonic radar (Blender, procedural, units = cm). Re-uses the ESP32 +
1.3" OLED breadboard from edit10 (same channel look), adds an SG90 servo with an HC-SR04 head that
sweeps with timeline.sweep(), a translucent ultrasonic beam (cyan, red while alarm), a mini
breadboard with green/red LEDs + buzzer, and an orange 'intruder' cube that slides in and out.
The OLED shows the radar scope from edit11/make_screens.py. 24 fps, 384 frames.
Run: python3 edit11/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, BOOT, OBJ_ANGLE, OBJ_DIST, sweep, alarm, presence  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
S = Vector((7.6, -1.2, 0))                     # servo base
PIV = S + Vector((0, 0, 2.5))                  # servo output shaft
R90 = (math.radians(90), 0, 0)


def heading_dir(a):
    t = math.radians(a)
    return Vector((math.cos(t), -math.sin(t), 0))


CUBE = S + heading_dir(OBJ_ANGLE) * OBJ_DIST + Vector((0, 0, 1.75))


def emit_alpha(name, col, strength, alpha):
    def b(nt):
        e = nt.nodes.new("ShaderNodeEmission")
        e.name = "em"
        e.inputs["Color"].default_value = (*col, 1)
        e.inputs["Strength"].default_value = strength
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = alpha
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(e.outputs[0], mx.inputs[2])
        return mx
    return k.node_mat(name, b)


def build_radar():
    def sb(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.0, 0.07, 0.55, 1)
        p.inputs["Roughness"].default_value = 0.25
        p.inputs["Coat Weight"].default_value = 0.4
        return p
    body = k.node_mat("servo_body", sb)
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    gold = bpy.data.materials["gold"]
    k.box("sv_body", (2.3, 1.2, 2.25), S + Vector((0, 0, 1.12)), body)
    k.box("sv_tabs", (3.2, 1.2, 0.25), S + Vector((0, 0, 1.75)), body)
    k.cyl("sv_top", 0.6, 0.35, S + Vector((0, 0, 2.3)), body, verts=32)
    k.text("sv_lbl", "SG90", 0.4, S + Vector((0, -0.62, 0.9)), [k.emit("sv_t", (0.9, 0.9, 0.95), 1.0)], extrude=0.0)
    before = set(bpy.data.objects)
    k.cyl("horn_hub", 0.35, 0.3, PIV + Vector((0, 0, 0.05)), k.pbr("horn", (0.95, 0.95, 0.93), 0.35), verts=24)
    k.box("bracket", (4.8, 0.25, 0.3), PIV + Vector((0, 0, 0.3)), blk)
    k.box("bracket_up", (4.8, 0.25, 2.4), PIV + Vector((0, 0.2, 1.5)), blk)
    hc = PIV + Vector((0, -0.05, 1.55))
    k.box("hc_pcb", (4.5, 0.15, 2.0), hc, k.pbr("hc_m", (0.05, 0.25, 0.65), 0.4))
    k.text("hc_lbl", "HC-SR04", 0.32, hc + Vector((0, -0.09, -0.75)), [k.emit("hc_t", (0.9, 0.92, 0.95), 1.0)], extrude=0.0)
    for sx in (-1.3, 1.3):
        k.cyl("hc_can", 0.8, 1.2, hc + Vector((sx, -0.65, 0.15)), steel, rot=R90, verts=40)
        k.cyl("hc_mesh", 0.68, 0.05, hc + Vector((sx, -1.27, 0.15)), k.pbr("mesh", (0.03, 0.03, 0.03), 0.8), rot=R90, verts=40)
    k.box("hc_xtal", (0.6, 0.25, 0.3), hc + Vector((0, -0.15, 0.55)), steel)
    for i in range(4):
        k.box("hc_pin", (0.064, 0.064, 0.6), hc + Vector((-0.38 + i * 0.254, 0, 1.25)), gold)
    beam = emit_alpha("beam_m", (0.2, 0.9, 1.0), 1.6, 0.09)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.6, radius2=4.2, depth=16, location=hc + Vector((0, -1.3 - 8, 0.15)),
                                    rotation=R90)
    cone = bpy.context.object
    cone.name = "beam"
    cone.data.materials.append(beam)
    cone.visible_shadow = False
    head_parts = [o for o in bpy.data.objects if o not in before]
    head = bpy.data.objects.new("radar_head", None)
    bpy.context.collection.objects.link(head)
    head.location = PIV
    bpy.context.view_layer.update()
    for o in head_parts:
        o.parent = head
        o.matrix_parent_inverse = head.matrix_world.inverted()
    # sensor wires ride with the head down to the shaft, then a static bundle runs to the ESP32
    for i, col in enumerate(((0.85, 0.1, 0.05), (1.0, 0.8, 0.05), (0.1, 0.6, 0.2), (0.04, 0.04, 0.04))):
        top = hc + Vector((-0.38 + i * 0.254, 0, 1.5))
        w = b10.poly_wire(f"w_hc{i}", b10.bez(top, top + Vector((0, 0.8, 0.4)), PIV + Vector((0.2 * i - 0.3, 1.2, 0.8)),
                                                PIV + Vector((0.2 * i - 0.3, 0.9, 0.2)), 24), col, r=0.05)
        w.parent = head
        w.matrix_parent_inverse = head.matrix_world.inverted()
        a = PIV + Vector((0.2 * i - 0.3, 0.9, 0.2))
        e = Vector((b10.E.x + 1.0 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_hcb{i}", b10.bez(a, a + Vector((-1.0, -4.0, -2.0)), e + Vector((0.5, -4.5, -0.6)), e), col, r=0.05)
    for i, col in enumerate(((0.35, 0.18, 0.08), (0.85, 0.1, 0.05), (0.98, 0.55, 0.05))):     # servo leads
        a = S + Vector((-1.15, 0.2 - i * 0.2, 0.4))
        e = Vector((b10.E.x + 2.2 + i * 0.254, -1.27 - 0.254 * 3, b10.TOP))
        b10.poly_wire(f"w_sv{i}", b10.bez(a, a + Vector((-2, -3.5, -0.3)), e + Vector((0.5, -4.0, -0.6)), e), col, r=0.05)
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        head.rotation_euler = (0, 0, math.radians(90 - sweep(max(f, 0))))
        head.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    em = beam.node_tree.nodes["em"].inputs["Color"]
    b10.key_bool(em, "default_value", alarm, (1.0, 0.12, 0.08, 1), (0.2, 0.9, 1.0, 1))
    k.show(cone, [(BOOT, N + 1)])


def build_alarm_board():
    L0 = Vector((-4.3, -6.6, 0))
    k.box("mini_bb", (4.6, 3.4, 0.9), L0 + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (4.6, 3.4), L0 + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    leds = []
    for name, x, col, states in (("led_g", -1.2, (0.1, 1.0, 0.2), lambda f: f >= BOOT and not alarm(f)),
                                 ("led_r", -0.3, (1.0, 0.06, 0.03), lambda f: alarm(f) and (f // 3) % 2 == 0)):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.inputs["Base Color"].default_value = (*[0.08 + 0.8 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.6
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        c = L0 + Vector((x, 0.3, 0.9))
        k.cyl(name + "_body", 0.25, 0.45, c + Vector((0, 0, 0.85)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=c + Vector((0, 0, 1.08)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        k.cyl(name + "_rim", 0.29, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), bpy.data.materials["steel"])
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.6)))
        g = bpy.context.object
        g.data.color = col
        g.data.shadow_soft_size = 0.2
        b10.key_bool(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", states, 4.0)
        b10.key_bool(g.data, "energy", states, 3.0)
        leds.append(c)
    k.cyl("buzzer", 0.62, 0.95, L0 + Vector((1.2, 0.2, 1.38)), bpy.data.materials["esp_blk"], verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, L0 + Vector((1.2, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    for i, (c, col) in enumerate(((leds[0], (0.1, 0.7, 0.2)), (leds[1], (0.85, 0.1, 0.05)), (L0 + Vector((1.2, 0.9, 0.9)), (0.95, 0.95, 0.95)))):
        a = c + Vector((0, 1.0, 0))
        e = Vector((b10.E.x - 1.2 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_al{i}", b10.bez(a, a + Vector((0, 0.4, 1.6)), e + Vector((0, -1.0, 1.6)), e), col, r=0.05)


def build_cube():
    bpy.ops.mesh.primitive_cube_add(size=3.5, location=CUBE)
    cube = bpy.context.object
    cube.name = "intruder"
    bev = cube.modifiers.new("bev", "BEVEL")
    bev.width = 0.35
    bev.segments = 4
    bpy.ops.object.shade_smooth()
    cube.data.materials.append(k.pbr("cube_m", (1.0, 0.35, 0.06), rough=0.45))
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        p = presence(max(f, 0))
        cube.location = CUBE + Vector((14, -4, 0)) * (1 - p)
        cube.rotation_euler = (0, 0, math.radians(30 * (1 - p)))
        cube.keyframe_insert("location", frame=f)
        cube.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    vis, on = [], None
    for f in range(N + 1):
        v = presence(f) > 0.01
        if v and on is None:
            on = f
        if not v and on is not None:
            vis.append((on, f))
            on = None
    if on is not None:
        vis.append((on, N + 1))
    k.show(cube, vis)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (2, -4, 1), 70000, 35)
    k.area("fill", (45, -35, 40), (2, -4, 1), 22000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (2, 0, 2), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    build_radar()
    build_alarm_board()
    build_cube()

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
    head = PIV + Vector((0, -0.4, 1.6))
    mid = Vector((2.0, -5.0, 1.0))
    cams = [
        cam("s0", [(Sh[0], Vector((-7, -26, 10)), Vector((3, -5, 2))), (Sh[1], Vector((-5, -23, 9)), Vector((3, -5, 2)))], 35, CUBE, 5.6),
        cam("s1", [(Sh[1], Vector((1.5, -22, 34)), Vector((1.5, -5, 0))), (Sh[2], Vector((1.5, -19, 30)), Vector((1.5, -5, 0)))], 30, mid, 8.0),
        cam("s2", [(Sh[2], head + Vector((9, -13, 4)), head), (Sh[3], head + Vector((-4, -14, 4)), head)], 40, head, 2.8),
        cam("s3", [(Sh[3], scr + Vector((0.0, -5.6, 5.8)), scr), (Sh[4], scr + Vector((0.4, -5.0, 5.2)), scr)], 50, scr, 2.8),
        cam("s4", [(Sh[4], Vector((11, -27, 11)), Vector((3, -6, 2))), (Sh[5], Vector((8, -24, 9.5)), Vector((3, -6, 2)))], 35, CUBE, 5.6),
        cam("s5", [(Sh[5], Vector((-11, -22, 20)), mid), (Sh[6], Vector((11, -24, 20)), mid)], 32, mid, 8.0),
        cam("s6", [(Sh[6], Vector((-2, -21, 16)), mid), (N, Vector((-2.5, -24, 18)), mid)], 32, mid, 8.0),
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
