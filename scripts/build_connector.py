from pathlib import Path
import math, json, random
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
# Mating-face coordinates in mm. Catalog p.193 mirrored horizontally;
# numbering checked against Hirose EDC-010386-73-73 revision 4.
pins={1:(-.95,-2.58),2:(-2.38,-1.1),3:(-2.71,.48),4:(-1.77,2.1),5:(0,2.75),6:(1.77,2.1),7:(2.71,.48),8:(2.38,-1.1),9:(.95,-2.58),10:(0,-1.38),11:(-.95,.55),12:(.95,.55)}
S=64; C=512
parts=[]
surface_finish='chrome'
def add(s): parts.append(s)
def circle(r,fill,stroke=None,sw=.01,extra=''):
 add(f'<circle cx="512" cy="512" r="{r*S:.5f}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw*S}"' if stroke else '')+f' {extra}/>')
def point(r,a):return (C+S*r*math.cos(a),C+S*r*math.sin(a))
def annulus(ri,ro,a,b):
 p=[point(ro,a),point(ro,b),point(ri,b),point(ri,a)]
 return f'M {p[0][0]:.4f} {p[0][1]:.4f} A {ro*S} {ro*S} 0 0 1 {p[1][0]:.4f} {p[1][1]:.4f} L {p[2][0]:.4f} {p[2][1]:.4f} A {ri*S} {ri*S} 0 0 0 {p[3][0]:.4f} {p[3][1]:.4f} Z'
def metal(ri,ro,base=174,contrast=50):
 # Machined metal with sharply focused reflections and deep shadow tones.
 def lobe(angle,centre,width):
  delta=math.atan2(math.sin(angle-centre),math.cos(angle-centre))
  return math.exp(-.5*(delta/width)**2)
 def gold(value):
  stops=((22,(30,18,5)),(80,(79,45,12)),(125,(139,83,19)),
         (170,(201,135,38)),(210,(243,190,79)),(248,(255,246,194)))
  for (lo,a),(hi,b) in zip(stops,stops[1:]):
   if value<=hi:
    t=max(0,min(1,(value-lo)/(hi-lo)))
    return '#'+''.join(f'{round(x+(y-x)*t):02x}' for x,y in zip(a,b))
  return '#fff6c2'
 add('<g stroke-width="0.7" stroke-linejoin="round">')
 for i in range(480):
  a=2*math.pi*i/480;b=2*math.pi*(i+1.02)/480
  v=base+contrast*(.58*math.cos(2*(a+.65))+.18*math.cos(5*a+.6)+.07*math.sin(11*a))
  v+=58*lobe(a,-.95,.105)+38*lobe(a,2.25,.16)-22*lobe(a,.65,.24)
  v=max(22,min(248,round(v)))
  col=gold(v) if surface_finish=='gold' else f'#{v:02x}{min(255,v+3):02x}{min(255,v+5):02x}'
  add(f'<path d="{annulus(ri,ro,a,b)}" fill="{col}" stroke="{col}"/>')
 add('</g>')
def keypath(ri,ro,a,w):
 # Parallel sides, with both curved ends concentric to the connector axis.
 hi=math.asin(w/(2*ri)); ho=math.asin(w/(2*ro))
 p=[point(ri,a-hi),point(ro,a-ho),point(ro,a+ho),point(ri,a+hi)]
 return f'M{p[0][0]:.4f} {p[0][1]:.4f} L{p[1][0]:.4f} {p[1][1]:.4f} A{ro*S} {ro*S} 0 0 1 {p[2][0]:.4f} {p[2][1]:.4f} L{p[3][0]:.4f} {p[3][1]:.4f} A{ri*S} {ri*S} 0 0 0 {p[0][0]:.4f} {p[0][1]:.4f} Z'
