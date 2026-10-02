"""Authoritative Rev-D1 component/pin manifest. Coordinates in mm.

Electrical scope: USB-powered nominal-12-V common-supply pin detector. All twelve
terminals are sense inputs; none is a power output or a hard ground connection.
"""
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'tester12v'
REVISION = 'D1'
NS = uuid.UUID('8a06ce08-1e08-4191-92e2-fb13dbb74d71')
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
ic('MIE1W0505BGLVH',[(1,'GND1','power_in'),(11,'GND1','passive'),(12,'GND1','passive'),(9,'VIN','power_in'),(10,'VIN','passive'),(8,'EN','input')],[(2,'GND2','power_out'),(3,'GND2','passive'),(4,'GND2','passive'),(5,'VOUT','power_out'),(6,'VOUT','passive'),(7,'VSEL','input')],20.32)
ic('TLV75533',[(1,'IN','power_in'),(3,'EN','input'),(2,'GND','power_in')],[(5,'OUT','power_out'),(4,'NC','no_connect')])
ic('OPA320',[(3,'IN+','input'),(4,'IN-','input'),(2,'VSS','power_in')],[(1,'OUT','output'),(5,'VDD','power_in')])
ic('TLV809EA30',[(3,'VDD','power_in'),(1,'GND','power_in')],[(2,'RESET_N','output')])
for n in (4,5):ic('CONN'+str(n),[],[(k,str(k),'passive') for k in range(1,n+1)],5.08)
SYMS['TP']=dict(kind='tp',pins=[dict(n='1',name='1',type='passive',x=0,y=0,angle=90)],w=1,h=1)
SYMS['FLAG']=dict(kind='flag',pins=[dict(n='1',name='pwr',type='power_out',x=0,y=0,angle=90)],w=1,h=1)

