"""Check kart/combined GLBs and re-import the runtime FBX into an empty scene."""
import json
from pathlib import Path
import struct

import bpy

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/karts/streamliner/exports'
FBX=ROOT/'game/Assets/_DarioKart/Art/Models/Karts/streamliner.fbx'
manifest=json.loads((OUT/'streamliner.manifest.json').read_text())


def glb(path):
    data=path.read_bytes()
    magic,version,size=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and size==len(data)
    length,kind=struct.unpack_from('<I4s',data,12)
    assert kind==b'JSON'
    return json.loads(data[20:20+length])


kart=glb(OUT/'streamliner.glb')
combined=glb(OUT/'riff-streamliner.glb')
expected={'Streamliner_Root','SteeringWheel_Spin','Seat_Root'}
expected.update('Steer_'+side for side in ('FL','FR','RL','RR'))
expected.update('Spin_'+side for side in ('FL','FR','RL','RR'))
expected.update(manifest['sockets'])
for doc in (kart,combined):
    names={n.get('name','') for n in doc['nodes']}
    assert expected<=names,expected-names
    assert not doc.get('cameras')
    assert not any(n.startswith(('Kart_Camera_','Kart_Studio_','Reference_')) for n in names)
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            assert {'POSITION','NORMAL','TEXCOORD_0'}<=p['attributes'].keys()
assert not kart.get('skins')
assert len(combined['skins'])==1
assert len(combined['skins'][0]['joints'])==14
assert sum(len(p.get('targets',[])) for mesh in combined['meshes'] for p in mesh['primitives'])==2
assert combined.get('animations')
assert len(kart['meshes'])==manifest['exportKartMeshCount']
for doc in (kart,combined):
    nodes=doc['nodes']
    seat=next(n for n in nodes if n.get('name')=='Seat_Root')
    assert any('mesh' in nodes[i] for i in seat.get('children',[])), 'Seat must remain its own mesh'
    assert not any(nodes[i].get('name')=='Riff_Driver_Rig' for i in seat.get('children',[]))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(FBX))
names={o.name for o in bpy.context.scene.objects}
assert expected<=names,expected-names
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==manifest['exportKartMeshCount']
assert all(o.data.uv_layers for o in meshes)
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
assert any(o.type=='MESH' for o in bpy.data.objects['Seat_Root'].children)
positions=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
bounds=[[min(v[k] for v in positions),max(v[k] for v in positions)] for k in range(3)]
for measured,original in zip(bounds,manifest['kartBoundsMetersXYZ']):
    assert max(abs(a-b) for a,b in zip(measured,original))<.002,(bounds,manifest['kartBoundsMetersXYZ'])
for side in ('FL','FR','RL','RR'):
    assert bpy.data.objects['Spin_'+side].parent.name=='Steer_'+side
report={'passed':True,'kartMeshCount':len(meshes),'kartTriangles':manifest['exportKartTriangles'],
        'combinedDriverBones':14,'combinedBlinkTargets':2,
        'fbxHierarchyPreserved':True,'fbxBoundsPreservedWithinMeters':.002,
        'seatSeparatelyEditable':True,
        'materialsInKartGLB':len(kart.get('materials',[])),
        'studioAndReferenceObjectsExcluded':True,'unityRendererVerified':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('STREAMLINER_VERIFIED '+json.dumps(report),flush=True)
