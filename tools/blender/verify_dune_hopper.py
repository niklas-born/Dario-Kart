"""Validate Dune Hopper exchange files and re-import its FBX into an empty scene."""
import hashlib
import json
from pathlib import Path
import struct

import bpy

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/karts/dune-hopper/exports'
manifest=json.loads((OUT/'dune-hopper.manifest.json').read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb(path):
    data=path.read_bytes()
    magic,version,size=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and size==len(data)
    length,kind=struct.unpack_from('<I4s',data,12)
    assert kind==b'JSON'
    return json.loads(data[20:20+length])


assert digest(ROOT/manifest['source'])==manifest['sourceSha256']
assert digest(ROOT/manifest['driver'])==manifest['driverSourceSha256']
for key,path in manifest['outputs'].items():
    assert digest(ROOT/path)==manifest['outputHashes'][key]
kart=glb(OUT/'dune-hopper.glb')
combined=glb(OUT/'grit-dune-hopper.glb')
expected={'Dune_Hopper_Root','Dune_Steering_Frame','Dune_Steering_Spin','Dune_Seat_Root','Dune_Spare_Mount'}
expected.update('Dune_Steer_'+n for n in ('FL','FR','RL','RR'))
expected.update('Dune_Spin_'+n for n in ('FL','FR','RL','RR'))
expected.update(manifest['sockets'])
for doc in (kart,combined):
    nodes=doc['nodes']
    names={n.get('name',''):i for i,n in enumerate(nodes)}
    assert expected<=names.keys(),expected-names.keys()
    assert not doc.get('cameras')
    assert not any(n.startswith(('Dune_Studio_','Dune_Concept_Reference','Dune_Camera_')) for n in names)
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert {'POSITION','NORMAL','TEXCOORD_0'}<=primitive['attributes'].keys()
    parents={child:i for i,node in enumerate(nodes) for child in node.get('children',[])}
    root=names['Dune_Hopper_Root']
    assert parents[names['Dune_Seat_Root']]==root
    assert parents[names['Dune_Spare_Mount']]==root
    assert any('mesh' in nodes[c] for c in nodes[names['Dune_Seat_Root']].get('children',[]))
    for n in ('FL','FR','RL','RR'):
        assert parents[names['Dune_Spin_'+n]]==names['Dune_Steer_'+n]
    if 'Grit_Driver_Rig' in names:
        assert parents[names['Grit_Driver_Rig']]==root
assert not kart.get('skins') and not kart.get('animations')
assert len(kart['meshes'])==manifest['exportKartMeshCount']==8
assert len(combined['skins'])==1
assert len(combined['skins'][0]['joints'])==14
target_count=sum(len(p.get('targets',[])) for mesh in combined['meshes'] for p in mesh['primitives'])
assert target_count==1,target_count
assert combined.get('animations')
assert any(channel['target']['path']=='weights' for anim in combined['animations'] for channel in anim['channels'])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/manifest['output']))
objects=bpy.context.scene.objects
names={o.name for o in objects}
assert expected<=names,expected-names
meshes=[o for o in objects if o.type=='MESH']
assert len(meshes)==manifest['exportKartMeshCount']
assert all(o.data.uv_layers for o in meshes)
assert not any(o.type in {'ARMATURE','LIGHT','CAMERA'} for o in objects)
assert bpy.data.objects['Dune_Seat_Root'].parent.name=='Dune_Hopper_Root'
assert bpy.data.objects['Dune_Spare_Mount'].parent.name=='Dune_Hopper_Root'
assert any(o.type=='MESH' for o in bpy.data.objects['Dune_Seat_Root'].children)
positions=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
bounds=[[min(v[k] for v in positions),max(v[k] for v in positions)] for k in range(3)]
for measured,original in zip(bounds,manifest['kartBoundsMetersXYZ']):
    assert max(abs(a-b) for a,b in zip(measured,original))<.002,(bounds,manifest['kartBoundsMetersXYZ'])
for n,spec in manifest['wheelPivots'].items():
    spin=bpy.data.objects[spec['spin']]
    assert spin.parent.name==spec['steer']
    assert max(abs(a-b) for a,b in zip(spin.matrix_world.translation,spec['centerMeters']))<.002
report={'passed':True,'kartMeshCount':len(meshes),'kartTriangles':manifest['exportKartTriangles'],
        'combinedDriverBones':14,'combinedBlinkTargets':target_count,'animatedBlinkExported':True,
        'fbxHierarchyPreserved':True,'fbxBoundsAndWheelCentersPreservedWithinMeters':.002,
        'driverAndSeatSeparate':True,'carOnlyExportExcludesDriver':True,'spareSeparateFromRoadWheelPivots':True,
        'nativeControlChecks':manifest['checks'],
        'sourceAndOutputHashesMatch':True,'materialsInKartGLB':len(kart.get('materials',[])),
        'studioAndReferenceObjectsExcluded':True,'unityRendererVerified':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('DUNE_HOPPER_VERIFIED '+json.dumps(report),flush=True)
