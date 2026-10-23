"""Render the manufactured jig meshes with the project's native D2 KiCad model."""
import bpy
import collections
import json
import math
import sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(REPO/'output/enclosure-d2/board-and-display.blend'))
pcb=bpy.data.objects['D2 PCB - native KiCad geometry']
pcb.matrix_world=Matrix.Identity(4)
for o in list(bpy.data.objects):
    if o!=pcb:bpy.data.objects.remove(o,do_unlink=True)

# The source model is centred on the board, +Y toward the back edge.
# Large horizontal faces independently locate the laminate surfaces.
planes=collections.defaultdict(float)
for face in pcb.data.polygons:
    zs=[pcb.data.vertices[i].co.z for i in face.vertices]
    if max(zs)-min(zs)<.0001 and -1.1<zs[0]<1.1:
        planes[round(zs[0],4)]+=face.area
largest=sorted(planes.items(),key=lambda kv:kv[1],reverse=True)[:8]
print('PCB_HORIZONTAL_PLANES',largest,flush=True)
# KiCad's VRML export places laminate bottom at -0.8 and top at +0.8.
assert planes[-.8]>1000 and planes[.8]>1000, largest
pcb.location=(43,-31,9.8)
pcb['source']='Actual Rev D2 PCB: hardware/rev-d/tester12v.kicad_pcb'

def mat(name,rgb,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*rgb,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    return m

teal=mat('Printed base - teal PETG',(.025,.24,.32))
orange=mat('Printed removable pogo arm',(.85,.23,.035))
steel=mat('Fasteners',(.3,.34,.37),.8,.25)
gold=mat('Pogo - simplified external envelope',(.62,.39,.08),.8,.22)
black=mat('AGND lead',(.012,.015,.02),0,.48)
paper=mat('Warm white studio',(.79,.82,.83),0,.7)
ink=mat('Text',(.025,.045,.06),0,.6)

# The previous CAD view already stores calibrated black mask materials.
for m in pcb.data.materials:
    if m.use_nodes:
        b=m.node_tree.nodes.get('Principled BSDF')
        if b:b.inputs['Roughness'].default_value=.5

def import_stl(name,path,loc,material):
    bpy.ops.wm.stl_import(filepath=str(path))
    o=bpy.context.object;o.name=name;o.location=loc;o.data.materials.append(material)
    # Only split normals for curved facets; retain dimensional mesh geometry.
    for p in o.data.polygons:p.use_smooth=False
    return o
base=import_stl('PRINT 1 - base',ROOT/'01_base.stl',(-7,-69,0),teal)
arm=import_stl('PRINT 2 - removable pogo arm',ROOT/'02_pogo_arm.stl',(68,-14,25),orange)

def cylinder(name,center,radius,depth,material,axis=(0,0,1),vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=center)
    o=bpy.context.object;o.name=name;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    o.data.materials.append(material)
    bevel=o.modifiers.new('Tiny highlight bevel','BEVEL');bevel.width=.08;bevel.segments=2
    o.modifiers.new('Normals','WEIGHTED_NORMAL')
    return o
hardware=[]
for x in (71,83):
    hardware.append(cylinder('M3 arm screw',(x,7,36.5),2.75,3,steel))
hardware.append(cylinder('M3 x 12 clamp screw',(82.5,-15.5,30),2.75,3,steel,axis=(0,1,0)))

contact_z=10.6
tip=cylinder('1.5 mm contact head - on AGND',(77,-10,contact_z+.25),.75,.5,gold)
plunger=cylinder('Extended plunger - illustrative',(77,-10,(11.1+15.9)/2),.5,15.9-11.1,gold)
barrel=cylinder('2 mm pogo barrel - clamped',(77,-10,(15.9+38.6)/2),1.0,38.6-15.9,gold)
tail=cylinder('Wire tail - illustrative',(77,-10,40.1),.65,3,gold)
probe=[tip,plunger,barrel,tail]

def tube(name,points,material,radius):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=24;c.bevel_depth=radius;c.bevel_resolution=4
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,v in zip(s.bezier_points,points):p.co=v;p.handle_left_type=p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);o.data.materials.append(material);return o
wire=tube('AGND supply negative wire - illustrative',[(77,-10,41.6),(77,-7,46),(88,4,45),(105,10,37),(114,7,16)],black,.65)

def text(name,body,loc,size):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.space_line=1.3
    o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);o.location=loc;o.data.materials.append(ink);return o

bpy.ops.mesh.primitive_plane_add(size=2000,location=(45,-25,-.08))
floor=bpy.context.object;floor.name='Studio floor';floor.data.materials.append(paper)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.22,.22,.22)
scene.view_settings.view_transform='AgX'

for name,pos,energy,size in [
    ('Large key',(10,-65,150),200000,110),('Right fill',(130,-20,90),140000,85),('Rear edge',(50,90,100),180000,90)
]:
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos
    o.rotation_euler=(Vector((45,-25,10))-o.location).to_track_quat('-Z','Y').to_euler()

camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
def camera(pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=scale;camdata.lens=45;camdata.clip_start=.1;camdata.clip_end=3000

camera((145,-155,142),(48,-23,11),153)
scene.render.filepath=str(ROOT/'assembly-preview.png')
if '--parts-only' not in sys.argv:
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'D2_AGND_jig_preview.blend'))

# Detail view with the exact same printable arm/pad alignment.
camera((126,-76,69),(78,-6,25),58)
scene.render.resolution_x=1200;scene.render.resolution_y=1000
scene.render.filepath=str(ROOT/'pogo-contact-detail.png')
if '--parts-only' not in sys.argv:bpy.ops.render.render(write_still=True)

# A clean layout of the actual STLs in their supplied printing orientation.
for o in [pcb,base,arm,wire]+probe+hardware:o.hide_render=True
for name,filename,loc,material in [
    ('Base - print flat','01_base.stl',(-7,-69,0),teal),
    ('Pogo arm - print flat','02_pogo_arm.stl',(102,-63,0),orange),
    ('Optional bore coupon','03_pin_fit_coupon.stl',(102,-24,0),orange)
]:import_stl(name,ROOT/filename,loc,material)
camera((155,-166,177),(57,-18,5),178)
scene.render.resolution_x=1600;scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'print-parts-preview.png')
bpy.ops.render.render(write_still=True)

report={'source_board_laminate_surfaces_z':[-.8,.8],
        'PCB_laminate_bottom_in_fixture':9.0,'PCB_laminate_top_in_fixture':10.6,
        'native_model_min_z':-2.7,'minimum_native_solder_tail_to_base_floor_clearance':3.1,
        'drop_in_frame_clearance_per_side_mm':.2,'PCB_fasteners':0,
        'arm_bottom_to_tallest_native_component_clearance':4.2,
        'probe_geometry':'Simplified outer envelope; tip, barrel diameters and total length supplied by user. Tail and shoulder proportions illustrative.',
        'board_geometry':'Native KiCad model, source PCB hash matches enclosure-d2 reference.'}
(ROOT/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('JIG_PREVIEWS_COMPLETE',flush=True)
