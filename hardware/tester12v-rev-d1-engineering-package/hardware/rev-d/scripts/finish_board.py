"""Import the saved autorouter result and add isolated copper pours."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
def mm(x):return p.FromMM(x)
def v(x,y):return p.VECTOR2I(mm(x),mm(y))
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
# SES contains the complete routed result, including fixed fanout.
for t in list(b.GetTracks()):b.Delete(t)
for z in list(b.Zones()):
    if not z.GetIsRuleArea():b.Delete(z)
assert p.ImportSpecctraSES(b,str(ROOT/'tester12v-routed.ses'))
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetText()=='12 V NOMINAL / SENSE ONLY':t.SetPosition(v(50,2))
for layer in [p.F_Cu,p.B_Cu]:
    for net,x1,x2 in [('USB_GND',.5,16.4),('AGND',17.6,85.5)]:
        z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(net));z.SetZoneName(net+'_PLANE');z.SetLocalClearance(mm(.25));z.SetThermalReliefGap(mm(.25));z.SetThermalReliefSpokeWidth(mm(.3));z.SetMinThickness(mm(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
        poly=z.Outline();poly.NewOutline()
        for x,y in [(x1,.5),(x2,.5),(x2,61.5),(x1,61.5)]:poly.Append(mm(x),mm(y))
        b.Add(z)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
print('Routed board saved:',len(list(b.GetTracks())),'track/via objects')
