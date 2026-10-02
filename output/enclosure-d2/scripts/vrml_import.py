"""Read KiCad's normalized VRML export into Blender without approximating PCB geometry.

Supports the normalized Transform / Shape / IndexedFaceSet tree written by
KiCad 9, with DEF/USE sharing. Intended for this exported source, not arbitrary
VRML scenes. Coordinates returned by this project's exports are millimetres.
"""
import re
import bpy
from mathutils import Matrix,Vector,Quaternion

VECTORS={'center':3,'translation':3,'scale':3,'rotation':4,'scaleOrientation':4,
 'diffuseColor':3,'specularColor':3,'emissiveColor':3}

class Parser:
    def __init__(self,path):
        s=re.sub(r'#[^\n]*','',open(path).read())
        self.tokens=re.findall(r'"(?:\\.|[^"\\])*"|[{}\[\]]|[^\s,{}\[\]]+',s)
        self.i=0;self.defs={}
    def pop(self):
        t=self.tokens[self.i];self.i+=1;return t
    def scalar(self,t):
        if t in ('TRUE','FALSE'):return t=='TRUE'
        try:return float(t)
        except ValueError:return t.strip('"')
    def value(self,field=''):
        t=self.tokens[self.i]
        if field in VECTORS:return [float(self.pop()) for _ in range(VECTORS[field])]
        if t=='[':
            self.pop();result=[]
            while self.tokens[self.i]!=']':result.append(self.value())
            self.pop();return result
        if t=='USE':self.pop();return self.defs[self.pop()]
        if t=='DEF':
            self.pop();name=self.pop();node=self.value();node['def']=name;self.defs[name]=node;return node
        if self.i+1<len(self.tokens) and self.tokens[self.i+1]=='{':
            kind=self.pop();self.pop();node={'kind':kind}
            while self.tokens[self.i]!='}':
                key=self.pop();node[key]=self.value(key)
            self.pop();return node
        return self.scalar(self.pop())
    def parse(self):
        nodes=[]
        while self.i<len(self.tokens):nodes.append(self.value())
        return nodes

def rotation(a):return Quaternion(Vector(a[:3]),a[3]).to_matrix().to_4x4()

def load(path,prefix,collection):
    nodes=Parser(path).parse();objects=[];materials={};meshes={}
    def material(node):
        m=node.get('appearance',{}).get('material',{})
        rgb=m.get('diffuseColor',[.5,.5,.5]);alpha=1-m.get('transparency',0)
        key=tuple(rgb)+(alpha,)
        if key not in materials:
            mat=bpy.data.materials.new(prefix+'_material_'+str(len(materials)))
            mat.diffuse_color=(*rgb,alpha);mat.use_nodes=True
            bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,alpha)
            bs.inputs['Roughness'].default_value=.36
            materials[key]=mat
        return materials[key]
    def walk(node,parent):
        kind=node['kind']
        if kind=='Transform':
            t=Matrix.Translation(Vector(node.get('translation',[0,0,0])))
            c=Matrix.Translation(Vector(node.get('center',[0,0,0])))
            r=rotation(node.get('rotation',[0,0,1,0]));sr=rotation(node.get('scaleOrientation',[0,0,1,0]))
            scale=Matrix.Diagonal(Vector(node.get('scale',[1,1,1])+[1]))
            matrix=parent@t@c@r@sr@scale@sr.inverted()@c.inverted()
            for child in node.get('children',[]):walk(child,matrix)
        elif kind=='Shape':
            g=node['geometry'];assert g['kind']=='IndexedFaceSet',g['kind']
            key=id(g)
            if key not in meshes:
                points=g['coord']['point'];vertices=[points[i:i+3] for i in range(0,len(points),3)]
                faces=[];face=[]
                for i in g['coordIndex']:
                    if i==-1:
                        if len(face)>=3:faces.append(face)
                        face=[]
                    else:face.append(int(i))
                mesh=bpy.data.meshes.new(prefix+'_'+g.get('def','mesh'))
                mesh.from_pydata(vertices,[],faces);mesh.update();meshes[key]=mesh
            obj=bpy.data.objects.new(prefix+'_'+node.get('def','shape'),meshes[key]);collection.objects.link(obj)
            obj.matrix_world=parent
            if not obj.data.materials:obj.data.materials.append(material(node))
            objects.append(obj)
        else:raise ValueError('Unsupported top-level VRML node '+kind)
    for node in nodes:walk(node,Matrix.Identity(4))
    return objects

def bounds(objects):
    coords=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return [[min(p[i] for p in coords),max(p[i] for p in coords)] for i in range(3)]
