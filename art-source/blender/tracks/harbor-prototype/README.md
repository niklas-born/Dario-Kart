# Harbor driving prototype

This is a local conversion experiment using the user-supplied Toad Harbor GLB.
The main loop follows the yellow line in `/Users/niklasborn/Downloads/test.png`.
The two alternatives follow the red lines: the outside gazebo bend and direct
upper-street climb, and the outside downhill route. The earlier invented shortcut
has been replaced. `review/marked-layout.png` uses the same overhead framing as
the supplied marked image for comparison.

## Play

Open `game/Assets/_DarioKart/Scenes/Tracks/HarborPrototype.unity` in Unity and press
Play, or launch `builds/harbor-prototype/HarborPrototype.app` when built.

- WASD or arrow keys: accelerate, brake/reverse, steer.
- Space: looser grip for drifting.
- R: recover to the last valid checkpoint.
- T: toggle the prototype's automatic test driver on the main circuit.
- Enter: restart the three-lap race.

Main track: approximately 1,204 m long, 14 m wide, 54 m elevation range at the
chosen scale. Alternatives are 5.5 m wide. The scale is a gameplay choice based
on the supplied geometry, not a claim about the original game's meters.

Seven ordered gates sit before or after branch junctions so both alternatives
count as valid routes. The optional cyan dock ramp launches over the bridge;
the other half of the road remains passable. A cyan downhill pad boosts speed.
A moving cargo block can be passed on either side. Falling below the course
automatically recovers the kart; R also handles any other stuck position.

The Dune Hopper mesh is used for the test kart with simplified materials.
The original harbor is scenery. Smooth road, alternate-route collision, and
guardrails are authored separately. The alternatives use ordinary sloping
road physics rather than an anti-gravity wall-driving system.

## Verification

`review/validation.json`: collision coverage along the main circuit and ordered
checkpoint/lap rules, including rejected skips and a three-lap finish.

`review/driving-test.json`: a complete physics-driven lap on the yellow circuit
and one using each red alternative, with moving cargo enabled and zero recovery
teleports. The alternative laps use a slower test-driver setting; their lap times
must not be interpreted as comparative route balance.

`review/runtime-test.json`, when present, is the separately built player's
three-lap smoke test. `review/playtest.png` is captured by that player.

The controller is an initial arcade handling prototype. Drifting, jump tuning,
camera clearance, scenery/material cleanup, manual feel, and target-device
performance still need playtesting. There is no item system, opponent field,
production AI, anti-gravity, or phone input in this scene.

The repository-wide `tools/check_repo.py` check reports stale source provenance
for the existing Streamliner and Dune Hopper exports. That issue is separate
from the harbor's compilation, build, road and driving tests.

## Rebuild

From the repository root:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_harbor.py
```

Then in Unity, use **Dario Kart → Harbor → Build driving prototype**, followed by
**Validate road and lap rules**, **Simulate driving lap**, and **Build Mac playtest**.
The builder opens the generated course additively to preserve other open work.
It refuses to rebuild a harbor scene with unsaved edits. Running the builder
replaces generated harbor meshes, materials and its saved scene.

`harbor.json` records the source hash, coordinate conversion, sampled route,
alternative paths, checkpoints, extracted materials, and source attribution.
The road trace is defined in reference-image pixels in `tools/blender/build_harbor.py`.
No new Unity package dependency is required.

## Provenance

Source: `mario_kart_8_-_toad_harbor.glb`, supplied by the user.
Embedded metadata identifies **H,yoshi** as the Sketchfab uploader and declares
**CC-BY-4.0**. Source URL:
https://sketchfab.com/3d-models/mario-kart-8-toad-harbor-97681cab2c9445069b335e940116562f

The file contains Mario Kart/Nintendo content; the uploader's metadata alone
does not establish underlying rights. This prototype records that provenance
and has not been published. Modifications include scale/origin normalization,
texture extraction, an FBX export, a simplified sea material, and the new track
collision and gameplay components. See `art-source/asset-register.json`.
