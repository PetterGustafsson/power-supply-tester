"""Render the final I15 components and the operator-confirmed fasteners."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import bpy, math, sys, json
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/final-layout-poster'
OUT.mkdir(parents=True,exist_ok=True)
ST=ROOT/'case-cad/cad_I9/stl'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
PREVIEW='--preview' in args
DETAIL='--tie-detail' in args
S=.001
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene

def linear(h):
    v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)
def material(name,col,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(*linear(col),1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
ivory=material('Marble ivory','E7E4DA',.5)
n=ivory.node_tree.nodes;l=ivory.node_tree.links
tex=n.new('ShaderNodeTexVoronoi');tex.inputs['Scale'].default_value=90
coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.075
ramp.color_ramp.elements[0].color=(*linear('494843'),1)
ramp.color_ramp.elements[1].position=.135;ramp.color_ramp.elements[1].color=(*linear('D8D6CD'),1)
l.new(tex.outputs['Distance'],ramp.inputs[0]);l.new(ramp.outputs[0],n['Principled BSDF'].inputs['Base Color'])
charcoal=material('Charcoal PLA','27272A',.64)
orange=material('Orange crown','FF6A13',.42)
black=material('Black fasteners','111214',.38)
black_steel=material('Black steel self-tapping screws','171A1D',.31,.65)
rubber=material('Rubber','17181A',.85)
silver=material('Nickel plated metal','C9CDD0',.25,1)
white=material('Natural connector','E9E7DB',.6)
floor_mat=material('Warm grey paper','C8C7C1',.8)
M={}
def mat(col,rough=.45,metal=0):
    key=(col,rough,metal)
    if key not in M:M[key]=material(col,col,rough,metal)
    return M[key]

def finish(o,m,smooth=False):
    o.data.materials.append(m)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o
def imported(path,m):
    bpy.ops.wm.stl_import(filepath=str(path),global_scale=1)
    o=bpy.context.object;finish(o,m)
    return o
def bounds(objects):
    v=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return Vector(tuple(min(p[i] for p in v) for i in range(3))),Vector(tuple(max(p[i] for p in v) for i in range(3)))
def place(objects,x,y,rotation=None):
    if rotation:
        for o in objects:o.matrix_world=rotation@o.matrix_world
    bpy.context.view_layer.update()
    lo,hi=bounds(objects);shift=Vector((x-(lo.x+hi.x)/2,y-(lo.y+hi.y)/2,-lo.z))
    for o in objects:o.matrix_world=Matrix.Scale(S,4)@Matrix.Translation(shift)@o.matrix_world
    return objects
def cube(name,loc,size,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=tuple(v*S for v in loc));o=bpy.context.object;o.name=name
    o.dimensions=tuple(v*S for v in size);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,m)
    if bevel:
        b=o.modifiers.new('Edge glints','BEVEL');b.width=bevel*S;b.segments=3
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def cylinder(name,a,b,r,m,vertices=48):
    a,b=Vector(a)*S,Vector(b)*S;d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r*S,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();finish(o,m,True)
    return o
def tube(name,pts,r,m):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16
    cu.bevel_depth=r*S;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*[x*S for x in v],1)
    o=bpy.data.objects.new(name,cu);sc.collection.objects.link(o);o.data.materials.append(m);return o

# Latest print package. The printed shim was replaced by a foam pad as built.
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
with ZipFile(ROOT/'case-cad/cad_I15/PSU_case_I15_print.3mf') as z:doc=ET.fromstring(z.read('3D/3dmodel.model'))
printed={}
for node in doc.findall('m:resources/m:object',ns):
    name=node.get('name');kind=name.removeprefix('I15_')
    if kind=='shim':continue
    verts=[tuple(float(v.get(c)) for c in ('x','y','z')) for v in node.findall('m:mesh/m:vertices/m:vertex',ns)]
    faces=[tuple(int(t.get(c)) for c in ('v1','v2','v3')) for t in node.findall('m:mesh/m:triangles/m:triangle',ns)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
    finish(o,ivory if kind=='top' else orange if kind=='crown' else charcoal)
    printed[kind]=o
place([printed['top']],115,310)
place([printed['base']],297,310)
place([printed['crown']],180,192,Matrix.Rotation(math.pi,4,'X'))
place([printed['retainer']],275,192)
foam=material('2 mm closed-cell foam','242527',.91)
fn=foam.node_tree.nodes;fl=foam.node_tree.links
noise=fn.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=165
bump=fn.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.00016
fl.new(noise.outputs['Fac'],bump.inputs['Height']);fl.new(bump.outputs['Normal'],fn['Principled BSDF'].inputs['Normal'])
cube('2 mm foam support pad',(363,192,1),(11,22,2),foam,.3)

# Source PCBA layers retain the KiCad component geometry and silkscreen.
pcb=[imported(ST/'REF_PCB_RevD2_board.stl',mat('101315',.35)),
     imported(ST/'render/PCB_silk.stl',mat('EDEDE6',.6)),
     imported(ST/'render/PCB_pads.stl',silver)]
colors={'dark':('161616',.5,0),'metal':('C8C8C8',.3,1),'green':('136A2C',.45,0),'white':('EFEDE2',.55,0),'brown':('6B4A3A',.55,0)}
for p in sorted((ST/'render').glob('REF_PCB_*__*.stl')):
    pcb.append(imported(p,mat(*colors[p.stem.split('__')[1]])))
place(pcb,479,310)

# Vendor display, laid glass-up in its own local frame.
G=Vector((0,-10,59.88));u=Vector((0,.766044443,.642787610));a=Vector((0,-.642787610,.766044443))
R=Matrix(((1,0,0,0),(0,u.y,u.z,0),(0,a.y,a.z,0),(0,0,0,1)))@Matrix.Translation(-G)
display=[imported(ST/f'render/display_{k}.stl',m) for k,m in [('PCB',mat('1B2238')),('LCM',mat('050607',.15)),('parts',charcoal)]]
for o in display:o.matrix_world=R@o.matrix_world
place(display,78,192)
# Unpowered black glass, with a quiet studio reflection and no display artwork.
lo,hi=bounds(display)
screen_mat=material('Black display glass','010203',.16)
# Keep the overhead softbox from washing the unpowered glass to grey.
screen_mat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.006
screen_mat.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=0
vv=[(0,0,0)]+[(16.1*math.cos(2*math.pi*i/128),16.1*math.sin(2*math.pi*i/128),0) for i in range(128)]
ff=[(0,i+1,(i+1)%128+1) for i in range(128)]
me=bpy.data.meshes.new('LCD active circle');me.from_pydata(vv,[],ff);me.update()
ob=bpy.data.objects.new('Black display glass',me);sc.collection.objects.link(ob);finish(ob,screen_mat)
ob.scale=(S,S,S);ob.location=(78*S,193.5*S,hi.z+.00015)

# The selected 4-inch extender: rounded right-angle male, finely ribbed soft
# flat cable laid straight, and an elongated rounded female overmold.
usb=material('USB soft black overmold','1C1E20',.32)
cube('USB right-angle male overmold',(436,192,3.3),(14,11,6.6),usb,1.9)
shell=cube('USB-C male rounded metal shell',(432.4,192,8.9),(2.6,8.3,6.2),silver,1.2)
cube('USB-C male dark contact cavity',(432.4,192,12.06),(1.45,6.9,.13),black,.65)
for i in range(12):
    cube('USB-C male contact',(432.3,189.35+i*.48,12.15),(.52,.19,.07),mat('C0A75E',.28,1),.04)
for i in range(3):
    cube('USB male strain relief rib',(440.8+i*.82,192,2.2),(.48,10.2,3.7),usb,.18)

path=[(443+i*70/120,192) for i in range(121)]
rv=[]
for i,(x,y) in enumerate(path):
    before=Vector(path[max(0,i-1)]);after=Vector(path[min(len(path)-1,i+1)])
    tangent=(after-before).normalized();normal=Vector((-tangent.y,tangent.x))
    z=1.05+.12*math.sin(math.pi*i/(len(path)-1))
    rv += [((x+side*normal.x)*S,(y+side*normal.y)*S,(z+up)*S) for up,side in [(-.65,-3.25),(-.65,3.25),(.65,3.25),(.65,-3.25)]]
rf=[(0,3,2,1)]
for i in range(len(path)-1):
    for j in range(4):rf.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
rf.append(tuple(4*(len(path)-1)+i for i in range(4)))
rm=bpy.data.meshes.new('Flexible flat USB cable');rm.from_pydata(rv,[],rf);rm.update()
ro=bpy.data.objects.new('USB soft flat cable',rm);sc.collection.objects.link(ro);finish(ro,usb)
be=ro.modifiers.new('Rounded soft cable edges','BEVEL');be.width=.18*S;be.segments=3
ro.modifiers.new('Soft cable normals','WEIGHTED_NORMAL')
# Longitudinal ridges are visible in the supplied product reference.
for side in [-2.7,-2.1,-1.5,-.9,-.3,.3,.9,1.5,2.1,2.7]:
    pts=[]
    for i,(x,y) in enumerate(path):
        tangent=(Vector(path[min(len(path)-1,i+1)])-Vector(path[max(0,i-1)])).normalized()
        pts.append((x-side*tangent.y,y+side*tangent.x,1.71+.12*math.sin(math.pi*i/(len(path)-1))))
    tube('Fine longitudinal USB cable rib',pts,.065,usb)
cube('USB-C female rounded overmold',(522,192,3.3),(18,11.8,6.6),usb,2.6)
cube('USB-C female metal lip',(531.1,192,3.3),(.65,8.7,3.1),silver,.9)
cube('USB-C female contact opening',(531.47,192,3.3),(.13,7.5,2.0),black,.8)
cube('USB female cable neck',(514,192,1.7),(3.6,7.8,3.0),usb,.6)

# Hirose shell comes from the derived source CAD. Recover its known cable axis.
plug=imported(ST/'REF_HR10A-10P-12S(73)_female_plug.stl',silver)
d=Vector((-.55,.835,0)).normalized();ang=-math.atan2(d.y,d.x)
rot=Matrix.Rotation(ang,4,'Z')
place([plug],211.5,117,rot)
lo,hi=bounds([plug]);rear=hi.x/S
cylinder('Black 12-core jacket',(rear-5,117,3.5),(342,117,3.5),3.5,black)
wire_colors=['C0392B','202225','E67E22','F1C40F','27AE60','2980B9','8E44AD','7F8C8D','E7E8E5','8B4513','E96AA5','16A085']
# A packed 12-core cross-section inside the cut jacket. Each conductor has its
# own starting position and tangent, rather than sharing a fan-out vertex.
starts=[(2.45*math.cos(2*math.pi*i/9+.17),3.5+2.45*math.sin(2*math.pi*i/9+.17)) for i in range(9)]
starts += [(.85*math.cos(2*math.pi*i/3+.4),3.5+.85*math.sin(2*math.pi*i/3+.4)) for i in range(3)]
starts.sort(key=lambda p:p[0])
stagger=[1.4,-1.6,.2,2.6,-.5,1.0,-2.0,.4,2.0,-1.0,1.8,-.2]
for i,col in enumerate(wire_colors):
    sy,sz=starts[i];yy=117+(i-5.5)*3.8+.42*math.sin(i*2.2)
    ex=382+stagger[i];theta=math.radians(3.5*math.sin(i*1.7))
    direction=Vector((math.cos(theta),math.sin(theta),0))
    end=Vector((ex,yy,1.5))
    controls=[Vector((338.5,117+sy,sz)),Vector((354+i*.16,117+sy,sz)),end-direction*(11+.8*math.sin(i)),end]
    pts=[]
    for j in range(81):
        t=j/80;v=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
        # A small individual bow gives each loose wire a relaxed lay.
        v.y+=.34*math.sin(i*1.8)*math.sin(math.pi*t)**2
        pts.append(tuple(v))
    tube(f'Conductor {i+1}',pts,.66,mat(col,.4))
    collar_end=end+direction*5
    cylinder('Green ferrule collar',end,collar_end,1.5,mat('1E9E3A',.4))
    cylinder('Crimped ferrule pin',collar_end,collar_end+direction*8,.55,silver,24)

# Five-wire harness; the poster does not assign the illustrative colors to pins.
cube('JST-XH5',(108,50,2.9),(9,13,5.8),white,.4)
for i,col in enumerate(['C0392B','202225','E67E22','2980B9','F1C40F']):
    yy=50+(i-2)*3.2;end=50+(i-2)*2.5
    pts=[]
    for j in range(31):
        t=j/30;sm=t*t*(3-2*t);pts.append((29+74*t,yy+(end-yy)*sm,.6))
    tube('Harness wire',pts,.4,mat(col,.45))
    cylinder('Single pin housing',(20,yy,.65),(29,yy,.65),.65,black,24)
    cube('Harness contact',(18,yy,.65),(4,.64,.64),mat('D4AF37',.3,1))

# Confirmed self-tapping screws: countersunk flat heads, Phillips drive,
# sharp points and coarse triangular thread. Six M2 x 6, four M2.5 x 10.
def screw(x,y,diam,length):
    existing=set(bpy.data.objects)
    headr=diam*.96;hh=diam*.64;core=diam*.31
    # Lathe a shallow cylindrical rim followed by the conical underside.
    profile=[(0,headr*.96),(.10,headr),(.22,headr),(hh,core),(length-diam*.85,core),(length,.035)]
    vv=[];ff=[];N=64
    for xx,r in profile:
        vv.extend([(xx*S,r*math.cos(j*2*math.pi/N)*S,r*math.sin(j*2*math.pi/N)*S) for j in range(N)])
    ff.append(tuple(reversed(range(N))))
    for k in range(len(profile)-1):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    ff.append(tuple((len(profile)-1)*N+j for j in range(N)))
    mesh=bpy.data.meshes.new('Countersunk self-tapping screw');mesh.from_pydata(vv,[],ff);mesh.update()
    h=bpy.data.objects.new(f'M{diam:g} x {length:g} flat Phillips screw',mesh);sc.collection.objects.link(h);finish(h,black_steel,True)
    for width,height in [(diam*.28,headr*1.4),(headr*1.4,diam*.28)]:
        cut=cube('Phillips recess cutter',(.2,0,0),(.75,width,height),black,.04)
        bo=h.modifiers.new('Phillips recess','BOOLEAN');bo.operation='DIFFERENCE';bo.object=cut
        bpy.context.view_layer.objects.active=h;bpy.ops.object.modifier_apply(modifier=bo.name)
        bpy.data.objects.remove(cut,do_unlink=True)
    pitch=diam*.43;start=hh*.8;run=length-start-.14;turns=run/pitch
    tv=[];tf=[];steps=int(turns*40)
    for j in range(steps+1):
        t=j/steps;xx=start+run*t;theta=turns*t*2*math.pi
        taper=min(1,max(.035,(length-xx)/(diam*.85)))
        for dx,r in [(-pitch*.32,core),(-.025,diam*.51),(pitch*.30,core)]:
            tv.append(((xx+dx)*S,r*taper*math.cos(theta)*S,r*taper*math.sin(theta)*S))
    for j in range(steps):
        for k in range(2):tf.append((j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k))
    mesh=bpy.data.meshes.new('Sharp coarse self-tapping thread');mesh.from_pydata(tv,[],tf);mesh.update()
    ridge=bpy.data.objects.new('Self-tapping helical thread',mesh);sc.collection.objects.link(ridge);finish(ridge,black_steel,True)
    objects=[o for o in bpy.data.objects if o not in existing]
    rot=Matrix.Rotation(math.atan(headr/length),4,'Y')
    for ob in objects:ob.matrix_world=rot@ob.matrix_world
    bpy.context.view_layer.update();lo,hi=bounds(objects)
    # Uniform enlargement keeps the ten small fasteners legible on the poster.
    transform=Matrix.Translation(Vector((x,y,0))*S)@Matrix.Scale(1.65,4)@Matrix.Translation(Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z)))
    for ob in objects:ob.matrix_world=transform@ob.matrix_world
for row in range(2):
    for col in range(3):screw(190+col*22,44+row*11,2,6)
    for col in range(2):screw(319+col*25,44+row*11,2.5,10)

# Four rubber feet, shown as individual grommets, and the single cable tie.
for i in range(4):
    x=439+(i%2)*12;y=45+(i//2)*12
    bpy.ops.mesh.primitive_torus_add(major_radius=3.7*S,minor_radius=1*S,major_segments=48,minor_segments=12,location=(x*S,y*S,1*S));finish(bpy.context.object,rubber,True)
    cylinder('Grommet neck',(x,y,1),(x,y,7),2.7,rubber)
    cylinder('Grommet bore shadow',(x,y,7.01),(x,y,7.03),1.5,black)
nylon=material('Natural nylon cable tie','DDDCCF',.36)
np=nylon.node_tree.nodes['Principled BSDF']
np.inputs['IOR'].default_value=1.48
np.inputs['Subsurface Weight'].default_value=.025
np.inputs['Coat Weight'].default_value=.08

# A loose 2.5 mm tie: thin flexible band, serrated inner face, smooth edge
# margins, rounded taper and a hollow locking head with a visible pawl.
def tie_center(x):
    u=(x-491.15)/(566-491.15)
    y=50+.36*math.sin(2*math.pi*u)
    z=.38+.13*math.sin(math.pi*u)+.52*max(0,(x-556)/10)**2
    return y,z
sections=[(491.15+i*(556-491.15)/65,2.5) for i in range(66)]
sections += [(558,2.35),(560,1.95),(562,1.35),(564,.78),(565.5,.62),(566,.35)]
verts=[]
for x,width in sections:
    yy,zz=tie_center(x)
    verts += [(x*S,(yy-width/2)*S,(zz-.31)*S),(x*S,(yy+width/2)*S,(zz-.31)*S),
              (x*S,(yy+width/2)*S,(zz+.31)*S),(x*S,(yy-width/2)*S,(zz+.31)*S)]
faces=[(0,3,2,1)]
for i in range(len(sections)-1):
    for k in range(4):faces.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
faces.append(tuple(4*(len(sections)-1)+i for i in range(4)))
mesh=bpy.data.meshes.new('Thin flexible nylon band');mesh.from_pydata(verts,[],faces);mesh.update()
strap=bpy.data.objects.new('Cable tie flexible strap and rounded tip',mesh);sc.collection.objects.link(strap);finish(strap,nylon)
bev=strap.modifiers.new('Soft strap edges','BEVEL');bev.width=.075*S;bev.segments=3
strap.modifiers.new('Strap normals','WEIGHTED_NORMAL')

# Shallow sawtooth ridges stop short of the two smooth side rails.
tv=[];tf=[]
for i in range(94):
    x=494+i*.65;yy,zz=tie_center(x);base=len(tv)
    for side in (-.91,.91):
        tv += [((x-.23)*S,(yy+side)*S,(zz+.305)*S),
               ((x+.16)*S,(yy+side)*S,(zz+.415)*S),
               ((x+.21)*S,(yy+side)*S,(zz+.305)*S)]
    tf += [tuple(base+j for j in f) for f in ((0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))]
mesh=bpy.data.meshes.new('Ratchet tooth ridges');mesh.from_pydata(tv,[],tf);mesh.update()
teeth=bpy.data.objects.new('Cable tie 94 ratchet teeth',mesh);sc.collection.objects.link(teeth);finish(teeth,nylon)

head=cube('Cable tie locking head',(489,50,1.55),(4.5,4.15,3.1),nylon)
cut=cube('Locking head through aperture',(488.15,50,1.6),(1.55,2.8,5),nylon)
mod=head.modifiers.new('Open locking aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
bpy.context.view_layer.objects.active=head;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cut,do_unlink=True)
bev=head.modifiers.new('Moulded head corners','BEVEL');bev.width=.18*S;bev.segments=3
head.modifiers.new('Head normals','WEIGHTED_NORMAL')
pawl=cube('Cable tie locking pawl',(488.78,50,1.65),(1.0,2.35,.32),nylon,.07)
pawl.rotation_euler.y=math.radians(-20)
# Fine moulded lip around the entry makes the mouth read as a slot.
cube('Locking head entry lip',(487.22,50,2.99),(.22,3.0,.22),nylon,.07)

# Soft studio ground, direct overhead camera, exact correspondence to PDF mm.
cube('Ground',(297,210,-.8),(1300,1000,1.5),floor_mat)
world=bpy.data.worlds.new('Studio world');world.use_nodes=True;sc.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(*linear('F1EFE8'),1)
world.node_tree.nodes['Background'].inputs[1].default_value=.12
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=Vector(loc)*S
    o.rotation_euler=(Vector((297,210,0))*S-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft key',(70,470,700),7,.7)
area('Long fill',(650,80,550),2,.8)
cam=bpy.data.cameras.new('Poster camera');o=bpy.data.objects.new('Poster camera',cam);sc.collection.objects.link(o)
o.location=(.297,.210,1.2);o.rotation_euler=(0,0,0);cam.type='ORTHO';cam.ortho_scale=.594;cam.clip_start=.001;cam.clip_end=10;sc.camera=o
sc.render.engine='CYCLES';sc.cycles.samples=24 if PREVIEW else 64;sc.cycles.use_denoising=True
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
    for device in pref.devices:device.use=device.type=='METAL'
    if any(d.type=='METAL' for d in pref.devices):sc.cycles.device='GPU'
    print('DEVICES',[(d.name,d.type,d.use) for d in pref.devices])
except Exception as e:print('CPU renderer',e)
sc.render.resolution_x=2100 if PREVIEW else 5600;sc.render.resolution_y=1485 if PREVIEW else 3960
if DETAIL:
    look=Vector((526.5,50,1))*S
    o.location=Vector((526.5,-5,85))*S
    o.rotation_euler=(look-o.location).to_track_quat('-Z','Y').to_euler()
    cam.ortho_scale=.098
    sc.render.resolution_x=1800;sc.render.resolution_y=750
    sc.cycles.samples=48
sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard';sc.view_settings.look='Medium High Contrast'
sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/('tie-detail.png' if DETAIL else 'layout-preview.png' if PREVIEW else 'layout-render.png'))
if not DETAIL:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'final-layout.blend'))
bpy.ops.render.render(write_still=True)
(OUT/'parts-manifest.json').write_text(json.dumps({'enclosure':'I15','electronics':'Rev D2',
    'display_surface':'unpowered black glass',
    'usb_support':{'type':'foam pad','quantity':1,'thickness_mm':2},
    'usb_extender':{'quantity':1,'type':'90 degree USB-C male to female, soft flat cable','length_inches':4,'pose':'straight','reference_asin':'B0D9XGFW3W'},
    'screw_reference_asin':'B0G24Z3P66','hardware':[
    {'use':'PCB and display','quantity':6,'allocation':{'PCB':4,'display':2},'size':'M2','length_mm':6,'type':'self-tapping','material':'steel','finish':'black','head':'countersunk flat Phillips'},
    {'use':'case','quantity':4,'size':'M2.5','length_mm':10,'type':'self-tapping','material':'steel','finish':'black','head':'countersunk flat Phillips'}]},indent=2)+'\n')
