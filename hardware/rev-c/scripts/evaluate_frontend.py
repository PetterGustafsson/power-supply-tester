"""Evaluate a passive Rev-C candidate. This is not a qualified IC/PCB model.
Floating DC source, switched ADS1115 typical input impedances, bias divider,
resistor tolerances and independent ADC gain/offset assumptions are explicit.
"""
from pathlib import Path
import itertools,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
N=13
RS=2e6; RB=4700.; TOP=4700.; BOT=1000.; GAIN=1+RS/RB
# TI SBAS444E: PGA +/-1.024 V: 3M common mode, 2.4M differential.
RLOAD=1/(1/3e6+1/2.4e6)
LSB=1.024/32768

def circuit(rs,rb,top,bot,rl,rail=3.3):
    models=[]
    for mux in range(4):
        g=np.zeros((N,N));rhs=np.zeros(N)
        g[12,12]+=1/top+1/bot;rhs[12]=rail/top
        for i in range(12):
            c=1/rb[i];g[i,i]+=c;g[12,12]+=c;g[i,12]-=c;g[12,i]-=c
            if i%4==mux:g[i,i]+=1/rl[i]
        inv=np.linalg.inv(g);models.append((g,rhs,inv,inv@rhs))
    return models

def scan(models,rs,positive=None,negative=None,volts=0,clamp=None):
    v=np.empty(12)
    for mux,(g,rhs,inv,x0) in enumerate(models):
        x=x0
        if positive is not None:
            a,b=positive,negative;z=inv[:,a]-inv[:,b]
            current=(volts-x0[a]+x0[b])/(rs[a]+rs[b]+z[a]-z[b]);x=x0+z*current
        elif clamp is not None:
            a,value=clamp;z=inv[:,a]
            current=(value-x0[a])/(rs[a]+z[a]);x=x0+z*current
        v[mux::4]=x[mux:12:4]
    return v

def relative(raw,zero):
    # Normalize the open-input readings to remove common bias/supply movement.
    base=np.median(raw/zero)
    return raw-zero*base

def calibrate(models,rs,adc_gain,adc_offset):
    zero=scan(models,rs)*adc_gain+adc_offset
    gains=np.empty(12)
    for i in range(12):
        low=relative(scan(models,rs,clamp=(i,0))*adc_gain+adc_offset,zero)[i]
        high=relative(scan(models,rs,clamp=(i,12))*adc_gain+adc_offset,zero)[i]
        gains[i]=12/(high-low)
    return zero,gains

rs=np.full(12,RS);rb=np.full(12,RB);rl=np.full(12,RLOAD)
models=circuit(rs,rb,TOP,BOT,rl)
zero,gains=calibrate(models,rs,np.ones(12),np.zeros(12))
rows=[]
for a,b in itertools.permutations(range(12),2):
    for voltage in (0,.5,3.3,5,9,12,15,18,24,48):
        raw=scan(models,rs,a,b,voltage);corrected=relative(raw,zero)*gains
        observed=corrected[a]-corrected[b]
        assert raw.min()>0 and raw.max()<1.024
        assert abs(observed-voltage)<(.03 if voltage<=18 else .08),(a,b,voltage,observed)
        if voltage:assert corrected.argmax()==a and corrected.argmin()==b
        rows.append((a+1,b+1,voltage,observed))

# Sensitivity bounds are assumptions, not manufacturer guaranteed distributions.
rng=np.random.default_rng(301026);maxerr=0;errors=[];misidentifications=0
for trial in range(500):
    rs=RS*(1+rng.uniform(-.01,.01,12));rb=RB*(1+rng.uniform(-.01,.01,12))
    top=TOP*(1+rng.uniform(-.01,.01));bot=BOT*(1+rng.uniform(-.01,.01))
    rl=RLOAD*rng.uniform(.5,2,12)
    ag=1+rng.uniform(-.0015,.0015,12);ao=rng.uniform(-.000375,.000375,12)
    model=circuit(rs,rb,top,bot,rl)
    zero,gs=calibrate(model,rs,ag,ao)
    for rail in (3.0,3.3,3.6):
        model=circuit(rs,rb,top,bot,rl,rail)
        for a,b in ((0,1),(0,4),(0,11),(8,7)):
            raw=scan(model,rs,a,b,12)*ag+ao
            # One conversion, +/-0.5 LSB quantization. Extra noise/leakage below.
            raw=np.round(raw/LSB)*LSB
            result=relative(raw,zero)*gs;reported=result[a]-result[b]
            errors.append(float(reported-12))
            if result.argmax()!=a or result.argmin()!=b:misidentifications+=1
maxerr=max(map(abs,errors))
assert maxerr<.08 and not misidentifications,(maxerr,misidentifications)
# Full voltage on a single terminal, no even-split credit; include bias source
# impedance in the off-state path. Worst R tolerances. No ADC diode assistance.
off_bound=48*(RB*1.01+1/(1/(TOP*1.01)+1/(BOT*1.01)))/(RS*.99+RB*1.01+1/(1/(TOP*1.01)+1/(BOT*1.01)))
assert off_bound<.15
report={
 'status':'PASS_CALCULATION_ONLY','nominal_attenuation':GAIN,'adc_FSR_V':1.024,
 'input_referred_LSB_V':GAIN*LSB,'nominal_bias_V':3.3*BOT/(TOP+BOT),
 'ordered_pairs':132,'nominal_cases':len(rows),'nominal_max_error_V':max(abs(r[2]-r[3]) for r in rows),
 'nominal_max_error_0_to_18V':max(abs(r[2]-r[3]) for r in rows if r[2]<=18),
 'calibrated_sensitivity_trials':len(errors),'calibrated_12V_max_error_V':maxerr,
 'wrong_polarity_or_pair':misidentifications,
 'unpowered_48V_single_terminal_bound_V':off_bound,
 'series_resistor_max_power_W':(48/(RS*.99))**2*1e6*1.01,
 'pair_loading_12V_uA':12/(2*RS+2*RB)*1e6,
 'per_channel_leakage_change_10nA_input_error_V':RS*10e-9,
 'limitations':['Not a transistor-level ADS1115 model; input impedance is typical only.',
 '500 seeded 1% resistor/ADC sensitivity sets, not a proof of all corners.',
 'Offset/gain are calibrated at 3.3V before supply sweep; firmware must implement bias normalization.',
 'No physical tests, PCB leakage, EMC/ESD, hot plug or transient verification included in this report.',
 '48V is an off-state calculation, not an operating or survival rating.',
 'Ground-referenced 0V/12V calibration uses isolated analog ground only; final instrument is floating.']}
(ROOT/'validation/passive-front-end.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
