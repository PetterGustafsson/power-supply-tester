"""JLC public library snapshot, read through its live search UI on 2026-09-30.

Prices are displayed USD 1-piece tier (preorder estimates where stock is zero).
Stock is not reserved. Quantities exclude assembly attrition. Not a quote.
"""
from urllib.parse import quote

# MPN, JLC code, category, displayed stock, USD/unit, package, specification.
DATA = [
 ('XY350V-3.5-4P','C557656','Extended',5706,.2981,'TH 3.5mm','XINYA 4-way screw terminal, 14x6.9mm, 0.8mm square pins; Economic/Standard wave soldering'),
 ('0805W8F1004T5E','C17514','Basic',2424518,.0043,'0805','1M; 1%; 100ppm/K; 125mW; 150V'),
 ('B0305S-1WR3','C7465186','Extended',1632,1.1215,'SIP 11.68x6mm','EVISUN; 3.3V input, 5V unregulated output, 20mA minimum load; Economic/Standard wave soldering'),
 ('TPS70933DBVR','C89347','Extended',22547,.3345,'SOT-23-5','TI exact part; 30V input, 150mA, reverse blocking; Economic/Standard'),
 ('0805B471K500NT','C1743','Basic',297164,.0095,'0805','470pF; 10%; 50V; X7R'),
 ('BZT52C12','C19077410','Promotional Extended',543166,.0168,'SOD-123','12V zener; 350mW; leakage <=100nA at 8V; 11.4-12.6V at 5mA'),
 ('MIE1W0505BGLVH-3R-Z','C22419841','Extended',2143,1.9358,'LGA-12 4x5mm','MPS regulated isolated 5V 1W; VIN 4.5-5.5V; VSEL tied to VOUT'),
 ('RT0805BRD07165KL','C865215','Extended',2403,.0456,'0805','165k; 0.1%; 25ppm/K; 125mW; 150V'),
 ('RT0805BRD0710KL','C110775','Extended',865510,.0400,'0805','10k; 0.1%; 25ppm/K; 125mW; 150V'),
 ('RT0805BRD07100KL','C122537','Extended',423155,.0404,'0805','100k; 0.1%; 25ppm/K; 125mW; 150V'),
 ('RC0805FR-07220RL','C114519','Extended',418019,.0062,'0805','220R; 1%; 100ppm/K; 125mW; 150V'),
 ('RC0805FR-074K7L','C60816','Extended',4262890,.0077,'0805','4.7k; 1%; 100ppm/K; 125mW; 150V'),
 ('RC0805FR-071KL','C95781','Extended',3318528,.0037,'0805','1k; 1%; 100ppm/K; 125mW; 150V'),
 ('RC0805FR-07100KL','C96346','Extended',828383,.0073,'0805','100k; 1%; 100ppm/K; 125mW; 150V'),
 ('0805W8F2200T5E','C17557','Basic',901910,.0054,'0805','220R; 1%; 100ppm/K; 125mW; 150V'),
 ('0805W8F4701T5E','C17673','Basic',5092033,.0050,'0805','4.7k; 1%; 100ppm/K; 125mW; 150V'),
 ('0805W8F1001T5E','C17513','Basic',31226169,.0040,'0805','1k; 1%; 100ppm/K; 125mW; 150V'),
 ('0805W8F1003T5E','C149504','Basic',4232521,.0059,'0805','100k; 1%; 100ppm/K; 125mW; 150V'),
 ('GRM2165C1H102JA01D','C86030','Extended',0,.0109,'0805','1nF; 5%; 50V; C0G; preorder MOQ 799'),
 ('GRM21BR71H104KA01L','C77082','Extended',233613,.0290,'0805','100nF; 10%; 50V; X7R'),
 ('GRM21BR61A106KE19L','C77073','Extended',9009,.0633,'0805','10uF; 10%; 10V; X5R'),
 ('GRM21BR71E105KA99L','C77080','Extended',18836,.0581,'0805','1uF; 10%; 25V; X7R'),
 ('GRM21BR61A226ME44L','C441864','Extended',6627,.1993,'0805','22uF; 20%; 10V; X5R'),
 ('CC0805JRNPO9BN102','C62774','Extended',1080509,.0096,'0805','1nF; 5%; 50V; C0G/NP0'),
 ('CC0805KRX7R9BB104','C49678','Basic',19276466,.0189,'0805','100nF; 10%; 50V; X7R'),
 ('CL21A106KAYNNNE','C15850','Basic',5006159,.0651,'0805','10uF; 10%; 25V; X5R'),
 ('CL21B105KBFNNNE','C28323','Basic',2300572,.0399,'0805','1uF; 10%; 50V; X7R'),
 ('CL21A226MAQNNNE','C45783','Basic',4005225,.2201,'0805','22uF; 20%; 25V; X5R; manufacturer NRND'),
 ('ADS1115IDGSR','C37593','Extended',26773,1.2190,'VSSOP-10','TI ADS1115; exact original'),
 ('ADG4612BRUZ','C657391','Extended',0,2.7916,'TSSOP-16','ADI power-off protected quad switch; preorder MOQ 4; est. 9 days'),
 ('ADG4612BRUZ-REEL7','C207399','Extended',41,6.7450,'TSSOP-16','Same ADG4612BRUZ die and RU-16 package; reel packaging'),
 ('R05C05TE05S-R','C5338283','Extended',0,10.4867,'SOIC-16-300mil','RECOM isolated 5V converter; preorder MOQ 1; lead time not displayed'),
 ('ISO1640BDR','C5122339','Extended',4169,1.8708,'SOIC-8','TI 8-pin B variant; exact original'),
 ('TLV75533PDBVR','C404027','Extended',137124,.1421,'SOT-23-5','TI 3.3V LDO; exact original'),
 ('OPA320AIDBVR','C92494','Extended',30656,1.3588,'SOT-23-5','TI OPA320; exact original'),
 ('TLV809EA30DBZR','C2860914','Extended',800,.2141,'SOT-23','TI 3.08V supervisor; exact original'),
 ('BZT52H-C12,115','C282531','Extended',37634,.0421,'SOD-123F','Nexperia 12V zener; exact original'),
 ('PMEG2010ER,115','C82288','Extended',12880,.1788,'SOD-123W','Nexperia Schottky; exact original'),
 ('1206L025/24YR','C3762322','Extended',5149,.2396,'1206','Littelfuse 250mA PTC; R1max 2.3ohm; exact original'),
 ('1984633','C5144867','Extended',65,1.5603,'TH 3.5mm','Phoenix 4-way horizontal terminal; exact original'),
 ('B5B-XH-A(LF)(SN)','C157991','Extended',71511,.0852,'TH 2.5mm','JST XH 5-way vertical; exact original'),
]
CATALOG = {d[0]: dict(zip(('mpn','lcsc','category','stock','unit_usd','package','spec'),d)) for d in DATA}
for mpn, row in CATALOG.items():
    row.update(checked='2026-09-30',source='https://jlcpcb.com/parts/componentSearch?searchTxt='+quote(mpn),
               price_basis='1+ displayed' if row['stock'] else 'Preorder estimate',
               moq=799 if mpn=='GRM2165C1H102JA01D' else 4 if mpn=='ADG4612BRUZ' else 1,
               status='IN STOCK' if row['stock'] else 'PREORDER')

