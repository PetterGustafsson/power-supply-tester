from pathlib import Path
import math, json, random
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
# Mating-face coordinates in mm. Catalog p.193 mirrored horizontally;
# numbering checked against Hirose EDC-010386-73-73 revision 4.
pins={1:(-.95,-2.58),2:(-2.38,-1.1),3:(-2.71,.48),4:(-1.77,2.1),5:(0,2.75),6:(1.77,2.1),7:(2.71,.48),8:(2.38,-1.1),9:(.95,-2.58),10:(0,-1.38),11:(-.95,.55),12:(.95,.55)}
S=64; C=512
parts=[]
def add(s): parts.append(s)
def circle(r,fill,stroke=None,sw=.01,extra=''):
 add(f'<circle cx="512" cy="512" r="{r*S:.5f}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw*S}"' if stroke else '')+f' {extra}/>')
def point(r,a):return (C+S*r*math.cos(a),C+S*r*math.sin(a))
def annulus(ri,ro,a,b):
 p=[point(ro,a),point(ro,b),point(ri,b),point(ri,a)]
 return f'M {p[0][0]:.4f} {p[0][1]:.4f} A {ro*S} {ro*S} 0 0 1 {p[1][0]:.4f} {p[1][1]:.4f} L {p[2][0]:.4f} {p[2][1]:.4f} A {ri*S} {ri*S} 0 0 0 {p[3][0]:.4f} {p[3][1]:.4f} Z'
def metal(ri,ro,base=174,contrast=50):
 # Analytic directional reflections, drawn as pure vectors (no bitmap textures).
 add('<g stroke-width="0.7" stroke-linejoin="round">')
 for i in range(480):
  a=2*math.pi*i/480;b=2*math.pi*(i+1.02)/480
  v=base+contrast*(.58*math.cos(2*(a+.65))+.22*math.cos(5*a+.6)+.12*math.sin(11*a))
  v=max(22,min(248,round(v)))
  col=f'#{v:02x}{min(255,v+1):02x}{min(255,v+2):02x}'
  add(f'<path d="{annulus(ri,ro,a,b)}" fill="{col}" stroke="{col}"/>')
 add('</g>')
def keypath(ri,ro,a,w):
 # Parallel sides, with both curved ends concentric to the connector axis.
 hi=math.asin(w/(2*ri)); ho=math.asin(w/(2*ro))
 p=[point(ri,a-hi),point(ro,a-ho),point(ro,a+ho),point(ri,a+hi)]
 return f'M{p[0][0]:.4f} {p[0][1]:.4f} L{p[1][0]:.4f} {p[1][1]:.4f} A{ro*S} {ro*S} 0 0 1 {p[2][0]:.4f} {p[2][1]:.4f} L{p[3][0]:.4f} {p[3][1]:.4f} A{ri*S} {ri*S} 0 0 0 {p[0][0]:.4f} {p[0][1]:.4f} Z'
