"""I7 Cycles renders. blender -b -P scenes.py -- <scene> <out.png> [samples]
scenes: usb_cutaway | usb_closeup | bay | module_bay"""
import bpy, sys, math, os, glob
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; SCN, OUTP = a[0], a[1]; SMP = int(a[2]) if len(a) > 2 else 128
S = 0.001; ST = "/workspace/psu-tester-case/cad_I7/stl"; RD = f"{ST}/render"
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def lin(h): c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]; return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
MT = {}
def mat(col, rough=0.5, metal=0.0, coat=0.0, alpha=1.0):
    k = (col, rough, metal, coat, alpha)
    if k in MT: return MT[k]
    m = bpy.data.materials.new(str(k)); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if alpha < 1: b.inputs["Alpha"].default_value = alpha; m.blend_method = 'BLEND'
    MT[k] = m; return m
def imp(f, m, smooth=35, bevel=None):
    if not os.path.exists(f): print("MISSING", f); return None
    bpy.ops.wm.stl_import(filepath=f, global_scale=S); o = bpy.context.selected_objects[0]
    o.data.materials.append(m)
    if smooth: bpy.ops.object.shade_auto_smooth(angle=math.radians(smooth))
    return o
IV, CH, OR = mat("E3DED0", 0.5), mat("232325", 0.6), mat("FF6A13", 0.45)
def printed(sfx="_world", which=("I7_base", "I7_top", "I7_crown", "I7_retainer"), d=ST):
    cm = {"I7_base": CH, "I7_top": IV, "I7_crown": OR, "I7_retainer": mat("2A2A2C", 0.6)}
    for k in which: imp(f"{d}/{k}{sfx}.stl", cm[k])
def pcb():
    imp(f"{ST}/REF_PCB_RevD2_board.stl", mat("0E0F10", 0.32, coat=0.3))
    imp(f"{RD}/PCB_silk.stl", mat("EDEDE6", 0.6), smooth=0); imp(f"{RD}/PCB_pads.stl", mat("C9C9C4", 0.25, 1.0), smooth=0); imp(f"{RD}/PCB_copper.stl", mat("C9C9C4", 0.3, 1.0), smooth=0)
    C = dict(dark=mat("161616", 0.45), metal=mat("C8C8C8", 0.25, 1.0), green=mat("0E6A2A", 0.42), white=mat("EFEDE2", 0.5), brown=mat("6B4A3A", 0.5))
    for f in glob.glob(f"{RD}/REF_PCB_*__*.stl"): imp(f, C[f.split("__")[1][:-4]])
def module(cut=False):
    imp(f"{RD}/display_PCB.stl", mat("1B2238", 0.4, coat=0.2)); imp(f"{RD}/display_LCM.stl", mat("050607", 0.06, coat=1.0)); imp(f"{RD}/display_parts.stl", mat("2A2A2E", 0.4, 0.4))
WC = ["C0392B", "1A1A1A", "E67E22", "F1C40F", "27AE60", "2980B9", "8E44AD", "7F8C8D", "ECF0F1", "8B4513", "E91E63", "16A085"]
def cable12(ext=False):
    imp(f"{ST}/REF_cable_12pin_7mm.stl", mat("141414", 0.5))
    for i in range(12): imp(f"{RD}/conductor_{i:02d}.stl", mat(WC[i], 0.34, coat=0.25), smooth=60)     # I7b satin PVC
    imp(f"{ST}/REF_ferrule_pins_0.314in_x12.stl", mat("D3CFC6", 0.27, 1.0), smooth=50); imp(f"{ST}/REF_ferrule_collars_green_x12.stl", mat("1E9E3A", 0.33, coat=0.2), smooth=50)
    imp(f"{RD}/ferrule_strands.stl", mat("B87333", 0.35, 1.0)); imp(f"{RD}/cable_foil.stl", mat("D0D2D6", 0.22, 1.0), smooth=0); imp(f"{RD}/cable_filler.stl", mat("EEEADF", 0.9))
    if ext: imp(f"{ST}/REF_cable_12pin_7mm_external.stl", mat("141414", 0.5)); imp(f"{ST}/REF_HR10A-10P-12S(73)_female_plug.stl", mat("C9CCD1", 0.22, 1.0))
def tie():
    imp(f"{ST}/REF_zip_tie_2.5mm_centre.stl", mat("F1EFE8", 0.45), smooth=30)
