from pathlib import Path
import json
p=Path('output'); original=(p/'hr10a-10p-12p.svg').read_text(); coords=json.loads((p/'geometry.json').read_text())['pin_centres_mm']
# Add UI treatment to the untouched original rendered connector geometry.
def art(name,power,ground,status):
 c='#53e5a0' if status=='CORRECT' else '#ff6268'
 svg=original.replace('width="1024" height="1024"','width="1024" height="1024"')
 svg=svg.replace('<defs>','''<defs><filter id="status-glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter><filter id="pin-glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="8"/></filter>''',1)
 shades=['#b1ffda','#16aa65','#65efac','#098047','#85f2bd'] if status=='CORRECT' else ['#ffb7b9','#bd2635','#ff7077','#8d1826','#ff9ca4']
 stops=''.join(f'<stop offset="{offset}" stop-color="{color}"/>' for offset,color in zip([0,.27,.49,.74,1],shades))
 svg=svg.replace('</defs>',f'<linearGradient id="status-metal" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient></defs>',1)
 # Full existing collar: inner radius 6.30 mm, outer radius 6.90 mm.
 ring=f'<g id="machine-result"><circle cx="512" cy="512" r="422.4" fill="none" stroke="{c}" stroke-width="40" opacity=".28" filter="url(#status-glow)"/><circle cx="512" cy="512" r="422.4" fill="none" stroke="url(#status-metal)" stroke-width="38.4"/>'
 for i in range(30):
  ring+=f'<circle cx="512" cy="512" r="{404+i*1.22}" fill="none" stroke="{"#fff" if i%3 else "#052b19"}" stroke-width=".3" opacity=".12"/>'
 ring+=f'<circle cx="512" cy="512" r="440.9" fill="none" stroke="{shades[0]}" stroke-width="1.3" opacity=".85"/><circle cx="512" cy="512" r="403.8" fill="none" stroke="{shades[3]}" stroke-width="1.4"/></g>'
 overlay=[ring]
 for n,color in [(power,'#ffd77a'),(ground,'#8ce7f4')]:
  x,y=coords[str(n)];x=512+64*x;y=512+64*y
  overlay.append(f'<g id="detected-pin-{n}"><circle cx="{x}" cy="{y}" r="29" fill="{color}" opacity=".8" filter="url(#pin-glow)"/><circle cx="{x}" cy="{y}" r="31" fill="none" stroke="{color}" stroke-width="3.5"/><circle cx="{x}" cy="{y}" r="18" fill="{color}" opacity=".5"/><circle cx="{x-4}" cy="{y-5}" r="7" fill="#fff" opacity=".33"/></g>')
 # Callouts lie in the metal annulus; fine leaders terminate at the pin halo.
 labels=[(power,'#ffd77a', '+24V', (340,260) if power==1 else (680,260)),(ground,'#8ce7f4','GND',(670,780) if ground==5 else (274,656))]
 for n,color,label,(tx,ty) in labels:
  x,y=coords[str(n)];px=512+x*64;py=512+y*64
  dx=tx-px;dy=ty-py;l=(dx*dx+dy*dy)**.5
  sx=px+dx/l*35;sy=py+dy/l*35
  # End leaders outside the glyphs now that the opaque plates are removed.
  edge=min(142/max(abs(dx),.001),48/max(abs(dy),.001))
  ex=tx-dx*edge;ey=ty-dy*edge
  overlay.append(f'<path d="M{sx} {sy}L{ex} {ey}" fill="none" stroke="#080d12" stroke-width="7" opacity=".6"/><path d="M{sx} {sy}L{ex} {ey}" fill="none" stroke="{color}" stroke-width="2.5"/><text x="{tx}" y="{ty+30}" fill="{color}" font-family="Arial,sans-serif" font-size="88" font-weight="600" text-anchor="middle" stroke="#111920" stroke-width="5" stroke-linejoin="round" paint-order="stroke fill">{label}</text>')
 svg=svg.replace('</svg>','\n'.join(overlay)+'</svg>')
 (p/f'{name}.svg').write_text(svg)
 return svg
left=art('rendered-pins-correct',1,5,'CORRECT');right=art('rendered-pins-wrong',9,3,'WRONG PINS')
# Prefix every id/reference in each nested SVG to avoid collisions.
import re
def nest(s,prefix,x):
 ids=re.findall(r'\bid="([^"]+)"',s)
 for i in ids:
  s=s.replace(f'id="{i}"',f'id="{prefix}{i}"').replace(f'url(#{i})',f'url(#{prefix}{i})')
 s=s.replace('width="1024" height="1024"',f'x="{x}" y="100" width="430" height="430"')
 return s
(p/'rendered-power-concept.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="610" viewBox="0 0 1000 610"><rect width="1000" height="610" fill="#12191f"/><text x="48" y="51" fill="#eef1f3" font-size="25" font-family="Arial,sans-serif">Power, located.</text><text x="48" y="78" fill="#95a4ae" font-size="14" font-family="Arial,sans-serif">Original rendered connector · illuminated contacts · status in the metal collar</text>{nest(left,'a-',40)}{nest(right,'b-',530)}<text x="255" y="558" fill="#abb8c0" font-size="15" text-anchor="middle" font-family="Arial,sans-serif">Accepted by the machine</text><text x="745" y="558" fill="#abb8c0" font-size="15" text-anchor="middle" font-family="Arial,sans-serif">Unexpected power-pin positions</text><text x="500" y="591" fill="#74858f" font-size="12" text-anchor="middle" font-family="Arial,sans-serif">Example positions only. The machine supplies the detected pins and verdict.</text></svg>''')
