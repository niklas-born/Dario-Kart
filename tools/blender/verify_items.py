"""Fresh FBX import and GLB structural verification for the item collection."""
import bpy
import json
import hashlib
from pathlib import Path
import struct
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
results=[]
for folder in sorted((ROOT/'art-source/blender/items').iterdir()):
    if not folder.is_dir():continue
    path=folder/'exports'/(folder.name+'.fbx')
    if not path.exists():continue
    manifest=json.loads(path.with_suffix('.manifest.json').read_text())
    for filename,digest in manifest['sha256'].items():
        asset=folder/filename if filename.endswith('.blend') else folder/'exports'/filename
        assert hashlib.sha256(asset.read_bytes()).hexdigest()==digest,('Stale provenance',asset)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    objects=list(bpy.context.scene.objects)
    meshes=[o for o in objects if o.type=='MESH']
    triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
    assert triangles==manifest['triangles'],(folder.name,triangles,manifest['triangles'])
    assert len(meshes)==manifest['meshObjects']
    assert all(o.data.uv_layers for o in meshes)
    assert all(o.type=='MESH' for o in objects),'Studio or other non-mesh content leaked'
    assert all(len(o.data.vertices)>0 and len(o.data.polygons)>0 for o in meshes)
    assert all(p.area>1e-12 for o in meshes for p in o.data.polygons),'Degenerate faces'
    bounds=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    dimensions=[max(v[k] for v in bounds)-min(v[k] for v in bounds) for k in range(3)]
    expected=[manifest['boundsMeters'][1][k]-manifest['boundsMeters'][0][k] for k in range(3)]
    assert max(abs(a-b) for a,b in zip(sorted(dimensions),sorted(expected)))<.015,(dimensions,expected)
    data=path.with_suffix('.glb').read_bytes()
    magic,version,length=struct.unpack_from('<III',data)
    assert magic==0x46546c67 and version==2 and length==len(data)
    size,kind=struct.unpack_from('<II',data,12)
    gltf=json.loads(data[20:20+size]);assert kind==0x4e4f534a
    assert not gltf.get('cameras') and not gltf.get('animations')
    assert all('TEXCOORD_0' in p['attributes'] and 'NORMAL' in p['attributes'] for m in gltf['meshes'] for p in m['primitives'])
    glb_triangles=sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
    assert glb_triangles==triangles,(folder.name,glb_triangles,triangles)
    result={'item':folder.name,'passed':True,'triangles':triangles,'meshObjects':len(meshes),
            'fbxRoundTrip':'UVs, nondegenerate geometry, counts, scale, studio exclusion',
            'glbChecks':'Valid container, matching triangle count, normals, UVs, no cameras or unexpected animation',
            'provenance':'Source, FBX, and GLB hashes verified',
            'engineTested':False}
    (folder/'exports/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    results.append(result)
(ROOT/'art-source/blender/items/validation.json').write_text(json.dumps(results,indent=2)+'\n')
print('ITEM_VALIDATION',json.dumps(results))
