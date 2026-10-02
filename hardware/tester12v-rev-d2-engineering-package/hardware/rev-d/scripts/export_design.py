"""Refresh schematic, manufacturing exports and checks without changing copper."""
import collections,csv,hashlib,json,subprocess,sys
from pathlib import Path
import pcbnew as pcb
import build_kicad as g
from design import ROOT,PARTS,REVISION
from jlc_catalog import CATALOG
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
M=ROOT/'manufacturing';V=ROOT/'validation';S=ROOT/'sourcing'
for d in (M,V,S,M/'gerbers',M/'stencil'):d.mkdir(exist_ok=True)
source=ROOT/'tester12v.kicad_pcb';before=hashlib.sha256(source.read_bytes()).hexdigest()
for q in PARTS:q['local_fp']='Tester:'+q['fp'].split(':',1)[1] if q['fp'] else ''
g.schematic('root','12 V multipin detector Rev '+REVISION+' - isolated USB power')
for k in range(3):g.schematic('bank'+str(k+1),f'Inputs {k*4+1}-{k*4+4}: passive sensing and ADC')
g.outputs()
groups=collections.defaultdict(list)
for q in PARTS:
    if q['mpn'] and not q['dnp']:groups[q['mpn']].append(q)
b=pcb.LoadBoard(str(source));fps={f.GetReference():f for f in b.GetFootprints()}
def write(path,header,rows):
    with path.open('w',newline='') as f:w=csv.writer(f);w.writerow(header);w.writerows(rows)
review=[];bom=[];cpl=[];pincheck=[]
for mpn,ps in groups.items():
    c=CATALOG[mpn];refs=','.join(q['ref'] for q in ps)
    review.append(dict(c,refs=refs,qty_per_board=len(ps)))
    bom.append([c['spec'],refs,c['package'],c['lcsc'],mpn])
    for q in ps:
        f=fps[q['ref']];pos=f.GetPosition();x,y=pcb.ToMM(pos.x),-pcb.ToMM(pos.y)
        if q['ref'].startswith('J') or q['ref']=='U7':
            shapes=[a for a in f.GraphicalItems() if isinstance(a,pcb.PCB_SHAPE) and a.GetLayer()==pcb.F_Fab]
            pts=[pt for a in shapes for pt in (a.GetStart(),a.GetEnd())]
            x=pcb.ToMM(min(z.x for z in pts)+max(z.x for z in pts))/2
            y=-pcb.ToMM(min(z.y for z in pts)+max(z.y for z in pts))/2
        cpl.append([q['ref'],f'{x:.4f}',f'{y:.4f}','Top',f'{f.GetOrientationDegrees():.4f}'])
        if q['ref'].startswith(('U','J','D')):
            pad=next(z for z in f.Pads() if z.GetNumber()=='1');pt=pad.GetPosition()
            note='Board coordinates: X right, Y down. Match physical pin 1 in JLC viewer.'
            if q['ref'] in ('J1','J2','J3'):note+=' WIRE OPENINGS toward lower edge (+Y); SCREWS UP. Library contact 1 is rightmost; drawing has no manufacturer pin-1 mark. Direction is the assembly requirement.'
            pincheck.append([q['ref'],mpn,pcb.ToMM(pt.x),pcb.ToMM(pt.y),pad.GetNetname(),note])
write(M/'jlc-bom.csv',['Comment','Designator','Footprint','LCSC Part #','Manufacturer Part Number'],bom)
write(M/'jlc-cpl-native-angles.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
write(M/'pin1-review.csv',['Reference','MPN','Pin1 X mm','Pin1 Y mm','Pin1 net','Instructions'],pincheck)
assert {r[0] for r in cpl}=={q['ref'] for q in PARTS if q['mpn'] and not q['dnp']}
cost=sum(r['qty_per_board']*r['unit_usd'] for r in review)
meta=dict(checked='2026-09-30',currency='USD',components_per_board=len(cpl),unique_skus=len(review),
 basic_skus=sum(r['category']=='Basic' for r in review),extended_skus=sum(r['category']=='Extended' for r in review),
 basic_components=sum(r['qty_per_board'] for r in review if r['category']=='Basic'),
 parts_per_board_usd=round(cost,4),nominal_parts_for_two_usd=round(cost*2,4),
 shortage_skus=[r['lcsc'] for r in review if r['stock']<2*r['qty_per_board']],
 assumptions='Displayed 1+ prices, nominal fitted quantities only. Excludes attrition, PCB, assembly/loading fees, shipping, duties, tax and external display/MCU. Stock not reserved. No Rev D JLC checkout quote yet.',
 assembly='New U7 power module, U5 regulator and J1-J3 terminals explicitly list Economic and Standard. Full BOM acceptance/DFM and placement rotations still require JLC review.',
 parts=review)
(S/'jlc-review.json').write_text(json.dumps(meta,indent=2)+'\n')
write(S/'jlc-review.csv',list(review[0]),[[r[k] for k in review[0]] for r in review])
log=[]
def run(args):
    r=subprocess.run([str(a) for a in args],capture_output=True,text=True)
    log.append('$ '+' '.join(str(a) for a in args)+'\n'+r.stdout+r.stderr)
    (V/'manufacturing-export.log').write_text('\n'.join(log))
    if r.returncode:raise RuntimeError(log[-1])
run([CLI,'sch','export','netlist','--format','kicadxml','--output',V/'schematic.net',ROOT/'tester12v.kicad_sch'])
run([CLI,'sch','erc','--format','json','--exit-code-violations','--output',V/'erc.json',ROOT/'tester12v.kicad_sch'])
run([CLI,'pcb','drc','--schematic-parity','--format','json','--exit-code-violations','--output',V/'drc-final.json',source])
run([sys.executable,ROOT/'scripts/audit_board.py'])
run([CLI,'pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','--output',M/'gerbers',source])
run([CLI,'pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-map','--map-format','pdf','--output',M/'gerbers',source])
run([CLI,'pcb','export','pos','--format','csv','--units','mm','--smd-only','--exclude-dnp','--output',M/'placements-smd.csv',source])
run([sys.executable,ROOT/'scripts/plot_stencil.py'])
run([CLI,'sch','export','pdf','--output',ROOT/'previews/schematic.pdf',ROOT/'tester12v.kicad_sch'])
assert before==hashlib.sha256(source.read_bytes()).hexdigest(),'Export changed PCB'
print(json.dumps({k:v for k,v in meta.items() if k!='parts'},indent=2))
