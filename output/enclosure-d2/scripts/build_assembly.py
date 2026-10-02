"""Render the actual D2 board and official Waveshare STEP, with a proposed harness.

Model units are mm. The harness, plug envelopes, standoffs and enclosure outline
are planning geometry. They are not a released enclosure or a harness drawing.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent))
from vrml_import import bounds
ROOT=Path(__file__).resolve().parents[1]
reuse_geometry='--reuse-geometry' in sys.argv
if reuse_geometry:
    # Reuse the already joined native meshes; lighting and layout are rebuilt.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'board-and-display.blend'))
    for o in list(bpy.data.objects):
        if o.name in ('D2 PCB - native KiCad geometry','Waveshare ESP32-S3-LCD-1.28 - official STEP'):
            o.matrix_world=Matrix.Identity(4)
        else:bpy.data.objects.remove(o,do_unlink=True)
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sources/imported.blend'))
VIEW_SUFFIX='-usb-rear-connector-ui'

# Convert CAD display colours from sRGB into Blender's linear shader inputs.
# This keeps the specified black mask black under the studio lighting.
for mat in ([] if reuse_geometry else bpy.data.materials):
    if mat.use_nodes:
        bs=mat.node_tree.nodes.get('Principled BSDF')
        if bs:
            rgba=tuple(bs.inputs['Base Color'].default_value)
            rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgba[:3]]
            bs.inputs['Base Color'].default_value=(*rgb,rgba[3])
            bs.inputs['Roughness'].default_value=.5
            bs.inputs['Specular IOR Level'].default_value=.22

def material(name,rgb,metal=0,rough=.45):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
white=material('Ivory connector',(0.78,.78,.73));dark=material('Housing dark',(.025,.031,.038));
gold=material('Brass standoffs',(.57,.37,.09),.7);floor=material('Warm studio',(.82,.84,.85))
labelmat=material('Labels',(.035,.055,.07));guide=material('Planning outline',(.13,.4,.52),.25)

def cube(name,loc,size,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('Rounded edges','BEVEL');m.width=bevel;m.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def tube(name,points,mat,r=.4):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=24;c.bevel_depth=r;c.bevel_resolution=4
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,v in zip(s.bezier_points,points):p.co=v;p.handle_left_type=p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat);return o
def text(name,body,loc,size=2.0,mat=labelmat):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.align_x='CENTER';c.space_line=1.25
    o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);o.location=loc;o.data.materials.append(mat);return o
def cylinder(name,x,y,z,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=(x,y,z))
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def combine(collection,name):
    objects=list(collection.objects)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    # Bake the exact imported transform, then use an identity origin for placements.
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return o

# Discard the dummy 1 mm import board, retaining every manufacturer-model surface.
dc=bpy.data.collections['display']
for o in list(dc.objects):
    if bounds([o])[0][0]>50:bpy.data.objects.remove(o,do_unlink=True)
display_bounds=bounds(list(dc.objects))
print('DISPLAY_BOUNDS_MM',display_bounds,flush=True)
pcb=combine(bpy.data.collections['tester-d2'],'D2 PCB - native KiCad geometry')
display=combine(dc,'Waveshare ESP32-S3-LCD-1.28 - official STEP')
pcb['source']='hardware/rev-d/tester12v.kicad_pcb; no manufacturing edits'
display['source']='Waveshare official ESP32-S3-LCD-1_28.stp'
display['dimensions_mm']=[b-a for a,b in display_bounds]
display_top=display_bounds[2][1]
display_bottom=display_bounds[2][0]
cy=(display_bounds[1][0]+display_bounds[1][1])/2

# The display's front active area is centred on the round part, independent of
# the USB tab. Source drawing: 36.5 x 39.5 PCB; active LCD diameter 32.4 mm.
# Manufacturer STEP is oriented screen upward with the USB tab toward -Y.
screen=bpy.data.materials.new('Connector UI concept - simulated readings');screen.use_nodes=True
nodes=screen.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.28
bs.inputs['Specular IOR Level'].default_value=.025
im=nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(ROOT/'sources/display-connector-ui.png'))
im.image.pack()
screen.node_tree.links.new(im.outputs['Color'],bs.inputs['Base Color']);screen.node_tree.links.new(im.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.6
verts=[(0,.14,display_top+.025)]+[(16.2*math.cos(i*2*math.pi/128),.14+16.2*math.sin(i*2*math.pi/128),display_top+.025) for i in range(128)]
mesh=bpy.data.meshes.new('Active LCD 32.4mm');mesh.from_pydata(verts,[],[(0,i+1,(i+1)%128+1) for i in range(128)]);mesh.update()
uv=mesh.uv_layers.new()
for poly in mesh.polygons:
    for loop in poly.loop_indices:
        # Counter-rotate the illustrative UI so it remains readable after the
        # module turns. Actual firmware rotation is a separate integration step.
        v=mesh.vertices[mesh.loops[loop].vertex_index].co;uv.data[loop].uv=(.5-(v.x/32.4),.5-((v.y-.14)/32.4))
screenobj=bpy.data.objects.new('Screen example - not a live measurement',mesh);bpy.context.scene.collection.objects.link(screenobj);screenobj.data.materials.append(screen)

scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.world.color=(.28,.28,.28);scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.use_file_extension=True
cube('Studio floor',(0,0,-6.1),(800,800,1),floor)
def area(name,loc,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((-15,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-80,-80,160),450000,120);area('Fill',(100,30,110),300000,100);area('Rim',(-40,120,100),300000,90)
camdata=bpy.data.cameras.new('Assembly camera');cam=bpy.data.objects.new('Assembly camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.clip_end=2000
def camera(loc,target,scale):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale

colors=[('1 - 5V VSYS',(.66,.035,.02)),('2 - GND',(.012,.015,.019)),('3 - 3V3',(.95,.28,.025)),('4 - SDA GPIO6',(.92,.7,.015)),('5 - SCL GPIO7',(.025,.42,.66))]
wiremats=[material(n,c) for n,c in colors]
temporary=[]
def add(o):temporary.append(o);return o
def clear_layout():
    for o in temporary:bpy.data.objects.remove(o,do_unlink=True)
    temporary.clear()
def arrange(displaypos,mode):
    pcb.location=(0,0,0);display.location=displaypos;screenobj.location=displaypos
    rotation=Matrix.Rotation(math.pi,3,'Z')
    display.rotation_euler=(0,0,math.pi);screenobj.rotation_euler=(0,0,math.pi)
    def from_display(point):return rotation@Vector(point)+Vector(displaypos)
    for x in (-40,40):
        for y in (-28,28):add(cylinder('PCB mounting standoff',x,y,-3.3,2.4,5,gold))
    # Plug envelope at J4. Wire leads emerge vertically before bending.
    add(cube('J4 mating plug - approximate',(-36.5,-10,10.1),(4.7,13.3,7),white,.25))
    # The manufacturer model supplies the header bodies. These short individual
    # insulated terminations depict a custom 1.27 mm breakout harness; do not
    # interpret their geometry as a catalog plug specification.
    endpoint_local=[(12.864,-4.159,-9.1),(12.864,-5.429,-9.1),(14.134,-4.159,-9.1),(12.864,-2.889,-9.1),(12.864,-1.619,-9.1)]
    for i,(name,col) in enumerate(colors):
        start=Vector((-36.5,-15+2.5*i,13.6));end=from_display(endpoint_local[i])
        if mode=='spread':
            edge=displaypos[0]+24+i*.8
            pts=[start,(-46,-15+2.5*i,18+i*.4),(edge,end.y,15+i*.4),(edge,end.y,end.z-2),(end.x,end.y,end.z-2),end]
        else:
            pts=[start,(-36,-8+i*1.8,18+i*.45),(-12,4+i*1.3,20+i*.2),(end.x,end.y,end.z-3),end]
        add(tube(name,pts,wiremats[i],.42))
        add(cube('Display harness termination '+name,(end.x,end.y,end.z+1),(.95,.95,2),dark,.12))
    # Deliberate USB access indication; no cable electronics are modelled.
    add(cube('USB-C plug clearance envelope',from_display((0,-27.2,-4.4)),(10,12,5),dark,1))
    add(tube('USB power cable',[from_display((0,-33.2,-4.4)),from_display((0,-49.2,-4.4)),from_display((10,-61.2,-5.4))],dark,1.8))

arrange((-77,4,13),'spread')
add(text('Board label','TESTER PCB  /  86 x 62 mm',(0,38,0),2.4))
add(text('Display label','ESP32 + ROUND LCD\n36.5 x 39.5 mm module',(-78,-28,13),2.2))
add(text('Harness label','5-WIRE HARNESS\n5V / GND / 3V3 / SDA / SCL',(-32,-41,-5),1.8))
camera((-125,-160,175),(-30,-4,3),180)
bpy.context.view_layer.update()
scene.render.filepath=str(ROOT/f'board-and-display{VIEW_SUFFIX}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'board-and-display{VIEW_SUFFIX}.blend'))

# Second view explores a lid-mounted display above the board. Dashed posts and
# a floor outline indicate a provisional 96 x 76 mm outer enclosure footprint.
clear_layout();arrange((7,9,32),'stacked')
for x in (-48,48):
    for y in (-38,38):
        for z in range(-4,36,4):add(tube('Provisional case corner',[(x,y,z),(x,y,z+2)],guide,.2))
for a,b in [((-48,-38,-5),(48,-38,-5)),((48,-38,-5),(48,38,-5)),((48,38,-5),(-48,38,-5)),((-48,38,-5),(-48,-38,-5))]:add(tube('96 x 76 mm planning footprint',[a,b],guide,.35))
add(text('Enclosure label','STARTING ENVELOPE: 96 x 76 x 42 mm\nCONCEPT ONLY - MOUNTS / CUTOUTS TO BE DESIGNED',(0,-48,-5),1.75))
camera((112,-142,117),(0,0,11),157)
bpy.context.view_layer.update()
scene.render.filepath=str(ROOT/f'lid-mounted-layout{VIEW_SUFFIX}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'lid-mounted-layout{VIEW_SUFFIX}.blend'))

report={'pcb_source':'hardware/rev-d/tester12v.kicad_pcb','pcb_mm':[86,62,1.6],
 'display_source':'Waveshare official STEP and mechanical PDF','display_drawing_board_mm':[36.5,39.5],
 'display_mesh_bounds_mm':display_bounds,'active_display_diameter_mm':32.4,
 'suggested_outer_case_mm':[96,76,42], 'case_size_status':'provisional planning envelope; wall, plugs, mounts, antenna and USB access need detailed design',
 'wire_diameter_mm':.84,'wire_geometry':'illustrative custom harness, not a production cable drawing',
 'display_rotation_degrees':180,'usb_direction':'rear, away from screw terminals',
 'screen_source':'output/silk-colors-clean-preview.png; latest connector UI from chat 01a0ae0d-bb99-7d81-8145-319294c614de',
 'screen':'existing artwork used unchanged; preview counter-rotated to remain upright; firmware not modified; simulated 5/12/24 V readings, not a hardware range validation',
 'no_manufacturing_files_modified':True}
(ROOT/'assembly-notes.json').write_text(json.dumps(report,indent=2)+'\n')
print('ASSEMBLY_RENDER_COMPLETE',flush=True)
