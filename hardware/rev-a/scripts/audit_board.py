"""Check exported schematic connectivity against physical PCB pads and scope."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
t=ET.parse(ROOT/'validation/schematic.net');expected={}
for net in t.findall('./nets/net'):
    for node in net.findall('node'):
        if not node.attrib['ref'].startswith('#'):
            expected[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
actual={(f.GetReference(),pad.GetNumber()):pad.GetNetname()
        for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber()}
assert actual==expected,dict(missing=set(expected)-set(actual),extra=set(actual)-set(expected),
                            mismatches=[(k,expected[k],actual.get(k)) for k in expected if actual.get(k)!=expected[k]])
primary={'USB_GND','USB5V','USB5V_F','HOST3V3','SDA_HOST','SCL_HOST'}
bridges=[]
for f in b.GetFootprints():
    nets={z.GetNetname() for z in f.Pads() if z.GetNetname() and not z.GetNetname().startswith('unconnected-')}
    if nets&primary and nets-primary:bridges.append(f.GetReference())
assert sorted(bridges)==['U7','U8'],bridges
for n in range(1,13):
    connected={key for key,value in actual.items() if value==f'P{n}'}
    assert connected=={(f'J{(n-1)//4+1}',str((n-1)%4+1)),(f'R{3*n-2}','1')},connected
    assert actual[f'R{3*n-2}','2']==actual[f'R{3*n-1}','1']==f'MID{n}'
    assert actual[f'R{45+n}','1']==actual[f'R{3*n-1}','2']==f'S{n}'
    assert actual[f'R{45+n}','2']=='AGND'
    assert actual[f'R{3*n}','1']==actual[f'U{(n-1)//4+1}',str((n-1)%4+4)]==f'A{n}'
assert [actual[f'U{i}','1'] for i in (1,2,3)]==['AGND','A3V3','SDA_ISO']
assert b.GetCopperLayerCount()==2
assert abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-1.6)<1e-6
tracks=[z for z in b.GetTracks() if not isinstance(z,p.PCB_VIA)]
vias=[z for z in b.GetTracks() if isinstance(z,p.PCB_VIA)]
assert min(p.ToMM(z.GetWidth()) for z in tracks)>=.1999
assert min(p.ToMM(z.GetDrillValue()) for z in vias)>=.2999
assert all(p.ToMM(z.GetWidth(p.F_Cu))>=.5999 for z in vias)
erc=json.loads((ROOT/'validation/erc.json').read_text());drc=json.loads((ROOT/'validation/drc-final.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
assert all(not s['violations'] for s in erc['sheets'])
report={'status':'PASS','physical_pad_nets_compared':len(actual),
        'raw_input_paths_checked':12,'only_isolation_boundary_components':sorted(bridges),
        'layers':2,'thickness_mm':1.6,'tracks':len(tracks),'vias':len(vias),
        'minimum_track_width_mm':min(p.ToMM(z.GetWidth()) for z in tracks),
        'board_sha256':hashlib.sha256((ROOT/'tester12v.kicad_pcb').read_bytes()).hexdigest(),
        'schematic_netlist_sha256':hashlib.sha256((ROOT/'validation/schematic.net').read_bytes()).hexdigest()}
(ROOT/'validation/board-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
