"""Export the existing approved Grit + Dune Hopper as a static test-track visual.
The original character and vehicle files are never changed.
"""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'art-source/blender/karts/dune-hopper/exports/grit-dune-hopper.glb'
out=ROOT/'game/Assets/_DarioKart/Art/Models/Tracks/stormbreak-prototype'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();original=list(bpy.context.scene.objects);copies=[];infos=[]
for i,o in enumerate([o for o in original if o.type=='MESH']):
 evaluated=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(evaluated);ob=bpy.data.objects.new(f'StormbreakKart_{i:02}',me);bpy.context.collection.objects.link(ob);ob.matrix_world=o.matrix_world.copy();copies.append(ob)
 slots=[]
 for j,m in enumerate(me.materials):
  c=list(m.diffuse_color);bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
  if bs:c=list(bs.inputs['Base Color'].default_value)
  slots.append({'name':f'Kart_{i:02}_{j:02}','color':c})
 infos.append({'name':ob.name,'materials':slots})
bpy.ops.object.select_all(action='DESELECT')
for ob in copies:ob.select_set(True)
bpy.context.view_layer.objects.active=copies[0]
bpy.ops.export_scene.fbx(filepath=str(out/'stormbreak-kart.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,path_mode='STRIP')
(out/'kart-materials.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':infos},indent=2))
print('STORMBREAK KART:',len(copies),'mesh parts with original material slots')
