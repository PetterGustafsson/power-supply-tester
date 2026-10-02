from pathlib import Path
import pcbnew as p
import build_kicad as g
from design import PARTS,ROOT,uid
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
assert not any(f.GetReference()=='D13' for f in b.GetFootprints())
g.copy_libraries();d=next(c for c in PARTS if c['ref']=='D13')
lib,name=d['local_fp'].split(':');f=p.FootprintLoad(str(g.FPDIR),name);f.SetFPID(p.LIB_ID(lib,name));f.SetReference('D13');f.SetValue(d['value']);f.SetPosition(g.vec(33,15));f.Reference().SetLayer(p.F_Fab);f.Reference().SetPosition(g.vec(33,12.5));f.Value().SetVisible(False)
path=p.KIID_PATH();path.push_back(p.KIID(uid('root')));path.push_back(p.KIID(d['uuid']));f.SetPath(path)
for z in f.Pads():z.SetNet(b.FindNet(d['pins'][z.GetNumber()]))
b.Add(f)
# Remove the unused A4 escape stub identified by DRC.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='A4' and abs(t.GetLength()/1e6-1.8125)<.0001:b.Delete(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
