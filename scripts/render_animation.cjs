const sharp=require('/Users/petter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{for(let i=0;i<40;i++){const n=String(i).padStart(2,'0');await sharp('output/animation-frames/'+n+'.svg').resize(480,480).flatten({background:'#12191f'}).png().toFile('output/animation-frames/'+n+'.png');}})();
