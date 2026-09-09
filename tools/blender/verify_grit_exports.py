"""Verify the separate Grit driver, skinning, blink, and portable file round trip."""
import hashlib
import json
from pathlib import Path
import struct

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/characters/grit'
EXPORTS=OUT/'exports'
manifest=json.loads((EXPORTS/'grit-driver.export.json').read_text())
for file_key,hash_key in [('source','sourceSha256'),('output','outputSha256'),('glb','glbSha256')]:
    assert hashlib.sha256((ROOT/manifest[file_key]).read_bytes()).hexdigest()==manifest[hash_key]
data=(EXPORTS/'grit-driver.glb').read_bytes()
magic,version,size=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and size==len(data)
length,kind=struct.unpack_from('<I4s',data,12)
assert kind==b'JSON'
doc=json.loads(data[20:20+length])
assert len(doc['skins'])==1 and len(doc['skins'][0]['joints'])==14
assert not doc.get('cameras')
for node in doc['nodes']:
    name=node.get('name','').lower()
    assert not any(word in name for word in ('seat','guide','studio','reference','camera','steering'))
targets=0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        assert {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'}<=p['attributes'].keys()
        targets+=len(p.get('targets',[]))
assert targets==1
assert len(doc['meshes'])==manifest['checks']['meshes']
assert doc.get('animations')

bpy.ops.wm.open_mainfile(filepath=str(OUT/'grit-driver.blend'))
scene=bpy.context.scene
scene.frame_set(1)
rig=bpy.data.objects['Grit_Driver_Rig']
assert rig.parent is None and len(rig.data.bones)==14
meshes=[o for o in scene.objects if o.type=='MESH']
assert len(scene.objects)==len(meshes)+1
assert len(meshes)==manifest['checks']['meshes']
assert all(o.parent==rig for o in meshes)
lid=bpy.data.objects['Upper_Lid_Center']
assert lid.data.shape_keys.key_blocks['Blink'].value==0
scene.frame_set(44)
assert lid.data.shape_keys.key_blocks['Blink'].value==1
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
closed_lid=lid.evaluated_get(dg)
closed_mesh=closed_lid.to_mesh()
tree=BVHTree.FromPolygons([closed_lid.matrix_world@v.co for v in closed_mesh.vertices],
                         [p.vertices[:] for p in closed_mesh.polygons])
marker=bpy.data.objects['Eye_Catchlight'].evaluated_get(dg)
marker_mesh=marker.to_mesh()
for v in marker_mesh.vertices:
    p=marker.matrix_world@v.co
    hit,normal,index,distance=tree.ray_cast(Vector((p.x,-2,p.z)),Vector((0,1,0)),4)
    assert hit is not None and hit.y < p.y-.00001, 'Reflection protrudes through the closed eyelid'
closed_lid.to_mesh_clear()
marker.to_mesh_clear()
scene.frame_set(1)
for obj in meshes:
    assert obj.data.uv_layers
    assert any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers)
    for v in obj.data.vertices:
        assert 1<=len(v.groups)<=4
        assert abs(sum(g.weight for g in v.groups)-1)<.0001

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(EXPORTS/'grit-driver.fbx'))
scene=bpy.context.scene
scene.frame_set(1)
meshes=[o for o in scene.objects if o.type=='MESH']
rigs=[o for o in scene.objects if o.type=='ARMATURE']
assert len(rigs)==1 and len(rigs[0].data.bones)==14
assert len(meshes)==len(doc['meshes'])
assert sum(bool(o.data.shape_keys) for o in meshes)==1
assert all(o.data.uv_layers for o in meshes)
assert all(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes)
verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
bounds=[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]
error=max(abs(a-b) for axis,ref in zip(bounds,manifest['boundsMetersXYZ']) for a,b in zip(axis,ref))
assert error<.002, (bounds,manifest['boundsMetersXYZ'])
report={'passed':True,'driverOnlyNativeFile':True,'seatAndWheelExcluded':True,
        'meshes':len(meshes),'triangles':manifest['checks']['triangles'],'bones':14,
        'blinkTargets':1,'blinkAtFrame44Verified':True,'weightsNormalized':True,
        'closedLidCoversEyeReflection':True,
        'glbAnimations':len(doc['animations']),'fbxBoundsMaxErrorMeters':error,
        'UVsAndSkinningPreserved':True,'unityRendererVerified':False}
(EXPORTS/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('GRIT_EXPORTS_VERIFIED '+json.dumps(report),flush=True)
