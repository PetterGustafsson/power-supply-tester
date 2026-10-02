import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from vrml_import import load,bounds
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
out={}
for name in ['tester-d2','display']:
    col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col)
    objects=load(str(root/'sources'/f'{name}.wrl'),name,col)
    out[name]={'bounds_mm':bounds(objects),'objects':len(objects),'last_objects':[{ 'name':o.name,'bounds':bounds([o]),'color':list(o.data.materials[0].diffuse_color)} for o in objects[-14:]]}
(root/'sources/model-inspection.json').write_text(json.dumps(out,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sources/imported.blend'))
print(json.dumps(out,indent=2))
