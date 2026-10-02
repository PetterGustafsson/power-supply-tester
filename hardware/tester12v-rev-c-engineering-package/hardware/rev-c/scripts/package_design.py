"""Verify and archive a reviewable engineering package, not an approved order."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re,zipfile
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
M=ROOT/'manufacturing';V=ROOT/'validation';FW=WORKSPACE/'firmware/Tester12VRevC'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return list(csv.DictReader(path.open()))
audit=json.loads((V/'board-audit.json').read_text())
assert audit['status']=='PASS' and digest(ROOT/'tester12v.kicad_pcb')==audit['board_sha256']
assert digest(V/'schematic.net')==audit['schematic_netlist_sha256']
drc=json.loads((V/'drc-final.json').read_text());erc=json.loads((V/'erc.json').read_text())
assert not any(drc[k] for k in ('violations','unconnected_items','schematic_parity'))
assert all(not s['violations'] for s in erc['sheets'])
assert json.loads((V/'passive-front-end.json').read_text())['status']=='PASS_CALCULATION_ONLY'
transient=json.loads((V/'transient-results.json').read_text())
assert len(transient['cases'])==48 and transient['normal_slew_all_pass']
assert (V/'firmware-tests.log').read_text().startswith('PASS: 3564')
build=json.loads((FW/'build-evidence.json').read_text());assert build['compile_exit_code']==0
for name,sha in build['source_sha256'].items():assert digest(FW/name)==sha,name
for name,sha in build['binary_sha256'].items():assert digest(FW/'build'/name)==sha,name
suffixes=['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs','F_Silkscreen.gto','B_Silkscreen.gbo','Edge_Cuts.gm1','PTH.drl','NPTH.drl']
fabrication=[M/'gerbers'/('tester12v-'+s) for s in suffixes]
for f in fabrication:
    data=f.read_text();assert len(data)>100 and data.rstrip().endswith('M30' if f.suffix=='.drl' else 'M02*')
outline=(M/'gerbers/tester12v-Edge_Cuts.gm1').read_text()
points=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',outline)]
assert len(points)==8 and set(points)=={(0,0),(86,0),(0,-62),(86,-62)}
assert all(n==2 for n in Counter(points).values())
npth=(M/'gerbers/tester12v-NPTH.drl').read_text()
assert 'T1C2.700' in npth
assert {(float(x),float(y)) for x,y in re.findall(r'^X([\d.-]+)Y([\d.-]+)$',npth,re.M)}=={(3,-3),(3,-59),(83,-3),(83,-59)}
pth=(M/'gerbers/tester12v-PTH.drl').read_text()
assert len(re.findall(r'^X[\d.-]+Y[\d.-]+$',pth,re.M))==21+audit['vias']
board=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()}
bom=rows(M/'bom.csv');assert len(bom)==87
assert {r['Reference'] for r in bom if r['Populate']=='NO'}=={'R46','R47'}
pop={r['Reference']:r for r in bom if r['Populate']=='YES'};assert len(pop)==85
for row in bom:
    f=fps[row['Reference']];assert row['Value']==f.GetValue()
    for field,column in [('MPN','MPN'),('Manufacturer','Manufacturer'),('LCSC','LCSC'),('JLC Category','JLC Category')]:
        q=f.GetFieldByName(field);assert q and q.GetText()==row[column] and not q.IsVisible(),(row['Reference'],field)
jlc=rows(M/'jlc-bom.csv');cpl=rows(M/'jlc-cpl-native-angles.csv')
jrefs=[r for row in jlc for r in row['Designator'].split(',')]
assert len(jlc)==15 and len(jrefs)==len(set(jrefs))==len(cpl)==85
assert set(jrefs)==set(pop)=={r['Designator'] for r in cpl}
for row in jlc:
    for ref in row['Designator'].split(','):
        assert row['LCSC Part #']==pop[ref]['LCSC'] and row['Manufacturer Part Number']==pop[ref]['MPN']
assert len(rows(M/'placements-smd.csv'))==80
paste=(M/'stencil/tester12v-F_Paste.gtp').read_text()
assert paste.rstrip().endswith('M02*') and '%TO.C,R46*%' not in paste and '%TO.C,R47*%' not in paste
with zipfile.ZipFile(M/'tester12v-rev-c-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in fabrication:z.write(f,f.name)
report=dict(status='PASS_ENGINEERING_PACKAGE_CHECKS',revision='C',board_sha256=audit['board_sha256'],
 fitted_components=85,bom_skus=15,basic_components=72,gerber_outline_mm=[86,62],
 physical_validation=False,jlc_placement_review=False,jlc_checkout_created=False,
 abnormal_forced_rail_collapse_failures=sum(not x['within_absolute_voltage_limits'] for x in transient['cases']),
 note='Normal-slew model passed; forced 1/10us rail-short cases exceed ADC absolute voltage window. Read REPORT.md. Package is not approval to place an order.')
(V/'package-checks.json').write_text(json.dumps(report,indent=2)+'\n')
files=[f for f in ROOT.rglob('*') if f.is_file() and not any(x in f.parts for x in ('__pycache__',)) and f.suffix not in ('.pyc','.lck','.bak') and f.name not in ('SHA256SUMS.txt','.DS_Store')]
files += [f for f in FW.rglob('*') if f.is_file() and f.suffix not in ('.elf','.map') and f.name!='.DS_Store']
manifest=''.join(digest(f)+'  '+str(f.relative_to(WORKSPACE))+'\n' for f in sorted(files))
(ROOT/'SHA256SUMS.txt').write_text(manifest)
package=ROOT.parent/'tester12v-rev-c-engineering-package.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files+[ROOT/'SHA256SUMS.txt']:z.write(f,str(f.relative_to(WORKSPACE)))
    z.writestr('START-HERE.txt','Read hardware/rev-c/README.md and validation/REPORT.md.\nOne USB cable to the Waveshare module powers the tester.\nEngineering prototype only: JLC placement/DFM and physical tests remain.\nUse Rev C BOM/Gerbers/CPL together. Do not use old Rev B firmware.\nNative CPL angles require JLC viewer review. No order has been placed.\n')
with zipfile.ZipFile(package) as z:assert z.testzip() is None
print(json.dumps(report,indent=2));print(str(package));print('SHA256 '+digest(package))
