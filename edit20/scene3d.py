#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + PIR (HC-SR501) motion alarm (Blender, procedural, units = cm). Re-uses the
ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds an HC-SR501 with its white fresnel
dome on a purple acrylic stand, a glowing detection fan on the mat (grey DISARMED / cyan ARMED / red
ALARM), a little toy 'chor' with a money bag that walks into it (timeline.thief()), a KY-040 knob that
arms the system and a red ALARM / green SAFE LED pair + buzzer. 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, ZONE, HALF, knob, thief, armed, alarm, detecting, busy  # noqa: E402
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
SP = S + Vector((0, 0, 2.2))                   # HC-SR501 pcb centre
FACE = 1.4                                     # dome front, along DIR from SP
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
    k.box("pir_pcb", (0.15, 3.3, 2.5), SP, k.pbr("pir_m", (0.04, 0.35, 0.12), 0.4))
    k.box("pir_base", (0.35, 2.3, 2.3), SP + Vector((0.22, 0, 0.1)), k.pbr("pir_white", (0.92, 0.92, 0.9), 0.5))

    def dome(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Base Color"].default_value = (0.95, 0.95, 0.93, 1)
        p.inputs["Roughness"].default_value = 0.35
        p.inputs["Subsurface Weight"].default_value = 0.3
        p.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        return p
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.95, location=SP + Vector((0.4, 0, 0.1)), segments=48, ring_count=24)
    o = bpy.context.object
    o.name = "pir_dome"
    o.scale = (0.85, 1, 1)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(k.node_mat("pir_dome_m", dome))
    tex = o.modifiers.new("facets", "DISPLACE")                     # fresnel-lens facets
    tx = bpy.data.textures.new("facet_tex", "VORONOI")
    tx.noise_scale = 0.22
    tex.texture = tx
    tex.strength = 0.03
    k.text("pir_lbl", "HC-SR501", 0.26, SP + Vector((0.09, 0, -1.08)), [k.emit("pir_t", (0.9, 0.92, 0.95), 1.0)], extrude=0.0,
           rot=(math.radians(90), 0, math.radians(90)))
    for sy in (-1.1, 1.1):                                          # sensitivity / delay pots
        k.cyl("pir_pot", 0.22, 0.2, SP + Vector((-0.17, sy, -0.75)), k.pbr("pot_m", (0.95, 0.6, 0.1), 0.4), rot=RY, verts=24)
    for i in range(3):
        k.box("hc_pin", (0.064, 0.064, 0.6), SP + Vector((-0.1, -0.254 + i * 0.254, 1.5)), gold)
    root = bpy.data.objects.new("sensor_root", None)
    bpy.context.collection.objects.link(root)
    root.location = S
    parts = [o for o in bpy.data.objects if o not in before and o is not root]
    for o in parts:
        o.location = o.location - S
        o.parent = root
    root.rotation_euler = (0, 0, ANG)
    bpy.context.view_layer.update()
    for i, col in enumerate(((0.85, 0.1, 0.05), (1.0, 0.8, 0.05), (0.04, 0.04, 0.04))):
        a = world(Vector((-0.1, -0.254 + i * 0.254, 1.75)))
        e = Vector((b10.E.x - 0.7 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_hc{i}", b10.bez(a, a + Vector((-0.4, 0, 1.4)), e + Vector((0, 0.8, 1.8)), e), col, r=0.05)


def world(local):
    """Sensor-local offset (x = facing direction) from SP -> world position."""
    r = Vector((local.x * DIR.x - local.y * DIR.y, local.x * DIR.y + local.y * DIR.x, local.z))
    return SP + r


def thief_pos(f):
    u, v, walking = thief(f)
    c = world(Vector((FACE + u, v, 0)))
    return Vector((c.x, c.y, 0)), walking


def build_thief():
    """Little toy 'chor': black striped body, skin head, black eye mask, swinging legs, money bag."""
    root = bpy.data.objects.new("thief_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)

    def stripes(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = "Z"
        w.inputs["Scale"].default_value = 3.0
        r = nt.nodes.new("ShaderNodeValToRGB")
        r.color_ramp.interpolation = "CONSTANT"
        r.color_ramp.elements[0].color = (0.02, 0.02, 0.025, 1)
        r.color_ramp.elements[1].position = 0.5
        r.color_ramp.elements[1].color = (0.9, 0.9, 0.9, 1)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = 0.5
        nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
        nt.links.new(w.outputs["Fac"], r.inputs["Fac"])
        nt.links.new(r.outputs["Color"], p.inputs["Base Color"])
        return p
    body = k.node_mat("thief_body", stripes)
    blk = k.pbr("thief_blk", (0.02, 0.02, 0.025), 0.5)
    skin = k.pbr("thief_skin", (0.85, 0.55, 0.38), 0.45)
    k.cyl("t_body", 0.62, 1.5, Vector((0, 0, 1.75)), body, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, location=(0, 0, 2.5), segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(body)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, location=(0, 0, 3.15), segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(skin)
    k.cyl("t_mask", 0.635, 0.28, Vector((0, 0, 3.22)), blk, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.64, location=(0, 0, 3.32), segments=32, ring_count=16)
    cap = bpy.context.object
    cap.scale = (1, 1, 0.75)
    bpy.ops.object.shade_smooth()
    cap.data.materials.append(blk)
    for sx in (-0.22, 0.22):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(sx, -0.58, 3.22), segments=16, ring_count=8)
        bpy.context.object.data.materials.append(k.emit("t_eye", (1, 1, 1), 1.2))
    bag = k.pbr("bag_m", (0.75, 0.62, 0.38), 0.8)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0.85, 0.1, 1.6), segments=24, ring_count=12)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(bag)
    k.text("t_bag", "$", 0.45, Vector((0.85, -0.42, 1.45)), [k.pbr("bag_t", (0.1, 0.4, 0.1), 0.6)], extrude=0.02)
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    root.scale = (1.35, 1.35, 1.35)
    legs = []
    for sx in (-0.28, 0.28):
        lr = bpy.data.objects.new("leg_root", None)
        bpy.context.collection.objects.link(lr)
        lr.parent = root
        lr.location = (sx, 0, 1.05)
        b0 = set(bpy.data.objects)
        k.cyl("t_leg", 0.2, 1.0, Vector((0, 0, -0.5)), blk, verts=16)
        k.box("t_shoe", (0.32, 0.5, 0.18), Vector((0, -0.12, -0.98)), blk)
        for o in [o for o in bpy.data.objects if o not in b0]:
            o.parent = lr
        legs.append(lr)
    k.interp("LINEAR")
    phase = 0.0
    for f in range(-1, N + 1):
        ff = max(f, 0)
        pos, walking = thief_pos(ff)
        nxt, _ = thief_pos(ff + 1)
        if walking:
            phase += 0.55
        bob = 0.12 * abs(math.sin(phase)) if walking else 0.0
        root.location = pos + Vector((0, 0, bob))
        dv = nxt - pos
        if dv.length > 1e-3:
            root.rotation_euler = (0, 0, math.atan2(dv.y, dv.x) + math.pi / 2)
        else:
            root.rotation_euler = (0, 0, ANG + math.pi / 2 - 0.9)            # stand, turned towards the camera
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        for j, lr in enumerate(legs):
            lr.rotation_euler = (0.5 * math.sin(phase + j * math.pi) if walking else 0.0, 0, 0)
            lr.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")


def build_zone():
    """Detection fan on the mat in front of the PIR (colour / opacity set per frame in upd)."""
    import bmesh

    def b(nt):
        e = nt.nodes.new("ShaderNodeEmission")
        e.name = "E"
        e.inputs["Strength"].default_value = 2.5
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.name = "MIX"
        mx.inputs["Fac"].default_value = 0.0
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(e.outputs[0], mx.inputs[2])
        return mx
    m = k.node_mat("zone_m", b)
    for name, r0, r1 in (("zone", FACE, FACE + ZONE), ("zone_edge", FACE + ZONE - 0.25, FACE + ZONE)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        n = 40
        inner, outer = [], []
        for i in range(n + 1):
            a = -HALF + 2 * HALF * i / n
            for r, lst in ((r0, inner), (r1, outer)):
                p = world(Vector((r * math.cos(a), r * math.sin(a), 0)))
                lst.append(bm.verts.new((p.x, p.y, 0.02 if name == "zone" else 0.03)))
        for i in range(n):
            bm.faces.new((inner[i], inner[i + 1], outer[i + 1], outer[i]))
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(m if name == "zone" else k.node_mat("zone_edge_m", b))
        o.visible_shadow = False


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
    build_thief()
    build_zone()

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
    son = world(Vector((1.7, 0, -0.3)))               # sensor + zone
    game = Vector((0.8, 0.9, 1.4))                   # OLED + sensor + zone + LEDs
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
        h = alarm(ff)
        flash = h and (ff // 4) % 2 == 0
        for name, on in (("led_r", flash), ("led_g", armed(ff) and not h)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        if h:
            col, a = (1.0, 0.08, 0.04), (0.2 if flash else 0.11)
        elif armed(ff):
            col, a = (0.1, 0.8, 1.0), 0.08 + 0.03 * math.sin(ff * 0.3)
        else:
            col, a = (0.6, 0.65, 0.7), 0.05
        for mat, mul in (("zone_m", 1.0), ("zone_edge_m", 5.0)):
            nt = bpy.data.materials[mat].node_tree
            nt.nodes["E"].inputs["Color"].default_value = (*col, 1)
            nt.nodes["MIX"].inputs["Fac"].default_value = min(1.0, a * mul)
        bpy.data.materials["pir_dome_m"].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 0.6 if detecting(ff) else 0.0
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
