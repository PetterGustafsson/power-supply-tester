"""Generate native KiCad 9 schematic, board placement, libraries, BOM and netlist.

Run with KiCad's bundled Python (pcbnew). Routing is a separate explicit step;
this script never claims that a placement-only board is fabrication-ready.
"""
import csv, json, math, shutil
from pathlib import Path
import pcbnew as pcb
from design import ROOT, PROJECT, PARTS, SYMS, CHANNELS, SCOPE, uid

KROOT=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
FPDIR=ROOT/'libraries'/'Tester.pretty'
FPDIR.mkdir(parents=True,exist_ok=True)

def q(s):return json.dumps(str(s),ensure_ascii=False)
def eff(size=1.0,hide=False,justify=''):
    return f'(effects (font (size {size} {size}))'+(' (hide yes)' if hide else '')+(f' (justify {justify})' if justify else '')+')'
def snap(v):return round(round(v/1.27)*1.27,4)
def wire(a,b,key):return f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid(key)}))'

def symbol_def(name, full=False):
    s=SYMS[name]; libname='Tester:'+name if full else name
    kind=s['kind'];prefix='#FLG' if kind=='flag' else ('TP' if kind=='tp' else ('U' if kind=='ic' else ('C' if kind=='c' else 'R')))
    h=s['h']/2; w=s['w']/2
    parts=[f'(symbol {q(libname)} (pin_names (offset 0.508)'+(' (hide yes)' if kind!='ic' else '')+') (pin_numbers'+(' (hide yes)' if kind!='ic' else '')+') (in_bom '+('no' if kind in ('flag','tp') else 'yes')+') (on_board '+('no' if kind=='flag' else 'yes')+')',
     f'(property "Reference" {q(prefix)} (at 0 {h+3.81} 0) {eff()})',
     f'(property "Value" {q(name)} (at 0 {h+1.27} 0) {eff()})',
     f'(property "Footprint" "" (at 0 0 0) {eff(hide=True)})',
     f'(symbol {q(name+"_0_1")}']
    if kind in ('r','ic'):
        parts.append(f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type {"background" if kind=="ic" else "none"})))')
    elif kind=='c':
        for x in (-0.8,0.8):parts.append(f'(polyline (pts (xy {x} -2) (xy {x} 2)) (stroke (width 0.254) (type default)) (fill (type none)))')
        for a,b in [(-2.54,-0.8),(0.8,2.54)]:parts.append(f'(polyline (pts (xy {a} 0) (xy {b} 0)) (stroke (width 0) (type default)) (fill (type none)))')
    elif kind in ('z','d'):
        parts.append('(polyline (pts (xy 1.27 -1.778) (xy -1.27 0) (xy 1.27 1.778) (xy 1.27 -1.778)) (stroke (width 0.254) (type default)) (fill (type none)))')
        parts.append('(polyline (pts (xy -2 -1.778) (xy -1.27 -1.778) (xy -1.27 1.778) (xy -0.5 1.778)) (stroke (width 0.254) (type default)) (fill (type none)))')
        for a,b in [(-2.54,-1.27),(1.27,2.54)]:parts.append(f'(polyline (pts (xy {a} 0) (xy {b} 0)) (stroke (width 0) (type default)) (fill (type none)))')
    elif kind in ('tp','flag'):
        parts.append('(circle (center 0 0.635) (radius 0.635) (stroke (width 0.15) (type default)) (fill (type none)))')
    parts.append(')')
    parts.append(f'(symbol {q(name+"_1_1")}')
    for p in s['pins']:
        length=0 if kind in ('tp','flag') else 2.54
        parts.append(f'(pin {p["type"]} line (at {p["x"]} {p["y"]} {p["angle"]}) (length {length}) (name {q(p["name"])} {eff(0.95)}) (number {q(p["n"])} {eff(0.9)}))')
    parts.extend([')',')']);return '\n'.join(parts)

