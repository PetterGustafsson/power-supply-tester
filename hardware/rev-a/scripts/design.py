"""Authoritative Rev-A component/pin manifest. Coordinates in mm.

Electrical scope: separately powered nominal-12-V DC pair detector. All twelve
terminals are sense inputs; none is a power output or a hard ground connection.
"""
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'tester12v'
NS = uuid.UUID('fdbf9edf-019f-4a95-94d0-9d1887e8cd30')
def uid(s): return str(uuid.uuid5(NS, s))

SYMS = {}
def ic(name, left, right, width=15.24):
    pins=[]
    height=max(len(left),len(right))*2.54+2.54
    for side, seq in [('L',left),('R',right)]:
        for k, (number, label, kind) in enumerate(seq):
            y=(len(seq)-1)*1.27-k*2.54
            pins.append(dict(n=str(number),name=label,type=kind,x=(-1 if side=='L' else 1)*(width/2+2.54),y=y,angle=0 if side=='L' else 180))
    SYMS[name]=dict(kind='ic',pins=pins,w=width,h=height)

def passive(name,kind='r'):
    SYMS[name]=dict(kind=kind,pins=[dict(n='1',name='~',type='passive',x=-5.08,y=0,angle=0),dict(n='2',name='~',type='passive',x=5.08,y=0,angle=180)],w=5.08,h=2.54)
passive('R');passive('C','c');passive('D','d');passive('DZ','z');passive('LED','d');passive('FB','r');passive('FUSE','r')
ic('ADS1115',[(4,'AIN0','input'),(5,'AIN1','input'),(6,'AIN2','input'),(7,'AIN3','input'),(1,'ADDR','input')],[(8,'VDD','power_in'),(3,'GND','power_in'),(9,'SDA','bidirectional'),(10,'SCL','input'),(2,'ALERT_RDY','open_collector')])
ic('ADG4612',[(3,'S1','passive'),(14,'S2','passive'),(11,'S3','passive'),(6,'S4','passive'),(1,'IN1','input'),(16,'IN2','input'),(9,'IN3','input'),(8,'IN4','input')],[(2,'D1','passive'),(15,'D2','passive'),(10,'D3','passive'),(7,'D4','passive'),(13,'VDD','power_in'),(4,'VSS','power_in'),(5,'GND','power_in'),(12,'NC','no_connect')])
ic('ISO1640B',[(1,'VCC1','power_in'),(2,'SDA1','bidirectional'),(3,'SCL1','bidirectional'),(4,'GND1','power_in')],[(8,'VCC2','power_in'),(7,'SDA2','bidirectional'),(6,'SCL2','bidirectional'),(5,'GND2','power_in')])
ic('R05C05TE05S',[(1,'-VIN','power_in'),(2,'-VIN','passive'),(3,'+VIN','power_in'),(4,'+VIN','passive'),(5,'SGNDIN','passive'),(6,'SGNDIN','passive'),(7,'SGNDIN','passive'),(8,'SGNDIN','passive')],[(16,'-VOUT','power_out'),(15,'-VOUT','passive'),(14,'+VOUT','power_out'),(13,'+VOUT','passive'),(12,'SGNDOUT','passive'),(11,'SGNDOUT','passive'),(10,'DNC','no_connect'),(9,'SGNDOUT','passive')],20.32)
ic('TLV75533',[(1,'IN','power_in'),(3,'EN','input'),(2,'GND','power_in')],[(5,'OUT','power_out'),(4,'NC','no_connect')])
ic('OPA320',[(3,'IN+','input'),(4,'IN-','input'),(2,'VSS','power_in')],[(1,'OUT','output'),(5,'VDD','power_in')])
ic('TLV809EA30',[(3,'VDD','power_in'),(1,'GND','power_in')],[(2,'RESET_N','output')])
for n in (4,5):ic('CONN'+str(n),[],[(k,str(k),'passive') for k in range(1,n+1)],5.08)
SYMS['TP']=dict(kind='tp',pins=[dict(n='1',name='1',type='passive',x=0,y=0,angle=90)],w=1,h=1)
SYMS['FLAG']=dict(kind='flag',pins=[dict(n='1',name='pwr',type='power_out',x=0,y=0,angle=90)],w=1,h=1)

