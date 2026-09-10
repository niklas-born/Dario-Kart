"""Export the turn authoring scenes to a scene-baked GLB and Unity pose sweep.

The FBX contains a two-second left-to-right steering sweep, with no root motion
or wheel roll. Sample its time from steering input; roll the Spin pivots in code.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from animate_kart_turns import CONFIGS, ROOT


def package(kart):
    cfg = CONFIGS[kart]
    folder = ROOT / 'art-source/blender/karts' / kart
    bpy.ops.wm.open_mainfile(filepath=str(folder / (cfg['stem'] + '-turns.blend')))
    scene = bpy.context.scene
    scene.frame_set(1)
    root = bpy.data.objects[cfg['root']]
    rig = bpy.data.objects[cfg['rig']]
    objects = [root, *root.children_recursive]
    meshes = [o for o in objects if o.type == 'MESH']
    # Radial eye decals in the source have inward winding. Blender's two-sided
    # shading hides this, but Unity back-face culling drops the irises/pupils.
    # Correct export copies without touching the accepted sculpt or its weights.
    for obj in meshes:
        if obj.name.startswith(('Iris', 'Pupil')):
            toward_back = sum((obj.matrix_world.to_3x3() @ p.normal).y for p in obj.data.polygons)
            if toward_back > 0:
                obj.data.flip_normals()
    # Reduce only rigid kart parts. Driver skinning, blink and native file remain intact.
    groups = {}
    for obj in meshes:
        if any(m.type == 'ARMATURE' for m in obj.modifiers):
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if sum(len(p.vertices) - 2 for p in obj.data.polygons) > 350:
            modifier = obj.modifiers.new('Turn export reduction', 'DECIMATE')
            modifier.ratio = .62
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        groups.setdefault(obj.parent, []).append(obj)
    for parent, members in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        if len(members) > 1:
            bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = cfg['stem'] + '_' + parent.name
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.012)
        bpy.ops.object.mode_set(mode='OBJECT')
    objects = [root, *root.children_recursive]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    scene.name = cfg['stem'] + '_Turn_Rehearsal'
    bpy.ops.export_scene.gltf(filepath=str(folder / 'exports' / (cfg['stem'] + '-turns.glb')),
        export_format='GLB', use_selection=True, export_yup=True, export_extras=True,
        export_animations=True, export_animation_mode='SCENE', export_force_sampling=True,
        export_bake_animation=True, export_anim_scene_split_object=False)

    # Replace the rehearsal with a deterministic pose lookup table for gameplay.
    root.animation_data_clear()
    root.rotation_euler = (0, 0, 0)
    root['travel_meters'] = root['wheel_spin_degrees'] = 0.0
    if rig.animation_data:
        rig.animation_data.action = None  # Keep the chest/gaze drivers.
    rig.pose.bones['head'].rotation_euler = (0, 0, 0)
    for obj in objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            obj.data.shape_keys.animation_data_clear()
            for key in obj.data.shape_keys.key_blocks:
                key.value = 0
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, 61
    for frame in range(1, 62):
        root['steering_degrees'] = -28.0 + 56.0 * (frame - 1) / 60
        root.keyframe_insert(data_path='["steering_degrees"]', frame=frame)
    root.animation_data.action.name = 'SteeringPose'
    scene.frame_set(31)
    out = ROOT / 'game/Assets/_DarioKart/Art/Models/Karts/Turns'
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(out / (cfg['stem'] + '-turns.fbx')),
        use_selection=True, object_types={'MESH', 'EMPTY', 'ARMATURE'},
        axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS', use_mesh_modifiers=True, use_triangles=True,
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0, add_leaf_bones=False, use_custom_props=True)
    palette = []
    for mat in {m for o in objects if o.type == 'MESH' for m in o.data.materials if m}:
        node = mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
        color = list(node.inputs['Base Color'].default_value if node else mat.diffuse_color)
        palette.append(dict(name=mat.name, color=color,
            metallic=node.inputs['Metallic'].default_value if node else 0,
            roughness=node.inputs['Roughness'].default_value if node else .5))
    (out / (cfg['stem'] + '-turns.json')).write_text(json.dumps(dict(
        id=cfg['stem'], frontRadius=cfg['radii'][0], rearRadius=cfg['radii'][1],
        spinPrefix=cfg['prefix'], materials=sorted(palette, key=lambda m: m['name'])), indent=2) + '\n')
    print('TURN_EXPORT_COMPLETE', kart, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kart', choices=['all', *CONFIGS], default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    for kart in CONFIGS if args.kart == 'all' else [args.kart]:
        package(kart)
