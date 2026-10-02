"""Annotated three-rail concept; source geometry is unchanged. Simulated data."""
from pathlib import Path
import math, json, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'
W=720; s=W/1024; FPS=30; N=360
source=Image.open(OUT/'hr10a-10p-12p.png').convert('RGBA').resize((W,W),Image.Resampling.LANCZOS)
back=Image.new('RGBA',(W,W),'#080e13');back.alpha_composite(source)
back=ImageEnhance.Brightness(back.convert('RGB')).enhance(.78)
geo=json.loads((OUT/'geometry.json').read_text())
P={int(k):(512+64*x,512+64*y) for k,(x,y) in geo['pin_centres_mm'].items()}
cold=(116,229,251);hot=(255,214,140)
rails=[(5,[1,2],(208,455),(228,245,210)),(12,[8,9],(811,455),(255,192,62)),(24,[10,12],(512,248),(255,103,122))]
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
for n in [4,5,6]:
    a=P[n];branches.append((a,(a[0]-28,a[1]-42),(530,620),hub,0,.28,85,18,cold))
for v,group,_,color in rails:
    for n in group:
        z=P[n]
        bend=-115 if n in [1,2] else 120 if n in [8,9] else -12
        branches.append((hub,(590+bend,548),(z[0]+bend,z[1]+75),z,.28,1,round(70+v*3),11+v*.30,color))
random.seed(48); seeds=[(random.random(),random.random()*math.tau,random.uniform(.3,1),random.uniform(.8,2.4)) for _ in range(150)]
mask=Image.new('L',(W,W),0);d=ImageDraw.Draw(mask);d.ellipse(box(512,512,239),fill=255)
for x,y in P.values():
    d.ellipse(box(x,y,32),fill=0)


def lettering(image,x,y,value,color,size):
    f=ImageFont.truetype(fontpath,round(size*s))
    shadow=Image.new('RGBA',(W,W));dd=ImageDraw.Draw(shadow)
    dd.text((x*s,(y+2)*s),value,font=f,fill=(0,0,0,245),anchor='mm',stroke_width=round(3*s))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2*s)))
    ImageDraw.Draw(image).text((x*s,y*s),value,font=f,fill=color,anchor='mm')

# Raised molded numerals are part of the insulator, beneath the flowing light.
md=ImageDraw.Draw(back)
numberfont=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',round(30*s))
for n,(px,py) in P.items():
    x,y=(px-35,py-25) if n==1 else (px+35,py-25) if n==9 else (px,py-55)
    md.text(((x+1.5)*s,(y+2)*s),str(n),font=numberfont,fill=(3,7,9),anchor='mm',stroke_width=1)
    md.text(((x-1)*s,(y-1)*s),str(n),font=numberfont,fill=(108,119,120),anchor='mm')
    md.text((x*s,y*s),str(n),font=numberfont,fill=(57,66,68),anchor='mm')