F={
 'R':'Resistor_SMD:R_0805_2012Metric', 'C':'Capacitor_SMD:C_0805_2012Metric',
 'DZ':'Diode_SMD:D_SOD-123F','LED':'LED_SMD:LED_0805_2012Metric',
 'ADS':'Package_SO:TSSOP-10_3x3mm_P0.5mm',
 'SW':'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
 'ISO':'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
 'DCDC':'Tester:R05C05TE05S', 'SOT5':'Package_TO_SOT_SMD:SOT-23-5',
 'SOT3':'Package_TO_SOT_SMD:SOT-23',
 'TERM':'TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal',
 'JST':'Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical',
 'TP':'TestPoint:TestPoint_Pad_D1.5mm',
}
PARTS=[]
def add(ref,sym,value,pins,fp,pcb,sch,page='root',mpn='',maker='',note='',dnp=False,schrot=0):
    entry=dict(ref=ref,sym=sym,value=value,pins={str(k):v for k,v in pins.items()},fp=fp,pcb=pcb,sch=sch,page=page,mpn=mpn,maker=maker,note=note,dnp=dnp,schrot=schrot,uuid=uid(ref))
    assert {p['n'] for p in SYMS[sym]['pins']}==set(entry['pins']),ref
    PARTS.append(entry);return entry

def resistor(ref,value,a,b,pcb,sch,page='root',precision=False,dnp=False):
    mpns={'165k':'RT0805BRD07165KL','10k':'RT0805BRD0710KL','220R':'RC0805FR-07220RL','1k':'RC0805FR-071KL','100k':'RC0805FR-07100KL','2.2k':'RC0805FR-072K2L','4.7k':'RC0805FR-074K7L','10R':'RC0805FR-0710RL'}
    if precision and value=='100k':mpns['100k']='RT0805BRD07100KL'
    return add(ref,'R',value,{1:a,2:b},F['R'],pcb,sch,page,mpns[value],'Yageo','0.1%, 25 ppm/K' if precision else '1%',dnp)
def capacitor(ref,value,a,b,pcb,sch,page='root'):
    mpns={'1n':'GRM2165C1H102JA01D','10n':'GRM21BR71H103KA01L','100n':'GRM21BR71H104KA01L','1u':'GRM21BR71E105KA99L','10u':'GRM21BR61A106KE19L','22u':'GRM21BR61A226ME44L'}
    return add(ref,'C',value,{1:a,2:b},F['C'],pcb,sch,page,mpns[value],'Murata','Use specified capacitance, voltage and dielectric')

# Bank channels have unique input terminals and no hard ground connection.
# ADG4612 switches lie AFTER the 330k current-limiting chain and BEFORE the
# bias resistors. Their power-off blocking also protects the bias buffer.
CHANNELS=[]
for bank,cx in enumerate((30,52,74)):
    page='bank'+str(bank+1); first=bank*4+1
    add('J'+str(bank+1),'CONN4',f'INPUTS {first}-{first+3}',{k:f'P{first+k-1}' for k in range(1,5)},F['TERM'],[cx-5.25,72,0],[30,92],page,'1984633','Phoenix Contact','PT 1,5/4-3,5-H; 1984633 verified against Phoenix Contact product page, 3.5mm pitch')
    adc='U'+str(bank+1);sw='U'+str(bank+4)
    adc_inputs=[4,5,6,7]; sourcepins=[3,14,11,6]; drainpins=[2,15,10,7]
    ap={8:'A3V3',3:'AGND',9:'SDA_ISO',10:'SCL_ISO',2:None,1:['AGND','A3V3','SDA_ISO'][bank]}
    sp={13:'ISO5V',4:'AGND',5:'AGND',12:None,1:'SENSE_EN',16:'SENSE_EN',9:'SENSE_EN',8:'SENSE_EN'}
    for k in range(4):
        n=first+k;x=cx+(k-1.5)*5;sy=40+k*38
        ra=f'R{3*n-2}';rb=f'R{3*n-1}';rc=f'R{3*n}'
        resistor(ra,'165k',f'P{n}',f'MID{n}',[x,65,90],[78,sy],page,True)
        resistor(rb,'165k',f'MID{n}',f'S{n}',[x,60,90],[115,sy],page,True)
        add('D'+str(n),'DZ','12V clamp',{1:f'S{n}',2:'AGND'},F['DZ'],[x,54,90],[151,sy],page,'BZT52H-C12,115','Nexperia','Clamp is before power-off switch; not an ADC rail clamp')
        resistor(rc,'10k',f'A{n}','VBIAS',[x,37,90],[151,sy+13],page,True)
        resistor(f'R{45+n}','100k',f'S{n}','AGND',[x,50,0],[115,sy+13],page,True)
        capacitor('C'+str(n),'1n',f'A{n}','AGND',[x,32,90],[191,sy+13],page)
        add('TP'+str(n),'TP',f'A{n}',{1:f'A{n}'},F['TP'],[x,40.5,0],[192,sy],page)
        ap[adc_inputs[k]]=f'A{n}';sp[sourcepins[k]]=f'S{n}';sp[drainpins[k]]=f'A{n}'
        CHANNELS.append(dict(pin=n,bank=bank,adc=adc,address=0x48+bank,mux=k,series=[ra,rb],bias=rc,switch=sw,s_pin=sourcepins[k],d_pin=drainpins[k],adc_pin=adc_inputs[k],clamp=f'D{n}',startup=f'R{45+n}',filter=f'C{n}',testpoint=f'TP{n}'))
    add(adc,'ADS1115','ADS1115IDGSR',ap,F['ADS'],[cx,25,0],[334,88],page,'ADS1115IDGSR','Texas Instruments','ADDR=GND/3V3/SDA for 0x48/0x49/0x4A')
    add(sw,'ADG4612','ADG4612BRUZ',sp,F['SW'],[cx,45.5,0],[261,91],page,'ADG4612BRUZ','Analog Devices','TSSOP-16; powered from isolated 5V; enable from 3.08V supervisor')
    capacitor('C'+str(13+bank),'100n','A3V3','AGND',[cx+5,25,90],[330,130],page)
    capacitor('C'+str(16+bank),'100n','ISO5V','AGND',[cx+6,46,90],[260,135],page)

