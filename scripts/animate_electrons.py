from pathlib import Path
import xml.etree.ElementTree as E
import math,random,sys
FAIL="--fail" in sys.argv
VOLTAGE_DEMO="--voltage-demo" in sys.argv
P=Path('output');D=P/('electron-fail-frames' if FAIL else 'electron-frames');D.mkdir(exist_ok=True)
N='http://www.w3.org/2000/svg';E.register_namespace('',N)
base=E.parse(P/('rendered-pins-wrong.svg' if FAIL else 'rendered-pins-correct.svg')).getroot()
A,B,C,Z=((338.56,542.72),(437,553),(586,465),(572.8,346.88)) if FAIL else ((512,688),(605,580),(585,440),(451.2,346.88))
def el(tag,attrs,parent):return E.SubElement(parent,f'{{{N}}}{tag}',{k:str(v) for k,v in attrs.items()})
def bez(t):
 # A shallow arc between the contacts, preserving a gentle outward bow.
 a,b,c,d=A,B,C,Z;u=1-t
 x=u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0]
 y=u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1]
 dx=3*u*u*(b[0]-a[0])+6*u*t*(c[0]-b[0])+3*t*t*(d[0]-c[0]);dy=3*u*u*(b[1]-a[1])+6*u*t*(c[1]-b[1])+3*t*t*(d[1]-c[1]);l=math.hypot(dx,dy)
 return x,y,-dy/l,dx/l
