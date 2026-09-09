# Riff — driver model

Open **[riff-driver-only.blend](riff-driver-only.blend)** for just Riff, with no seat, steering wheel, car, or studio objects. His rig, seated pose, idle, and blinks are preserved. Move `Riff_Driver_Rig` in Object Mode to move the whole character. [Matching GLB](exports/riff-driver-only.glb).

This clean file retains his placement from the assembled Streamliner, `(0, 0.10, 0.38)` in Blender coordinates. The [separate seat](../../karts/streamliner/streamliner-seat.blend) uses the same coordinates. The files align when appended together without an additional placement offset.

Open **[riff-driver.blend](riff-driver.blend)** for the UV-mapped, poseable model. The driver is seated, with a turquoise pear-shaped body, curled teal horns, three crown fins, sleepy eyelids, an ivory-toothed grin, and closed driving fists.

- [Latest three-quarter render](review/rigged/driver_hero.png)
- [Front render](review/rigged/driver_front.png) and [side render](review/rigged/driver_side.png)
- [Concept comparison](review/concept-comparison.png)
- [Blink test](review/rigged/blink-test.png) and [head-turn test](review/rigged/head-turn-test.png)
- [FBX](exports/riff-driver.fbx) and [GLB](exports/riff-driver.glb)

The actual mesh was built and rendered in Blender. Review images are renders of that geometry. Both original Riff concept sheets are packed into the Blender file under `CONCEPT_REFERENCE`.

## Editing and posing

`RIFF_DRIVER` contains the driver meshes and `Riff_Driver_Rig`. The 14-bone skeleton supports the head, torso, arms, hands, thighs, and feet. Each upper eyelid has a `Blink` shape key. The timeline contains a subtle seated idle over frames 1–120, with the eyes fully closed at frame 44. The file opens at frame 1.

The seat and steering wheel in `FIT_GUIDE_NOT_FOR_EXPORT` are temporary fitting guides in this standalone driver file. The [combined Streamliner model](../../karts/streamliner/README.md) now fits Riff into his car and uses those parts in its cockpit. Hidden legs and feet are an inferred seated construction because the concepts cover them with the cockpit.

The detailed sculpt remains in [riff-driver-v11.blend](riff-driver-v11.blend). Earlier numbered files and their renders preserve the iteration history. The poseable file has a reduced mesh, UVs, and normalized skin weights with at most four influences per vertex. Exact counts and sampled reduction error are in [the export manifest](exports/riff-driver.provenance.json).

## Concept comparison history

Only Riff has entered 3D production. No other racer is represented by a recolored copy of this model.

| Pass | Parts compared and corrected |
| --- | --- |
| 01 | Initial body, arms, hands, smile, horns, and driving pose; front, side, rear, and face renders. |
| 02 | Fixed the initially closed blink control; shortened horns and reduced the mouth opening. |
| 03 | Blended shoulders, reshaped the muzzle, refined fingers, and added the nose. |
| 04 | Put iris and pupil surfaces on the eye globe so the lids occlude them; added gums and rounded crown fins. |
| 05 | Enlarged hands, raised the steering grip, and corrected the mouth surface position at the corners. |
| 06 | Varied tooth sizes to match the broad central incisors; reduced excess specular highlights. |
| 07 | Smoothed horn surfaces and revised the closed grip. |
| 08 | Rebuilt fists with finger divisions; refined brows, crown buds, and horn roots. |
| 09 | Checked side attachments of brows and nose; adjusted horn depth. |
| 10 | Corrected finger-crease direction and refined the tapered horn curls. |
| 11 | Increased the horn surface resolution to remove visible faceting. |
| Rigged review | Re-rendered the reduced model, closed blink, and a seven-degree head turn. |

Use the round-02 concept as the primary visual reference and round-01 for its larger character views. The sheets are perspective illustrations, so their cameras and partially hidden anatomy are not exact orthographic measurements. The comparison images show the references and actual model directly; no numerical likeness score is claimed.

## Export scope

FBX and GLB contain only the rigged driver. Cameras, lighting, references, seat, and wheel are excluded. UVs, skin weights, blink morph targets, and animation are included. [Validation](exports/validation.json) records GLB structure checks and a fresh FBX import.

These exports are staged beside the source model for review. The eventual Unity destination is `game/Assets/_DarioKart/Art/Models/Characters/riff-driver.fbx`, with a wrapper prefab and URP materials created separately. Unity rendering has not been verified. Blender's procedural micro-bump requires baking for an identical runtime surface; exchange formats preserve the base material values. This first driver still needs a combined driver-and-kart performance budget and animation stress testing before shipping.

## Rebuild

From the repository root, using Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_riff.py -- --revision 11 --views driver_front,driver_hero,driver_side,driver_rear --resolution 1000 --samples 48
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/characters/riff/riff-driver-v11.blend --python-exit-code 1 --python tools/blender/prepare_riff.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_riff_exports.py
```

Use a new revision number to preserve an existing sculpt. Preparing writes the stable `riff-driver.blend` and exchange files; it leaves the numbered sculpt intact.
