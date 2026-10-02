"""Synchronize NC nets and pre-route the low-resistance 5V supply paths."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
def mm(v):return p.FromMM(v)
def v(x,y):return p.VECTOR2I(mm(x),mm(y))
def xy(z):return p.ToMM(z.x),p.ToMM(z.y)
fps={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,n):return next(z for z in fps[ref].Pads() if z.GetNumber()==str(n))
for net in ET.parse(ROOT/'validation/schematic.net').findall('./nets/net'):
 name=net.attrib['name'];n=b.FindNet(name)
 if not n:n=p.NETINFO_ITEM(b,name);b.Add(n)
 for node in net.findall('node'):
  ref=node.attrib['ref']
  if ref in fps:pad(ref,node.attrib['pin']).SetNet(n)
def line(net,a,c,width=.2,layer=p.F_Cu):
 z=p.PCB_TRACK(b);z.SetStart(v(*a));z.SetEnd(v(*c));z.SetWidth(mm(width));z.SetLayer(layer);z.SetNet(b.FindNet(net));z.SetLocked(True);b.Add(z)
def via(net,x,y):
 z=p.PCB_VIA(b);z.SetPosition(v(x,y));z.SetWidth(mm(.6));z.SetDrill(mm(.3));z.SetViaType(p.VIATYPE_THROUGH);z.SetLayerPair(p.F_Cu,p.B_Cu);z.SetNet(b.FindNet(net));z.SetLocked(True);b.Add(z)
# Input terminals are paired contacts. Broad copper stays outside fine pitch pads.
a=xy(pad('J4',3).GetPosition());c=xy(pad('J4',4).GetPosition());line('V5_IN',a,c,1.5)
line('V5_IN',a,(a[0],44),1.5);line('V5_IN',(a[0],44),xy(pad('F1',1).GetPosition()),1.5)
for n in (5,6,7,8):
 z=xy(pad('Q1',n).GetPosition());line('V5_F',z,(64,z[1]),.4)
line('V5_F',(64,33.095),(64,42),1.0);line('V5_F',(64,42),xy(pad('F1',2).GetPosition()),1.5)
for n in (1,2,3):
 z=xy(pad('Q1',n).GetPosition());line('V5',z,(56,z[1]),.4)
line('V5',(56,33.095),(56,35.635),.6);via('V5',56,34.2);via('V5',56,35.1)
line('V5',(56,34.2),(56,40.5),1.5,p.B_Cu);line('V5',(56,40.5),(4.2,40.5),1.5,p.B_Cu)
# Six CM5 5V contacts fan out independently to a common low-resistance bus.
for n in (77,79,81,83,85,87):
 z=xy(pad('J5',n).GetPosition());line('V5',z,(4.2,z[1]),.2)
y1=xy(pad('J5',77).GetPosition())[1];y2=xy(pad('J5',87).GetPosition())[1]
line('V5',(4.2,y1),(4.2,y2),.6);via('V5',4.2,40.5);via('V5',4.2,41.5)
line('V5',(4.2,40.5),(4.2,41.5),1.0,p.B_Cu)
# Tie the adjacent custom converter lands before exporting to the autorouter.
for net,ns,x in [('V5',(8,9,10),73.8),('HGND',(1,11,12),73.8),('A3V3_RAW',(5,6),79.2),('AGND',(2,3,4,7),79.2)]:
 ys=[]
 for n in ns:
  a=xy(pad('U7',n).GetPosition());ys.append(a[1]);line(net,a,(x,a[1]),.2)
 # AGND VSEL pin7 is remote from pin2/3/4; do not short across output pads5/6.
 if net=='AGND':
  line(net,(x,min(ys)),(80,min(ys)),.2);line(net,(80,min(ys)),(80,max(ys)),.2);line(net,(80,max(ys)),(x,max(ys)),.2)
  g=[xy(pad('U7',n).GetPosition())[1] for n in (2,3,4)];line(net,(x,min(g)),(x,max(g)),.2)
 else:line(net,(x,min(ys)),(x,max(ys)),.2)
b.BuildConnectivity();p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b);p.ExportSpecctraDSN(b,str(ROOT/'tester12v.dsn'))
print('Fixed feed and converter lands prepared:',len(list(b.GetTracks())),'objects')
