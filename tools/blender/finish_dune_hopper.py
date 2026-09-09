"""Review and package the open Dune Hopper scene; keep detailed source intact."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy

parser=argparse.ArgumentParser()
parser.add_argument('--views',default='hero,front,side,rear,top,steering')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/karts/dune-hopper'
EXPORTS=OUT/'exports'
REVIEW=OUT/'review/final'
GAME=ROOT/'game/Assets/_DarioKart/Art/Models/Karts'
for path in (EXPORTS,REVIEW,GAME): path.mkdir(parents=True,exist_ok=True)
source=Path(bpy.data.filepath)
driver_source=ROOT/'art-source/blender/characters/grit/grit-driver.blend'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
driver_hash=digest(driver_source)
scene=bpy.context.scene
root=bpy.data.objects['Dune_Hopper_Root']
rig=bpy.data.objects['Grit_Driver_Rig']
seat=bpy.data.objects['Dune_Seat_Root']
spare=bpy.data.objects['Dune_Spare_Mount']
controller_objects=list(bpy.data.collections['DUNE_CONTROLS'].objects)
driver=list(bpy.data.collections['GRIT_DRIVER'].objects)
collection_names=('DUNE_FRAME','DUNE_PANELS','DUNE_RUNNING_GEAR','DUNE_ENGINE','DUNE_COCKPIT','DUNE_SEAT','DUNE_DETAILS')
kart=[o for name in collection_names for o in bpy.data.collections[name].objects if o.type=='MESH']


def choose(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]


def tris(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)


def update_pose(steer,spin):
    root['steering_degrees']=float(steer)
    root['wheel_spin_degrees']=float(spin)
    root.update_tag()
    scene.frame_set(1)
    bpy.context.view_layer.update()


def matrix_error(a,b):
    return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))


# Check actual evaluated transforms, including the stationary carried spare.
update_pose(0,0)
centers={n:bpy.data.objects['Dune_Spin_'+n].matrix_world.translation.copy() for n in ('FL','FR','RL','RR')}
spare_before=spare.matrix_world.copy()
update_pose(22,35)
dg=bpy.context.evaluated_depsgraph_get()
for name in centers:
    steer=bpy.data.objects['Dune_Steer_'+name].evaluated_get(dg)
    spin=bpy.data.objects['Dune_Spin_'+name].evaluated_get(dg)
    assert abs(steer.rotation_euler.z-math.radians(22 if name.startswith('F') else 0))<1e-5
    assert abs(spin.rotation_euler.x-math.radians(35))<1e-5
    assert (spin.matrix_world.translation-centers[name]).length<1e-5
assert abs(bpy.data.objects['Dune_Steering_Spin'].evaluated_get(dg).rotation_euler.z-math.radians(27.5))<1e-5
assert matrix_error(spare.matrix_world,spare_before)<1e-6
update_pose(0,0)
assert seat.parent==root and rig.parent==root
seat_mesh=bpy.data.objects['Dune_Seat_Cushion']
seat_before=seat_mesh.matrix_world.copy()
rig_before=rig.matrix_world.copy()
rig.location.x+=1
bpy.context.view_layer.update()
assert matrix_error(seat_mesh.matrix_world,seat_before)<1e-6
rig.matrix_world=rig_before
bpy.context.view_layer.update()
driver_before={o.name:o.matrix_world.copy() for o in driver if o.type=='MESH'}
seat_root_before=seat.matrix_world.copy()
seat.location.x+=1
bpy.context.view_layer.update()
assert (seat_mesh.matrix_world.translation-seat_before.translation).length>.99
assert all(matrix_error(bpy.data.objects[n].matrix_world,m)<1e-6 for n,m in driver_before.items())
seat.matrix_world=seat_root_before
bpy.context.view_layer.update()
checks={'frontSteeringDegreesTested':22,'roadWheelSpinDegreesTested':35,
        'steeringWheelDegreesTested':27.5,'wheelCentersRemainFixed':True,
        'rearWheelsDoNotSteer':True,'spareRemainsFixed':True,
        'driverAndSeatMoveIndependently':True,'driverSourceUnchanged':True}

scene.camera=bpy.data.objects['Dune_Camera_hero']
scene.render.resolution_x=1500
scene.render.resolution_y=1230
scene.render.resolution_percentage=100
scene.cycles.samples=56
scene.render.filepath=str(REVIEW/'hero.png')
scene['asset_status']='Grit and Dune Hopper visual model; steering and wheel pivots tested. Unity gameplay remains separate.'
scene['kart_revision_source']=str(source.relative_to(ROOT))
choose([root])
blend=OUT/'grit-dune-hopper.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
views=[v for v in args.views.split(',') if v and v!='none']
for view in views:
    update_pose(22,35) if view=='steering' else update_pose(0,0)
    scene.camera=bpy.data.objects['Dune_Camera_'+('hero' if view=='steering' else view)]
    scene.render.filepath=str(REVIEW/('steering-test.png' if view=='steering' else view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('DUNE_FINAL_RENDER '+view,flush=True)
update_pose(0,0)

# Reduce exchange meshes only, after saving the detailed native scene.
before=sum(tris(o) for o in kart)
for obj in kart:
    if tris(obj)>350:
        choose([obj])
        modifier=obj.modifiers.new('Exchange reduction','DECIMATE')
        modifier.ratio=.22 if obj.name.startswith('Chunky_tread_') else .50
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    assert not obj.data.validate()
groups={}
for obj in kart: groups.setdefault(obj.parent,[]).append(obj)
runtime=[]
for parent,objects in groups.items():
    choose(objects)
    if len(objects)>1: bpy.ops.object.join()
    obj=bpy.context.object
    obj.name='Dune_Static_Body' if parent==root else parent.name+'_Mesh'
    runtime.append(obj)
assert len(runtime)==8,len(runtime)
choose(runtime)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008)
bpy.ops.object.mode_set(mode='OBJECT')
for obj in runtime:
    assert obj.data.uv_layers
    assert not obj.data.validate()
    assert all(math.isfinite(x) for vertex in obj.data.vertices for x in vertex.co)

choose([root]+runtime+[o for o in controller_objects if o!=root])
fbx=GAME/'dune-hopper.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH','EMPTY'},
    axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    use_mesh_modifiers=True,bake_anim=False,add_leaf_bones=False,use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'dune-hopper.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_animations=False,export_extras=True)
choose([root]+runtime+[o for o in controller_objects if o!=root]+driver)
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'grit-dune-hopper.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_animations=True,export_extras=True)

positions=[o.matrix_world@v.co for o in runtime for v in o.data.vertices]
bounds=[[min(v[k] for v in positions),max(v[k] for v in positions)] for k in range(3)]
palette={}
for obj in runtime:
    for mat in obj.data.materials:
        if not mat or mat.name in palette: continue
        p=mat.node_tree.nodes.get('Principled BSDF')
        if not p: continue
        palette[mat.name]={'baseColorLinearRGBA':list(p.inputs['Base Color'].default_value),
                         'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,
                         'coat':p.inputs['Coat Weight'].default_value,
                         'emissionLinearRGBA':list(p.inputs['Emission Color'].default_value),
                         'emissionStrength':p.inputs['Emission Strength'].default_value}
assert digest(driver_source)==driver_hash
checks.update({'kartMeshesUVmapped':True,'meshValidationPassed':True,'referenceAndStudioExcluded':True,
               'unityRendererVerified':False,'gameplayPhysicsImplemented':False})
outputs={'unityKartFBX':str(fbx.relative_to(ROOT)),
         'kartGLB':str((EXPORTS/'dune-hopper.glb').relative_to(ROOT)),
         'combinedGLB':str((EXPORTS/'grit-dune-hopper.glb').relative_to(ROOT))}
manifest={'schemaVersion':1,'id':'dune-hopper','source':str(blend.relative_to(ROOT)),
          'sourceSha256':digest(blend),'output':str(fbx.relative_to(ROOT)),'outputSha256':digest(fbx),
          'blenderVersion':bpy.app.version_string,'versionedSource':str(source.relative_to(ROOT)),
          'concept':'art-source/concepts/racers/round-02/02-grit-v2.png',
          'driver':str(driver_source.relative_to(ROOT)),'driverSourceSha256':driver_hash,
          'driverPlacementMeters':[0,.12,.58],'units':'meters','blenderForward':'-Y','exportUp':'Y',
          'nativeKartTriangles':before,'exportKartTriangles':sum(tris(o) for o in runtime),
          'driverTriangles':sum(tris(o) for o in driver if o.type=='MESH'),
          'exportKartMeshCount':len(runtime),'kartBoundsMetersXYZ':bounds,
          'wheelPivots':{n:{'steer':'Dune_Steer_'+n,'spin':'Dune_Spin_'+n,
                            'centerMeters':list(centers[n]),'radiusMeters':.547 if n.startswith('F') else .577}
                         for n in centers},
          'seatRoot':seat.name,'driverRoot':rig.name,'spareRoot':spare.name,
          'steeringWheelRoot':'Dune_Steering_Spin',
          'sockets':[o.name for o in controller_objects if o.name.startswith('Dune_Socket_')],
          'outputs':outputs,'outputHashes':{k:digest(ROOT/path) for k,path in outputs.items()},
          'checks':checks,'materials':palette}
(EXPORTS/'dune-hopper.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(GAME/'dune-hopper.export.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('DUNE_HOPPER_EXPORTED '+json.dumps({k:manifest[k] for k in ('exportKartTriangles','driverTriangles','exportKartMeshCount','checks')}),flush=True)
if views:
    scene.camera=bpy.data.objects['Dune_Camera_hero']
    scene.render.resolution_percentage=80
    scene.cycles.samples=40
    scene.render.filepath=str(REVIEW/'exchange-mesh-check.png')
    bpy.ops.render.render(write_still=True)
