from pathlib import Path
from PIL import Image
import sys
FAIL="--fail" in sys.argv
folder="electron-fail-frames" if FAIL else "electron-frames"
name="electron-tunnel-fail-animation" if FAIL else "electron-tunnel-animation"
p=Path('output');frames=[Image.open(f).convert('RGB') for f in sorted((p/folder).glob('*.png'))]
sheet=Image.new('RGB',(480,480*3))
for k,n in enumerate([0,16,34]):sheet.paste(frames[n],(0,480*k))
palette=sheet.quantize(colors=256)
q=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
q[0].save(p/(name+'.gif'),save_all=True,append_images=q[1:],duration=100,loop=0,optimize=False,disposal=2)
small=[im.resize((240,240),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
small[0].save(p/(name+'-240.gif'),save_all=True,append_images=small[1:],duration=100,loop=0,optimize=False,disposal=2)
check=Image.open(p/(name+'.gif'));print('Verified',check.n_frames,'frames,',check.size,'pixels')