yy,xx=np.mgrid[0:W,0:W]
radius=np.hypot(xx-512*s,yy-512*s)/s
anglemap=np.arctan2(yy-512*s,xx-512*s)
ridge=np.sqrt(np.maximum(0,np.sin(np.pi*np.clip((radius-405)/34,0,1))))
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
encoder=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{W}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'silk-molded.mp4')],stdin=subprocess.PIPE)
frames=[]
for frame in range(N):
    t=frame/N;sec=frame/FPS
    reveal=smooth((sec-.2)/1.15)*(1-smooth((sec-10.6)/1.4))
    ground_power=smooth((sec-1.0)/.7)
    powers=[smooth((sec-onset)/1.2) for onset in [2.0,2.65,3.3]]
    pulses=[.78+.22*(.5+.5*math.cos(sec*2.1-ri*math.tau/3)) for ri in range(3)]
    im=back.copy()
    # The status collar is metal with a sweeping reflection, not a solid neon line.
    shine=np.maximum(0,np.cos(anglemap-math.tau*t))**22
    opposite=np.maximum(0,-np.cos(anglemap-math.tau*t))**8
    value=.28+.28*ridge+.38*shine+.08*opposite
    # A blue-white wake-up changes to emerald only after all rails settle.
    accepted=smooth((sec-4.5)/.8)
    rim=np.array([125,156,169])*(1-accepted)+np.array([75,227,161])*accepted
    rgb=np.clip(value[:,:,None]*rim+shine[:,:,None]*70,0,255).astype(np.uint8)
    collar=Image.fromarray(rgb)
    # Replace only the original collar annulus, preserving every locating key.
    cm=Image.new('L',(W,W));cmd=ImageDraw.Draw(cm)
    cmd.ellipse(box(512,512,439),fill=255);cmd.ellipse(box(512,512,404),fill=0)
    im=Image.composite(collar,im,cm)
    light=Image.new('RGB',(W,W));ld=ImageDraw.Draw(light)
    for j,(a,b,c,z,start,end,count,width,warm) in enumerate(branches):
        onset=1.0 if j<3 else [2.0,2.65,3.3][(j-3)//2]
        power=ground_power if j<3 else powers[(j-3)//2]
        if j>=3:power*=pulses[(j-3)//2]
        front=smooth((sec-onset)/1.2)
        if power<.005:continue
        # Fine twisting filaments form a flowing silk ribbon beneath particles.
        for strand in range(9):
            last=None
            for step in range(81):
                u=step/80
                if u>front:break
                x,y,nx,ny=bez(a,b,c,z,u)
                twist=math.sin(strand*math.tau/9+u*math.tau*1.8-sec*.95)
                displacement=width*math.sin(math.pi*u)*twist
                x+=nx*displacement;y+=ny*displacement
                q=start+(end-start)*u
                mid=(214,248,239)
                low,high,w=(cold,mid,q/.5) if q<.5 else (mid,warm,(q-.5)/.5)
                intensity=(.08+.11*(twist+1)/2)*power*math.sin(math.pi*u)**.3
                col=tuple(round((lo+(hi-lo)*w)*intensity) for lo,hi in zip(low,high))
                if last:ld.line((*last,x*s,y*s),fill=col,width=1)
                last=(x*s,y*s)
        for offset,phase,spread,size in seeds[:count]:
            u=(offset+sec*.43+j*.17)%1
            if u>front:continue
            x,y,nx,ny=bez(a,b,c,z,u)
            spiral=math.sin(phase+u*math.tau*1.5+math.tau*t)
            off=width*spread*math.sin(math.pi*u)*spiral
            x+=nx*off;y+=ny*off
            q=start+(end-start)*u
            mid=(213,247,239)
            lo,hi,w=(cold,mid,q/.5) if q<.5 else (mid,warm,(q-.5)/.5)
            strength=power*(.45+.55*(spiral+1)/2)*min(1,u*15,(1-u)*15)
            color=tuple(round((v+(w2-v)*w)*strength) for v,w2 in zip(lo,hi))
            xx,yy,_,_=bez(a,b,c,z,max(0,u-.018))
            ld.line((xx*s,yy*s,x*s,y*s),fill=tuple(round(v*.4) for v in color),width=1)
            ld.ellipse(box(x,y,size),fill=color)
    light=Image.composite(light,Image.new('RGB',(W,W)),mask)
    im=ImageChops.screen(im,light.filter(ImageFilter.GaussianBlur(3*s)))
    im=ImageChops.screen(im,light)
    halos=Image.new('RGB',(W,W));hd=ImageDraw.Draw(halos)
    active={n:col for _,group,_,col in rails for n in group};active.update({4:cold,5:cold,6:cold})
    for n,color in active.items():
        x,y=P[n]
        power=ground_power if n in [4,5,6] else powers[next(i for i,(_,group,_,_) in enumerate(rails) if n in group)]
        if n not in [4,5,6]:power*=pulses[next(i for i,(_,group,_,_) in enumerate(rails) if n in group)]
        onset=1.0 if n in [4,5,6] else [2.0,2.65,3.3][next(i for i,(_,group,_,_) in enumerate(rails) if n in group)]+.6
        flash=math.exp(-((sec-onset-.28)/.18)**2)
        col=tuple(min(255,round(c*power+flash*65)) for c in color)
        hd.ellipse(box(x,y,26),outline=col,width=round((4+flash*3)*s))
        if flash>.03:hd.ellipse(box(x,y,29+(sec-onset)*16),outline=tuple(round(c*flash*.4) for c in color),width=1)
    im=ImageChops.screen(im,halos.filter(ImageFilter.GaussianBlur(7*s)))
    im=ImageChops.screen(im,halos.filter(ImageFilter.GaussianBlur(2*s)))
    im=ImageChops.screen(im,halos)
    im=im.convert('RGBA')
    # Matching saturated halos and labels identify rails without leader lines.
    for ri,(v,group,(x,y),color) in enumerate(rails):
        color=tuple(round(c*(.15+.85*powers[ri])*pulses[ri]) for c in color)
        lettering(im,x,y,f'{v:.1f} V',color,62)
    lettering(im,512,809,'0.0 V',cold,58)
    lettering(im,512,854,'RETURN',cold,25)
    im=ImageEnhance.Brightness(im.convert('RGB')).enhance(reveal)
    encoder.stdin.write(im.tobytes())
    frames.append(im.resize((480,480),Image.Resampling.LANCZOS))
    if frame%30==0:print(f'Rendered {frame}/{N}',flush=True)

encoder.stdin.close();assert encoder.wait()==0
frames[180].save(OUT/'silk-molded-preview.png')
palette=Image.new('RGB',(480*3,480))
for i,k in enumerate([150,200,250]):palette.paste(frames[k],(i*480,0))
palette=palette.quantize(colors=256)
for size,suffix in [(480,''),(240,'-240')]:
    q=[f.resize((size,size),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    target=OUT/f'silk-molded{suffix}.gif'
    q[0].save(target,save_all=True,append_images=q[1:],duration=[30,30,40]*(N//3),loop=0,optimize=False,disposal=2)
    with Image.open(target) as check:
        assert 0 < check.n_frames <= N
        duration=0
        for i in range(check.n_frames):
            check.seek(i); duration+=check.info.get("duration",0)
        assert duration==12000
    print(target,flush=True)
