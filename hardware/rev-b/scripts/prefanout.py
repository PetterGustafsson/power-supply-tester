"""Place fixed switch enable buses and drain escape vias before autorouting."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
assert not list(b.GetTracks())
def mm(x):return p.FromMM(x)
def vec(x,y):return p.VECTOR2I(mm(x),mm(y))
def tr(a,z,net):
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetLayer(p.F_Cu);t.SetWidth(mm(.2));t.SetNetCode(net);b.Add(t)
for ref in ['U4','U5','U6']:
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref);pads={z.GetNumber():z for z in f.Pads()};cx=p.ToMM(f.GetPosition().x)
 en=pads['1'].GetNetCode()
 tr(pads['1'].GetPosition(),pads['16'].GetPosition(),en)
 tr(pads['8'].GetPosition(),pads['9'].GetPosition(),en)
 tr(vec(cx,43.225),vec(cx,47.775),en)
 a=pads['7'].GetPosition();dest=vec(cx-1.05,47.125);net=pads['7'].GetNetCode();tr(a,dest,net)
 via=p.PCB_VIA(b);via.SetPosition(dest);via.SetWidth(mm(.6));via.SetDrill(mm(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(net);b.Add(via)
p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b);p.ExportSpecctraDSN(b,str(ROOT/'tester12v-prefanout.dsn'))
print('Fixed switch fanout added')
