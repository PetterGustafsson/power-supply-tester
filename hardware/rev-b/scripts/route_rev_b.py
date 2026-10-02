import pcbnew as p
import complete_connections as r
b=r.b;v=r.vec;mm=r.mm
# Move the five existing S-net detours 0.1 mm outwards for the wider SOD-123 lands.
for net,cx in [('S4',37.5),('S5',44.5),('S8',59.5),('S10',71.5),('S12',81.5)]:
 for t in b.GetTracks():
  if t.GetNetname()!=net or isinstance(t,p.PCB_VIA):continue
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   pt=get();x,y=r.xy(pt)
   if 51.2<y<55 and .7<abs(x-cx)<1.05:setter(v(x+(.12 if x>cx else -.12),y))
def track(net,a,c,width=.3,layer=p.F_Cu):
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetLayer(layer);t.SetWidth(mm(width));t.SetNet(b.FindNet(net));b.Add(t)
def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));b.Add(t)
for net,x,capx in [('USB5V_F',13.9125,12.2),('ISO5V',18.0875,19.8)]:
 track(net,(x,9.3625),(x,10.625))
 track(net,(x,10.175),(capx,10.05))
for net,x,capx,vx in [('USB_GND',13.9125,12.2,13.5),('AGND',18.0875,19.8,18.5)]:
 track(net,(x,11.375),(x,12.6375))
 track(net,(x,11.825),(capx,11.95))
 track(net,(x,12.6375),(vx,13.5));via(net,vx,13.5)
for net,a,z in [('USB5V_F',(9.9,10.05),(12.2,10.05)),('USB_GND',(9.9,11.95),(12.2,11.95)),('ISO5V',(19.8,10.05),(22.1,10.05)),('AGND',(19.8,11.95),(22.1,11.95))]:track(net,a,z)
# Connect fuse to module input with .4mm copper; keep entirely on host side.
track('USB5V_F',(6,6.6),(9.9,6.6),.4);track('USB5V_F',(9.9,6.6),(9.9,10.05),.4)
for t in list(b.GetTracks()):
 if t.GetNetname()=='ISO5V' and abs(p.ToMM(t.GetEnd().x)-26.05)<.001 and abs(p.ToMM(t.GetEnd().y)-15.9)<.001:b.Delete(t)
# Existing ISO5V exits were preserved at the boundary of the modified area.
for t in b.GetTracks():
 if t.GetNetname()=='ISO5V' and (p.ToMM(t.GetStart().x)<33 and p.ToMM(t.GetStart().y)<22):
  print('ISO',r.xy(t.GetStart()),r.xy(t.GetEnd()),t.GetLayer())
p.SaveBoard(str(r.ROOT/'tester12v.kicad_pcb'),b)
r.route('ISO5V',(22.1,10.05),(31.8625,10.95),(17.6,1,37,22))
r.route('ISO5V',(22.1,10.05),(28.8,15.9),(17.6,1,37,22))
# Restore the removed layer transition at the old secondary branch.
via('ISO5V',27.8615,16.2364)
r.route('ISO5V',(28.8,15.9),(27.8615,16.2364),(17.6,1,37,22))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(r.ROOT/'tester12v.kicad_pcb'),b)
