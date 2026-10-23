"""Blender quick bay renders. Usage: blender -b -P bay.py -- cfg.json ; cfg: out, res, cam{loc,look,lens|ortho}, objs[{f,col,alpha,shift(mm along AF),cut}], cut_keep ('xneg'|None), arrows"""
import bpy, sys, json, math
from mathutils import Vector
cfg = json.load(open(sys.argv[sys.argv.index("--")+1])); S = 0.001
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
AF = Vector(cfg["AF"])
def lin(h): c = [int(h[i:i+2],16)/255 for i in (0,2,4)]; return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
def mat(name, col, alpha=1.0, rough=0.55):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1); b.inputs["Roughness"].default_value = rough; b.inputs["Alpha"].default_value = alpha
    if alpha < 1: m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    return m
def new_cutter():
    bpy.ops.mesh.primitive_cube_add(size=1); c = bpy.context.object; c.scale = (0.3, 0.4, 0.4); c.location = (cfg.get("cut_x", 0.0)*S + 0.15, 0, 0.05)   # removes x > cut_x
    c.hide_render = True; c.hide_viewport = True; return c
for o in cfg["objs"]:
    bpy.ops.wm.stl_import(filepath=o["f"], global_scale=S); ob = bpy.context.selected_objects[0]
    ob.data.materials.append(mat(o["f"], o["col"], o.get("alpha", 1.0)))
    ob.location = AF*o.get("shift", 0.0)*S
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
    if cfg.get("cut") and o.get("cut", True):
        cutter = new_cutter()
        md = ob.modifiers.new("cut", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter; md.solver = 'EXACT'
        if o.get("capcol"):
            cm = mat("cap" + o["f"], o["capcol"]); ob.data.materials.append(cm); cutter.data.materials.append(cm); md.material_mode = 'TRANSFER'
for a in cfg.get("arrows", []):       # arrows along AF: start (mm), length (mm, signed), colour
    p0 = Vector(a["p"])*S; L = a["len"]*S; d = AF*(1 if L > 0 else -1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6*S, depth=abs(L)*0.8); c = bpy.context.object
    c.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); c.location = p0 + d*abs(L)*0.4
    bpy.ops.mesh.primitive_cone_add(radius1=1.8*S, radius2=0, depth=abs(L)*0.2); k = bpy.context.object
    k.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); k.location = p0 + d*abs(L)*0.9
    m = mat("arrow", a.get("col", "D02020"), rough=0.4); c.data.materials.append(m); k.data.materials.append(m)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.85,0.85,0.85,1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
for nm, rot, e in (("k", (50, 0, -40), 3.0), ("f", (60, 0, 120), 1.2), ("u", (180, 0, 0), 1.0)):
    l = bpy.data.lights.new(nm, 'SUN'); l.energy = e; l.angle = 0.3; ob = bpy.data.objects.new(nm, l); sc.collection.objects.link(ob)
    ob.rotation_euler = tuple(math.radians(v) for v in rot)
cam = cfg["cam"]; cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
co.location = Vector(cam["loc"])*S; look = Vector(cam["look"])*S
co.rotation_euler = (look - co.location).to_track_quat('-Z', 'Y').to_euler(); cd.clip_start = 0.001; cd.clip_end = 5
if "ortho" in cam: cd.type = 'ORTHO'; cd.ortho_scale = cam["ortho"]*S
else: cd.lens = cam.get("lens", 50)
sc.render.engine = 'CYCLES'; sc.cycles.samples = cfg.get("samples", 24); sc.cycles.use_denoising = True
sc.cycles.transparent_max_bounces = 16
sc.render.resolution_x, sc.render.resolution_y = cfg["res"]; sc.view_settings.view_transform = 'AgX'
sc.render.filepath = cfg["out"]; bpy.ops.render.render(write_still=True)
