"""Beauty-first three-rail concept; source geometry is unchanged. Simulated data."""
from pathlib import Path
import math, json, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'
W=720; s=W/1024; FPS=20; N=120
source=Image.open(OUT/'hr10a-10p-12p.png').convert('RGBA').resize((W,W),Image.Resampling.LANCZOS)
back=Image.new('RGBA',(W,W),'#080e13');back.alpha_composite(source)
back=ImageEnhance.Brightness(back.convert('RGB')).enhance(.78)
geo=json.loads((OUT/'geometry.json').read_text())
P={int(k):(512+64*x,512+64*y) for k,(x,y) in geo['pin_centres_mm'].items()}
cold=(116,229,251);hot=(255,214,140)
rails=[(5,[1,2],(208,455),(255,230,176)),(12,[8,9],(811,455),(255,218,147)),(24,[10,12],(512,265),(255,198,106))]
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
def box(x,y,r):return ((x-r)*s,(y-r)*s,(x+r)*s,(y+r)*s)
def bez(a,b,c,z,u):
    v=1-u
    x=v**3*a[0]+3*v*v*u*b[0]+3*v*u*u*c[0]+u**3*z[0]
    y=v**3*a[1]+3*v*v*u*b[1]+3*v*u*u*c[1]+u**3*z[1]
    dx=3*v*v*(b[0]-a[0])+6*v*u*(c[0]-b[0])+3*u*u*(z[0]-c[0])
    dy=3*v*v*(b[1]-a[1])+6*v*u*(c[1]-b[1])+3*u*u*(z[1]-c[1]);l=max(1,math.hypot(dx,dy))
    return x,y,-dy/l,dx/l

# A spacious shared field; paths end precisely at the physical contacts.
hub=(548,608)
branches=[]
for n in [5,6]:
    a=P[n];branches.append((a,(a[0]-28,a[1]-42),(530,620),hub,0,.28,40,12,cold))
for v,group,_,color in rails:
    for n in group:
        z=P[n]
        bend=-62 if n in [1,2] else 78 if n in [8,9] else 0
        branches.append((hub,(590+bend,548),(z[0]+bend,z[1]+75),z,.28,1,round(22+v*1.7),7+v*.38,color))
random.seed(48); seeds=[(random.random(),random.random()*math.tau,random.uniform(.3,1),random.uniform(.9,2.2)) for _ in range(80)]
mask=Image.new('L',(W,W),0);d=ImageDraw.Draw(mask);d.ellipse(box(512,512,239),fill=255)
for x,y in P.values():d.ellipse(box(x,y,25),fill=0)

def lettering(image,x,y,value,color,size):
    f=ImageFont.truetype(fontpath,round(size*s))
    shadow=Image.new('RGBA',(W,W));dd=ImageDraw.Draw(shadow)
    dd.text((x*s,(y+2)*s),value,font=f,fill=(0,0,0,245),anchor='mm',stroke_width=round(3*s))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2*s)))
    ImageDraw.Draw(image).text((x*s,y*s),value,font=f,fill=color,anchor='mm')

yy,xx=np.mgrid[0:W,0:W]
radius=np.hypot(xx-512*s,yy-512*s)/s
anglemap=np.arctan2(yy-512*s,xx-512*s)
ridge=np.sqrt(np.maximum(0,np.sin(np.pi*np.clip((radius-405)/34,0,1))))
frames=[]
for frame in range(N):
    t=frame/N;im=back.copy()
    # The status collar is metal with a sweeping reflection, not a solid neon line.
    shine=np.maximum(0,np.cos(anglemap-math.tau*t))**22
    opposite=np.maximum(0,-np.cos(anglemap-math.tau*t))**8
    value=.36+.30*ridge+.26*shine+.08*opposite
    rgb=np.clip(value[:,:,None]*np.array([75,227,161])+shine[:,:,None]*70,0,255).astype(np.uint8)
    collar=Image.fromarray(rgb)
    # Replace only the original collar annulus, preserving every locating key.
    cm=Image.new('L',(W,W));cmd=ImageDraw.Draw(cm)
    cmd.ellipse(box(512,512,439),fill=255);cmd.ellipse(box(512,512,404),fill=0)
    im=Image.composite(collar,im,cm)
    light=Image.new('RGB',(W,W));ld=ImageDraw.Draw(light)
    for j,(a,b,c,z,start,end,count,width,warm) in enumerate(branches):
        for offset,phase,spread,size in seeds[:count]:
            u=(offset+2*t+j*.17)%1
            x,y,nx,ny=bez(a,b,c,z,u)
            spiral=math.sin(phase+u*math.tau*1.5+math.tau*t)
            off=width*spread*math.sin(math.pi*u)*spiral
            x+=nx*off;y+=ny*off
            q=start+(end-start)*u
            mid=(213,247,239)
            lo,hi,w=(cold,mid,q/.5) if q<.5 else (mid,warm,(q-.5)/.5)
            strength=(.45+.55*(spiral+1)/2)*min(1,u*15,(1-u)*15)
            color=tuple(round((v+(w2-v)*w)*strength) for v,w2 in zip(lo,hi))
            xx,yy,_,_=bez(a,b,c,z,max(0,u-.018))
            ld.line((xx*s,yy*s,x*s,y*s),fill=tuple(round(v*.4) for v in color),width=1)
            ld.ellipse(box(x,y,size),fill=color)
    light=Image.composite(light,Image.new('RGB',(W,W)),mask)
    im=ImageChops.screen(im,light.filter(ImageFilter.GaussianBlur(3*s)))
    im=ImageChops.screen(im,light)
    halos=Image.new('RGB',(W,W));hd=ImageDraw.Draw(halos)
    active={n:col for _,group,_,col in rails for n in group};active.update({5:cold,6:cold})
    for n,color in active.items():
        x,y=P[n];hd.ellipse(box(x,y,26),outline=color,width=round(4*s))
    im=ImageChops.screen(im,halos.filter(ImageFilter.GaussianBlur(7*s)))
    im=ImageChops.screen(im,halos.filter(ImageFilter.GaussianBlur(2*s)))
    im=ImageChops.screen(im,halos)
    im=im.convert('RGBA')
    for v,group,(x,y),color in rails:
        lettering(im,x,y,f'{v} V',color,78)
        # Matching short accent under each value, keeping the face quiet.
    lettering(im,512,805,'0 V',cold,60)
    lettering(im,512,858,'COMMON RETURN',(127,164,175),21)
    frames.append(im.convert('RGB').resize((480,480),Image.Resampling.LANCZOS))
    if frame%30==0:print(f'Rendered {frame}/{N}',flush=True)

frames[30].save(OUT/'luminous-rails-preview.png')
palette=Image.new('RGB',(480*3,480))
for i,k in enumerate([0,40,80]):palette.paste(frames[k],(i*480,0))
palette=palette.quantize(colors=256)
for size,suffix in [(480,''),(240,'-240')]:
    q=[f.resize((size,size),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    target=OUT/f'luminous-rails{suffix}.gif'
    q[0].save(target,save_all=True,append_images=q[1:],duration=50,loop=0,optimize=False,disposal=2)
    with Image.open(target) as check:assert check.n_frames==N
    print(target,flush=True)
