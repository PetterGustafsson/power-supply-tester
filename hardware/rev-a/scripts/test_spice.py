"""Run ngspice transient models for attached-DUT startup and USB removal.

Behavioral IC models deliberately expose assumptions. They do not certify
ADG4612, OPA320 or LDO behavior below their specified operating supplies.
"""
from pathlib import Path
import ctypes as c, json, shutil, tempfile, xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ng=c.CDLL('/Applications/KiCad/KiCad.app/Contents/Frameworks/libngspice.0.dylib')
CB=c.CFUNCTYPE(c.c_int,c.c_char_p,c.c_int,c.c_void_p);log=[]
@CB
def output(s,i,u):log.append(s.decode(errors='replace'));return 0
ng.ngSpice_Init(output,None,None,None,None,None,None)
tree=ET.parse(ROOT/'validation/schematic.net');netmap={}
for net in tree.findall('./nets/net'):
    for node in net.findall('node'):netmap[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
values={x.attrib['ref']:x.findtext('value') for x in tree.findall('./components/comp')}
def node(n):return '0' if n=='AGND' else n
results=[]
for volts in [0,12,18,48]:
  for fall in [.0001,.002,.020]:
    # 0.1ms supply collapse is intentionally stressful. Actual output hold-up
    # depends on effective C24 and load, and must be measured on the prototype.
    name=f'{volts}V-{int(fall*1e6)}us'
    lines=[f'Tester Rev A startup/shutdown {name}',
      'Vfive ISO5V 0 PWL(0 0 10m 5 400m 5 '+str(.400+fall)+' 0 440m 0)',
      # Regulated until dropout. No hold-up credit from C24 is taken here.
      'Bvdd A3V3 0 V=min(3.3,max(v(ISO5V)-0.2,0))',
      'Rtop A3V3 BIAS_SET 10k','Rbottom BIAS_SET 0 10k','Cref BIAS_SET 0 1n',
      'Bbuffer BUF 0 V=min(max(v(BIAS_SET),0),max(v(A3V3)-0.03,0))',
      'Bbufen BE 0 V=(v(A3V3)>1.8 ? 3.3 : 0)',
      'Sbuffer BUF VBIAS BE 0 BUFSW','.model BUFSW SW(Ron=1 Roff=1e12 Vt=2 Vh=0)',
      'Rbleed VBIAS 0 220',f'VDUT P1 P12 {volts}',
      '.model PROTECT D(Is=1e-10 N=1.5 BV=12 IBV=5m)',
      '.model INPUTSW SW(Ron=17 Roff=1e12 Vt=2 Vh=0)',
      '.options reltol=1e-5 abstol=1e-12 method=gear']
    for number in list(range(1,37))+list(range(46,58)):
      ref=f'R{number}';lines.append(f'{ref} {node(netmap[ref,"1"])} {node(netmap[ref,"2"])} {values[ref]}')
    for i in range(1,13):
      lines += [f'Dz{i} 0 S{i} PROTECT',
        # Conservative early OVP threshold of VDD+1V (typical is +1.8V).
        f'Ben{i} EN{i} 0 V=(time>0.210 && v(A3V3)>3.08 && v(S{i})<v(ISO5V)+1 ? 3.3 : 0)',
        f'Sin{i} S{i} A{i} EN{i} 0 INPUTSW',f'Cfilter{i} A{i} 0 1.2n',
        f'Radc{i} A{i} 0 4.285714meg',
        # Stress all drain leakage in the same direction. Intermediate-supply
        # transition is an assumption, not a guaranteed vendor model.
        f'Bleak{i} 0 A{i} I=(v(EN{i})>2 ? 0 : (v(ISO5V)>1 ? 38u : 3u))']
    lines+=['.tran 10u 440m 0 10u','.end']
    netlist=ROOT/'validation'/f'spice-{name}.cir';netlist.write_text('\n'.join(lines)+'\n')
    array=(c.c_char_p*(len(lines)+1))(*[s.encode() for s in lines],None)
    assert ng.ngSpice_Circ(array)==0
    assert ng.ngSpice_Command(b'run')==0
    ng.ngSpice_Command(b'set wr_singlescale');ng.ngSpice_Command(b'set wr_vecnames')
    destination='/private/tmp/tester-spice-transient.dat'
    ng.ngSpice_Command(('wrdata '+destination+' v(A3V3) v(VBIAS) v(A1) v(A12) v(S1) v(S12) v(EN1)').encode())
    data=np.loadtxt(destination,skiprows=1)
    assert len(data)>1000,'Simulation did not produce transient data'
    time=data[:,0];rail=data[:,1];hi=data[:,3];lo=data[:,4]
    overshoot=float(max(np.max(hi-rail),np.max(lo-rail)))
    minimum=float(min(hi.min(),lo.min()))
    settled=(time>.30)&(time<.35);span=float(np.mean(hi[settled]-lo[settled])*37.3)
    # Report stress failures honestly. Very fast hard shorts are outside the
    # normal shutdown model and cannot be certified by this behavioral model.
    safe=overshoot<.30 and minimum>-.30
    if volts in (12,18):assert abs(span-volts)<.15,(name,span)
    results.append(dict(case=name,rail_fall_s=fall,applied_V=volts,
      adc_above_rail_max_V=overshoot,adc_min_V=minimum,settled_reported_V=span,
      within_ADC_absolute_voltage_window=safe))
    if volts==12 and fall==.002:
      with (ROOT/'validation/startup-shutdown.csv').open('w') as f:
        f.write('time_s,A3V3,VBIAS,A1,A12,S1,S12,EN1\n');np.savetxt(f,data[::10],delimiter=',',fmt='%.9g')
    ng.ngSpice_Command(b'destroy all')
report={'engine':'ngspice 44.2','model':'Behavioral, not vendor-validated',
 'cases':results,'normal_shutdown_pass':all(r['within_ADC_absolute_voltage_window'] for r in results if r['rail_fall_s']>=.002),
 'assumptions':['Ideal LDO with 0.2V dropout, no output-capacitor hold-up credit.',
  'Buffer disconnects below 1.8V; partial-supply IC behavior is not specified by this model.',
  '1.2nF input capacitors stress +20% tolerance; source clamps use a generic diode model.',
  'Switch leakage 38uA when supply >1V, 3uA below; transition is an explicit modeling assumption.',
  'A 0.1ms collapse is an extra stress case, not a guaranteed operating condition.']}
(ROOT/'validation/spice-results.json').write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'validation/spice.log').write_text('\n'.join(log)+'\n')
print(json.dumps(report,indent=2))
