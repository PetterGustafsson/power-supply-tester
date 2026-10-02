from pathlib import Path
import xml.etree.ElementTree as ET
p=Path('output');ns='http://www.w3.org/2000/svg'; ET.register_namespace('',ns)
root=ET.parse(p/'rendered-pins-correct.svg').getroot();children=list(root); start=next(i for i,e in enumerate(children) if e.get('id')=='machine-result'); tail=children[start:]
for e in tail:root.remove(e)
groups={}
for name,els in [('verdict',[tail[0]]),('power',[tail[1],*tail[3:6]]),('ground',[tail[2],*tail[6:9]])]:
 g=ET.SubElement(root,f'{{{ns}}}g',{'id':'reveal-'+name})
 for el in els:g.append(el)
 groups[name]=g
# Standalone animated vector, with a reduced-motion fallback.
style=ET.SubElement(root,f'{{{ns}}}style')
style.text='''
#reveal-power {animation: power-reveal 6s ease-in-out infinite;}
#reveal-ground {animation: ground-reveal 6s ease-in-out infinite;}
#reveal-verdict {animation: verdict-reveal 6s ease-in-out infinite;}
@keyframes power-reveal {0%,12%{opacity:0} 23%,90%{opacity:1} 100%{opacity:0}}
@keyframes ground-reveal {0%,28%{opacity:0} 39%,90%{opacity:1} 100%{opacity:0}}
@keyframes verdict-reveal {0%,44%{opacity:0} 55%,90%{opacity:1} 100%{opacity:0}}
@media (prefers-reduced-motion:reduce){#reveal-power,#reveal-ground,#reveal-verdict{animation:none;opacity:1}}
'''
ET.ElementTree(root).write(p/'rendered-power-animation.svg',encoding='unicode')
root.remove(style)
frames=p/'animation-frames';frames.mkdir(exist_ok=True)
def opacity(t,a,b):
 if t<a:return 0
 if t<b:
  f=(t-a)/(b-a);return f*f*(3-2*f)
 if t<5.4:return 1
 return max(0,(6-t)/.6)
for i in range(40):
 t=i*.15
 for name,(a,b) in {'power':(.72,1.38),'ground':(1.68,2.34),'verdict':(2.64,3.30)}.items():groups[name].set('opacity',str(opacity(t,a,b)))
 ET.ElementTree(root).write(frames/f'{i:02}.svg',encoding='unicode')
