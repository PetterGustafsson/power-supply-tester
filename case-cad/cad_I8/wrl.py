"""Minimal VRML2 parser for KiCad exports -> list of (path, 4x4, verts, faces, rgb)."""
import re, numpy as np
TOK = re.compile(r'[\[\]{}]|[^\s,\[\]{}]+')
def tokens(txt):
    txt = re.sub(r'#[^\n]*', '', txt); return TOK.findall(txt)
class P:
    def __init__(s, t): s.t, s.i, s.defs = t, 0, {}
    def peek(s, k=0): return s.t[s.i + k] if s.i + k < len(s.t) else None
    def nxt(s): v = s.t[s.i]; s.i += 1; return v
    def node(s):
        name = None
        if s.peek() == 'USE': s.nxt(); return s.defs[s.nxt()]
        if s.peek() == 'DEF': s.nxt(); name = s.nxt()
        typ = s.nxt(); assert s.nxt() == '{', typ
        n = {'_type': typ, '_name': name}
        while s.peek() != '}':
            f = s.nxt(); n[f] = s.value()
        s.nxt()
        if name: s.defs[name] = n
        return n
    def isnum(s, v):
        try: float(v); return True
        except: return v in ('TRUE', 'FALSE')
    def value(s):
        p = s.peek()
        if p == '[':
            s.nxt(); out = []
            while s.peek() != ']':
                if s.isnum(s.peek()): out.append(s.nxt())
                else: out.append(s.node())
            s.nxt()
            if out and isinstance(out[0], str): return np.array([float(x) if x not in ('TRUE','FALSE') else float(x=='TRUE') for x in out])
            return out
        if p in ('DEF', 'USE') or (s.peek(1) == '{'): return s.node()
        out = []
        while s.isnum(s.peek()): out.append(s.nxt())
        return np.array([float(x) if x not in ('TRUE','FALSE') else float(x=='TRUE') for x in out])
def rotm(r):
    ax = r[:3]; a = r[3]; n = np.linalg.norm(ax)
    if n < 1e-12 or abs(a) < 1e-12: return np.eye(4)
    x, y, z = ax/n; c, s_ = np.cos(a), np.sin(a); C = 1 - c
    M = np.eye(4); M[:3, :3] = [[c+x*x*C, x*y*C-z*s_, x*z*C+y*s_], [y*x*C+z*s_, c+y*y*C, y*z*C-x*s_], [z*x*C-y*s_, z*y*C+x*s_, c+z*z*C]]; return M
def tr(v): M = np.eye(4); M[:3, 3] = v; return M
def xf(n):
    T = tr(n.get('translation', np.zeros(3))); C = tr(n.get('center', np.zeros(3))); R = rotm(n.get('rotation', np.array([0, 0, 1, 0.])))
    SR = rotm(n.get('scaleOrientation', np.array([0, 0, 1, 0.]))); S = np.diag([*n.get('scale', np.ones(3)), 1.0])
    return T @ C @ R @ SR @ S @ np.linalg.inv(SR) @ np.linalg.inv(C)
def walk(n, M, path, out):
    if n['_type'] in ('Transform', 'Group'):
        M2 = M @ xf(n) if n['_type'] == 'Transform' else M
        for c in n.get('children', []): walk(c, M2, path + [n['_name']], out)
    elif n['_type'] == 'Shape':
        g = n['geometry']; pts = g['coord']['point'].reshape(-1, 3); ci = g['coordIndex'].astype(int)
        faces, cur = [], []
        for k in ci:
            if k < 0:
                for j in range(1, len(cur) - 1): faces.append((cur[0], cur[j], cur[j+1]))
                cur = []
            else: cur.append(k)
        mat = n['appearance']['material']; col = mat.get('diffuseColor', np.array([.5, .5, .5]))
        v = (M @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
        out.append(dict(path=path, verts=v, faces=np.array(faces), rgb=col.tolist(), shape=n['_name'], transp=float(mat.get('transparency', np.zeros(1))[0]) if len(mat.get('transparency', [])) else 0))
def load(f):
    p = P(tokens(open(f).read())); roots = []
    while p.peek() is not None: roots.append(p.node())
    out = []
    for r in roots: walk(r, np.eye(4), [], out)
    return out
