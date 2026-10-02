"""Rev E component/pin manifest, derived from Rev D2. Coordinates in mm.

Electrical scope: 5-V-powered CM5 nominal-12-V common-supply pin detector. All twelve
terminals are sense inputs; none is a power output or a hard ground connection.
"""
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'tester12v'
REVISION = 'E'
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
 'solder_mask':'Black, both sides','silkscreen':'White, both sides; J4 numbered signal labels and ESP32 wiring key',
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

# Rev E: preserve the validated twelve-channel sensing topology, replace the
# external ESP32 harness and the unregulated power chain with a CM5 carrier.
# No existing revision is edited by this generator.
remove={'J4','U4','U5','U7','D1','F1','R39','R40','R41','R42','R43','R46','R47',
        'C18','C19','C20','C21','C22','C23','TP13','TP14','TP15','TP16','TP17'}
PARTS[:]=[p for p in PARTS if p['ref'] not in remove and not p['ref'].startswith('#')]
for p in PARTS:
    p['pins']={k:('HGND' if v=='USB_GND' else v) for k,v in p['pins'].items()}
    if p['pcb']:p['pcb'][0]+=60
    if p['ref']=='U6':p['pcb']=[76.5,27,0];p['note']='Isolated I2C, GPIO2/3 host side. CM5 internal 1.8k pull-ups; isolated 4.7k pull-ups. 100kHz.'
    if p['ref']=='C24':p['pcb']=[70,28,90]
    if p['ref']=='C25':p['pcb']=[84,28,90]
    if p['ref'] in ('C16','C17'):p['pins']['1']='V5';p['pins']['2']='HGND';p['pcb'][0]=69
    if p['ref']=='TP18':p['pcb']=[91,5,0]
    if p['ref']=='TP19':p['pcb']=[137,10,0]
    if p['ref']=='TP20':p['pcb']=[115,14,0]
    if p['ref']=='TP21':p['pcb']=[140,16,0]
    if p['ref']=='TP22':p['pcb']=[140,23,0]

ic('CONN2',[],[(1,'1','passive'),(2,'2','passive')],5.08)
ic('CONN3',[],[(i,str(i),'passive') for i in range(1,4)],5.08)
ic('CONN12',[(i,str(i),'passive') for i in range(1,7)],[(i,str(i),'passive') for i in range(7,13)],7.62)
ic('PMOS8',[(i,'S','passive') for i in (1,2,3)]+[(4,'G','input')],[(i,'D','passive') for i in (5,6,7,8)])

add('J4','CONN4','5 V POWER INPUT',{1:'HGND',2:'HGND',3:'V5_IN',4:'V5_IN'},
    'Tester:XY350V_3.5_4P',[60.25,52,180],[30,48],mpn='XY350V-3.5-4P',maker='Ningbo Xinlaiya Elec.',
    note='Same stocked terminal as J1-J3: no extra Extended SKU. Viewed from top, left-to-right: +5V,+5V,GND,GND. Regulated 5.1V recommended; never DUT voltage.')
add('F1','FUSE','5A input fuse',{1:'V5_IN',2:'V5_F'},'Fuse:Fuse_1206_3216Metric',[56,42,0],[72,48],
    mpn='JFC1206-1500FS',maker='Shenzhen JDT Fuse',note='5A fast fuse. Does not establish an allowed 5A current through CM5 sockets.')
add('Q1','PMOS8','AO4409 UMW',{1:'V5',2:'V5',3:'V5',4:'HGND',5:'V5_F',6:'V5_F',7:'V5_F',8:'V5_F'},
    'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',[60,35,0],[120,48],mpn='AO4409',maker='UMW',
    note='C347462 exact manufacturer; max 9.5mohm at VGS=-4.5V,25C. Reverse polarity: drain to fused input, source to load, gate grounded. No overvoltage protection.')
add('U7','MIE1W0505BGLVH','MIE1W0505BGLVH-3R-Z',
    {1:'HGND',11:'HGND',12:'HGND',9:'V5',10:'V5',8:'V5',2:'AGND',3:'AGND',4:'AGND',5:'A3V3_RAW',6:'A3V3_RAW',7:'AGND'},
    'Tester:MIE1W0505BGLVH',[76.5,10,90],[205,45],mpn='MIE1W0505BGLVH-3R-Z',maker='Monolithic Power Systems',
    note='VSEL=GND2 selects regulated 3.3V. EN=VIN. No minimum-load preload. 30uF nominal output capacitance, plus 100nF; 10ohm/10uF analog rail filter. Functional isolation only.')
add('R50','R','10R',{1:'A3V3_RAW',2:'A3V3'},F['R'],[83,10,0],[277,45],mpn='0805W8F100JT5E',maker='UNI-ROYAL',note='Basic 10ohm analog supply RC filter. DC/ripple/rail-collapse behaviour needs bench measurement.')
for ref,value,a,b,xy,sc in [
 ('C18','10u','V5','HGND',[59,28,0],[30,100]),
 ('C19','100n','V5','HGND',[65,28,0],[75,100]),
 ('C20','10u','A3V3_RAW','AGND',[83,16,0],[205,92]),
 ('C21','100n','A3V3_RAW','AGND',[83,20,0],[248,92]),
 ('C22','10u','A3V3','AGND',[89,10,90],[277,83]),
 ('C23','100n','A3V3','AGND',[95,10,90],[277,102]),
 ('C29','10u','A3V3_RAW','AGND',[88,16,0],[205,112]),
 ('C30','10u','A3V3_RAW','AGND',[93,16,0],[248,112]),
 ('C31','10u','V5','HGND',[2.5,40,90],[30,120]),
 ('C32','10u','V5','HGND',[2.5,45,90],[75,120]),
 ('C33','10u','V5','HGND',[2.5,50,90],[30,140]),
 ('C34','100n','HOST3V3','HGND',[2.5,35,90],[75,140]),
]:capacitor(ref,value,a,b,xy,sc)