# Approved package-equivalent substitutions; circuit values and footprints stay fixed.
SUBSTITUTIONS = {
 'RC0805FR-07220RL':('0805W8F2200T5E','UNI-ROYAL','Basic; same 1%, 100ppm/K, 125mW, 150V rating'),
 'RC0805FR-074K7L':('0805W8F4701T5E','UNI-ROYAL','Basic; same 1%, 100ppm/K, 125mW, 150V rating'),
 'RC0805FR-071KL':('0805W8F1001T5E','UNI-ROYAL','Basic; same 1%, 100ppm/K, 125mW, 150V rating'),
 'RC0805FR-07100KL':('0805W8F1003T5E','UNI-ROYAL','Basic; same 1%, 100ppm/K, 125mW, 150V rating'),
 'GRM2165C1H102JA01D':('CC0805JRNPO9BN102','Yageo','Stocked replacement; 1nF, 5%, 50V, C0G/NP0 preserved'),
 'GRM21BR71H104KA01L':('CC0805KRX7R9BB104','Yageo','Basic; 100nF, 10%, 50V, X7R preserved'),
 'GRM21BR61A106KE19L':('CL21A106KAYNNNE','Samsung Electro-Mechanics','Basic; 10uF, 10%, X5R; voltage rating increased to 25V'),
 'GRM21BR71E105KA99L':('CL21B105KBFNNNE','Samsung Electro-Mechanics','Basic; 1uF, 10%, X7R; voltage rating increased to 50V'),
 'GRM21BR61A226ME44L':('CL21A226MAQNNNE','Samsung Electro-Mechanics','Basic; 22uF, 20%, X5R; 25V. NRND but deep JLC stock for prototype; requalify for production'),
 'ADG4612BRUZ':('ADG4612BRUZ-REEL7','Analog Devices','In-stock tape-and-reel packaging; same silicon, pinout and TSSOP-16'),
}

def apply(parts):
    for p in parts:
        old=p['mpn']
        if old=='0805W8F1004T5E':p['maker']='UNI-ROYAL'
        if old=='0805B471K500NT':
            p['maker']='Fenghua'
            p['note']='470pF +/-10%, 50V X7R; Rev D candidate model bounds total input capacitance at 1nF'
        
        if old in SUBSTITUTIONS:
            p['mpn'],p['maker'],why=SUBSTITUTIONS[old]
            p['note']+=' | JLC: '+why
        if p['mpn'] in CATALOG:
            p['lcsc']=CATALOG[p['mpn']]['lcsc']
            p['jlc_category']=CATALOG[p['mpn']]['category']