def schematic(page,title):
    rootid=uid('root'); pageid=rootid if page=='root' else uid(page)
    entries=[p for p in PARTS if p['page']==page]
    out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {pageid}) (paper "A3")',
     f'(title_block (title {q(title)}) (date "2026-09-30") (rev "C") (company "Power supply tester") (comment 1 "12 V nominal DC | USB-powered measurement only") (comment 2 "Prototype: bench validation required"))',
     '(lib_symbols']
    out.extend(symbol_def(n,True) for n in sorted(set(p['sym'] for p in entries)))
    out.append(')')
    for part in entries:
        name=part['sym'];s=SYMS[name];x,y=map(snap,part['sch']);a=part['schrot']
        ref=part['ref'];h=s['h']/2
        path='/'+rootid+('' if page=='root' else '/'+uid('sheet-'+page))
        out.extend([f'(symbol (lib_id {q("Tester:"+name)}) (at {x} {y} {a}) (unit 1) (in_bom {"no" if ref.startswith(("#","TP")) else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp {"yes" if part["dnp"] else "no"}) (uuid {part["uuid"]})',
          f'(property "Reference" {q(ref)} (at {x} {y-h-4.445} 0) {eff(1.0,ref.startswith("#"))})',
          f'(property "Value" {q(part["value"])} (at {x} {y-h-2.54} 0) {eff(0.95)})',
          f'(property "Footprint" {q(part.get("local_fp",part["fp"]))} (at {x} {y} 0) {eff(hide=True)})',
          f'(property "MPN" {q(part["mpn"])} (at {x} {y} 0) {eff(hide=True)})',
          f'(property "LCSC" {q(part.get("lcsc",""))} (at {x} {y} 0) {eff(hide=True)})',
          f'(property "Manufacturer" {q(part["maker"])} (at {x} {y} 0) {eff(hide=True)})',
          f'(property "Notes" {q(part["note"])} (at {x} {y} 0) {eff(hide=True)})'])
        for pin in s['pins']:out.append(f'(pin {q(pin["n"])} (uuid {uid(ref+"-pin-"+pin["n"])}))')
        out.append(f'(instances (project {q(PROJECT)} (path {q(path)} (reference {q(ref)}) (unit 1)))))')
        for p in s['pins']:
            net=part['pins'][p['n']]; rad=math.radians(a)
            px=x+p['x']*math.cos(rad)-p['y']*math.sin(rad)
            py=y-(p['x']*math.sin(rad)+p['y']*math.cos(rad))
            px,py=round(px,4),round(py,4)
            if net is None:
                out.append(f'(no_connect (at {px} {py}) (uuid {uid(ref+"-nc-"+p["n"])}))');continue
            if s['kind'] in ('tp','flag'):
                end=(px,round(py+5.08,4));orient=0;justify='left'
            else:
                ang=(p['angle']+a)%360; dx=-math.cos(math.radians(ang))*3.81;dy=math.sin(math.radians(ang))*3.81
                end=(round(px+dx,4),round(py+dy,4));orient=0 if dx>=0 else 180;justify='left' if dx>=0 else 'right'
            out.append(wire((px,py),end,ref+'-'+p['n']+'-wire'))
            out.append(f'(global_label {q(net)} (shape passive) (at {end[0]} {end[1]} {orient}) {eff(0.9,False,justify)} (uuid {uid(ref+"-label-"+p["n"])}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {end[0]} {end[1]} 0) {eff(hide=True)}))')
    def text(t,x,y,size=1.4):out.append(f'(text {q(t)} (at {x} {y} 0) {eff(size,False,"left")} (uuid {uid(page+t)}))')
    if page=='root':
        text('CONTROLLER / USB',22,18,2);text('ISOLATED POWER + I2C',107,18,2);text('ANALOG POWER / REFERENCE',214,18,2)
        text('Waveshare ESP32-S3-LCD-1.28\nJ4: 1=5V, 2=GND, 3=3V3, 4=SDA/GPIO6, 5=SCL/GPIO7\nR46/R47 DNP: host module already has 4.7k pull-ups.',22,98,1.1)
        text('All DUT pins remain isolated from USB ground.\nFunctional isolation only: not a mains/CAT-rated instrument.',22,222,1.2)
        for k in range(3):
            x=25+125*k;y=230;child='bank'+str(k+1)
            out.append(f'(sheet (at {x} {y}) (size 107.95 20.32) (fields_autoplaced) (stroke (width 0.15) (type default)) (fill (color 0 0 0 0.0)) (uuid {uid("sheet-"+child)}) (property "Sheetname" "Inputs {k*4+1}-{k*4+4}" (at {x} {y-1.27} 0) {eff()}) (property "Sheetfile" "{child}.kicad_sch" (at {x} {y+21.59} 0) {eff()}) (instances (project {q(PROJECT)} (path "/{rootid}" (page "{k+2}")))))')
    else:
        text(title.upper(),20,18,2)
        text('Two 1M resistors limit input current.\n4.7k returns each ADC input to passive VBIAS.\nNo analog switch or active input clamp.\nInput attenuation also applies without USB power.',25,215,1.3)
        text('470pF filters are on the ADC side.\nNominal attenuation = 426.5319. PGA = +/-1.024V.\nMeasure one live DC pair, other terminals open.',230,215,1.3)
        text('12V nominal; 0-18V intended measurement range.\n48V is a calculation stress, not a survival rating.\nDo not connect any terminal directly to AGND or USB_GND.',25,242,1.2)
    if page=='root':out.append(f'(sheet_instances (path "/" (page "1")))')
    out.append(')')
    dest=ROOT/(PROJECT+'.kicad_sch' if page=='root' else page+'.kicad_sch')
    dest.write_text('\n'.join(out)+'\n')