# Controller/display harness: no DUT wire goes to this connector.
add('J4','CONN5','DISPLAY HARNESS',{1:'USB5V',2:'USB_GND',3:'HOST3V3',4:'SDA_HOST',5:'SCL_HOST'},F['JST'],[6,55,90],[35,45],mpn='B5B-XH-A(LF)(SN)',maker='JST',note='1=5V,2=GND,3=3V3,4=GPIO6 SDA,5=GPIO7 SCL. USB supplies both boards; no battery-only operation guaranteed.')
add('U7','R05C05TE05S','R05C05TE05S-R',{1:'USB_GND',2:'USB_GND',3:'USB5V_F',4:'USB5V_F',5:'USB_GND',6:'USB_GND',7:'USB_GND',8:'USB_GND',9:'AGND',10:None,11:'AGND',12:'AGND',13:'ISO5V',14:'ISO5V',15:'AGND',16:'AGND'},F['DCDC'],[16,11,0],[137,47],mpn='R05C05TE05S-R',maker='RECOM',note='Mandatory local 10uF+100nF at input and output; SGNDIN/OUT tied to their own return')
add('U8','ISO1640B','ISO1640BDR',{1:'HOST3V3',2:'SDA_HOST',3:'SCL_HOST',4:'USB_GND',5:'AGND',6:'SCL_ISO',7:'SDA_ISO',8:'A3V3'},F['ISO'],[16,29,0],[137,124],mpn='ISO1640BDR',maker='Texas Instruments',note='B suffix is the 8-pin device; do not substitute ISO1640DW')
add('U9','TLV75533','TLV75533PDBVR',{1:'ISO5V',2:'AGND',3:'ISO5V',4:None,5:'A3V3'},F['SOT5'],[33,10,0],[224,44],mpn='TLV75533PDBVR',maker='Texas Instruments')
add('U10','OPA320','OPA320AIDBVR',{1:'VBIAS',2:'AGND',3:'BIAS_SET',4:'VBIAS',5:'A3V3'},F['SOT5'],[54,11,0],[221,116],mpn='OPA320AIDBVR',maker='Texas Instruments',note='Unity gain reference buffer. No large output capacitor directly on the buffer.')
add('U11','TLV809EA30','TLV809EA30DBZR',{1:'AGND',2:'SENSE_EN',3:'A3V3'},F['SOT3'],[73,10,0],[318,115],mpn='TLV809EA30DBZR',maker='Texas Instruments',note='3.08V falling threshold, 200ms release delay, push-pull; default pinout GND=1 RESET=2 VDD=3')
add('D13','D','Reverse protection',{1:'ISO5V',2:'A3V3'},'Diode_SMD:Nexperia_CFP3_SOD-123W',[33,15,0],[223,82],mpn='PMEG2010ER,115',maker='Nexperia',note='Schottky OUT-to-IN reverse-current protection for U9; cathode to ISO5V')
resistor('R37','10k','A3V3','BIAS_SET',[46,7,0],[192,86],precision=True)
resistor('R38','10k','BIAS_SET','AGND',[46,12,0],[192,97],precision=True)
resistor('R39','220R','VBIAS','AGND',[54,18,0],[221,150])
# Push-pull supervisor avoids a pull-up divider against 12 internal pull-downs.
resistor('R40','100k','SENSE_EN','AGND',[72,17,0],[318,143])
resistor('R41','4.7k','A3V3','SDA_ISO',[80,6,0],[276,165])
resistor('R42','4.7k','A3V3','SCL_ISO',[80,11,0],[276,178])
resistor('R43','4.7k','HOST3V3','SDA_HOST',[6,24,0],[50,134],dnp=True)
resistor('R44','4.7k','HOST3V3','SCL_HOST',[6,29,0],[50,149],dnp=True)
resistor('R45','1k','A3V3','AGND',[65,17,0],[318,163])
add('F1','FUSE','250mA PTC',{1:'USB5V',2:'USB5V_F'},'Fuse:Fuse_1206_3216Metric',[6,8,90],[65,45],mpn='1206L025/24YR',maker='Littelfuse',note='5V supply only, slow resettable overcurrent protection')
for ref,value,a,b,pcb,sch in [
 ('C19','10u','USB5V_F','USB_GND',[6,14,90],[80,65]),
 ('C20','100n','USB5V_F','USB_GND',[6,18,90],[80,77]),
 ('C21','10u','ISO5V','AGND',[26,10,90],[175,45]),
 ('C22','100n','ISO5V','AGND',[26,15,90],[175,58]),
 ('C23','1u','ISO5V','AGND',[32,5,0],[223,69]),
 ('C24','22u','A3V3','AGND',[38,10,90],[259,45]),
 ('C25','100n','A3V3','AGND',[38,15,90],[259,58]),
 ('C26','100n','HOST3V3','USB_GND',[7,35,90],[98,160]),
 ('C27','100n','A3V3','AGND',[22,25,90],[176,136]),
 ('C28','1n','BIAS_SET','AGND',[45,18,0],[193,150]),
 ('C29','100n','A3V3','AGND',[59,11,90],[265,128]),
 ('C30','100n','A3V3','AGND',[67,10,90],[365,138]),
]:capacitor(ref,value,a,b,pcb,sch)

