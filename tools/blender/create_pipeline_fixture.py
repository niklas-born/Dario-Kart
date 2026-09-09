"""Create an original metric ramp fixture. Run using Blender --background."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
destination = ROOT / "art-source/blender/props/pipeline_ramp.blend"
if destination.exists():
    raise FileExistsError(f"Preserving existing source: {destination}")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
collection = bpy.data.collections.new("EXPORT")
bpy.context.scene.collection.children.link(collection)
# A wedge rising along Blender -Y; 4 m wide, 8 m long, 2 m tall.
vertices = [(-2, 4, 0), (2, 4, 0), (-2, -4, 0), (2, -4, 0),
            (-2, -4, 2), (2, -4, 2)]
faces = [(0, 1, 3, 2), (0, 4, 5, 1), (2, 3, 5, 4), (0, 2, 4), (1, 5, 3)]
mesh = bpy.data.meshes.new("PipelineRampMesh")
mesh.from_pydata(vertices, [], faces)
mesh.update()
ramp = bpy.data.objects.new("PipelineRamp", mesh)
collection.objects.link(ramp)
bpy.context.view_layer.objects.active = ramp
ramp.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode="OBJECT")
destination.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
print(f"Created metric pipeline fixture: {destination}")
