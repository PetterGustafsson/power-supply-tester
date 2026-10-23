"""Pack the connector artwork and export its exact RGB565 LCD preview."""
from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'output/connector-lcd-240.png'
im=Image.open(source).convert('RGB');assert im.size==(240,240)
data=bytearray()
samples=im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()
for r,g,b in samples:
    value=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
    data.extend((value>>8,value&255))
geo=json.loads((ROOT/'output/geometry.json').read_text())
points=[tuple(round(120+15*v) for v in geo['pin_centres_mm'][str(pin)]) for pin in range(1,13)]
header='''#pragma once
#include <cstdint>
// Existing connector artwork, RGB565 high byte first. No measurement is baked in.
// Regenerate with scripts/build_live_graphics_assets.py (Pillow required).
namespace tester_ui {
static const uint8_t connectorBackdrop[] = {
'''
header+=''.join(','.join(f'0x{b:02x}' for b in data[i:i+24])+',\n' for i in range(0,len(data),24))
header+='};\nstatic_assert(sizeof(connectorBackdrop)==240*240*2,"Backdrop size");\n'
header+='struct Point { float x,y; };\n'
header+='static constexpr Point pinPositions[12]={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in points)+'};\n}\n'
(ROOT/'firmware/Tester12VRevD/ConnectorBackdrop.h').write_text(header)
preview=bytearray()
for hi,lo in zip(data[::2],data[1::2]):
    value=(hi<<8)|lo
    preview.extend((((value>>11)&31)*255//31,((value>>5)&63)*255//63,(value&31)*255//31))
Image.frombytes('RGB',(240,240),bytes(preview)).save(ROOT/'output/connector-base-240-rgb565.png',optimize=True)
print('Packed existing artwork and all 12 geometry-based pin centers:',len(data),'bytes')
