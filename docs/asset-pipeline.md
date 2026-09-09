# Blender and game asset pipeline

## Ownership and locations

| Asset | Editable source | Runtime location |
| --- | --- | --- |
| Karts and drivers | `art-source/blender/karts`, `characters` | `Art/Models/Karts`, `Characters`; wrapper in `Prefabs/Karts` |
| Track roads and scenery | `art-source/blender/tracks/<track-id>`, `props` | `Art/Models/Tracks/<track-id>`, `Props`; assembled in `Scenes/Tracks` |
| Items and hazards | `art-source/blender/items`, `obstacles` | `Art/Models/Items`, `Obstacles`; wrappers in matching `Prefabs` folders |
| Materials and texture work | `art-source/textures` | Baked images in `Art/Textures`; Unity materials in `Art/Materials` |
| Rig and animation | Character/kart `.blend` files | Exported animation in `Art/Animations` |
| Effects | Blender source where needed, Unity graph assets | `Art/VFX`; gameplay event triggers in code |
| Audio | `art-source/audio` | `Audio/Music`, `SFX`, `Ambience`, `Mixers` |

Runtime paths in this table are relative to `game/Assets/_DarioKart`. Track source folders get the same stable ID as their runtime course.

## Static mesh contract (implemented)

1. Model at real scale: **one Blender unit = one meter**, metric units, unit scale 1. Blender Z is up; author forward-facing assets toward **-Y**. Export uses **-Z forward / Y up**; validate a facing arrow in Unity before producing vehicles.
2. Put exported meshes in a collection named `EXPORT`. Keep lights, cameras, high-poly bake sources, and reference art elsewhere. The current tool intentionally accepts only unparented static meshes with applied rotation and scale; rigs and animation need a separate export preset.
3. Apply rotation and scale in Blender. Use deliberate pivots: kart root at ground center, road modules at a snapping point, moving props at their rotation axis. Do not merge an entire course into one mesh.
4. Supply UVs and normals. Bake procedural materials to images. FBX does not reproduce a Blender node graph or Cycles lighting in Unity. The provided ramp is only a geometry/scale fixture, not production art.
5. Run the export tool below. It exports only `EXPORT`, applies modifiers, disables animation, converts units, and writes an adjacent provenance JSON file. It never saves changes back into the source `.blend`. The Unity importer disables automatic material import so runtime materials are authored explicitly.
6. Unity imports the FBX. Assign URP materials, explicit colliders, LOD groups, and gameplay components on a wrapper prefab under `Prefabs`, not on the imported model asset. Unity import scale stays 1; inspect actual bounds in meters.
7. Place that prefab in a course scene, wire profiles and markers, and test at race speed. Keep the same FBX path and `.meta` when updating the mesh.

From the repository root on the setup Mac:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/create_pipeline_fixture.py
"/Applications/Blender.app/Contents/MacOS/Blender" --background art-source/blender/props/pipeline_ramp.blend --python-exit-code 1 --python tools/blender/export_static.py -- --output game/Assets/_DarioKart/Art/Models/Props/pipeline_ramp.fbx
```

The fixture generator refuses to overwrite its source. For normal work, create/edit a `.blend` manually and run only the export command with that source and destination. On other platforms substitute the Blender executable path. Pin the team's Blender version; the fixture was generated with 5.2.1 LTS.

## Example wiring

Riff's [Streamliner vehicle](../art-source/blender/karts/streamliner/README.md) uses a separate vehicle export path because its wheels are parented to steering and axle pivots. `tools/blender/finish_streamliner.py` saves the detailed combined authoring file, exports a car-only FBX under `Art/Models/Karts`, and provides car-only and combined GLBs beside the Blender source. The adjacent manifest records material values and sockets. `tools/blender/verify_streamliner.py` checks the portable files and re-imports the FBX to verify hierarchy and scale. A gameplay prefab and Unity material setup are still required.

`pipeline_ramp.blend` → `pipeline_ramp.fbx` → setup command creates `Prefabs/Obstacles/PipelineRamp.prefab` → mesh collider + `SurfaceAuthoring(asphalt)` → `Scenes/Development/AssetPreview.unity`.

The ramp is 4 m wide, 8 m long, and 2 m high. Confirm these bounds after import. The preview uses a simple material to isolate orientation, scale, normals, and collision. There is no launch script yet: boost/launch pads will be separate trigger prefabs, with Blender supplying their visuals.

## Production art targets (starting budgets, not measured limits)

- Kart plus driver: roughly 30–60K triangles at LOD0; build lower LODs after camera-distance tests.
- Texture sets: generally 1K–2K, with shared trim sheets/atlases for track props; reserve larger maps for justified hero assets.
- Separate road collision from decoration; use simple colliders for moving hazards and static mesh collision for road surfaces.
- Establish texel density with the first art benchmark. Use base color in sRGB; normals and masks as linear data. Document channel packing per material.
- Keep road silhouettes, item silhouettes, pad arrows, and hazard warnings readable during a 30–45 m/s pass. These speeds are tuning targets, not measured gameplay.
- Review in the runtime renderer with the actual camera, shadows, post-processing, and target resolution. Blender beauty renders are references, not acceptance evidence.

## Asset provenance and version control

Record third-party asset author, source URL, license, proof-of-purchase location if relevant, and modifications in `art-source/asset-register.json` before importing. The included procedural fixture is original project geometry. Keep source assets and runtime exports in Git LFS; keep `.meta`, `.unity`, `.prefab`, `.asset`, source code, and export manifests as text. Install LFS before committing binary files. Lock heavily edited `.blend` files when using a remote that supports LFS locking.