def mm(v):return pcb.FromMM(v)
def vec(x,y):return pcb.VECTOR2I(mm(x),mm(y))
def fp_line(fp,x1,y1,x2,y2,layer,width=.12):
    s=pcb.PCB_SHAPE(fp);s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(vec(x1,y1));s.SetEnd(vec(x2,y2));s.SetLayer(layer);s.SetWidth(mm(width));fp.Add(s)

def make_b0305():
    fp=pcb.FOOTPRINT(None);fp.SetFPID(pcb.LIB_ID('Tester','B0305S_1WR3_EVISUN'))
    fp.SetLibDescription('EVISUN B_S-1WR3 V1.0 p4. Pin1=-VIN,2=+VIN,3=-VOUT,4=+VOUT; pin1 origin; 1mm drills; 2.54mm pitch.')
    fp.SetAttributes(pcb.FP_THROUGH_HOLE)
    for n in range(1,5):
        pad=pcb.PAD(fp);pad.SetNumber(str(n));pad.SetAttribute(pcb.PAD_ATTRIB_PTH);pad.SetShape(pcb.PAD_SHAPE_RECT if n==1 else pcb.PAD_SHAPE_CIRCLE)
        pad.SetPosition(vec((n-1)*2.54,0));pad.SetSize(vec(1.7,1.7));pad.SetDrillSize(vec(1,1))
        # Only copper and mask, never paste for through-hole pads.
        ls=pcb.LSET();[ls.AddLayer(x) for x in (pcb.F_Cu,pcb.B_Cu,pcb.F_Mask,pcb.B_Mask)];pad.SetLayerSet(ls);fp.Add(pad)
    for layer,x1,y1,x2,y2 in [(pcb.F_Fab,-2.03,-5.1,9.65,.9),(pcb.F_SilkS,-2.13,-5.2,9.75,1.1),(pcb.F_CrtYd,-2.53,-5.6,10.15,1.6)]:
        for a,b in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:fp_line(fp,*a,*b,layer,.05 if layer==pcb.F_CrtYd else .12)
    fp_line(fp,-1.3,.9,-1.3,-.2,pcb.F_SilkS)
    fp.Reference().SetPosition(vec(3.81,-6.2));fp.Value().SetPosition(vec(3.81,2.5))
    pcb.PCB_IO_MGR.PluginFind(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(FPDIR),fp)

def make_terminal():
    fp=pcb.FOOTPRINT(None);fp.SetFPID(pcb.LIB_ID('Tester','XY350V_3.5_4P'))
    fp.SetLibDescription('XINYA XY350V-3.5-4P drawing C557656: 14x6.9x8.6mm body, 0.8mm square pins; 1.4mm drills. Pin1 origin.')
    fp.SetAttributes(pcb.FP_THROUGH_HOLE)
    for n in range(1,5):
        pad=pcb.PAD(fp);pad.SetNumber(str(n));pad.SetAttribute(pcb.PAD_ATTRIB_PTH);pad.SetShape(pcb.PAD_SHAPE_RECT if n==1 else pcb.PAD_SHAPE_CIRCLE)
        pad.SetPosition(vec((n-1)*3.5,0));pad.SetSize(vec(2.4,2.4));pad.SetDrillSize(vec(1.4,1.4))
        ls=pcb.LSET();[ls.AddLayer(x) for x in (pcb.F_Cu,pcb.B_Cu,pcb.F_Mask,pcb.B_Mask)];pad.SetLayerSet(ls);fp.Add(pad)
    for layer,x1,y1,x2,y2 in [(pcb.F_Fab,-1.75,-3.45,12.25,3.45),(pcb.F_SilkS,-1.85,-3.55,12.35,3.55),(pcb.F_CrtYd,-2.5,-4,13,4)]:
        for a,b in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:fp_line(fp,*a,*b,layer,.05 if layer==pcb.F_CrtYd else .12)
    fp_line(fp,-1.85,2.7,-1,3.55,pcb.F_SilkS)
    pcb.PCB_IO_MGR.PluginFind(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(FPDIR),fp)

