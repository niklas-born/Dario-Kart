"""Check, package, and export the open Streamliner Blender scene.

Keeps the detailed authoring scene; reduces and groups only the exchange meshes.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser=argparse.ArgumentParser()
parser.add_argument('--views',default='hero,front,side,rear,top,steering',help='Comma-separated review views, or none for export only')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/karts/streamliner'
EXPORTS=OUT/'exports'
REVIEW=OUT/'review/final'
GAME=ROOT/'game/Assets/_DarioKart/Art/Models/Karts'
for p in (EXPORTS,REVIEW,GAME):
    p.mkdir(parents=True,exist_ok=True)
source=Path(bpy.data.filepath)
scene=bpy.context.scene
root=bpy.data.objects['Streamliner_Root']
controls=bpy.data.collections['STREAMLINER_CONTROLS']
cart_collections=[bpy.data.collections[n] for n in ('STREAMLINER_BODYWORK','STREAMLINER_RUNNING_GEAR','STREAMLINER_DETAILS','STREAMLINER_COCKPIT','STREAMLINER_SEAT') if n in bpy.data.collections]
cart=[o for c in cart_collections for o in c.objects if o.type=='MESH']
driver=list(bpy.data.collections['RIFF_DRIVER'].objects)

# Keep the bottom of the cockpit lining inside the curved hull, including older drafts.
shell=bpy.data.objects['Streamliner_Monocoque']
tree=BVHTree.FromPolygons([v.co for v in shell.data.vertices],[p.vertices[:] for p in shell.data.polygons])
liner=bpy.data.objects['Cockpit_inner_tub']
for vertex in list(liner.data.vertices)[:128]:
    origin=vertex.co.copy()
    origin.z=-2
    hit,normal,_,_=tree.ray_cast(origin,Vector((0,0,1)),5)
    if hit is not None:
        vertex.co.z=max(vertex.co.z,hit.z+.025)


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def tri_count(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)


def parent(obj,p):
    bpy.context.view_layer.update()
    world=obj.matrix_world.copy()
    obj.parent=p
    obj.matrix_world=world


# Keep the seat independently selectable, including in the exchange files.
seat_collection=bpy.data.collections.get('STREAMLINER_SEAT')
if seat_collection is None:
    seat_collection=bpy.data.collections.new('STREAMLINER_SEAT')
    scene.collection.children.link(seat_collection)
seat_root=bpy.data.objects.get('Seat_Root')
if seat_root is None:
    seat_root=bpy.data.objects.new('Seat_Root',None)
    controls.objects.link(seat_root)
    seat_root.location=bpy.data.objects['Socket_Driver_Seat'].matrix_world.translation
    seat_root.empty_display_size=.15
    parent(seat_root,root)
seat_root['instructions']='Move Seat_Root to move only the cushion and back. Riff moves with Riff_Driver_Rig.'
for name in ('Seat_Cushion','Seat_Back'):
    obj=bpy.data.objects[name]
    parent(obj,seat_root)
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    seat_collection.objects.link(obj)

# The steering wheel rotates around its tilted column axis.
wheel=bpy.data.objects['Steering_Wheel']
frame=bpy.data.objects.get('SteeringWheel_Frame')
if frame is None:
    frame=bpy.data.objects.new('SteeringWheel_Frame',None)
    controls.objects.link(frame)
    frame.matrix_world=wheel.matrix_world.copy()
    parent(frame,root)
spin=bpy.data.objects.get('SteeringWheel_Spin')
if spin is None:
    spin=bpy.data.objects.new('SteeringWheel_Spin',None)
    controls.objects.link(spin)
    spin.parent=frame
    spin.location=(0,0,0)
for obj in list(bpy.data.collections['STREAMLINER_COCKPIT'].objects):
    if obj.name=='Steering_Wheel' or obj.name.startswith(('Steering_Spoke','Wheel_Hub')):
        parent(obj,spin)
f=spin.driver_add('rotation_euler',2).driver
for variable in list(f.variables):
    f.variables.remove(variable)
v=f.variables.new()
v.name='angle'
v.targets[0].id=root
v.targets[0].data_path='["steering_degrees"]'
f.expression='angle * 0.0226892802759263'
root['controls_help']='steering_degrees turns the front wheels and steering wheel; wheel_spin_degrees rotates all tires.'
root['integration_note']='Visual controls only. Runtime code drives the named transform pivots.'


def update_pose(steer,rotation):
    root['steering_degrees']=steer
    root['wheel_spin_degrees']=rotation
    root.update_tag()
    scene.frame_set(1)
    bpy.context.view_layer.update()


update_pose(22,35)
dg=bpy.context.evaluated_depsgraph_get()
checks={}
for name in ('FL','FR'):
    value=bpy.data.objects['Steer_'+name].evaluated_get(dg).rotation_euler.z
    assert abs(value-math.radians(22))<.0001,(name,value)
for name in ('FL','FR','RL','RR'):
    value=bpy.data.objects['Spin_'+name].evaluated_get(dg).rotation_euler.x
    assert abs(value-math.radians(35))<.0001,(name,value)
    center=bpy.data.objects['Spin_'+name].matrix_world.translation
    steer_center=bpy.data.objects['Steer_'+name].matrix_world.translation
    assert (center-steer_center).length<.00001
checks.update({'frontSteeringDegreesTested':22,'wheelSpinDegreesTested':35,'wheelCentersRemainFixed':True})
update_pose(0,0)

# Capture a useful top view without cutting off the long nose or tail.
bpy.data.objects['Kart_Camera_top'].data.ortho_scale=6.25
scene.camera=bpy.data.objects['Kart_Camera_hero']
scene.render.resolution_x=1500
scene.render.resolution_y=1170
scene.cycles.samples=64
scene.render.filepath=str(REVIEW/'hero.png')
scene['asset_status']='Riff with Streamliner; modeled and visually reviewed; Unity gameplay not implemented.'
scene['kart_revision_source']=str(source.relative_to(ROOT))
scene['native_driver_source']='art-source/blender/characters/riff/riff-driver.blend'
select(root)
blend=OUT/'riff-streamliner.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

for view in [v for v in args.views.split(',') if v and v not in ('steering','none')]:
    scene.camera=bpy.data.objects['Kart_Camera_'+view]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('FINAL_RENDER '+view,flush=True)
if 'steering' in args.views.split(','):
    update_pose(22,35)
    scene.camera=bpy.data.objects['Kart_Camera_hero']
    scene.render.filepath=str(REVIEW/'steering-test.png')
    bpy.ops.render.render(write_still=True)
update_pose(0,0)

# Optimize copies in memory after saving the full authoring file.
before=sum(tri_count(o) for o in cart)
for obj in cart:
    if tri_count(obj)>350:
        select(obj)
        m=obj.modifiers.new('Exchange mesh reduction','DECIMATE')
        m.ratio=.62
        bpy.ops.object.modifier_apply(modifier=m.name)
    obj.data.validate()
groups={}
for obj in cart:
    groups.setdefault(obj.parent,[]).append(obj)
runtime=[]
for p,objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects)>1:
        bpy.ops.object.join()
    obj=bpy.context.object
    obj.name='Streamliner_Static' if p==root else 'Streamliner_'+p.name+'_Mesh'
    runtime.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for obj in runtime:
    obj.select_set(True)
bpy.context.view_layer.objects.active=runtime[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012)
bpy.ops.object.mode_set(mode='OBJECT')
for obj in runtime:
    assert obj.data.uv_layers
    assert not obj.data.validate()
    assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)

controller_objects=list(controls.objects)


def choose(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=root


def fbx(path):
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','EMPTY'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_mesh_modifiers=True,bake_anim=False,add_leaf_bones=False,use_custom_props=True)


choose(runtime+controller_objects)
fbx(GAME/'streamliner.fbx')
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'streamliner.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_animations=False,export_extras=True)
choose(runtime+controller_objects+driver)
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'riff-streamliner.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_animations=True,export_extras=True)

positions=[o.matrix_world@v.co for o in runtime for v in o.data.vertices]
bounds=[[min(v[k] for v in positions),max(v[k] for v in positions)] for k in range(3)]
palette={}
for obj in runtime:
    for m in obj.data.materials:
        if not m or m.name in palette:
            continue
        p=m.node_tree.nodes.get('Principled BSDF')
        if not p:
            continue
        palette[m.name]={'baseColorLinearRGBA':list(p.inputs['Base Color'].default_value),
                         'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,
                         'transmission':p.inputs['Transmission Weight'].default_value}
checks.update({'kartMeshesUVmapped':True,'meshValidationPassed':True,'referenceAndStudioExcluded':True,
               'unityRendererVerified':False,'gameplayPhysicsImplemented':False})
manifest={'schemaVersion':1,'id':'streamliner','source':str(blend.relative_to(ROOT)),
          'sourceSha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
          'output':str((GAME/'streamliner.fbx').relative_to(ROOT)),
          'outputSha256':hashlib.sha256((GAME/'streamliner.fbx').read_bytes()).hexdigest(),
          'blenderVersion':bpy.app.version_string,
          'versionedSource':str(source.relative_to(ROOT)),
          'concept':'art-source/concepts/racers/round-02/01-riff-v2.png',
          'driver':'art-source/blender/characters/riff/riff-driver.blend',
          'driverPlacementMeters':[0,.10,.38],'units':'meters','blenderForward':'-Y','exportUp':'Y',
          'nativeKartTriangles':before,'exportKartTriangles':sum(tri_count(o) for o in runtime),
          'driverTriangles':sum(tri_count(o) for o in driver if o.type=='MESH'),
          'exportKartMeshCount':len(runtime),'kartBoundsMetersXYZ':bounds,
          'wheelPivots':{n:{'steer':'Steer_'+n,'spin':'Spin_'+n,'radiusMeters':.435 if n.startswith('F') else .603} for n in ('FL','FR','RL','RR')},
          'seatRoot':'Seat_Root','driverRoot':'Riff_Driver_Rig',
          'sockets':[o.name for o in controller_objects if o.name.startswith('Socket_')],
          'outputs':{'unityKartFBX':str((GAME/'streamliner.fbx').relative_to(ROOT)),
                     'kartGLB':str((EXPORTS/'streamliner.glb').relative_to(ROOT)),
                     'combinedGLB':str((EXPORTS/'riff-streamliner.glb').relative_to(ROOT))},
          'checks':checks,'materials':palette}
(EXPORTS/'streamliner.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(GAME/'streamliner.export.json').write_text(json.dumps({k:manifest[k] for k in ('schemaVersion','id','source','sourceSha256','output','outputSha256','blenderVersion','units','outputs','wheelPivots','driverPlacementMeters','materials')},indent=2)+'\n')
print('STREAMLINER_EXPORTED '+json.dumps({k:manifest[k] for k in ('exportKartTriangles','driverTriangles','exportKartMeshCount','checks')}),flush=True)
if args.views!='none':
    scene.camera=bpy.data.objects['Kart_Camera_hero']
    scene.render.resolution_percentage=75
    scene.cycles.samples=40
    scene.render.filepath=str(REVIEW/'exchange-mesh-check.png')
    bpy.ops.render.render(write_still=True)
