"""Apply D2 J4 silkscreen and black/white finish without electrical edits."""
import hashlib,inspect,json,subprocess,sys
import pcbnew as p
from design import ROOT,REVISION
from build_kicad import harness_silkscreen,black_white_stackup

path=ROOT/'tester12v.kicad_pcb';b=p.LoadBoard(str(path))
before=hashlib.sha256(path.read_bytes()).hexdigest()
def electrical(board):
    pads=sorted((f.GetReference(),z.GetNumber(),z.GetNetname(),z.GetPosition().x,z.GetPosition().y) for f in board.GetFootprints() for z in f.Pads())
    tracks=sorted((t.GetNetname(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetLayer(),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()) for t in board.GetTracks())
    return pads,tracks
original=electrical(b)
labels={'ESP32','5 SCL7','4 SDA6','3 3V3','2 GND','1 5V',
 'J4: 5V / GND / 3V3 / SDA6 / SCL7','J4: 1=5V/VSYS  2=GND  3=3V3',
 '4=SDA/GPIO6  5=SCL/GPIO7','5V FROM ESP32 USB - NO 12V'}
for item in list(b.GetDrawings()):
    if isinstance(item,p.PCB_TEXT):
        if item.GetText() in labels:b.Remove(item)
        elif item.GetText().startswith('REV D'):item.SetText('REV '+REVISION)
harness_silkscreen(b)
p.SaveBoard(str(path),b);black_white_stackup(path)
# Reload in a fresh process: macOS pcbnew's wrapper can lose type information
# after font initialization. Compare every saved pad and route before normalizing.
fingerprint=hashlib.sha256(json.dumps(original).encode()).hexdigest()
check='import sys,json,hashlib,pcbnew as p\n'+inspect.getsource(electrical)+'\nb=p.LoadBoard(sys.argv[1])\nassert hashlib.sha256(json.dumps(electrical(b)).encode()).hexdigest()==sys.argv[2]\nassert b.GetDesignSettings().m_HasStackup\np.SaveBoard(sys.argv[1],b)\n'
subprocess.run([sys.executable,'-c',check,str(path),fingerprint],check=True)
assert path.read_text().count('(color "Black")')==2
assert path.read_text().count('(color "White")')==2
report=dict(status='PASS',revision=REVISION,all_pads_nets_and_routes_unchanged=True,
 solder_mask='Black, both sides',silkscreen='White, both sides',
 j4_top_to_bottom=['5 SCL7','4 SDA6','3 3V3','2 GND','1 5V'],
 previous_board_sha256=before)
dest=ROOT/'validation/harness-labels.json'
if not dest.exists():dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