def copy_libraries():
    make_b0305();make_terminal()
    for p in PARTS:
        if not p['fp']:p['local_fp']='';continue
        lib,name=p['fp'].split(':',1)
        if lib!='Tester':shutil.copyfile(KROOT/'footprints'/(lib+'.pretty')/(name+'.kicad_mod'),FPDIR/(name+'.kicad_mod'))
        p['local_fp']='Tester:'+name
    (ROOT/'libraries'/'Tester.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(symbol_def(n) for n in SYMS)+'\n)\n')
    (ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Tester") (type "KiCad") (uri "${KIPRJMOD}/libraries/Tester.kicad_sym") (options "") (descr "Local verified pin definitions")))\n')
    (ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Tester") (type "KiCad") (uri "${KIPRJMOD}/libraries/Tester.pretty") (options "") (descr "Project footprint copies")))\n')

def board_text(b,t,x,y,size=1,layer=pcb.F_SilkS,angle=0):
    txt=pcb.PCB_TEXT(b);txt.SetText(t);txt.SetPosition(vec(x,y));txt.SetTextSize(vec(size,size));txt.SetTextThickness(mm(.15));txt.SetLayer(layer);txt.SetMirrored(layer==pcb.B_SilkS);txt.SetTextAngle(pcb.EDA_ANGLE(angle,pcb.DEGREES_T));b.Add(txt)

def make_board():
    b=pcb.BOARD();b.SetCopperLayerCount(2)
    ds=b.GetDesignSettings();ds.SetBoardThickness(mm(1.6));ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.2);ds.m_ViasMinSize=mm(.6);ds.m_MinThroughDrill=mm(.3);ds.m_CopperEdgeClearance=mm(.3);ds.m_HoleToHoleMin=mm(.25)
    ds.m_NetSettings.GetDefaultNetclass().SetClearance(mm(.2));ds.m_SilkClearance=mm(.15);ds.m_MinSilkTextHeight=mm(.8);ds.m_MinSilkTextThickness=mm(.12)
    nets={}
    for n in sorted({v for p in PARTS for v in p['pins'].values() if v}):
        net=pcb.NETINFO_ITEM(b,n);b.Add(net);nets[n]=net
    for p in PARTS:
        if not p['pcb']:continue
        lib,name=p['local_fp'].split(':',1);fp=pcb.FootprintLoad(str(FPDIR),name)
        if not fp:raise RuntimeError('Missing footprint '+name)
        fp.SetFPID(pcb.LIB_ID(lib,name));fp.SetReference(p['ref']);fp.SetValue(p['value']);fp.SetDNP(p['dnp'])
        path=pcb.KIID_PATH();path.push_back(pcb.KIID(uid('root')))
        if p['page']!='root':path.push_back(pcb.KIID(uid('sheet-'+p['page'])))
        path.push_back(pcb.KIID(p['uuid']));fp.SetPath(path)
        x,y,a=p['pcb'];fp.SetPosition(vec(x,y));fp.SetOrientationDegrees(a)
        for pad in fp.Pads():
            num=pad.GetNumber()
            if num in p['pins'] and p['pins'][num]:pad.SetNet(nets[p['pins'][num]])
        fp.Reference().SetTextSize(vec(.8,.8));fp.Reference().SetTextThickness(mm(.12))
        fp.Reference().SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        fp.Reference().SetPosition(vec(x+(1.8 if p['ref'][0] in 'RC' else 0),y-2.0))
        if p['ref'].startswith(('TP','R','C','D','F')):fp.Reference().SetLayer(pcb.F_Fab)
        else:fp.Reference().SetLayer(pcb.F_Fab)
        fp.Value().SetVisible(False);b.Add(fp)
    for k,(x,y) in enumerate([(3,3),(83,3),(3,59),(83,59)],1):
        fp=pcb.FootprintLoad(str(KROOT/'footprints'/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');fp.SetReference('H'+str(k));fp.SetBoardOnly(True);fp.SetPosition(vec(x,y));fp.Reference().SetVisible(False);fp.Value().SetVisible(False);b.Add(fp)
    for a,c in [((0,0),(86,0)),((86,0),(86,62)),((86,62),(0,62)),((0,62),(0,0))]:
        s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(vec(*a));s.SetEnd(vec(*c));s.SetLayer(pcb.Edge_Cuts);s.SetWidth(mm(.05));b.Add(s)
    # Copper keepout across the entire functional isolation boundary.
    z=pcb.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(pcb.LSET.AllCuMask());z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowCopperPour(True)
    z.SetZoneName('ISOLATION_NO_COPPER'); poly=z.Outline();poly.NewOutline()
    for x,y in [(16.65,.3),(17.35,.3),(17.35,61.7),(16.65,61.7)]:poly.Append(mm(x),mm(y))
    b.Add(z)
    for cx,k in zip((32,52,72),range(3)):
        
        for j in range(4):board_text(b,str(k*4+j+1),cx-5.25+j*3.5,58.8,.9)
        board_text(b,f'0x{0x48+k:02X}',cx,16,1)
    board_text(b,'12 V NOMINAL / SENSE ONLY',50,2,1.0)
    board_text(b,'USB',11.5,50.5,.8)
    board_text(b,'REV C',10,57,1)
    board_text(b,'ISOLATED',17,46,.8,pcb.F_SilkS,90)
    board_text(b,'J4: 5V / GND / 3V3 / SDA6 / SCL7',45,57,.9,pcb.B_SilkS)
    board_text(b,'12 SENSE INPUTS | NO OUTPUT | NOT FOR MAINS',46,49,.9,pcb.B_SilkS)
    pcb.SaveBoard(str(ROOT/(PROJECT+'.kicad_pcb')),b)
    pcb.ExportSpecctraDSN(b,str(ROOT/(PROJECT+'.dsn')))
    return b

def project_file():
    proj={
      'meta':{'filename':PROJECT+'.kicad_pro','version':1},
      'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.3,'min_hole_clearance':.25,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.12},'rule_severities':{'unconnected_items':'error'}}},
      'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.2,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25,'wire_width':6,'bus_width':12,'line_style':0,'schematic_color':'rgba(0, 0, 0, 0.000)','pcb_color':'rgba(0, 0, 0, 0.000)'}]},
      'schematic':{'drawing':{'default_text_size':40}},
    }
    (ROOT/(PROJECT+'.kicad_pro')).write_text(json.dumps(proj,indent=2)+'\n')

def outputs():
    (ROOT/'design-manifest.json').write_text(json.dumps(dict(scope=SCOPE,channels=CHANNELS,parts=PARTS),indent=2)+'\n')
    with (ROOT/'manufacturing'/'bom.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','Manufacturer','MPN','Footprint','Populate','Notes','LCSC','JLC Category'])
        for p in PARTS:
            if p['ref'].startswith('#') or p['ref'].startswith('TP'):continue
            w.writerow([p['ref'],p['value'],p['maker'],p['mpn'],p['local_fp'],'NO' if p['dnp'] else 'YES',p['note'],p.get('lcsc',''),p.get('jlc_category','')])
    with (ROOT/'pin-map.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['Input','Connector','Contact','ADC','I2C_address','AIN','ADC_pin','Testpoint'])
        for c in CHANNELS:w.writerow([c['pin'],'J'+str(c['bank']+1),(c['pin']-1)%4+1,c['adc'],hex(c['address']),c['mux'],c['adc_pin'],c['testpoint']])

if __name__=='__main__':
    copy_libraries();project_file()
    schematic('root','12 V universal pin-voltage tester - power and controller')
    for k in range(3):schematic('bank'+str(k+1),f'Inputs {k*4+1}-{k*4+4}: protected sensing and ADC')
    make_board();outputs()
    print(f'Generated {len(PARTS)} schematic components; {len(CHANNELS)} sensing channels. Board still requires routing.')
