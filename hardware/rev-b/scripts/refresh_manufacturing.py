"""Synchronize Rev B purchasing fields and regenerate its manufacturing exports.

Run using KiCad's bundled Python. This deliberately never calls make_board,
changes component values, fills zones, moves footprints or reroutes copper.
"""
import hashlib,json,re,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
import pcbnew as pcb
from design import ROOT,PARTS

CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
M=ROOT/'manufacturing';V=ROOT/'validation'
SOURCE=ROOT/'tester12v.kicad_pcb'
FIELDS={'MPN','Manufacturer','LCSC','JLC Category'}
def digest(b):return hashlib.sha256(b).hexdigest()
def physical_tree(raw):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',raw.decode())
    stack=[];root=None
    for token in tokens:
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            else:root=node
            stack.append(node)
        elif token==')':stack.pop()
        else:stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack
    for item in root:
        if isinstance(item,list) and item and item[0]=='footprint':
            item[:]=[x for x in item if not (isinstance(x,list) and len(x)>1 and x[0]=='property' and x[1] in FIELDS)]
    return root
def normalized_plot(raw):
    # Strip only timestamp headers/comments; all drawing commands remain compared.
    return '\n'.join(line for line in raw.decode().splitlines() if
        not line.startswith(('%TF.CreationDate,','G04 Created by KiCad','; DRILL file','; #@! TF.CreationDate,')))

before=SOURCE.read_bytes()
b=pcb.LoadBoard(str(SOURCE));parts={p['ref']:p for p in PARTS}
updated=0
for f in b.GetFootprints():
    p=parts.get(f.GetReference())
    if not p or not p['mpn']:continue
    for name,value in [('MPN',p['mpn']),('Manufacturer',p['maker']),('LCSC',p['lcsc']),('JLC Category',p['jlc_category'])]:
        field=f.GetFieldByName(name)
        if not field:
            field=pcb.PCB_FIELD(f,f.GetNextFieldId(),name)
            field.SetPosition(f.GetPosition());field.SetLayer(pcb.F_Fab)
            field.SetVisible(False);field.SetText(value)
            f.AddField(field)
        else:
            field.SetText(value);field.SetVisible(False)
    updated+=1
with tempfile.TemporaryDirectory(prefix='tester12v-manufacturing-') as tmp:
    candidate=Path(tmp)/SOURCE.name
    pcb.SaveBoard(str(candidate),b)
    after=candidate.read_bytes()
    assert physical_tree(before)==physical_tree(after),'PCB changed beyond purchasing fields'
    SOURCE.write_bytes(after)

log=[]
def run(args):
    r=subprocess.run([str(a) for a in args],capture_output=True,text=True)
    log.append('$ '+' '.join(str(a) for a in args)+'\n'+r.stdout+r.stderr)
    if r.returncode:
        (V/'manufacturing-export.log').write_text('\n'.join(log))
        raise RuntimeError('Export failed: '+' '.join(str(a) for a in args))
run([sys.executable,ROOT/'scripts/export_jlc.py'])
run([CLI,'pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','--output',M/'gerbers',SOURCE])
run([CLI,'pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-map','--map-format','pdf','--output',M/'gerbers',SOURCE])
run([CLI,'pcb','export','pos','--format','csv','--units','mm','--smd-only','--exclude-dnp','--output',M/'placements-smd.csv',SOURCE])
run([sys.executable,ROOT/'scripts/plot_stencil.py'])
run([sys.executable,ROOT/'scripts/plot_assembly.py'])
run([CLI,'sch','export','pdf','--output',ROOT/'previews/schematic.pdf',ROOT/'tester12v.kicad_sch'])
run([CLI,'sch','erc','--format','json','--output',V/'erc.json',ROOT/'tester12v.kicad_sch'])
run([CLI,'sch','export','netlist','--format','kicadxml','--output',V/'schematic.net',ROOT/'tester12v.kicad_sch'])
run([CLI,'pcb','drc','--schematic-parity','--format','json','--output',V/'drc-final.json',SOURCE])
run([sys.executable,ROOT/'scripts/audit_board.py'])
(M/'stencil/tester12v-job.gbrjob').unlink(missing_ok=True)
assert digest(SOURCE.read_bytes())==digest(after),'Exporter modified PCB'
report=dict(status='PASS',revision='B',purchasing_metadata_footprints=updated,
    pcb_run_input_sha256=digest(before),pcb_after_sha256=digest(after),
    exporter_geometry_unchanged=True,
    meaning='Rev B circuit/layout changes checked separately against Rev A; manufacturing files freshly regenerated from Rev B.')
(V/'manufacturing-sync.json').write_text(json.dumps(report,indent=2)+'\n')
(V/'manufacturing-export.log').write_text('\n'.join(log))
print(json.dumps(report,indent=2))
