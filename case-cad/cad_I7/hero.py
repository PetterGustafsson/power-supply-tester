"""Hero render: assembled I6 case (ivory colourway) with the 12-core cable + HR10A-10P-12S(73) plug on the bench.  blender -b -P hero.py -- out.png"""
import bpy, sys, math, os
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--")+1]; S = 0.001; ST = "/workspace/psu-tester-case/cad_I7/stl"
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def lin(h): c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]; return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
def mat(n, col, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal; return m
P = [("I7_top_world", "E3DED0", 0.55, 0), ("I7_base_world", "2A2A2C", 0.6, 0), ("I7_crown_world", "FF6A13", 0.45, 0), ("render/display_LCM", "050607", 0.06, 0), ("render/display_PCB", "1B2238", 0.4, 0),
     ("REF_grommet_foot_x4", "151515", 0.7, 0), ("REF_cable_12pin_7mm", "111111", 0.5, 0), ("REF_cable_12pin_7mm_external", "111111", 0.5, 0),
     ("REF_HR10A-10P-12S(73)_female_plug", "C9CCD1", 0.25, 1.0)]
for f, col, r, m in P:
    bpy.ops.wm.stl_import(filepath=f"{ST}/{f}.stl", global_scale=S); o = bpy.context.selected_objects[0]
    o.data.materials.append(mat(f, col, r, m)); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, -0.08, -2*S)); bpy.context.object.data.materials.append(mat("floor", "B4B4B1", 0.7))
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin("E8E8E6"), 1); bg.inputs[1].default_value = 0.08
C = Vector((8, -72, 14))
def area(name, loc, energy, size):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; ob = bpy.data.objects.new(name, l); sc.collection.objects.link(ob)
    ob.location = Vector(loc)*S; ob.rotation_euler = (C*S - ob.location).to_track_quat('-Z', 'Y').to_euler()
area("key", (-260, -330, 420), 2.6, 0.5); area("fill", (320, -200, 250), 0.7, 0.7); area("rim", (60, 300, 380), 1.4, 0.8)
cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
A, E, dist = math.radians(-32), math.radians(30), 0.62
co.location = C*S + Vector((math.sin(A)*math.cos(E), -math.cos(A)*math.cos(E), math.sin(E)))*dist
co.rotation_euler = (C*S - co.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = 58; cd.clip_start = 0.01; cd.clip_end = 10
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get("SMP", 64)); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
