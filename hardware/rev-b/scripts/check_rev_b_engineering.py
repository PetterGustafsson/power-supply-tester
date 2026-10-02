"""Check changed components against recorded manufacturer ratings and design limits."""
from pathlib import Path
import json,math,hashlib
import pcbnew as p
from design import PARTS,ROOT
parts={x['ref']:x for x in PARTS}
b=p.LoadBoard(str(ROOT/'tester12v.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
# MPS Rev1.0 pp2,4: explicitly strapped 5V output, enabled with primary input.
expected={'1':'USB_GND','11':'USB_GND','12':'USB_GND','8':'USB5V_F','9':'USB5V_F','10':'USB5V_F','2':'AGND','3':'AGND','4':'AGND','5':'ISO5V','6':'ISO5V','7':'ISO5V'}
assert {q.GetNumber():q.GetNetname() for q in fps['U7'].Pads()}==expected
for q in fps['U7'].Pads():
 x=p.ToMM(q.GetPosition().x)
 assert x<14.65 if q.GetNetname().startswith('USB') else x>17.35
assert parts['C19']['value']=='10u' and parts['C21']['value']=='22u'
assert all(parts[r]['value']=='100n' for r in ['C20','C22'])
# Worst additive allowance, conservatively including both load and line terms.
vmin=4.85-.02*5-.02*5-.1/2;vmax=5.15+.02*5+.02*5+.1/2
assert vmin>3.3+.2 and vmax<5.5
cmax=470e-12*1.10*1.15;assert cmax<600e-12
rth=1/(1/10000+1/100000+1/330000)
for ref in [f'C{i}' for i in range(1,13)]+['C28']:
 assert parts[ref]['value']=='470p' and parts[ref]['lcsc']=='C1743'
for i in range(1,13):
 assert parts['D'+str(i)]['mpn']=='BZT52C12'
 assert fps['D'+str(i)].GetFPID().GetLibItemName()=='D_SOD-123'
# Even assigning a full 48 V to one path, current is limited by 330k.
clamp_pmax=12.6*48/(330000*.999)
assert clamp_pmax<.350/100
# 35mA is a design allocation, not a measured or guaranteed board current.
load_allowance=.035;assert load_allowance<.2
report=dict(status='PASS',module_pin_and_5V_strap_checked=True,
  module_land_source='MPS Rev1.0 p16; local coordinates and joined land halves in apply_rev_b.py',
  module_required_input_V=[4.5,5.5],conservative_output_window_V=[vmin,vmax],
  LDO_max_operating_input_V=5.5,output_design_allocation_A=load_allowance,module_capacity_A=.2,
  filter_C_max_tolerance_temperature_F=cmax,transient_test_C_F=600e-12,
  filter_nominal_pole_Hz=1/(2*math.pi*rth*470e-12),old_filter_nominal_pole_Hz=1/(2*math.pi*rth*1e-9),
  zener_leakage_datasheet_A=100e-9,zener_power_bound_48V_W=clamp_pmax,zener_rating_W=.350,
  firmware_source_sha256={str(f.name):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT.parents[1]/'firmware/Tester12V').glob('*') if f.is_file()},
  limitations=['35mA output allocation includes margin; USB input current and PTC/cable/VSYS drop must be measured.',
   'MPS switching ripple, EMI, real MLCC effective capacitance and startup are not simulated with vendor models.',
   'Filter bandwidth increases about 2.13x; white-noise contribution could rise about 1.46x. Verify 60-second noise and calibrated DC accuracy.',
   '100nA zener leakage limit is at 8V and 25C. Temperature and flux leakage need hardware qualification.'])
(ROOT/'validation/rev-b-engineering.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
