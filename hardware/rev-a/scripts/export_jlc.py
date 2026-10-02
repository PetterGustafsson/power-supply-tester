"""Export sourcing-only update; never write the routed board or its Gerbers."""
import csv,json,hashlib,collections,xml.etree.ElementTree as ET
import pcbnew as pcb
import build_kicad as g
from design import ROOT,PARTS
from jlc_catalog import CATALOG,SUBSTITUTIONS

M=ROOT/'manufacturing';S=ROOT/'sourcing'
board_path=ROOT/'tester12v.kicad_pcb'
board_hash=hashlib.sha256(board_path.read_bytes()).hexdigest()
before=json.loads((S/'manifest-before-jlc.json').read_text())['parts']
old={p['ref']:p for p in before}
electrical_fields=['ref','sym','value','pins','fp','pcb','sch','page','dnp','schrot','uuid']
for p in PARTS:
    for key in electrical_fields:
        assert p[key]==old[p['ref']][key],(p['ref'],key)
    p['local_fp']='Tester:'+p['fp'].split(':',1)[1] if p['fp'] else ''
g.schematic('root','12 V universal pin-voltage tester - power and controller')
for k in range(3):g.schematic('bank'+str(k+1),f'Inputs {k*4+1}-{k*4+4}: protected sensing and ADC')
g.outputs()
groups=collections.defaultdict(list)
all_groups=collections.defaultdict(list)
for p in PARTS:
    if p['ref'].startswith(('#','TP')):continue
    all_groups[(p['mpn'],p['local_fp'],p['dnp'])].append(p)
    if not p['dnp']:groups[p['mpn']].append(p)
assert sum(map(len,groups.values()))==114
assert len(groups)==24
def write_csv(path,header,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
write_csv(M/'bom-grouped.csv',['References','Quantity','Value','Manufacturer','MPN','Footprint','Populate','LCSC'],
    [[','.join(p['ref'] for p in ps),len(ps),'; '.join(dict.fromkeys(p['value'] for p in ps)),ps[0]['maker'],key[0],key[1],'NO' if key[2] else 'YES',ps[0]['lcsc']] for key,ps in all_groups.items()])
header=['Comment','Designator','Footprint','LCSC Part #','Manufacturer Part Number']
upload=[];review=[]
for mpn,ps in groups.items():
    c=CATALOG[mpn];refs=','.join(p['ref'] for p in ps)
    upload.append([c['spec'],refs,c['package'],c['lcsc'],mpn])
    old_mpn=old[ps[0]['ref']]['mpn'];o=CATALOG[old_mpn]
    review.append(dict(c,refs=refs,qty_per_board=len(ps),old_mpn=old_mpn,old_lcsc=o['lcsc'],
       old_category=o['category'],old_unit_usd=o['unit_usd'],old_stock=o['stock'],
       old_moq=o['moq'],old_price_basis=o['price_basis'],
       change=SUBSTITUTIONS[old_mpn][2] if old_mpn in SUBSTITUTIONS else 'Retained exact original'))
write_csv(M/'jlc-bom.csv',header,upload)
budget=[r.copy() for r in upload]
for r in budget:
    if r[3]=='C207399':r[3]='C657391';r[4]='ADG4612BRUZ';r[0]=CATALOG['ADG4612BRUZ']['spec']
write_csv(M/'jlc-bom-preorder-switches.csv',header,budget)
board=pcb.LoadBoard(str(board_path));fps={f.GetReference():f for f in board.GetFootprints()}
cpl=[]
for ps in groups.values():
    for p in ps:
        f=fps[p['ref']];pos=f.GetPosition();x,y=pcb.ToMM(pos.x),-pcb.ToMM(pos.y)
        if p['ref'].startswith('J'):
            # Connector origins are pin 1. Use the F.Fab body outline centre.
            shapes=[a for a in f.GraphicalItems() if isinstance(a,pcb.PCB_SHAPE) and a.GetLayer()==pcb.F_Fab]
            points=[pt for a in shapes for pt in (a.GetStart(),a.GetEnd())]
            assert points,p['ref']
            x=pcb.ToMM(min(pt.x for pt in points)+max(pt.x for pt in points))/2
            y=-pcb.ToMM(min(pt.y for pt in points)+max(pt.y for pt in points))/2
        cpl.append([p['ref'],f'{x:.4f}',f'{y:.4f}','Top',f'{f.GetOrientationDegrees():.4f}'])
write_csv(M/'jlc-cpl.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
assert len(cpl)==len(set(r[0] for r in cpl))==114
assert set(r[0] for r in cpl)=={p['ref'] for ps in groups.values() for p in ps}
extended=sum(r['category']=='Extended' for r in review)
basic=sum(r['category']=='Basic' for r in review)
parts_cost=sum(r['qty_per_board']*2*r['unit_usd'] for r in review)
meta=dict(checked='2026-09-30',currency='USD',boards=2,unique_skus=len(review),
    basic_skus=basic,extended_skus=extended,components_per_board=114,
    in_stock_skus=sum(r['stock']>0 for r in review),
    shortage_skus=[r['lcsc'] for r in review if r['stock']<2*r['qty_per_board']],
    nominal_parts_usd=round(parts_cost,4),
    nominal_parts_excluding_preorder_usd=round(sum(r['qty_per_board']*2*r['unit_usd'] for r in review if r['stock']),4),
    economic_fee_reduction_usd=round(basic*3.07,2),economic_extended_loading_usd=round(extended*3.07,2),
    optional_switch_preorder_reduction_usd=round(6*(6.7450-2.7916),4),
    board_sha256=board_hash,copper_changed=False,
    assumptions='1+ displayed unit prices; nominal fitted quantities only; no attrition, MOQ overhead, PCB, assembly, shipping, tax or display. Converter price is an unconfirmed preorder estimate. Not a JLC quote.',
    fee_source='https://jlcpcb.com/help/article/pcb-assembly-price',
    parts=review)
(S/'jlc-review.json').write_text(json.dumps(meta,indent=2)+'\n')
(S/'jlc-catalog-snapshot.json').write_text(json.dumps(list(CATALOG.values()),indent=2)+'\n')
write_csv(S/'jlc-review.csv',list(review[0]),[[r[k] for k in review[0]] for r in review])
assert hashlib.sha256(board_path.read_bytes()).hexdigest()==board_hash
print(json.dumps({k:v for k,v in meta.items() if k!='parts'},indent=2))
