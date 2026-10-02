const sharp = require('/Users/petter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const path = require('path');
(async()=>{
 const root=path.resolve(__dirname,'..');
 for(const name of ['hr10a-10p-12p','hr10a-10p-12p-numbered']) {
  await sharp(path.join(root,'output',name+'.svg'),{density:144}).png().toFile(path.join(root,'output',name+'.png'));
 }
 await sharp(path.join(root,'output/hr10a-10p-12p.svg')).resize(900,900).flatten({background:'#15191e'}).png().toFile(path.join(root,'output/preview-dark.png'));
})();
