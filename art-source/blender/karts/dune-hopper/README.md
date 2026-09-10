# Grit — Dune Hopper

**Animated turns:** [open the turn rig](grit-dune-hopper-turns.blend), [watch Riff and Grit](../turn-animation-preview.mp4), or read the [controls and Unity integration](../TURN-ANIMATION.md). The new version adds steering-linked hands, arm IK, body lean, gaze and radius-based tire roll.

Open **[grit-dune-hopper.blend](grit-dune-hopper.blend)** for the detailed vehicle with the accepted Grit driver seated inside. The driver, seat, steering wheel, road wheels, and carried spare have independent transform groups.

The buggy follows the [approved concept](../../../concepts/racers/round-02/02-grit-v2.png): graphite tube frame, triangular yellow panels, a square headlamp, steel skid plates with three open slots, knobby tires with orange rims, exposed orange coilovers, a rear engine, twin hollow exhaust tips, two red tail lamps, and a strapped spare. Geometry is constructed in Blender; review images are actual mesh renders.

## Review and revisions

- [Three-quarter view](review/final/hero.png)
- [Front](review/final/front.png), [side](review/final/side.png), [rear](review/final/rear.png), and [top](review/final/top.png)
- [Steering and wheel rotation check](review/final/steering-test.png)
- [Reduced exchange mesh comparison](review/final/exchange-mesh-check.png)

| Pass | Comparison and correction |
| --- | --- |
| 01 | Established the frame, cockpit fit, mechanical parts, and four-wheel stance around Grit. |
| 02 | Lowered and reduced the spare, replaced rectangular tread blocks with softer irregular lugs, exposed the rim fasteners, seated the fender bolts, and reduced studio lighting. |
| 03 | Moved the upper shock mounts below the fenders after the rendered side and front views revealed protrusions. Final views also check steering and the reduced exchange geometry. |

The illustrated views vary in their mechanical details and proportions. This model uses one consistent wheelbase and a conventional carried spare; its chassis and hidden mounting details are inferred. It is a reviewed interpretation of the concept, not a claim of exact geometric equivalence.

## Editing and controls

| Select | What it moves |
| --- | --- |
| `Dune_Hopper_Root` | Entire vehicle and seated driver. |
| `Grit_Driver_Rig` | Grit only; his 14-bone rig, idle, and blink remain available. |
| `Dune_Seat_Root` | Cushion, back, bolsters, and seat mounting rails only. |
| `Dune_Steer_FL` / `FR` | Front steering pivots. |
| `Dune_Spin_FL` / `FR` / `RL` / `RR` | Road wheel rotation around each axle center. |
| `Dune_Steering_Spin` | Steering wheel around its tilted column. |
| `Dune_Spare_Mount` | Carried spare; independent of wheel rotation. |

In Blender, change the root's `steering_degrees` and `wheel_spin_degrees` custom properties to preview the controls. The saved neutral pose uses zero for both. Steering was tested at 22°, road wheel rotation at 35°, and steering wheel rotation at 27.5°; wheel centers stayed fixed and the rear wheels did not steer. These are visual controls, not a suspension solver or gameplay controller. Driver hands remain in the accepted driving pose; steering does not automatically animate his arms.

Grit is placed at `(0, 0.12, 0.58)` meters relative to the kart root. The [standalone driver](../../characters/grit/grit-driver.blend) remains unchanged. The combined scene packs the approved concept into a hidden reference collection. Studio and reference collections are excluded from exports.

## Files and integration

| File | Purpose |
| --- | --- |
| `grit-dune-hopper.blend` | Detailed, editable combined scene and review setup. |
| `grit-dune-hopper-v03.blend` | Numbered final modeling pass; earlier passes preserve comparisons. |
| `exports/dune-hopper.glb` | Vehicle only, with materials and eight separate mesh groups. |
| `exports/grit-dune-hopper.glb` | Vehicle plus rigged Grit, idle animation, and blink. |
| `game/Assets/_DarioKart/Art/Models/Karts/dune-hopper.fbx` | Vehicle geometry staged for Unity; source path is relative to the repository root. |
| `exports/dune-hopper.manifest.json` | Geometry counts, dimensions, wheel pivots, sockets, material values, source/output hashes, and native checks. |
| `exports/validation.json` | GLB structure and fresh FBX import checks. |

The eight vehicle mesh groups are the static body, seat, four road wheels, steering wheel, and spare. The kart has 224,734 triangles in the detailed source and 100,101 in the exchange meshes; the unchanged driver adds 45,690. The detailed native parts stay individually editable; only the exchange meshes are reduced, grouped, and UV-mapped. Blender uses meters, −Y forward, and Z up. Exchange files use Y up. Export validation checks UVs, driver/seat separation, the 14-bone skeleton and blink, hierarchy, source hashes, and FBX bounds and wheel centers within 2 mm.

Runtime code should drive the named pivots rather than relying on Blender property drivers. The FBX importer preserves the hierarchy and disables automatic materials, animation, lights, and cameras. Build URP materials from the manifest's linear color and PBR values, then assign them in a wrapper prefab. The model has no colliders, LOD chain, vehicle physics, or gameplay prefab yet. Its detailed art budget requires profiling and further LOD work before a twelve-kart race; Unity rendering and platform performance have not been verified.

## Rebuild

Run from the repository root with Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_dune_hopper.py -- --revision 03 --views none
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/karts/dune-hopper/grit-dune-hopper-v03.blend --python-exit-code 1 --python tools/blender/finish_dune_hopper.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_dune_hopper.py
```

Use a new revision number for subsequent modeling work. Finishing overwrites the stable combined file, final renders, and exchange files, while preserving the numbered source and standalone driver.
