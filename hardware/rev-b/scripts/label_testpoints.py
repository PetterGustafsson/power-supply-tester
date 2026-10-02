import pcbnew as p
from design import ROOT
from build_kicad import board_text
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'))
for i in range(12):
 bank=i//4;cx=[30,52,74][bank];x=cx+(i%4-1.5)*5
 board_text(b,f'A{i+1}',x+2.4,40.5,.8)
for name,x,y in [('5V',9,62),('GND',9.5,66),('3V3',10,39),('ISO5V',26,2.7),('3V3',38,2.7),('AGND',85,20.5),('BIAS',60,20),('EN',78,20),('SDA',87.6,25),('SCL',87.6,29),('LCD',6,58.5)]:board_text(b,name,x,y,.8)
p.SaveBoard(str(ROOT/'tester12v.kicad_pcb'),b)
