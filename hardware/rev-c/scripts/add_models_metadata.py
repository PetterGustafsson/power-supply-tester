"""Add dimensioned visual envelopes and purchasing metadata; preserve copper."""
from pathlib import Path
import pcbnew as p
from design import ROOT,PARTS,SYMS
folder=ROOT/'libraries/3d';folder.mkdir(exist_ok=True)
def box(center,size,color):
    # KiCad VRML length unit is 0.1 inch; convert dimensions from mm.
    return 'Transform { translation %s children [ Shape { appearance Appearance { material Material { diffuseColor %s } } geometry Box { size %s } } ] }\n'%(' '.join(str(x/2.54) for x in center),' '.join(map(str,color)),' '.join(str(x/2.54) for x in size))
power='#VRML V2.0 utf8\n# EVISUN dimensional envelope, not a vendor detailed model.\n'
power+=box((3.81,2.1,5.1),(11.68,6,10.2),(.08,.08,.08))
for i in range(4):power+=box((i*2.54,0,-1.75),(.5,.3,3.5),(.7,.7,.7))
(folder/'B0305S_envelope.wrl').write_text(power)
term='#VRML V2.0 utf8\n# XY350V dimensional envelope; screw blocks are illustrative.\n'
term+=box((5.25,0,4.3),(14,6.9,8.6),(.04,.35,.12))
for i in range(4):
    term+=box((i*3.5,0,-1.75),(.8,.8,3.5),(.7,.7,.7))
    term+=box((i*3.5,0,8.6),(2,2,.2),(.65,.65,.65))
(folder/'XY350V_envelope.wrl').write_text(term)
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'));parts={q['ref']:q for q in PARTS}
for f in b.GetFootprints():
    ref=f.GetReference()
    if ref.startswith('H'):f.SetBoardOnly(True);continue
    q=parts[ref]
    for pad in f.Pads():
        n=pad.GetNumber()
        if n in q['pins'] and q['pins'][n] is None:
            name=next(z['name'] for z in SYMS[q['sym']]['pins'] if z['n']==n)
            netname=f'unconnected-({ref}-{name}-Pad{n})'
            net=b.FindNet(netname)
            if not net:net=p.NETINFO_ITEM(b,netname);b.Add(net)
            pad.SetNet(net)
    if ref.startswith('TP'):f.SetExcludedFromBOM(True);continue
    for key,value in [('MPN',q['mpn']),('Manufacturer',q['maker']),('LCSC',q.get('lcsc','')),('JLC Category',q.get('jlc_category',''))]:
        field=f.GetFieldByName(key)
        if not field:field=p.PCB_FIELD(f,f.GetNextFieldId(),key);f.Add(field)
        field.SetText(value);field.SetVisible(False)
    model=None
    if ref=='U7':model='B0305S_envelope.wrl'
    if ref in ('J1','J2','J3'):model='XY350V_envelope.wrl'
    if model:
        f.Models().clear();m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/libraries/3d/'+model;f.Add3DModel(m)
p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
print('Metadata and dimensioned component envelopes updated; copper preserved.')
