"""Compose a vector-labelled A2 poster over the source-CAD component render."""
from pathlib import Path
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'output/final-layout-poster'
PREVIEW='--preview' in sys.argv
OUT=ROOT/('tmp/pdfs' if PREVIEW else 'output/pdf')
OUT.mkdir(parents=True,exist_ok=True)
fonts=ART/'fonts';fonts.mkdir(exist_ok=True)
for name,weight in [('Regular',400),('Medium',500),('Semibold',600)]:
    path=fonts/f'Inter-{name}.ttf'
    if not path.exists():
        from fontTools.ttLib import TTFont as SourceFont
        from fontTools.varLib.instancer import instantiateVariableFont
        f=SourceFont(ROOT/'assets/fonts/inter/Inter-opsz-wght.ttf')
        instantiateVariableFont(f,{'wght':weight,'opsz':24},inplace=True).save(path)
    pdfmetrics.registerFont(TTFont('Inter-'+name,str(path)))

pdf=OUT/('final-layout-preview.pdf' if PREVIEW else 'power-supply-tester-final-layout.pdf')
W,H=594*mm,420*mm
c=canvas.Canvas(str(pdf),pagesize=(W,H))
c.setTitle('Power supply tester - final component layout')
c.setAuthor('Petter')
c.setSubject('I15 enclosure, Rev D2 electronics, confirmed assembly fasteners')
c.drawImage(str(ART/('layout-preview.png' if PREVIEW else 'layout-render.png')),0,0,W,H)
INK=HexColor('#242627');MUTED=HexColor('#555755');ORANGE=HexColor('#D95B19')

def text(t,x,y,size=12,font='Regular',color=INK,tracking=0,align='center'):
    width=pdfmetrics.stringWidth(t,'Inter-'+font,size)+tracking*max(0,len(t)-1)
    if align=='center':x=x*mm-width/2
    elif align=='right':x=x*mm-width
    else:x=x*mm
    obj=c.beginText(x,y*mm);obj.setFont('Inter-'+font,size);obj.setFillColor(color);obj.setCharSpace(tracking);obj.textOut(t);c.drawText(obj)
def label(name,detail,x,y=244,second=None):
    text(name,x,y,12,'Medium')
    text(detail,x,y-6.2,9.3,color=MUTED)
    if second:text(second,x,y-11.4,9.0,color=MUTED)

text('POWER SUPPLY TESTER',297,394,32,'Medium',tracking=2.6)
text('FINAL COMPONENT LAYOUT',297,382,10,'Medium',tracking=2.1,color=MUTED)
text('I15  /  REV D2',567,395,9.2,'Medium',align='right',tracking=.8)
c.setStrokeColor(ORANGE);c.setLineWidth(1.4);c.line(285*mm,375*mm,309*mm,375*mm)

label('Top shell  ×1','Marble finish',115)
label('Base  ×1','Charcoal PLA',297)
label('Measurement PCBA  ×1','Rev D2 · 12 sensing inputs',479)

label('Display module  ×1','Waveshare ESP32-S3-LCD-1.28',78,158)
label('Crown  ×1','Orange PLA',180,158)
label('Display retainer  ×1','Charcoal PLA',275,158)
label('Foam pad  ×1','2 mm thick',363,158)
label('USB-C extender  ×1','4 inch · 90° male to female',480,158,'Soft flat cable')

label('12-contact connector cable  ×1','HR10A-10P-12S(73) · 12 ferrule ends',297,83)

text('AS-BUILT HARDWARE',27,67.5,9.8,'Semibold',color=ORANGE,tracking=1.1,align='left')
text('ALL SCREWS: BLACK · FLAT PHILLIPS · SELF-TAPPING',567,67.5,9.6,'Medium',tracking=.5,align='right')
c.setLineWidth(.35);c.setStrokeColor(HexColor('#AAA9A2'));c.line(27*mm,64.5*mm,567*mm,64.5*mm)

label('Display harness  ×1','JST-XH5 to display',69,29)
label('PCB + display screws  ×6','M2 × 6 mm',212,29,'4 PCB · 2 display')
label('Case screws  ×4','M2.5 × 10 mm',331.5,29)
label('Rubber feet  ×4','Base grommets',445,29)
label('Cable tie  ×1','Cable strain relief',526,29)

c.setStrokeColor(HexColor('#A2A29C'));c.setLineWidth(.35);c.line(27*mm,11.5*mm,567*mm,11.5*mm)
text('I15 ENCLOSURE · REV D2 ELECTRONICS · 22 OCT 2026',27,6.5,7.4,'Medium',color=MUTED,tracking=.55,align='left')
text('COMPONENT LAYOUT · NOT TO SCALE',567,6.5,7.4,color=MUTED,tracking=.55,align='right')
c.showPage();c.save()
print(pdf)