def harness():
    imp(f"{ST}/REF_harness_5x_1pin_housing_d1.2.stl", mat("111111", 0.45)); imp(f"{ST}/REF_harness_5_wires_to_J4.stl", mat("C0392B", 0.45))
    imp(f"{ST}/REF_harness_5x_breadboard_pins_0.64sq.stl", mat("D4AF37", 0.25, 1.0)); imp(f"{ST}/REF_J4_XH5_plug.stl", mat("F2F0E6", 0.5))
def usb():
    imp(f"{RD}/usb_male_body.stl", mat("111113", 0.42)); imp(f"{RD}/usb_male_shell.stl", mat("C8C8CC", 0.2, 1.0), smooth=40)
    imp(f"{RD}/usb_ribbon.stl", mat("2B2B2E", 0.5, coat=0.15)); imp(f"{RD}/usb_female_body.stl", mat("111113", 0.42))
    imp(f"{RD}/usb_female_shell.stl", mat("C8C8CC", 0.2, 1.0), smooth=40); imp(f"{RD}/usb_female_tongue.stl", mat("0A0A0A", 0.5))
def hw():
    imp(f"{ST}/REF_grommet_foot_x4.stl", mat("151515", 0.7)); imp(f"{ST}/REF_screw_M2.5x12_PCB_x4.stl", mat("1A1A1A", 0.5))
def floor(z, col="B9B9B5", size=3):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z*S)); bpy.context.object.data.materials.append(mat(col, 0.65))
def world(col="E8E8E6", s=0.08):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin(col), 1); bg.inputs[1].default_value = s
def area(name, loc, energy, size, look):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; ob = bpy.data.objects.new(name, l); sc.collection.objects.link(ob)
    ob.location = Vector(loc)*S; ob.rotation_euler = (Vector(look)*S - ob.location).to_track_quat('-Z', 'Y').to_euler()
