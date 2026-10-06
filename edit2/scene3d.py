#!/usr/bin/env python3
"""Builds and renders the 3D animation for the Serial.begin(9600) short.

Everything is modelled procedurally (no downloaded assets): an Arduino Uno-style
board, a laptop, the USB cable, flying 1/0 bits, two "baud-rate" dials, the
clock-wire X, the mismatch X, the success tick, and floating 3D labels.

Timeline = the tightened voiceover timeline at 30 fps (see SHOT_FRAMES).
Run:  python3 edit2/scene3d.py [--preview] [--start N --end M]
Needs the `bpy` module (pip install bpy). Renders with Cycles; uses the GPU
(OptiX/CUDA) automatically if one is available, else the CPU.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SCREENS = os.path.join(HERE, "work", "screens")
FRAMES = os.path.join(HERE, "work", "frames")
FONT = os.path.join(HERE, "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
FPS = 30
END = 788
# shot starts (output frames): hook, devices, bits, no-clock, mismatch, X, fix, same, cta
SHOT_FRAMES = [0, 87, 183, 273, 366, 450, 530, 638, 704]

ARD = Vector((-2.4, 0.0, 0.0))
LAP = Vector((2.6, 0.5, 0.0))
DIAL_A = Vector((-2.4, 0.0, 3.0))
DIAL_L = Vector((2.6, 0.5, 3.65))
HOOK = Vector((0.0, 60.0, 3.0))

prefs = bpy.context.preferences.edit


def interp(kind):
    prefs.keyframe_new_interpolation_type = kind


# ------------------------------------------------------------------ helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, END - 1
    return sc


def node_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sh = build(nt)
    nt.links.new(sh.outputs[0], out.inputs[0])
    return m


def emit(name, col, strength=1.0):
    def b(nt):
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (*col, 1)
        e.inputs["Strength"].default_value = min(strength, 1.4)
        return e
    return node_mat(name, b)


def pbr(name, col, rough=0.4, metal=0.0, em=None, ems=0.0):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if em:
            p.inputs["Emission Color"].default_value = (*em, 1)
            p.inputs["Emission Strength"].default_value = ems
        return p
    return node_mat(name, b)


def image_emit(name, path, strength=1.2):
    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path)
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = strength
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    return node_mat(name, b)


def box(name, size, loc, mat, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("bev", "BEVEL")
    bev.width = min(size) * 0.18
    bev.segments = 2
    o.data.materials.append(mat)
    if parent:
        bpy.context.view_layer.update()
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def text(name, body, size, loc, mats, extrude=0.06, align="CENTER", rot=(math.radians(90), 0, 0), spans=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = extrude * 0.25
    cu.bevel_resolution = 2
    cu.align_x = align
    cu.align_y = "CENTER"
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    for m in mats:
        o.data.materials.append(m)
    for a, b, idx in spans or []:
        for i in range(a, b):
            cu.body_format[i].material_index = idx
    return o


def show(o, frames):
    """frames: list of (start, end) where object renders; hidden elsewhere."""
    interp("CONSTANT")
    o.hide_render = True
    o.keyframe_insert("hide_render", frame=-1)
    for a, b in frames:
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=a)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=b)
    interp("BEZIER")


def pop(o, f, s=1.0, over=1.18):
    interp("BEZIER")
    o.scale = (0.001,) * 3
    o.keyframe_insert("scale", frame=f)
    o.scale = (s * over,) * 3
    o.keyframe_insert("scale", frame=f + 5)
    o.scale = (s,) * 3
    o.keyframe_insert("scale", frame=f + 9)


# ------------------------------------------------------------------ world
def build_world(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 260
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.06
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    grad = nt.nodes.new("ShaderNodeSeparateXYZ")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.004, 0.008, 0.03, 1)
    mix.inputs["B"].default_value = (0.03, 0.012, 0.07, 1)
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs["Factor"].default_value = 0.5
    nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(tc.outputs["Generated"], grad.inputs[0])
    nt.links.new(grad.outputs["Z"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], add.inputs["A"])
    nt.links.new(ramp.outputs["Color"], add.inputs["B"])
    nt.links.new(add.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs[0], out.inputs[0])


def area(name, loc, target, energy, size, col=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = col
    o = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


# ------------------------------------------------------------------ models
def build_floor():
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    f = bpy.context.object
    f.data.materials.append(pbr("floor", (0.012, 0.015, 0.03), rough=0.28, metal=0.2))
    # soft glowing grid ring under the devices
    bpy.ops.mesh.primitive_torus_add(major_radius=4.6, minor_radius=0.015, location=(0.1, 0.25, 0.005))
    bpy.context.object.data.materials.append(emit("ring", (0.1, 0.5, 1.0), 4))


def build_arduino():
    root = bpy.data.objects.new("arduino", None)
    bpy.context.collection.objects.link(root)
    root.location = ARD
    pcb = pbr("pcb", (0.0, 0.22, 0.45), rough=0.35)
    black = pbr("blk", (0.02, 0.02, 0.025), rough=0.5)
    metal = pbr("metal", (0.8, 0.8, 0.82), rough=0.2, metal=1.0)
    gold = pbr("gold", (0.9, 0.7, 0.3), rough=0.25, metal=1.0)
    x, y = ARD.x, ARD.y
    box("pcb", (2.7, 2.1, 0.07), (x, y, 0.16), pcb, root)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl("standoff", 0.07, 0.14, (x + sx * 1.2, y + sy * 0.9, 0.07), metal)
    box("chip", (1.3, 0.36, 0.12), (x + 0.15, y - 0.35, 0.26), black, root)
    for i in range(14):
        box("leg", (0.04, 0.06, 0.05), (x - 0.45 + i * 0.092, y - 0.55, 0.22), metal, root)
        box("leg", (0.04, 0.06, 0.05), (x - 0.45 + i * 0.092, y - 0.15, 0.22), metal, root)
    box("hdrT", (2.2, 0.14, 0.2), (x + 0.05, y + 0.92, 0.3), black, root)
    box("hdrB", (1.9, 0.14, 0.2), (x + 0.2, y - 0.92, 0.3), black, root)
    for i in range(18):
        box("pin", (0.035, 0.035, 0.05), (x - 0.98 + i * 0.12, y + 0.92, 0.41), gold, root)
    box("usb", (0.55, 0.5, 0.32), (x + 1.25, y + 0.45, 0.36), metal, root)
    box("jack", (0.5, 0.36, 0.3), (x + 1.25, y - 0.55, 0.35), black, root)
    box("xtal", (0.32, 0.12, 0.1), (x - 0.6, y + 0.35, 0.25), metal, root)
    led = box("led", (0.1, 0.06, 0.05), (x - 0.9, y + 0.55, 0.22), emit("led", (0.2, 1.0, 0.3), 30), root)
    t = text("ardlbl", "ARDUINO", 0.24, (x - 0.15, y + 0.2, 0.2), [emit("w", (1, 1, 1), 2)], extrude=0.0, rot=(0, 0, 0))
    t2 = text("ardlbl3d", "ARDUINO", 0.32, (x, y - 1.6, 0.25), [emit("grey", (0.55, 0.62, 0.8), 1.5)], extrude=0.02)
    return root, led, t, t2


def build_laptop():
    root = bpy.data.objects.new("laptop", None)
    bpy.context.collection.objects.link(root)
    root.location = LAP
    alu = pbr("alu", (0.25, 0.27, 0.3), rough=0.3, metal=0.8)
    keys = pbr("keys", (0.03, 0.03, 0.04), rough=0.6)
    x, y = LAP.x, LAP.y
    box("base", (3.2, 2.1, 0.1), (x, y, 0.07), alu, root)
    box("kbd", (2.8, 1.0, 0.02), (x, y + 0.3, 0.13), keys, root)
    box("pad", (1.0, 0.6, 0.015), (x, y - 0.6, 0.125), pbr("pad", (0.18, 0.19, 0.22), 0.4, 0.5), root)
    box("port", (0.06, 0.3, 0.1), (x - 1.62, y - 0.2, 0.08), keys, root)
    tilt = math.radians(-12)
    lid = box("lid", (3.2, 0.08, 2.05), (x, y + 1.05 + 0.2, 1.08), alu, root, rot=(tilt, 0, 0))
    screens = {}
    for name in ["idle", "bad0", "bad1", "bad2", "bad3", "good0", "good1", "good2", "good3", "cta"]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y + 1.05 + 0.2 - 0.05 + 0.0, 1.1), rotation=(math.radians(90) + tilt, 0, 0))
        p = bpy.context.object
        p.name = "scr_" + name
        p.scale = (2.95, 1.84, 1)
        # nudge the plane in front of the lid along its normal
        p.location += Vector((0, -0.045, 0.0))
        p.data.materials.append(image_emit("m_" + name, os.path.join(SCREENS, name + ".png")))
        screens[name] = p
    t = text("laplbl3d", "LAPTOP", 0.32, (x, y - 1.6, 0.25), [emit("grey2", (0.55, 0.62, 0.8), 1.5)], extrude=0.02)
    return root, screens, t


def build_cable():
    cu = bpy.data.curves.new("cable", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    pts = [ARD + Vector((1.55, 0.45, 0.36)), Vector((0.0, -0.9, 0.1)), LAP + Vector((-1.68, -0.2, 0.08))]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.055
    cu.bevel_resolution = 4
    o = bpy.data.objects.new("cable", cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(pbr("cablem", (0.02, 0.02, 0.025), rough=0.35))
    # glowing data line on top of the cable
    cu2 = cu.copy()
    cu2.bevel_depth = 0.07
    glow = bpy.data.objects.new("cableglow", cu2)
    bpy.context.collection.objects.link(glow)
    glow.data.materials.clear()
    glow.data.materials.append(emit("cglow", (0.1, 0.5, 1.0), 0.0))
    return o, glow


def build_bits(path, start, end):
    blue = emit("bit1", (0.02, 0.2, 1.0), 6)
    red = emit("bit0", (1.0, 0.03, 0.05), 6)
    white = emit("bitw", (1, 1, 1), 3)
    pattern = "10110010011010110"
    bits = []
    interp("LINEAR")
    for i, ch in enumerate(pattern):
        bpy.ops.mesh.primitive_cube_add(size=0.34)
        b = bpy.context.object
        b.name = f"bit{i}"
        bev = b.modifiers.new("bev", "BEVEL")
        bev.width = 0.06
        bev.segments = 3
        b.data.materials.append(blue if ch == "1" else red)
        c = b.constraints.new("FOLLOW_PATH")
        c.target = path
        c.use_fixed_location = True
        c.forward_axis = "FORWARD_X"
        t = text(f"bt{i}", ch, 0.3, (0, -0.18, 0.0), [white], extrude=0.01)
        t.parent = b
        launch = start + i * 7
        c.offset_factor = 0.0
        c.keyframe_insert("offset_factor", frame=launch)
        c.offset_factor = 1.0
        c.keyframe_insert("offset_factor", frame=launch + 34)
        b.location = (0, 0, 0.32)
        show(b, [(launch, min(end, launch + 35))])
        show(t, [(launch, min(end, launch + 35))])
        bits.append(b)
    interp("BEZIER")
    return bits


def build_dial(name, loc, label, col_label):
    face = emit(name + "face", (0.06, 0.07, 0.12), 1.0)
    rim = emit(name + "rim", (0.15, 0.55, 1.0), 6)
    needle_m = emit(name + "needle", (1.0, 0.05, 0.03), 8)
    rot = (math.radians(90), 0, 0)
    d = cyl(name, 0.75, 0.08, loc, face, rot=rot)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.78, minor_radius=0.045, location=loc, rotation=rot)
    ring = bpy.context.object
    ring.data.materials.append(rim)
    ticks = []
    for i in range(12):
        a = i / 12 * 2 * math.pi
        p = loc + Vector((math.sin(a) * 0.6, -0.06, math.cos(a) * 0.6))
        ticks.append(box(name + "tick", (0.04, 0.02, 0.12), p, emit(name + "tk", (0.8, 0.85, 1), 3), rot=(0, a, 0)))
    pivot = bpy.data.objects.new(name + "pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = loc + Vector((0, -0.08, 0))
    needle = box(name + "ndl", (0.06, 0.03, 0.62), loc + Vector((0, -0.08, 0.26)), needle_m)
    bpy.context.view_layer.update()
    needle.parent = pivot
    needle.matrix_parent_inverse = pivot.matrix_world.inverted()
    cap = cyl(name + "cap", 0.09, 0.06, loc + Vector((0, -0.1, 0)), emit(name + "capm", (1, 1, 1), 2), rot=rot)
    lbls = {}
    for key, txt, col in label:
        lbls[key] = text(name + key, txt, 0.42, loc + Vector((0, -0.05, -1.2)), [emit(name + key + "m", col, 4)], extrude=0.012)
    parts = [d, ring, needle, cap] + ticks
    return parts, pivot, lbls


def build_x(name, loc, size, col):
    m = emit(name, col, 8)
    a = box(name + "a", (size * 0.22, size * 0.18, size * 1.2), loc, m, rot=(0, math.radians(45), 0))
    b = box(name + "b", (size * 0.22, size * 0.18, size * 1.2), loc, m, rot=(0, math.radians(-45), 0))
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = loc
    bpy.context.view_layer.update()
    for p in (a, b):
        p.parent = root
        p.matrix_parent_inverse = root.matrix_world.inverted()
    return root, [a, b]


def build_tick(name, loc, size, col):
    m = emit(name, col, 8)
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = loc
    a = box(name + "a", (size * 0.2, size * 0.18, size * 0.55), loc + Vector((-size * 0.28, 0, -size * 0.12)), m, rot=(0, math.radians(-45), 0))
    b = box(name + "b", (size * 0.2, size * 0.18, size * 1.1), loc + Vector((size * 0.18, 0, size * 0.1)), m, rot=(0, math.radians(35), 0))
    bpy.context.view_layer.update()
    for p in (a, b):
        p.parent = root
        p.matrix_parent_inverse = root.matrix_world.inverted()
    return root, [a, b]


# ------------------------------------------------------------------ cameras
def camera(name, keys, lens_keys=None, shake=None):
    """keys: [(frame, cam_loc, target_loc)]"""
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 36
    cam = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(cam)
    tgt = bpy.data.objects.new(name + "_t", None)
    bpy.context.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    interp("BEZIER")
    for f, loc, t in keys:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
        tgt.location = t
        tgt.keyframe_insert("location", frame=f)
    for f, lens in lens_keys or [(keys[0][0], 35)]:
        cd.lens = lens
        cd.keyframe_insert("lens", frame=f)
    if shake:
        f0, dur, amp = shake
        for i in range(dur):
            k = amp * (1 - i / dur) ** 2
            base = Vector(keys[0][1])
            cam.location = base + Vector((math.sin(i * 2.1) * k, 0, math.cos(i * 2.9) * k))
            cam.keyframe_insert("location", frame=f0 + i)
    return cam


# ------------------------------------------------------------------ build
def build(sc):
    build_world(sc)
    build_floor()
    area("key", (-3, -6, 7), (0, 0, 0.5), 900, 6)
    area("rimL", (-7, 4, 3), (-2, 0, 0.5), 500, 4, (0.2, 0.5, 1.0))
    area("rimR", (7, 4, 3), (2, 0, 0.5), 500, 4, (0.8, 0.25, 1.0))
    area("hookkey", HOOK + Vector((0, -6, 4)), HOOK, 600, 6)

    S = SHOT_FRAMES

    # --- hook: 3D "Serial.begin(9600)" with the 9600 glowing
    white = pbr("hookw", (0.9, 0.92, 1.0), rough=0.25, metal=0.3)
    green = pbr("hookg", (0.02, 0.6, 0.12), rough=0.2, metal=0.3, em=(0.05, 1.0, 0.25), ems=0.35)
    hook = text("hook", "Serial.begin(9600)", 0.62, HOOK + Vector((0, 0, 2.3)), [white, green], extrude=0.12, spans=[(13, 17, 1)])
    big = text("hookbig", "9600", 2.4, HOOK, [green], extrude=0.35)
    hook9600 = HOOK + Vector((0, 0, 0.0))
    for o in (hook, big):
        show(o, [(S[0], S[1])])
    pop(big, 6, over=1.25)
    q = text("hookq", "?", 2.0, HOOK + Vector((3.4, 0.4, 0.3)), [pbr("qm", (0.9, 0.7, 0.02), rough=0.25, metal=0.3, em=(1, 0.85, 0.1), ems=0.35)], extrude=0.25,
             rot=(math.radians(90), 0, math.radians(-12)))
    show(q, [(22, S[1])])
    pop(q, 22, over=1.4)

    # --- devices + cable
    ard, led, _, ard3d = build_arduino()
    lap, screens, lap3d = build_laptop()
    cable, glow = build_cable()
    interp("BEZIER")
    gm = glow.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in [(S[2], 0.0), (S[2] + 10, 3.0), (S[3], 3.0), (S[3] + 12, 0.0), (S[6] + 40, 0.0), (S[6] + 50, 3.0)]:
        gm.default_value = v
        gm.keyframe_insert("default_value", frame=f)

    tx = text("tx", "TX", 0.42, ARD + Vector((1.45, -0.6, 1.0)), [emit("txm", (0.25, 0.6, 1.0), 5)], extrude=0.012)
    rx = text("rx", "RX", 0.42, LAP + Vector((-1.55, -0.9, 1.0)), [emit("rxm", (0.25, 0.6, 1.0), 5)], extrude=0.012)
    for o, f in ((tx, S[1] + 25), (rx, S[1] + 35)):
        show(o, [(f, S[3])])
        pop(o, f)

    build_bits(cable, S[1] + 60, S[3] + 20)

    yel = emit("yel", (1.0, 0.85, 0.1), 6)
    wht = emit("wht", (1, 1, 1), 3)
    bps = text("bps", "9600", 0.95, Vector((0.2, -0.6, 2.35)), [yel], extrude=0.02)
    bps2 = text("bps2", "bits / second", 0.42, Vector((0.2, -0.6, 1.7)), [wht], extrude=0.012)
    for o, f in ((bps, S[2] + 32), (bps2, S[2] + 38)):
        show(o, [(f, S[3])])
        pop(o, f)

    # --- dials
    da, pa, la = build_dial("dA", DIAL_A, [("l", "9600", (0.05, 1.0, 0.25))], None)
    dl, pl, ll = build_dial("dL", DIAL_L, [("ok", "9600", (0.05, 1.0, 0.25)), ("bad", "115200", (1.0, 0.03, 0.04))], None)
    for o in da + dl + [la["l"]]:
        show(o, [(S[3], END)])
    for o in da + dl:
        pass
    show(ll["ok"], [(S[3], S[4]), (S[6] + 22, END)])
    show(ll["bad"], [(S[4], S[6] + 22)])
    pop(ll["bad"], S[4])
    pop(ll["ok"], S[6] + 22)
    pop(da[0], S[3])
    pop(dl[0], S[3] + 4)

    # needles: same speed, then laptop runs 8x fast, then eases back into sync
    w = -0.13
    interp("LINEAR")
    for f in (0, END):
        pa.rotation_euler = (0, -w * f, 0)
        pa.keyframe_insert("rotation_euler", frame=f)
    for f in (0, S[4]):
        pl.rotation_euler = (0, -w * f, 0)
        pl.keyframe_insert("rotation_euler", frame=f)
    fast_end = S[6] + 20
    a_fast = -w * S[4] + (-w * 8) * (fast_end - S[4])
    pl.rotation_euler = (0, a_fast, 0)
    pl.keyframe_insert("rotation_euler", frame=fast_end)
    sync = S[6] + 50
    target = -w * sync
    while target < a_fast + 2.5:
        target += 2 * math.pi
    interp("BEZIER")
    pl.rotation_euler = (0, target, 0)
    pl.keyframe_insert("rotation_euler", frame=sync)
    interp("LINEAR")
    pl.rotation_euler = (0, target + (-w) * (END - sync), 0)
    pl.keyframe_insert("rotation_euler", frame=END)
    interp("BEZIER")

    # --- "no clock wire": dashed wire between dials with a red X
    dash_m = emit("dash", (0.6, 0.65, 0.75), 2)
    dashes = []
    for i in range(11):
        k = (i + 0.5) / 11
        p = DIAL_A.lerp(DIAL_L, k)
        if 0.38 < k < 0.62:
            continue
        dashes.append(box("dash", (0.22, 0.05, 0.05), p, dash_m))
    for i, o in enumerate(dashes):
        show(o, [(S[3] + 15 + i * 2, S[4])])
    xr, xparts = build_x("nowire", DIAL_A.lerp(DIAL_L, 0.5), 0.9, (1.0, 0.01, 0.02))
    for o in xparts:
        show(o, [(S[3] + 38, S[4])])
    pop(xr, S[3] + 38)
    cw = text("clockwire", "CLOCK WIRE", 0.34, DIAL_A.lerp(DIAL_L, 0.5) + Vector((0, 0, 0.8)), [emit("cwm", (0.8, 0.85, 1), 3)], extrude=0.01)
    show(cw, [(S[3] + 30, S[4])])
    pop(cw, S[3] + 30)

    # --- laptop screens
    sched = [("idle", 0, S[4]), ("bad0", S[4], S[4] + 18), ("bad1", S[4] + 18, S[4] + 38),
             ("bad2", S[4] + 38, S[4] + 58), ("bad3", S[4] + 58, S[6] + 20),
             ("good0", S[6] + 20, S[6] + 45), ("good1", S[6] + 45, S[6] + 60),
             ("good2", S[6] + 60, S[6] + 75), ("good3", S[6] + 75, S[8]), ("cta", S[8], END)]
    for name, a, b in sched:
        show(screens[name], [(a, b)])

    # --- big red X (mismatch) and green tick (fixed)
    bx, bxp = build_x("bigx", LAP + Vector((-0.2, -1.6, 1.4)), 1.4, (1.0, 0.01, 0.02))
    for o in bxp:
        show(o, [(S[5] + 3, S[6])])
    pop(bx, S[5] + 3, over=1.35)
    tk, tkp = build_tick("tick", LAP + Vector((1.1, -1.2, 1.5)), 1.0, (0.05, 1.0, 0.2))
    for o in tkp:
        show(o, [(S[6] + 85, S[8])])
    pop(tk, S[6] + 85, over=1.35)

    same = text("same", "SAME NUMBER!", 0.72, Vector((0.1, 0.2, 4.75)), [yel], extrude=0.02)
    show(same, [(S[7] + 6, S[8])])
    pop(same, S[7] + 6)
    for o in (la["l"], ll["ok"]):
        pass

    # --- cameras (one per shot, switched with timeline markers)
    lap_scr = LAP + Vector((0, 1.2, 1.1))
    cams = [
        camera("cA", [(S[0], HOOK + Vector((-1.5, -13, 1.6)), HOOK + Vector((0, 0, 1.2))),
                      (S[1] - 12, HOOK + Vector((0.4, -10.5, 1.1)), HOOK + Vector((0.3, 0, 1.0))),
                      (S[1], HOOK + Vector((0, -4.0, 0.6)), hook9600 + Vector((0, 0, 0.6)))],
               lens_keys=[(S[0], 30), (S[1] - 12, 32), (S[1], 80)]),
        camera("cB", [(S[1], Vector((-6.5, -7.5, 4.0)), ARD + Vector((0.6, 0, 0.3))),
                      (S[2], Vector((-0.5, -10.5, 6.5)), Vector((0.2, 0.3, 0.6)))], lens_keys=[(S[1], 30)]),
        camera("cC", [(S[2], Vector((-3.2, -4.0, 0.9)), Vector((-1.4, 0, 0.5))),
                      (S[2] + 30, Vector((-1.2, -5.2, 1.3)), Vector((0.0, -0.4, 1.1))),
                      (S[3], Vector((0.9, -6.4, 1.7)), Vector((0.4, -0.3, 1.5)))], lens_keys=[(S[2], 26)]),
        camera("cD", [(S[3], Vector((0.1, -9.0, 2.6)), Vector((0.1, 0, 2.0))),
                      (S[4], Vector((0.1, -13.0, 3.6)), Vector((0.1, 0, 2.0)))], lens_keys=[(S[3], 30)]),
        camera("cE", [(S[4], Vector((0.6, -6.0, 2.4)), Vector((2.4, 0.6, 2.2))),
                      (S[5], Vector((1.8, -5.0, 2.2)), Vector((2.6, 0.6, 2.2)))], lens_keys=[(S[4], 30)]),
        camera("cF", [(S[5], Vector((2.0, -6.2, 1.9)), Vector((2.5, 0.4, 1.8))),
                      (S[6], Vector((2.1, -5.6, 1.9)), Vector((2.5, 0.4, 1.8)))], lens_keys=[(S[5], 30)],
               shake=(S[5] + 3, 14, 0.18)),
        camera("cG", [(S[6], Vector((1.2, -7.0, 2.8)), Vector((2.6, 0.5, 2.2))),
                      (S[6] + 40, Vector((1.6, -6.0, 2.6)), Vector((2.6, 0.5, 2.3))),
                      (S[7], Vector((2.3, -5.0, 2.0)), lap_scr)], lens_keys=[(S[6], 30)]),
        camera("cH", [(S[7], Vector((-3.8, -8.6, 2.8)), Vector((0.1, 0, 2.7))),
                      (S[8], Vector((3.6, -8.6, 3.6)), Vector((0.1, 0, 2.7)))], lens_keys=[(S[7], 26)]),
        camera("cI", [(S[8], Vector((2.4, -6.5, 1.6)), lap_scr), (END, Vector((2.6, -2.2, 1.15)), lap_scr)],
               lens_keys=[(S[8], 30)]),
    ]
    for f, cam in zip(S, cams):
        m = sc.timeline_markers.new(cam.name, frame=f)
        m.camera = cam
    sc.camera = cams[0]


def setup_render(sc, preview):
    sc.render.engine = "CYCLES"
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280
    sc.render.resolution_percentage = 50 if preview else 100
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.use_persistent_data = True
    sc.render.use_overwrite = False  # resume: skip frames already on disk
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(FRAMES, "")
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    cy = sc.cycles
    cy.samples = 8 if preview else 10
    cy.use_adaptive_sampling = True
    cy.use_denoising = True
    cy.max_bounces = 4
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 2
    cy.transmission_bounces = 0
    cy.caustics_reflective = cy.caustics_refractive = False
    cy.device = "CPU"
    try:
        cp = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
            try:
                cp.compute_device_type = kind
                cp.get_devices()
                if any(d.type == kind for d in cp.devices):
                    for d in cp.devices:
                        d.use = d.type == kind
                    cy.device = "GPU"
                    break
            except TypeError:
                continue
    except Exception:
        pass
    print("Cycles device:", cy.device)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=END - 1)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--save", action="store_true", help="also save the .blend")
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(FRAMES, exist_ok=True)
    sc = reset()
    build(sc)
    setup_render(sc, args.preview)
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "work", "serial_begin.blend"))
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
