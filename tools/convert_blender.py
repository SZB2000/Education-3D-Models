# Blender 3.6+ background import; one self-contained model per input file.
import bpy,sys,pathlib
src,dst,max_px=sys.argv[sys.argv.index('--')+1:];src=pathlib.Path(src);max_px=int(max_px)
bpy.ops.wm.read_factory_settings(use_empty=True)
ext=src.suffix.lower()
if ext in ('.glb','.gltf'):bpy.ops.import_scene.gltf(filepath=str(src))
elif ext=='.fbx':bpy.ops.import_scene.fbx(filepath=str(src))
elif ext=='.obj':bpy.ops.wm.obj_import(filepath=str(src))
elif ext=='.ply':bpy.ops.wm.ply_import(filepath=str(src))
elif ext=='.stl':bpy.ops.wm.stl_import(filepath=str(src))
elif ext=='.dae':bpy.ops.wm.collada_import(filepath=str(src))
else:raise ValueError('Unsupported input format')
if not any(o.type=='MESH' for o in bpy.context.scene.objects):raise ValueError('No renderable meshes')
for img in bpy.data.images:
 if img.source!='FILE':continue
 w,h=img.size
 if not w or not h:raise ValueError('Missing texture: '+img.name)
 if max(w,h)>max_px:
  k=max_px/max(w,h);img.scale(max(1,round(w*k)),max(1,round(h*k)));img.pack()
bpy.ops.export_scene.gltf(filepath=dst,export_format='GLB',export_animations=True)