def cam(look, az, el, dist, lens=50, focus=None, fstop=None, ortho=None, W=1600, H=1000):
    cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
    A, E = math.radians(az), math.radians(el); L = Vector(look)*S
    co.location = L + Vector((math.sin(A)*math.cos(E), -math.cos(A)*math.cos(E), math.sin(E)))*dist
    co.rotation_euler = (L - co.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens; cd.clip_start = 0.002; cd.clip_end = 10
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    if focus is not None:
        cd.dof.use_dof = True; cd.dof.focus_distance = (Vector(focus)*S - co.location).length; cd.dof.aperture_fstop = fstop
    sc.render.resolution_x, sc.render.resolution_y = W, H
    return co
def cam_dir(look, view_dir, up, dist, ortho, W=1600, H=1000):
    cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
    L = Vector(look)*S; d = Vector(view_dir).normalized(); co.location = L - d*dist
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler() if up is None else (d).to_track_quat('-Z', 'Y').to_euler()
    cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_start = 0.001; cd.clip_end = 10
    sc.render.resolution_x, sc.render.resolution_y = W, H
    return co
G = (0.0, -10.0, 59.88); AF = (0.0, -0.6428, 0.7660); UF = (0.0, 0.7660, 0.6428)
def mp(x, u, aa): return tuple(G[i] + x*(1 if i == 0 else 0) + u*UF[i] + aa*AF[i] for i in range(3))
if SCN == "usb_cutaway":
    printed("_cutx0", d=RD); pcb(); module(); usb(); harness(); cable12()
    floor(-2.0); world(s=0.35)
    look = (0, 4, 34)
    area("key", (-260, -180, 300), 6.0, 0.35, look); area("fill", (-250, 200, 120), 2.0, 0.6, look); area("top", (-60, 0, 400), 3.0, 0.8, look)
    cam(look, -90, 14, 0.26, lens=50, focus=mp(0, -25, -9), fstop=5.6)
elif SCN == "usb_closeup":
    usb(); floor(26.5, "9A9A96"); world("D8D8D6", 0.06)
    look = (0, 6, 31)
    area("key", (-160, -140, 220), 1.1, 0.25, look); area("rim", (120, 220, 160), 1.4, 0.3, look); area("fill", (220, -160, 90), 0.35, 0.5, look)
    cam(look, -50, 22, 0.20, lens=55, focus=mp(0, -25, -9), fstop=6.3)
elif SCN == "bay":
    printed(which=("I7_base", "I7_retainer")); pcb(); module(); usb(); harness(); hw(); cable12(ext=False); tie()
    floor(-2.0); world(s=0.1)
    look = (2, -18, 16)
    area("key", (-200, -260, 360), 6.0, 0.4, look); area("fill", (260, -120, 200), 2.0, 0.6, look); area("top", (0, 0, 450), 2.5, 0.9, look)
    cam(look, -20, 38, 0.30, lens=45, focus=(0, -24, 17.9), fstop=8)
elif SCN == "module_bay":
    imp(f"{RD}/I7_top_cutmod.stl", IV); imp(f"{RD}/I7_crown_cutmod.stl", OR); imp(f"{RD}/display_PCB_cutmod.stl", mat("1B2238", 0.4))
    world("FFFFFF", 0.35)
    look = mp(0, -1.5, -2.6)
    area("key", tuple(G[i] - 220*AF[i] + 60*UF[i] - (60 if i == 0 else 0) for i in range(3)), 3.0, 0.5, look)
    area("cam", tuple(G[i] - 300*AF[i] for i in range(3)), 3.0, 0.3, look)
    cam_dir(look, AF, None, 0.3, 0.062, W=1400, H=1400)
elif SCN.startswith("trench") or SCN == "bay_routing":
    TY = -18.65
    look = (3, TY, 4)
    world("E8E8E6", 0.25); floor(-0.01, "B9B9B5")
    if SCN == "trench_top":
        imp(f"{ST}/I7_base_world.stl", CH)
        area("key", (-60, TY - 80, 300), 3.0, 0.5, look); area("top", (0, TY, 400), 4.0, 0.6, look)
        cam_dir((3, -19.0, 0), (0, 0, -1), None, 0.3, 0.075, W=1200, H=1000)
    elif SCN in ("trench_sec", "trench_sec_tie"):
        imp(f"{RD}/I7_base_cutTY.stl", CH, smooth=0); imp(f"{RD}/I7_base_cutTY_cap.stl", mat("8C8C90", 0.7), smooth=0)     # section face lighter
        if SCN == "trench_sec_tie":
            imp(f"{RD}/cable_cutTY.stl", mat("141414", 0.5), smooth=30); imp(f"{RD}/cable_cutTY_cap.stl", mat("3A3A3C", 0.8), smooth=0)
            imp(f"{RD}/tie_cutTY.stl", mat("F1EFE8", 0.45), smooth=0); imp(f"{RD}/tie_cutTY_cap.stl", mat("E8C35A", 0.6), smooth=0)
        lk = (3.0, TY, 5.0)
        area("key", (-120, TY - 220, 160), 3.5, 0.5, lk); area("fill", (160, TY - 150, 90), 1.4, 0.6, lk); area("top", (0, TY, 300), 2.0, 0.6, lk)
        cam(lk, -14, 24, 0.045, lens=60, W=1200, H=1000)
    elif SCN == "trench_tie":
        imp(f"{ST}/I7_base_world.stl", CH); imp(f"{ST}/REF_cable_12pin_7mm.stl", mat("141414", 0.5)); tie()
        lk = (3, TY, 5)
        area("key", (-160, TY - 200, 260), 4.0, 0.5, lk); area("fill", (200, TY - 60, 120), 1.5, 0.6, lk); area("top", (0, TY, 350), 2.5, 0.8, lk)
        cam(lk, 35, 34, 0.08, lens=50, W=1200, H=1000)
    else:   # bay_routing: PCB ghosted, shows the real routing to J1-J3 and the centred tie
        imp(f"{ST}/I7_base_world.stl", CH); cable12(); tie(); hw()
        imp(f"{ST}/REF_PCB_RevD2_board.stl", mat("0E0F10", 0.3, alpha=0.12))
        for k in ("J1", "J2", "J3"): imp(f"{ST}/REF_PCB_{k}_XY350V_4p.stl", mat("0E6A2A", 0.42))
        lk = (8, -8, 8)
        area("key", (-200, -260, 360), 5.0, 0.5, lk); area("fill", (260, -120, 200), 2.0, 0.6, lk); area("top", (0, 0, 450), 3.0, 0.9, lk)
        cam(lk, -25, 52, 0.25, lens=45, focus=(5, -15, 8), fstop=11)
sc.render.engine = 'CYCLES'; sc.cycles.samples = SMP; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
sc.render.filepath = OUTP; bpy.ops.render.render(write_still=True)
