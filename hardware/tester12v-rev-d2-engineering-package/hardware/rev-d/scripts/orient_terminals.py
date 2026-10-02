"""Apply the D-to-D1 mechanical change while preserving all routed input paths.

Idempotent; does not rebuild or reroute the board. All numbered inputs retain
their physical holes, net names and ADC channels. Only connector contact numbers
reverse, with pin-one origin moving to the right end of each terminal block.
"""
import hashlib,json,re
import pcbnew as p
from design import ROOT,PARTS,REVISION
from build_kicad import terminal_graphics,make_terminal,vec

path=ROOT/'tester12v.kicad_pcb';b=p.LoadBoard(str(path))
fps={f.GetReference():f for f in b.GetFootprints()}
def pads():
    return sorted((f.GetReference(),pad.GetNetname(),pad.GetPosition().x,pad.GetPosition().y)
                  for f in b.GetFootprints() for pad in f.Pads())
def tracks():
    return sorted((t.GetNetname(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetLayer(),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()) for t in b.GetTracks())
before_pads=pads();before_tracks=tracks();before_hash=hashlib.sha256(path.read_bytes()).hexdigest()
make_terminal()
for part in PARTS:
    if part['ref'] not in ('J1','J2','J3'):continue
    f=fps[part['ref']];cx=32+20*(int(part['ref'][1])-1)
    assert f.GetOrientationDegrees()%360 in (0,180)
    assert abs(p.ToMM(f.GetPosition().y)-52)<1e-6
    assert abs(p.ToMM(f.GetPosition().x)-(cx+(5.25 if f.GetOrientationDegrees()%360==180 else -5.25)))<1e-6
    f.SetOrientationDegrees(0);f.SetPosition(vec(0,0))
    for g in list(f.GraphicalItems()):
        if isinstance(g,p.PCB_SHAPE):f.Remove(g)
    terminal_graphics(f)
    f.SetPosition(vec(*part['pcb'][:2]));f.SetOrientationDegrees(part['pcb'][2])
    for pad in f.Pads():pad.SetNet(b.FindNet(part['pins'][pad.GetNumber()]))
    f.Reference().SetPosition(vec(cx,47));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetText() in ('REV D','REV D1'):t.SetText('REV '+REVISION)
assert before_pads==pads(),'Physical input locations/nets changed'
assert before_tracks==tracks(),'Routed copper changed'
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
assert p.ExportSpecctraDSN(b,str(ROOT/'tester12v.dsn'))
# SES routes are keyed by net, so their copper remains valid. Keep its component
# placements consistent so finish_board.py cannot rotate the blocks back inward.
ses=ROOT/'tester12v-routed.ses';s=ses.read_text()
for bank in range(1,4):
    x=round((32+20*(bank-1)+5.25)*10000)
    s,n=re.subn(r'\(place J'+str(bank)+r' \d+ -520000 front (?:0|180)\)',f'(place J{bank} {x} -520000 front 180)',s)
    assert n==1
ses.write_text(s)
report=dict(revision=REVISION,status='PASS',input_pad_locations_and_nets_preserved=True,
 routed_tracks_preserved=True,terminal_rotation_degrees=180,wire_entry_direction='board +Y toward lower edge at Y=62 mm',
 input_labels='1 through 12 remain left-to-right; physical connector contacts 4,3,2,1 within each block',
 previous_board_sha256=before_hash)
dest=ROOT/'validation/terminal-orientation.json'
if not dest.exists():dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
