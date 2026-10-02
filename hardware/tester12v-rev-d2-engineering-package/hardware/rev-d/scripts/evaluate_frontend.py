"""Rev D nodal DC model, exercised through the actual firmware classifier.
All 3^12 assignments are evaluated, including unobservable single-pole cases.
ADC impedance/gain/offset sensitivity is an assumption, not qualification.
"""
from pathlib import Path
import ctypes as ct,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RS=2e6;RB=4700.;TOP=4700.;BOT=1000.;RL=1/(1/3e6+1/2.4e6);LSB=1.024/32768
class Model:
 def __init__(self,rs=None,rb=None,rl=None,top=TOP,bot=BOT,ref_r=RB,ref_rl=RL,ag=None,ao=None,ref_gain=1.,ref_offset=0.):
  self.rs=np.full(12,RS) if rs is None else rs;self.rb=np.full(12,RB) if rb is None else rb
  self.rl=np.full(12,RL) if rl is None else rl;self.top=top;self.bot=bot;self.ref_r=ref_r;self.ref_rl=ref_rl
  self.ag=np.ones(12) if ag is None else ag;self.ao=np.zeros(12) if ao is None else ao;self.ref_gain=ref_gain;self.ref_offset=ref_offset
 def scan(self,states,volts=12.,rail=3.3,grounded=False):
  states=np.atleast_2d(states);size=len(states);raw=np.zeros((size,12));refs=np.zeros((size,4));gr=1/self.rb
  active=states!=0;gs=active/self.rs;positive=states==1
  rfrac=(1/self.ref_r)/(1/self.ref_r+1/self.ref_rl)
  for mux in range(4):
   gl=np.where(np.arange(12)%4==mux,1/self.rl,0)
   den=gr+gs+gl;a=gr/den;b=gs/den;d=b*positive*volts
   A=1/self.top+1/self.bot+np.sum(gr*(1-a),axis=1)+(1/self.ref_r)*(1-rfrac)
   B=-np.sum(gr*b,axis=1);R=rail/self.top+np.sum(gr*d,axis=1)
   if grounded:bias=R/A;w=np.zeros(size)
   else:
    C=-np.sum(gs*a,axis=1);D=np.sum(gs*(1-b),axis=1)
    T=-np.sum(gs*(1-b)*positive*volts,axis=1)
    # With all inputs open, omit the undetermined floating source node.
    # Single-pole-only connections remain physically tied in this model.
    D=np.where(D==0,1.,D)
    bias=(R*D-B*T)/(A*D-B*C);w=(A*T-C*R)/(A*D-B*C)
   nodes=a*bias[:,None]+b*w[:,None]+d
   raw[:,mux::4]=nodes[:,mux::4]*self.ag[mux::4]+self.ao[mux::4]
   refs[:,mux]=bias*rfrac*self.ref_gain+self.ref_offset
  return raw,refs
 def calibration(self):
  raw,ref=self.scan(np.zeros(12));ratio=raw[0]/ref[0,np.arange(12)%4];gain=np.zeros(12)
  for i in range(12):
   state=np.zeros(12);state[i]=1
   low,lr=self.scan(state,0,grounded=True);high,hr=self.scan(state,12,grounded=True)
   delta=(high[0,i]-ratio[i]*hr[0,i%4])-(low[0,i]-ratio[i]*lr[0,i%4])
   gain[i]=12/delta
  return ratio,gain
lib=ct.CDLL(str(ROOT/'validation/firmware-check.dylib'))
f32=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS');u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS')
lib.check_batch.argtypes=[ct.c_int,f32,f32,f32,f32,u16,u16,ct.c_float,ct.c_float,ct.POINTER(ct.c_float)]
lib.check_batch.restype=ct.c_int

def verify(model,states,volts=12.,rail=3.3,quantize=False,ratio=None,gain=None):
 raw,ref=model.scan(states,volts,rail)
 if quantize:raw=np.round(raw/LSB)*LSB;ref=np.round(ref/LSB)*LSB
 if ratio is None:ratio,gain=model.calibration()
 masks=np.left_shift(1,np.arange(12));pos=np.sum((states==1)*masks,axis=1).astype(np.uint16);neg=np.sum((states==2)*masks,axis=1).astype(np.uint16)
 args=[np.ascontiguousarray(x,dtype=np.float32) for x in (raw,ref,ratio,gain)]
 error=ct.c_float();failed=lib.check_batch(len(states),*args,pos,neg,volts,.15,ct.byref(error))
 if failed:
  n=failed-1;v=(raw[n]-ratio*ref[n,np.arange(12)%4])*gain
  raise AssertionError(dict(state=states[n].tolist(),volts=volts,rail=rail,corrected=v.tolist(),failure_index=n))
 return error.value,float(raw.min()),float(raw.max())