for k,(net,xy,sc) in enumerate([
 ('USB5V',[6,62],[30,184]),('USB_GND',[6,66],[60,184]),
 ('HOST3V3',[6,39],[90,184]),('ISO5V',[26,5],[120,184]),
 ('A3V3',[38,5],[150,184]),('AGND',[85,18],[180,184]),
 ('VBIAS',[60,18],[210,184]),('SENSE_EN',[78,18],[240,184]),
 ('SDA_ISO',[85,25],[270,184]),('SCL_ISO',[85,29],[300,184])],13):
    add('TP'+str(k),'TP',net,{1:net},F['TP'],[*xy,0],sc)
for k,net in enumerate(('USB5V','USB5V_F','USB_GND','HOST3V3')):
    add('#FLG'+str(k+1),'FLAG',net,{1:net},'',None,[35+50*k,205])

assert len(set(p['ref'] for p in PARTS))==len(PARTS)

# Sourcing metadata only: keep all electrical values, nets and geometry unchanged.
from jlc_catalog import apply as apply_jlc_sourcing
apply_jlc_sourcing(PARTS)

SCOPE={
 'nominal_voltage_V':12,'intended_measurement_V':[0,18],
 'dc_miswire_design_limit_V':48,'input_count':12,
 'input_scope':'One DC source on any pair; other terminals open. Reversed polarity allowed. Multiple rails are reported as ambiguous.',
 'power':'USB 5V and host 3V3 through J4 from the existing Waveshare module',
 'display':'Waveshare ESP32-S3-LCD-1.28 via five-wire harness; module mechanically separate',
 'isolation':'Functional isolation of all measurement electronics from USB; not mains/CAT rated',
 'accuracy':'Design target +/-0.15V around 12V at room temperature after per-channel calibration; not a measured guarantee',
 'board_mm':[90,80],'layers':2,'thickness_mm':1.6,
 'calibration_required':True,'bench_verified':False,
}
