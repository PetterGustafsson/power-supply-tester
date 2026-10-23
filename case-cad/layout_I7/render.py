"""blender -b -P render.py -- out.png labels(0/1) view(angle|top)"""
import bpy, sys, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; OUT, LAB, VIEW = a[0], a[1] == "1", a[2]
S = 0.001; cfg = json.load(open("/workspace/psu-tester-case/layout_I7/items.json"))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def lin(h): c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]; return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
MATS = {}
def mat(col, rough=0.5, metal=0):
    k = (col, rough, metal)
    if k in MATS: return MATS[k]
    m = bpy.data.materials.new(str(k)); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    MATS[k] = m; return m
for it in cfg["items"]:
    for p in it["parts"]:
        bpy.ops.wm.stl_import(filepath=p["f"], global_scale=S); o = bpy.context.selected_objects[0]
        o.data.materials.append(mat(p["col"], p["rough"], p["metal"])); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
x0, y0, x1, y1 = cfg["extent"]; cx, cy = (x0 + x1)/2, (y0 + y1)/2
bpy.ops.mesh.primitive_plane_add(size=3, location=(cx*S, cy*S, 0)); fl = bpy.context.object; fl.data.materials.append(mat("B4B4B1", 0.7))
if LAB:
    FB = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"); FR = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    for it in cfg["items"]:
        lines = it["label"].split("\n"); lx, ly = it["label_xy"]
        for i, t in enumerate(lines):
            cu = bpy.data.curves.new("t", 'FONT'); cu.body = t; cu.font = FB if i == 0 else FR; cu.size = (6.0 if i == 0 else 5.0)*S
            cu.align_x = 'CENTER'; cu.align_y = 'TOP'
            ob = bpy.data.objects.new("t", cu); sc.collection.objects.link(ob); ob.location = (lx*S, (ly - (0 if i == 0 else 2.0 + i*6.0))*S, 0.05*S)
            ob.data.materials.append(mat("1A1A1C" if i == 0 else "2E2E32", 0.8))
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin("E8E8E6"), 1); bg.inputs[1].default_value = 0.12
def area(name, loc, energy, size, look=(cx, cy, 0)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; ob = bpy.data.objects.new(name, l); sc.collection.objects.link(ob)
    ob.location = Vector(loc)*S; ob.rotation_euler = (Vector(look)*S - ob.location).to_track_quat('-Z', 'Y').to_euler()
area("key", (cx - 250, cy - 200, 600), 5.5, 0.6)
area("fill", (cx + 350, cy - 100, 350), 1.5, 0.8)
area("top", (cx, cy + 100, 700), 2.5, 1.0)
cd = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cd); sc.collection.objects.link(co); sc.camera = co
W, H = 1600, 1000
if VIEW == "top":
    cd.type = 'ORTHO'; cd.ortho_scale = max((x1 - x0)*1.08, (y1 - y0)*1.08*W/H)*S
    co.location = (cx*S, cy*S, 1.0); co.rotation_euler = (0, 0, 0)
else:
    el = math.radians(58); look = Vector((cx, cy + 8, 0))*S; dist = 1.25
    co.location = look + Vector((0, -math.cos(el), math.sin(el)))*dist
    co.rotation_euler = (look - co.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = 70; cd.sensor_width = 36
    cd.lens = 36/((x1 - x0)*1.02*S)*dist
cd.clip_start = 0.01; cd.clip_end = 10
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(__import__("os").environ.get("SMP", 64)); sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
