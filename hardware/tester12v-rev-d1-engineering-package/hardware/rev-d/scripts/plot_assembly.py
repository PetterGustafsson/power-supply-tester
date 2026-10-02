"""Native KiCad assembly drawing from a plot-only board copy."""
import pcbnew as p
from design import ROOT,REVISION
from build_kicad import vec,board_text
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
for f in b.GetFootprints():
    for g in list(f.GraphicalItems()):
        if isinstance(g,p.PCB_TEXT):g.SetLayer(p.User_9)
    if f.GetReference().startswith('TP'):f.Reference().SetLayer(p.User_9)
    f.Reference().SetTextSize(vec(.75,.75));f.Reference().SetTextThickness(p.FromMM(.1))
    label_positions={'U4':(8,7.3),'C16':(2,7.3),'D1':(8,12.5),'C17':(2,12.5),'C25':(21.8,28),'J4':(3.5,32.5)}
    if f.GetReference() in label_positions:f.Reference().SetPosition(vec(*label_positions[f.GetReference()]))
    f.Value().SetVisible(False)
board_text(b,'REV '+REVISION+' ASSEMBLY - BOARD 86 x 62 mm',43,66,1.1,p.F_Fab)
board_text(b,'R46/R47 DNP | U7 pin 1 = USB_GND | D1 pad 1 = cathode',43,69,.9,p.F_Fab)
board_text(b,'Pin 1 coordinates: manufacturing/pin1-review.csv',43,72,.9,p.F_Fab)
board_text(b,'J1/J2/J3: WIRE OPENINGS TOWARD LOWER EDGE; SCREWS UP',43,75,.9,p.F_Fab)
board_text(b,'Inputs 1-12 left-to-right; connector contacts 4,3,2,1 per block',43,78,.9,p.F_Fab)
c=p.PLOT_CONTROLLER(b);o=c.GetPlotOptions();o.SetOutputDirectory(str(ROOT/'previews'));o.SetAutoScale(True);o.SetScale(1);o.SetPlotFrameRef(False);o.SetPlotValue(False);o.SetPlotReference(True);o.SetSketchPadsOnFabLayers(True);o.SetPlotPadNumbers(True)
c.SetLayer(p.F_Fab);c.OpenPlotfile('assembly',p.PLOT_FORMAT_PDF,'Rev '+REVISION+' assembly');c.GetPlotter().SetColorMode(False)
for layer in [p.F_Fab,p.F_SilkS,p.Edge_Cuts]:c.SetLayer(layer);c.PlotLayer()
c.ClosePlot();(ROOT/'previews/tester12v-assembly.pdf').replace(ROOT/'previews/assembly.pdf')
