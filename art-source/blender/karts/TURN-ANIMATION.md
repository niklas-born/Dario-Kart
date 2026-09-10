# Riff and Grit — turn animation

[Watch the six-second comparison](turn-animation-preview.mp4).

| Driver | Editable animation scene | Animated exchange preview |
| --- | --- | --- |
| Riff / Streamliner | [riff-streamliner-turns.blend](streamliner/riff-streamliner-turns.blend) | [GLB](streamliner/exports/riff-streamliner-turns.glb) |
| Grit / Dune Hopper | [grit-dune-hopper-turns.blend](dune-hopper/grit-dune-hopper-turns.blend) | [GLB](dune-hopper/exports/grit-dune-hopper-turns.glb) |

Play frames **1–145 at 24 fps**. The studio rehearsal turns right, centers, turns left, and centers again. Its small heading changes illustrate the pose; it does not simulate a driving path. Original accepted assemblies and standalone drivers are preserved.

The front tires steer with an Ackermann angle difference. The steering wheel, wrist targets, two-bone arm IK, slight torso lean and head turn follow the same control. The rear tires only roll, and Grit's spare remains fixed. Existing idle and blink animation is retained in the Blender/GLB rehearsal.

For manual posing, clear the kart root's rehearsal action, then set `steering_degrees` between −28 and +28. `travel_meters` rolls each road tire according to its radius; negative distance reverses it. The original `wheel_spin_degrees` remains an additional manual offset. The animation controls do not implement suspension travel or tire contact physics.

## Unity

Ready-to-use visual prefabs live in `game/Assets/_DarioKart/Resources/KartTurns/`:

- `riff-streamliner.prefab`
- `grit-dune-hopper.prefab`

Place either visual beneath a `HarborKart` to receive steering and signed speed automatically. Existing Harbor and Stormbreak prototype karts with recognized Dune Hopper or Streamliner visual names replace their static visual in memory when Play starts, retaining the old child's placement. Saved scene geometry and vehicle handling are unchanged. Existing standalone game builds must be rebuilt to include this work.

`KartTurnVisuals` samples a baked two-second steering pose sweep and applies wheel roll independently in `LateUpdate`. Steering is smoothed, reverse speed reverses the tires, and resetting the kart centers the pose. This avoids an IK package dependency and preserves the authored arm/hand pose. Unity's FBX handedness conversion reverses the source steering sign; the component compensates. The gameplay sweep contains steering poses only; the GLB rehearsal additionally contains the idle and blink.

Regenerate prefabs, material assignments, validation and Unity review renders with **Dario Kart → Animation → Build and validate turn prefabs**. Each model's `review/turns/` contains Blender poses, and `review/turns/unity/` contains actual Unity captures.

## Rebuild and validation

From the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/animate_kart_turns.py -- --kart all --render
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/package_kart_turns.py
python3 tools/blender/verify_kart_turns.py
```

The rig checks ±28°, ±20° and neutral steering, evaluated wrist contact (within 3 mm), stable wheel centers, radius-based rolling, rear steering and the spare. Actual measured wrist errors are below 0.001 mm. GLB checks confirm the 14-bone skeleton, baked steering/arm/wheel channels, six-second duration, blink and unchanged accepted source hashes. Unity checks sample both turn extremes, verify the direction against +X, hand contact, unchanged wheel centers, a fixed rear steering axis, return to center, and forward/reverse rolling.

The generic `tools/check_repo.py` also reports pre-existing stale source provenance in the original `streamliner.export.json` and `dune-hopper.export.json`. Those original export manifests are separate from the new animation validation reports.

To regenerate the video, run `tools/blender/render_kart_turns.py` in Blender once with `-- --kart streamliner` and once with `-- --kart dune-hopper`. Encode the two PNG sequences from `builds/turn-animation/` with FFmpeg at 24 fps and combine them with `hstack`.
