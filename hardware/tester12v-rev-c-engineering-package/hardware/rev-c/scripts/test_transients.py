"""Passive front-end startup/shutdown model, including single-pin DC stress.
No ADC clamp diode credit and no proprietary IC behavior assumed. The power
rail is imposed to expose its required slew limit; actual USB startup and
shutdown require bench verification after assembly.
"""
from pathlib import Path
import ctypes as c,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ng=c.CDLL('/Applications/KiCad/KiCad.app/Contents/Frameworks/libngspice.0.dylib')
CB=c.CFUNCTYPE(c.c_int,c.c_char_p,c.c_int,c.c_void_p);log=[]
@CB
def out(s,i,u):log.append(s.decode(errors='replace'));return 0
ng.ngSpice_Init(out,None,None,None,None,None,None)
results=[]
for voltage in (0,12,18,48):
 for mode in ('pair','positive_single','negative_single'):
  for fall in (1e-6,1e-5,1e-4,1e-3):
   name=f'{voltage}V-{mode}-{fall*1e6:g}us'
   lines=[name,f'VDD A3V3 0 PWL(0 0 1m 3.6 10m 3.6 {0.01+fall} 0 12m 0)',
    'Rtop A3V3 VBIAS 4747','Rbottom VBIAS 0 1010','Cref VBIAS 0 600p',
    '.options reltol=1e-5 abstol=1e-13 method=gear']
   if mode=='pair':lines.append(f'VDUT P1 P12 {voltage}')
   else:lines.append(f'VDUT P1 0 {voltage if mode=="positive_single" else -voltage}')
   for i in range(1,13):
    lines.extend([f'Rhi{i} P{i} MID{i} 990k',f'Rlo{i} MID{i} A{i} 990k',
      f'Rbias{i} A{i} VBIAS 4747',f'Cfilter{i} A{i} 0 600p',
      # Tiny shunts regularize otherwise floating SPICE nodes without affecting results.
      f'Rstray{i} A{i} 0 1t'])
   # 50ns step catches fast-rail failure. Keep startup/shutdown duration short.
   lines.extend(['.tran 100n 12m 0 100n','.end'])
   (ROOT/'validation'/f'transient-{name}.cir').write_text('\n'.join(lines)+'\n')
   arr=(c.c_char_p*(len(lines)+1))(*[x.encode() for x in lines],None)
   assert ng.ngSpice_Circ(arr)==0 and ng.ngSpice_Command(b'run')==0
   ng.ngSpice_Command(b'set wr_singlescale');ng.ngSpice_Command(b'set wr_vecnames')
   path='/private/tmp/revc-transient.dat'
   ng.ngSpice_Command(f'wrdata {path} v(A3V3) v(VBIAS) v(A1) v(A12)'.encode())
   data=np.loadtxt(path,skiprows=1);rail=data[:,1];a=data[:,3:5]
   above=float(np.max(a-rail[:,None]));below=float(np.min(a));ok=above<.3 and below>-.3
   result=dict(case=name,fall_us=fall*1e6,min_ADC_V=below,max_ADC_above_rail_V=above,within_absolute_voltage_limits=ok)
   results.append(result)
   if voltage==18 and mode=='pair' and fall==1e-4:
    np.savetxt(ROOT/'validation/startup-shutdown.csv',data[::50],delimiter=',',header='time_s,A3V3,VBIAS,A1,A12',comments='')
   ng.ngSpice_Command(b'destroy all')
normal=[x for x in results if x['fall_us']>=100]
assert all(x['within_absolute_voltage_limits'] for x in normal)
report={'status':'PASS_NORMAL_SLEW_MODEL','cases':results,
 'normal_slew_cases':len(normal),'normal_slew_all_pass':True,
 'normal_max_ADC_above_rail_V':max(x['max_ADC_above_rail_V'] for x in normal),
 'normal_min_ADC_V':min(x['min_ADC_V'] for x in normal),
 'assumptions':['600pF bounds fitted 470pF tolerance/temperature plus node parasitics.',
 'Minimum 2M series and maximum 4.7k/bias resistor tolerance used.',
 '100us is the deliberately fast normal rail-collapse model; bulk output capacitor and load should make USB removal slower. Must be measured.',
 '1us and 10us cases represent abnormal forced rail collapse, not USB removal; failures remain reported.',
 'No claim of ADC behavior below operating voltage, ESD immunity, 48V survival or physical qualification.']}
(ROOT/'validation/transient-results.json').write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'validation/transient.log').write_text('\n'.join(log)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
print('Abnormal forced-collapse failures:',sum(not x['within_absolute_voltage_limits'] for x in results))
