#!/usr/bin/env python3
"""Photoreal ESP32 RFID smart door lock (Blender, procedural). Oak panel door in a white hallway,
breadboard on the middle rail with an ESP32 DevKit, MFRC522 reader, green/red status LEDs and a
buzzer; SG90 servo + stainless sliding bolt on the lock edge, strike on the jamb. A 'VISITOR'
card is refused, the orange key fob is accepted, the bolt slides back and the door swings open
into a bright room. 1 unit = 2.5 cm. 24 fps, 384 frames.
Run: python3 edit8/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit2_scene3d", os.path.join(HERE, "..", "edit2", "scene3d.py"))
k = importlib.util.module_from_spec(_spec)  # edit2 modelling helpers
_spec.loader.exec_module(k)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from timeline import FPS, N, SHOTS, unlocked, servo_deg, green, red, door_angle, fob, card  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
TEX = os.path.join(HERE, "work", "tex")
B = Vector((10.5, 0, 44))                      # breadboard centre on the door face
R90 = (math.radians(90), 0, 0)                 # local +z (out of the door) -> world -y
READER = Vector((11.45, -1.0, 44.1))           # where a card/fob touches the MFRC522


def L(x, y, z):
    """Board-local (x right, y up, z out of the door) -> world."""
    return Vector((B.x + x, -z, B.z + y))


def lbox(name, size, loc, mat):
    return k.box(name, (size[0], size[2], size[1]), L(*loc), mat)


def wire(name, pts, col, r=0.022, mat=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat or k.pbr(name + "m", col, rough=0.35))
    return o


def tex_mat(name, path, rough=0.5, scale=1.0, bump=0.0, emit=0.0):
    def b(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, 1)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = rough
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        if bump:
            bm = nt.nodes.new("ShaderNodeBump")
            bm.inputs["Strength"].default_value = bump
            nt.links.new(t.outputs["Color"], bm.inputs["Height"])
            nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
        return p
    return k.node_mat(name, b)


def plane(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def key_bool(target, prop, states, on_val):
    """CONSTANT keyframes for a bool-per-frame state on a socket (default_value) or light (energy)."""
    k.interp("CONSTANT")
    prev = None
    for f in range(-1, N + 1):
        v = states(max(f, 0))
        if v != prev:
            setattr(target, prop, on_val if v else 0.0)
            target.keyframe_insert(prop, frame=f)
            prev = v
    k.interp("BEZIER")


def status_led(name, lx, ly, col, states):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*[0.08 + 0.8 * c for c in col], 1)
        p.inputs["Roughness"].default_value = 0.08
        p.inputs["Transmission Weight"].default_value = 0.6
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        return p
    m = k.node_mat(name, b)
    k.cyl(name + "_rim", 0.135, 0.035, L(lx, ly, 0.4), m, rot=R90, verts=32)
    k.cyl(name + "_body", 0.12, 0.2, L(lx, ly, 0.51), m, rot=R90, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=L(lx, ly, 0.61), segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(m)
    bpy.ops.object.light_add(type="POINT", location=L(lx, ly, 0.9))
    g = bpy.context.object
    g.data.color = col
    g.data.shadow_soft_size = 0.12
    key_bool(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", states, 3.5)
    key_bool(g.data, "energy", states, 30.0)


def build_board():
    lbox("bb_body", (4.6, 3.0, 0.38), (0, 0, 0.19), k.pbr("bb_side", (0.9, 0.89, 0.85), rough=0.55))
    plane("bb_top", (4.6, 3.0), L(0, 0, 0.382), tex_mat("bb_top_m", os.path.join(TEX, "breadboard.png"), rough=0.6), rot=R90)
    pcb = k.pbr("esp_pcb", (0.015, 0.015, 0.018), rough=0.35)
    blk = k.pbr("esp_blk", (0.02, 0.02, 0.022), rough=0.45)
    steel = bpy.data.materials["steel"]
    gold = k.pbr("gold", (0.95, 0.72, 0.3), rough=0.25, metal=1.0)
    ex = -1.25
    lbox("esp_board", (1.0, 2.1, 0.05), (ex, 0, 0.65), pcb)
    for sx in (-0.41, 0.41):
        lbox("esp_hdr", (0.1, 1.5, 0.1), (ex + sx, -0.1, 0.43), blk)
        for i in range(15):
            lbox("esp_pad", (0.06, 0.06, 0.012), (ex + sx, -0.8 + i * 0.1, 0.68), gold)
    lbox("esp_mod", (0.98, 0.72, 0.04), (ex, 0.66, 0.695), blk)
    lbox("esp_shield", (0.7, 0.66, 0.07), (ex, 0.6, 0.75), steel)
    k.text("esp_lbl", "ESP32", 0.16, L(ex, 0.62, 0.79), [k.pbr("etch", (0.4, 0.41, 0.43), 0.5, 1.0)], extrude=0.0)
    for i in range(5):
        lbox("esp_ant", (0.6 if i % 2 == 0 else 0.03, 0.03, 0.006), (ex, 0.92 + i * 0.03, 0.72), gold)
    lbox("esp_usb", (0.3, 0.22, 0.12), (ex, -1.0, 0.74), steel)
    lbox("esp_chip", (0.18, 0.18, 0.04), (ex + 0.15, -0.55, 0.69), blk)
    for sx in (-0.33, 0.33):
        lbox("esp_btn", (0.16, 0.16, 0.06), (ex + sx, -0.85, 0.7), steel)
    pw = k.pbr("pwr_led", (0.5, 0.02, 0.02), rough=0.2, em=(1.0, 0.04, 0.02), ems=25.0)
    lbox("esp_pwr", (0.06, 0.04, 0.03), (ex - 0.25, -0.35, 0.69), pw)
    bpy.ops.object.light_add(type="POINT", location=L(ex - 0.25, -0.35, 0.8))
    bpy.context.object.data.color = (1, 0.05, 0.03)
    bpy.context.object.data.energy = 0.6
    # USB cable hanging down the door (like a real wall-mounted build)
    lbox("usb_plug", (0.26, 0.3, 0.14), (ex, -1.24, 0.74), k.pbr("plug", (0.05, 0.05, 0.05), rough=0.4))
    wire("usb_cable", [L(ex, -1.38, 0.74), L(ex, -2.2, 0.6), L(ex - 0.3, -8, 0.25), L(ex - 0.2, -30, 0.2),
                       L(ex + 0.4, -43.5, 0.3)], (0.03, 0.03, 0.03), r=0.07)
    # MFRC522 on standoffs
    rx, ry = 0.95, 0.1
    for sx, sy in ((-0.6, -1.0), (0.6, -1.0), (-0.6, 1.0), (0.6, 1.0)):
        k.cyl("rc_stand", 0.07, 0.42, L(rx + sx, ry + sy, 0.6), steel, rot=R90, verts=12)
    lbox("rc_pcb", (1.6, 2.4, 0.05), (rx, ry, 0.8), k.pbr("rc_edge", (0.08, 0.33, 0.68), rough=0.4))
    plane("rc_top", (1.6, 2.4), L(rx, ry, 0.826), tex_mat("rc_m", os.path.join(TEX, "rc522.png"), rough=0.35), rot=R90)
    lbox("rc_chip", (0.3, 0.3, 0.05), (rx, ry + 0.75, 0.86), blk)
    lbox("rc_xtal", (0.3, 0.12, 0.1), (rx - 0.5, ry + 0.7, 0.88), steel)
    for i in range(8):
        lbox("rc_pin", (0.03, 0.3, 0.03), (rx - 0.7 + i * 0.2, ry + 1.3, 0.84), gold)
    # jumpers RC522 header -> ESP32 pins
    cols = [(0.95, 0.15, 0.1), (1.0, 0.55, 0.05), (1.0, 0.85, 0.05), (0.15, 0.3, 0.95), (0.45, 0.25, 0.1), (0.1, 0.1, 0.1)]
    for i, c in enumerate(cols):
        a = L(rx - 0.5 + i * 0.2, ry + 1.45, 0.84)
        bnd = L(ex + 0.5, 0.6 - i * 0.12, 0.38)
        wire(f"jmp{i}", [a, a + Vector((0, -0.4 - 0.1 * i, 0.3 + 0.08 * i)),
                         (a + bnd) / 2 + Vector((0, -0.9 - 0.12 * i, 0.4 + 0.05 * i)), bnd + Vector((0.15, -0.35, 0)), bnd],
             c, r=0.026)
    # status LEDs + buzzer
    status_led("led_g", -0.45, -1.05, (0.1, 1.0, 0.2), green)
    status_led("led_r", -0.1, -1.05, (1.0, 0.05, 0.03), red)
    k.cyl("buzzer", 0.26, 0.32, L(-0.3, 0.95, 0.54), blk, rot=R90, verts=40)
    k.cyl("buzzer_hole", 0.05, 0.02, L(-0.3, 0.95, 0.7), k.pbr("hole", (0, 0, 0), 0.9), rot=R90, verts=16)
    wire("w_led", [L(-0.45, -1.3, 0.38), L(-0.6, -1.5, 0.7), L(ex + 0.5, -0.6, 0.38)], (0.1, 0.7, 0.2), r=0.024)
    wire("w_led2", [L(-0.1, -1.3, 0.38), L(-0.3, -1.6, 0.8), L(ex + 0.5, -0.4, 0.38)], (0.9, 0.9, 0.9), r=0.024)


def build_lock():
    steel = bpy.data.materials["steel"]
    brushed = bpy.data.materials["brushed"]
    k.box("lock_house", (1.7, 0.7, 4.2), Vector((16.4, -0.35, 44)), brushed)
    for z in (42.4, 45.6):
        k.cyl("lock_screw", 0.14, 0.06, Vector((16.4, -0.72, z)), steel, rot=R90, verts=20)
    bolt_root = bpy.data.objects.new("bolt_root", None)
    bpy.context.collection.objects.link(bolt_root)
    bolt_root.location = (0, 0, 0)
    bolt = k.box("bolt", (2.0, 0.42, 0.7), Vector((17.9, -0.35, 44)), steel)
    bpy.context.view_layer.update()
    bolt.parent = bolt_root
    # SG90 servo beside the lock, horn linked to the bolt
    def sb(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.0, 0.07, 0.55, 1)
        p.inputs["Roughness"].default_value = 0.25
        p.inputs["Coat Weight"].default_value = 0.4
        return p
    body = k.node_mat("servo_body", sb)
    S = Vector((14.4, 0, 44))
    k.box("sv_body", (0.45 * 2, 0.85, 0.45 * 2), S + Vector((0, -0.43, 0)), body)
    k.box("sv_tabs", (1.25, 0.06, 0.45 * 2), S + Vector((0, -0.7, 0)), body)
    k.cyl("sv_top", 0.17, 0.18, S + Vector((0, -0.94, 0.22)), body, rot=R90, verts=32)
    k.text("sv_lbl", "SG90", 0.16, S + Vector((0, -0.87, -0.25)), [k.emit("sv_t", (0.9, 0.9, 0.95), 1.0)], extrude=0.0)
    white = k.pbr("horn", (0.95, 0.95, 0.93), rough=0.35)
    pivot = bpy.data.objects.new("sv_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = S + Vector((0, -1.06, 0.22))
    horn = k.box("sv_horn", (0.62, 0.05, 0.11), S + Vector((0.2, -1.06, 0.22)), white)
    hub = k.cyl("sv_hub", 0.08, 0.08, S + Vector((0, -1.06, 0.22)), white, rot=R90, verts=24)
    bpy.context.view_layer.update()
    for o in (horn, hub):
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
    wire("sv_link", [S + Vector((0.45, -1.1, 0.22)), S + Vector((1.2, -1.0, 0.1)), Vector((16.4, -0.75, 44))],
         (0.8, 0.8, 0.82), r=0.03, mat=steel)
    k.interp("LINEAR")
    for f in range(-1, N + 1, 2):
        u = unlocked(max(f, 0))
        bolt_root.location = (-1.45 * u, 0, 0)
        bolt_root.keyframe_insert("location", frame=f)
        pivot.rotation_euler = (0, math.radians(-servo_deg(max(f, 0))), 0)
        pivot.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    for i, col in enumerate(((0.35, 0.18, 0.08), (0.85, 0.1, 0.05), (0.98, 0.55, 0.05))):
        wire(f"sv_w{i}", [S + Vector((-0.45, -0.3, -0.05 + i * 0.05)), S + Vector((-1.2, -0.5, -0.8)),
                          L(1.6, -1.4 + i * 0.1, 0.38)], col, r=0.02)
    # lever handle + key cylinder
    k.cyl("rosette", 0.9, 0.25, Vector((14.6, -0.12, 36)), brushed, rot=R90)
    k.cyl("lever_neck", 0.32, 1.2, Vector((14.6, -0.8, 36)), brushed, rot=R90)
    k.box("lever", (4.2, 0.55, 0.55), Vector((12.7, -1.35, 36)), brushed)
    k.cyl("key_cyl", 0.6, 0.2, Vector((14.6, -0.1, 31.5)), brushed, rot=R90)
    k.box("keyway", (0.12, 0.05, 0.6), Vector((14.6, -0.22, 31.5)), k.pbr("kw", (0.02, 0.02, 0.02), 0.6))


def build_room(sc):
    k.pbr("steel", (0.8, 0.81, 0.83), rough=0.18, metal=1.0)
    k.pbr("brushed", (0.72, 0.73, 0.75), rough=0.32, metal=1.0)
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.85, 0.78, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    plane("floor", (300, 300), Vector((0, 0, 0)), tex_mat("floor_m", os.path.join(TEX, "floor.png"), rough=0.3, scale=6.0, bump=0.02))
    wall = k.pbr("wall", (0.86, 0.85, 0.82), rough=0.85)
    k.box("wall_l", (80, 2, 120), Vector((-60.5, 1.0, 60)), wall)
    k.box("wall_r", (80, 2, 120), Vector((60.5, 1.0, 60)), wall)
    k.box("wall_t", (41, 2, 40), Vector((0, 1.0, 102.5)), wall)
    jamb = k.pbr("jamb", (0.55, 0.3, 0.12), rough=0.45)
    k.box("jamb_l", (2.3, 2.8, 82.5), Vector((-19.35, 0.6, 41.25)), jamb)
    k.box("jamb_r", (2.3, 2.8, 82.5), Vector((19.35, 0.6, 41.25)), jamb)
    k.box("jamb_t", (41, 2.8, 2.5), Vector((0, 0.6, 81.75)), jamb)
    k.box("strike", (0.5, 0.9, 1.4), Vector((18.45, -0.1, 44)), bpy.data.materials["brushed"])
    k.box("switch", (2.0, 0.3, 3.0), Vector((26, -0.15, 44)), k.pbr("switch_m", (0.95, 0.95, 0.94), 0.4))
    k.box("baseboard", (200, 0.6, 3.0), Vector((0, -0.3, 1.5)), k.pbr("base_m", (0.95, 0.95, 0.94), 0.5))
    # bright room behind the door
    plane("inside", (90, 90), Vector((0, 45, 40)), k.emit("inside_m", (1.0, 0.93, 0.8), 1.4), rot=R90)
    k.area("inside_light", (0, 25, 60), (0, 0, 40), 60000, 30, col=(1.0, 0.9, 0.75))
    k.area("key", (-35, -70, 95), (6, 0, 42), 120000, 40, col=(1.0, 0.95, 0.88))
    k.area("fill", (45, -55, 55), (6, 0, 42), 40000, 40, col=(0.85, 0.9, 1.0))
    k.area("top", (10, -15, 110), (10, 0, 44), 25000, 25, col=(1.0, 0.92, 0.8))


def build_door():
    oak = tex_mat("oak_m", os.path.join(TEX, "oak.png"), rough=0.42, bump=0.03)
    oak_d = k.pbr("oak_edge", (0.5, 0.26, 0.09), rough=0.45)
    k.box("door", (36, 1.6, 80), Vector((0, 0.8, 40)), oak_d)
    plane("door_face", (35.9, 79.9), Vector((0, -0.002, 40)), oak, rot=R90)
    for z0, z1 in ((48, 76), (5, 40)):                      # raised panels (mouldings)
        for x0, x1, zz0, zz1 in ((-13, 13, z0, z0 + 0.8), (-13, 13, z1 - 0.8, z1), (-13, -12.2, z0 + 0.85, z1 - 0.85), (12.2, 13, z0 + 0.85, z1 - 0.85)):
            k.box("moulding", (x1 - x0, 0.5, zz1 - zz0), Vector(((x0 + x1) / 2, -0.25, (zz0 + zz1) / 2)), oak_d)
    k.cyl("peephole", 0.45, 0.2, Vector((0, -0.1, 62)), bpy.data.materials["brushed"], rot=R90)


def build_tokens():
    """Visitor card and orange key fob, each on an empty keyed to its approach curve."""
    roots = {}
    for name in ("card", "fob"):
        r = bpy.data.objects.new(name + "_root", None)
        bpy.context.collection.objects.link(r)
        roots[name] = r
    c = Vector((0, 0, 0))
    k.box("card_body", (3.4, 0.03, 2.15), c, k.pbr("card_edge", (0.95, 0.95, 0.95), 0.3))
    plane("card_face", (3.38, 2.13), c + Vector((0, -0.02, 0)), tex_mat("card_m", os.path.join(TEX, "card.png"), rough=0.25), rot=R90)
    orange = k.pbr("fob_m", (1.0, 0.25, 0.08), rough=0.45)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.22, location=(0, 0, -0.1), rotation=R90, vertices=48)
    f = bpy.context.object
    f.name = "fob_body"
    f.scale = (1.0, 1.25, 1.0)
    bpy.ops.object.shade_smooth()
    f.data.materials.append(orange)
    k.cyl("fob_logo", 0.35, 0.02, Vector((0, -0.12, -0.15)), k.pbr("fob_logo_m", (0.85, 0.18, 0.05), 0.3), rot=R90, verts=32)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.045, location=(0, 0, 1.05), rotation=(0, math.radians(90), 0))
    ring = bpy.context.object
    bpy.ops.object.shade_smooth()
    ring.data.materials.append(bpy.data.materials["steel"])
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.name.startswith("card_") and o.type == "MESH":
            o.parent = roots["card"]
        elif o.name.startswith("fob_") and o.type == "MESH" or o is ring:
            o.parent = roots["fob"]
    k.interp("LINEAR")
    away_card, away_fob = Vector((3.0, -11.0, 37.0)), Vector((19.0, -10.0, 35.0))
    for fr in range(-1, N + 1):
        for name, fn, away, rz in (("card", card, away_card, -25), ("fob", fob, away_fob, 30)):
            u = fn(max(fr, 0))
            r = roots[name]
            r.location = away.lerp(READER + Vector((0, -0.08, 0)), u)
            r.rotation_euler = (0, math.radians(rz * (1 - u)), math.radians(-rz * 0.6 * (1 - u)))
            r.keyframe_insert("location", frame=fr)
            r.keyframe_insert("rotation_euler", frame=fr)
    k.interp("BEZIER")
    for o in bpy.data.objects:                 # only on screen in the shots that use them
        if o.parent is roots["card"]:
            k.show(o, [(SHOTS[3] - 2, SHOTS[4])])
        elif o.parent is roots["fob"]:
            k.show(o, [(0, SHOTS[1] - 4), (SHOTS[4], SHOTS[5] + 2)])


def build(sc):
    build_room(sc)
    before = set(bpy.data.objects)
    build_door()
    build_board()
    build_lock()
    door_objs = [o for o in bpy.data.objects if o not in before and o.parent is None]
    hinge = bpy.data.objects.new("door_root", None)
    bpy.context.collection.objects.link(hinge)
    hinge.location = (-18.0, 0.8, 0)
    bpy.context.view_layer.update()
    for o in door_objs:
        o.parent = hinge
        o.matrix_parent_inverse = hinge.matrix_world.inverted()
    k.interp("LINEAR")
    for f in range(-1, N + 1, 2):
        hinge.rotation_euler = (0, 0, math.radians(door_angle(max(f, 0))))
        hinge.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    build_tokens()

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        c.data.clip_end = 1000
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    Sh = SHOTS
    lockc = Vector((13.2, -0.5, 44.0))
    rd = READER
    door_c = Vector((2.0, 0, 41.0))
    sv = Vector((15.6, -0.6, 44.0))
    cams = [
        cam("s0", [(Sh[0], Vector((5.5, -15.5, 47.5)), lockc), (Sh[1], Vector((6.5, -14.0, 47.0)), lockc)], 38, rd, 2.8),
        cam("s1", [(Sh[1], Vector((-14, -80, 46)), door_c), (Sh[2], Vector((-9, -68, 44)), door_c)], 28, B, 5.6),
        cam("s2", [(Sh[2], Vector((7.6, -7.6, 46.4)), B + Vector((0.1, -0.6, 0.1))),
                   (Sh[3], Vector((9.4, -6.8, 45.4)), B + Vector((0.1, -0.6, 0.1)))], 45, B + Vector((0, -0.7, 0)), 2.0),
        cam("s3", [(Sh[3], Vector((17.0, -13.5, 47.0)), rd + Vector((0, 0, -0.3))),
                   (Sh[4], Vector((16.0, -12.0, 46.4)), rd + Vector((0, 0, -0.3)))], 40, rd, 2.4),
        cam("s4", [(Sh[4], Vector((5.0, -13.0, 47.0)), rd + Vector((0, 0, -0.3))),
                   (Sh[5], Vector((6.2, -11.5, 46.4)), rd + Vector((0, 0, -0.3)))], 40, rd, 2.4),
        cam("s5", [(Sh[5], Vector((12.6, -7.4, 46.8)), sv), (Sh[6], Vector((13.8, -6.6, 45.8)), sv)], 42, sv, 2.0),
        cam("s6", [(Sh[6], Vector((-2, -60, 43)), door_c), (N, Vector((-5, -66, 44)), door_c)], 30, door_c, 5.6),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]


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
    sc.render.use_persistent_data = False   # persistent data intermittently rendered the servo black
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 8, 6, 3
    cy.samples = 8 if args.preview else 14
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
