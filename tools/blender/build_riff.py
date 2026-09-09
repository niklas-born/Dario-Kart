"""Build and render Riff's seated driver model using Blender's native mesh tools.

Run with Blender --background --factory-startup --python-exit-code 1 --python
tools/blender/build_riff.py -- --revision 01 --views front,hero,side,rear
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--revision', default='01')
parser.add_argument('--views', default='front,hero,side,rear')
parser.add_argument('--resolution', type=int, default=900)
parser.add_argument('--samples', type=int, default=48)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT = ROOT / 'art-source/blender/characters/riff'
RENDERS = OUT / 'review' / ('v' + args.revision)
OUT.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection':
        bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
character = bpy.data.collections.new('RIFF_DRIVER')
guide = bpy.data.collections.new('FIT_GUIDE_NOT_FOR_EXPORT')
studio = bpy.data.collections.new('STUDIO')
refs = bpy.data.collections.new('CONCEPT_REFERENCE')
for collection in (character, guide, studio, refs):
    scene.collection.children.link(collection)


def move(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def linear(hex_color):
    vals = [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v < .04045 else ((v+.055)/1.055)**2.4 for v in vals) + (1,)


def material(name, color, roughness=.45, metallic=0, subsurface=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = linear(color)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = linear(color)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Subsurface Weight'].default_value = subsurface
    bsdf.inputs['Subsurface Radius'].default_value = (.65, .3, .18)
    bsdf.inputs['Specular IOR Level'].default_value = .3
    return m


skin = material('Riff | turquoise skin', '17AEBE', .64, subsurface=.025)
horn = material('Riff | deep teal horns and brows', '06546B', .49, subsurface=.01)
lidmat = material('Riff | upper eyelids', '1AABBA', .64, subsurface=.025)
sclera = material('Riff | cool mint sclera', 'B9C3AC', .36)
iris = material('Riff | blue teal iris', '237B8B', .25)
pupil = material('Riff | pupil', '092D37', .20)
mouthmat = material('Riff | mouth interior', '713340', .58)
gum = material('Riff | gums', 'CA5A65', .5, subsurface=.025)
tongue = material('Riff | tongue', 'EE7C86', .42, subsurface=.06)
tooth = material('Riff | warm ivory teeth', 'FFF0CD', .32)
seatmat = material('Guide | charcoal cushion', '323A3C', .64)
wheelmat = material('Guide | leather', '684329', .50)
metal = material('Guide | metal', '92A4A6', .3, .65)
floor = material('Studio | ivory', 'EEE5D7', .72)
floor.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=linear('FFF3DF')
floor.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0
for mat in (skin, lidmat):
    nodes=mat.node_tree.nodes
    nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.18
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=230
    noise.inputs['Detail'].default_value=2
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.13
    bump.inputs['Distance'].default_value=.001
    mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    mat.node_tree.links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])


def mesh_obj(name, vertices, faces, mat, collection=character):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    return obj


def apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def uvball(name, center, scale, mat, collection=character, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=center)
    obj = move(bpy.context.object, collection)
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def rounded_box(name, center, scale, radius, mat, collection=character):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = move(bpy.context.object, collection)
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    m = obj.modifiers.new('Sculpted soft edges', 'BEVEL')
    m.width = radius
    m.segments = 4
    apply(obj, m)
    n = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    apply(obj, n)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def catmull(points, steps=10):
    pts = [Vector(p) for p in points]
    result = []
    for i in range(len(pts)-1):
        a,b,c,d = pts[max(i-1,0)],pts[i],pts[i+1],pts[min(i+2,len(pts)-1)]
        for j in range(steps):
            t = j/steps
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    result.append(pts[-1])
    return result


def tube(name, points, radii, mat, sides=16, steps=10, collection=character):
    samples = catmull([tuple(p)+(r,) for p,r in zip(points,radii)], steps)
    verts=[]
    for i,p in enumerate(samples):
        direction = Vector(samples[min(i+1,len(samples)-1)][:3])-Vector(samples[max(0,i-1)][:3])
        direction.normalize()
        b = direction.cross(Vector((0,1,0)))
        if b.length < .01:
            b = direction.cross(Vector((1,0,0)))
        b.normalize()
        n = direction.cross(b).normalized()
        center = Vector(p[:3])
        for k in range(sides):
            angle = 2*math.pi*k/sides
            verts.append(center+max(.001,p[3])*(b*math.cos(angle)+n*math.sin(angle)))
    faces=[]
    for i in range(len(samples)-1):
        for k in range(sides):
            faces.append((i*sides+k,i*sides+(k+1)%sides,(i+1)*sides+(k+1)%sides,(i+1)*sides+k))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(samples)-1)*sides+k for k in range(sides)))
    return mesh_obj(name,verts,faces,mat,collection)


# Smooth rings provide a continuous pear silhouette, avoiding a separate head/neck.
profile = [(.20,.01,.01,.05),(.28,.25,.2,.07),(.42,.405,.29,.055),
           (.62,.47,.32,.02),(.83,.455,.325,0),(1.04,.397,.30,0),
           (1.23,.337,.278,.004),(1.38,.235,.196,.02),(1.47,.01,.01,.03)]
profile_samples = catmull(profile,8)


def cross_section(z):
    for a,b in zip(profile_samples[:-1],profile_samples[1:]):
        if a[0] <= z <= b[0]:
            t=(z-a[0])/(b[0]-a[0])
            return tuple(a[j]*(1-t)+b[j]*t for j in (1,2,3))
    p=profile_samples[0] if z < .2 else profile_samples[-1]
    return p[1],p[2],p[3]


def front_y(x,z):
    rx,ry,cy=cross_section(z)
    base=cy-ry*math.sqrt(max(.001,1-(x/max(.01,rx))**2))
    front_factor=max(.001,1-(x/max(.01,rx))**2)**1.5
    return base-.075*math.exp(-((z-1.015)/.11)**2)*math.exp(-(x/.31)**4)*front_factor


verts=[]
N=96
for z,rx,ry,cy in profile_samples:
    for j in range(N):
        a=2*math.pi*j/N
        x=rx*math.cos(a)
        y=cy+ry*math.sin(a)
        if math.sin(a) < 0:
            y-=.075*math.exp(-((z-1.015)/.11)**2)*math.exp(-(x/.31)**4)*(-math.sin(a))**3
        verts.append((x,y,z))
faces=[]
for i in range(len(profile_samples)-1):
    for j in range(N):
        faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
faces.extend([tuple(reversed(range(N))),tuple((len(profile_samples)-1)*N+j for j in range(N))])
body=mesh_obj('Riff_Skin',verts,faces,skin)
skin_parts=[body]

for sign,suffix in [(-1,'L'),(1,'R')]:
    arm_points=[(sign*.22,.015,1.018),(sign*.377,-.045,.925),
                (sign*.434,-.19,.79),(sign*.39,-.37,.773),(sign*.282,-.56,.847)]
    skin_parts.append(tube('Arm_'+suffix,arm_points,[.11,.131,.137,.13,.089],skin))
    # Closed driving fist: the outer silhouette is rounded; finger divisions are carved below.
    skin_parts.append(uvball('Palm_'+suffix,(sign*.276,-.608,.839),(.125,.099,.119),skin))
    thumbtip=(sign*.17,-.683,.853)
    skin_parts.append(tube('Thumb_'+suffix,[(sign*.205,-.558,.863),(sign*.157,-.622,.894),
                           thumbtip],[.045,.042,.029],skin,sides=16))
    skin_parts.append(uvball('Thumbtip_'+suffix,thumbtip,(.029,.029,.029),skin,segments=24,rings=16))
    # Hidden seated anatomy stays compact and can be checked without the guide.
    skin_parts.append(uvball('Thigh_'+suffix,(sign*.21,-.17,.285),(.17,.25,.14),skin))
    skin_parts.append(uvball('Foot_'+suffix,(sign*.21,-.43,.205),(.125,.22,.095),skin))

bpy.ops.object.select_all(action='DESELECT')
for obj in skin_parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
remesh=body.modifiers.new('Continuous sculpt surface','REMESH')
remesh.mode='VOXEL'
remesh.voxel_size=.0055
remesh.use_smooth_shade=True
apply(body,remesh)
smooth=body.modifiers.new('Relax fused anatomy','SMOOTH')
smooth.factor=.65
smooth.iterations=12
apply(body,smooth)

for sign,suffix in [(-1,'L'),(1,'R')]:
    for index in range(2):
        path=[]
        for j in range(17):
            t=j/16
            x=sign*(.324-index*.007-.108*t)
            z=.902-index*.048-.076*t+.009*math.sin(math.pi*t)
            y=-.608-.099*math.sqrt(max(.01,1-((abs(x)-.276)/.125)**2-((z-.839)/.119)**2))-.001
            path.append((x,y,z))
        cut=tube('Temporary_finger_crease',path,[.001+.008*math.sin(math.pi*j/16)**.5 for j in range(17)],skin,steps=2,sides=12)
        b=body.modifiers.new('Sculpt finger division','BOOLEAN')
        b.operation='DIFFERENCE'
        b.solver='EXACT'
        b.object=cut
        apply(body,b)
        bpy.data.objects.remove(cut,do_unlink=True)

# Physically cut the smile opening into the body, then line the cavity.
outline=[]
for i in range(49):
    u=-1+2*i/48
    outline.append((.285*u,1.004+.071*u*u))
for i in range(47,0,-1):
    u=-1+2*i/48
    outline.append((.285*u,.935+.14*u*u))
cutverts=[(x,y,z) for y in (-.85,-.11) for x,z in outline]
n=len(outline)
cutfaces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
cutfaces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
cutter=mesh_obj('Temporary_smile_cutter',cutverts,cutfaces,None)
boolean=body.modifiers.new('Smile cavity','BOOLEAN')
boolean.operation='DIFFERENCE'
boolean.solver='EXACT'
boolean.object=cutter
apply(body,boolean)
bpy.data.objects.remove(cutter,do_unlink=True)
relax=body.modifiers.new('Soften carved smile border','SMOOTH')
relax.factor=.35
relax.iterations=3
apply(body,relax)
dec=body.modifiers.new('Sculpt topology reduction','DECIMATE')
dec.ratio=.30
apply(body,dec)
for p in body.data.polygons:
    p.use_smooth=True

bowlverts=[(0,-.108,.943)]
bowlverts += [(x,front_y(x,z)+.007,z) for x,z in outline]
bowlfaces=[(0,1+i,1+(i+1)%n) for i in range(n)]
mesh_obj('Mouth_Cavity',bowlverts,bowlfaces,mouthmat)
lower=[]
for i in range(25):
    u=-.98+1.96*i/24
    x=.285*u
    z=.935+.14*u*u
    lower.append((x,front_y(x,z)-.002,z))
tube('Lower_Lip',lower,[.005+(.009*(1-abs(-.98+1.96*i/24))) for i in range(25)],skin,steps=2)
upper=[]
for i in range(25):
    u=-1+2*i/24
    x=.285*u
    z=1.004+.071*u*u
    upper.append((x,front_y(x,z)-.001,z))
tube('Upper_Lip',upper,[.004+.009*(1-abs(-1+2*i/24)) for i in range(25)],skin,steps=2)
uvball('Tongue',(0,-.303,.951),(.10,.036,.016),tongue)
for row in ('upper','lower'):
    pts=[]
    for i in range(33):
        u=-.95+1.9*i/32
        x=.285*u
        z=1.004+.071*u*u-.007 if row=='upper' else .935+.14*u*u+.008
        pts.append((x,front_y(x,z)+.035,z))
    tube('Gums_'+row,pts,[.009]*33,gum,steps=2,sides=12)
for row,count in [('upper',8),('lower',5)]:
    for i in range(count):
        if row=='upper':
            x=[-.230,-.187,-.121,-.042,.042,.121,.187,.230][i]
            width=[.031,.048,.069,.080,.080,.069,.048,.031][i]
        else:
            x=(i-2)*.072
            width=.066
        u=x/.285
        top=1.004+.071*u*u
        bottom=.935+.14*u*u
        h=.034*(1-.5*abs(u)) if row=='upper' else .023*(1-.6*abs(u))
        z=top-h/2+.002 if row=='upper' else bottom+h/2-.003
        y=front_y(x,z)+.042
        t=rounded_box('Tooth_'+row+'_'+str(i),(x,y,z),(width,.038,h),.009,tooth)
        t.rotation_euler[2]=-.28*u

# Eyes and spherical skin lids are separate geometry so blink remains editable.
for sign,suffix in [(-1,'L'),(1,'R')]:
    cx=sign*.134
    cy=-.282
    cz=1.187
    rx,ry,rz=.131,.105,.103
    uvball('Eye_'+suffix,(cx,cy,cz),(rx,ry,rz),sclera)
    # A skin cap occupies the upper 60 percent of each globe.
    cutoff=-.026/rz
    latitude0=math.asin(cutoff)
    ev=[]
    for row in range(25):
        lat=latitude0+(math.pi/2-latitude0)*row/24
        for col in range(64):
            lon=2*math.pi*col/64
            ev.append((cx+(rx+.004)*math.cos(lat)*math.cos(lon),
                       cy+(ry+.004)*math.cos(lat)*math.sin(lon),cz+(rz+.004)*math.sin(lat)))
    ef=[]
    for row in range(24):
        for col in range(64):
            ef.append((row*64+col,row*64+(col+1)%64,(row+1)*64+(col+1)%64,(row+1)*64+col))
    eyelid=mesh_obj('Upper_Lid_'+suffix,ev,ef,lidmat)
    eyelid.shape_key_add(name='Basis')
    blink=eyelid.shape_key_add(name='Blink')
    blink.value=0.0
    for idx,v in enumerate(blink.data):
        row,col=divmod(idx,64)
        lat=-math.pi/2+(math.pi)*row/24
        lon=2*math.pi*col/64
        v.co=(cx+(rx+.004)*math.cos(lat)*math.cos(lon),
              cy+(ry+.004)*math.cos(lat)*math.sin(lon),cz+(rz+.004)*math.sin(lat))
    ix=cx-sign*.008
    iz=1.141
    # Color patches follow the actual globe, so the skin lid occludes them.
    # Separate spheres in front of the eye would incorrectly poke through a blink.
    for label,radx,radz,offset,mat in [('Iris',.047,.045,.001,iris),('Pupil',.027,.032,.002,pupil)]:
        pv=[]
        for row in range(13):
            r=max(.0001,row/12)
            for col in range(48):
                angle=col*2*math.pi/48
                x=ix+radx*r*math.cos(angle)
                z=iz+radz*r*math.sin(angle)
                depth=math.sqrt(max(.001,1-((x-cx)/rx)**2-((z-cz)/rz)**2))
                pv.append((x,cy-ry*depth-offset,z))
        pf=[]
        for row in range(12):
            for col in range(48):
                pf.append((row*48+col,row*48+(col+1)%48,(row+1)*48+(col+1)%48,(row+1)*48+col))
        mesh_obj(label+'_'+suffix,pv,pf,mat)
    brow=uvball('Eyebrow_'+suffix,(sign*.139,-.256,1.327),(.101,.035,.032),horn,segments=48,rings=24)
    for v in brow.data.vertices:
        v.co.z-=1.8*v.co.x*v.co.x
        v.co.y+=front_y(brow.location.x+v.co.x,brow.location.z+v.co.z)-brow.location.y-.015

# Distinctive C-shaped horns, growing outwards and curling back towards center.
for sign,suffix in [(-1,'L'),(1,'R')]:
    hornpoints=[(sign*.13,.05,1.26),(sign*.31,.07,1.365),(sign*.465,.035,1.493),
                (sign*.476,-.025,1.626),(sign*.382,-.075,1.688),
                (sign*.280,-.105,1.660),(sign*.224,-.13,1.615)]
    hornpoints=[(x,y+.35*(abs(x)-.30),z) for x,y,z in hornpoints]
    radii=[.09,.11,.095,.080,.058,.027,.003]
    h=tube('Horn_'+suffix,hornpoints,radii,horn,sides=64,steps=12)
    h.scale.x=.93
    bpy.context.view_layer.objects.active=h
    bpy.ops.object.select_all(action='DESELECT')
    h.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    hr=h.modifiers.new('Sculpt continuous horn surface','REMESH')
    hr.mode='VOXEL'
    hr.voxel_size=.004
    hr.use_smooth_shade=True
    apply(h,hr)
    hs=h.modifiers.new('Relax horn curl','SMOOTH')
    hs.factor=.7
    hs.iterations=9
    apply(h,hs)
    hd=h.modifiers.new('Horn sculpt reduction','DECIMATE')
    hd.ratio=.22
    apply(h,hd)
    for p in h.data.polygons:
        p.use_smooth=True

for index,(x,height,lean) in enumerate([(-.074,.13,-.035),(0,.205,.009),(.075,.145,.035)]):
    tuft=uvball('Crown_Tuft_'+str(index),(x,-.025,1.414+height*.36),(.033,.029,height*.64),skin,segments=32,rings=24)
    tuft.rotation_euler[1]=math.atan2(lean,height)
for index,(y,z,r) in enumerate([(-.07,1.464,.024),(-.106,1.448,.021)]):
    uvball('Front_Crest_Bud_'+str(index),(0,y,z),(r,r,r),skin,segments=24,rings=16)
for index in range(3):
    z=1.43-index*.062
    rx,ry,cy=cross_section(z)
    uvball('Back_Tuft_'+str(index),(0,cy+ry-.004,z),(.027,.028,.039),skin,segments=24,rings=16)

# Tiny upturned nose is a skin-colored saddle between the eyes and smile.
nose=tube('Nose',[(-.037,front_y(-.037,1.083),1.083),(0,front_y(0,1.076)-.010,1.076),(.037,front_y(.037,1.083),1.083)],
          [.002,.012,.002],skin,steps=12,sides=16)

# Separate neutral fit guide. It is never included in driver exports.
rounded_box('Seat_Cushion',(0,.065,.165),(.74,.64,.13),.055,seatmat,guide)
seat=rounded_box('Seat_Back',(0,.295,.52),(.69,.16,.76),.073,seatmat,guide)
seat.rotation_euler[0]=math.radians(7)
bpy.ops.mesh.primitive_torus_add(major_radius=.255,minor_radius=.032,major_segments=64,minor_segments=16,
                               location=(0,-.654,.740))
wheel=move(bpy.context.object,guide)
wheel.name='Steering_Wheel_Guide'
wheel.rotation_euler[0]=math.radians(52)
wheel.data.materials.append(wheelmat)
for p in wheel.data.polygons:
    p.use_smooth=True
for angle in (0,2*math.pi/3,4*math.pi/3):
    end=wheel.matrix_world @ Vector((.225*math.cos(angle),.225*math.sin(angle),0))
    # Matrix world needs an evaluated update after assigning rotation/location.
bpy.context.view_layer.update()
for angle in (0,2*math.pi/3,4*math.pi/3):
    end=wheel.matrix_world @ Vector((.225*math.cos(angle),.225*math.sin(angle),0))
    tube('Wheel_Spoke',[(0,-.654,.740),end],[.017,.014],metal,collection=guide,steps=2)
uvball('Wheel_Hub',(0,-.657,.740),(.045,.035,.045),metal,guide,24,16)

# Pack references inside the .blend for modeling comparisons.
for i,relative in enumerate(['art-source/concepts/racers/round-02/01-riff-v2.png',
                             'art-source/concepts/racers/round-01/01-riff-v1.png']):
    im=bpy.data.images.load(str(ROOT/relative))
    im.pack()
    obj=bpy.data.objects.new('Reference_'+str(i),None)
    refs.objects.link(obj)
    obj.empty_display_type='IMAGE'
    obj.data=im
    obj.empty_display_size=3
    obj.location=(3+i*3,1,1.5)
    obj.rotation_euler=(math.pi/2,0,0)
    obj.hide_render=True
refs.hide_viewport=True

# Soft studio lighting matches the concepts; all illumination is real scene data.
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,.04))
ground=move(bpy.context.object,studio)
ground.name='Studio_Ground'
ground.data.materials.append(floor)
# A separate camera-visible backdrop keeps lighting physical and the review background ivory.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,4,4),rotation=(math.pi/2,0,0))
backdrop=move(bpy.context.object,studio)
backdrop.name='Studio_Backdrop'
bgmat=bpy.data.materials.new('Studio | camera ivory')
bgmat.use_nodes=True
ns=bgmat.node_tree.nodes
ns.clear()
em=ns.new('ShaderNodeEmission')
em.inputs['Color'].default_value=linear('FCF5E8')
em.inputs['Strength'].default_value=1
out=ns.new('ShaderNodeOutputMaterial')
bgmat.node_tree.links.new(em.outputs[0],out.inputs[0])
backdrop.data.materials.append(bgmat)
backdrop.visible_diffuse=False
backdrop.visible_glossy=False
backdrop.visible_shadow=False
scene.world.use_nodes=True
worldnodes=scene.world.node_tree.nodes
worldlinks=scene.world.node_tree.links
worldnodes['Background'].inputs[0].default_value=(.82,.88,1,1)
worldnodes['Background'].inputs[1].default_value=.25
visible_bg=worldnodes.new('ShaderNodeBackground')
visible_bg.inputs[0].default_value=linear('F8F0E3')
visible_bg.inputs[1].default_value=3
ray=worldnodes.new('ShaderNodeLightPath')
mix=worldnodes.new('ShaderNodeMixShader')
worldlinks.new(ray.outputs['Is Camera Ray'],mix.inputs[0])
worldlinks.new(worldnodes['Background'].outputs[0],mix.inputs[1])
worldlinks.new(visible_bg.outputs[0],mix.inputs[2])
worldlinks.new(mix.outputs[0],worldnodes['World Output'].inputs[0])


def area(name,position,power,size,color):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()


area('Key_softbox',(-3,-4,5),350,3.5,(1,.95,.9))
area('Fill_softbox',(3,-2,3),120,3,(.85,.94,1))
area('Rim_softbox',(0,3,4),350,3,(1,.96,.89))
scene.render.engine='CYCLES'
scene.cycles.samples=args.samples
scene.cycles.use_denoising=True
scene.render.resolution_x=args.resolution
scene.render.resolution_y=args.resolution
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.render.film_transparent=False

cameras={
    'front':((0,-6,1.20),(0,-.07,1.00)),
    'hero':((3,-6,2.45),(0,-.07,.98)),
    'side':((6,0,1.20),(0,-.10,1.00)),
    'rear':((0,6,1.30),(0,-.02,1.00)),
    'face':((0,-6,1.22),(0,-.25,1.19)),
    'driver_front':((0,-6,2.02),(0,-.12,1.17)),
    'driver_hero':((3,-6,2.30),(0,-.12,1.17)),
    'driver_side':((6,0,2.02),(0,-.12,1.17)),
    'driver_rear':((0,6,2.02),(0,0,1.17)),
}
for name,(position,target) in cameras.items():
    data=bpy.data.cameras.new('Camera_'+name)
    obj=bpy.data.objects.new('Camera_'+name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'
    data.ortho_scale=1.30 if name.startswith('driver_') else 1.16 if name=='face' else 2.12
    data.lens=70
scene.camera=bpy.data.objects['Camera_hero']

scene['concept_status']='Iterative driver sculpt: requires render comparison; not approved final'
scene['revision']=args.revision
scene['scope']='Riff driver; seat and wheel are fitting guides, not the final kart'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for space in [a.spaces.active for a in screen.areas if a.type=='VIEW_3D']:
        space.region_3d.view_distance=3.5
        space.region_3d.view_location=(0,0,1)
        space.clip_end=500
blendpath=OUT/('riff-driver-v'+args.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blendpath))
stats={'revision':args.revision,'meshObjects':len([o for o in character.objects if o.type=='MESH']),
       'triangles':sum(len(p.vertices)-2 for o in character.objects if o.type=='MESH' for p in o.data.polygons),
       'blend':str(blendpath.relative_to(ROOT))}
(RENDERS/'build-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('RIFF_BUILD '+json.dumps(stats),flush=True)
for view in args.views.split(','):
    scene.camera=bpy.data.objects['Camera_'+view]
    scene.render.filepath=str(RENDERS/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RIFF_RENDER '+scene.render.filepath,flush=True)
