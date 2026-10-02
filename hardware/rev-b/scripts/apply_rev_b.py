"""Rebuild Rev B from the preserved, routed Rev A board; reroute separately."""
import json
import pcbnew as p
import build_kicad as g
from design import ROOT,PARTS
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
# Land pattern from MPS datasheet Rev 1.0 page 16, top view. Split connected
# paired lands along their centre so all 12 schematic pin numbers are retained.
lines=['(footprint "MIE1W0505BGLVH" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)',
 '(descr "MPS MIE1W0505BGLVH LGA12 4x5mm; Rev1.0 p16 lands; pin1 upper left")',
 '(property "Reference" "U7" (at 0 -3.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
 '(property "Value" "MIE1W0505BGLVH" (at 0 3.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))']
for n,x,y in [(1,-1.6375,-2.0875),(8,1.6375,-2.0875),(2,-1.6375,2.0875),(7,1.6375,2.0875)]:
 lines.append(f'(pad "{n}" smd rect (at {x} {y}) (size .575 .675) (layers "F.Cu" "F.Paste" "F.Mask"))')
for y,nums in [(-2.0875,[12,11,10,9]),(2.0875,[3,4,5,6])]:
 for i,(x,n) in enumerate(zip([-.825,-.375,.375,.825],nums)):
  # Each half is .45 wide; the .30-wide notch straddles the joined pair.
  notch_right=i%2==0
  points=[(-.225,-.3375),(.075,-.3375),(.075,-.2125),(.225,-.2125),(.225,.3375),(-.225,.3375)]
  if not notch_right:points=[(-a,b) for a,b in points]
  if y>0:points=[(a,-b) for a,b in points]
  pts=' '.join(f'(xy {a} {b})' for a,b in points)
  lines.append(f'(pad "{n}" smd custom (at {x} {y}) (size .1 .1) (layers "F.Cu" "F.Paste" "F.Mask") (options (clearance outline) (anchor rect)) (primitives (gr_poly (pts {pts}) (width 0) (fill yes))))')
for layer,w,h in [('F.Fab',2,2.5),('F.CrtYd',2.25,2.75)]:
 lines.append(f'(fp_rect (start {-w} {-h}) (end {w} {h}) (stroke (width .05) (type default)) (fill none) (layer "{layer}"))')
lines.append('(fp_circle (center -1.5 -1.2) (end -1.3 -1.2) (stroke (width .12) (type default)) (fill none) (layer "F.SilkS"))')
lines.append('(model "${KIPRJMOD}/libraries/3d/MIE1W0505BGLVH.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
lines.append(')')
(g.FPDIR/'MIE1W0505BGLVH.kicad_mod').write_text('\n'.join(lines))
g.copy_libraries()
b=p.LoadBoard(str(ROOT.parent/'rev-a/tester12v.kicad_pcb'))
# Remove only local power routing; preserve the rest of the verified Rev A copper.
removed=[]
for t in list(b.GetTracks()):
 pts=[t.GetStart(),t.GetEnd()]
 if all(p.ToMM(pt.x)<28.5 and p.ToMM(pt.y)<22 for pt in pts) and t.GetNetname() in ('USB5V_F','USB_GND','ISO5V','AGND'):
  removed.append(t.GetNetname());b.Delete(t)
parts={x['ref']:x for x in PARTS}
for f in list(b.GetFootprints()):
 ref=f.GetReference();part=parts.get(ref)
 if not part:continue
 oldpads={q.GetNumber():q.GetPosition() for q in f.Pads()}
 replace=ref=='U7' or ref in ['D'+str(i) for i in range(1,13)]
 if replace:
  nf=p.FootprintLoad(str(g.FPDIR),part['fp'].split(':')[1]);nf.SetFPID(p.LIB_ID('Tester',part['fp'].split(':')[1]));nf.SetReference(ref);nf.SetPath(f.GetPath());b.Remove(f);b.Add(nf);f=nf
  f.Reference().SetLayer(p.F_Fab);f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(mm(.12))
 f.SetValue(part['value']);f.Value().SetVisible(False)
 if ref in ['U7','C19','C20','C21','C22'] or replace:
  x,y,a=part['pcb'];f.SetPosition(v(x,y));f.SetOrientationDegrees(a)
  f.Reference().SetPosition(v(x,y-2.7));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 for pad in f.Pads():
  net=part['pins'][pad.GetNumber()]
  if net:pad.SetNet(b.FindNet(net))
  if ref.startswith('D') and ref!='D13' and oldpads[pad.GetNumber()]!=pad.GetPosition():
   t=p.PCB_TRACK(b);t.SetStart(oldpads[pad.GetNumber()]);t.SetEnd(pad.GetPosition());t.SetWidth(mm(.2));t.SetLayer(p.F_Cu);t.SetNetCode(pad.GetNetCode());b.Add(t)
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and 'REV A' in d.GetText():d.SetText(d.GetText().replace('REV A','REV B'))
b.GetTitleBlock().SetRevision('B')
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
for f in b.GetFootprints():
 if f.GetReference() in ['U7','C19','C20','C21','C22','F1']:
  print(f.GetReference(),[(q.GetNumber(),q.GetNetname(),p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)) for q in f.Pads()])
print('Removed local segments',len(removed))
