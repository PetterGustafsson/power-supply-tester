"""Independent linear nodal analysis from KiCad's EXPORTED schematic netlist.

This is a design calculation, not a vendor IC model or a physical test. Switch
Ron and ADC input loading are explicit approximations. Nonlinear startup is
checked separately in ngspice. Run with KiCad's Python (numpy included).
"""
import csv, itertools, json, math, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
tree=ET.parse(ROOT/'validation/schematic.net')
values={x.attrib['ref']:x.findtext('value') for x in tree.findall('./components/comp')}
nets={}
for net in tree.findall('./nets/net'):
    for node in net.findall('node'):nets[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
nodes=[f'{prefix}{n}' for prefix in ['P','MID','S','A'] for n in range(1,13)]
idx={v:k for k,v in enumerate(nodes)}
fixed={'VBIAS':1.65,'AGND':0.0}
def ohms(s):return float(s[:-1])*{'k':1000,'M':1e6,'R':1}[s[-1]] if s[-1] in 'kMR' else float(s)

def matrix(mux, loading=True):
    G=np.zeros((48,48));rhs=np.zeros(48)
    def resistor(a,b,r):
        conductance=1/r
        for node,other in [(a,b),(b,a)]:
            if node not in idx:continue
            i=idx[node];G[i,i]+=conductance
            if other in idx:G[i,idx[other]]-=conductance
            else:rhs[i]+=conductance*fixed[other]
    for n in list(range(1,37))+list(range(46,58)):
        ref=f'R{n}';resistor(nets[ref,'1'],nets[ref,'2'],ohms(values[ref]))
    for bank in range(3):
        sw='U'+str(bank+4)
        for sp,dp in [(3,2),(14,15),(11,10),(6,7)]:
            resistor(nets[sw,str(sp)],nets[sw,str(dp)],12.5)
        if loading:
            adc='U'+str(bank+1)
            # Typical common-mode 6M and differential 15M, single-ended to GND.
            resistor(nets[adc,str(4+mux)],'AGND',1/(1/6e6+1/15e6))
    return np.linalg.inv(G),rhs

models=[matrix(i) for i in range(4)]
def scan(positive,negative,volts):
    result=np.zeros(12)
    for mux,(inv,rhs) in enumerate(models):
        x0=inv@rhs;a=idx[f'P{positive}'];b=idx[f'P{negative}']
        z=inv[:,a]-inv[:,b]
        current=(volts-x0[a]+x0[b])/(z[a]-z[b]);x=x0+z*current
        for bank in range(3):
            # Read through the actual U1/U2/U3 pad mapping, not a parallel map.
            ref=f'U{bank+1}';result[bank*4+mux]=x[idx[nets[ref,str(mux+4)]]]
    return result

rows=[];maxerr=0;limits=[100.,-100.];checks=0
for a,b in itertools.permutations(range(1,13),2):
    for voltage in [0,3.3,5,9,12,15,18,24,48]:
        adc=scan(a,b,voltage);observed=37.3*(adc.max()-adc.min())
        assert np.all(adc>0.15) and np.all(adc<3.10),(a,b,voltage,adc)
        if voltage:
            assert int(adc.argmax())+1==a and int(adc.argmin())+1==b
            assert abs(observed-voltage)<voltage*.004
        else:assert observed<.01
        if voltage==12:maxerr=max(maxerr,abs(observed-12))
        limits=[min(limits[0],float(adc.min())),max(limits[1],float(adc.max()))]
        rows.append([a,b,voltage,observed,*adc.tolist()]);checks+=1

# Reproducible sensitivity sweep. These bounds are test assumptions; the ADC
# single-ended offset and input impedance are not guaranteed max/min specs.
rng=np.random.default_rng(120926);count=20000
rseries=330e3*(1+rng.uniform(-.001,.001,(count,2)))
rbias=10e3*(1+rng.uniform(-.001,.001,(count,2)))
rpre=100e3*(1+rng.uniform(-.001,.001,(count,2)))
ron=rng.uniform(4,17,(count,2))
rload=(1/(1/6e6+1/15e6))*rng.uniform(.5,2,(count,2))
q=1/(1/rbias+1/rload);t=1.65*q/rbias
rth=1/(1/rpre+1/(ron+q));s0=t*rth/(ron+q)
current=(12-s0[:,0]+s0[:,1])/(rseries.sum(axis=1)+rth.sum(axis=1))
s=s0+np.column_stack([current,-current])*rth
adc=(s*q+t*ron)/(q+ron)
gain=rng.uniform(-.0015,.0015,(count,2));offset=rng.uniform(-.000375,.000375,(count,2))
# Room-temperature clamp leakage bound plus on-switch leakage stress.
leak=rng.uniform(-.105e-6,.105e-6,(count,2))
adc=adc+leak*rth*q/(ron+q)
read=np.round((adc*(1+gain)+offset)/.000125)*.000125
error=37.3*(read[:,0]-read[:,1])-12
assert np.max(np.abs(error))<.40
assert np.all(read[:,0]>read[:,1])

# Exact resistor corner transfer, including asymmetric R tolerances and Ron.
cornererrors=[]
for signs in itertools.product([-1,1],repeat=6):
    rs=np.array([330e3,330e3])*(1+.001*np.array(signs[:2]))
    rb=np.array([10e3,10e3])*(1+.001*np.array(signs[2:4]))
    rp=np.array([100e3,100e3])*(1+.001*np.array(signs[4:6]))
    rt=1/(1/rp+1/(rb+17));base=1.65*rt/(rb+17)
    I=(12-base[0]+base[1])/(rs.sum()+rt.sum())
    source=base+np.array([I,-I])*rt
    node=(source*rb+1.65*17)/(rb+17)
    cornererrors.append(float(37.3*(node[0]-node[1])-12))
assert max(map(abs,cornererrors))<.05

off_leak=3e-6
off_adc_bound=off_leak*12*220+off_leak*10000
assert off_adc_bound<.3
# Conservative resistor power: full 48V across one 330k chain, no sharing credit.
resistor_power=(48/(330e3*.999))**2*(165e3*1.001)
assert resistor_power<.125/10
# During startup, even ignoring the negative Zener, source bleed gives +/-2.1 V
# at an 18V floating pair, below the 5V switch's overvoltage disconnect threshold.
startup_smax=18*100e3*1.001/(2*330e3*.999+2*100e3*.999)
assert startup_smax<3.0
report={
 'status':'PASS','scope':'Pre-fabrication models only; no assembled PCB tested',
 'exported_netlist_cases':checks,'ordered_pin_pairs':132,
 'voltages_tested_V':[0,3.3,5,9,12,15,18,24,48],
 'nominal_12V_max_loading_error_V':maxerr,'ADC_extrema_through_48V':limits,
 'resistor_corner_cases':64,'resistor_corner_max_error_12V_V':max(map(abs,cornererrors)),
 'sensitivity_trials':count,'sensitivity_uncalibrated_max_abs_error_V':float(np.max(np.abs(error))),
 'sensitivity_uncalibrated_99_percent_abs_error_V':float(np.quantile(np.abs(error),.99)),
 'off_state_ADC_leakage_bound_V':off_adc_bound,
 'worst_165k_power_at_48V_W':resistor_power,
 'startup_source_bound_18V_V':startup_smax,
 'filter_time_constant_s':1/(1/10000+1/100000+1/330000)*1e-9,
 'limitations':['ADC impedance and offset sweep bounds are assumptions, not guaranteed limits.',
  'Steady-state linear models exclude PCB leakage, EMI and nonlinear fault behavior.',
  'Calibration and bench verification remain required. 48V is a DC miswire design target.']}
(ROOT/'validation/circuit-results.json').write_text(json.dumps(report,indent=2)+'\n')
with (ROOT/'validation/all-pin-pairs.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['positive','negative','applied_V','reported_V']+[f'A{i}_V' for i in range(1,13)]);w.writerows(rows)
print(json.dumps(report,indent=2))
