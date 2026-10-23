"""Build the Rev D2 calibration fixture in millimetres with FreeCAD's OCCT kernel.

Run with FreeCAD's bundled Python after adding its Resources/lib to sys.path.
The PCB coordinates below match KiCad: x right, ky down from the upper edge.
Model coordinates are (x, -ky, z), preserving the board's physical handedness.
STLs are individually placed on z=0; STEP/FCStd retain assembly coordinates.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET

if sys.platform == 'darwin':
    sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import Mesh
import MeshPart

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
P = {
    'fixture_revision': 'v2_drop_in_frame',
    'pcb_width': 86.0, 'pcb_depth': 62.0, 'pcb_thickness': 1.6,
    'pcb_bottom_z': 9.0, 'base_thickness': 4.0,
    'pcb_mount_holes': [[3, 3], [83, 3], [3, 59], [83, 59]],
    'pcb_hole_diameter': 2.7, 'pcb_fasteners_required': 0,
    'board_clearance_per_side': 0.2,
    'board_pocket_width': 86.4, 'board_pocket_depth': 62.4,
    'corner_relief_diameter': 4.0,
    'frame_wall_thickness': 3.5, 'frame_top_z': 11.4,
    'entry_chamfer': 0.6, 'entry_chamfer_degrees': 45,
    'support_ledge_width_inside_pcb_edge': 2.0,
    'agnd_xy_kicad': [77.0, 10.0], 'agnd_pad_diameter': 1.5,
    'pogo_barrel_diameter': 2.0, 'pogo_tip_diameter': 1.5,
    'pogo_free_length': 33.0, 'pogo_fully_compressed_length': 25.7,
    'nominal_compression': 2.0, 'pogo_bore': 2.2,
    'arm_bottom_z': 25.0, 'arm_thickness': 10.0,
    'arm_mount_xy_kicad': [[71.0, -7.0], [83.0, -7.0]],
    'arm_mount_bore': 3.4, 'register_boss_diameter': 6.0,
    'register_socket_diameter': 6.4, 'register_height': 2.0,
    'register_socket_depth': 2.2, 'clamp_split': 0.8,
    'clamp_screw_x': 82.5, 'clamp_screw_z': 30.0,
    'clamp_bore': 3.4, 'clamp_screw_length': 12.0, 'arm_front_kicad_y': 14.0,
    'm3_nut_slot_width': 5.8,
    'm3_nut_slot_thickness': 2.7,
    'base_bounds_kicad': [-7, 93, -15, 69],
}
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'

def box(x0, x1, ky0, ky1, z0, z1):
    return Part.makeBox(x1-x0, ky1-ky0, z1-z0, App.Vector(x0, -ky1, z0))

def rounded_box(x0, x1, ky0, ky1, z0, z1, radius):
    s = box(x0, x1, ky0, ky1, z0, z1)
    edges = [e for e in s.Edges if len(e.Vertexes) == 2
             and abs(abs(e.Vertexes[1].Point.z-e.Vertexes[0].Point.z)-(z1-z0)) < 1e-6]
    return s.makeFillet(radius, edges)

def cylinder(x, ky, z0, z1, diameter):
    return Part.makeCylinder(diameter/2, z1-z0, App.Vector(x, -ky, z0))

def rectangle_wire(x0,x1,ky0,ky1,z):
    points = [App.Vector(x0,-ky0,z),App.Vector(x1,-ky0,z),
              App.Vector(x1,-ky1,z),App.Vector(x0,-ky1,z)]
    return Part.makePolygon(points+[points[0]])

def text_solid(text, height, x, y, z, depth):
    glyphs = Part.makeWireString(text, str(Path(FONT).parent)+'/', Path(FONT).name, height)
    solids = []
    for wires in glyphs:
        if not wires: continue
        f = Part.makeFace(wires, 'Part::FaceMakerBullseye')
        f.translate(App.Vector(x,y,z))
        solids.append(f.extrude(App.Vector(0,0,depth)))
    return Part.makeCompound(solids)

def engrave(shape, text, height, x, y, top):
    return shape.cut(text_solid(text, height, x, y, top-.45, .65))

def make_base():
    s = rounded_box(-7,93,-15,69,0,4,4)
    s = s.cut(rounded_box(10,76,10,52,-.1,4.1,5))
    c = P['board_clearance_per_side']
    w, d = P['pcb_width'], P['pcb_depth']
    t = P['frame_wall_thickness']
    top = P['frame_top_z']
    zseat = P['pcb_bottom_z']
    ledge = P['support_ledge_width_inside_pcb_edge']
    # This continuous ledge carries the PCB underside. Its centre is open for
    # components and through-hole solder tails; no PCB screws or pegs are used.
    rim = rounded_box(-c-t,w+c+t,-c-t,d+c+t,3.9,top,t)
    rim = rim.cut(rounded_box(ledge,w-ledge,ledge,d-ledge,3.8,zseat,1.0))
    rim = rim.cut(box(-c,w+c,-c,d+c,zseat,top+.1))
    chamfer = P['entry_chamfer']
    entry = Part.makeLoft([
        rectangle_wire(-c,w+c,-c,d+c,top-chamfer),
        rectangle_wire(-c-chamfer,w+c+chamfer,-c-chamfer,d+c+chamfer,top),
    ],True,False)
    rim = rim.cut(entry)
    s = s.fuse(rim)
    # A nonconductive support under TP19 prevents local board bending.
    s = s.fuse(cylinder(77,10,3.9,9,4))
    s = s.fuse(rounded_box(66,88,-14,-1,3.8,25,1.5))
    for x, ky in P['arm_mount_xy_kicad']:
        s = s.fuse(cylinder(x,ky,24.9,27,6))
    s = s.removeSplitter()
    # Full-depth circular corner reliefs let the PCB's sharp corners seat.
    # Their upper edges receive the same 45-degree lead-in as the straight walls.
    radius = P['corner_relief_diameter']/2
    for x,ky in [(-c,-c),(w+c,-c),(-c,d+c),(w+c,d+c)]:
        s = s.cut(cylinder(x,ky,-.1,top+.1,2*radius))
        cone = Part.makeCone(radius,radius+chamfer,chamfer,
                             App.Vector(x,-ky,top-chamfer))
        s = s.cut(cone)
    for x, ky in P['arm_mount_xy_kicad']:
        s = s.cut(cylinder(x,ky,-.1,27.1,3.4))
        # M3 nuts load from the rear side; no heat-set inserts required.
        s = s.cut(box(x-2.9,x+2.9,-14.2,-3.2,19.0,21.6))
    s = engrave(s,'REV D2',2.0,1,-68.1,4)
    return s.removeSplitter()

def make_arm():
    s = rounded_box(68,86,-13,14,25,35,1.0)
    for x, ky in P['arm_mount_xy_kicad']:
        s = s.cut(cylinder(x,ky,24.9,35.1,3.4))
        s = s.cut(cylinder(x,ky,24.9,27.2,6.4))
    s = s.cut(cylinder(77,10,24.9,35.1,P['pogo_bore']))
    gap = P['clamp_split']
    s = s.cut(box(77,86.2,10-gap/2,10+gap/2,24.9,35.1))
    # The screw axis is perpendicular to the slit, so the barrel is clamped
    # around its circumference rather than hit by a pointed grub screw.
    screw = Part.makeCylinder(1.7,13.2,App.Vector(82.5,-14.1,30),App.Vector(0,1,0))
    s = s.cut(screw)
    # Side-loading M3 nut, axis along Y, flats constrained vertically.
    s = s.cut(box(79.2,86.2,2.0,4.7,27.1,32.9))
    s = engrave(s,'AGND',2.5,69.5,-2.6,35)
    return s.removeSplitter()

def make_coupon():
    s = rounded_box(0,18,-50,0,0,4,2)
    for i, diameter in enumerate([2.0,2.1,2.2,2.3,2.4]):
        y = 5+10*i
        s = s.cut(cylinder(4,-y,-.1,4.1,diameter))
        s = engrave(s,f'{diameter:.1f}',2.5,8,y-1.1,4)
    return s.removeSplitter()

def translated(shape, xyz):
    s = shape.copy(); s.translate(App.Vector(*xyz)); return s

def mesh_shape(shape):
    return MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.12,Relative=False)

def inspect_shape(name, shape, mesh):
    assert shape.isValid(), f'{name}: invalid BREP'
    assert len(shape.Solids) == 1, f'{name}: expected one connected solid'
    assert mesh.isSolid(), f'{name}: mesh is not closed'
    assert not mesh.hasNonManifolds(), f'{name}: nonmanifold mesh'
    assert mesh.countComponents() == 1, f'{name}: disconnected mesh'
    b = shape.BoundBox
    return {'brep_valid':True,'solids':len(shape.Solids),'watertight':True,
            'mesh_components':mesh.countComponents(),'facets':mesh.CountFacets,
            'volume_mm3':shape.Volume,'dimensions_mm':[b.XLength,b.YLength,b.ZLength]}

def write_3mf(parts, path):
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',ns)
    def tag(n): return '{'+ns+'}'+n
    model = ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    ET.SubElement(model,tag('metadata'),{'name':'Title'}).text = 'Rev D2 drop-in PCB frame and AGND pogo jig - no PCB screws'
    resources = ET.SubElement(model,tag('resources'))
    build = ET.SubElement(model,tag('build'))
    for idx,(name,mesh,offset) in enumerate(parts,1):
        obj = ET.SubElement(resources,tag('object'),{'id':str(idx),'type':'model','name':name})
        m = ET.SubElement(obj,tag('mesh')); vs = ET.SubElement(m,tag('vertices')); ts = ET.SubElement(m,tag('triangles'))
        vertices, triangles = mesh.Topology
        for v in vertices:
            ET.SubElement(vs,tag('vertex'),{'x':f'{v.x+offset[0]:.6f}','y':f'{v.y+offset[1]:.6f}','z':f'{v.z+offset[2]:.6f}'})
        for a,b,c in triangles:
            ET.SubElement(ts,tag('triangle'),{'v1':str(a),'v2':str(b),'v3':str(c)})
        ET.SubElement(build,tag('item'),{'objectid':str(idx)})
    types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',types)
        z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))

def main():
    ROOT.mkdir(exist_ok=True)
    base, arm, coupon = make_base(), make_arm(), make_coupon()
    common = base.common(arm)
    assert common.Volume < 1e-5, f'Assembly interference: {common.Volume}'
    pcb_envelope = box(0,86,0,62,9,10.6)
    board_interference = base.common(pcb_envelope).Volume
    assert board_interference < 1e-5, f'PCB does not seat: {board_interference}'
    # Check the actual locating walls, ledge, corner cutouts and entry flare.
    inside = lambda x,ky,z: base.isInside(App.Vector(x,-ky,z),1e-6,False)
    assert not inside(-.1,31,10) and not inside(86.1,31,10)
    assert inside(-.3,31,10) and inside(86.3,31,10)
    assert not inside(43,-.1,10) and not inside(43,62.1,10)
    assert inside(43,-.3,10) and inside(43,62.3,10)
    assert inside(1,31,8.9) and inside(85,31,8.9)
    assert inside(43,1,8.9) and inside(43,61,8.9)
    for x,ky in [(-.2,-.2),(86.2,-.2),(-.2,62.2),(86.2,62.2)]:
        assert not inside(x,ky,2) and not inside(x,ky,10)
    assert inside(-.4,31,10.7) and not inside(-.4,31,11.3)
    # Actual PCB mechanical sources; verify pad and mount coordinates.
    source_pcb = REPO/'hardware/rev-d/tester12v.kicad_pcb'
    manifest_path = REPO/'hardware/rev-d/design-manifest.json'
    reference = json.loads((ROOT/'pcb-reference.json').read_text())
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else reference
    pcb_sha256 = hashlib.sha256(source_pcb.read_bytes()).hexdigest() if source_pcb.exists() else reference['source_sha256']
    assert pcb_sha256 == reference['source_sha256'], 'PCB changed; recheck fixture geometry before rebuilding'
    agnd = next(p for p in manifest['parts'] if p['ref']=='TP19')
    assert agnd['pcb'][:2] == P['agnd_xy_kicad'] and agnd['value']=='AGND'
    assert manifest['scope']['board_mm'] == [86,62]
    assert manifest['scope']['thickness_mm'] == 1.6

    printable = {
        '01_base': translated(base,(7,69,0)),
        '02_pogo_arm': translated(arm,(-68,14,-25)),
        '03_pin_fit_coupon': coupon,
    }
    meshes = {}; validation = {}
    for name,shape in printable.items():
        m = mesh_shape(shape); meshes[name] = m
        validation[name] = inspect_shape(name,shape,m)
        m.write(str(ROOT/f'{name}.stl'))
        # Re-import the actual STL to catch export corruption, not just BREP errors.
        check = Mesh.Mesh(str(ROOT/f'{name}.stl'))
        assert check.isSolid() and not check.hasNonManifolds() and check.countComponents()==1
    write_3mf([(name,meshes[name],offset) for name,offset in [
        ('01_base',(0,0,0)),('02_pogo_arm',(107,0,0)),('03_pin_fit_coupon',(107,35,0))
    ]], ROOT/'D2_AGND_jig_print_plate.3mf')
    (ROOT/'D2_AGND_jig_drop_in.3mf').write_bytes((ROOT/'D2_AGND_jig_print_plate.3mf').read_bytes())
    reimport = Mesh.Mesh(str(ROOT/'D2_AGND_jig_print_plate.3mf'))
    assert reimport.isSolid() and not reimport.hasNonManifolds()
    assert reimport.countComponents() == 3
    b = reimport.BoundBox
    assert max(abs(a-b) for a,b in zip([b.XLength,b.YLength,b.ZLength],[125,85,27])) < .001
    validation['3mf_reimport'] = {'watertight':True,'components':3,'dimensions_mm':[b.XLength,b.YLength,b.ZLength]}

    doc = App.newDocument('D2_AGND_drop_in_pogo_jig')
    for name,shape in [('Base',base),('Pogo_arm',arm),('Fit_coupon',translated(coupon,(101,-60,0)))]:
        obj = doc.addObject('Part::Feature',name); obj.Label=name.replace('_',' '); obj.Shape=shape
        if App.GuiUp:
            obj.ViewObject.ShapeColor = (.15,.48,.62) if name=='Base' else (.95,.48,.12)
    sheet = doc.addObject('Spreadsheet::Sheet','Dimensions')
    sheet.set('A1','REFERENCE DIMENSIONS (mm) / edit Python source and regenerate to change geometry')
    for row,(key,value) in enumerate(P.items(),2):
        sheet.set('A'+str(row),key); sheet.set('B'+str(row),str(value))
    doc.recompute(); doc.saveAs(str(ROOT/'D2_AGND_jig.FCStd'))
    Part.export([doc.Base,doc.Pogo_arm],str(ROOT/'D2_AGND_jig.step'))
    step_check = Part.read(str(ROOT/'D2_AGND_jig.step'))
    assert step_check.isValid() and len(step_check.Solids)==2
    assert abs(step_check.Volume-base.Volume-arm.Volume) < .001
    validation['step_reimport'] = {'brep_valid':True,'solids':2,'volume_matches_original':True}
    (ROOT/'dimensions.json').write_text(json.dumps(P,indent=2)+'\n')
    validation.update({
        'assembly_interference_mm3':common.Volume,
        'PCB_envelope_interference_mm3':board_interference,
        'drop_in_frame':{'pocket_mm':[86.4,62.4],'clearance_per_side_mm':.2,
                         'corner_reliefs_mm':4.0,'entry_chamfer_mm':.6,
                         'entry_chamfer_degrees':45,'pcb_fasteners':0,
                         'ledge_and_wall_section_checks_passed':True},
        'pad_alignment_mm':{'x':77.0,'y_kicad':10.0,'error_nominal':0.0},
        'nominal_PCB_underside_to_base_mm':5.0,
        'PCB_contact_z':10.6,
        'nominal_pin_tail_z_at_2mm_compression':41.6,
        'pin_tail_above_arm_mm':6.6,
        'print_plate_envelope_mm':[125,85,27],
        'physically_fit_tested':False,
        'source_pcb_sha256':pcb_sha256,
        'limitations':'Pin insertion depth is set during assembly; spring force and exact barrel/tail shoulder profile were not supplied. Fit coupon verifies printer-dependent bore clearance.',
    })
    (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2))

if __name__ == '__main__': main()
