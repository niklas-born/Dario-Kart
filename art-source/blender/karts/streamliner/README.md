# Riff — Streamliner

**Animated turns:** [open the turn rig](riff-streamliner-turns.blend), [watch Riff and Grit](../turn-animation-preview.mp4), or read the [controls and Unity integration](../TURN-ANIMATION.md). The new version adds steering-linked hands, arm IK, body lean, gaze and radius-based tire roll.

Open **[riff-streamliner.blend](riff-streamliner.blend)** for the complete car with Riff seated at the wheel.

For separate parts, open **[Riff only](../../characters/riff/riff-driver-only.blend)** or **[seat only](streamliner-seat.blend)**. These clean files contain only their named part and retain the assembled coordinates, so they line up when appended together. Riff keeps his seated pose, skeleton, idle, and blinks. [Separated preview](review/final/driver-and-seat-separated.png).

The model follows the [approved Streamliner concept](../../../concepts/racers/round-02/01-riff-v2.png): a long tapered cream-and-teal body, coral center stripe, exposed front suspension, small front tires, oversized rear tires, inset wheels, a curved windscreen, and twin upswept exhausts. The driver is reused from the accepted Riff model.

## View the result

- [Three-quarter render](review/final/hero.png)
- [Front](review/final/front.png), [side](review/final/side.png), [rear](review/final/rear.png), and [top](review/final/top.png)
- [Steering test](review/final/steering-test.png)
- [Combined car and driver GLB](exports/riff-streamliner.glb)
- [Car-only GLB](exports/streamliner.glb)

These images are rendered from the actual Blender geometry. The original driver file is preserved. The car's concept sheet is packed with the driver references in the combined Blender file.

## Controls in Blender

Select `Streamliner_Root` and open its custom properties:

| Control | Result |
| --- | --- |
| `steering_degrees` | Turns both front wheels and the steering wheel. Suggested range: −32° to +32°. |
| `wheel_spin_degrees` | Rotates all four wheels around their axle centers. |

Riff keeps his existing skeleton, seated idle, and blink shapes. `Steer_FL`, `Steer_FR`, `Steer_RL`, and `Steer_RR` hold the wheel assemblies; each has a `Spin_…` child. The separate steering-wheel frame aligns its spin to the tilted column.

To move only the driver, select `Riff_Driver_Rig` in Object Mode. To move only the seat, select `Seat_Root`; its cushion and back live in `STREAMLINER_SEAT`. Neither moves the other. Both still follow `Streamliner_Root` when moving the complete kart. The exported seat also remains a separate mesh beneath `Seat_Root`.

The shell, cockpit, suspension, tires, rims, exhausts, and details remain editable in named Blender collections. The model uses meters, with −Y forward and Z up. There are sockets for the driver's seat, camera target, item spawn, and both exhausts.

## Repository wiring

| File | Purpose |
| --- | --- |
| `riff-streamliner.blend` | Detailed authoring scene with Riff, materials, controls, cameras, and lighting. |
| `streamliner-seat.blend`, `exports/streamliner-seat.glb` | Separate cushion and seat back, with their own root and original assembly position. |
| `riff-streamliner-v01.blend`, `v02.blend` | Earlier car revisions retained for comparison. |
| `exports/riff-streamliner.glb` | Portable preview of the combined car and animated driver. |
| `exports/streamliner.glb` | Car-only exchange asset with material values and transform hierarchy. |
| `game/Assets/_DarioKart/Art/Models/Karts/streamliner.fbx` | Car-only Unity import, including wheel pivots and sockets. |
| `exports/streamliner.manifest.json` | Scale, geometry counts, source provenance, material values, pivots, and output paths. |

The exchange meshes are reduced and grouped by moving part; the detailed authoring geometry remains in the `.blend`. The driver belongs at `(0, 0.10, 0.38)` in Blender coordinates, also recorded by `Socket_Driver_Seat`. Use the exported socket when assembling it in Unity rather than manually copying Blender-axis values into a Unity transform.

The Unity importer disables automatic material creation. Assign URP materials using the values in the adjacent `streamliner.export.json`. Runtime code must drive the exported pivots; Blender property drivers do not become gameplay scripts. Driving physics, suspension simulation, colliders, and Unity visual/performance validation remain separate game work.

## Review and checks

The first pass established the body, cockpit fit, wheel sizes, suspension, and exhaust arrangement. The second corrected the stripe's fit to the curved hood, tightened the cockpit behind the seat, widened the tires, opened the exhaust bores, and fixed the cockpit floor/lining clearance. Front, side, rear, top, and three-quarter views were inspected.

The preparation script checks 22° steering and 35° wheel rotation, verifies that wheel centers stay fixed, and adds UVs to the exchange meshes. [Export validation](exports/validation.json) checks both GLBs and imports the FBX into a fresh Blender scene to compare pivots, hierarchy, UVs, and bounds. These checks do not claim Unity rendering or gameplay has been tested.

## Rebuild

From the repository root, with Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_streamliner.py -- --revision 02 --views hero,front,side,rear,top --resolution 1200 --samples 48
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/karts/streamliner/riff-streamliner-v02.blend --python-exit-code 1 --python tools/blender/finish_streamliner.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/separate_riff.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_streamliner.py
```

Use a new revision number when preserving an existing draft. Finishing saves the stable combined model, renders, and exchange files without modifying the standalone Riff driver.
