const sharp=require('/Users/petter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const folder=process.argv.includes('--fail')?'electron-fail-frames':'electron-frames';
(async()=>{for(let i=0;i<48;i++){const n=String(i).padStart(2,'0');await sharp('output/'+folder+'/'+n+'.svg').resize(480,480).flatten({background:'#12191f'}).png().toFile('output/'+folder+'/'+n+'.png');}})();
