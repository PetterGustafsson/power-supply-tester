"""Regenerate schematic/BOM, synchronize board values and explicit no-connect nets.
Does not change placement or copper routing.
"""
from pathlib import Path
import pcbnew as p
import build_kicad as g
from design import PARTS,SYMS,ROOT
# Footprint copies stay unchanged: preserve the original placed/library identifiers.
g.copy_libraries();g.schematic('root','12 V universal pin-voltage tester - power and controller')
for k in range(3):g.schematic('bank'+str(k+1),f'Inputs {k*4+1}-{k*4+4}: protected sensing and ADC')
g.outputs()
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'));parts={c['ref']:c for c in PARTS}
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref.startswith('H'):f.SetBoardOnly(True);continue
 c=parts[ref];f.SetValue(c['value'])
 if ref.startswith('TP'):f.SetExcludedFromBOM(True)
 for pad in f.Pads():
  n=pad.GetNumber()
  if n in c['pins'] and c['pins'][n] is None:
   name=next(q['name'] for q in SYMS[c['sym']]['pins'] if q['n']==n)
   netname=f'unconnected-({ref}-{name}-Pad{n})'
   net=b.FindNet(netname)
   if not net:net=p.NETINFO_ITEM(b,netname);b.Add(net)
   pad.SetNet(net)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
