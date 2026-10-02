"""Plot populated-pad paste from an in-memory copy; preserve the native PCB."""
import pcbnew as p
from design import ROOT
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
for f in b.GetFootprints():
    if f.IsDNP():
        for pad in f.Pads():
            layers=pad.GetLayerSet();layers.RemoveLayer(p.F_Paste);pad.SetLayerSet(layers)
c=p.PLOT_CONTROLLER(b);o=c.GetPlotOptions()
o.SetOutputDirectory(str(ROOT/'manufacturing/stencil'))
o.SetPlotFrameRef(False);o.SetPlotValue(False);o.SetPlotReference(False)
o.SetAutoScale(False);o.SetScale(1);o.SetUseGerberProtelExtensions(True)
o.SetUseGerberX2format(True);o.SetCreateGerberJobFile(False)
c.SetLayer(p.F_Paste);c.OpenPlotfile('F_Paste',p.PLOT_FORMAT_GERBER,'Populated SMD paste')
c.PlotLayer();c.ClosePlot()
