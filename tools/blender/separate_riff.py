"""Extract aligned, independently editable driver and seat files from the kart.

Run after finish_streamliner.py. The assembled file and its placement are preserved.
"""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
KART = ROOT / 'art-source/blender/karts/streamliner'
DRIVER = ROOT / 'art-source/blender/characters/riff'
SOURCE = KART / 'riff-streamliner.blend'
report = {'source': str(SOURCE.relative_to(ROOT)),
          'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'units': 'meters', 'placement': 'Original assembled Blender coordinates retained',
          'parts': {}}


def detach(obj):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = world
    bpy.context.view_layer.update()


def positions(objects):
    bpy.context.view_layer.update()
    return {o.name: [o.matrix_world @ v.co for v in o.data.vertices]
            for o in objects if o.type == 'MESH'}


def save_part(label, names, root_name, path):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    objects = [bpy.data.objects[n] for n in names]
    before = positions(objects)
    root = bpy.data.objects[root_name]
    detach(root)
    for obj in list(bpy.data.objects):
        if obj.name not in names:
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if not collection.all_objects:
            bpy.data.collections.remove(collection)
    after = positions(objects)
    error = max((a-b).length for name in before for a,b in zip(before[name],after[name]))
    assert error < 1e-6, (label,error)
    assert root.parent is None
    assert {o.name for o in scene.objects} == set(names)
    if label == 'driver':
        assert len(root.data.bones) == 14
        assert root.animation_data.action
        lids = [o for o in objects if o.type == 'MESH' and o.data.shape_keys]
        assert len(lids) == 2
        scene.frame_set(44)
        assert all(o.data.shape_keys.key_blocks['Blink'].value > .99 for o in lids)
        scene.frame_set(1)
    else:
        assert all(not any(m.type=='ARMATURE' for m in o.modifiers) for o in objects)

    scene.camera = None
    scene.compositing_node_group = None
    scene['asset_status'] = 'Independent '+label+'; original seated pose and assembly coordinates retained.'
    verts = [v for values in after.values() for v in values]
    low = Vector(tuple(min(v[k] for v in verts) for k in range(3)))
    high = Vector(tuple(max(v[k] for v in verts) for k in range(3)))
    center = (low+high)*.5
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_perspective = 'PERSP'
                space.region_3d.view_location = center
                space.region_3d.view_distance = (high-low).length*1.65
                space.region_3d.view_rotation = Vector((3,-6,2.5)).to_track_quat('Z','Y')
                space.shading.type = 'MATERIAL'
                space.overlay.show_overlays = True
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    glb = path.parent / 'exports' / (path.stem+'.glb')
    glb.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
                             export_yup=True,export_animations=(label=='driver'),export_extras=True)
    report['parts'][label] = {'blend':str(path.relative_to(ROOT)), 'glb':str(glb.relative_to(ROOT)),
                             'root':root_name, 'objectCount':len(objects),
                             'maxPlacementDeviationMeters':error}
    print('SEPARATED '+label,flush=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
driver_names = [o.name for o in bpy.data.collections['RIFF_DRIVER'].objects]
seat_names = ['Seat_Root','Seat_Cushion','Seat_Back']
# Verify the actual editor interaction: moving the driver cannot pull the seat.
seat_before = positions([bpy.data.objects[n] for n in seat_names])
rig = bpy.data.objects['Riff_Driver_Rig']
rig.location.x += 1
seat_after = positions([bpy.data.objects[n] for n in seat_names])
assert all((a-b).length < 1e-7 for n in seat_before for a,b in zip(seat_before[n],seat_after[n]))
report['driverMovesWithoutSeat'] = True

save_part('driver',driver_names,'Riff_Driver_Rig',DRIVER/'riff-driver-only.blend')
save_part('seat',seat_names,'Seat_Root',KART/'streamliner-seat.blend')

# Review the separated geometry side by side; this presentation pose is not saved.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
visible = set(driver_names+seat_names)
for obj in scene.objects:
    if obj.type == 'MESH' and obj.name not in visible and not obj.name.startswith('Kart_Studio_'):
        obj.hide_render = True
rig = bpy.data.objects['Riff_Driver_Rig']
seat = bpy.data.objects['Seat_Root']
rig.location.x -= .72
seat.location.x += .95
camera = bpy.data.objects['Kart_Camera_hero']
target = Vector((.12,0,1.18))
camera.location = (3,-7,3.3)
camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale = 3.65
scene.camera = camera
scene.render.resolution_x = 1300
scene.render.resolution_y = 950
scene.render.resolution_percentage = 100
scene.cycles.samples = 32
scene.render.filepath = str(KART/'review/final/driver-and-seat-separated.png')
bpy.ops.render.render(write_still=True)
report['passed'] = True
(KART/'exports/separation.json').write_text(json.dumps(report,indent=2)+'\n')
print('SEPARATION_VERIFIED '+json.dumps(report),flush=True)
