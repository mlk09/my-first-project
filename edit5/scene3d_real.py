#!/usr/bin/env python3
"""Photoreal-style ESP32 water-level scene (bright white desk, real glass, breadboard with holes,
detailed ESP32 DevKit, 5 mm LEDs with legs, OLED graph, rainbow jumper arches, shallow depth of field).
Same timeline as scene3d.py (24 fps, 336 frames), renders into work/frames3d.
Run: python3 edit5/scene3d_real.py [--preview] [--start N --end M --step S]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit2"))
import scene3d as k  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
TEX = os.path.join(HERE, "work", "tex")
OLED = os.path.join(HERE, "work", "oled_real")
FPS, END = 24, 336
SHOTS = [0, 41, 82, 123, 164, 205, 246, 300]
FILL0, FILL1 = 30, 240
G = Vector((0.5, 1.0, 0))          # glass centre
GR, GH = 0.85, 2.6                 # glass radius / height
B = Vector((-0.1, -1.35, 0))       # breadboard centre


def pct(f):
    if f <= FILL0:
        return 12.0
    if f >= FILL1:
        return 100.0
    u = (f - FILL0) / (FILL1 - FILL0)
    return 12 + 88 * (1 - (1 - u) ** 1.6)


def level_z(p):
    return 0.1 + (GH - 0.35) * p / 100


def mat_glass(name, col=(1, 1, 1), ior=1.5, rough=0.0):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Transmission Weight"].default_value = 1.0
        p.inputs["Roughness"].default_value = rough
        p.inputs["IOR"].default_value = ior
        return p
    return k.node_mat(name, b)


def mat_tex(name, path, rough=0.5, metal=0.0):
    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
        return p
    return k.node_mat(name, b)


def textured_plane(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def wire(name, pts, col, r=0.022, plugs=True):
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
    o.data.materials.append(k.pbr(name + "m", col, rough=0.35))
    if plugs:   # black dupont housings at both ends
        for p in (pts[0], pts[-1]):
            k.box(name + "_plug", (0.07, 0.07, 0.24), p + Vector((0, 0, 0.1)), PLUG)


def build(sc):
    global PLUG
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    PLUG = k.pbr("plug", (0.02, 0.02, 0.02), rough=0.4)

    # white desk + soft backdrop
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    bpy.context.object.data.materials.append(k.pbr("desk", (0.86, 0.86, 0.85), rough=0.38))
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 14, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(k.pbr("wall", (0.62, 0.63, 0.65), rough=0.9))
    k.area("soft_key", (-5, -4, 8), (0, 0, 1), 1500, 7)
    k.area("soft_fill", (6, -3, 4), (0, 0, 1), 600, 8)
    k.area("back", (1, 6, 5), G + Vector((0, 0, 1.5)), 700, 4)

    # ---- glass + water + pour stream
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=GR, depth=GH, location=G + Vector((0, 0, GH / 2)),
                                        end_fill_type="NOTHING")
    glass = bpy.context.object
    bpy.ops.object.shade_smooth()
    sol = glass.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.05
    glass.modifiers.new("sub", "SUBSURF").levels = 1
    glass.data.materials.append(mat_glass("glass", ior=1.5))
    k.cyl("glass_base", GR, 0.12, G + Vector((0, 0, 0.06)), mat_glass("glass_base_m", ior=1.5), verts=96)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=GR - 0.06, depth=1, location=(0, 0, 0.5))
    water = bpy.context.object
    bpy.ops.object.shade_smooth()
    bpy.ops.object.transform_apply(location=True)
    water.location = G + Vector((0, 0, 0.12))
    water.data.materials.append(mat_glass("water", (0.78, 0.92, 1.0), ior=1.33))
    k.interp("LINEAR")
    for f in range(0, END + 1, 3):
        water.scale = (1, 1, max(0.02, level_z(pct(f)) - 0.12))
        water.keyframe_insert("scale", frame=f)
    k.interp("BEZIER")
    stream = k.cyl("stream", 0.05, 1, Vector((0, 0, 0)), mat_glass("stream_m", (0.92, 0.97, 1.0), 1.33), verts=24)
    k.interp("LINEAR")
    for f in range(0, END + 1, 3):
        top, bot = GH + 2.5, level_z(pct(f))
        stream.location = G + Vector((-0.3, 0.15, (top + bot) / 2))
        stream.scale = (1 + 0.15 * math.sin(f * 1.7), 1, top - bot)
        stream.keyframe_insert("location", frame=f)
        stream.keyframe_insert("scale", frame=f)
    k.interp("BEZIER")
    k.show(stream, [(FILL0, FILL1)])

    # ---- HC-SR04 clipped on the rim, transducers tilted down into the glass
    # HC-SR04 standing on the front rim, transducers facing the camera (like a real clip-on mount)
    blue = k.pbr("sr_pcb", (0.02, 0.14, 0.5), rough=0.35)
    alu = k.pbr("sr_alu", (0.85, 0.86, 0.88), rough=0.18, metal=1.0)
    meshm = k.pbr("sr_mesh", (0.04, 0.04, 0.05), rough=0.8)
    S0 = G + Vector((0.1, -GR + 0.12, GH + 0.08))
    k.box("sr_board", (1.1, 0.05, 0.5), S0, blue)
    for sx in (-0.28, 0.28):
        k.cyl("sr_can", 0.17, 0.26, S0 + Vector((sx, -0.15, 0)), alu, rot=(math.radians(90), 0, 0))
        k.cyl("sr_face", 0.14, 0.02, S0 + Vector((sx, -0.285, 0)), meshm, rot=(math.radians(90), 0, 0))
    k.box("sr_xtal", (0.16, 0.06, 0.08), S0 + Vector((0, -0.05, -0.15)), alu)
    for i in range(4):
        k.box("sr_pin", (0.03, 0.18, 0.03), S0 + Vector((-0.12 + i * 0.08, 0.1, 0.22)), alu)
    k.text("sr_lbl", "HC-SR04", 0.07, S0 + Vector((0, -0.03, 0.17)), [k.emit("sr_t", (0.9, 0.9, 0.9), 1.0)], extrude=0.0)
    k.box("sr_clip", (0.1, 0.2, 0.3), S0 + Vector((-0.45, 0.08, -0.15)), PLUG)
    k.box("sr_clip2", (0.1, 0.2, 0.3), S0 + Vector((0.55, 0.08, -0.15)), PLUG)
    for i in range(10):   # faint ultrasonic pings
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.008)
        ring = bpy.context.object
        ring.data.materials.append(k.emit(f"ping{i}", (0.3, 0.75, 1.0), 1.0))
        f0 = 44 + i * 4
        surf = level_z(pct(f0 + 10)) + 0.02
        k.interp("LINEAR")
        for ff, z, s in ((f0, GH - 0.3, 0.6), (f0 + 10, surf, 2.4)):
            ring.location = G + Vector((0.1 + 0.28 * (1 if i % 2 else -1), -GR + 0.35, z))
            ring.scale = (s, s, s)
            ring.keyframe_insert("location", frame=ff)
            ring.keyframe_insert("scale", frame=ff)
        k.interp("BEZIER")
        k.show(ring, [(f0, f0 + 11)])

    # ---- breadboard with holes
    k.box("bb_body", (4.2, 1.9, 0.22), B + Vector((0, 0, 0.11)), k.pbr("bb_side", (0.9, 0.89, 0.85), rough=0.6))
    textured_plane("bb_top", (4.2, 1.9), B + Vector((0, 0, 0.222)), mat_tex("bb_tex", os.path.join(TEX, "breadboard.png"), 0.55))

    # ---- ESP32 DevKit (long axis along x), straddling the left half
    E = B + Vector((-1.25, 0.05, 0.22))
    pcb = k.pbr("esp_pcb", (0.025, 0.025, 0.03), rough=0.35)
    gold = k.pbr("gold", (0.92, 0.74, 0.32), rough=0.22, metal=1.0)
    steel = k.pbr("steel", (0.78, 0.79, 0.81), rough=0.2, metal=1.0)
    for s in (-1, 1):
        k.box("esp_hdr", (1.8, 0.09, 0.25), E + Vector((0, s * 0.42, 0.12)), pcb)
    k.box("esp_board", (2.0, 1.0, 0.06), E + Vector((0, 0, 0.28)), pcb)
    for s in (-1, 1):
        for i in range(15):
            k.cyl("esp_pad", 0.035, 0.02, E + Vector((-0.84 + i * 0.12, s * 0.42, 0.315)), gold, verts=12)
    k.box("wroom_pcb", (0.95, 0.68, 0.04), E + Vector((0.45, 0, 0.33)), pcb)
    textured_plane("wroom", (0.68, 0.6), E + Vector((0.38, 0, 0.395)), mat_tex("wroom_m", os.path.join(TEX, "wroom.png"), 0.25, 0.7),
                   rot=(0, 0, math.radians(-90)))
    k.box("wroom_can", (0.7, 0.62, 0.06), E + Vector((0.38, 0, 0.36)), steel)
    k.box("usb", (0.24, 0.3, 0.12), E + Vector((-1.0, 0, 0.36)), steel)
    k.box("cp2102", (0.22, 0.22, 0.05), E + Vector((-0.55, 0.15, 0.33)), k.pbr("chip", (0.05, 0.05, 0.05), 0.4))
    for dy in (-0.3, 0.3):
        k.box("btn", (0.14, 0.12, 0.08), E + Vector((-0.78, dy, 0.34)), steel)
        k.cyl("btn_cap", 0.035, 0.04, E + Vector((-0.78, dy, 0.39)), PLUG, verts=12)
    k.cyl("pwr_led", 0.03, 0.02, E + Vector((-0.5, -0.3, 0.32)), k.emit("pwr", (1.0, 0.1, 0.05), 1.4), verts=12)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.5, location=E + Vector((-2.8, 0, 0.36)),
                                        rotation=(0, math.radians(90), 0))
    bpy.context.object.data.materials.append(k.pbr("usb_cable", (0.02, 0.02, 0.02), rough=0.45))
    k.box("usb_plug", (0.35, 0.22, 0.14), E + Vector((-1.25, 0, 0.36)), k.pbr("usb_plug_m", (0.03, 0.03, 0.03), 0.4))

    # ---- 5 mm LEDs with legs (green / yellow / red)
    f_y = next(f for f in range(END) if pct(f) >= 50)
    f_r = next(f for f in range(END) if pct(f) >= 90)
    for i, (col, on) in enumerate((((0.1, 1.0, 0.25), 0), ((1.0, 0.72, 0.05), f_y), ((1.0, 0.06, 0.04), f_r))):
        L = B + Vector((0.35 + i * 0.32, -0.35, 0.22))
        for dx in (-0.05, 0.05):
            k.box("leg", (0.018, 0.018, 0.45), L + Vector((dx, 0, 0.22)), steel)
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.inputs["Base Color"].default_value = (*col, 1)
            p.inputs["Transmission Weight"].default_value = 0.2
            p.inputs["Roughness"].default_value = 0.15
            p.inputs["Emission Color"].default_value = (*col, 1)
            return p
        m = k.node_mat(f"led{i}", b)
        k.cyl(f"led{i}_body", 0.1, 0.2, L + Vector((0, 0, 0.55)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=L + Vector((0, 0, 0.65)))
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        k.cyl(f"led{i}_rim", 0.115, 0.03, L + Vector((0, 0, 0.46)), m, verts=32)
        em = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        k.interp("CONSTANT")
        for ff, v in ((0, 0.0), (on, 3.5)):
            em.default_value = v
            em.keyframe_insert("default_value", frame=ff)
        bpy.ops.object.light_add(type="POINT", location=L + Vector((0, -0.15, 0.6)))
        lt = bpy.context.object
        lt.data.color = col
        lt.data.shadow_soft_size = 0.05
        for ff, v in ((0, 0.0), (on, 6.0)):
            lt.data.energy = v
            lt.data.keyframe_insert("energy", frame=ff)
        k.interp("BEZIER")

    # ---- 0.96" OLED module standing on the right, tilted toward camera
    O = B + Vector((1.55, -0.2, 0.22))
    oled_root = bpy.data.objects.new("oled_root", None)
    bpy.context.collection.objects.link(oled_root)
    oled_root.location = O
    op = [k.box("oled_pcb", (0.9, 0.06, 0.9), O + Vector((0, 0, 0.5)), k.pbr("oled_pcb_m", (0.03, 0.2, 0.62), rough=0.35)),
          k.box("oled_glass", (0.84, 0.03, 0.46), O + Vector((0, -0.045, 0.56)), k.pbr("oled_blk", (0.01, 0.01, 0.012), rough=0.05))]
    for i in range(4):
        op.append(k.box("oled_pin", (0.03, 0.03, 0.2), O + Vector((-0.12 + i * 0.08, 0, 0.98)), gold))
    for sx in (-0.38, 0.38):
        for sz in (0.12, 0.88):
            op.append(k.cyl("oled_hole", 0.04, 0.07, O + Vector((sx, 0, sz)), steel, rot=(math.radians(90), 0, 0), verts=16))

    def scr_b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "oled_tex"
        tex.image = bpy.data.images.load(os.path.join(OLED, "012.png"))
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.5
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    bpy.ops.mesh.primitive_plane_add(size=1, location=O + Vector((0, -0.062, 0.56)), rotation=(math.radians(90), 0, 0))
    scr = bpy.context.object
    scr.scale = (0.8, 0.4, 1)
    scr.data.materials.append(k.node_mat("oled", scr_b))
    op.append(scr)
    bpy.context.view_layer.update()
    for p in op:
        p.parent = oled_root
        p.matrix_parent_inverse = oled_root.matrix_world.inverted()
    oled_root.rotation_euler = (math.radians(-12), 0, math.radians(-8))
    k.cyl("buzzer", 0.16, 0.2, B + Vector((1.45, 0.55, 0.32)), k.pbr("buzz", (0.03, 0.03, 0.03), 0.45), verts=32)

    # ---- rainbow jumper arches (like a real build)
    rainbow = [(0.35, 0.18, 0.08), (0.95, 0.45, 0.05), (0.98, 0.82, 0.05), (0.1, 0.6, 0.2), (0.1, 0.35, 0.9), (0.5, 0.2, 0.75)]
    for i, col in enumerate(rainbow):
        a = E + Vector((-0.6 + i * 0.12, 0.42, 0.25))
        b_ = B + Vector((0.15 + i * 0.16, 0.45, 0.22))
        wire(f"arch{i}", [a, (a + b_) / 2 + Vector((0, 0.2, 1.2 + i * 0.07)), b_], col)
    for i, col in enumerate(rainbow[1:5]):
        a = E + Vector((0.2 + i * 0.12, -0.42, 0.25))
        b_ = O + Vector((-0.12 + i * 0.08, 0.05, 1.05))
        wire(f"oarch{i}", [a, (a + b_) / 2 + Vector((0, -0.4, 0.9 + i * 0.05)), b_], col)
    # sensor lead: 4 wires up over the rim and down behind the glass to the breadboard
    for i, col in enumerate(((0.95, 0.45, 0.05), (0.5, 0.2, 0.75), (0.1, 0.35, 0.9), (0.02, 0.02, 0.02))):
        a = G + Vector((-0.02 + i * 0.08, -GR + 0.22, GH + 0.32))
        wire(f"sr{i}", [a, G + Vector((-0.3, 0.3, GH + 0.8)), G + Vector((-1.5, 0.7, 1.3)),
                        E + Vector((0.6 + i * 0.12, 0.42, 0.25))], col, plugs=False)

    # ---- cameras with depth of field
    oled_c = O + Vector((0, -0.07, 0.56))
    leds_c = B + Vector((0.67, -0.35, 0.75))
    gtop = G + Vector((0.1, -GR + 0.1, GH + 0.05))
    Sh = SHOTS

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        fo = bpy.data.objects.new(name + "_focus", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    cams = [
        cam("s1", [(Sh[0], Vector((-3.6, -6.8, 4.6)), Vector((0.0, -0.3, 1.1))),
                   (Sh[1], Vector((-3.1, -6.3, 4.3)), Vector((0.0, -0.3, 1.1)))], 32, Vector((0.2, -0.6, 0.8)), 2.8),
        cam("s2", [(Sh[1], gtop + Vector((-1.0, -2.6, 0.9)), gtop + Vector((0, 0.6, -0.5))),
                   (Sh[2], gtop + Vector((-0.6, -2.3, 0.7)), gtop + Vector((0, 0.6, -0.6)))], 38, gtop, 2.0),
        cam("s3", [(Sh[2], G + Vector((4.2, -2.4, 1.9)), G + Vector((0, 0, 1.4))),
                   (Sh[3], G + Vector((3.8, -2.9, 2.1)), G + Vector((0, 0, 1.5)))], 30, G + Vector((0.6, -0.3, 1.3)), 2.2),
        cam("s4", [(Sh[3], oled_c + Vector((0.3, -1.9, 0.45)), oled_c),
                   (Sh[4], oled_c + Vector((-0.1, -1.55, 0.3)), oled_c)], 50, oled_c, 1.6),
        cam("s5", [(Sh[4], leds_c + Vector((-1.0, -2.0, 0.7)), leds_c),
                   (Sh[5], leds_c + Vector((0.5, -1.8, 0.6)), leds_c)], 45, leds_c, 1.6),
        cam("s6", [(Sh[5], gtop + Vector((0.8, -2.3, 0.2)), gtop + Vector((0, 0.3, -0.2))),
                   (Sh[6], gtop + Vector((0.4, -2.0, 0.35)), gtop + Vector((0, 0.3, -0.15)))], 36, gtop + Vector((0, 0.2, 0)), 2.0),
        cam("s7", [(Sh[6], Vector((3.2, -6.2, 3.6)), Vector((0.0, -0.3, 1.2))),
                   (Sh[7], Vector((2.2, -5.8, 3.8)), Vector((0.0, -0.3, 1.2)))], 32, Vector((0.3, -0.6, 0.9)), 2.8),
        cam("s8", [(Sh[7], Vector((-2.4, -6.4, 3.6)), Vector((0.0, -0.3, 1.25))),
                   (END, Vector((-1.6, -5.8, 3.4)), Vector((0.0, -0.3, 1.25)))], 32, Vector((0.2, -0.6, 0.9)), 2.8),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        p = int(round(pct(scene.frame_current)))
        if p not in imgs:
            imgs[p] = bpy.data.images.load(os.path.join(OLED, f"{p:03d}.png"), check_existing=True)
        bpy.data.materials["oled"].node_tree.nodes["oled_tex"].image = imgs[p]
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=END - 1)
    ap.add_argument("--step", type=int, default=1)
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(FRAMES, exist_ok=True)
    sc = k.reset()
    sc.render.fps = FPS
    build(sc)
    k.setup_render(sc, args.preview)
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces, cy.transparent_max_bounces = 12, 10, 4, 8
    cy.samples = 10 if args.preview else 16
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(FRAMES, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
