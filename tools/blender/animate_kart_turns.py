"""Add steering-linked driver IK to the first two reviewed kart assemblies.

Writes separate -turns.blend authoring files and pose checks. Follow with
package_kart_turns.py for GLB/Unity exports. Accepted static sources are only read.
Run with Blender --background --factory-startup --python this_file -- --kart all.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = {
    'streamliner': dict(stem='riff-streamliner', root='Streamliner_Root',
        rig='Riff_Driver_Rig', prefix='', steering='SteeringWheel_Spin',
        controls='STREAMLINER_CONTROLS', camera='Kart_Camera_hero', ratio=.9,
        radii=(.435, .603), driver='RIFF_DRIVER'),
    'dune-hopper': dict(stem='grit-dune-hopper', root='Dune_Hopper_Root',
        rig='Grit_Driver_Rig', prefix='Dune_', steering='Dune_Steering_Spin',
        controls='DUNE_CONTROLS', camera='Dune_Camera_hero', ratio=.9,
        radii=(.547, .577), driver='GRIT_DRIVER'),
}


def drive(owner, path, index, root, expression, property_name='steering_degrees'):
    curve = owner.driver_add(path, index)
    driver = curve.driver
    for variable in list(driver.variables):
        driver.variables.remove(variable)
    variable = driver.variables.new()
    variable.name = 'value'
    variable.targets[0].id = root
    variable.targets[0].data_path = '["' + property_name + '"]'
    driver.expression = expression


def pose(scene, root, angle, distance=0):
    root['steering_degrees'] = float(angle)
    root['travel_meters'] = float(distance)
    root.update_tag()
    bpy.context.view_layer.update()


def build(kart, render):
    cfg = CONFIGS[kart]
    folder = ROOT / 'art-source/blender/karts' / kart
    source = folder / (cfg['stem'] + '.blend')
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.frame_set(1)
    root = bpy.data.objects[cfg['root']]
    rig = bpy.data.objects[cfg['rig']]
    wheel = bpy.data.objects[cfg['steering']]
    controls = bpy.data.collections[cfg['controls']]
    pose(scene, root, 0)
    root['travel_meters'] = 0.0
    root.id_properties_ui('travel_meters').update(description='Signed road distance; each tire rolls using its own radius')
    root.id_properties_ui('steering_degrees').update(min=-28, max=28,
        description='Positive turns right. Front tires, wheel, hands, chest and gaze follow this control.')
    root['turn_animation_help'] = 'Play frames 1–145 for the turn rehearsal. Clear root animation to use steering_degrees and travel_meters manually. Original wheel_spin_degrees remains an additional manual offset.'

    # The neutral wrist transforms are captured before any constraint is added.
    grips = {side: rig.matrix_world @ rig.pose.bones['hand.' + side].matrix
             for side in ('L', 'R')}
    targets = {}
    for side in ('L', 'R'):
        target = bpy.data.objects.new('Steering_Grip_' + side, None)
        controls.objects.link(target)
        target.parent = wheel
        target.matrix_world = grips[side]
        target.empty_display_type = 'SPHERE'
        target.empty_display_size = .035
        targets[side] = target
    bpy.context.view_layer.update()
    for side in ('L', 'R'):
        forearm = rig.pose.bones['forearm.' + side]
        constraint = forearm.constraints.new('IK')
        constraint.name = 'Keep wrist on steering grip'
        constraint.target = targets[side]
        constraint.chain_count = 2
        constraint.use_stretch = False
        constraint.iterations = 128
        constraint = rig.pose.bones['hand.' + side].constraints.new('COPY_ROTATION')
        constraint.name = 'Follow steering grip orientation'
        constraint.target = targets[side]
        constraint.target_space = 'WORLD'
        constraint.owner_space = 'WORLD'

    # Local chest Z points forward, and local head Y points upward in these rigs.
    # Preserve the existing idle tilt and blink; gaze uses a different channel.
    chest = rig.pose.bones['chest']
    head = rig.pose.bones['head']
    chest.rotation_mode = head.rotation_mode = 'XYZ'
    drive(chest, 'rotation_euler', 2, root, 'value * -0.0016')
    drive(head, 'rotation_euler', 1, root, 'value * 0.0032')
    # The column's local Z points away from the driver: clockwise from the
    # driver's view is negative here, while right tire steering is positive Z.
    drive(wheel, 'rotation_euler', 2, root, f'value * {-cfg["ratio"]} * pi/180')

    steers = {side: bpy.data.objects[cfg['prefix'] + 'Steer_' + side]
              for side in ('FL', 'FR', 'RL', 'RR')}
    spins = {side: bpy.data.objects[cfg['prefix'] + 'Spin_' + side] for side in steers}
    wheelbase = abs(steers['FL'].matrix_world.translation.y - steers['RL'].matrix_world.translation.y)
    half_track = abs(steers['FR'].matrix_world.translation.x - steers['FL'].matrix_world.translation.x) / 2
    for side, pivot in steers.items():
        if side.startswith('F'):
            # Ackermann: the inside front tire has the tighter steering angle.
            sign = 1 if side == 'FR' else -1
            drive(pivot, 'rotation_euler', 2, root,
                  f'atan(tan(value*pi/180)/(1-({sign * half_track / wheelbase})*tan(value*pi/180)))')
        spin = spins[side]
        radius = cfg['radii'][0 if side.startswith('F') else 1]
        drive(spin, 'rotation_euler', 0, root, f'value/{radius}', 'travel_meters')
        driver = spin.animation_data.drivers.find('rotation_euler', index=0).driver
        manual = driver.variables.new()
        manual.name = 'manual'
        manual.targets[0].id = root
        manual.targets[0].data_path = '["wheel_spin_degrees"]'
        driver.expression += '+manual*pi/180'

    # Numerical stress checks operate on evaluated bones, not only the controls.
    errors = []
    centers = {side: pivot.matrix_world.translation.copy() for side, pivot in spins.items()}
    spare = bpy.data.objects.get('Dune_Spare_Mount')
    spare_matrix = spare.matrix_world.copy() if spare else None
    measured = []
    for angle in (-28, -20, 0, 20, 28):
        pose(scene, root, angle, 1.0)
        dg = bpy.context.evaluated_depsgraph_get()
        evaluated_rig = rig.evaluated_get(dg)
        for side in ('L', 'R'):
            wrist = evaluated_rig.matrix_world @ evaluated_rig.pose.bones['hand.' + side].head
            error = (wrist - targets[side].evaluated_get(dg).matrix_world.translation).length
            errors.append(error)
            assert error < .003, (kart, angle, side, 'wrist target error', error)
        for side, pivot in spins.items():
            assert (pivot.matrix_world.translation - centers[side]).length < 1e-5
            radius = cfg['radii'][0 if side.startswith('F') else 1]
            assert abs(pivot.evaluated_get(dg).rotation_euler.x - 1 / radius) < 1e-5
        assert all(abs(steers[side].rotation_euler.z) < 1e-6 for side in ('RL', 'RR'))
        if spare:
            assert max(abs(spare.matrix_world[i][j] - spare_matrix[i][j]) for i in range(4) for j in range(4)) < 1e-6
        measured.append({'input': angle, 'frontLeft': math.degrees(steers['FL'].rotation_euler.z),
                         'frontRight': math.degrees(steers['FR'].rotation_euler.z)})
    pose(scene, root, 0)
    scene.frame_start, scene.frame_end = 1, 145
    scene.render.fps = 24
    # Rehearsal stays on the studio plinth. Heading anticipates the next arc;
    # actual game translation/heading is owned by the physics controller.
    for frame, angle, heading in [(1, 0, 0), (19, 0, 0), (43, 26, 9),
                                  (55, 26, 12), (79, 0, 0), (103, -26, -9),
                                  (115, -26, -12), (139, 0, 0), (145, 0, 0)]:
        root['steering_degrees'] = float(angle)
        root.keyframe_insert(data_path='["steering_degrees"]', frame=frame)
        root.rotation_euler.z = math.radians(heading)
        root.keyframe_insert(data_path='rotation_euler', frame=frame)
    for frame in range(1, 146):
        root['travel_meters'] = (frame - 1) / 24 * 1.4
        root.keyframe_insert(data_path='["travel_meters"]', frame=frame)
    root.animation_data.action.name = cfg['stem'] + '_Turn_Rehearsal'
    for frame, label in [(1, 'STRAIGHT'), (43, 'RIGHT TURN'), (79, 'CENTER'), (103, 'LEFT TURN'), (139, 'CENTER')]:
        scene.timeline_markers.new(label, frame=frame)
    scene.camera = bpy.data.objects[cfg['camera']]
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.render.resolution_x, scene.render.resolution_y = 960, 780
    scene.render.resolution_percentage = 100
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
    output = folder / (cfg['stem'] + '-turns.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report = dict(kart=kart, source=str(source.relative_to(ROOT)), sourceSha256=source_hash,
                  authoringFile=str(output.relative_to(ROOT)), maxWristErrorMeters=max(errors),
                  testedSteering=measured, rearWheelsStayStraight=True, wheelCentersStayFixed=True,
                  radiusBasedRolling=True, spareStaysFixed=bool(spare), previewFrames=[1, 145], fps=24)
    review = folder / 'review/turns'
    review.mkdir(parents=True, exist_ok=True)
    if render:
        for frame, label in [(1, 'straight'), (49, 'right'), (109, 'left')]:
            scene.frame_set(frame)
            scene.render.filepath = str(review / (label + '.png'))
            bpy.ops.render.render(write_still=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    (folder / 'exports/turn-animation.validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('TURN_RIG_VALIDATED', json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kart', choices=['all', *CONFIGS], default='all')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    for kart in CONFIGS if args.kart == 'all' else [args.kart]:
        build(kart, args.render)
