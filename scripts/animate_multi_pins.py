"""Illustrative voltage/polarity animation; particles do not measure current."""
from pathlib import Path
import json, math, random, subprocess
import xml.etree.ElementTree as E
from PIL import Image

P = Path(__file__).resolve().parents[1]
D = P / 'output/multi-pin-frames'
D.mkdir(exist_ok=True)
NS = 'http://www.w3.org/2000/svg'
E.register_namespace('', NS)
base = E.parse(P / 'output/hr10a-10p-12p.svg').getroot()
coords = json.loads((P / 'output/geometry.json').read_text())['pin_centres_mm']
points = {int(k): (512 + 64*x, 512 + 64*y) for k,(x,y) in coords.items()}
positive, negative = [1,2,3], [5,6]
hub = (527, 515)
random.seed(12)
particles = [(random.random(), random.uniform(-1,1), random.uniform(2,4)) for _ in range(55)]

def el(parent, tag, **attrs):
    return E.SubElement(parent, '{'+NS+'}'+tag, {k.replace('_','-'):str(v) for k,v in attrs.items()})

def curve(a,b,u,bend):
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    nx,ny=-dy/length,dx/length
    bow=math.sin(math.pi*u)*bend
    return a[0]+dx*u+nx*bow,a[1]+dy*u+ny*bow,nx,ny

for frame in range(60):
    root=E.fromstring(E.tostring(base))
    defs=root.find('{'+NS+'}defs')
    filt=el(defs,'filter',id='flow-glow',x='-100%',y='-100%',width='300%',height='300%')
    el(filt,'feGaussianBlur',stdDeviation=4)
    t=frame/60
    g=el(root,'g',id='multi-flow')
    # A neutral shimmering ring: no pass/fail verdict is assumed.
    el(g,'circle',cx=512,cy=512,r=422,fill='none',stroke='#b5d4db',stroke_width=32,opacity=.65)
    el(g,'circle',cx=512,cy=512,r=422,fill='none',stroke='#f1ffff',stroke_width=15,
       stroke_dasharray='110 2542',transform=f'rotate({360*t} 512 512)',opacity=.9,
       filter='url(#flow-glow)')
    branches=[(points[n],hub,0,.5,55) for n in negative]+[(hub,points[n],.5,1,37) for n in positive]
    for j,(a,b,start,end,count) in enumerate(branches):
        bend=(j-2)*8
        for k,(phase,spread,size) in enumerate(particles[:count]):
            u=(phase+2*t)%1
            x,y,nx,ny=curve(a,b,u,bend)
            off=spread*14*math.sin(math.pi*u)
            x+=nx*off;y+=ny*off
            v=start+(end-start)*u
            cold,white,hot=(99,220,255),(224,249,243),(255,191,82)
            c0,c1,w=(cold,white,v*2) if v<.5 else (white,hot,(v-.5)*2)
            color='#'+''.join(f'{round(p+(q-p)*w):02x}' for p,q in zip(c0,c1))
            opacity=.75*min(1,u*12,(1-u)*12)
            if k%4==0:
                el(g,'circle',cx=x,cy=y,r=size*2,fill=color,opacity=opacity*.65,filter='url(#flow-glow)')
            el(g,'circle',cx=x,cy=y,r=size,fill=color,opacity=opacity)
            xx,yy,_,_=curve(a,b,max(0,u-.035),bend)
            el(g,'path',d=f'M{x} {y} L{xx+nx*off} {yy+ny*off}',stroke=color,stroke_width=size*.8,opacity=opacity*.5)
    for group,color,sign in [(positive,'#ffd77a','+'),(negative,'#8ce7f4','−')]:
        for n in group:
            x,y=points[n]
            el(g,'circle',cx=x,cy=y,r=27,fill=color,opacity=.35,filter='url(#flow-glow)')
            el(g,'circle',cx=x,cy=y,r=28,fill='none',stroke=color,stroke_width=5)
            label=el(g,'text',x=x,y=y-38,fill=color,font_family='Arial',font_size=29,
                     font_weight=700,text_anchor='middle',stroke='#111920',stroke_width=4,paint_order='stroke fill')
            label.text=f'{n}{sign}'
    for text,x,y,size,color in [('+24V',340,266,84,'#ffd77a'),('RETURN',620,822,66,'#8ce7f4')]:
        node=el(g,'text',x=x,y=y,fill=color,font_family='Arial',font_size=size,font_weight=600,
                text_anchor='middle',stroke='#111920',stroke_width=5,paint_order='stroke fill')
        node.text=text
    E.ElementTree(root).write(D/f'{frame:02}.svg',encoding='unicode')

renderer = """
const sharp=require('sharp');
(async()=>{for(let i=0;i<60;i++){let n=String(i).padStart(2,'0');await sharp(process.argv[1]+'/'+n+'.svg').resize(480,480).flatten({background:'#12191f'}).png().toFile(process.argv[1]+'/'+n+'.png');}})().catch(e=>{console.error(e);process.exit(1)});
"""
subprocess.run(['node','-e',renderer,str(D)],check=True)
frames=[Image.open(D/f'{i:02}.png').convert('RGB') for i in range(60)]
sheet=Image.new('RGB',(480,480*3))
for j,k in enumerate([0,20,40]):sheet.paste(frames[k],(0,j*480))
palette=sheet.quantize(colors=256)
for size,suffix in [(480,''),(240,'-240')]:
    output=P/f'output/multi-pin-electron-flow{suffix}.gif'
    images=[im.resize((size,size),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    images[0].save(output,save_all=True,append_images=images[1:],duration=50,loop=0,optimize=False,disposal=2)
    with Image.open(output) as check:
        assert check.n_frames==60 and check.size==(size,size)
    print(output)
