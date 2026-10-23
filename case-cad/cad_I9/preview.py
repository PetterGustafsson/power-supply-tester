"""Blender quick clay preview of STLs. args after --: out.png W H az el dist|ortho_scale ortho(0/1) lookx,y,z file:hexcol ..."""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
out, Wd, Ht, az, el, dist, ortho, look = a[0], int(a[1]), int(a[2]), float(a[3]), float(a[4]), float(a[5]), a[6] == "1", Vector(map(float, a[7].split(",")))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def lin(h): c = [int(h[i:i+2],16)/255 for i in (0,2,4)]; return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
for spec in a[8:]:
    f, col = spec.rsplit(":", 1)
    bpy.ops.wm.stl_import(filepath=f, global_scale=0.001); o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new(f); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1); b.inputs["Roughness"].default_value = 0.6
    o.data.materials.append(m); bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.9,0.9,0.9,1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
import os
LB = os.environ.get("LIGHT_BELOW") == "1"   # I8: underside views
for nm, rot, e in ((("k", (140, 0, -40), 3.0), ("f", (125, 0, 120), 1.2), ("t", (180, 0, 0), 0.8)) if LB else (("k", (50, 0, -40), 3.0), ("f", (60, 0, 120), 1.0))):
    l = bpy.data.lights.new(nm, 'SUN'); l.energy = e; l.angle = 0.3; o = bpy.data.objects.new(nm, l); sc.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(v) for v in rot)
cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
A, E = math.radians(az), math.radians(el)
co.location = look + Vector((math.sin(A)*math.cos(E), -math.cos(A)*math.cos(E), math.sin(E)))*(0.5 if ortho else dist)
co.rotation_euler = (look - co.location).to_track_quat('-Z','Y').to_euler(); cd.lens = 80; cd.clip_end = 10
if ortho: cd.type = 'ORTHO'; cd.ortho_scale = dist
sc.render.engine = 'CYCLES'; sc.cycles.samples = 12; sc.cycles.use_denoising = True; sc.render.resolution_x, sc.render.resolution_y = Wd, Ht
sc.render.film_transparent = False; sc.view_settings.view_transform = 'AgX'
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
