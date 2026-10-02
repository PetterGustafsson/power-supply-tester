import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const out=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(out,'../../hardware/rev-b');
const data=JSON.parse(await fs.readFile(root+'/sourcing/jlc-review.json','utf8'));
const wb=Workbook.create();
const sum=wb.worksheets.add('Summary');
const bom=wb.worksheets.add('BOM');
const src=wb.worksheets.add('Sources');
const n=data.parts.length,end=5+n;
const money='$0.00';
function style(sh,range,widths){
 sh.showGridLines=false;
 sh.getRange(range).format.font={name:'Arial',size:10,color:'#22334A'};
 sh.getRange(range).format.rowHeight=24;
 sh.getRange(range).format.verticalAlignment='center';
 widths.forEach((width,i)=>sh.getRangeByIndexes(0,i,range.endsWith('30')?30:40,1).format.columnWidthPx=width);
}
function header(sh,r){sh.getRange(r).format={fill:'#243B5A',font:{color:'#FFFFFF',bold:true},horizontalAlignment:'center',wrapText:true,rowHeight:32};}
style(sum,'A1:F30',[325,115,30,225,180,170]);
sum.tabColor='#243B5A';
sum.getRange('A2').values=[['12 V tester · Rev B sourcing review']];
sum.getRange('A2').format.font={size:15,bold:true};
sum.getRange('A3').values=[['Checked 30 Sep 2026 · USD · prototype quantities']];
sum.getRange('A5:B6').values=[['Boards to assemble',2],['Economic extended loading fee',3.07]];
sum.getRange('B5:B6').format.fill='#FFF0C5';
sum.getRange('B6').setNumberFormat(money);
sum.dataValidations.add({range:'B5',rule:{type:'whole',operator:'between',formula1:1,formula2:100}});
sum.getRange('A8:A14').values=[['Nominal fitted parts'],['Of which unavailable parts'],['Economic extended loading allowance'],['Parts + loading only'],['Basic + promotional loading avoided'],['Parts short of nominal quantity'],['Fitted components per board']];
sum.getRange('B8:B14').formulas=[['=SUM(BOM!H6:H29)'],['=SUMIF(BOM!J6:J29,"PREORDER",BOM!H6:H29)'],['=SUM(BOM!I6:I29)'],['=B8+B10'],['=(COUNTIF(BOM!C6:C29,"Basic")+COUNTIF(BOM!C6:C29,"Promotional Extended"))*B6'],['=COUNTIF(BOM!J6:J29,"PREORDER")+COUNTIF(BOM!J6:J29,"SHORT")'],['=SUM(BOM!D6:D29)']];
sum.getRange('B8:B12').setNumberFormat(money);
sum.getRange('A11:B11').format.fill='#EAF0F7';
sum.getRange('A11:B11').format.font.bold=true;
sum.getRange('B13').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FCE5E5',font:{color:'#9E2424',bold:true}}});
sum.getRange('D5').values=[['Stocked primary BOM']];sum.getRange('D5').format.font.bold=true;
sum.getRange('D6:F7').merge();sum.getRange('D6').values=[['All 24 selected types showed stock for 2 or 5 boards. U7 is now MPS C22419841. Recheck stock plus attrition at checkout.']];sum.getRange('D6:F7').format.wrapText=true;sum.getRange('D6:F7').format.fill='#EAF0F7';
sum.getRange('D9:F11').merge();sum.getRange('D9').values=[['This is not a checkout quote. Costs exclude attrition, MOQ extras, PCB fabrication, assembly setup, placement, LGA X-ray, shipping, tax, display and harness. Stock is not reserved.']];sum.getRange('D9:F11').format.wrapText=true;
sum.getRange('A17').values=[['Optional lower-cost switch preorder']];sum.getRange('A17').format.font.bold=true;
sum.getRange('A18:B19').values=[['ADG4612BRUZ unit estimate',2.7916],['Potential nominal parts saving',null]];
sum.getRange('B18').setNumberFormat('$0.0000');
sum.getRange('B19').formulas=[['=B5*3*(6.745-B18)']];sum.getRange('B19').setNumberFormat(money);
sum.getRange('D17:F20').merge();sum.getRange('D17').values=[['Alternate BOM uses C657391 for U4–U6. JLC displayed zero stock, MOQ 4 and estimated 9-day lead time. Same TSSOP chip; use only if preorder price and delivery are acceptable. Primary BOM uses stocked C207399.']];sum.getRange('D17:F20').format.wrapText=true;
sum.getRange('A22:F24').merge();sum.getRange('A22').values=[['Rev B changes the converter, its footprint and routing, C21 to 22uF, filters to 470pF, and zener footprint/source. Precision resistors and protected switches retained. Computer checks pass; hardware noise, sequencing and calibration remain untested. C21/C24 are NRND but deeply stocked.']];sum.getRange('A22:F24').format.wrapText=true;
sum.getRange('A27').values=[['JLC fee schedule']];sum.getRange('A28').values=[[data.fee_source]];sum.getRange('A28:F28').merge();sum.getRange('A28').format.font.color='#536B88';

