"""Validate and package the finished release without changing its PCB."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parents[1]
MFG=ROOT/'manufacturing';VAL=ROOT/'validation'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
audit=json.loads((VAL/'board-audit.json').read_text())
assert digest(ROOT/'tester12v.kicad_pcb')==audit['board_sha256']
assert digest(VAL/'schematic.net')==audit['schematic_netlist_sha256']
assert audit['status']=='PASS'
erc=json.loads((VAL/'erc.json').read_text());drc=json.loads((VAL/'drc-final.json').read_text())
assert all(not s['violations'] for s in erc['sheets'])
assert not any(drc[k] for k in ('violations','unconnected_items','schematic_parity'))
assert json.loads((VAL/'circuit-results.json').read_text())['status']=='PASS'
spice=json.loads((VAL/'spice-results.json').read_text())
assert len(spice['cases'])==12 and all(c['within_ADC_absolute_voltage_window'] for c in spice['cases'])
assert (VAL/'firmware-tests.log').read_text().startswith('PASS:')
assert 'Sketch uses 389969 bytes' in (VAL/'firmware-build.log').read_text()

suffixes=['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs',
          'F_Silkscreen.gto','B_Silkscreen.gbo','Edge_Cuts.gm1','PTH.drl','NPTH.drl']
fabrication=[MFG/'gerbers'/('tester12v-'+s) for s in suffixes]
for file in fabrication:
    data=file.read_text();assert len(data)>100
    assert data.rstrip().endswith('M30' if file.suffix=='.drl' else 'M02*')
outline=(MFG/'gerbers/tester12v-Edge_Cuts.gm1').read_text()
points=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',outline)]
assert len(points)==8 and set(points)=={(0,0),(90,0),(0,-80),(90,-80)}
edges=[frozenset(points[i:i+2]) for i in range(0,8,2)]
assert len(set(edges))==4 and all(n==2 for n in Counter(points).values())
npth=(MFG/'gerbers/tester12v-NPTH.drl').read_text()
assert 'T1C2.700' in npth
npthpoints={(float(x),float(y)) for x,y in re.findall(r'^X([\d.-]+)Y([\d.-]+)$',npth,re.M)}
assert npthpoints=={(3,-3),(3,-77),(87,-3),(87,-77)}
pth=(MFG/'gerbers/tester12v-PTH.drl').read_text()
drill_hits=len(re.findall(r'^X[\d.-]+Y[\d.-]+$',pth,re.M))
assert drill_hits==17+audit['vias']
board=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
footprints={f.GetReference():f for f in board.GetFootprints()}
rows=list(csv.DictReader((MFG/'bom.csv').open()))
assert len(rows)==116
assert {r['Reference'] for r in rows if r['Populate']=='NO'}=={'R43','R44'}
populated={r['Reference']:r for r in rows if r['Populate']=='YES'}
assert len(populated)==114
for ref,row in populated.items():
    assert row['Value']==footprints[ref].GetValue(),ref
    assert row['Footprint']==footprints[ref].GetFPID().GetLibItemName() or row['Footprint'].split(':')[-1]==footprints[ref].GetFPID().GetLibItemName(),ref
for row in rows:
    f=footprints[row['Reference']]
    for field,column in [('MPN','MPN'),('Manufacturer','Manufacturer'),('LCSC','LCSC'),('JLC Category','JLC Category')]:
        assert f.GetFieldByName(field).GetText()==row[column],(row['Reference'],field)
        assert not f.GetFieldByName(field).IsVisible()
cpl=list(csv.DictReader((MFG/'placements-smd.csv').open()))
assert len(cpl)==110 and len({r['Ref'] for r in cpl})==110
assert {r['Ref'] for r in cpl}==set(populated)-{'J1','J2','J3','J4'}
for row in cpl:
    f=footprints[row['Ref']];pos=f.GetPosition()
    assert abs(float(row['PosX'])-p.ToMM(pos.x))<1e-6
    assert abs(float(row['PosY'])+p.ToMM(pos.y))<1e-6
    assert abs((float(row['Rot'])-f.GetOrientationDegrees()+180)%360-180)<1e-6
    assert row['Side']=='top' and row['Val']==f.GetValue()
paste=(MFG/'stencil/tester12v-F_Paste.gtp').read_text()
assert paste.rstrip().endswith('M02*')
assert '%TO.C,R43*%' not in paste and '%TO.C,R44*%' not in paste
grouped=list(csv.DictReader((MFG/'bom-grouped.csv').open()))
assert sum(int(r['Quantity']) for r in grouped if r['Populate']=='YES')==114

# Sourcing update: independently compare the JLC files to native schematic data.
jlc=list(csv.DictReader((MFG/'jlc-bom.csv').open()))
jlc_cpl=list(csv.DictReader((MFG/'jlc-cpl.csv').open()))
assert len(jlc)==24 and len(jlc_cpl)==114
jrefs=[ref for row in jlc for ref in row['Designator'].split(',')]
assert len(jrefs)==len(set(jrefs))==114 and set(jrefs)==set(populated)
assert {r['Designator'] for r in jlc_cpl}==set(jrefs)
tree=ET.parse(VAL/'schematic.net')
components={c.attrib['ref']:c for c in tree.findall('./components/comp')}
for row in jlc:
    assert re.fullmatch(r'C[0-9]+',row['LCSC Part #'])
    for ref in row['Designator'].split(','):
        fields={f.attrib['name']:f.text or '' for f in components[ref].findall('./fields/field')}
        assert fields['MPN']==row['Manufacturer Part Number']==populated[ref]['MPN']
        assert fields['LCSC']==row['LCSC Part #']==populated[ref]['LCSC']
        assert components[ref].findtext('value')==populated[ref]['Value']
for row in jlc_cpl:
    f=footprints[row['Designator']]
    if row['Designator'].startswith('J'):
        shapes=[s for s in f.GraphicalItems() if isinstance(s,p.PCB_SHAPE) and s.GetLayer()==p.F_Fab]
        pts=[pt for s in shapes for pt in (s.GetStart(),s.GetEnd())]
        x=p.ToMM(min(a.x for a in pts)+max(a.x for a in pts))/2
        y=-p.ToMM(min(a.y for a in pts)+max(a.y for a in pts))/2
    else:x,y=p.ToMM(f.GetPosition().x),-p.ToMM(f.GetPosition().y)
    assert abs(float(row['Mid X'])-x)<1e-5 and abs(float(row['Mid Y'])-y)<1e-5
    assert float(row['Rotation'])==f.GetOrientationDegrees() and row['Layer']=='Top'
def nets(t):
    return {n.attrib['name']:sorted((v.attrib['ref'],v.attrib['pin']) for v in n.findall('node')) for n in t.findall('./nets/net')}
def without_u7(t):
    return {k:[x for x in vals if x[0]!='U7'] for k,vals in nets(t).items() if any(x[0]!='U7' for x in vals)}
assert without_u7(tree)==without_u7(ET.parse(ROOT.parent/'rev-a/validation/schematic.net'))
assert json.loads((VAL/'rev-b-design-delta.json').read_text())['status']=='PASS'
assert json.loads((VAL/'rev-b-engineering.json').read_text())['status']=='PASS'
sync=json.loads((VAL/'manufacturing-sync.json').read_text())
assert sync['status']=='PASS' and sync['exporter_geometry_unchanged']
assert sync['pcb_after_sha256']==audit['board_sha256']
review=json.loads((ROOT/'sourcing/jlc-review.json').read_text())
assert review['shortage_skus']==[] and review['in_stock_skus']==24
with zipfile.ZipFile(ROOT/'sourcing/JLC-BOM-review-rev-b.xlsx') as z:
    assert z.testzip() is None
    for name in z.namelist():
        if name.startswith('xl/worksheets/') and name.endswith('.xml'):
            assert not ET.fromstring(z.read(name)).findall('.//{*}c[@t="e"]'),name
sourcing_checks={'status':'PASS','revision':'B','jlc_bom_unique_parts':24,'populated_references':114,
    'DNP_excluded':['R43','R44'],'jlc_cpl_positions_verified':114,
    'native_MPN_and_LCSC_match':True,'non_U7_connectivity_unchanged':True,
    'native_PCB_purchasing_fields_match':True,'approved_revision_deltas_checked':True,
    'manufacturing_regenerated_from_revision':'B','workbook_has_no_error_cells':True,
    'basic_skus':9,'promotional_extended_skus':1,'extended_skus':14,
    'procurement_status':'All 24 types in stock at lookup; JLC matching, attrition, placement and DFM still required',
    'limitations':'File checks do not verify JLC library rotations, vendor DFM or assembled hardware.'}
(VAL/'jlc-sourcing-checks.json').write_text(json.dumps(sourcing_checks,indent=2)+'\n')

fabzip=MFG/'tester12v-rev-b-fabrication.zip'
with zipfile.ZipFile(fabzip,'w',zipfile.ZIP_DEFLATED) as z:
    for file in fabrication+[MFG/'fabrication-notes.txt']:z.write(file,file.name)
with zipfile.ZipFile(fabzip) as z:
    assert z.testzip() is None and len(z.namelist())==10
report={'status':'PASS','board_sha256':audit['board_sha256'],
        'outline_mm':[90,80],'gerber_layers':7,'plated_drill_hits':drill_hits,
        'nonplated_2_7mm_holes':4,'bom_rows':116,'populated_components':114,
        'smd_placements_matching_native':110,'do_not_populate':['R43','R44'],
        'stencil_excludes_DNP':True,'bare_pcb_zip_entries':10,
        'bare_pcb_zip_sha256':digest(fabzip),
        'limitations':'File consistency checks only; vendor DFM and physical first article remain required.'}
(VAL/'release-checks.json').write_text(json.dumps(report,indent=2)+'\n')

# Keep the JLC handoff unambiguous: exactly one primary BOM and matching CPL.
order_files={
 'PCB-Gerbers.zip':fabzip,'BOM.csv':MFG/'jlc-bom.csv','CPL.csv':MFG/'jlc-cpl.csv',
 'ORDER-INSTRUCTIONS.txt':MFG/'ORDER-INSTRUCTIONS.txt',
 'reference/assembly.pdf':ROOT/'previews/assembly.pdf',
 'reference/schematic.pdf':ROOT/'previews/schematic.pdf',
 'reference/front-paste.gtp':MFG/'stencil/tester12v-F_Paste.gtp',
 'reference/bom-detailed.csv':MFG/'bom.csv',
 'reference/bom-grouped.csv':MFG/'bom-grouped.csv',
 'reference/manufacturing-sync.json':VAL/'manufacturing-sync.json',
 'reference/jlc-sourcing-checks.json':VAL/'jlc-sourcing-checks.json',
 'reference/release-checks.json':VAL/'release-checks.json',
 'reference/rev-b-engineering.json':VAL/'rev-b-engineering.json',
 'reference/VALIDATION.txt':VAL/'REPORT.md',
}
orderzip=ROOT.parent/'tester12v-rev-b-jlc-order.zip'
order_hashes={name:digest(file) for name,file in order_files.items()}
with zipfile.ZipFile(orderzip,'w',zipfile.ZIP_DEFLATED) as z:
    for name,file in order_files.items():z.write(file,name)
    z.writestr('SHA256SUMS.txt',''.join(order_hashes[name]+'  '+name+'\n' for name in sorted(order_hashes)))
with zipfile.ZipFile(orderzip) as z:
    assert z.testzip() is None
    for name,h in order_hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
    assert set(z.namelist())==set(order_files)|{'SHA256SUMS.txt'}
order_report={'status':'PASS','order_archive_sha256':digest(orderzip),
    'order_archive_entries':len(order_files)+1,'primary_bom':'BOM.csv','matching_cpl':'CPL.csv',
    'fabrication_archive':'PCB-Gerbers.zip','reference_count':114,
    'alternate_BOM_excluded':True,'source_file_hashes':order_hashes,
    'procurement_status':sourcing_checks['procurement_status']}
(VAL/'order-package-checks.json').write_text(json.dumps(order_report,indent=2)+'\n')

files=[ROOT/n for n in ['README.md','tester12v.kicad_pro','tester12v.kicad_pcb',
 'tester12v.kicad_sch','bank1.kicad_sch','bank2.kicad_sch','bank3.kicad_sch',
 'design-manifest.json','pin-map.csv','sym-lib-table','fp-lib-table']]
files+=list((ROOT/'libraries').rglob('*.kicad_mod'))+[ROOT/'libraries/Tester.kicad_sym']
files+=list((ROOT/'previews').glob('*'))
files+=fabrication+[fabzip,MFG/'fabrication-notes.txt',MFG/'bom.csv',MFG/'bom-grouped.csv',
 MFG/'placements-smd.csv',MFG/'stencil/tester12v-F_Paste.gtp']
files+=list((MFG/'gerbers').glob('*.pdf'))
files+=list(MFG.glob('jlc-*.csv'))+[MFG/'JLC-ORDER-NOTES.txt',MFG/'ORDER-INSTRUCTIONS.txt',orderzip]
files+=[f for f in (ROOT/'sourcing').glob('*') if f.name in ['jlc-review.json','jlc-review.csv','jlc-catalog-snapshot.json','JLC-BOM-review-rev-b.xlsx']]
files+=list((ROOT/'libraries/3d').glob('*'))
files+=[ROOT.parent/'rev-a/tester12v.kicad_pcb',ROOT.parent/'rev-a/design-manifest.json',ROOT.parent/'rev-a/validation/schematic.net']
files+=[VAL/'jlc-sourcing-checks.json']
files+=[VAL/n for n in ['manufacturing-sync.json','manufacturing-export.log',
 'rev-b-design-delta.json','rev-b-engineering.json','order-package-checks.json']]
files+=[VAL/n for n in ['REPORT.md','erc.json','drc-final.json','board-audit.json',
 'circuit-results.json','all-pin-pairs.csv','bench-pairs.csv','spice-results.json',
 'startup-shutdown.csv','schematic.net','firmware-tests.log','firmware-build.log','release-checks.json']]
files+=list(VAL.glob('spice-*.cir'))
files+=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'scripts').glob('*.cpp'))
files+=[f for f in (ROOT/'sources').glob('*') if not f.name.startswith('MCP6001')]
fw=WORKSPACE/'firmware/Tester12V'
files+=[f for f in fw.glob('*') if f.is_file()]+list((fw/'build').rglob('*.bin'))
files=sorted(set(files));assert all(f.is_file() and f.stat().st_size>0 for f in files)
hashfile=ROOT/'SHA256SUMS.txt'
hashfile.write_text(''.join(digest(f)+'  '+str(f.relative_to(WORKSPACE))+'\n' for f in files))
files.append(hashfile)
fullzip=ROOT.parent/'tester12v-rev-b-complete.zip'
with zipfile.ZipFile(fullzip,'w',zipfile.ZIP_DEFLATED) as z:
    for file in files:z.write(file,'tester12v-rev-b/'+str(file.relative_to(WORKSPACE)))
    z.writestr('tester12v-rev-b/START-HERE.txt',
      'Read hardware/rev-b/README.md and hardware/rev-b/validation/REPORT.md first.\n'
      'The bare PCB upload ZIP is in hardware/rev-b/manufacturing/.\n'
      'Use hardware/tester12v-rev-b-jlc-order.zip for the concise JLC handoff.\n'
      'Read its ORDER-INSTRUCTIONS.txt; JLC placement and DFM review remain.\n'
      'Editable KiCad design and matching firmware are included.\n'
      'This is an unbuilt prototype; completed checks are computer checks only.\n'
      'hardware/rev-b/SHA256SUMS.txt uses paths relative to this package root.\n')
with zipfile.ZipFile(fullzip) as z:assert z.testzip() is None
print(json.dumps(report,indent=2))
print(f'Complete package: {len(files)+1} files, {fullzip.stat().st_size} bytes')
print(f'Complete package SHA256: {digest(fullzip)}')
print(f'JLC order package: {orderzip}, {orderzip.stat().st_size} bytes, SHA256 {digest(orderzip)}')