F={
 'R':'Resistor_SMD:R_0805_2012Metric', 'C':'Capacitor_SMD:C_0805_2012Metric',
 'DZ':'Diode_SMD:D_SOD-123','LED':'LED_SMD:LED_0805_2012Metric',
 'ADS':'Package_SO:TSSOP-10_3x3mm_P0.5mm',
 'SW':'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
 'ISO':'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
 'DCDC':'Tester:MIE1W0505BGLVH', 'SOT5':'Package_TO_SOT_SMD:SOT-23-5',
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
    mpns={'1M':'0805W8F1004T5E','165k':'RT0805BRD07165KL','10k':'RT0805BRD0710KL','220R':'RC0805FR-07220RL','1k':'RC0805FR-071KL','100k':'RC0805FR-07100KL','2.2k':'RC0805FR-072K2L','4.7k':'RC0805FR-074K7L','10R':'RC0805FR-0710RL'}
    if precision and value=='100k':mpns['100k']='RT0805BRD07100KL'
    return add(ref,'R',value,{1:a,2:b},F['R'],pcb,sch,page,mpns[value],'Yageo','0.1%, 25 ppm/K' if precision else '1%',dnp)
def capacitor(ref,value,a,b,pcb,sch,page='root'):
    mpns={'470p':'0805B471K500NT','1n':'GRM2165C1H102JA01D','10n':'GRM21BR71H103KA01L','100n':'GRM21BR71H104KA01L','1u':'GRM21BR71E105KA99L','10u':'GRM21BR61A106KE19L','22u':'GRM21BR61A226ME44L'}
    return add(ref,'C',value,{1:a,2:b},F['C'],pcb,sch,page,mpns[value],'Murata','Use specified capacitance, voltage and dielectric')


# Rev D uses resistive attenuation, with no power-off analog switches.
ic('B0305S',[(2,'VIN','power_in'),(1,'GND1','power_in')],[(4,'VOUT','power_out'),(3,'GND2','power_out')])
ic('TPS70933',[(1,'IN','power_in'),(3,'EN','input'),(2,'GND','power_in')],[(5,'OUT','power_out'),(4,'NC','no_connect')])
CHANNELS=[]
for bank,cx in enumerate((32,52,72)):
    page='bank'+str(bank+1);first=bank*4+1
    # Rotate each block about its body centre. Reverse contact assignments so
    # the existing copper and user-facing input numbers remain left-to-right.
    add('J'+str(bank+1),'CONN4',f'INPUTS {first}-{first+3}',{k:f'P{first+4-k}' for k in range(1,5)},'Tester:XY350V_3.5_4P',[cx+5.25,52,180],[30,92],page,'XY350V-3.5-4P','Ningbo Xinlaiya Elec.','C557656; 3.5mm pitch, 0.8mm square pins, 1.4mm drill. 14x6.9mm body. WIRE OPENINGS FACE LOWER BOARD EDGE (+Y); footprint contact 1 at right. Input labels increase left-to-right.')
    ap={8:'A3V3',3:'AGND',9:'SDA_ISO',10:'SCL_ISO',2:None,1:['AGND','A3V3','SDA_ISO'][bank]}
    for k in range(4):
        n=first+k;x=cx+(k-1.5)*4;sy=40+k*38
        ra=f'R{3*n-2}';rb=f'R{3*n-1}';rc=f'R{3*n}'
        resistor(ra,'1M',f'P{n}',f'MID{n}',[x,44,90],[78,sy],page)
        resistor(rb,'1M',f'MID{n}',f'A{n}',[x,38,90],[115,sy],page)
        resistor(rc,'4.7k',f'A{n}','VBIAS',[x,32,90],[151,sy+13],page)
        capacitor('C'+str(n),'470p',f'A{n}','AGND',[x,27,90],[191,sy+13],page)
        add('TP'+str(n),'TP',f'A{n}',{1:f'A{n}'},F['TP'],[x,35,0],[192,sy],page)
        ap[4+k]=f'A{n}'
        CHANNELS.append(dict(pin=n,bank=bank,adc=f'U{bank+1}',address=0x48+bank,mux=k,series=[ra,rb],bias=rc,adc_pin=4+k,filter=f'C{n}',testpoint=f'TP{n}'))
    add(f'U{bank+1}','ADS1115','ADS1115IDGSR',ap,F['ADS'],[cx,20,0],[285,88],page,'ADS1115IDGSR','Texas Instruments','PGA +/-1.024V, nominal attenuation 426.5319. Rev D calibration/firmware required.')
    capacitor('C'+str(13+bank),'100n','A3V3','AGND',[cx+5,20,90],[285,130],page)

add('J4','CONN5','DISPLAY HARNESS',{1:'USB5V',2:'USB_GND',3:'HOST3V3',4:'SDA_HOST',5:'SCL_HOST'},F['JST'],[6,46,90],[30,48],mpn='B5B-XH-A(LF)(SN)',maker='JST',note='1=VSYS/5V,2=GND,3=3V3,4=GPIO6 SDA,5=GPIO7 SCL. One USB cable to Waveshare powers both boards.')
add('U4','TLV75533','TLV75533PDBVR',{1:'USB5V_F',2:'USB_GND',3:'USB5V_F',4:None,5:'P3V3'},F['SOT5'],[8,10,0],[112,45],mpn='TLV75533PDBVR',maker='Texas Instruments',note='Primary 3.3V preregulator avoids 4.5V minimum requirement at USB-fed isolated converter. 500mA rating.')
add('U5','TPS70933','TPS70933DBVR',{1:'ISO5V_RAW',2:'AGND',3:None,4:None,5:'A3V3'},F['SOT5'],[29,10,0],[265,45],mpn='TPS70933DBVR',maker='Texas Instruments',note='30V VIN withstands unregulated converter output. EN intentionally floating, internally enabled; do not tie to VIN. Integrated reverse-current blocking.')
add('U6','ISO1640B','ISO1640BDR',{1:'HOST3V3',2:'SDA_HOST',3:'SCL_HOST',4:'USB_GND',5:'AGND',6:'SCL_ISO',7:'SDA_ISO',8:'A3V3'},F['ISO'],[17,27,0],[170,130],mpn='ISO1640BDR',maker='Texas Instruments',note='Functional isolation, 100kHz I2C. Non-isolated host pullups on Waveshare.')
add('U7','B0305S','B0305S-1WR3',{1:'USB_GND',2:'P3V3',3:'AGND',4:'ISO5V_RAW'},'Tester:B0305S_1WR3_EVISUN',[13.19,17,0],[188,45],mpn='B0305S-1WR3',maker='EVISUN',note='C7465186 exact manufacturer. 3.3V input, 5V unregulated output; 20mA minimum output load supplied by five 1k resistors. Through-hole, JLC Economic eligible.')
add('D1','D','LDO reverse protection',{1:'USB5V_F',2:'P3V3'},'Diode_SMD:Nexperia_CFP3_SOD-123W',[8,15,0],[112,83],mpn='PMEG2010ER,115',maker='Nexperia',note='OUT-to-IN reverse-current protection for U4; cathode to USB5V_F')
add('F1','FUSE','250mA PTC',{1:'USB5V',2:'USB5V_F'},'Fuse:Fuse_1206_3216Metric',[9,5,0],[65,48],mpn='1206L025/24YR',maker='Littelfuse',note='USB power path only; not a DUT fuse')
resistor('R37','4.7k','A3V3','VBIAS',[48,6,0],[332,45])
resistor('R38','1k','VBIAS','AGND',[48,10,0],[332,64])
for i in range(5):resistor(f'R{39+i}','1k','ISO5V_RAW','AGND',[22+i*4,6,90],[188+i*42,108])
resistor('R44','4.7k','A3V3','SDA_ISO',[64,6,0],[270,150])
resistor('R45','4.7k','A3V3','SCL_ISO',[64,10,0],[270,169])
resistor('R46','4.7k','HOST3V3','SDA_HOST',[6,25,0],[40,135],dnp=True)
resistor('R47','4.7k','HOST3V3','SCL_HOST',[6,29,0],[40,154],dnp=True)
# Current on the isolated rail is small; a bleed discharges the supply on removal.
resistor('R48','1k','A3V3','AGND',[56,10,0],[333,165])
for ref,value,a,b,pcb,sch in [
 ('C16','10u','USB5V_F','USB_GND',[4,10,90],[75,77]),
 ('C17','100n','USB5V_F','USB_GND',[4,15,90],[75,91]),
 ('C18','10u','P3V3','USB_GND',[10,21,0],[124,105]),
 ('C19','100n','P3V3','USB_GND',[10,24,0],[124,119]),
 ('C20','10u','ISO5V_RAW','AGND',[25,17,90],[225,64]),
 ('C21','100n','ISO5V_RAW','AGND',[25,22,90],[225,78]),
 ('C22','10u','A3V3','AGND',[35,10,90],[292,64]),
 ('C23','100n','A3V3','AGND',[35,15,90],[292,78]),
 ('C24','100n','HOST3V3','USB_GND',[10,28,90],[115,154]),
 ('C25','100n','A3V3','AGND',[24,28,90],[216,155]),
 ('C26','470p','VBIAS','AGND',[48,14,0],[332,83]),
]:capacitor(ref,value,a,b,pcb,sch)
for k,(net,xy,sc) in enumerate([
 ('USB5V',[6,50.5],[30,189]),('USB_GND',[6,53],[65,189]),
 ('HOST3V3',[12.5,34],[100,189]),('P3V3',[14,4],[135,189]),
 ('ISO5V_RAW',[24.7,10],[170,189]),('A3V3',[40,10],[205,189]),
 ('AGND',[77,10],[240,189]),('VBIAS',[55,14],[275,189]),
 ('SDA_ISO',[80,16],[310,189]),('SCL_ISO',[80,23],[345,189])],13):
    add('TP'+str(k),'TP',net,{1:net},F['TP'],[*xy,0],sc)
for k,net in enumerate(('USB5V','USB5V_F','USB_GND','HOST3V3')):
    add('#FLG'+str(k+1),'FLAG',net,{1:net},'',None,[35+50*k,210])
# Regulator enable inputs intentionally unconnected where the vendor permits it.
# Fourth ADC measures a replica open channel, independent of DUT pin states.
# Tie unused analog inputs to AGND as recommended by TI.
add('U8','ADS1115','ADS1115IDGSR',{1:'SCL_ISO',2:None,3:'AGND',4:'REF_ADC',5:'AGND',6:'AGND',7:'AGND',8:'A3V3',9:'SDA_ISO',10:'SCL_ISO'},F['ADS'],[62,20,0],[355,130],mpn='ADS1115IDGSR',maker='Texas Instruments',note='Independent reference monitor at 0x4B, AIN0. Same PGA and conversion timing as input banks; unused inputs tied to AGND.')
resistor('R49','4.7k','VBIAS','REF_ADC',[60,14,0],[270,210])
capacitor('C27','100n','A3V3','AGND',[67,20,90],[355,161])
capacitor('C28','470p','REF_ADC','AGND',[65,14,0],[332,210])
from jlc_catalog import apply
apply(PARTS)
SCOPE={
 'revision':REVISION,'status':'ENGINEERING DRAFT - NOT RELEASED FOR ORDER',
 'mechanical_change':'J1-J3 rotated 180 degrees with wire entry toward lower edge (+Y); input labels 1-12 and electrical paths unchanged. Uses Rev D firmware.',
 'nominal_voltage_V':12,'intended_measurement_V':[0,18],
 'input_count':12,'all_assignment_identification_target_V':[9,18],'input_scope':'One common floating DC supply; any positive/return/open assignment, with at least one positive and one return for live classification. Measure only; no power outputs or continuity test.',
 'power':'One USB cable to Waveshare ESP32-S3-LCD-1.28; five-wire harness. USB5V preregulated to 3.3V before isolation.',
 'display':'Waveshare ESP32-S3-LCD-1.28 non-touch; external MCU/display module',
 'isolation':'Functional isolation from USB; not mains or CAT rated.',
 'accuracy':'Target +/-0.15V near 12V after room-temperature calibration; not physically verified.',
 'nominal_gain':1+2e6/4700,'adc_FSR_V':1.024,
 'board_mm':[86,62],'layers':2,'thickness_mm':1.6,
 'calibration_required':True,'bench_verified':False,
 '48V_note':'Calculation stress only, not a survival rating.'}
