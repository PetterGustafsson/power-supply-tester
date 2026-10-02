"""Independently compare exported schematic, routed pads and model assumptions."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
t=ET.parse(ROOT/'validation/schematic.net');expected={}
components={c.attrib['ref']:c for c in t.findall('./components/comp')}
values={ref:c.findtext('value') for ref,c in components.items()}
for net in t.findall('./nets/net'):
    for node in net.findall('node'):
        if not node.attrib['ref'].startswith('#'):
            expected[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
actual={(f.GetReference(),pad.GetNumber()):pad.GetNetname()
        for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber()}
assert actual==expected,[(k,expected.get(k),actual.get(k)) for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k)]
primary={'USB_GND','USB5V','USB5V_F','HOST3V3','P3V3','SDA_HOST','SCL_HOST'}
bridges=[]
for f in b.GetFootprints():
    nets={z.GetNetname() for z in f.Pads() if z.GetNetname() and not z.GetNetname().startswith('unconnected-')}
    if nets&primary and nets-primary:bridges.append(f.GetReference())
assert sorted(bridges)==['U6','U7'],bridges
for n in range(1,13):
    a,c,d=f'R{3*n-2}',f'R{3*n-1}',f'R{3*n}'
    ref=f'J{(n-1)//4+1}';contact=str(4-(n-1)%4)
    assert {key for key,value in actual.items() if value==f'P{n}'}=={(ref,contact),(a,'1')}
    f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
    pad=next(z for z in f.Pads() if z.GetNumber()==contact)
    # Independent spatial check: user labels and existing ADC paths stay 1..12
    # left-to-right despite the reversed physical contact numbering in D1.
    assert f.GetOrientationDegrees()%360==180
    assert abs(p.ToMM(pad.GetPosition().x)-(26.75+20*((n-1)//4)+3.5*((n-1)%4)))<1e-6
    assert abs(p.ToMM(pad.GetPosition().y)-52)<1e-6
    assert actual[a,'2']==actual[c,'1']==f'MID{n}'
    assert actual[c,'2']==actual[d,'1']==actual[f'U{(n-1)//4+1}',str((n-1)%4+4)]==f'A{n}'
    assert actual[d,'2']=='VBIAS'
    assert actual[f'C{n}','1']==f'A{n}' and actual[f'C{n}','2']=='AGND'
    assert values[a]==values[c]=='1M' and values[d]=='4.7k' and values[f'C{n}']=='470p'
assert (values['R37'],values['R38'],values['C26'])==('4.7k','1k','470p')
assert [actual['R37',str(i)] for i in (1,2)]==['A3V3','VBIAS']
assert [actual['R38',str(i)] for i in (1,2)]==['VBIAS','AGND']
for r in range(39,44):
    assert values[f'R{r}']=='1k' and [actual[f'R{r}',str(i)] for i in (1,2)]==['ISO5V_RAW','AGND']
assert [actual[f'U{i}','1'] for i in (1,2,3)]==['AGND','A3V3','SDA_ISO']
assert actual['U8','1']=='SCL_ISO' and actual['U8','4']=='REF_ADC'
assert all(actual['U8',str(i)]=='AGND' for i in (3,5,6,7))
assert [actual['R49',str(i)] for i in (1,2)]==['VBIAS','REF_ADC'] and values['R49']=='4.7k'
assert [actual['C28',str(i)] for i in (1,2)]==['REF_ADC','AGND'] and values['C28']=='470p'
assert [actual['C27',str(i)] for i in (1,2)]==['A3V3','AGND'] and values['C27']=='100n'
assert actual['U8','8']=='A3V3' and actual['U8','9']=='SDA_ISO' and actual['U8','10']=='SCL_ISO'
assert [actual['U7',str(i)] for i in (1,2,3,4)]==['USB_GND','P3V3','AGND','ISO5V_RAW']
assert actual['U5','3'].startswith('unconnected-') # TI TPS709 EN must not be tied to raw VIN.
assert [actual['D1',str(i)] for i in (1,2)]==['USB5V_F','P3V3']
assert [actual['J4',str(i)] for i in range(1,6)]==['USB5V','USB_GND','HOST3V3','SDA_HOST','SCL_HOST']
assert {f.GetReference() for f in b.GetFootprints() if f.IsDNP()}=={'R46','R47'}
assert b.GetCopperLayerCount()==2 and abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-1.6)<1e-6
tracks=[z for z in b.GetTracks() if not isinstance(z,p.PCB_VIA)]
vias=[z for z in b.GetTracks() if isinstance(z,p.PCB_VIA)]
assert min(p.ToMM(z.GetWidth()) for z in tracks)>=.1999
assert min(p.ToMM(z.GetDrillValue()) for z in vias)>=.2999
assert all(p.ToMM(z.GetWidth(p.F_Cu))>=.5999 for z in vias)
erc=json.loads((ROOT/'validation/erc.json').read_text());drc=json.loads((ROOT/'validation/drc-final.json').read_text())
assert not any(drc[k] for k in ('violations','unconnected_items','schematic_parity'))
assert all(not s['violations'] for s in erc['sheets'])
report={'status':'PASS','physical_pad_nets_compared':len(actual),'passive_model_topology_matches_exported_netlist':True,
 'outward_terminals_and_left_to_right_inputs_checked':True,
 'raw_input_paths_checked':12,'only_isolation_boundary_components':sorted(bridges),
 'layers':2,'thickness_mm':1.6,'tracks':len(tracks),'vias':len(vias),'minimum_track_width_mm':min(p.ToMM(z.GetWidth()) for z in tracks),
 'board_sha256':hashlib.sha256((ROOT/'tester12v.kicad_pcb').read_bytes()).hexdigest(),
 'schematic_netlist_sha256':hashlib.sha256((ROOT/'validation/schematic.net').read_bytes()).hexdigest()}
(ROOT/'validation/board-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
