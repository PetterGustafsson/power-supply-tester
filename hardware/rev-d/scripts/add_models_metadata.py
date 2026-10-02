"""Add dimensioned visual envelopes and purchasing metadata; preserve copper."""
from pathlib import Path
import math
import pcbnew as p
from design import ROOT,PARTS,SYMS
folder=ROOT/'libraries/3d';folder.mkdir(exist_ok=True)
def box(center,size,color):
    # KiCad VRML length unit is 0.1 inch; convert dimensions from mm.
    return 'Transform { translation %s children [ Shape { appearance Appearance { material Material { diffuseColor %s } } geometry Box { size %s } } ] }\n'%(' '.join(str(x/2.54) for x in center),' '.join(map(str,color)),' '.join(str(x/2.54) for x in size))
def cylinder(center,radius,height,color,vertical=False):
    # Use explicit triangles: KiCad's VRML importer omits Cylinder primitives.
    n=32;points=[]
    def point(a,b,t):
        dx,dy,dz=(a,b,t) if vertical else (a,t,b)
        return (center[0]+dx,center[1]+dy,center[2]+dz)
    for t in (-height/2,height/2):
        points.extend(point(radius*math.cos(i*2*math.pi/n),radius*math.sin(i*2*math.pi/n),t) for i in range(n))
    points.extend([point(0,0,-height/2),point(0,0,height/2)])
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([[i,2*n,j],[n+i,n+j,2*n+1],[i,j,n+j],[i,n+j,n+i]])
    return 'Shape { appearance Appearance { material Material { diffuseColor %s } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n'%(' '.join(map(str,color)),', '.join(' '.join(str(v/2.54) for v in pt) for pt in points),', '.join(' '.join(map(str,face+[-1])) for face in faces))
def prism(x0,x1,profile,color):
    points=[(x,y,z) for x in (x0,x1) for y,z in profile];n=len(profile)
    faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
    return 'Shape { appearance Appearance { material Material { diffuseColor %s } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n'%(' '.join(map(str,color)),', '.join(' '.join(str(v/2.54) for v in pt) for pt in points),', '.join(' '.join(map(str,face+[-1])) for face in faces))
power='#VRML V2.0 utf8\n# EVISUN dimensional envelope, not a vendor detailed model.\n'
power+=box((3.81,2.1,5.1),(11.68,6,10.2),(.08,.08,.08))
for i in range(4):power+=box((i*2.54,0,-1.75),(.5,.3,3.5),(.7,.7,.7))
(folder/'B0305S_envelope.wrl').write_text(power)
term='#VRML V2.0 utf8\n# XY350V body/pitch/height from C557656 drawing. Openings and screw details illustrative.\n# Entry is model +Y = footprint -Y. At PCB rotation 180 it faces board +Y.\n'
green=(.04,.35,.12);metal=(.65,.65,.65)
term+=box((5.25,0,.4),(14,6.9,.8),green)
term+=box((5.25,-.875,2.45),(14,5.15,3.3),green)
term+=prism(-1.75,12.25,[(-3.45,4.1),(3.45,4.1),(3.45,4.6),(1.75,8.4),(-1.75,8.4),(-3.45,4.6)],green)
for x,w in [(-1.475,.55),(1.75,1.1),(5.25,1.1),(8.75,1.1),(11.975,.55)]:
    term+=box((x,2.575,2.45),(w,1.75,3.3),green)
for i in range(4):
    term+=box((i*3.5,0,-1.75),(.8,.8,3.5),(.7,.7,.7))
    term+=box((i*3.5,1.73,2.35),(2.15,.06,2.5),metal)
    term+=cylinder((i*3.5,1.775,2.35),.8,.04,(.07,.07,.07))
    term+=cylinder((i*3.5,0,8.5),1.1,.18,metal,True)
    term+=box((i*3.5,0,8.595),(1.9,.22,.01),(.08,.08,.08))
(folder/'XY350V_envelope.wrl').write_text(term)
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'));parts={q['ref']:q for q in PARTS}
for f in b.GetFootprints():
    ref=f.GetReference()
    if ref.startswith('H'):f.SetBoardOnly(True);continue
    q=parts[ref]
    for pad in f.Pads():
        n=pad.GetNumber()
        if n in q['pins'] and q['pins'][n] is None:
            name=next(z['name'] for z in SYMS[q['sym']]['pins'] if z['n']==n)
            netname=f'unconnected-({ref}-{name}-Pad{n})'
            net=b.FindNet(netname)
            if not net:net=p.NETINFO_ITEM(b,netname);b.Add(net)
            pad.SetNet(net)
    if ref.startswith('TP'):f.SetExcludedFromBOM(True);continue
    for key,value in [('MPN',q['mpn']),('Manufacturer',q['maker']),('LCSC',q.get('lcsc','')),('JLC Category',q.get('jlc_category',''))]:
        field=f.GetFieldByName(key)
        if not field:field=p.PCB_FIELD(f,f.GetNextFieldId(),key);f.Add(field)
        field.SetText(value);field.SetVisible(False)
    model=None
    if ref=='U7':model='B0305S_envelope.wrl'
    if ref in ('J1','J2','J3'):model='XY350V_envelope.wrl'
    if model:
        f.Models().clear();m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/libraries/3d/'+model;f.Add3DModel(m)
p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
print('Metadata and dimensioned component envelopes updated; copper preserved.')