random.seed(9);particles=[(random.random(),random.random()*math.tau,random.uniform(.2,1),random.uniform(1,2.9)) for _ in range(180)]
for frame in range(48):
 root=E.fromstring(E.tostring(base));defs=root.find(f'{{{N}}}defs')
 f=el('filter',{'id':'electron-bloom','x':'-70%','y':'-70%','width':'240%','height':'240%'},defs);el('feGaussianBlur',{'stdDeviation':'4'},f)
 grad=el('linearGradient',{'id':'beam-color','gradientUnits':'userSpaceOnUse','x1':A[0],'y1':A[1],'x2':Z[0],'y2':Z[1]},defs)
 el('stop',{'offset':0,'stop-color':'#69deff'},grad);el('stop',{'offset':.48,'stop-color':'#b7eef0'},grad);el('stop',{'offset':1,'stop-color':'#ffcf76'},grad)
 # Steady 24V preview: periodic motion loops without a startup ramp or fade.
 t=frame/48;strength=1.0
 if VOLTAGE_DEMO:
  # 0V pause, 1.2s linear rise, 1.8s hold, then a single-frame drop.
  strength=max(0,min(1,(frame-4)/12)) if frame<34 else 0.0
 children=list(root);idx=next(i for i,x in enumerate(children) if x.get('id')=='machine-result')
 g=E.Element(f'{{{N}}}g',{'id':'electron-tunnel','opacity':str(min(1,strength*2))});root.insert(idx,g)
 center=f'M{A[0]} {A[1]} C{B[0]} {B[1]} {C[0]} {C[1]} {Z[0]} {Z[1]}'
 el('path',{'d':center,'fill':'none','stroke':'url(#beam-color)','stroke-width':9+strength*17,'opacity':.10*strength,'filter':'url(#electron-bloom)'},g)
 # Faint curving strands define a tube without masking the metal and contacts.
 for phase in [0,math.pi/2,math.pi,math.pi*1.5]:
  pts=[]
  for j in range(81):
   u=j/80;x,y,nx,ny=bez(u);r=(math.sin(math.pi*u)**.65)*22*math.sin(phase+u*math.tau*2-math.tau*t)
   pts.append(f'{x+nx*r:.2f},{y+ny*r:.2f}')
  el('polyline',{'points':' '.join(pts),'fill':'none','stroke':'url(#beam-color)','stroke-width':1.1,'opacity':.12*strength},g)
 for k,(offset,phase,rad,size) in enumerate(particles):
  if k>25+155*strength:continue
  u=(offset+t)%1;x,y,nx,ny=bez(u)
  angle=phase+u*math.tau*2+math.tau*t
  radius=(math.sin(math.pi*u)**.65)*25*rad
  depth=math.cos(angle);x+=nx*radius*math.sin(angle);y+=ny*radius*math.sin(angle)
  r=int(105+150*u);gg=int(222-15*u);b=int(255-137*u);color=f'#{r:02x}{gg:02x}{b:02x}'
  opacity=(.2+.7*strength)*(.55+.45*(depth+1)/2)*min(1,u*15,(1-u)*15)
  if k%4==0:el('circle',{'cx':x,'cy':y,'r':size*2.7,'fill':color,'opacity':opacity*.55,'filter':'url(#electron-bloom)'},g)
  el('circle',{'cx':x,'cy':y,'r':size*(.7+.4*strength),'fill':color,'opacity':opacity},g)
  # Tiny motion trails follow the curved field direction.
  x2,y2,_,_=bez(max(0,u-.012));dx=x-x2;dy=y-y2
  if k%3==0:el('path',{'d':f'M{x:.2f} {y:.2f}l{-dx*.35:.2f} {-dy*.35:.2f}','stroke':color,'stroke-width':size*.55,'opacity':opacity*.5},g)
 # Traveling specular reflections stay within the full-width green collar.
 collar=next(e for e in root.iter() if e.get('id')=='machine-result')
 if FAIL:
  # Three gentle brightness pulses per 4.8-second loop; always visibly red.
  brightness=.55+.45*(.5+.5*math.cos(math.tau*t*3))
  filt=el('filter',{'id':'failure-pulse','color-interpolation-filters':'sRGB'},defs)
  transfer=el('feComponentTransfer',{},filt)
  for channel in ['R','G','B']:el('feFunc'+channel,{'type':'linear','slope':brightness},transfer)
  collar.set('filter','url(#failure-pulse)')
 shimmer=el('g',{'id':'collar-shimmer'},collar)
 ri,ro=403.9,440.9
 def ring_sector(a,b):
  def pt(r,a):return (512+r*math.cos(a),512+r*math.sin(a))
  a0,a1,b1,b0=pt(ro,a),pt(ro,b),pt(ri,b),pt(ri,a)
  return f'M{a0[0]:.3f} {a0[1]:.3f}A{ro} {ro} 0 0 1 {a1[0]:.3f} {a1[1]:.3f}L{b1[0]:.3f} {b1[1]:.3f}A{ri} {ri} 0 0 0 {b0[0]:.3f} {b0[1]:.3f}Z'
 for j in range(240):
  a=math.tau*j/240;b=math.tau*(j+1.025)/240
  moving=a-math.tau*t+.7
  # A broad reflection and a narrower glint trail around the collar.
  delta=math.atan2(math.sin(moving),math.cos(moving))
  opposite=math.atan2(math.sin(moving-math.pi),math.cos(moving-math.pi))
  shine=.66*math.exp(-.5*(delta/.22)**2)+.36*math.exp(-.5*(opposite/.43)**2)
  if shine>.008:el('path',{'d':ring_sector(a,b),'fill':'#ffe3e5' if FAIL else '#e4fff2','opacity':shine},shimmer)
 # The ring remains the machine's pin-pair verdict, separate from voltage.
 if VOLTAGE_DEMO:
  power_id='detected-pin-9' if FAIL else 'detected-pin-1'
  for node in root.iter():
   if node.tag==f'{{{N}}}text' and node.text=='+24V':node.text=f'+{24*strength:.0f}V'
   if node.get('id')==power_id:node.set('opacity',str(strength))
 E.ElementTree(root).write(D/f'{frame:02}.svg',encoding='unicode')
 if frame==24:E.ElementTree(root).write(P/('electron-tunnel-fail-concept.svg' if FAIL else 'electron-tunnel-concept.svg'),encoding='unicode')
