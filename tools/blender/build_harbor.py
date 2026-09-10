"""Convert the user-supplied harbor GLB into a reproducible Unity prototype.

Run with Blender --background --factory-startup --python this_file.
Only generated harbor-prototype outputs are replaced. The input GLB is read only.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/Users/niklasborn/Downloads/mario_kart_8_-_toad_harbor.glb')
OUT = ROOT/'game/Assets/_DarioKart/Art/Models/Tracks/harbor-prototype'
ART = ROOT/'art-source/blender/tracks/harbor-prototype'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'Textures').mkdir(exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
bpy.context.view_layer.update()
objects = [o for o in bpy.context.scene.objects if o.type=='MESH']
original = {}
materials = []
for i,o in enumerate(objects):
    original[o.name] = o
    matrix = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = matrix
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for v in o.data.vertices:
        v.co *= .05
        v.co.z += 29.65127
    o.data.update()
    mat = o.active_material
    color, texture, alpha = [1,1,1,1], '', False
    if mat and mat.use_nodes:
        bs = next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if bs:
            color=list(bs.inputs['Base Color'].default_value)
            links=bs.inputs['Base Color'].links
            if links and links[0].from_node.type=='TEX_IMAGE':
                im=links[0].from_node.image
                texture=f'Textures/color_{i:02d}.png'
                im.filepath_raw=str(OUT/texture)
                im.file_format='PNG'
                im.save()
            alpha=bool(bs.inputs['Alpha'].links) or bs.inputs['Alpha'].default_value < .99
    o.name=f'HarborVisual_{i:02d}'
    materials.append({'name':o.name,'color':color,'texture':texture,'alpha':alpha})

# Trace the ground roads explicitly; decorative overhead paths are excluded.
roads = [original[n] for n in ['Object_35','Object_23']]
bvhs = [BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]) for o in roads]
pixels=[(530,1060),(430,1050),(335,1041),(302,1023),(289,1002),(307,977),
        (340,952),(350,914),(350,850),(350,803),(343,761),(342,715),
        (348,681),(366,660),(402,635),(429,615),(455,612),(470,623),
        (489,649),(511,690),(536,739),(563,776),(595,796),(629,802),
        (656,789),(666,759),(651,729),(625,694),(608,659),(602,624),
        (608,598),(628,582),(656,577),(702,582),(749,582),(786,572),
        (831,546),(872,516),(914,472),(953,444),(991,427),(1030,427),
        (1057,438),(1068,460),(1085,486),(1095,516),(1089,546),(1070,574),
        (1042,602),(1026,622),(978,665),(930,710),(880,757),(827,804),
        (775,850),(727,895),(697,923),(684,943),(682,962),(693,985),
        (706,1009),(710,1035),(700,1059),(672,1070),(624,1072),(580,1066)]
def pixel_point(px,py):
    x,y=(5+(px-750)*130/1500)*5,(10+(750-py)*130/1500)*5
    hits=[b.ray_cast(Vector((x,y,150)),Vector((0,0,-1)),250)[0] for b in bvhs]
    hits=[h for h in hits if h is not None]
    z=max((h.z for h in hits),default=0)
    return Vector((x,y,z+.12)),bool(hits)
controls=[]
missing=[]
valid=[]
for px,py in pixels:
    p,hit=pixel_point(px,py)
    controls.append(p)
    valid.append(hit)
    if not hit: missing.append([px,py])
# Small absent road faces (market and summit) get an explicitly bridged height.
# Never project onto roofs or drop a missing sample to sea level.
for i,hit in enumerate(valid):
    if hit: continue
    before=(i-1)%len(controls)
    after=(i+1)%len(controls)
    while not valid[before]: before=(before-1)%len(controls)
    while not valid[after]: after=(after+1)%len(controls)
    a=(controls[i]-controls[before]).xy.length
    b=(controls[after]-controls[i]).xy.length
    controls[i].z=controls[before].z+(controls[after].z-controls[before].z)*a/(a+b)
def catmull(a,b,c,d,t):
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
route=[]
control_indices=[]
for i,b in enumerate(controls):
    a,c,d=controls[(i-1)%len(controls)],controls[(i+1)%len(controls)],controls[(i+2)%len(controls)]
    control_indices.append(len(route))
    for k in range(max(4,math.ceil((c-b).length/2))):
        t=k/max(4,math.ceil((c-b).length/2))
        p=catmull(a,b,c,d,t)
        route.append(p)

def unity(p): return {'x':round(-p.x,4),'y':round(p.z,4),'z':round(-p.y,4)}
def closest_pixel(pixel):
    x,y,_=pixel_point(*pixel)[0]
    return min(range(len(route)),key=lambda i:(route[i].x-x)**2+(route[i].y-y)**2)

# User's red strokes: outer gazebo loop with a steep town cut, and the long
# outside descent. Endpoints overlap the main route for a driveable connection.
alternative_pixels=[
    [(536,739),(551,769),(572,798),(596,820),(621,829),(644,821),
     (662,797),(674,770),(683,740),(690,710),(698,671),(706,632),(713,604),(715,582)],
    [(1041,621),(1037,649),(1024,666),(997,690),(968,716),(936,747),
     (904,778),(873,804),(840,826),(821,849),(798,875),(771,898),
     (749,919),(747,933),(759,957),(770,984),(769,1006),(748,1028),(715,1047)]]
alternatives=[]
alternative_routes=[]
for ai,stroke in enumerate(alternative_pixels):
    start=closest_pixel(stroke[0]);end=closest_pixel(stroke[-1])
    pts=[pixel_point(*p)[0] for p in stroke]
    pts[0]=route[start].copy();pts[-1]=route[end].copy()
    # Height follows the corresponding portion of the course, including its
    # flat harbor approach and summit. Map locations follow the user's red line.
    for i,p in enumerate(pts[1:-1],1):
        nearest=closest_pixel(stroke[i]);p.z=route[nearest].z+.12
    if ai==0:
        # After the gazebo, this branch climbs directly to the upper street.
        for i in range(6,len(pts)):
            t=(i-6)/(len(pts)-1-6);s=t*t*(3-2*t)
            pts[i].z=pts[6].z*(1-s)+pts[-1].z*s
    smooth=[]
    for i in range(len(pts)-1):
        a=pts[max(i-1,0)];b=pts[i];c=pts[i+1];d=pts[min(i+2,len(pts)-1)]
        steps=max(4,math.ceil((c-b).length/1.5))
        for k in range(steps):smooth.append(catmull(a,b,c,d,k/steps))
    smooth.append(pts[-1])
    alternative_routes.append(smooth)
    alternatives.append({'name':['Gazebo and upper street alternative','Outside descent alternative'][ai],
                         'start':start,'end':end,'width':5.5,'points':[unity(p) for p in smooth]})
length=sum((route[(i+1)%len(route)]-p).length for i,p in enumerate(route))
data={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      'scale':.05,'lengthMeters':length,'elevationMeters':max(p.z for p in route)-min(p.z for p in route),
      'widthMeters':14,'materials':materials,'route':[unity(p) for p in route],
      'checkpoints':[closest_pixel(p) for p in [(530,1060),(350,850),(489,649),(786,572),(1095,516),(1042,602),(624,1072)]],
      'jumpIndex':closest_pixel((350,850)), 'hazardIndex':closest_pixel((831,546)),
      'boostIndex':closest_pixel((880,757)), 'alternatives':alternatives,
      'layoutReference':'/Users/niklasborn/Downloads/test.png',
      'controlsMissingRoad':missing,
      'attribution':'Mario Kart 8 - Toad Harbor; uploaded by H,yoshi (Sketchfab). Embedded metadata: CC-BY-4.0. Underlying Nintendo content rights not independently verified.',
      'sourceUrl':'https://sketchfab.com/3d-models/mario-kart-8-toad-harbor-97681cab2c9445069b335e940116562f'}
(OUT/'harbor.json').write_text(json.dumps(data,indent=2))
bpy.ops.object.select_all(action='DESELECT')
for o in objects: o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.fbx(filepath=str(OUT/'harbor-scenery.fbx'),use_selection=True,
    object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,
    bake_anim=False,add_leaf_bones=False,path_mode='STRIP')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'harbor-scenery.blend'))
# Render an exact overhead route comparison in the user's reference framing.
review=ART/'review';review.mkdir(exist_ok=True)
for name,points,color in [('Yellow main circuit',route,(1,.75,.05,1))]+[(f'Red alternative {i+1}',p,(1,.04,.015,1)) for i,p in enumerate(alternative_routes)]:
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=.8;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for dest,src in zip(sp.points,points):dest.co=(src.x,src.y,100,1)
    sp.use_cyclic_u=name.startswith('Yellow')
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob)
    mat=bpy.data.materials.new(name);mat.diffuse_color=color;mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color
    bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=1
    ob.data.materials.append(mat)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1500;sc.render.resolution_y=1500;sc.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(25,50,1500));sc.camera=bpy.context.object;sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=650;sc.camera.data.clip_end=3000
bpy.ops.object.light_add(type='SUN',rotation=(.2,-.3,.2));bpy.context.object.data.energy=2
sc.render.filepath=str(review/'marked-layout.png');bpy.ops.render.render(write_still=True)
print(json.dumps({k:data[k] for k in ['lengthMeters','elevationMeters','widthMeters','controlsMissingRoad']}))
