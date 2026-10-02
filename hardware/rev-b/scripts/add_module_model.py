"""Dimensioned envelope only (4 x 5 x 1.28 mm), not a manufacturer STEP model."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'libraries/3d';folder.mkdir(exist_ok=True)
items=[]
def ent(s):items.append(s);return '#'+str(len(items))
app=ent("APPLICATION_CONTEXT('automotive_design')")
ctx=ent("PRODUCT_CONTEXT('',"+app+",'mechanical')")
prod=ent("PRODUCT('MIE1W0505BGLVH','MIE1W0505BGLVH','Package envelope only',("+ctx+"))")
form=ent("PRODUCT_DEFINITION_FORMATION('','',"+prod+")")
dctx=ent("PRODUCT_DEFINITION_CONTEXT('part definition',"+app+",'design')")
pdef=ent("PRODUCT_DEFINITION('design','',"+form+","+dctx+")")
pds=ent("PRODUCT_DEFINITION_SHAPE('','',"+pdef+")")
unit=ent("(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.))")
aunit=ent("(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.))")
sunit=ent("(NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT())")
unc=ent("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.000001),"+unit+",'distance_accuracy_value','')")
gctx=ent("(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(("+unc+")) GLOBAL_UNIT_ASSIGNED_CONTEXT(("+unit+","+aunit+","+sunit+")) REPRESENTATION_CONTEXT('',''))")
verts=[(-2.,-2.5,.03),(2.,-2.5,.03),(2.,2.5,.03),(-2.,2.5,.03),(-2.,-2.5,1.28),(2.,-2.5,1.28),(2.,2.5,1.28),(-2.,2.5,1.28)]
pts=[ent("CARTESIAN_POINT('',("+','.join(map(str,v))+"))") for v in verts]
faces=[]
for seq in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
 loop=ent("POLY_LOOP('',("+','.join(pts[i] for i in seq)+"))")
 bound=ent("FACE_OUTER_BOUND('',"+loop+",.T.)")
 a,b,c=[verts[i] for i in seq[:3]]
 u=tuple(b[i]-a[i] for i in range(3));w=tuple(c[i]-b[i] for i in range(3))
 norm=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
 axis=ent("DIRECTION('',("+','.join(map(str,norm))+"))")
 ref=ent("DIRECTION('',("+','.join(map(str,u))+"))")
 pos=ent("AXIS2_PLACEMENT_3D('',"+pts[seq[0]]+","+axis+","+ref+")")
 plane=ent("PLANE('',"+pos+")")
 faces.append(ent("FACE_SURFACE('',("+bound+"),"+plane+",.T.)"))
shell=ent("CLOSED_SHELL('',("+','.join(faces)+"))")
brep=ent("FACETED_BREP('Package envelope',"+shell+")")
rep=ent("FACETED_BREP_SHAPE_REPRESENTATION('',("+brep+"),"+gctx+")")
ent("SHAPE_DEFINITION_REPRESENTATION("+pds+","+rep+")")
text="ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('MPS package dimensional envelope only'),'2;1');\nFILE_NAME('MIE1W0505BGLVH.step','2026-09-30T00:00:00',(''),(''),'','', '');\nFILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\nENDSEC;\nDATA;\n"+'\n'.join('#'+str(i+1)+'='+x+';' for i,x in enumerate(items))+"\nENDSEC;\nEND-ISO-10303-21;\n"
(folder/'MIE1W0505BGLVH.step').write_text(text)
