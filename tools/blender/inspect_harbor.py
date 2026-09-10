"""Read-only GLB inspection; renders and metrics go to a temporary review folder."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT = Path('/tmp/dario-harbor-inspect')
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath='/Users/niklasborn/Downloads/mario_kart_8_-_toad_harbor.glb')
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
stats = []
for o in meshes:
    matrix = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = matrix
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.select_set(False)
    for v in o.data.vertices:
        v.co *= .01
    o.data.update()
    area = sum(p.area for p in o.data.polygons)
    up = sum(p.area for p in o.data.polygons if p.normal.z > .7)
    stats.append({'name': o.name, 'mesh': o.data.name, 'area': area, 'up': up,
                  'materials': [m.name for m in o.data.materials]})
(OUT / 'meshes.json').write_text(json.dumps(stats, indent=2))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1500
sc.render.resolution_y = 1500
sc.render.resolution_percentage = 100
sc.world.color = (.4, .4, .4)
sc.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add(location=(5, 10, 300))
cam = bpy.context.object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 130
sc.camera = cam
bpy.ops.object.light_add(type='SUN', rotation=(.2, -.3, .2))
bpy.context.object.data.energy = 2
sc.render.filepath = str(OUT / 'top.png')
bpy.ops.render.render(write_still=True)
cam.location = (105, -130, 135)
cam.rotation_euler = (Vector((5, 10, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = str(OUT / 'perspective.png')
bpy.ops.render.render(write_still=True)
print('INSPECTION', OUT)
from mathutils.bvhtree import BVHTree
bvhs = [(o, BVHTree.FromPolygons([v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons])) for o in meshes]
pixels = [(530,1057),(400,1045),(310,1030),(300,990),(345,950),(350,850),(350,780),(350,680),(305,625),(300,590),(435,555),(475,600),(505,675),(565,770),(615,795),(660,780),(655,740),(620,690),(600,630),(615,590),(650,575),(730,575),(815,550),(910,480),(980,435),(1040,450),(1080,490),(1090,530),(1065,570),(970,670),(865,765),(750,865),(675,945),(685,980),(710,1020),(700,1050),(665,1070)]
samples=[]
for px,py in pixels:
    x,y = 5+(px-750)*130/1500,10+(750-py)*130/1500
    hits=[]
    for o,bvh in bvhs:
        loc,n,face,dist=bvh.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),200)
        if loc is not None:
            hits.append({'object':o.name,'z':round(loc.z,3),'normal':list(n)})
    samples.append({'pixel':[px,py],'xy':[x,y],'hits':sorted(hits,key=lambda h:-h['z'])})
(OUT/'route-probes.json').write_text(json.dumps(samples,indent=2))