def build(labels=False):
 parts.clear()
 add('''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-labelledby="connector-title connector-desc">
<title id="connector-title">Hirose HR10A-10P-12P(73), male plug, mating face</title>
<desc id="connector-desc">Orthographic front view, main key at 12 o'clock. Twelve silver contacts in black polyamide, with a matte nickel shell. Pin 1 is upper left; pin 9 upper right. Independently authored UI illustration referencing Hirose mechanical drawing EDC-010386-73-73 and HR10 catalog. Surface finish, knurl microgeometry and pin tip profiles are illustrative. Not a manufacturing drawing.</desc>
<metadata>Units: 64 SVG units per mm. Maximum shell diameter: 14.7 mm. Transparent background. Projection: mating side. Contact IDs: pin-1 through pin-12. Sources and accuracy limits: README.md and geometry.json.</metadata>
<defs>
 <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f8f8f5"/><stop offset=".28" stop-color="#9fa09e"/><stop offset=".49" stop-color="#eeefec"/><stop offset=".73" stop-color="#6d706f"/><stop offset="1" stop-color="#c2c5c3"/></linearGradient>
 <linearGradient id="wall" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#171a1c"/><stop offset=".3" stop-color="#444845"/><stop offset=".58" stop-color="#8d8f88"/><stop offset=".8" stop-color="#4a4d48"/><stop offset="1" stop-color="#b1b2aa"/></linearGradient>
 <radialGradient id="polyamide" cx=".32" cy=".24" r=".88"><stop stop-color="#303337"/><stop offset=".44" stop-color="#212428"/><stop offset=".82" stop-color="#171a1e"/><stop offset="1" stop-color="#101215"/></radialGradient>
 <radialGradient id="insert-edge"><stop offset=".94" stop-color="#111315" stop-opacity="0"/><stop offset=".98" stop-color="#090a0b" stop-opacity=".45"/><stop offset="1" stop-color="#040505" stop-opacity=".85"/></radialGradient>
 <linearGradient id="seat" x1="0" y1="0" x2=".35" y2="1"><stop stop-color="#101215"/><stop offset=".45" stop-color="#15171a"/><stop offset=".8" stop-color="#383b3e"/><stop offset="1" stop-color="#414449"/></linearGradient>
 <radialGradient id="pin" cx=".3" cy=".24" r=".82"><stop stop-color="#fffefa"/><stop offset=".24" stop-color="#e6e8e7"/><stop offset=".52" stop-color="#aeb4b7"/><stop offset=".72" stop-color="#777e82"/><stop offset=".86" stop-color="#d3d7d6"/><stop offset="1" stop-color="#525a5e"/></radialGradient>
 <linearGradient id="pin-bevel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#eef0ef"/><stop offset=".25" stop-color="#969da0"/><stop offset=".6" stop-color="#52595b"/><stop offset="1" stop-color="#d0d4d2"/></linearGradient>
 <clipPath id="insert-clip"><circle cx="512" cy="512" r="244.48"/></clipPath>
 <style>.pin-state{fill:none;stroke:var(--pin-highlight,#61d5ee);stroke-width:3;opacity:0}.pin[data-active="true"] .pin-state{opacity:1}.pin{outline:none}.pin:focus .pin-state{opacity:1}</style>
</defs>''')
 add('<g id="shell" aria-label="Matte nickel-plated shell">')
 # Rear knurled grip seen just outside the forward collar in an axial view.
 circle(7.35,'#626766')
 metal(6.88,7.32,164,52)
 add('<g id="knurled-grip" fill="none">')
 for i in range(100):
  a=2*math.pi*i/100
  add(f'<path d="{annulus(7.18,7.345,a,a+.017)}" fill="#edf0ec" opacity=".60"/>')
  add(f'<path d="{annulus(6.96,7.31,a+.018,a+.039)}" fill="#333938" opacity=".49"/>')
  x,y=point(7.325,a+.045);x2,y2=point(6.99,a+.025)
  add(f'<path d="M{x:.3f} {y:.3f}L{x2:.3f} {y2:.3f}" stroke="#f6f7f1" stroke-width=".6" opacity=".45"/>')
 add('</g>')
 circle(6.94,'#343b3c', '#dadcda', .018)
 metal(6.30,6.90,192,60)
 # Fine lathe / satin rings; these are decorative, not dimension claims.
 for i in range(45):
  r=6.32+i*.0124
  circle(r,'none','#fff' if i%3 else '#26302f', .004, f'opacity="{.07 if i%3 else .10}"')
 circle(6.88,'none','#f5f6f1',.023)
 circle(6.32,'none','#505656',.033)
 circle(6.27,'url(#wall)')
 circle(6.23,'none','#0c1011',.022)
 circle(5.92,'none','#bfc3b9',.018,'opacity=".22"')
 circle(5.57,'#24282a')
 metal(5.15,5.50,142,45)
 circle(5.48,'none','#e0e1da',.018)
 circle(5.16,'none','#343c3c',.022)
 circle(5.13,'url(#wall)')
 # Five asymmetric polarization keys: main key and four secondary keys.
 # Polar positions follow the manufacturer's axial projection.
 keys=[(-90,2.6),(-140,1.6),(140,1.6),(75,1.6),(40,1.6)]
 add('<g id="polarization-keys">')
 for a,w in keys:
  half=math.asin(w/(2*4.75));aa=math.radians(a)
  add(f'<path d="{keypath(4.66,5.15,aa,w)}" fill="url(#edge)" stroke="#454b4b" stroke-width="1.1"/>')
  add(f'<path d="{keypath(4.75,5.12,aa,w-.045)}" fill="url(#edge)"/>')
  add(f'<path d="{keypath(5.11,5.145,aa,w-.07)}" fill="#e8e9e3" opacity=".8"/>')
 add('</g>')
 circle(4.75,'url(#edge)')
 metal(4.54,4.75,179,44)
 circle(4.745,'none','#f3f4ed',.016)
 # Inner metal mating lip: 4.55 outside and 3.85 bore radius.
 metal(3.85,4.55,185,55)
 for i in range(42):
  circle(3.88+i*.0154,'none','#fff' if i%2 else '#292f30',.0032,'opacity=".10"')
 circle(4.53,'none','#f1f1eb',.018)
 circle(3.86,'none','#747a79',.03)
 add('</g>')
 add('<g id="insulator" aria-label="Black polyamide insulator">')
 circle(3.84,'#090c0e')
 circle(3.80,'url(#polyamide)')
 # Deterministic vector microtexture; subtly molded, not stone or noise raster.
 random.seed(17)
 add('<g clip-path="url(#insert-clip)" pointer-events="none">')
 for i in range(1600):
  x=random.uniform(-3.8,3.8);y=random.uniform(-3.8,3.8)
  if x*x+y*y>3.8**2:continue
  add(f'<circle cx="{512+x*S:.2f}" cy="{512+y*S:.2f}" r="{random.uniform(.15,.55):.2f}" fill="{ "#cbd0d1" if i%2 else "#000"}" opacity="{random.uniform(.025,.11):.3f}"/>')
 add('</g>')
 circle(3.80,'url(#insert-edge)')
 circle(3.80,'none','#686c6c',.009,'opacity=".45"')
 add('</g><g id="contacts" aria-label="Twelve silver-plated male pins">')
 for n,(x,y) in pins.items():
  px,py=512+x*S,512+y*S
  add(f'<g id="pin-{n}" class="pin" data-pin="{n}" data-x-mm="{x}" data-y-mm="{y}" transform="translate({px:.2f} {py:.2f})"><title>Pin {n}</title>')
  add('<circle r="34.6" fill="#0c0e10"/><circle r="33.2" fill="url(#seat)"/><circle r="25.0" fill="#0a0c0e"/><circle cy="2.8" r="21.3" fill="#000" opacity=".6"/><circle r="19.2" fill="url(#pin-bevel)"/><circle r="16.1" fill="url(#pin)"/><path d="M-12 -7 A14 14 0 0 1 4 -13" fill="none" stroke="#fff" stroke-width="1.05" opacity=".68"/><circle cx="-4" cy="-5" r="6" fill="#fff" opacity=".10"/><circle class="pin-state" r="38"/>')
  add('</g>')
 add('</g>')
 if labels:
  add('<g id="pin-labels" aria-label="Mating-side pin numbers" font-family="Arial,Helvetica,sans-serif" font-size="19" font-weight="600" text-anchor="middle" fill="#dbe2e4">')
  for n,(x,y) in pins.items():
   # Numbers sit just above each seat, keeping the metal pin face unobscured.
   add(f'<text x="{512+x*S:.2f}" y="{512+y*S-42:.2f}">{n}</text>')
  add('</g>')
 add('</svg>')
 return '\n'.join(parts)
for label,name in [(False,'hr10a-10p-12p'),(True,'hr10a-10p-12p-numbered')]:
 (OUT/f'{name}.svg').write_text(build(label))
(OUT/'geometry.json').write_text(json.dumps({'part':'HR10A-10P-12P(73)','view':'male plug mating face, main key up','svg_units_per_mm':64,'svg_center':[512,512],'shell_diameter_mm':14.7,'pin_centres_mm':{str(k):v for k,v in pins.items()},'pin_centres_source':'Hirose HR10 catalog p.193, horizontal reflection; numbering verified with EDC-010386-73-73 rev.4','limits':'Pin tip/seat diameters, microtexture, knurl count and optical finish are illustrative. STEP is simplified and omits contacts. Not a manufacturing model.'},indent=2))
print('Created two SVGs and geometry.json')
