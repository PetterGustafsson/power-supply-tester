"""Render a simulated, expected-map PASS demo over the original Hirose artwork.

No hardware is read or flashed. Particle speed does not represent current.
"""
from pathlib import Path
import json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
SIZE, FPS, HOLD = 480, 20, 3
S = SIZE / 1024
base = Image.open(OUT / 'hr10a-10p-12p.png').convert('RGBA').resize((SIZE,SIZE), Image.Resampling.LANCZOS)
background = Image.new('RGBA', base.size, '#12191f'); background.alpha_composite(base)
geometry = json.loads((OUT / 'geometry.json').read_text())
pins = {int(n): ((512+64*x)*S,(512+64*y)*S) for n,(x,y) in geometry['pin_centres_mm'].items()}
fontpath='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size): return ImageFont.truetype(fontpath, round(size*S))
amber, cyan = (255,215,122), (140,231,244)
# Each scenario is independently assumed to match its expected wiring map.
scenarios = [
    {'name':'Single pair', 'return':[5], 'rails':[(3.3,[1])]},
    {'name':'Shared 5 V', 'return':[5,6], 'rails':[(5,[1,2,3])]},
    {'name':'Shared 12 V', 'return':[3,4,5], 'rails':[(12,[8,9,10,12])]},
    {'name':'Three voltage rails', 'return':[5,6], 'rails':[(5,[1,2]),(12,[8,9]),(24,[10,12])]},
]
phases=[(scenario,railindex) for scenario in scenarios for railindex in range(len(scenario['rails']))]
random.seed(31)
seeds=[(random.random(),random.uniform(-1,1),random.uniform(1.3,2.6)) for _ in range(48)]

def text(draw,xy,value,fill,size):
    draw.text((xy[0]*S,xy[1]*S),value,font=font(size),fill=fill,anchor='mm',stroke_width=1,stroke_fill='#111920')

def position(a,b,u,bend):
    dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
    nx,ny=-dy/length,dx/length
    bow=math.sin(math.pi*u)*bend
    return a[0]+dx*u+nx*bow,a[1]+dy*u+ny*bow,nx,ny

# Prevent animation from covering contacts or stationary pin numbers.
mask=Image.new('L',(SIZE,SIZE),0); md=ImageDraw.Draw(mask)
md.ellipse((512*S-240*S,512*S-240*S,512*S+240*S,512*S+240*S),fill=255)
for x,y in pins.values():
    r=33*S;md.ellipse((x-r,y-r,x+r,y+r),fill=0)
    md.rectangle((x-24*S,y-73*S,x+24*S,y-38*S),fill=0)

frames=[]
for phaseindex,(scenario,railindex) in enumerate(phases):
    voltage,positive=scenario['rails'][railindex]
    active=set(positive); returns=set(scenario['return'])
    allpositive={n for _,group in scenario['rails'] for n in group}
    for tick in range(FPS*HOLD):
        frame=background.copy(); draw=ImageDraw.Draw(frame)
        seconds=(phaseindex*FPS*HOLD+tick)/FPS
        # Green means this DEMO scenario matches its specified expected map.
        box=tuple(v*S for v in (90,90,934,934))
        draw.ellipse(box,outline=(49,190,125),width=round(30*S))
        angle=seconds*60
        draw.arc(box,angle,angle+38,fill=(171,255,220),width=round(11*S))
        # Group focus changes with a short particle fade, not moving contacts.
        fade=min(1,tick/5,(FPS*HOLD-1-tick)/5)
        hub=(524*S,493*S)
        if len(positive)==1 and len(returns)==1:
            branches=[(pins[next(iter(returns))],pins[positive[0]],0,1,45)]
        else:
            branches=[(pins[n],hub,0,.5,48) for n in sorted(returns)]
            branches += [(hub,pins[n],.5,1, max(18,round(48*len(returns)/len(positive)))) for n in positive]
        particles=Image.new('RGBA',frame.size); pd=ImageDraw.Draw(particles)
        for branch,(a,b,start,end,count) in enumerate(branches):
            for index,(offset,spread,size) in enumerate(seeds[:count]):
                u=(offset+seconds*.65+branch*.19)%1
                x,y,nx,ny=position(a,b,u,(branch-1)*5*S)
                offset_side=spread*13*S*math.sin(math.pi*u)
                x+=nx*offset_side;y+=ny*offset_side
                v=start+(end-start)*u
                cold,white,hot=(90,218,255),(226,248,240),(255,195,94)
                lo,hi,w=(cold,white,2*v) if v<.5 else (white,hot,2*v-1)
                color=tuple(round(p+(q-p)*w) for p,q in zip(lo,hi))
                alpha=round(235*fade*min(1,u*12,(1-u)*12))
                xx,yy,_,_=position(a,b,max(0,u-.032),(branch-1)*5*S)
                pd.line((xx+nx*offset_side,yy+ny*offset_side,x,y),fill=(*color,alpha//2),width=1)
                r=size*S;pd.ellipse((x-r,y-r,x+r,y+r),fill=(*color,alpha))
        # Multiply alpha by the keep-out mask; no particle crosses a key or label.
        from PIL import ImageChops
        particles.putalpha(ImageChops.multiply(particles.getchannel('A'),mask))
        glow=particles.filter(ImageFilter.GaussianBlur(1.3))
        glow.putalpha(ImageChops.multiply(glow.getchannel('A'),mask))
        frame.alpha_composite(glow);frame.alpha_composite(particles)
        draw=ImageDraw.Draw(frame)
        for n,(x,y) in pins.items():
            if n in allpositive or n in returns:
                color=cyan if n in returns else amber
                if n in allpositive and n not in active:color=tuple(round(c*.45) for c in color)
                r=28*S;draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=2)
            color=amber if n in active else cyan if n in returns else (174,184,188)
            text(draw,(x/S,y/S-55),str(n),color,31)
        text(draw,(512,144),f'+{voltage:g} V',amber,72)
        label='RETURN '+','.join(map(str,sorted(returns)))
        text(draw,(512,856),label,cyan,35)
        status='PASS' if len(scenario['rails'])==1 else f'PASS · RAIL {railindex+1}/{len(scenario["rails"])}'
        text(draw,(512,927),status,(176,255,212),30)
        frames.append(frame.convert('RGB'))
    frames[-FPS].save(OUT/f'correct-constellation-{phaseindex+1}.png')

samples=Image.new('RGB',(SIZE*3,SIZE*2))
for i in range(len(phases)):samples.paste(frames[i*FPS*HOLD+FPS],((i%3)*SIZE,(i//3)*SIZE))
samples.save(OUT/'correct-constellations-overview.png')
palette=samples.quantize(colors=256)
for size,suffix in [(480,''),(240,'-240')]:
    quantized=[im.resize((size,size),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    path=OUT/f'correct-constellations{suffix}.gif'
    quantized[0].save(path,save_all=True,append_images=quantized[1:],duration=1000//FPS,loop=0,optimize=False,disposal=2)
    with Image.open(path) as check:
        assert check.n_frames==len(frames) and check.size==(size,size)
    print(f'{path}: {len(frames)} frames, {len(frames)/FPS:g} seconds')
(OUT/'correct-constellations.json').write_text(json.dumps({'simulated':True,'view':geometry['view'],'fps':FPS,'seconds_per_rail':HOLD,'scenarios':scenarios,'meaning':'Green is an assumed expected-map match. Particle speed is illustrative, not measured current.'},indent=2))
