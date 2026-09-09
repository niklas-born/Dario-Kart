"""Prepare the reviewed Riff sculpt as a UV-mapped, poseable driver.

Open a versioned sculpt with Blender --background, then run this script.
The versioned sculpt is preserved; outputs go to riff-driver.blend and exports/.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art-source/blender/characters/riff'
REVIEW = OUT / 'review/rigged'
EXPORTS = OUT / 'exports'
for p in (REVIEW, EXPORTS):
    p.mkdir(parents=True, exist_ok=True)
source = Path(bpy.data.filepath)
scene = bpy.context.scene
collection = bpy.data.collections['RIFF_DRIVER']
meshes = [o for o in collection.objects if o.type == 'MESH']
report = {'sourceSculpt': str(source.relative_to(ROOT)), 'optimization': [], 'checks': {}}
report['meshCleanup'] = []


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def tri_count(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)


# Retain the dense, editable sculpt in its versioned source file.
for obj in meshes:
    initial = tri_count(obj)
    target = 400
    if obj.name == 'Riff_Skin':
        target = 24000
    elif obj.name.startswith('Horn_'):
        target = 2600
    elif obj.name.startswith('Eye_'):
        target = 1400
    elif obj.name.startswith(('Iris_', 'Pupil_')):
        target = 480
    elif obj.name.startswith(('Lower_Lip', 'Upper_Lip', 'Gums_')):
        target = 600
    elif obj.name.startswith('Crown_Tuft_'):
        target = 700
    elif obj.name.startswith('Eyebrow_'):
        target = 650
    if obj.data.shape_keys or initial <= target:
        continue
    original = [v.co.copy() for v in obj.data.vertices]
    select(obj)
    m = obj.modifiers.new('Driver LOD0 reduction', 'DECIMATE')
    m.ratio = target / initial
    bpy.ops.object.modifier_apply(modifier=m.name)
    tree = BVHTree.FromPolygons([v.co for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons])
    errors = [tree.find_nearest(v)[3] for v in original[::max(1, len(original)//2500)]]
    assert max(errors, default=0) < .012, f'Excessive reduction deviation: {obj.name}'
    report['optimization'].append({'mesh': obj.name, 'before': initial, 'after': tri_count(obj),
                                   'sampledMaxSurfaceDeviationMeters': round(max(errors, default=0), 6)})

# One atlas layout across the driver leaves space for subsequent painted/baked detail.
for obj in meshes:
    if obj.data.validate(verbose=True):
        report['meshCleanup'].append(obj.name)
    assert not obj.data.validate(), 'Mesh validation did not converge: '+obj.name
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Riff_Skin']
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.018, area_weight=.1)
bpy.ops.object.mode_set(mode='OBJECT')

arm = bpy.data.armatures.new('Riff_Driver_Skeleton')
rig = bpy.data.objects.new('Riff_Driver_Rig', arm)
collection.objects.link(rig)
rig.show_in_front = True
rig['instructions'] = 'Pose mode: head/chest, upper_arm/forearm/hand, thigh/foot. Blink is on both Upper_Lid meshes.'
select(rig)
bpy.ops.object.mode_set(mode='EDIT')
specs = [
    ('root', (0,0,.12), (0,0,.28), None),
    ('pelvis', (0,.04,.28), (0,.02,.60), 'root'),
    ('chest', (0,.02,.60), (0,0,.94), 'pelvis'),
    ('head', (0,0,.94), (0,0,1.47), 'chest'),
]
for sign, side in [(-1,'L'), (1,'R')]:
    specs += [
        ('upper_arm.'+side, (sign*.28,0,1.00), (sign*.434,-.22,.79), 'chest'),
        ('forearm.'+side, (sign*.434,-.22,.79), (sign*.277,-.57,.84), 'upper_arm.'+side),
        ('hand.'+side, (sign*.277,-.57,.84), (sign*.277,-.71,.835), 'forearm.'+side),
        ('thigh.'+side, (sign*.21,.01,.31), (sign*.21,-.22,.275), 'pelvis'),
        ('foot.'+side, (sign*.21,-.22,.275), (sign*.21,-.57,.21), 'thigh.'+side),
    ]
for name, head, tail, parent in specs:
    b = arm.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
segments = {name: (Vector(head), Vector(tail)) for name, head, tail, _ in specs}


def smoothstep(a, b, value):
    t = min(1, max(0, (value-a)/(b-a)))
    return t*t*(3-2*t)


def distance_to_segment(p, a, b):
    d = b-a
    return (p-(a+d*min(1,max(0,(p-a).dot(d)/d.length_squared)))).length


for obj in meshes:
    groups = {name: obj.vertex_groups.new(name=name) for name, *_ in specs}
    for v in obj.data.vertices:
        if obj.name != 'Riff_Skin':
            groups['head'].add([v.index], 1, 'REPLACE')
            continue
        p = obj.matrix_world @ v.co
        x,y,z = p
        side = 'L' if x < 0 else 'R'
        head = smoothstep(.82,.94,z)
        chest = smoothstep(.40,.69,z)*(1-head)
        weights = {'head': head, 'chest': chest, 'pelvis': max(0,1-head-chest)}
        arm_weight = max(smoothstep(.31,.43,abs(x)), smoothstep(.32,.43,-y)) * (1-smoothstep(.91,1.06,z)) * smoothstep(.54,.65,z)
        if arm_weight > .0001:
            candidates = ['upper_arm.'+side, 'forearm.'+side, 'hand.'+side]
            near = sorted((distance_to_segment(p,*segments[n]), n) for n in candidates)[:2]
            values = [1/(d+.018)**4 for d,n in near]
            for key in weights:
                weights[key] *= 1-arm_weight
            for (_,name), w in zip(near, values):
                weights[name] = arm_weight*w/sum(values)
        if z < .4:
            leg = (1-smoothstep(.29,.40,z))*smoothstep(.035,.13,abs(x))
            foot = smoothstep(.13,.34,-y)
            for key in weights:
                weights[key] *= 1-leg
            weights['thigh.'+side] = leg*(1-foot)
            weights['foot.'+side] = leg*foot
        active = sorted(((w,n) for n,w in weights.items() if w > .00001), reverse=True)[:4]
        total = sum(w for w,n in active)
        for w,n in active:
            groups[n].add([v.index], w/total, 'REPLACE')
    mod = obj.modifiers.new('Riff driver deformation', 'ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = True
    obj.parent = rig

# A subtle seated idle and blink demonstrate that the driver is poseable.
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, 120
head = rig.pose.bones['head']
head.rotation_mode = 'XYZ'
for frame, angle in [(1,0),(30,.022),(60,0),(90,-.022),(120,0)]:
    head.rotation_euler.z = angle
    head.keyframe_insert(data_path='rotation_euler', frame=frame)
rig.animation_data.action.name = 'Riff_Seated_Idle'
for obj in meshes:
    if not obj.data.shape_keys:
        continue
    key = obj.data.shape_keys.key_blocks['Blink']
    for frame, value in [(1,0),(42,0),(44,1),(47,0),(120,0)]:
        key.value = value
        key.keyframe_insert(data_path='value', frame=frame)
    obj.data.shape_keys.animation_data.action.name = 'Riff_Blink_'+obj.name[-1]
scene.frame_set(1)

for obj in meshes:
    assert obj.data.uv_layers, 'Missing UVs: '+obj.name
    assert not obj.data.validate(), 'Invalid geometry repaired: '+obj.name
    for v in obj.data.vertices:
        assert 1 <= len(v.groups) <= 4
        assert abs(sum(g.weight for g in v.groups)-1) < .0001
report['checks'].update({'allMeshesUVmapped': True, 'weightsNormalized': True, 'maxBoneInfluences': 4,
                         'boneCount': len(arm.bones), 'triangles': sum(tri_count(o) for o in meshes),
                         'seatedIdleFrames': [1,120], 'blinkFullyClosedFrame': 44,
                         'runtimeRendererVerified': False})
scene['concept_status'] = 'Riff driver after iterative concept comparison; see README and review images for scope.'
scene['source_sculpt'] = str(source.relative_to(ROOT))
scene['asset_id'] = 'riff-driver'
scene.camera = bpy.data.objects['Camera_driver_hero']
for name in ('Studio_Ground','Studio_Backdrop'):
    bpy.data.objects[name].visible_camera = False
for node in scene.world.node_tree.nodes:
    if node.type == 'BACKGROUND' and node.name != 'Background':
        node.inputs['Strength'].default_value = 1
select(rig)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_perspective = 'CAMERA'
            space.shading.type = 'MATERIAL'
            space.overlay.show_overlays = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'riff-driver.blend'))

# Export only the actual driver; no camera, seat, wheel, floor, or concept images.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(filepath=str(EXPORTS/'riff-driver.fbx'), use_selection=True,
                         object_types={'MESH','ARMATURE'}, axis_forward='-Z', axis_up='Y',
                         apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                         add_leaf_bones=False, use_armature_deform_only=True,
                         use_mesh_modifiers=False, bake_anim=True,
                         bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         bake_anim_simplify_factor=0)
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'riff-driver.glb'), export_format='GLB',
                          use_selection=True, export_yup=True, export_animations=True)
(EXPORTS/'riff-driver.provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print('RIFF_PREPARED '+json.dumps(report['checks']), flush=True)

scene.cycles.samples = 64
for name in ('driver_front','driver_hero','driver_side'):
    scene.camera = bpy.data.objects['Camera_'+name]
    scene.render.filepath = str(REVIEW/(name+'.png'))
    bpy.ops.render.render(write_still=True)
scene.frame_set(44)
scene.camera = bpy.data.objects['Camera_driver_hero']
scene.render.filepath = str(REVIEW/'blink-test.png')
bpy.ops.render.render(write_still=True)
scene.frame_set(1)
idle_action = rig.animation_data.action
rig.animation_data.action = None
head.rotation_euler.z = math.radians(7)
bpy.context.view_layer.update()
assert abs(head.rotation_euler.z-math.radians(7)) < .00001
scene.render.filepath = str(REVIEW/'head-turn-test.png')
bpy.ops.render.render(write_still=True)
head.rotation_euler.z = 0
rig.animation_data.action = idle_action
scene.frame_set(1)
