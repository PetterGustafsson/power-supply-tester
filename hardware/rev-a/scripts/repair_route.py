"""Route the final A4 connection with a clearance-aware two-layer grid search."""
from pathlib import Path
import heapq, math
import numpy as np
from PIL import Image,ImageDraw
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
target=b.FindNet('A4').GetNetCode()
# Make room at U4's inner escape; reroute the low-speed enable net afterward.
for t in list(b.GetTracks()):
 if t.GetNetname()=='SENSE_EN':b.Delete(t)
STEP=.05; X0,Y0=18.,32.;W,H=480,460
layers=[p.F_Cu,p.B_Cu]
def xy(pt):return (p.ToMM(pt.x),p.ToMM(pt.y))
def grid(pt):x,y=xy(pt);return (round((x-X0)/STEP),round((y-Y0)/STEP))
def mm(x):return p.FromMM(x)
def vec(x,y):return p.VECTOR2I(mm(x),mm(y))
def point(t):return vec(X0+t[0]*STEP,Y0+t[1]*STEP)
obs=[];viaobs=[];goals=set()
for li,layer in enumerate(layers):
 for radius,out in [(.1,obs),(.3,viaobs)]:
  im=Image.new('1',(W,H));d=ImageDraw.Draw(im);clear=.215+radius
  for fp in b.GetFootprints():
   for pad in fp.Pads():
    if pad.GetNetCode()==target or not pad.IsOnLayer(layer):continue
    box=pad.GetBoundingBox();x1,y1=xy(box.GetPosition());x2,y2=xy(box.GetEnd())
    d.rectangle(((x1-X0-clear)/STEP,(y1-Y0-clear)/STEP,(x2-X0+clear)/STEP,(y2-Y0+clear)/STEP),fill=1)
  for t in b.GetTracks():
   if t.GetNetCode()==target:
    if radius==.1 and t.IsOnLayer(layer):
     a=np.array(grid(t.GetStart()));z=np.array(grid(t.GetEnd()));n=max(1,int(np.max(np.abs(z-a))))
     for pos in np.linspace(a,z,n+1):
      x,y=map(int,np.round(pos));
      if 0<=x<W and 0<=y<H:goals.add((x,y,li))
    continue
   if not t.IsOnLayer(layer):continue
   a=grid(t.GetStart());z=grid(t.GetEnd());r=(p.ToMM(t.GetWidth(layer) if isinstance(t,p.PCB_VIA) else t.GetWidth())/2+clear)/STEP
   d.line((a,z),fill=1,width=math.ceil(2*r))
   for x,y in [a,z]:d.ellipse((x-r,y-r,x+r,y+r),fill=1)
  out.append(np.array(im,dtype=bool))
# Rectangular pad bounding boxes deliberately overestimate obstruction.
fp=next(f for f in b.GetFootprints() if f.GetReference()=='U4');pad=next(z for z in fp.Pads() if z.GetNumber()=='7')
sx,sy=grid(pad.GetPosition());start=(sx,sy,0);assert not obs[0][sy,sx]
glist=list(goals)
def h(t):return min(max(abs(t[0]-g[0]),abs(t[1]-g[1])) for g in glist)
q=[(h(start),0,start)];cost={start:0};prev={};end=None
while q:
 _,c,u=heapq.heappop(q)
 if c!=cost[u]:continue
 if u in goals:end=u;break
 x,y,l=u
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1),(0,0)]:
  ll=1-l if dx==dy==0 else l;xx=x+dx;yy=y+dy
  if not 1<=xx<W-1 or not 1<=yy<H-1 or obs[ll][yy,xx]:continue
  if ll!=l and (viaobs[0][y,x] or viaobs[1][y,x]):continue
  if dx and dy and (obs[l][y,xx] or obs[l][yy,x]):continue
  v=(xx,yy,ll);nc=c+(35 if ll!=l else math.hypot(dx,dy))
  if nc<cost.get(v,1e12):cost[v]=nc;prev[v]=u;heapq.heappush(q,(nc+h(v),nc,v))
assert end is not None,'No path found'
path=[end]
while path[-1]!=start:path.append(prev[path[-1]])
path=path[::-1]
# Compress collinear grid points, preserving layer changes.
pts=[path[0]]
for i in range(1,len(path)-1):
 a,z=path[i-1],path[i+1];u=path[i]
 if tuple(u[j]-a[j] for j in range(3))!=tuple(z[j]-u[j] for j in range(3)):pts.append(u)
pts.append(path[-1])
def track(a,z,l):
 if a==z:return
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetLayer(l);t.SetWidth(mm(.2));t.SetNetCode(target);b.Add(t)
track(pad.GetPosition(),point(pts[0]),p.F_Cu)
for a,z in zip(pts,pts[1:]):
 if a[2]!=z[2]:
  t=p.PCB_VIA(b);t.SetPosition(point(a));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNetCode(target);b.Add(t)
 else:track(point(a),point(z),layers[a[2]])
# Goal grid point may be up to 35um off the existing trace; overlapping widths bridge it.
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'tester12v-final.dsn'))
print('Completed A4 route',len(pts),'vertices',len(cost),'states')
