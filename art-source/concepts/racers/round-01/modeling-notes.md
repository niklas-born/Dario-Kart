# Modeling handoff — seated monster racers

**Vehicle architecture update:** [round 02](../round-02/README.md) supersedes this sheet's shared-visible-chassis approach. Reuse rig/controller interfaces and appropriate small parts, while preserving different wheelbases, wheel sizes, ride heights and body construction. Driver rig and material notes below still apply.

## Art target

Polished cartoon creatures with broad readable shapes, large expressive faces, soft skin or sculpted fur, satin painted karts, rubber tires, and restrained metal. Avoid adding tiny surface detail just because the concept renderer can show it. Check character recognition from the rear chase camera and at split-screen size.

The reference sheets share a base vehicle family. Reuse the structural chassis, steering assembly, wheel system, seat attachment and motor layout; vary shells, fenders, trim, tires and character proportions. The first round is intentionally cohesive. Further vehicle exploration can push shape variety without changing the driver/vehicle interface.

## First Blender blockout

Start with Riff to establish the shared chassis and seated pose. Next build Orbit to test a very different head silhouette and eye rig; then Momo to test a wider cockpit. Use that experience before building all eight at final detail.

Proposed base scale: approximately 2.1 m vehicle length, 1.5 m width and 1.35 m wheelbase, with 0.55 m diameter wheels. These are initial blockout dimensions, not measurements derived from the artwork. Resolve wheel/axle spacing in 3D, check steering and suspension travel, then freeze the chassis standard. Wide-body racers may change visible shell width without changing collision fairness automatically.

Import each sheet into Blender as image references. Use the side/front views to establish proportions and the hero/rear views to resolve volumes. Establish true orthographic cameras in Blender. Where views disagree, choose a consistent constructed model rather than trying to satisfy contradictory pixels. The concept art does not define engineering dimensions or hidden underbody geometry.

## Asset separation

Keep these objects distinct:

- Gameplay/vehicle root at ground center, aligned with the repo's meter-scale export convention.
- Chassis and body shell, steering wheel, four independently rotating wheels, and front steering pivots.
- Seat and simple interior footwell. The racer stays seated; do not omit seat support or let hands float above controls.
- Driver body, eyes/lids, mouth/teeth, and silhouette appendages as appropriate for deformation.
- Optional exhausts, lights, spoilers, and effect socket empties on the vehicle.

Use a simple seated driver rig: pelvis/root, torso lean, head, arms/hands, eyelids and jaw; add horn/ear/stalk secondary motion where appropriate. Legs can remain seated and economical. No walking animation set is needed for this game direction. Keep driver and kart separately editable even though they always appear together in gameplay.

Animations to plan: idle breathing, steering/lean, drift lean, jump anticipation, airborne reaction, landing squash, boost delight, hit reaction and victory. Fix hands to the wheel using constraints/IK in the final rig. Keep exaggerated motion inside a tested silhouette envelope so horns do not pass through another player's camera.

## Per-character construction notes

| Racer | Modeling / rig focus |
| --- | --- |
| Riff | Smooth loop horns with clean inner silhouettes; independent eyelids; preserve rounded cheeks |
| Grit | Exactly one eye; broad upper eyelid; ivory horns and teeth need rounded readable edges |
| Brisk | Exactly three eyes, small central eye below the upper pair; decide a consistent spike count/layout across the 3D crown |
| Momo | Fur represented primarily with sculpted clumps and texture/normal detail; avoid a costly full hair groom as the baseline; accommodate broad shoulders |
| Pip | Sculpt fringe as clean masses; expressive round eyes; keep horn arcs clear of steering motion |
| Zip | Wing-like ears need thickness and a restrained secondary-motion rig; resolve crest/fin/exhaust variations in the sheet during blockout |
| Orbit | Exactly four eye stalks; separate eye aim/blink; constrain stalk motion to avoid intersecting one another |
| Moss | Three eyes with one upper-center and two lower; wide horns with downturned tips; establish horn clearance from cockpit and neighboring racers |

## Materials and runtime checks

Begin with a small shared material family: monster skin, sculpted fur variant, ivory horn/teeth, glossy eyes, painted body, rubber, metal and seat fabric. Share shaders while varying color and maps. Treat the studio highlights and soft contact shadows as a look reference, not baked lighting to paint into base color.

Test under Unity URP track lighting with the intended chase camera. Check that eye expression, horn silhouette, item-holding/activation cues, tire rotation and vehicle silhouette survive at gameplay size. The artwork is not evidence of runtime performance or final quality.

The repository's initial 30–60K triangle range for kart plus driver is a starting art budget. Profile the actual model and screen sizes; generate LODs only after establishing the silhouette and target device budget.

## Source and export paths

Source vehicles: `art-source/blender/karts/<racer-id>/`.
Source drivers: `art-source/blender/characters/<racer-id>/`.
Runtime models: `game/Assets/_DarioKart/Art/Models/Karts/<racer-id>/` and `Characters/<racer-id>/`.
Unity wrappers: `game/Assets/_DarioKart/Prefabs/Karts/`.
Definitions: `game/Assets/_DarioKart/Data/Karts/`.

The existing `tools/blender/export_static.py` is for static meshes only. Add and validate a dedicated rigged FBX export preset before exporting seated skeletal drivers; do not send armatures through that static preset. Source art stays outside Unity's Assets folder.

This round delivers visual concepts and these handoff notes. No finished models, rigs, textures, Unity prefabs or racer behavior are implied by the images.
