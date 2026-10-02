"""Readable native KiCad assembly PDF; changes are only to the plot copy."""
import pcbnew as p
from design import ROOT
from build_kicad import vec,board_text
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
for f in b.GetFootprints():
 for g in list(f.GraphicalItems()):
  if isinstance(g,p.PCB_TEXT):g.SetLayer(p.User_9)
 if f.GetReference().startswith('TP'):f.Reference().SetLayer(p.User_9)
 # These labels sit close to switch outlines / harness pads in the native
 # layout. Move only the plot-copy references for a legible assembly sheet.
 ref=f.GetReference()
 if ref.startswith('R') and ref[1:].isdigit() and 46<=int(ref[1:])<=57:
  pos=f.GetPosition();f.Reference().SetPosition(vec(p.ToMM(pos.x),48.65))
 if ref=='J4':f.Reference().SetPosition(vec(6.525,41.5))
board_text(b,'REV A ASSEMBLY - NOT TO SCALE',45,85,1.2,p.F_Fab)
board_text(b,'Board 90 x 80 mm | R43/R44 DNP | Test points A1-A12 = TP1-TP12',45,88,1,p.F_Fab)
c=p.PLOT_CONTROLLER(b);o=c.GetPlotOptions();o.SetOutputDirectory(str(ROOT/'previews'));o.SetAutoScale(True);o.SetScale(1);o.SetPlotFrameRef(False);o.SetPlotValue(False);o.SetPlotReference(True);o.SetSketchPadsOnFabLayers(True);o.SetPlotPadNumbers(True)
c.SetLayer(p.F_Fab);c.OpenPlotfile('assembly',p.PLOT_FORMAT_PDF,'Rev A assembly');c.GetPlotter().SetColorMode(False)
for layer in [p.F_Fab,p.F_SilkS,p.Edge_Cuts]:c.SetLayer(layer);c.PlotLayer()
c.ClosePlot();generated=ROOT/'previews'/'tester12v-assembly.pdf';generated.replace(ROOT/'previews'/'assembly.pdf')
