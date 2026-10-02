import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from vrml_import import bounds
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'sources/imported.blend'))
out=[]
for o in bpy.data.collections['display'].objects:
    b=bounds([o]);d=[v[1]-v[0] for v in b]
    if b[0][0]>10 and b[0][1]<17 and b[2][0]<-5:
        out.append({'bounds':b,'color':list(o.data.materials[0].diffuse_color)})
(root/'sources/header-bounds.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
