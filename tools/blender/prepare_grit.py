"""Prepare a reviewed Grit sculpt as a separate, rigged driver asset."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/characters/grit'
EXPORTS=OUT/'exports'
REVIEW=OUT/'review/final'
for path in (EXPORTS,REVIEW): path.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--views',default='hero,front,side,rear,face,blink,pose,fit')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source=Path(bpy.data.filepath)
scene=bpy.context.scene
collection=bpy.data.collections['GRIT_DRIVER']
meshes=[o for o in collection.objects if o.type=='MESH']
report={'id':'grit-driver','sourceSculpt':str(source.relative_to(ROOT)),
        'sourceSculptSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'optimization':[],'checks':{}}


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def triangles(obj): return sum(len(p.vertices)-2 for p in obj.data.polygons)


# Keep the detailed source intact; reduce visible error rather than copying its dense mesh.
for obj in meshes:
    before=triangles(obj)
    target=350
    if obj.name=='Grit_Skin': target=23000
    elif obj.name.startswith('Horn_'): target=2600
    elif obj.name.startswith('Eye_'): target=2200
    elif obj.name.startswith(('Iris_','Pupil_')): target=700
    elif obj.name.startswith(('Upper_Lip','Lower_Lip')): target=900
    elif obj.name.startswith('Crest_'): target=500
    elif obj.name.startswith('Tooth_'): target=240
    elif obj.name=='Mouth_Cavity': target=500
    if obj.data.shape_keys or before<=target: continue
    original=[v.co.copy() for v in obj.data.vertices]
    select(obj)
    m=obj.modifiers.new('Driver exchange reduction','DECIMATE')
    m.ratio=target/before
    bpy.ops.object.modifier_apply(modifier=m.name)
    obj.data.validate()
    tree=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[p.vertices[:] for p in obj.data.polygons])
    errors=[tree.find_nearest(v)[3] for v in original[::max(1,len(original)//3000)]]
    error=max(errors,default=0)
    assert error<.009,(obj.name,error)
    report['optimization'].append({'mesh':obj.name,'beforeTriangles':before,'afterTriangles':triangles(obj),
                                   'sampledMaxSurfaceDeviationMeters':error})
for obj in meshes: obj.data.validate()
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes: obj.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['Grit_Skin']
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.15)
bpy.ops.object.mode_set(mode='OBJECT')

arm=bpy.data.armatures.new('Grit_Driver_Skeleton')
rig=bpy.data.objects.new('Grit_Driver_Rig',arm)
collection.objects.link(rig)
rig.show_in_front=True
rig['instructions']='Object Mode moves the whole driver. Pose head, chest, arms, hands, thighs and feet. Blink lives on Upper_Lid_Center.'
rig['seat_is_separate']=True
select(rig)
bpy.ops.object.mode_set(mode='EDIT')
specs=[('root',(0,0,.12),(0,0,.25),None),('pelvis',(0,0,.25),(0,.015,.52),'root'),
       ('chest',(0,.015,.52),(0,.035,.84),'pelvis'),('head',(0,.035,.84),(0,.05,1.48),'chest')]
for s,side in [(-1,'L'),(1,'R')]:
    specs += [('upper_arm.'+side,(s*.32,0,.965),(s*.465,-.245,.686),'chest'),
              ('forearm.'+side,(s*.465,-.245,.686),(s*.281,-.59,.733),'upper_arm.'+side),
              ('hand.'+side,(s*.281,-.59,.733),(s*.281,-.732,.726),'forearm.'+side),
              ('thigh.'+side,(s*.198,.015,.28),(s*.20,-.245,.275),'pelvis'),
              ('foot.'+side,(s*.20,-.245,.275),(s*.202,-.59,.195),'thigh.'+side)]
for name,head,tail,parent in specs:
    b=arm.edit_bones.new(name)
    b.head,b.tail=head,tail
    if parent: b.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
segments={n:(Vector(h),Vector(t)) for n,h,t,_ in specs}


def smooth(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)))
    return t*t*(3-2*t)


def distance(p,a,b):
    v=b-a
    return (p-a-v*min(1,max(0,(p-a).dot(v)/v.length_squared))).length


for obj in meshes:
    groups={n:obj.vertex_groups.new(name=n) for n,*_ in specs}
    for v in obj.data.vertices:
        if obj.name!='Grit_Skin':
            groups['head'].add([v.index],1,'REPLACE')
            continue
        p=obj.matrix_world@v.co
        x,y,z=p
        side='L' if x<0 else 'R'
        head=smooth(.70,.86,z)
        chest=smooth(.34,.60,z)*(1-head)
        weights={'head':head,'chest':chest,'pelvis':max(0,1-head-chest)}
        arm_weight=max(smooth(.34,.46,abs(x)),smooth(.34,.46,-y))*(1-smooth(.88,1.035,z))*smooth(.48,.58,z)
        if arm_weight>.0001:
            near=sorted((distance(p,*segments[n]),n) for n in ('upper_arm.'+side,'forearm.'+side,'hand.'+side))[:2]
            w=[1/(d+.018)**4 for d,n in near]
            for n in weights: weights[n]*=1-arm_weight
            for (_,n),value in zip(near,w): weights[n]=arm_weight*value/sum(w)
        if z<.42:
            leg=(1-smooth(.29,.42,z))*smooth(.035,.125,abs(x))
            foot=smooth(.15,.35,-y)
            for n in weights: weights[n]*=1-leg
            weights['thigh.'+side]=leg*(1-foot)
            weights['foot.'+side]=leg*foot
        active=sorted(((w,n) for n,w in weights.items() if w>.00001),reverse=True)[:4]
        total=sum(w for w,n in active)
        for w,n in active: groups[n].add([v.index],w/total,'REPLACE')
    mod=obj.modifiers.new('Grit driver deformation','ARMATURE')
    mod.object=rig
    mod.use_deform_preserve_volume=True
    obj.parent=rig

scene.render.fps=30
scene.frame_start,scene.frame_end=1,120
head=rig.pose.bones['head']
head.rotation_mode='XYZ'
for frame,angle in [(1,0),(30,.018),(60,0),(90,-.018),(120,0)]:
    head.rotation_euler.z=angle
    head.keyframe_insert(data_path='rotation_euler',frame=frame)
rig.animation_data.action.name='Grit_Seated_Idle'
lid=bpy.data.objects['Upper_Lid_Center']
blink=lid.data.shape_keys.key_blocks['Blink']
for frame,value in [(1,0),(42,0),(44,1),(47,0),(120,0)]:
    blink.value=value
    blink.keyframe_insert(data_path='value',frame=frame)
lid.data.shape_keys.animation_data.action.name='Grit_Blink'
scene.frame_set(1)
for obj in meshes:
    assert obj.data.uv_layers
    assert not obj.data.validate()
    for v in obj.data.vertices:
        assert 1<=len(v.groups)<=4
        assert abs(sum(g.weight for g in v.groups)-1)<.0001
        assert all(math.isfinite(k) for k in v.co)
report['checks']={'triangles':sum(triangles(o) for o in meshes),'meshes':len(meshes),'bones':len(arm.bones),
                  'blinkTargets':1,'UVmapped':True,'normalizedWeights':True,'maxBoneInfluences':4,
                  'seatedIdleFrames':[1,120],'unityRendererVerified':False}
scene.camera=bpy.data.objects['Grit_Camera_hero']
scene.render.resolution_x=scene.render.resolution_y=1300
scene.cycles.samples=56
scene['asset_status']='Grit driver: reviewed sculpt, rig and separate fitting aids. See README for remaining runtime work.'
select(rig)
review_blend=OUT/'grit-driver-review.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(review_blend))
for view in args.views.split(','):
    if view in ('none','blink','pose','fit'): continue
    scene.camera=bpy.data.objects['Grit_Camera_'+view]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('GRIT_FINAL_RENDER '+view,flush=True)
if 'blink' in args.views.split(','):
    scene.frame_set(44)
    assert blink.value>.99
    scene.camera=bpy.data.objects['Grit_Camera_face']
    scene.render.filepath=str(REVIEW/'blink-test.png')
    bpy.ops.render.render(write_still=True)
scene.frame_set(1)
if 'pose' in args.views.split(','):
    idle=rig.animation_data.action
    rig.animation_data.action=None
    head.rotation_euler.z=math.radians(7)
    for side,angle in [('L',-8),('R',8)]:
        bone=rig.pose.bones['forearm.'+side]
        bone.rotation_mode='XYZ'
        bone.rotation_euler.y=math.radians(angle)
    bpy.context.view_layer.update()
    scene.camera=bpy.data.objects['Grit_Camera_hero']
    scene.render.filepath=str(REVIEW/'pose-test.png')
    bpy.ops.render.render(write_still=True)
    for bone in rig.pose.bones: bone.rotation_euler=(0,0,0)
    rig.animation_data.action=idle
scene.frame_set(1)
if 'fit' in args.views.split(','):
    guide=bpy.data.collections['FIT_GUIDE_NOT_FOR_EXPORT']
    guide.hide_render=False
    scene.camera=bpy.data.objects['Grit_Camera_hero']
    scene.render.filepath=str(REVIEW/'seat-and-wheel-fit.png')
    bpy.ops.render.render(write_still=True)
    guide.hide_render=True

# Export only the independent character. All scene dressing and fitting aids are omitted.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in meshes: obj.select_set(True)
bpy.context.view_layer.objects.active=rig
fbx=EXPORTS/'grit-driver.fbx'
glb=EXPORTS/'grit-driver.glb'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH','ARMATURE'},
    axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    add_leaf_bones=False,use_armature_deform_only=True,use_mesh_modifiers=False,bake_anim=True,
    bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,
                        export_animations=True,export_extras=True)
verts=[obj.matrix_world@v.co for obj in meshes for v in obj.data.vertices]
report['boundsMetersXYZ']=[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]

# The main driver file is clean: no seat, wheel, lights, floor, or reference objects.
keep=set([rig]+meshes)
for obj in list(bpy.data.objects):
    if obj not in keep: bpy.data.objects.remove(obj,do_unlink=True)
for col in list(bpy.data.collections):
    if not col.all_objects: bpy.data.collections.remove(col)
scene.camera=None
scene.compositing_node_group=None
scene['asset_status']='Grit only. Seat and steering wheel are separate fitting aids in grit-driver-review.blend.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_perspective='PERSP'
            space.region_3d.view_location=(0,-.08,1)
            space.region_3d.view_distance=3.3
            space.region_3d.view_rotation=Vector((3,-6,2.5)).to_track_quat('Z','Y')
            space.shading.type='MATERIAL'
            space.overlay.show_overlays=True
select(rig)
blend=OUT/'grit-driver.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report.update({'source':str(blend.relative_to(ROOT)),'sourceSha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
               'output':str(fbx.relative_to(ROOT)),'outputSha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),
               'glb':str(glb.relative_to(ROOT)),'glbSha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
               'blenderVersion':bpy.app.version_string,'units':'meters','forward':'-Y','up':'Z'})
(EXPORTS/'grit-driver.export.json').write_text(json.dumps(report,indent=2)+'\n')
print('GRIT_PREPARED '+json.dumps(report['checks']),flush=True)
