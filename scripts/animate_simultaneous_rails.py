"""Simulated common-return, three-rail display. Voltage controls visual intensity,
not particle speed. Original Hirose mating-face geometry stays unchanged."""
from pathlib import Path
import json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'
SIZE=480; S=SIZE/1024; FPS=20; COUNT=120
raw=Image.open(OUT/'hr10a-10p-12p.png').convert('RGBA').resize((SIZE,SIZE),Image.Resampling.LANCZOS)
base=Image.new('RGBA',raw.size,'#12191f');base.alpha_composite(raw)
geo=json.loads((OUT/'geometry.json').read_text())
pins={int(n):((512+64*x)*S,(512+64*y)*S) for n,(x,y) in geo['pin_centres_mm'].items()}
rails=[{'v':5,'pins':[1,2],'label':(196,460),'color':(255,230,161)},
       {'v':12,'pins':[8,9],'label':(822,460),'color':(255,206,113)},
       {'v':24,'pins':[10,12],'label':(512,250),'color':(255,174,66)}]
returns=[5,6]; cyan=(140,231,244);hub=(512*S,590*S)
fontpath='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
fonts={s:ImageFont.truetype(fontpath,round(s*S)) for s in [27,30,34,42,56]}
def text(d,x,y,t,c,size=30):
    d.text((x*S,y*S),t,font=fonts[size],fill=c,anchor='mm',stroke_width=1,stroke_fill='#111920')
def curve(a,b,u,bend):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    nx,ny=-dy/length,dx/length
    return a[0]+u*dx+nx*math.sin(math.pi*u)*bend,a[1]+u*dy+ny*math.sin(math.pi*u)*bend,nx,ny
mask=Image.new('L',base.size,0);md=ImageDraw.Draw(mask)
md.ellipse(tuple(v*S for v in [272,272,752,752]),fill=255)
for x,y in pins.values():
    r=32*S;md.ellipse((x-r,y-r,x+r,y+r),fill=0)
    md.rectangle((x-24*S,y-72*S,x+24*S,y-38*S),fill=0)
random.seed(25); seeds=[(random.random(),random.uniform(-1,1),random.uniform(1.7,3)) for _ in range(64)]
frames=[]
for frameidx in range(COUNT):
    t=frameidx/COUNT
    im=base.copy();d=ImageDraw.Draw(im)
    ring=tuple(v*S for v in [90,90,934,934])
    d.ellipse(ring,outline=(44,182,121),width=round(28*S))
    d.arc(ring,t*360,t*360+32,fill=(165,255,212),width=round(10*S))
    layer=Image.new('RGBA',im.size);ld=ImageDraw.Draw(layer)
    branches=[(pins[n],hub,0,.42,28,10*S,(221,245,233),1,0) for n in returns]
    for ri,rail in enumerate(rails):
        fraction=rail['v']/24
        for n in rail['pins']:
            branches.append((hub,pins[n],.42,1,round(8+34*fraction),(6+12*fraction)*S,
                             rail['color'],.48+.52*fraction,(ri-1)*9*S))
    for j,(a,b,start,end,count,width,hot,intensity,bend) in enumerate(branches):
        # Constant travel speed in screen pixels/second, independent of voltage.
        # Integer trips over the loop give seamless periodic motion.
        length=math.dist(a,b);trips=max(1,round(6*42/max(1,length)))
        for offset,spread,size in seeds[:count]:
            u=(offset+trips*t+j*.13)%1
            x,y,nx,ny=curve(a,b,u,bend);side=spread*width*math.sin(math.pi*u)
            x+=nx*side;y+=ny*side
            v=start+(end-start)*u;cold=(89,219,255);white=(223,247,235)
            c0,c1,w=(cold,white,v/.42) if v<.42 else (white,hot,(v-.42)/.58)
            col=tuple(round(p+(q-p)*w) for p,q in zip(c0,c1))
            alpha=round(240*intensity*min(1,u*14,(1-u)*14))
            xx,yy,_,_=curve(a,b,max(0,u-.024),bend)
            ld.line((xx+nx*side,yy+ny*side,x,y),fill=(*col,alpha//2),width=1)
            r=size*S;ld.ellipse((x-r,y-r,x+r,y+r),fill=(*col,alpha))
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    glow=layer.filter(ImageFilter.GaussianBlur(1.3));glow.putalpha(ImageChops.multiply(glow.getchannel('A'),mask))
    im.alpha_composite(glow);im.alpha_composite(layer);d=ImageDraw.Draw(im)
    # All rail annotations are permanent, with thin leader lines to both pins.
    for rail in rails:
        lx,ly=rail['label'];color=rail['color']
        for n in rail['pins']:
            px,py=pins[n];a=(lx*S, (ly+45)*S)
            dx,dy=a[0]-px,a[1]-py;length=math.hypot(dx,dy)
            end=(px+dx/length*34*S,py+dy/length*34*S)
            d.line((a,end),fill=(*color,155),width=1)
        # Dark outline gives frameless labels contrast on reflective metal.
        text(d,lx,ly,f'+{rail["v"]} V',color,56)
        text(d,lx,ly+43,','.join(map(str,rail['pins'])),color,27)
    active={n:r['color'] for r in rails for n in r['pins']}
    active.update({n:cyan for n in returns})
    for n,(x,y) in pins.items():
        c=active.get(n,(172,181,186))
        if n in active:
            r=28*S;d.ellipse((x-r,y-r,x+r,y+r),outline=c,width=2)
        text(d,x/S,y/S-55,str(n),c,30)
    text(d,512,806,'0 V · RETURN',cyan,42)
    text(d,512,852,'5,6',cyan,30)
    text(d,512,925,'PASS · ALL RAILS',(176,255,212),30)
    frames.append(im.convert('RGB'))

frames[25].save(OUT/'simultaneous-rails-preview.png')
sheet=Image.new('RGB',(SIZE*3,SIZE))
for i,n in enumerate([0,40,80]):sheet.paste(frames[n],(i*SIZE,0))
palette=sheet.quantize(colors=256)
for size,suffix in [(480,''),(240,'-240')]:
    q=[f.resize((size,size),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    target=OUT/f'simultaneous-rails{suffix}.gif'
    q[0].save(target,save_all=True,append_images=q[1:],duration=50,loop=0,optimize=False,disposal=2)
    with Image.open(target) as check:
        assert check.n_frames==COUNT and check.size==(size,size)
    print(target)
