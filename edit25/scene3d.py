#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + MQ-2 gas-leak alarm (Blender, procedural, units = cm). Re-uses the ESP32 +
1.3" OLED breadboard from edit10 (same channel look); adds an MQ-2 module (glowing heater mesh) on a
stand, a small red LPG cylinder whose valve releases translucent gas puffs that drift to the sensor
(timeline.leak() / gas()), a 5V exhaust fan that spins up on the alarm and blows the gas away, a
KY-040 knob that sets the limit and a red ALARM / green SAFE LED pair + buzzer. Native 1080x1920.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, knob, leak, gas, alarm, fan, fan_angle, busy  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX25 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
D = Vector((1.6, 5.4, 0))                      # MQ-2 stand centre
MQC = D + Vector((0.3, 0.1, 3.2))              # sensor dome (camera target)
CYL = D + Vector((5.2, 0.6, 0))                # LPG cylinder
VALVE = CYL + Vector((0.3, 0, 4.7))
FAN = D + Vector((-4.8, 1.4, 0))               # 5V exhaust fan
PUFFS = 16
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def build_mq2():
    blk = bpy.data.materials["esp_blk"]
    gold = bpy.data.materials["gold"]
    steel = bpy.data.materials["steel"]
    k.box("mq_stand", (3.2, 2.6, 0.9), D + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mq_stand_top", (3.2, 2.6), D + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    pcb = D + Vector((0, 0, 0.9 + 0.62))
    k.box("mq_pcb", (3.2, 2.2, 0.12), pcb, k.pbr("mq_pcb_m", (0.02, 0.1, 0.4), 0.35))
    k.text("mq_lbl", "MQ-2", 0.3, pcb + Vector((-0.95, -0.85, 0.065)), [k.emit("mq_silk", (0.95, 0.95, 0.95), 1.0)], extrude=0.0, rot=(0, 0, 0))
    k.cyl("mq_base", 1.0, 0.5, pcb + Vector((0.3, 0.1, 0.3)), k.pbr("mq_bake", (0.55, 0.45, 0.35), 0.6), verts=48)
    k.cyl("mq_can", 0.95, 1.1, pcb + Vector((0.3, 0.1, 1.05)), steel, verts=48)

    def mesh(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        ch = nt.nodes.new("ShaderNodeTexChecker")
        ch.inputs["Scale"].default_value = 60.0
        ch.inputs["Color1"].default_value = (0.55, 0.56, 0.58, 1)
        ch.inputs["Color2"].default_value = (0.03, 0.03, 0.035, 1)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Metallic"].default_value = 0.8
        p.inputs["Roughness"].default_value = 0.35
        p.inputs["Emission Color"].default_value = (1.0, 0.35, 0.08, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        nt.links.new(tc.outputs["Object"], ch.inputs["Vector"])
        nt.links.new(ch.outputs["Color"], p.inputs["Base Color"])
        return p
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.95, location=pcb + Vector((0.3, 0.1, 1.6)), segments=48, ring_count=24)
    dome = bpy.context.object
    dome.scale = (1, 1, 0.35)
    bpy.ops.object.shade_smooth()
    dome.data.materials.append(k.node_mat("mq_mesh", mesh))
    k.cyl("mq_pot", 0.25, 0.25, pcb + Vector((-1.15, 0.55, 0.18)), k.pbr("mq_pot_m", (0.15, 0.3, 0.9), 0.4), verts=24)
    for name, x in (("mq_led_pwr", -1.1), ("mq_led_do", -0.7)):
        k.box(name, (0.18, 0.12, 0.08), pcb + Vector((x, -0.55, 0.1)),
              k.pbr(name + "_m", (0.3, 0.02, 0.02), 0.3, em=(1.0, 0.1, 0.05), ems=8.0 if name == "mq_led_pwr" else 0.0))
    for i in range(4):
        x = pcb.x - 0.38 + i * 0.254
        k.box("mq_pin", (0.064, 0.064, 0.62), Vector((x, pcb.y + 1.0, 0.9 + 0.31)), gold)
        k.box("mq_hdr", (0.25, 0.25, 0.25), Vector((x, pcb.y + 1.0, 0.9 + 0.13)), blk)
    for i, col in enumerate(((0.85, 0.08, 0.05), (0.04, 0.04, 0.04), (0.1, 0.6, 0.2), (1.0, 0.8, 0.05))):
        a = Vector((D.x - 1.3, pcb.y + (i - 1.5) * 0.254, 0.9))
        e = Vector((b10.E.x - 0.7 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_mq{i}", b10.bez(a, a + Vector((-0.6, 0, 1.4)), e + Vector((0, 0.8, 1.6)), e), col, r=0.05)


def build_cylinder():
    red = k.pbr("lpg_red", (0.75, 0.05, 0.04), 0.25)
    steel = bpy.data.materials["steel"]
    k.cyl("lpg_body", 1.4, 3.6, CYL + Vector((0, 0, 1.9)), red, verts=64)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.4, location=CYL + Vector((0, 0, 3.7)), segments=48, ring_count=24)
    top = bpy.context.object
    top.scale = (1, 1, 0.45)
    bpy.ops.object.shade_smooth()
    top.data.materials.append(red)
    k.cyl("lpg_foot", 1.3, 0.25, CYL + Vector((0, 0, 0.12)), k.pbr("lpg_foot_m", (0.05, 0.05, 0.05), 0.5), verts=48)
    k.cyl("lpg_neck", 0.35, 0.5, CYL + Vector((0, 0, 4.35)), steel, verts=24)
    k.cyl("lpg_valve", 0.5, 0.3, CYL + Vector((0, 0, 4.7)), k.pbr("lpg_valve_m", (0.9, 0.7, 0.1), 0.3, 1.0), verts=24)
    k.cyl("lpg_nozzle", 0.12, 0.7, VALVE + Vector((0.2, 0, 0)), steel, rot=(0, math.radians(90), 0), verts=16)
    k.text("lpg_lbl", "LPG", 0.7, CYL + Vector((0, -1.42, 2.1)), [k.emit("lpg_t", (1, 1, 1), 1.2)], extrude=0.0)
    for j in range(PUFFS):
        def b(nt):
            pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
            pr.inputs["Base Color"].default_value = (0.82, 0.92, 0.8, 1)
            pr.inputs["Roughness"].default_value = 0.9
            pr.inputs["Emission Color"].default_value = (0.75, 0.9, 0.7, 1)
            pr.inputs["Emission Strength"].default_value = 0.15
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.name = "MIX"
            mx.inputs["Fac"].default_value = 0.0
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(pr.outputs[0], mx.inputs[2])
            return mx
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=3, location=VALVE)
        o = bpy.context.object
        o.name = f"puff{j}"
        bpy.ops.object.shade_smooth()
        o.data.materials.append(k.node_mat(f"puff{j}_m", b))
        o.visible_shadow = False


def puff_state(f, j):
    """(location, radius, alpha) of gas puff j."""
    u = ((f * 0.022) + j / PUFFS) % 1.0
    g = gas(f)
    lk = leak(f)
    src, dst = VALVE + Vector((0.6, 0, 0)), MQC + Vector((0, 0, 0.4))
    blow = fan(f)
    p = src.lerp(dst, min(1.0, u * 1.3)) + Vector((-6.0 * blow * u * u, 0.6 * math.sin(j * 2.1 + f * 0.05), 1.6 * u + 0.4 * math.sin(f * 0.08 + j)))
    r = 0.35 + 1.1 * u + 0.15 * math.sin(j * 1.7)
    a = 0.4 * max(lk * (1 - u) ** 0.5, g * 0.9) * math.sin(math.pi * u)
    return p, r, a


def build_fan():
    blk = k.pbr("fan_blk", (0.03, 0.03, 0.035), 0.45)
    k.box("fan_stand", (1.0, 1.4, 1.6), FAN + Vector((0, 0.3, 0.8)), bpy.data.materials["bb_side"])
    root = bpy.data.objects.new("fan_root", None)
    bpy.context.collection.objects.link(root)
    root.location = FAN + Vector((0, 0, 3.4))
    root.rotation_euler = (math.radians(75), 0, math.radians(-40))       # face the camera, aimed at the gas
    before = set(bpy.data.objects)
    k.box("fan_frame", (4.0, 4.0, 1.0), Vector((0, 0, 0)), blk)
    k.cyl("fan_hole", 1.85, 1.05, Vector((0, 0, 0)), k.pbr("fan_hole_m", (0.0, 0.0, 0.0), 0.9), verts=64)
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    hub = bpy.data.objects.new("fan_hub", None)
    bpy.context.collection.objects.link(hub)
    hub.parent = root
    b0 = set(bpy.data.objects)
    k.cyl("hub_c", 0.6, 1.1, Vector((0, 0, 0)), blk, verts=32)
    k.text("fan_lbl", "5V", 0.35, Vector((0, 0, 0.56)), [k.emit("fan_t", (0.9, 0.9, 0.95), 0.8)], extrude=0.0, rot=(0, 0, 0))
    for i in range(7):
        a = i * 2 * math.pi / 7
        k.box("blade", (1.3, 0.55, 0.06), Vector((1.15 * math.cos(a), 1.15 * math.sin(a), 0)), k.pbr("blade_m", (0.06, 0.06, 0.07), 0.4),
              rot=(math.radians(25), 0, a))
    for o in [o for o in bpy.data.objects if o not in b0]:
        o.parent = hub
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        hub.rotation_euler = (0, 0, -math.radians(fan_angle(max(f, 0))))
        hub.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    for i, col in enumerate(((0.85, 0.08, 0.05), (0.04, 0.04, 0.04))):
        a = FAN + Vector((0.4, -0.4 + i * 0.3, 1.6))
        e = Vector((b10.E.x - 2.2 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_fan{i}", b10.bez(a, a + Vector((0.5, -0.8, 1.0)), e + Vector((0, 0.8, 1.6)), e), col, r=0.05)


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
    build_mq2()
    build_controls()
    build_cylinder()
    build_fan()

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
    game = Vector((1.6, -0.3, 1.4))                   # OLED + MQ-2 + cylinder + fan
    kn = Vector((0.6, -3.6, 1.6))                     # knob + OLED
    cams = [
        cam("s0", [(Sh[0], Vector((2.6, -15, 19)), game), (Sh[1], Vector((2.0, -13.5, 17.5)), game)], 35, game, 5.6),
        cam("s1", [(Sh[1], Vector((0.8, -12, 25)), mid1), (Sh[2], Vector((0.8, -11, 23)), mid1)], 32, mid1, 8.0),
        cam("s2", [(Sh[2], MQC + Vector((3.0, -11.0, 8.0)), MQC + Vector((0.6, 0, 0.3))), (Sh[3], MQC + Vector((1.8, -10.0, 7.2)), MQC + Vector((0.6, 0, 0.3)))], 40, MQC, 2.8),
        cam("s3", [(Sh[3], kn + Vector((-2.0, -11, 11)), kn), (Sh[4], kn + Vector((-1.0, -10, 10)), kn)], 40, kn, 4.0),
        cam("s4", [(Sh[4], Vector((0.8, -15, 19)), game), (Sh[5], Vector((1.8, -13.5, 17)), game)], 35, game, 5.6),
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
        for name, on in (("led_r", h and (ff // 4) % 2 == 0), ("led_g", not h)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        bpy.data.materials["mq_led_do_m"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 8.0 if h else 0.0
        bpy.data.materials["mq_mesh"].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 2.5 * gas(ff)
        for j in range(PUFFS):
            o = bpy.data.objects[f"puff{j}"]
            loc, r, a = puff_state(ff, j)
            o.location = loc
            o.scale = (r, r, r * 0.8) if a > 0.01 else (0.001, 0.001, 0.001)
            bpy.data.materials[f"puff{j}_m"].node_tree.nodes["MIX"].inputs["Fac"].default_value = a
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
    cy.samples = 8 if args.preview else 12
    cy.transparent_max_bounces = 64
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920          # native HD (no upscale)
    sc.render.resolution_percentage = 33 if args.preview else 100
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
