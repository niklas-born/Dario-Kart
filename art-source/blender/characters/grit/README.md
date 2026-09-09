# Grit — driver model

Open **[grit-driver.blend](grit-driver.blend)** for Grit alone. His seat and steering wheel are separate fitting aids in [grit-driver-review.blend](grit-driver-review.blend); they are excluded from the main driver file and both exports.

Grit is the second racer modeled in Blender: a golden yellow cyclops with a broad egg-shaped body, one half-lidded amber eye, two inward-curving ivory horns, five upright crest spikes, a pointed-tooth grin, and curled driving hands. The [approved Dune Hopper sheet](../../../concepts/racers/round-02/02-grit-v2.png) is the primary reference. The [earlier sheet](../../../concepts/racers/round-01/02-grit-v1.png) supplies an unobstructed rear view of the character.

## Review

- [Three-quarter render](review/final/hero.png)
- [Front](review/final/front.png), [side](review/final/side.png), and [rear](review/final/rear.png)
- [Face close-up](review/final/face.png)
- [Closed blink](review/final/blink-test.png)
- [Head and arm pose check](review/final/pose-test.png)
- [Separate seat and steering guide fit](review/final/seat-and-wheel-fit.png)

All review images are rendered from the actual Blender meshes. The source concept images are packed into the review scene. The illustrated perspectives differ slightly, and the cockpit hides the lower body; the compact seated legs and feet are an inferred construction.

| Pass | Comparison and correction |
| --- | --- |
| 01 | Established Grit's original body, single eye, grin, horns, crest, and seated anatomy. |
| 02 | Corrected the blink's default state and the washed-out yellow rendering. Checked front, side, and face views. |
| 03 | Slimmed the forearms, shortened the crest, tightened the tooth spacing, and added iris detail. |
| 04 | Recessed tooth roots to stop them showing through the cheeks, fused the lips into the face, rounded smile corners, and checked the steering fit. |
| 05 | Rebuilt the driving hands with three curled fingers and a thumb on each side, replacing the round fist shapes. |
| 06 | Replaced the protruding eye reflection with a surface patch, then checked that the closed eyelid covers it. |

The numbered Blender scenes and their renders remain beside the stable driver so these changes are reviewable.

## Editing and posing

`GRIT_DRIVER` contains the character meshes and `Grit_Driver_Rig`. Select the rig in Object Mode to move the entire driver. Pose Mode exposes 14 bones for the root, pelvis, chest, head, upper arms, forearms, hands, thighs, and feet. The body and hands form a continuous skin mesh; the eye, horn, crest, tooth, and mouth details remain separately editable meshes attached to the rig.

`Upper_Lid_Center` has a `Blink` shape key. The timeline contains a subtle seated idle over frames 1–120 at 30 fps. Frame 44 shows a fully closed eye; frame 1 is the neutral driving pose. The guide collection can be enabled in the review scene for cockpit fitting. It has no dependency on the driver's rig.

## Files and checks

| File | Purpose |
| --- | --- |
| `grit-driver.blend` | Clean, UV-mapped and rigged driver with no seat, wheel, camera, or studio objects. |
| `grit-driver-review.blend` | Prepared driver with lighting, review cameras, packed references, and separate fitting guides. |
| `grit-driver-v06.blend` | Detailed sculpt before reduction and rigging. Earlier numbered files preserve previous passes. |
| `exports/grit-driver.fbx` | Rigged driver exchange asset for later Unity import. |
| `exports/grit-driver.glb` | Portable driver with material values, skeleton, blink, and animation. |
| `exports/grit-driver.export.json` | Exact mesh counts, sampled reduction error, dimensions, and source/output hashes. |
| `exports/validation.json` | Checks of the clean Blender file, GLB structure, and a fresh FBX import. |

The asset uses meters, −Y forward and Z up in Blender. Exports use Y up. Skin weights are normalized with at most four influences per vertex. Geometry is reduced from the detailed sculpt and inspected again after preparation. Validation checks that no fitting or studio objects enter the driver files and that scale, UVs, rigging, and the blink survive export.

Grit now has a separate [Dune Hopper vehicle and combined Blender scene](../../karts/dune-hopper/README.md). His standalone driver stays unchanged, and the vehicle seat has its own root. Unity materials, animation integration, performance budgets, and gameplay are separate work; the driver's exchange files are staged beside this Blender source.

## Rebuild

From the repository root, using Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_grit.py -- --revision 06 --views hero,front,side,rear,face,fit --resolution 1100 --samples 40
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/characters/grit/grit-driver-v06.blend --python-exit-code 1 --python tools/blender/prepare_grit.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_grit_exports.py
```

Use a new revision number to retain an existing sculpt. Preparation overwrites the stable driver, review scene, and exchange files, while preserving the numbered source.
