from pathlib import Path
import json
out=Path('output'); pins=json.loads((out/'geometry.json').read_text())['pin_centres_mm']
AMBER='#ffca62'; CYAN='#65d7ef'
def screen(state,power,ground):
 c={'CORRECT':'#45d391','WRONG PINS':'#ff6b70'}[state]
 s=['<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">', '<defs><radialGradient id="face"><stop stop-color="#242d35"/><stop offset="1" stop-color="#141b22"/></radialGradient><linearGradient id="metal" x2="1" y2="1"><stop stop-color="#b0b9be"/><stop offset=".4" stop-color="#4d5962"/><stop offset=".7" stop-color="#8b959b"/><stop offset="1" stop-color="#37424a"/></linearGradient></defs>', '<circle cx="120" cy="120" r="120" fill="#0c1218"/>',f'<circle cx="120" cy="120" r="114" fill="none" stroke="{c}" stroke-width="5"/>', f'<text x="120" y="31" fill="{c}" font-family="Arial,sans-serif" font-size="15" font-weight="700" text-anchor="middle">{state}</text>', '<circle cx="120" cy="121" r="78" fill="url(#metal)"/>','<circle cx="120" cy="121" r="73" fill="url(#face)" stroke="#080d12" stroke-width="2"/>','<path d="M113 45h14v7h-14z" fill="#bec7cb"/>']
 for n,(x,y) in pins.items():
  px=120+x*20;py=121+y*20
  active=n in (str(power),str(ground)); color=AMBER if n==str(power) else CYAN if n==str(ground) else '#35424d'
  r=10 if active else 8
  if active:s.append(f'<circle cx="{px}" cy="{py}" r="13" fill="none" stroke="{color}" stroke-width="1" opacity=".65"/>')
  s.append(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{color}" stroke="{color if active else "#62717d"}" stroke-width="1"/>')
  s.append(f'<text x="{px}" y="{py+3.7}" fill="{"#111921" if active else "#c1cbd2"}" font-size="11" font-family="Arial,sans-serif" font-weight="700" text-anchor="middle">{n}</text>')
 s.extend([f'<text x="120" y="211" fill="{AMBER}" font-family="Arial,sans-serif" font-size="12" font-weight="700" text-anchor="middle">+24V · PIN {power}</text>',f'<text x="120" y="225" fill="{CYAN}" font-family="Arial,sans-serif" font-size="12" font-weight="700" text-anchor="middle">GND · PIN {ground}</text>','</svg>'])
 return ''.join(s)
a=screen('CORRECT',1,5);b=screen('WRONG PINS',9,3)
(out/'power-pins-correct.svg').write_text(a);(out/'power-pins-wrong.svg').write_text(b)
# Nested vector screens preserve their actual 240px design coordinate system.
a=a.replace('width="240" height="240"','x="96" y="127" width="312" height="312"').replace('id="face"','id="faceA"').replace('url(#face)','url(#faceA)').replace('id="metal"','id="metalA"').replace('url(#metal)','url(#metalA)')
b=b.replace('width="240" height="240"','x="492" y="127" width="312" height="312"').replace('id="face"','id="faceB"').replace('url(#face)','url(#faceB)').replace('id="metal"','id="metalB"').replace('url(#metal)','url(#metalB)')
(out/'power-pins-concept.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="535" viewBox="0 0 900 535"><rect width="900" height="535" fill="#111820"/><g font-family="Arial,sans-serif"><text x="42" y="47" fill="#f1f5f8" font-size="26" font-weight="700">Located power pins</text><text x="42" y="77" fill="#a1afbb" font-size="16">Pin color shows polarity. The outer ring shows the machine’s verdict.</text>{a}{b}<text x="252" y="471" fill="#d9e2e8" font-size="16" text-anchor="middle">Machine accepts the detected pair</text><text x="648" y="471" fill="#d9e2e8" font-size="16" text-anchor="middle">Machine rejects the detected pair</text><text x="450" y="511" fill="#8495a3" font-size="13" text-anchor="middle">Example positions only — the machine supplies the actual pin numbers and result.</text></g></svg>''')
