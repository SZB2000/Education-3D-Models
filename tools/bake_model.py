"""Bake static educational meshes into one centered metre-sized glTF mesh; retain material groups."""
import json, struct, sys
from pathlib import Path
from collections import defaultdict
import numpy as np
src,out=map(Path,sys.argv[1:3])
raw=src.read_bytes()
length=struct.unpack_from("<I",raw,12)[0]
doc=json.loads(raw[20:20+length])
data=raw[28+length:]
sizes={"VEC3":3,"SCALAR":1}
def array(idx):
    a=doc["accessors"][idx]; b=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype({5126:"<f4",5125:"<u4",5123:"<u2",5121:"u1"}[a["componentType"]]); cols=sizes[a["type"]]
    return np.ndarray((a["count"],cols),dt,buffer=data,offset=b.get("byteOffset",0)+a.get("byteOffset",0),strides=(b.get("byteStride",dt.itemsize*cols),dt.itemsize))
def local(n):
    if "matrix" in n:return np.array(n["matrix"]).reshape(4,4).T
    x,y,z,w=n.get("rotation",[0,0,0,1]);m=np.eye(4)
    m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get("scale",[1,1,1]));m[:3,3]=n.get("translation",[0,0,0]);return m
roots=doc["scenes"][doc.get("scene",0)]["nodes"]
pick=int(sys.argv[3]) if len(sys.argv)>3 else None
groups=defaultdict(list)
def visit(i,m,enabled):
    n=doc["nodes"][i];m=m@local(n);enabled=enabled or pick==i
    if enabled and "mesh" in n:
        for prim in doc["meshes"][n["mesh"]]["primitives"]:
            v=array(prim["attributes"]["POSITION"])@m[:3,:3].T+m[:3,3]
            normals=array(prim["attributes"]["NORMAL"])@np.linalg.pinv(m[:3,:3]);normals/=np.maximum(1.e-10,np.linalg.norm(normals,axis=1,keepdims=True))
            ind=array(prim["indices"]).reshape(-1,3)
            if np.linalg.det(m[:3,:3])<0:ind=ind[:,[0,2,1]]
            groups[prim["material"]].append((v,normals,ind))
    for c in n.get("children",[]):visit(c,m,enabled)
for i in roots:visit(i,np.eye(4),pick is None)
lo=np.min([v.min(0) for parts in groups.values() for v,n,ind in parts],0)
hi=np.max([v.max(0) for parts in groups.values() for v,n,ind in parts],0)
packed=bytearray();views=[];access=[];prims=[];mats=[];nt=0
def write(a,t,vec):
    packed.extend(bytes((-len(packed))%4)); offset=len(packed);packed.extend(a.tobytes())
    views.append(dict(buffer=0,byteOffset=offset,byteLength=a.nbytes))
    b=dict(bufferView=len(views)-1,componentType=t,count=len(a),type=vec)
    if vec=="VEC3":b.update(min=a.min(0).tolist(),max=a.max(0).tolist())
    access.append(b);return len(access)-1
for mat,parts in groups.items():
    v=np.vstack([q[0] for q in parts]);v=((v-(lo+hi)/2)/max(hi-lo)).astype("<f4")
    norm=np.vstack([q[1] for q in parts]).astype("<f4");idx=[];offset=0
    for pos,n,i in parts:idx.append(i.astype("<u4")+offset);offset+=len(pos)
    ind=np.concatenate(idx).flatten();nt+=len(ind)//3
    prims.append(dict(attributes=dict(POSITION=write(v,5126,"VEC3"),NORMAL=write(norm,5126,"VEC3")),indices=write(ind,5125,"SCALAR"),material=len(mats)))
    mats.append(doc["materials"][mat])
j=dict(asset=doc["asset"],scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(primitives=prims)],materials=mats,buffers=[dict(byteLength=len(packed))],bufferViews=views,accessors=access)
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);packed.extend(bytes((-len(packed))%4))
out.write_bytes(struct.pack("<4sIIII",b"glTF",2,28+len(js)+len(packed),len(js),0x4e4f534a)+js+struct.pack("<II",len(packed),0x004e4942)+packed)
print(out.name,nt)
