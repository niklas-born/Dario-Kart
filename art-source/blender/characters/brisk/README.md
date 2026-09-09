# Brisk — driver model

Open **[brisk-driver.blend](brisk-driver.blend)** for Brisk alone. His seat and steering wheel are separate fitting aids in [brisk-driver-review.blend](brisk-driver-review.blend); they are excluded from the main driver file and both exchange files.

Brisk is the third racer modeled in Blender: a glacier-blue monster with exactly three sleepy eyes, two dark-blue eyebrows, a broad pointed-tooth grin, a pale belly, frost scales at the temples and upper back, and a crown of pale striped horns. The [Frost Runner concept sheet](../../../concepts/racers/round-02/03-brisk-v2.png) is the primary reference. The [earlier sheet](../../../concepts/racers/round-01/03-brisk-v1.png) helps resolve the back of the character.

The consistent modeled silhouette has five upright crown horns, two outward side horns, and three smaller spikes down the rear midline. Brisk remains in a driving pose with thick bent arms, three curled fingers and a thumb on each hand, compact seated thighs, and feet intended to fit inside his kart's footwell. The source sheets hide the lower body, so the legs and feet are an inferred construction.

## Geometry review

- [Three-quarter view](review/final/hero.png)
- [Front](review/final/front.png), [side](review/final/side.png), and [rear](review/final/rear.png)
- [Face close-up](review/final/face.png)
- [All three eyes closed](review/final/blink-test.png)
- [Head and arm pose check](review/final/pose-test.png)
- [Separate seat and steering guide fit](review/final/seat-and-wheel-fit.png)

Every review image is rendered from the actual Blender geometry. Both concept sheets are packed into the review scene. The concept views differ slightly; the source model resolves those differences into a consistent three-dimensional construction.

| Pass | Comparison and correction |
| --- | --- |
| 01 | Constructed Brisk's round blue body, three-eye face, seven front-visible horns, rear spikes, raised frost scales, pale belly, and seated anatomy. Reviewed the hero, front, side, rear, and face against both sheets. |
| 02 | Recessed the mouth surface and tongue so the tooth row remains visible, extended and brought tooth tips forward while retaining buried roots, softened the eyebrows and lip border, and closed the small radial seam at the belly center. Checked the separate seat and wheel fit. |

Numbered Blender sources preserve the sculpt passes, with their corresponding renders in `review/v01` and `review/v02`. The detailed sculpt is kept alongside the reduced, rigged driver.

## Editing and posing

`BRISK_DRIVER` contains the character meshes and `Brisk_Driver_Rig`. Object Mode moves the full driver. Pose Mode exposes 14 bones for the root, pelvis, chest, head, upper arms, forearms, hands, thighs, and feet. The continuous body mesh includes the seated limbs and curled driving hands; eyes, horns, bands, mouth details, belly patch, and scale clusters remain separately editable.

`Upper_Lid_L`, `Upper_Lid_R`, and `Upper_Lid_Center` each have a `Blink` shape key. The timeline contains a subtle seated idle over frames 1–120 at 30 fps, with a coordinated blink fully closed at frame 44. Frame 1 is the neutral driving pose. The belly and scale meshes receive the same spatial weight rules as the skin, so the belly follows torso motion. Face and horn details follow the head.

Enable `FIT_GUIDE_NOT_FOR_EXPORT` in the review scene to inspect cockpit fitting. Its seat and steering wheel are independent from the driver's rig. This package contains only a driver and fitting aids; the Frost Runner vehicle is separate work.

## Files and checks

| File | Purpose |
| --- | --- |
| `brisk-driver.blend` | Clean UV-mapped and rigged driver, without seat, wheel, lights, cameras, or reference objects. |
| `brisk-driver-review.blend` | Prepared driver with studio lighting, review cameras, packed references, and separate fitting guides. |
| `brisk-driver-v02.blend` | Detailed reviewed sculpt before reduction and rigging. |
| `exports/brisk-driver.fbx` | Rigged driver exchange asset for later engine import. |
| `exports/brisk-driver.glb` | Portable driver with material values, skeleton, three blink targets, and animation. |
| `exports/brisk-driver.export.json` | Source/output hashes, exact counts, dimensions, and sampled reduction error. |
| `exports/validation.json` | Native driver, GLB structure, closed-lid coverage, and fresh FBX import checks. |

The native scene uses meters, −Y forward and Z up. Exchange files use Y up. Weights are normalized with at most four influences per vertex. Validation checks that fitting and studio objects are absent, all three closed eyelids cover their eye reflections, and scale, UVs, skeleton, and blink targets survive export. Exact output counts and the latest validation result are in the linked reports.

The rig is a practical seated posing rig with a small idle demonstration. It does not include steering IK, a jaw control, a full race animation set, baked texture atlases, LODs, or an engine-tested material setup. The meshes remain numerous and the exchange geometry exceeds the early whole-kart art budget; consolidation and performance work should follow a measured target-device budget. Unity appearance, animation integration, and gameplay have not been verified.

## Rebuild

From the repository root, using Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_brisk.py -- --revision 02 --views hero,front,side,rear,face,fit --resolution 1100 --samples 40
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/characters/brisk/brisk-driver-v02.blend --python-exit-code 1 --python tools/blender/prepare_brisk.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_brisk_exports.py
```

Use a new revision number to retain an existing sculpt. Preparation overwrites the stable driver, review scene, and exchange files while preserving numbered sources.
