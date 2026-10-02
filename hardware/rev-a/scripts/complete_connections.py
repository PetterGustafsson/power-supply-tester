"""Finish remaining connections on two copper layers; verify separately with DRC."""
from pathlib import Path
import heapq,math
import numpy as np
from PIL import Image,ImageDraw
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
def mm(x):return p.FromMM(x)
def vec(x,y):return p.VECTOR2I(mm(x),mm(y))
def xy(v):return p.ToMM(v.x),p.ToMM(v.y)
layers=[p.F_Cu,p.B_Cu]
# Autorouter connected A4 on front copper, leaving its original escape via unused.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) and t.GetNetname()=='A4' and abs(p.ToMM(t.GetPosition().x)-28.95)<.001:b.Delete(t)

def route(net,start,end,bounds):
 STEP=.05;X0,Y0,X1,Y1=bounds;W=round((X1-X0)/STEP)+1;H=round((Y1-Y0)/STEP)+1
 code=b.FindNet(net).GetNetCode()
 def grid(pos):x,y=xy(pos);return round((x-X0)/STEP),round((y-Y0)/STEP)
 def point(t):return vec(X0+t[0]*STEP,Y0+t[1]*STEP)
 obs=[];viaobs=[]
 for layer in layers:
  for radius,out in [(.1,obs),(.3,viaobs)]:
   im=Image.new('1',(W,H));d=ImageDraw.Draw(im);clear=.205+radius
   for fp in b.GetFootprints():
    for pad in fp.Pads():
     if pad.GetNetCode()==code or not pad.IsOnLayer(layer):continue
     box=pad.GetBoundingBox();x1,y1=xy(box.GetPosition());x2,y2=xy(box.GetEnd())
     d.rectangle(((x1-X0-clear)/STEP,(y1-Y0-clear)/STEP,(x2-X0+clear)/STEP,(y2-Y0+clear)/STEP),fill=1)
   for t in b.GetTracks():
    if t.GetNetCode()==code or not t.IsOnLayer(layer):continue
    a,z=grid(t.GetStart()),grid(t.GetEnd());width=t.GetWidth(layer) if isinstance(t,p.PCB_VIA) else t.GetWidth();r=(p.ToMM(width)/2+clear)/STEP
    d.line((a,z),fill=1,width=math.ceil(2*r))
    for x,y in (a,z):d.ellipse((x-r,y-r,x+r,y+r),fill=1)
   out.append(np.array(im,dtype=bool))
 sx,sy=grid(vec(*start));gx,gy=grid(vec(*end));src=(sx,sy,0);goal=(gx,gy,0)
 assert not obs[0][sy,sx] and not obs[0][gy,gx],(net,'blocked endpoint')
 def heuristic(t):dx,dy=abs(t[0]-gx),abs(t[1]-gy);return max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy)
 q=[(heuristic(src),0,src)];cost={src:0};prev={};found=None
 while q:
  _,c,u=heapq.heappop(q)
  if c!=cost[u]:continue
  if u==goal:found=u;break
  x,y,l=u
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1),(0,0)]:
   ll=1-l if dx==dy==0 else l;xx,yy=x+dx,y+dy
   if not 1<=xx<W-1 or not 1<=yy<H-1 or obs[ll][yy,xx]:continue
   if ll!=l and (viaobs[0][y,x] or viaobs[1][y,x]):continue
   if dx and dy and (obs[l][y,xx] or obs[l][yy,x]):continue
   z=(xx,yy,ll);nc=c+(30 if ll!=l else math.hypot(dx,dy))
   if nc<cost.get(z,1e12):cost[z]=nc;prev[z]=u;heapq.heappush(q,(nc+heuristic(z),nc,z))
 assert found is not None,(net,'No path')
 path=[found]
 while path[-1]!=src:path.append(prev[path[-1]])
 path=path[::-1];pts=[path[0]]
 for i in range(1,len(path)-1):
  a,u,z=path[i-1:i+2]
  if tuple(u[j]-a[j] for j in range(3))!=tuple(z[j]-u[j] for j in range(3)):pts.append(u)
 pts.append(path[-1])
 for a,z in zip(pts,pts[1:]):
  if a[2]!=z[2]:
   t=p.PCB_VIA(b);t.SetPosition(point(a));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
  else:
   t=p.PCB_TRACK(b);t.SetStart(point(a));t.SetEnd(point(z));t.SetLayer(layers[a[2]]);t.SetWidth(mm(.2))
  t.SetNetCode(code);b.Add(t)
 print(net,'completed',len(pts),'vertices',len(cost),'search states',flush=True)
 p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)

if __name__=='__main__':
 route('A1',(27.85,25.5),(22.5,32.95),(18,18,42,43))
 route('SENSE_EN',(30,47.775),(52,47.775),(18,20,65,58))
 route('SENSE_EN',(52,43.225),(74,43.225),(38,18,89,58))
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
