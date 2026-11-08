#!/usr/bin/env python3
"""Photoreal ESP32 Smart Plant Watering (Blender, procedural, units = cm). Re-uses the ESP32 + 1.3" OLED
breadboard from edit10 on a neutral dark desk; a terracotta pot with a small plant (leaves droop and fade when
dry, perk up when watered), a capacitive soil-moisture probe, a clear water tank with a mini pump and a clear
tube whose end pours a water stream (with drops) onto the soil while the pump runs (planttime). Soil darkens
as it gets wet. Mini breadboard: red LED = pump ON, green LED = soil OK, buzzer. The OLED shows
plantgfx.oled_png(). Writes projected screen / LED / plant / water regions per frame (work/proj) for the
B&W + colour grade. 13 s loop. Run: python3 edit37/scene3d.py [--preview] [--start N --end M --step S]"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from planttime import FPS, N, SHOTS, pump, flow, wet, state  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
PROJ = os.path.join(HERE, "work", "proj")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
b10.OLED = OLED
MB = Vector((1.0, -6.4, 0))
LED_R = MB + Vector((0.6, 0.3, 0.9))
LED_G = MB + Vector((1.6, 0.3, 0.9))
P = Vector((10.5, -2.5, 0))                    # pot centre
POT_H, SOIL_Z = 5.5, 5.0
TANK = Vector((17.5, 0.5, 0))
TUBE_END = P + Vector((1.5, -1.3, 8.2))
PROBE = P + Vector((-2.0, -0.9, 0))
R90 = (math.radians(90), 0, 0)
LEAVES = [(0.2, 3.4, 0), (0.5, 3.3, 130), (0.8, 3.2, 250), (1.4, 3.1, 60), (1.8, 3.0, 190), (2.3, 2.9, 310), (2.9, 2.7, 20),
          (3.4, 2.6, 150), (3.9, 2.4, 270), (4.4, 2.2, 90), (4.9, 2.0, 210), (5.3, 1.8, 330), (5.7, 1.5, 40), (6.0, 1.3, 170)]


def mat_rgb(name, col, rough):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        return p
    return k.node_mat(name, b)


def water_mat(name):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Base Color"].default_value = (0.2, 0.5, 1.0, 1)
        p.inputs["Roughness"].default_value = 0.02
        p.inputs["Transmission Weight"].default_value = 0.6
        p.inputs["IOR"].default_value = 1.33
        p.inputs["Emission Color"].default_value = (0.2, 0.55, 1.0, 1)
        p.inputs["Emission Strength"].default_value = 1.6
        return p
    return k.node_mat(name, b)


def glass_mat(name):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1)
        p.inputs["Roughness"].default_value = 0.03
        p.inputs["Transmission Weight"].default_value = 1.0
        p.inputs["IOR"].default_value = 1.45
        return p
    return k.node_mat(name, b)


def build_pot():
    terra = mat_rgb("terra", (0.62, 0.3, 0.17), 0.8)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=2.5, radius2=3.3, depth=POT_H, location=P + Vector((0, 0, POT_H / 2)))
    pot = bpy.context.object
    pot.data.materials.append(terra)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=3.35, minor_radius=0.28, location=P + Vector((0, 0, POT_H)))
    rim = bpy.context.object
    rim.data.materials.append(terra)
    bpy.ops.object.shade_smooth()
    soil = mat_rgb("soil", (0.42, 0.31, 0.2), 0.95)
    k.cyl("soil", 3.1, 0.2, P + Vector((0, 0, SOIL_Z)), soil, verts=48)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    # plant: stem + leaves on pivots
    leaf_m = mat_rgb("leaf", (0.1, 0.45, 0.08), 0.45)
    stem_m = mat_rgb("stem", (0.18, 0.4, 0.1), 0.5)
    k.cyl("stem", 0.22, 6.6, P + Vector((0, 0, SOIL_Z + 3.3)), stem_m, verts=16)
    pivots = []
    for i, (hz, L, az) in enumerate(LEAVES):
        piv = bpy.data.objects.new(f"leafpiv{i}", None)
        bpy.context.collection.objects.link(piv)
        piv.location = P + Vector((0, 0, SOIL_Z + 0.6 + hz))
        piv.rotation_euler = (0, 0, math.radians(az))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12, location=(L * 0.55, 0, 0))
        lf = bpy.context.object
        lf.scale = (L * 0.55, L * 0.3, 0.07)
        lf.data.materials.append(leaf_m)
        bpy.ops.object.shade_smooth()
        lf.parent = piv
        pivots.append(piv)
    return pivots


def build_probe():
    blk = k.pbr("probe_m", (0.03, 0.03, 0.035), 0.35)
    k.box("probe_blade", (1.0, 0.12, 6.0), PROBE + Vector((0, 0, SOIL_Z - 0.6)), blk)
    k.box("probe_head", (1.6, 0.18, 1.6), PROBE + Vector((0, 0, SOIL_Z + 3.0)), blk)
    k.box("probe_chip", (0.5, 0.06, 0.5), PROBE + Vector((0, -0.12, SOIL_Z + 3.1)), k.pbr("chip", (0.1, 0.1, 0.1), 0.4))
    k.text("probe_lbl", "MOISTURE", 0.16, PROBE + Vector((0, -0.11, SOIL_Z + 2.45)), [k.emit("probe_t", (0.95, 0.95, 0.95), 0.9)], extrude=0.0, rot=R90)
    for i, col in enumerate(((0.85, 0.1, 0.05), (0.04, 0.04, 0.04), (0.95, 0.95, 0.95))):
        a = PROBE + Vector((-0.4 + 0.4 * i, 0.1, SOIL_Z + 3.8))
        e = Vector((b10.E.x + 0.3 + i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_probe{i}", b10.bez(a, a + Vector((-2.0, 0.8, 1.5)), e + Vector((2.0, 1.5, 3.0)), e), col, r=0.05)


def build_tank():
    glass = glass_mat("tank_glass")
    t = 0.15
    W_, D_, H_ = 4.0, 4.0, 6.5
    k.box("tank_bot", (W_, D_, t), TANK + Vector((0, 0, t / 2)), glass)
    for sx in (-1, 1):
        k.box("tank_s", (t, D_, H_), TANK + Vector((sx * (W_ - t) / 2, 0, H_ / 2)), glass)
    for sy in (-1, 1):
        k.box("tank_fb", (W_, t, H_), TANK + Vector((0, sy * (D_ - t) / 2, H_ / 2)), glass)
    k.box("tank_water", (W_ - 2 * t - 0.02, D_ - 2 * t - 0.02, 4.4), TANK + Vector((0, 0, t + 2.2)), water_mat("tank_water_m"))
    k.cyl("pump", 0.7, 1.4, TANK + Vector((0, 0, t + 0.7)), k.pbr("pump_m", (0.04, 0.04, 0.045), 0.4), verts=24)
    tube_pts = b10.bez(TANK + Vector((0, 0, 1.6)), TANK + Vector((0, 0, 10.0)), TUBE_END + Vector((0, 0, 4.5)), TUBE_END)
    b10.poly_wire("tube", tube_pts, (0.95, 0.97, 1.0), r=0.2)
    bpy.data.objects["tube"].data.materials.clear()
    bpy.data.objects["tube"].data.materials.append(glass)
    b10.poly_wire("tube_water", tube_pts, (0.3, 0.6, 1.0), r=0.12)
    tw = bpy.data.objects["tube_water"]
    tw.data.materials.clear()
    tw.data.materials.append(water_mat("tube_water_m"))
    # water stream from the tube end to the soil + falling drops
    L = TUBE_END.z - SOIL_Z - 0.1
    k.cyl("stream", 0.2, L, TUBE_END + Vector((0, 0, -L / 2)), water_mat("stream_m"), verts=16)
    drops = []
    for i in range(7):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.17, segments=12, ring_count=8, location=TUBE_END)
        dr = bpy.context.object
        dr.data.materials.append(bpy.data.materials["stream_m"])
        bpy.ops.object.shade_smooth()
        drops.append(dr)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.05, location=Vector((TUBE_END.x, TUBE_END.y, SOIL_Z + 0.13)))
    ring = bpy.context.object
    ring.data.materials.append(bpy.data.materials["stream_m"])
    return tw, bpy.data.objects["stream"], drops, ring


def build_side():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    steel = bpy.data.materials["steel"]
    blk = bpy.data.materials["esp_blk"]
    for name, c, col in (("led_r", LED_R, (1.0, 0.06, 0.03)), ("led_g", LED_G, (0.1, 1.0, 0.2))):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.name = "P"
            p.inputs["Base Color"].default_value = (*[0.02 + 0.2 * v for v in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.35
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        k.cyl(name + "_rim", 0.33, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        k.cyl(name + "_body", 0.29, 0.5, c + Vector((0, 0, 0.88)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.29, location=c + Vector((0, 0, 1.13)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), steel)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.7)))
        gl = bpy.context.object
        gl.name = name + "_glow"
        gl.data.color = col
        gl.data.shadow_soft_size = 0.2
        gl.data.energy = 0.0
    k.box("relay", (2.2, 1.6, 1.0), MB + Vector((3.0, 0.2, 1.4)), k.pbr("relay_m", (0.05, 0.15, 0.6), 0.35))
    for i, (a, col) in enumerate(((LED_R + Vector((0, 1.0, 0)), (0.85, 0.1, 0.05)), (LED_G + Vector((0, 1.0, 0)), (0.1, 0.7, 0.2)),
                                   (MB + Vector((3.0, 1.0, 1.4)), (0.4, 0.2, 0.7)))):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.25
    b10.plane("desk", (300, 300), Vector((0, 0, 0)), k.pbr("desk_m", (0.16, 0.15, 0.14), rough=0.7))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-15, -45, 70), (9, -2, 4), 70000, 32)
    k.area("fill", (55, -35, 40), (9, -2, 4), 14000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (9, 0, 4), 25000, 25, col=(0.8, 0.8, 1.0))
    b10.build_board()
    bpy.data.materials["blue_led"].node_tree.animation_data_clear()
    pivots = build_pot()
    build_probe()
    tube_water, stream, drops, ring = build_tank()
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
    pc = P + Vector((0, 0, 7.0))
    p0 = pc + Vector((-7.5, -17.0, 6.0))
    p1 = pc + Vector((-6.5, -15.0, 5.2))
    look0 = pc + Vector((0.5, 0, -0.5))
    wide_c = Vector((9.0, -1.0, 4.0))
    cams = [
        cam("s0", [(Sh[0], p0, look0), (Sh[1], p1, look0)], 36, pc, 4.0),
        cam("s1", [(Sh[1], scr + Vector((0.6, -9.6, 8.6)), scr + Vector((0, 0.9, 0.6))), (Sh[2], scr + Vector((0.1, -8.8, 7.9)), scr + Vector((0, 0.9, 0.6)))], 42, scr, 4.0),
        cam("s2", [(Sh[2], TUBE_END + Vector((7.0, -11.0, 2.0)), TUBE_END + Vector((-0.5, 0, -2.2))),
                   (Sh[3], TUBE_END + Vector((6.0, -9.5, 1.5)), TUBE_END + Vector((-0.5, 0, -2.2)))], 40, TUBE_END + Vector((0, 0, -2)), 3.5),
        cam("s3", [(Sh[3], pc + Vector((-3.0, -14.0, 1.5)), pc + Vector((0, 0, 0.5))), (Sh[4], pc + Vector((-2.2, -12.5, 1.8)), pc + Vector((0, 0, 0.5)))], 36, pc, 3.5),
        cam("s4", [(Sh[4], wide_c + Vector((-2, -34, 24)), wide_c), (Sh[5], wide_c + Vector((-1, -31, 22)), wide_c)], 34, wide_c, 8.0),
        cam("s5", [(Sh[5], p1, look0), (N, p0, look0)], 36, pc, 4.0),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]
    imgs = {}
    os.makedirs(PROJ, exist_ok=True)
    scr_obj = bpy.data.objects["oled_screen"]
    soil_p = bpy.data.materials["soil"].node_tree.nodes["P"]
    leaf_p = bpy.data.materials["leaf"].node_tree.nodes["P"]

    def upd(scene, *_):
        f = scene.frame_current
        ff = min(max(f, 0), N - 1)
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(OLED, f"{ff:04d}.png"), check_existing=True)
        bpy.data.materials["oled_scr"].node_tree.nodes["oled_tex"].image = imgs[f]
        wv = wet(ff)
        dry_c, wet_c = (0.42, 0.31, 0.2), (0.1, 0.06, 0.035)
        soil_p.inputs["Base Color"].default_value = (*[a + (b_ - a) * wv for a, b_ in zip(dry_c, wet_c)], 1)
        soil_p.inputs["Roughness"].default_value = 0.95 - 0.55 * wv
        ld, lw = (0.36, 0.33, 0.12), (0.07, 0.42, 0.06)
        leaf_p.inputs["Base Color"].default_value = (*[a + (b_ - a) * wv for a, b_ in zip(ld, lw)], 1)
        for i, piv in enumerate(pivots):
            droop = math.radians(58 - 6 * i) * (1 - wv) - math.radians(18) * wv
            piv.rotation_euler = (0, droop, math.radians(LEAVES[i][2]) + 0.05 * math.sin(ff * 0.07 + i))
        fl = flow(ff)
        stream.hide_render = fl < 0.02
        stream.scale = (max(0.05, fl), max(0.05, fl), 1)
        tube_water.hide_render = not pump(ff)
        L = TUBE_END.z - SOIL_Z
        for i, dr in enumerate(drops):
            ph = ((ff * 0.11 + i / len(drops)) % 1.0)
            dr.hide_render = fl < 0.3
            dr.location = TUBE_END + Vector((0.25 * math.sin(i * 2.3), 0.25 * math.cos(i * 1.7), -L * ph * ph))
        ring.hide_render = fl < 0.3
        ring.scale = (1 + 0.6 * ((ff * 0.15) % 1), 1 + 0.6 * ((ff * 0.15) % 1), 1)
        on = pump(ff)
        ok = state(ff) == "WET"
        for name, lit in (("led_r", on), ("led_g", ok)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if lit else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if lit else 0.0
        bl = bpy.data.materials["blue_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        bl.default_value = 22.0 if on else 0.0
        ci = max(i for i, s in enumerate(Sh) if s <= ff)
        cm = cams[ci]
        scene.camera = cm
        bpy.context.view_layer.update()

        def px(p):
            x, y = world_to_camera_view(scene, cm, p)[:2]
            return [x * 1080, (1 - y) * 1920]
        mw = scr_obj.matrix_world
        pts = {"screen": [px(mw @ v.co) for v in scr_obj.data.vertices], "led_r": px(LED_R + Vector((0, 0, 1.0))),
               "led_g": px(LED_G + Vector((0, 0, 1.0)))}
        a, b_ = px(LED_R + Vector((0, 0, 1.0))), px(LED_R + Vector((1.0, 0, 1.0)))
        pts["cm_px"] = abs(b_[0] - a[0])
        # plant / water regions: projected 3D boxes -> 2D bounding boxes
        def bbox(c0, c1):
            xs, ys = [], []
            for xx in (c0.x, c1.x):
                for yy in (c0.y, c1.y):
                    for zz in (c0.z, c1.z):
                        q = px(Vector((xx, yy, zz)))
                        xs.append(q[0])
                        ys.append(q[1])
            return [min(xs), min(ys), max(xs), max(ys)]
        pts["plant"] = bbox(P + Vector((-5, -5, SOIL_Z + 0.2)), P + Vector((5, 5, SOIL_Z + 9.5)))
        pts["water"] = bbox(TANK + Vector((-2.2, -2.2, 0)), TANK + Vector((2.2, 2.2, 11)))
        pts["tube"] = bbox(Vector((TUBE_END.x - 1, P.y - 1, SOIL_Z)), Vector((TANK.x + 2.2, TANK.y + 2.2, 13.5)))
        with open(os.path.join(PROJ, f"{ff:04d}.json"), "w") as fh:
            json.dump(pts, fh)
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
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 10, 8, 3
    cy.transparent_max_bounces = 16
    cy.samples = 8 if args.preview else 14
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = 33 if args.preview else 100
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
