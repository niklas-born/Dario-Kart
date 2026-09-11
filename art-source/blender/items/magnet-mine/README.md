# Magnet Mine

[Editable Blender model](magnet-mine.blend) · [Lit review scene](magnet-mine-review.blend) · [FBX](exports/magnet-mine.fbx) · [GLB](exports/magnet-mine.glb)

![Actual Blender render](review/final/hero.png)

Two passes: broad hazard-striped puck, rounded horseshoe and silver poles, shorter pole height relative to the red beacon, front hatch, and mounting bolts.

[Front](review/final/front.png) · [Rear](review/final/rear.png) · [Concept](../../../concepts/items/magnet-mine.png) · [Export validation](exports/validation.json)

The stable source preserves named editable parts in `EXPORT` and optional decorative effects in `EFFECTS`. Numbered `.blend` files and their `review/vXX` renders preserve the iteration history. The review scene has lighting, a camera, and the packed original concept sheet; these are excluded from exchange assets.

The exchange package has **10,484 triangles** across **10 material groups**, including optional effects. UVs, applied transforms, normals, mesh counts, dimensions, and studio exclusion are checked by the shared validator. Material colors use constant PBR values, without Blender-only procedural textures. GLB includes emission/transmission material extensions where used. FBX requires explicit URP materials; the material values and export pivot are recorded in [the manifest](exports/magnet-mine.manifest.json).

This is a static item art asset. Source jaw and other component pieces can be edited independently; the exchange meshes consolidate by material and are not rigged. Runtime animation, colliders, LODs, shader effects, gameplay behavior, and Unity appearance are not implemented or tested here. Unseen rear surfaces are a consistent modeled interpretation of the supplied single-view concept.

Rebuild the current design with Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_items.py -- --item magnet-mine --revision 02 --final --views hero,front,rear
```

Choose a new revision number to preserve an existing source pass. The stable model, review scene, and exchange files are refreshed on final packaging.
