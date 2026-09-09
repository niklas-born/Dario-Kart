"""Export the EXPORT collection to FBX. No changes are saved to source art."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
root = Path(__file__).resolve().parents[2]
source = Path(bpy.data.filepath).resolve()
if not bpy.data.filepath or not source.is_file():
    raise ValueError("Open a saved .blend source file before exporting.")
source_relative = source.relative_to(root / "art-source")
output = Path(args.output).resolve()
output.relative_to(root / "game/Assets/_DarioKart/Art/Models")
if output.suffix.lower() != ".fbx":
    raise ValueError("Output must be an .fbx in game/Assets/_DarioKart/Art/Models.")
scene = bpy.context.scene
if scene.unit_settings.system != "METRIC" or abs(scene.unit_settings.scale_length - 1) > 1e-6:
    raise ValueError("Use metric units with unit scale 1 (meters).")
collection = bpy.data.collections.get("EXPORT")
if collection is None or not collection.all_objects:
    raise ValueError("Add static meshes to a nonempty collection named EXPORT.")
objects = sorted(collection.all_objects, key=lambda obj: obj.name)
for obj in objects:
    if obj.type != "MESH" or obj.parent is not None or obj.animation_data is not None:
        raise ValueError(f"{obj.name}: this preset accepts only unparented static meshes.")
    if obj.rotation_mode != "XYZ" or any(abs(v) > 1e-6 for v in obj.rotation_euler):
        raise ValueError(f"{obj.name}: apply rotation and use XYZ rotation mode.")
    if any(abs(v - 1) > 1e-6 for v in obj.scale):
        raise ValueError(f"{obj.name}: apply scale before exporting.")
    if not obj.data.uv_layers:
        raise ValueError(f"{obj.name}: a UV map is required.")
    if obj.hide_get() or obj.hide_viewport or obj.name not in bpy.context.view_layer.objects:
        raise ValueError(f"{obj.name}: export meshes must be visible in the active view layer.")

bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
output.parent.mkdir(parents=True, exist_ok=True)
result = bpy.ops.export_scene.fbx(
    filepath=str(output), use_selection=True, object_types={"MESH"},
    global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
    bake_anim=False, add_leaf_bones=False, path_mode="STRIP",
)
if "FINISHED" not in result or not output.is_file():
    raise RuntimeError("FBX export did not finish.")
manifest = {
    "schemaVersion": 1,
    "source": "art-source/" + source_relative.as_posix(),
    "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "output": output.relative_to(root).as_posix(),
    "outputSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    "blenderVersion": bpy.app.version_string,
    "preset": "static-mesh-v1",
    "objects": [obj.name for obj in objects],
    "units": "meters",
}
output.with_suffix(".export.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Exported {len(objects)} mesh(es): {output}")
