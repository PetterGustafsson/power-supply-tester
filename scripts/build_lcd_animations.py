from pathlib import Path
from PIL import Image
import struct
OUT=Path('firmware/ConnectorDisplay');OUT.mkdir(exist_ok=True)
def rgb565(path):
 im=Image.open(path).convert('RGB').resize((240,240),Image.Resampling.LANCZOS)
 return [((r>>3)<<11)|((g>>2)<<5)|(b>>3) for r,g,b in im.get_flattened_data()]
def encode(cur,prev):
 data=bytearray();i=0
 while i<len(cur):
  if cur[i]==prev[i]:
   j=i+1
   while j<len(cur) and cur[j]==prev[j] and j-i<32767:j+=1
   data.extend(struct.pack('<H',j-i));i=j
  else:
   j=i+1
   while j<len(cur) and j-i<32767:
    if cur[j]==prev[j] and (j+3>=len(cur) or cur[j:j+4]==prev[j:j+4]):break
    j+=1
   data.extend(struct.pack('<H',0x8000|(j-i)))
   for v in cur[i:j]:data.extend(struct.pack('>H',v))
   i=j
 return data
def decode(data,prev):
 cur=prev.copy();pos=0;pixel=0
 while pos<len(data):
  op=struct.unpack_from('<H',data,pos)[0];pos+=2;n=op&32767
  assert n>0 and pixel+n<=57600
  if op&32768:
   for i in range(n):cur[pixel+i]=struct.unpack_from('>H',data,pos+i*2)[0]
   pos+=2*n
  pixel+=n
 assert pixel==57600
 return cur
payload=bytearray();offsets=[]
for folder in ['electron-frames','electron-fail-frames']:
 prev=[0]*57600
 frames=sorted((Path('output')/folder).glob('*.png'));assert len(frames)==48
 for path in frames:
  cur=rgb565(path);encoded=encode(cur,prev)
  assert decode(encoded,prev)==cur, path
  offsets.append(len(payload));payload.extend(encoded);prev=cur
 offsets.append(len(payload))
# 49 offsets for each state; shared boundary appears twice.
h='#pragma once\n#include <Arduino.h>\nconstexpr uint16_t kFramesPerState=48;\nconstexpr uint16_t kFrameMs=100;\nconst uint32_t animationOffsets[2][49] PROGMEM = {\n'
h+='{'+','.join(map(str,offsets[:49]))+'},\n{'+','.join(map(str,offsets[49:]))+'}\n};\n'
h+='const uint8_t animationData[] PROGMEM = {\n'
for i in range(0,len(payload),24):h+=','.join(f'0x{x:02x}' for x in payload[i:i+24])+',\n'
h+='};\n'
(OUT/'ConnectorAnimation.h').write_text(h)
print(f'Encoded and round-trip verified 96 frames: {len(payload):,} bytes (raw 11,059,200).')