model=Model();ratio,gain=model.calibration();nominal_max=0;minimum=1.;maximum=0.;total=0
for start in range(0,3**12,8192):
 code=np.arange(start,min(start+8192,3**12));states=((code[:,None]//(3**np.arange(12)))%3).astype(np.int8)
 for volts in (9.,12.,18.):
  err,low,high=verify(model,states,volts,ratio=ratio,gain=gain)
  nominal_max=max(nominal_max,err);minimum=min(minimum,low);maximum=max(maximum,high);total+=len(states)
# Independent direct nodal solve cross-check for representative topology.
def direct_solve(state,mux):
 active=np.nonzero(state)[0];n=len(active);size=14;mat=np.zeros((size,size));rhs=np.zeros(size)
 # Nodes 0..11 = ADC; 12 = bias; 13 = source return potential.
 for i in range(12):
  gr=1/RB;mat[i,i]+=gr;mat[12,12]+=gr;mat[i,12]-=gr;mat[12,i]-=gr
  if i%4==mux:mat[i,i]+=1/RL
  if state[i]:
   gs=1/RS;mat[i,i]+=gs;mat[13,13]+=gs;mat[i,13]-=gs;mat[13,i]-=gs
   d=12 if state[i]==1 else 0;rhs[i]+=gs*d;rhs[13]-=gs*d
 mat[12,12]+=1/TOP+1/BOT+1/(RB+RL);rhs[12]=3.3/TOP
 if not n:mat[13,13]=1
 return np.linalg.solve(mat,rhs)
for state in (np.array([1,2]+[0]*10),np.array([1]+[2]*11),np.array([1]*6+[2]*6),np.ones(12),np.full(12,2),np.zeros(12)):
 raw,ref=model.scan(state)
 for mux in range(4):
  x=direct_solve(state,mux);assert np.max(abs(raw[0,mux::4]-x[mux:12:4]))<1e-9
rng=np.random.default_rng(300926);sensitivity=0;sensmax=0
for trial in range(300):
 model=Model(rs=RS*(1+rng.uniform(-.01,.01,12)),rb=RB*(1+rng.uniform(-.01,.01,12)),rl=RL*rng.uniform(.5,2,12),top=TOP*(1+rng.uniform(-.01,.01)),bot=BOT*(1+rng.uniform(-.01,.01)),ref_r=RB*(1+rng.uniform(-.01,.01)),ref_rl=RL*rng.uniform(.5,2),ag=1+rng.uniform(-.0015,.0015,12),ao=rng.uniform(-.000375,.000375,12),ref_gain=1+rng.uniform(-.0015,.0015),ref_offset=rng.uniform(-.000375,.000375))
 ratio,gain=model.calibration();states=rng.integers(0,3,(100,12),dtype=np.int8)
 for i in range(12):
  states[i]=1;states[i,i]=2;states[12+i]=2;states[12+i,i]=1
 for rail in (3.,3.3,3.6):
  for volts in (9.,12.,18.):
   err,_,_=verify(model,states,volts,rail,True,ratio,gain);sensmax=max(sensmax,err);sensitivity+=len(states)
report={'status':'PASS_CALCULATION_AND_FIRMWARE','assignments':3**12,'live_assignments':3**12-2*2**12+1,
 'nominal_cases':total,'nominal_voltages_V':[9,12,18],'nominal_max_error_V':nominal_max,'nominal_ADC_min_V':minimum,'nominal_ADC_max_V':maximum,
 'sensitivity_cases':sensitivity,'sensitivity_max_error_V':sensmax,'wrong_pin_classifications':0,
 'direct_nodal_solver_crosscheck':True,'required_extra_parts':['U8','R49','C27','C28'],
 'maximum_nominal_12V_source_loading_uA':12/((RS+RB)/6*2)*1e6,
 'firmware_header_sha256':hashlib.sha256((ROOT.parents[1]/'firmware/Tester12VRevD/Measurement.h').read_bytes()).hexdigest(),
 'limitations':['One common low-impedance DC supply; at least one connection to each pole is required.',
 'All-source-off, all-open and only-one-pole-connected states are deliberately indistinguishable.',
 'This does not prove that two pins are physically connected or that a supply is faulty.',
 'Full-assignment identification targets 9-18V; low-voltage crowded assignments may be ambiguous.',
 'ADC input impedance, gain, offset and quantization model is not a vendor transistor-level model.',
 '300 seeded resistor/ADC sensitivity sets; calibration at 3.3V then rail sweep, not all component corners.',
 'No physical leakage, EMI, temperature, USB startup or calibration-noise qualification.']}
(ROOT/'validation/passive-front-end.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
