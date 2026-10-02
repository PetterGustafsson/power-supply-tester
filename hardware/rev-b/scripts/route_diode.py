import complete_connections as r
p=r.p;b=r.b
def pad(ref,n):return next(z for f in b.GetFootprints() if f.GetReference()==ref for z in f.Pads() if z.GetNumber()==n)
for number,net,target in [('1','ISO5V','C22'),('2','A3V3','C25')]:
 start=r.xy(pad('D13',number).GetPosition());end=r.xy(pad(target,'1').GetPosition())
 r.route(net,start,end,(18,2,44,25))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(r.ROOT/'tester12v.kicad_pcb'),b)