style(bom,'A1:J30',[100,245,160,75,90,100,90,100,85,110]);bom.tabColor='#476685';
bom.getRange('A2').values=[['Selected BOM · live JLC library snapshot']];bom.getRange('A2').format.font={size:15,bold:true};
bom.getRange('A3').values=[['Unit price is displayed 1+ tier; no volume discount or attrition assumed. Full sources on next tab.']];
bom.getRange('A5:J5').values=[['JLC part #','Manufacturer part number','Category','Qty / PCB','Required','Stock','Unit USD','Parts USD','Fee USD','Status']];header(bom,'A5:J5');
bom.getRange(`A6:J${end}`).values=data.parts.map(p=>[p.lcsc,p.mpn,p.category,p.qty_per_board,null,p.stock,p.unit_usd,null,null,null]);
for(let r=6;r<=end;r++){
 bom.getRange(`E${r}`).formulas=[[`=D${r}*Summary!$B$5`]];
 bom.getRange(`H${r}:J${r}`).formulas=[[`=E${r}*G${r}`,`=IF(C${r}="Extended",Summary!$B$6,0)`,`=IF(F${r}=0,"PREORDER",IF(F${r}<E${r},"SHORT","IN STOCK"))`]];
 if(r%2===0)bom.getRange(`A${r}:J${r}`).format.fill='#F3F6F9';
}
bom.getRange(`F6:F${end}`).setNumberFormat('#,##0');bom.getRange(`G6:G${end}`).setNumberFormat('$0.0000');bom.getRange(`H6:I${end}`).setNumberFormat(money);
bom.getRange(`J6:J${end}`).conditionalFormats.add('containsText',{text:'PREORDER',format:{fill:'#FCE5E5',font:{color:'#9E2424',bold:true}}});
bom.freezePanes.freezeRows(5);bom.freezePanes.freezeColumns(2);

style(src,'A1:G30',[100,160,210,330,330,430,430]);
src.getRange('A2').values=[['References, substitutions and source links']];src.getRange('A2').format.font={size:15,bold:true};
src.getRange('A3').values=[['Exact JLC code controls matching; reject similarly named substitute ICs. Sources checked 2026-09-30.']];
src.getRange('A5:G5').values=[['JLC part #','Designators','Previous MPN','Selected specification','Decision / reason','JLC source','Manufacturer source / qualification note']];header(src,'A5:G5');
const sourceMap={
 C1743:'Fenghua datasheet C1743.pdf: X7R +/-15% over -55 to 125C. Max model 600pF. Analog bandwidth increases; bench noise test required.',
 C19077410:'Hongjiacheng BZT52C12 datasheet Rev2.1 p2: leakage <=100nA at 8V; 350mW. SOD-123 footprint updated.',
 C22419841:'https://www.monolithicpower.com/en/products/isolation/mie1w0505bglvh.html — Rev1.0 pp2,4,14,16: 5V regulated, 12 pins, local caps, land pattern.',
 C49678:'https://yageogroup.com/download/specsheet/CC0805KRX7R9BB104',
 C28323:'https://product.samsungsem.com/mlcc/CL21B105KBFNNN.do',
 C45783:'https://product.samsungsem.com/cn/mlcc/CL21A226MAQNNN.do — NRND; fine for stocked prototype, review for production.',
 C207399:'https://www.analog.com/media/en/technical-documentation/data-sheets/adg4612_4613.pdf',
 C15850:'JLC listing: 10uF 25V X5R 10% 0805; real effective capacitance and supply transients still need bench verification.',
 C5338283:'Exact converter retained; do not substitute a generic SOIC-16 module. Preorder estimate only.'
};
src.getRange(`A6:G${end}`).values=data.parts.map(p=>[p.lcsc,p.refs,p.old_mpn,p.spec,p.change,p.source,sourceMap[p.lcsc]||'Exact original retained or passive ratings/package matched in JLC library.']);
src.getRange(`A6:G${end}`).format.wrapText=true;src.getRange(`A6:G${end}`).format.rowHeight=60;
src.getRange(`F6:G${end}`).format.font.color='#536B88';
src.freezePanes.freezeRows(5);src.freezePanes.freezeColumns(1);

wb.recalculate();
const results=()=>({parts:sum.getRange('B8').values[0][0],fees:sum.getRange('B10').values[0][0],short:sum.getRange('B13').values[0][0],fit:sum.getRange('B14').values[0][0]});
const before=results();
if(Math.abs(before.parts-data.nominal_parts_usd)>1e-7||before.short!==0||before.fit!==114)throw new Error('Unexpected totals '+JSON.stringify(before));
sum.getRange('B5').values=[[5]];wb.recalculate();
const changed=results();if(Math.abs(changed.parts-before.parts*2.5)>1e-7||changed.fees!==before.fees)throw new Error('Quantity sensitivity failed');
sum.getRange('B5').values=[[2]];wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A',options:{useRegex:true,maxResults:30},maxChars:3000});
console.log(JSON.stringify({totals:results(),sensitivity:'PASS',errors}));
await fs.writeFile(out+'/workbook-verification-rev-b.json',JSON.stringify({totals:results(),sensitivity:'PASS',errors},null,2));
for(const sh of [sum,bom,src]){
 const preview=await wb.render({sheetName:sh.name,autoCrop:'all',scale:1,format:'png'});
 await fs.writeFile(out+'/rev-b-'+sh.name.toLowerCase()+'.png',new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(out+'/JLC-BOM-review-rev-b.xlsx');
console.log((await wb.inspect({kind:'region',sheetId:'Summary',range:'A8:B14',maxChars:1800})).ndjson);
