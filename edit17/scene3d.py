#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + HC-SR04 object-detection alarm (Blender, procedural, units = cm).
Re-uses the ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds an HC-SR04 on a purple
acrylic stand facing +x, a red wooden block that slides towards it (timeline.dist()), glowing
ultrasonic ping rings that bounce back as orange echoes, a KY-040 knob that sets the alarm range and
a red ALERT / green CLEAR LED pair + buzzer driven by timeline.alert(). 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, PULSE, knob, dist, alert, busy  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX17 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
S = Vector((-2.4, 9.0, 0))                     # purple sensor stand (pivot)
ANG = math.radians(-35)                        # sensor faces +x turned 35 deg towards the camera
DIR = Vector((math.cos(ANG), math.sin(ANG), 0))
SP = S + Vector((0, 0, 1.95))                  # HC-SR04 pcb centre
FACE = 1.27                                    # can front, along DIR from SP
BLK = (2.0, 3.6, 3.0)                          # red wooden block
RINGS = 4
RY = (0, math.radians(90), 0)
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def build_sensor():
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    gold = bpy.data.materials["gold"]
    def acr(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.22, 0.1, 0.85, 1)
        p.inputs["Roughness"].default_value = 0.2
        p.inputs["Coat Weight"].default_value = 0.6
        return p
    purple = k.node_mat("acrylic", acr)
    before = set(bpy.data.objects)
    k.box("st_base", (3.6, 4.8, 0.3), S + Vector((-0.6, 0, 0.15)), purple)
    k.box("st_plate", (0.3, 3.0, 1.8), S + Vector((-0.75, 0, 1.2)), purple)
    k.box("hc_pcb", (0.15, 4.5, 2.0), SP, k.pbr("hc_m", (0.05, 0.25, 0.65), 0.4))
    k.text("hc_lbl", "HC-SR04", 0.32, SP + Vector((0.09, 0, -0.75)), [k.emit("hc_t", (0.9, 0.92, 0.95), 1.0)], extrude=0.0,
           rot=(math.radians(90), 0, math.radians(90)))
    for sy in (-1.3, 1.3):
        k.cyl("hc_can", 0.8, 1.2, SP + Vector((0.65, sy, 0.15)), steel, rot=RY, verts=40)
        k.cyl("hc_mesh", 0.68, 0.05, SP + Vector((1.27, sy, 0.15)), k.pbr("mesh", (0.03, 0.03, 0.03), 0.8), rot=RY, verts=40)
    k.box("hc_xtal", (0.25, 0.6, 0.3), SP + Vector((0.15, 0, 0.55)), steel)
    for i in range(4):
        k.box("hc_pin", (0.064, 0.064, 0.6), SP + Vector((-0.1, -0.38 + i * 0.254, 1.25)), gold)
    root = bpy.data.objects.new("sensor_root", None)
    bpy.context.collection.objects.link(root)
    root.location = S
    parts = [o for o in bpy.data.objects if o not in before and o is not root]
    for o in parts:
        o.location = o.location - S
        o.parent = root
    root.rotation_euler = (0, 0, ANG)
    bpy.context.view_layer.update()
    for i, col in enumerate(((0.85, 0.1, 0.05), (1.0, 0.8, 0.05), (0.1, 0.6, 0.2), (0.04, 0.04, 0.04))):
        a = world(Vector((-0.1, -0.38 + i * 0.254, 1.5)))
        e = Vector((b10.E.x - 0.7 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_hc{i}", b10.bez(a, a + Vector((-0.4, 0, 1.4)), e + Vector((0, 0.8, 1.8)), e), col, r=0.05)


def world(local):
    """Sensor-local offset (x = facing direction) from SP -> world position."""
    r = Vector((local.x * DIR.x - local.y * DIR.y, local.x * DIR.y + local.y * DIR.x, local.z))
    return SP + r


def gap(f):
    d = dist(f)
    return 0.2 * d + 0.3 + max(0.0, d - 30) * 0.9


def block_c(f):
    c = world(Vector((FACE + gap(f) + BLK[0] / 2, 0, 0)))
    return Vector((c.x, c.y, BLK[2] / 2))


def build_block():
    def wood(nt):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 3.0
        n.inputs["Detail"].default_value = 8.0
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 1.0, 14.0)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.45, 0.02, 0.01, 1)
        ramp.color_ramp.elements[1].color = (0.75, 0.06, 0.03, 1)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = 0.45
        p.inputs["Coat Weight"].default_value = 0.3
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
        return p
    o = k.box("block", BLK, Vector((0, 0, 0)), k.node_mat("wood_red", wood), rot=(0, 0, ANG))   # mesh at origin
    o.modifiers["bev"].width, o.modifiers["bev"].segments = 0.15, 3
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        o.location = block_c(max(f, 0))
        o.keyframe_insert("location", frame=f)
    k.interp("BEZIER")


