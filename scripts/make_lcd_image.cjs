const sharp=require('/Users/petter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const fs=require('fs');const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const p=sharp(path.join(root,'output/hr10a-10p-12p.svg'),{density:192}).resize(240,240).flatten({background:'#000000'}).removeAlpha();
 await p.clone().png().toFile(path.join(root,'output/connector-lcd-240.png'));
 const rgb=await p.raw().toBuffer();const bytes=[];
 for(let i=0;i<rgb.length;i+=3){const n=((rgb[i]>>3)<<11)|((rgb[i+1]>>2)<<5)|(rgb[i+2]>>3);bytes.push(n>>8,n&255);}
 let h='#pragma once\n#include <Arduino.h>\n// RGB565, high byte first, 240 x 240. Generated from the connector SVG.\nconst uint8_t connectorPixels[] PROGMEM = {\n';
 for(let i=0;i<bytes.length;i+=24) h+=bytes.slice(i,i+24).map(x=>'0x'+x.toString(16).padStart(2,'0')).join(',')+',\n';
 h+='};\nstatic_assert(sizeof(connectorPixels) == 240 * 240 * 2, "Incorrect image size");\n';
 fs.writeFileSync(path.join(root,'firmware/ConnectorDisplay/ConnectorImage.h'),h);
})();