def build(labels=False,finish='chrome'):
 global surface_finish
 surface_finish=finish
 parts.clear()
 add('''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-labelledby="connector-title connector-desc">
<title id="connector-title">Hirose HR10A-10P-12P(73), male plug, mating face</title>
<desc id="connector-desc">Orthographic front view, main key at 12 o'clock. Twelve brass-toned contacts in black polyamide, with a polished gold-toned shell. Pin 1 is upper left; pin 9 upper right. Independently authored UI illustration referencing Hirose mechanical drawing EDC-010386-73-73 and HR10 catalog. Surface finish, knurl microgeometry and pin tip profiles are illustrative. Not a manufacturing drawing.</desc>
<metadata>Units: 64 SVG units per mm. Maximum shell diameter: 14.7 mm. Transparent background. Projection: mating side. Contact IDs: pin-1 through pin-12. Sources and accuracy limits: README.md and geometry.json.</metadata>
<defs>
 <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff4c2"/><stop offset=".22" stop-color="#9c601c"/><stop offset=".48" stop-color="#ffe8a0"/><stop offset=".72" stop-color="#70400e"/><stop offset="1" stop-color="#d79d3c"/></linearGradient>
 <linearGradient id="wall" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#251807"/><stop offset=".3" stop-color="#664014"/><stop offset=".58" stop-color="#b77a2c"/><stop offset=".8" stop-color="#59340e"/><stop offset="1" stop-color="#e4b05b"/></linearGradient>
 <radialGradient id="polyamide" cx=".32" cy=".24" r=".88"><stop stop-color="#303337"/><stop offset=".44" stop-color="#212428"/><stop offset=".82" stop-color="#171a1e"/><stop offset="1" stop-color="#101215"/></radialGradient>
 <radialGradient id="insert-edge"><stop offset=".94" stop-color="#111315" stop-opacity="0"/><stop offset=".98" stop-color="#090a0b" stop-opacity=".45"/><stop offset="1" stop-color="#040505" stop-opacity=".85"/></radialGradient>
 <linearGradient id="seat" x1="0" y1="0" x2=".35" y2="1"><stop stop-color="#100e0c"/><stop offset=".45" stop-color="#1a1713"/><stop offset=".8" stop-color="#342a1d"/><stop offset="1" stop-color="#4b3720"/></linearGradient>
 <radialGradient id="pin" cx=".28" cy=".22" r=".86"><stop stop-color="#fffbe4"/><stop offset=".17" stop-color="#fff0b1"/><stop offset=".36" stop-color="#efc465"/><stop offset=".61" stop-color="#b77828"/><stop offset=".78" stop-color="#754319"/><stop offset=".9" stop-color="#d99c3b"/><stop offset="1" stop-color="#653812"/></radialGradient>
 <linearGradient id="pin-bevel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff0a9"/><stop offset=".24" stop-color="#bd7d28"/><stop offset=".57" stop-color="#4b2a10"/><stop offset=".84" stop-color="#e8ad47"/><stop offset="1" stop-color="#764315"/></linearGradient>
 <clipPath id="insert-clip"><circle cx="512" cy="512" r="244.48"/></clipPath>
 <style>.pin-state{fill:none;stroke:var(--pin-highlight,#61d5ee);stroke-width:3;opacity:0}.pin[data-active="true"] .pin-state{opacity:1}.pin{outline:none}.pin:focus .pin-state{opacity:1}</style>
</defs>''')
 add('<g id="shell" aria-label="Polished gold-toned shell">')
 # Rear knurled grip seen just outside the forward collar in an axial view.
 circle(7.35,'#6a4317')
 metal(6.88,7.32,164,52)
 add('<g id="knurled-grip" fill="none">')
 for i in range(100):
  a=2*math.pi*i/100
  add(f'<path d="{annulus(7.18,7.345,a,a+.017)}" fill="#fff1b9" opacity=".54"/>')
  add(f'<path d="{annulus(6.96,7.31,a+.018,a+.039)}" fill="#51300b" opacity=".42"/>')
  x,y=point(7.325,a+.045);x2,y2=point(6.99,a+.025)
  add(f'<path d="M{x:.3f} {y:.3f}L{x2:.3f} {y2:.3f}" stroke="#fff1b9" stroke-width=".6" opacity=".38"/>')
 add('</g>')
 circle(6.94,'#4c3213', '#f5d986', .018)
 metal(6.30,6.90,192,60)
 # Fine lathe / satin rings; these are decorative, not dimension claims.
 for i in range(45):
  r=6.32+i*.0124
  circle(r,'none','#fff4ce' if i%3 else '#45280b', .004, f'opacity="{.12 if i%3 else .16}"')
 circle(6.88,'none','#fff5d3',.023)
 circle(6.32,'none','#6a4317',.033)
 circle(6.27,'url(#wall)')
 circle(6.23,'none','#241606',.022)
 circle(5.92,'none','#ffe4a0',.018,'opacity=".29"')
 circle(5.57,'#33200b')
 metal(5.15,5.50,142,45)
 circle(5.48,'none','#ffe5a0',.018)
 circle(5.16,'none','#593710',.022)
 circle(5.13,'url(#wall)')
 # Five asymmetric polarization keys: main key and four secondary keys.
 # Polar positions follow the manufacturer's axial projection.
 keys=[(-90,2.6),(-140,1.6),(140,1.6),(75,1.6),(40,1.6)]
 add('<g id="polarization-keys">')
 for a,w in keys:
  half=math.asin(w/(2*4.75));aa=math.radians(a)
  add(f'<path d="{keypath(4.66,5.15,aa,w)}" fill="url(#edge)" stroke="#704511" stroke-width="1.1"/>')
  add(f'<path d="{keypath(4.75,5.12,aa,w-.045)}" fill="url(#edge)"/>')
  add(f'<path d="{keypath(5.11,5.145,aa,w-.07)}" fill="#fff0b6" opacity=".8"/>')
 add('</g>')
 circle(4.75,'url(#edge)')
 metal(4.54,4.75,179,44)
 circle(4.745,'none','#fff1c1',.016)
 # Inner metal mating lip: 4.55 outside and 3.85 bore radius.
 metal(3.85,4.55,185,55)
 for i in range(42):
  circle(3.88+i*.0154,'none','#fff3cc' if i%2 else '#55320e',.0032,'opacity=".14"')
 circle(4.53,'none','#fff3c7',.018)
 circle(3.86,'none','#76501d',.03)
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
 add('</g><g id="contacts" aria-label="Twelve brass-toned male pins">')
 for n,(x,y) in pins.items():
  px,py=512+x*S,512+y*S
  add(f'<g id="pin-{n}" class="pin" data-pin="{n}" data-x-mm="{x}" data-y-mm="{y}" transform="translate({px:.2f} {py:.2f})"><title>Pin {n}</title>')
  add('<circle r="34.6" fill="#0b0d0e"/><circle r="33.2" fill="url(#seat)"/><circle r="25.0" fill="#0b0a08"/><circle cy="2.8" r="22.4" fill="#000" opacity=".65"/><circle r="22.0" fill="url(#pin-bevel)"/><circle r="18.4" fill="url(#pin)"/><path d="M-14 -8 A16 16 0 0 1 5 -15" fill="none" stroke="#fff9d3" stroke-width="1.6" opacity=".9"/><path d="M3 17 A17 17 0 0 0 15 7" fill="none" stroke="#ffd37a" stroke-width="1.7" opacity=".72"/><circle cx="-6" cy="-7" r="4.8" fill="#fffef1" opacity=".4"/><circle class="pin-state" r="38"/>')
  add('</g>')
 add('</g>')
 if labels:
  add('<g id="pin-labels" aria-label="Mating-side pin numbers" font-family="Arial,Helvetica,sans-serif" font-size="19" font-weight="600" text-anchor="middle" fill="#dbe2e4">')
  for n,(x,y) in pins.items():
   # Numbers sit just above each seat, keeping the metal pin face unobscured.
   add(f'<text x="{512+x*S:.2f}" y="{512+y*S-42:.2f}">{n}</text>')
  add('</g>')
 add('</svg>')
 svg='\n'.join(parts)
 if finish=='chrome':
  # These tones belong to the shell and its keyways. Contact gradients stay brass.
  shell_colours={
   '#fff4c2':'#f8faf8','#9c601c':'#8c9495','#ffe8a0':'#edf2ef',
   '#70400e':'#5e6869','#d79d3c':'#bac2c2','#251807':'#171b1d',
   '#664014':'#42494a','#b77a2c':'#878f8f','#59340e':'#444c4c',
   '#e4b05b':'#b1bbba','#6a4317':'#62696a','#fff1b9':'#f3f8f7',
   '#51300b':'#333d3e','#4c3213':'#343d3e','#f5d986':'#d7e0df',
   '#fff4ce':'#ffffff','#45280b':'#283436','#fff5d3':'#f5f7f5',
   '#241606':'#0c1112','#ffe4a0':'#c2cbca','#33200b':'#23292b',
   '#ffe5a0':'#e0e7e3','#593710':'#343d3f','#704511':'#465052',
   '#fff0b6':'#e9efec','#fff1c1':'#f5f8f5','#fff3cc':'#ffffff',
   '#55320e':'#2a3335','#fff3c7':'#f1f5f2','#76501d':'#747e7e',
  }
  for warm,cool in shell_colours.items(): svg=svg.replace(warm,cool)
  svg=svg.replace('polished gold-toned shell','polished chrome shell')
  svg=svg.replace('Polished gold-toned shell','Polished chrome shell')
 return svg
for label,name,finish in [(False,'hr10a-10p-12p','chrome'),(True,'hr10a-10p-12p-numbered','chrome'),(False,'hr10a-10p-12p-gold','gold')]:
 (OUT/f'{name}.svg').write_text(build(label,finish))
(OUT/'geometry.json').write_text(json.dumps({'part':'HR10A-10P-12P(73)','view':'male plug mating face, main key up','svg_units_per_mm':64,'svg_center':[512,512],'shell_diameter_mm':14.7,'pin_centres_mm':{str(k):v for k,v in pins.items()},'pin_centres_source':'Hirose HR10 catalog p.193, horizontal reflection; numbering verified with EDC-010386-73-73 rev.4','limits':'Pin tip/seat diameters, microtexture, knurl count and optical finish are illustrative. STEP is simplified and omits contacts. Not a manufacturing model.'},indent=2))
print('Created chrome, numbered chrome, gold reflection SVGs and geometry.json')