def build_rings():
    import bmesh
    for j in range(RINGS):
        def b(nt):
            e = nt.nodes.new("ShaderNodeEmission")
            e.name = "E"
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.name = "MIX"
            mx.inputs["Fac"].default_value = 0.0
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(e.outputs[0], mx.inputs[2])
            return mx
        m = k.node_mat(f"ring{j}_m", b)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=32, location=SP)
        o = bpy.context.object
        o.name = f"ring{j}"
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (0.87 < v.co.x < 0.935)], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        bpy.ops.object.shade_smooth()
        o.data.materials.append(m)
        o.visible_shadow = False


def ring_state(f, j):
    """(centre, radius, facing angle, colour, alpha) of wavefront j at frame f, or None."""
    start = f - ((f - j * PULSE) % (RINGS * PULSE))
    age = f - start
    g = gap(f)
    tr = 0.5 * age
    a = max(0.0, 1 - age / (RINGS * PULSE)) * min(1, age / 2)
    if tr <= g:
        if tr > 5.0:
            return None
        return world(Vector((FACE, 0, 0))), max(tr, 0.15), ANG, (0.2, 0.85, 1.0), a
    if tr <= 2 * g:
        return world(Vector((FACE + g, 0, 0))), tr - g, ANG + math.pi, (1.0, 0.55, 0.1), a
    return None


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
        root.location = KNOB + Vector((0, -0.2, 0))
        root.keyframe_insert("rotation_euler", frame=f)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    for name, x, col in (("led_r", 0.6, (1.0, 0.06, 0.03)), ("led_g", 1.6, (0.1, 1.0, 0.2))):
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
            (ENC + Vector((0.4, 1.4, 0)), (0.95, 0.95, 0.95)), (MB + Vector((0.6, 1.3, 0.9)), (0.85, 0.1, 0.05)),
            (MB + Vector((1.6, 1.3, 0.9)), (0.1, 0.7, 0.2)), (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
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
    bpy.data.materials["blue_led"].node_tree.animation_data_clear()   # busy LED is set per frame in upd
    build_sensor()
    build_controls()
    build_block()
    build_rings()

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
    mid = Vector((3.0, -2.0, 1.8))
    mid1 = Vector((0.8, -1.4, 1.8))
    son = world(Vector((1.7, 0, -0.3)))               # sensor + block
    game = Vector((0.8, 0.9, 1.4))                   # OLED + sensor + block + LEDs
    kn = Vector((0.6, -3.6, 1.6))                     # knob + OLED
    cams = [
        cam("s0", [(Sh[0], Vector((2.2, -14, 20)), game), (Sh[1], Vector((1.6, -12.5, 18.5)), game)], 32, game, 5.6),
        cam("s1", [(Sh[1], Vector((0.8, -12, 25)), mid1), (Sh[2], Vector((0.8, -11, 23)), mid1)], 32, mid1, 8.0),
        cam("s2", [(Sh[2], son + Vector((5.0, -10.5, 9.0)), son), (Sh[3], son + Vector((3.4, -9.8, 8.2)), son)], 34, son, 4.0),
        cam("s3", [(Sh[3], kn + Vector((-2.0, -11, 11)), kn), (Sh[4], kn + Vector((-1.0, -10, 10)), kn)], 40, kn, 4.0),
        cam("s4", [(Sh[4], Vector((0.2, -14, 20)), game), (Sh[5], Vector((1.2, -12.5, 18)), game)], 32, game, 5.6),
        cam("s5", [(Sh[5], scr + Vector((-0.3, -11.5, 9.5)), scr + Vector((0, -3.4, -0.6))),
                   (Sh[6], scr + Vector((0.2, -10.5, 8.7)), scr + Vector((0, -3.4, -0.6)))], 40, scr, 4.0),
        cam("s6", [(Sh[6], Vector((-3, -21, 15)), mid), (N, Vector((-4, -23, 16)), mid)], 34, mid, 5.6),
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
        ff = min(max(f, 0), N - 1)                         # per frame (keyframes interpolate in Blender 5)
        h = alert(ff)
        for name, on in (("led_r", h), ("led_g", not h)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        for j in range(RINGS):
            o = bpy.data.objects[f"ring{j}"]
            st = ring_state(ff, j)
            nt = bpy.data.materials[f"ring{j}_m"].node_tree
            if st is None:
                nt.nodes["MIX"].inputs["Fac"].default_value = 0.0
                o.scale = (0.01, 0.01, 0.01)
                continue
            c, r, ang, col, a = st
            o.location = c + Vector((0, 0, 0.15))
            o.rotation_euler = (0, 0, ang)
            o.scale = (r, r, r)
            nt.nodes["E"].inputs["Color"].default_value = (*col, 1)
            nt.nodes["E"].inputs["Strength"].default_value = 6.0
            nt.nodes["MIX"].inputs["Fac"].default_value = 0.9 * a
        bl = bpy.data.materials["blue_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        bl.default_value = 22.0 if busy(ff) else 0.0
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
