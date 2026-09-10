# Stormbreak test track

A playable three-lap time trial built from the approved Stormbreak V2 road footprint. The track has an approximately 2,161 m continuous road, 18 m width, 16 m of gradual elevation change, closed safety walls, twelve ordered checkpoints, lap timing, recovery, minimap and an optional automatic test driver. Scenery includes the workshop, control tower, start gantry, cranes, turbine building, rocks and a simple sea plane outside the route.

## Play

Open `builds/stormbreak-prototype/StormbreakPrototype.app` from the repository root. In Unity, open `game/Assets/_DarioKart/Scenes/Tracks/StormbreakPrototype.unity` and press Play.

- WASD / arrow keys: accelerate, reverse/brake and steer.
- Space: loosen grip for a drift.
- R: return to the last valid checkpoint.
- T: toggle the automatic test driver; press again to take control.
- Enter: restart the three-lap session.
- Escape: quit the standalone player.

A two-second countdown precedes the start. Pass all twelve gates in order to complete a lap. The minimap shows your position. Grit and the Dune Hopper use a static snapshot of the existing approved combined asset, preserving its material colors and fitted seating pose. Character and wheel animation are not yet implemented in this test.

## Editable sources

`stormbreak-prototype.blend` contains the road and scenery as editable mesh objects grouped by part and material. The Unity scene supplies physics, race logic, lighting, camera and materials. The original concept and master road footprint remain in `art-source/concepts/tracks/stormbreak-v2/`.

This is a driving prototype with simple materials and low-detail scenery. It is not a final reproduction of the concept-art finish. The road has no jumps, water crossings or intersections. Opponents, items, phone controls, shortcuts and moving hazards are outside this initial build.

## Validation

`review/validation.json` records collision samples across the center and both sides of the road (3,240 total), checkpoint order and finish-state checks, physical wrong-way/off-road gate rejection, and three physics-driven laps. The automatic driver completed laps in about 118, 117 and 117 seconds, with zero road misses, airborne physics steps or recoveries and under 0.45 m of lateral deviation from the centerline. Human lap times depend on steering and drift use.

`review/start.png`, `review/overhead.png` and `review/general.png` are Unity renders of the actual generated scene. `review/build-success.txt` records a successful Mac build. Runtime test reports, when present, are separate from the editor physics checks; see `review/runtime-test.json` and `review/runtime-note.txt` for packaged-player validation.

The original Unity editor was open while the Mac was locked, so the build and checks ran in an isolated project copy. Only Stormbreak's new scene, generated assets and their Unity metadata were copied back. Existing harbor and character work was preserved.

The repository checker still reports pre-existing stale source hashes in `streamliner.export.json` and `dune-hopper.export.json`. Stormbreak introduces no missing metadata errors; it does not rewrite those unrelated source manifests.

## Rebuild

From the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/build_stormbreak.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/export_stormbreak_kart.py
```

Wait for Unity to import, then use **Dario Kart → Stormbreak → Build and verify everything**. The menu builds the scene, captures review images, verifies three laps, and packages the Mac app. It refuses to replace a scene while open scenes have unsaved edits. Generated Stormbreak outputs are replaced on rebuild; keep manual variations under separate names.

`build_stormbreak.py` reads the approved `layout.json`, resamples the closed curve at approximately 2 m spacing, supplies a gentle terrain height function, and exports the road and scenery. Upward-facing road normals are enforced explicitly to preserve raycasts on slopes. `stormbreak.json` and `build-report.json` record source hashes and geometry counts. `export_stormbreak_kart.py` reads the existing combined GLB without changing it and exports a static visual plus material-slot mapping.
