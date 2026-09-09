"""Verify the exported driver structure and re-import the FBX into an empty scene."""
import json
from pathlib import Path
import struct
import bpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'art-source/blender/characters/riff/exports'
data = (OUT/'riff-driver.glb').read_bytes()
magic, version, length = struct.unpack_from('<4sII',data,0)
assert magic == b'glTF' and version == 2 and length == len(data)
chunk_size, chunk_type = struct.unpack_from('<I4s',data,12)
assert chunk_type == b'JSON'
doc = json.loads(data[20:20+chunk_size])
assert len(doc['skins']) == 1
assert len(doc['skins'][0]['joints']) == 14
assert not doc.get('cameras')
for node in doc['nodes']:
    assert not node.get('name','').startswith(('Camera_','Studio_','Reference_','Seat_','Wheel_','Steering_'))
targets = 0
for mesh in doc['meshes']:
    for primitive in mesh['primitives']:
        assert {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'} <= primitive['attributes'].keys()
        targets += len(primitive.get('targets',[]))
assert targets == 2
assert doc.get('animations')
report = {'glb': {'meshes':len(doc['meshes']), 'joints':14, 'blinkTargets':targets,
                   'animationTracks':len(doc['animations']), 'guidesExcluded':True}}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(OUT/'riff-driver.fbx'))
meshes = [o for o in bpy.context.scene.objects if o.type=='MESH']
rigs = [o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(rigs)==1 and len(rigs[0].data.bones)==14
assert len(meshes)==len(doc['meshes'])
assert sum(bool(o.data.shape_keys) for o in meshes)==2
assert all(o.data.uv_layers for o in meshes)
assert all(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes)
positions = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
bounds = [[min(v[k] for v in positions),max(v[k] for v in positions)] for k in range(3)]
assert .9 < bounds[0][1]-bounds[0][0] < 1.4
assert 1.4 < bounds[2][1]-bounds[2][0] < 1.9
report['fbxRoundTrip'] = {'meshes':len(meshes), 'bones':14, 'blinkMeshes':2,
                          'boundsMetersXYZ':bounds, 'UVsAndSkinningPreserved':True}
report['unityRuntimeVerified'] = False
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('RIFF_EXPORT_VERIFIED '+json.dumps(report),flush=True)