# Published CM5 pin numbering. The second socket uses local contacts 1..100
# corresponding to module pins 101..200. Unused interfaces are explicitly NC.
import re
cm_text=(ROOT/'sources/CM5.txt').read_text()
pin_table=cm_text.split('\n4.2. Pinout\n',1)[1].split('\n4.2.1.',1)[0]
pin_names={int(n):name for n,name in re.findall(r'^\s*(\d{1,3})\s+(\S+)\s+.*$',pin_table,re.M) if 1<=int(n)<=200}
assert len(pin_names)==200,('CM5 pin table incomplete',len(pin_names))
cm={n:None for n in range(1,201)}
for n,name in pin_names.items():
    if name=='GND':cm[n]='HGND'
for n in (77,79,81,83,85,87):cm[n]='V5'
for n in (78,84,86):cm[n]='HOST3V3'
cm.update({56:'SCL_HOST',58:'SDA_HOST',38:'SPI_SCLK',40:'SPI_MISO',44:'SPI_MOSI',39:'SPI_CE0',
           41:'GPIO25',45:'GPIO24',49:'GPIO18',55:'UART_TX',51:'UART_RX',92:'PWR_BUTTON'})
for ref,start,xy,sc in [('J5',1,[7.5,34.5,0],[115,116]),('J6',101,[41.5,34.5,0],[300,116])]:
    def pin_type(n):
        if n in (77,79,81,83,85,87):return 'power_in'
        if n==84:return 'power_out'
        if n==78:return 'power_in'
        return 'passive'
    sym='CM5_'+ref
    ic(sym,[(k,pin_names[start+k-1],pin_type(start+k-1)) for k in range(1,51)],
           [(k,pin_names[start+k-1],pin_type(start+k-1)) for k in range(51,101)],35.56)
    add(ref,sym,'CM5 SOCKET '+str(start)+'-'+str(start+99),{k:cm[start+k-1] for k in range(1,101)},
        'Tester:CM5_SOCKET_'+ref,xy,sc,page='cm5',mpn='10164227-1001A1RLF',maker='Amphenol ICC',
        note='Raspberry Pi recommended 1.5mm socket. No components under module. 300mA/contact rating: six parallel 5V pins, not a 5A-per-module claim. CM5 with eMMC; preimage on an external IO carrier.')
add('J7','CONN12','HOST SPI / I2C',{1:'HGND',2:'HOST3V3',3:'SPI_SCLK',4:'SPI_MOSI',5:'SPI_MISO',6:'SPI_CE0',7:'GPIO25',8:'GPIO24',9:'GPIO18',10:'SDA_HOST',11:'SCL_HOST',12:'V5'},
    'Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical',[54,8,0],[90,208],page='cm5',
    note='Optional user-fitted 2x6 header. Host 3.3V logic, host ground, no isolation at this connector. Can connect a compatible SPI LCD or separately specified sensor/emitter. Not a power stimulus for DUT.',dnp=True)
add('J8','CONN2','POWER BUTTON',{1:'PWR_BUTTON',2:'HGND'},'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    [66,43,0],[220,208],page='cm5',note='Optional normally-open momentary button across these pads. CM5 handles safe OS shutdown where configured.',dnp=True)
add('J9','CONN3','UART CONSOLE',{1:'HGND',2:'UART_TX',3:'UART_RX'},'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    [52,30,0],[335,208],page='cm5',note='Optional 3.3V GPIO14/15 console. No USB connector. Do not apply 5V logic or power through UART.',dnp=True)
for i,(net,xy,sc) in enumerate([('V5_IN',[50,43],[30,178]),('V5',[48,41],[72,178]),('HGND',[70,38],[114,178]),('HOST3V3',[2.5,30],[156,178]),('A3V3_RAW',[98,16],[198,178])],23):
    add('TP'+str(i),'TP',net,{1:net},F['TP'],[*xy,0],sc)
for i,net in enumerate(('V5','HGND','A3V3')):
    add('#FLG'+str(i+1),'FLAG',net,{1:net},'',None,[30+i*50,233])
apply(PARTS)
SCOPE.update(revision=REVISION,status='ENGINEERING PROTOTYPE - NOT RELEASED FOR ORDER',
 power='External regulated 5V supply, nominal 5.1V; 5A source capability. CM5 socket currents require validation. F1 5A fuse and Q1 reverse-polarity protection.',
 host='Compute Module 5, eMMC and Wi-Fi variant assumed; CM5102016 (2GB/16GB) candidate. Module purchased and installed separately.',
 display='External compatible SPI display on optional J7; existing Waveshare ESP32 display is not a plug-in CM5 screen.',
 mechanical_change='146x62mm carrier; module 40x55mm with four M2.5 holes; no components under its 1.5mm stacking area.',
 isolation='Functional isolation from CM5/5V input via U6/U7; no mains or CAT rating.',
 board_mm=[146,62],interfaces={'measurement':'100kHz isolated I2C, GPIO2/3; four ADS1115 at 0x48..0x4B',
 'expansion':'Host SPI0 and I2C at J7; 3.3V logic only'},
 assembly_quantity_basis=2,usb_connector=False,sd_socket=False,emitter='No DUT stimulus; output requirements unspecified.',
 boot='Preimaged eMMC using an external CM5 IO board; Wi-Fi provisioning in image. CM5 Lite cannot boot on this carrier.',
 assumptions=['eMMC/Wi-Fi CM5; user variant question unanswered at design time.','Measurement-only DUT circuitry retained.'],
 no_under_module_components=True)
