"""Build Grit's original seated cyclops sculpt and render review angles."""
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
parser.add_argument('--views', default='hero,front,side,rear,face')
parser.add_argument('--resolution', type=int, default=1100)
parser.add_argument('--samples', type=int, default=40)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
REV = int(args.revision)
OUT = ROOT/'art-source/blender/characters/grit'
REVIEW = OUT/'review'/('v'+args.revision)
REVIEW.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1


def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


driver = collection('GRIT_DRIVER')
guide = collection('FIT_GUIDE_NOT_FOR_EXPORT')
studio = collection('STUDIO')
refs = collection('CONCEPT_REFERENCE')


def move(obj, target):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply(obj, mod):
    select(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def linear(color):
    c = [int(color[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)


def material(name, color, rough=.45, metal=0, sss=0):
    mat = bpy.data.materials.new('Grit | '+name)
    mat.diffuse_color = linear(color)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = linear(color)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Subsurface Radius'].default_value = (.7,.32,.14)
    p.inputs['Specular IOR Level'].default_value = .3
    return mat


skin = material('golden yellow skin','FFC900',.48,sss=.035)
hornmat = material('warm ivory horns','F3E3BF',.34,sss=.02)
white = material('warm eye white','F1E8D0',.32)
iris = material('amber iris','A56C0A',.28)
pupil = material('near black pupil','171508',.23)
mouthmat = material('deep mouth cavity','58251E',.64)
gum = material('warm gums','B64228',.48,sss=.025)
teeth = material('ivory teeth','FFF3D8',.32)
tongue = material('tongue','E57254',.48,sss=.04)
seatmat = material('fitting seat charcoal','343B3A',.68)
rubber = material('fitting steering grip','202725',.6)
metal = material('fitting wheel metal','848984',.35,.7)


def mesh(name, verts, faces, mat, coll=driver):
    data = bpy.data.meshes.new(name+'_Mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    coll.objects.link(obj)
    if mat:
        data.materials.append(mat)
    for p in data.polygons:
        p.use_smooth = True
    return obj


def ball(name, pos, scale, mat=skin, coll=driver, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    obj = move(bpy.context.object,coll)
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def box(name, pos, size, radius, mat, coll=driver):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    obj = move(bpy.context.object,coll)
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new('Rounded manufactured edges','BEVEL')
    mod.width, mod.segments = radius,5
    apply(obj,mod)
    mod = obj.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    apply(obj,mod)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def spline(points, steps=10):
    p = [Vector(v) for v in points]
    out = []
    for i in range(len(p)-1):
        a,b,c,d = p[max(0,i-1)],p[i],p[i+1],p[min(len(p)-1,i+2)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out+[p[-1]]


def tube(name, points, radii, mat=skin, sides=24, steps=8, coll=driver):
    points=spline([tuple(p)+(r,) for p,r in zip(points,radii)],steps)
    verts=[]
    for i,p in enumerate(points):
        tangent=(Vector(points[min(i+1,len(points)-1)][:3])-Vector(points[max(0,i-1)][:3])).normalized()
        b=tangent.cross(Vector((0,1,0)))
        if b.length<.01:
            b=tangent.cross(Vector((1,0,0)))
        b.normalize()
        n=tangent.cross(b).normalized()
        for j in range(sides):
            a=2*math.pi*j/sides
            verts.append(Vector(p[:3])+max(.0004,p[3])*(b*math.cos(a)+n*math.sin(a)))
    faces=[]
    for i in range(len(points)-1):
        for j in range(sides):
            faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]
    return mesh(name,verts,faces,mat,coll)


# A wide upper body and taper below the elbows give Grit his egg-shaped silhouette.
profile=spline([(.205,.007,.008,.04),(.27,.225,.205,.035),(.43,.35,.27,.02),
                (.64,.424,.323,.015),(.86,.469,.35,.025),(1.08,.476,.348,.037),
                (1.28,.417,.31,.055),(1.45,.294,.232,.068),
                (1.535,.145,.125,.068),(1.56,.002,.002,.065)],10)


def section(z):
    for a,b in zip(profile,profile[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0])
            return tuple(a[k]*(1-t)+b[k]*t for k in (1,2,3))
    return tuple(profile[0 if z<.205 else -1][k] for k in (1,2,3))


def front(x,z):
    rx,ry,cy=section(z)
    f=max(.001,1-(x/max(.001,rx))**2)
    return cy-ry*math.sqrt(f)-.047*math.exp(-((z-1.003)/.145)**2)*f**1.5


verts=[]
N=112
for z,rx,ry,cy in profile:
    for j in range(N):
        a=2*math.pi*j/N
        x,y=rx*math.cos(a),cy+ry*math.sin(a)
        if math.sin(a)<0:
            y-=.047*math.exp(-((z-1.003)/.145)**2)*(-math.sin(a))**3
        verts.append((x,y,z))
faces=[]
for i in range(len(profile)-1):
    for j in range(N):
        faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
faces += [tuple(reversed(range(N))),tuple((len(profile)-1)*N+j for j in range(N))]
body=mesh('Grit_Skin',verts,faces,skin)
parts=[body]
for s,side in [(-1,'L'),(1,'R')]:
    parts.append(tube('Arm_'+side,[(s*.31,.015,.97),(s*.437,-.06,.845),
                      (s*.465,-.245,.686),(s*.409,-.426,.67),(s*.277,-.595,.742)],
                      [.133,.139,.138,.135,.103]))
    parts.append(ball('Palm_'+side,(s*.281,-.641,.724),(.126,.105,.118)))
    parts.append(tube('Thumb_'+side,[(s*.22,-.586,.773),(s*.173,-.651,.789),(s*.176,-.721,.740)],
                      [.05,.042,.033]))
    parts.append(ball('Thumb_Tip_'+side,(s*.176,-.721,.740),(.033,.033,.033),segments=24,rings=16))
    parts.append(ball('Thigh_'+side,(s*.198,-.175,.278),(.172,.267,.15)))
    parts.append(ball('Foot_'+side,(s*.202,-.445,.197),(.142,.225,.105)))
    # Small toe bulges are integrated into the foot, without adding separate dangling digits.
    for i in range(3):
        parts.append(ball('Toe_'+side+str(i),(s*(.13+i*.072),-.594,.192),(.046,.071,.061),segments=24,rings=16))
bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
mod=body.modifiers.new('Fuse original sculpt anatomy','REMESH')
mod.mode='VOXEL'
mod.voxel_size=.005
mod.use_smooth_shade=True
apply(body,mod)
mod=body.modifiers.new('Relax anatomical joins','SMOOTH')
mod.factor,mod.iterations=.65,11
apply(body,mod)

# Closed driving fists with two softly carved finger divisions and a separate thumb silhouette.
for s,side in [(-1,'L'),(1,'R')]:
    for i in range(2):
        path=[]
        for j in range(17):
            t=j/16
            x=s*(.334-i*.006-.114*t)
            z=.785-i*.049-.073*t+.007*math.sin(math.pi*t)
            y=-.641-.105*math.sqrt(max(.01,1-((abs(x)-.281)/.126)**2-((z-.724)/.118)**2))-.001
            path.append((x,y,z))
        cut=tube('Finger_crease_cutter',path,[.001+.008*math.sin(math.pi*j/16)**.5 for j in range(17)],steps=2,sides=12)
        mod=body.modifiers.new('Finger crease','BOOLEAN')
        mod.operation,mod.solver,mod.object='DIFFERENCE','EXACT',cut
        apply(body,mod)
        bpy.data.objects.remove(cut,do_unlink=True)

# Cut an actual curved grin into the face, with a recessed interior.
WIDTH=.364
def top(u): return 1.005+.100*u*u
def bottom(u): return .864+.241*u*u
outline=[(WIDTH*(-1+2*i/64),top(-1+2*i/64)) for i in range(65)]
outline += [(WIDTH*(-1+2*i/64),bottom(-1+2*i/64)) for i in range(63,0,-1)]
n=len(outline)
cut=mesh('Smile_cutter',[(x,y,z) for y in (-.9,-.065) for x,z in outline],
         [tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],None)
mod=body.modifiers.new('Wide smile cavity','BOOLEAN')
mod.operation,mod.solver,mod.object='DIFFERENCE','EXACT',cut
apply(body,mod)
bpy.data.objects.remove(cut,do_unlink=True)
mod=body.modifiers.new('Soften smile corners','SMOOTH')
mod.factor,mod.iterations=.30,3
apply(body,mod)
mod=body.modifiers.new('Working sculpt reduction','DECIMATE')
mod.ratio=.38
apply(body,mod)
for p in body.data.polygons:
    p.use_smooth=True
mesh('Mouth_Cavity',[(0,-.064,.974)]+[(x,front(x,z)+.012,z) for x,z in outline],
     [(0,i+1,(i+1)%n+1) for i in range(n)],mouthmat)
for name,fn in [('Upper_Lip',top),('Lower_Lip',bottom)]:
    points=[]
    for i in range(41):
        u=-.98+1.96*i/40
        x,z=WIDTH*u,fn(u)
        points.append((x,front(x,z)-.005,z))
    tube(name,points,[.010+.008*(1-abs(-.98+1.96*i/40)) for i in range(41)],steps=2)
    tube(name.replace('Lip','Gum'),[(x,y+.033,z+(-.009 if name.startswith('Upper') else .009)) for x,y,z in points],
         [.010]*len(points),gum,steps=2,sides=16)
ball('Tongue',(0,-.265,.882),(.13,.048,.026),tongue)


def pointed_tooth(name, x, base, tip, width):
    # Rounded triangular tusks, wider at the gum and flattened along the mouth depth.
    rings=[(0,width*.47,.023),(.12,width*.50,.027),(.47,width*.34,.024),(.80,width*.13,.013),(1,.001,.001)]
    tv=[]
    for t,rx,ry in rings:
        z=base+(tip-base)*t
        center_y=front(x,z)+.043
        for j in range(24):
            a=2*math.pi*j/24
            tv.append((x+rx*math.cos(a),center_y+ry*math.sin(a),z))
    tf=[]
    for i in range(len(rings)-1):
        for j in range(24):
            tf.append((i*24+j,i*24+(j+1)%24,(i+1)*24+(j+1)%24,(i+1)*24+j))
    tf += [tuple(reversed(range(24))),tuple((len(rings)-1)*24+j for j in range(24))]
    ob=mesh(name,tv,tf,teeth)
    m=ob.modifiers.new('Rounded pointed tooth','SUBSURF')
    m.levels=2
    apply(ob,m)


for i,x in enumerate([-.286,-.204,-.108,0,.108,.204,.286]):
    u=x/WIDTH
    z=bottom(u)-.012
    h=(top(u)-bottom(u))*(.76 if abs(u)<.8 else .7)
    pointed_tooth('Tooth_Lower_'+str(i),x,z,z+h,.094 if abs(u)<.7 else .072)
for i,x in enumerate([-.31,-.246,-.155,-.054,.054,.155,.246,.31]):
    u=x/WIDTH
    z=top(u)+.010
    h=(top(u)-bottom(u))*.42
    pointed_tooth('Tooth_Upper_'+str(i),x,z,z-h,.060 if abs(u)<.7 else .045)

# One centered globe and a skin cap; all eye markings follow the sphere surface.
CX,CY,CZ=0,-.307,1.234
RX,RY,RZ=.218,.151,.214
ball('Eye_Center',(CX,CY,CZ),(RX,RY,RZ),white,segments=64,rings=40)
cutoff=-.008/RZ
lat0=math.asin(cutoff)
ev=[]
ROWS,COLS=28,80
for row in range(ROWS+1):
    lat=lat0+(math.pi/2-lat0)*row/ROWS
    for col in range(COLS):
        lon=2*math.pi*col/COLS
        ev.append((CX+(RX+.007)*math.cos(lat)*math.cos(lon),CY+(RY+.007)*math.cos(lat)*math.sin(lon),CZ+(RZ+.007)*math.sin(lat)))
ef=[]
for row in range(ROWS):
    for col in range(COLS):
        ef.append((row*COLS+col,row*COLS+(col+1)%COLS,(row+1)*COLS+(col+1)%COLS,(row+1)*COLS+col))
lid=mesh('Upper_Lid_Center',ev,ef,skin)
lid.shape_key_add(name='Basis')
blink=lid.shape_key_add(name='Blink')
blink.value=0.0
for idx,v in enumerate(blink.data):
    row,col=divmod(idx,COLS)
    lat=-math.pi/2+math.pi*row/ROWS
    lon=2*math.pi*col/COLS
    v.co=(CX+(RX+.007)*math.cos(lat)*math.cos(lon),CY+(RY+.007)*math.cos(lat)*math.sin(lon),CZ+(RZ+.007)*math.sin(lat))
for name,rx,rz,offset,mat in [('Iris_Center',.087,.087,.0015,iris),('Pupil_Center',.046,.055,.0025,pupil)]:
    pv=[]
    for row in range(17):
        r=max(.0001,row/16)
        for col in range(64):
            a=2*math.pi*col/64
            x=rx*r*math.cos(a)
            z=1.185+rz*r*math.sin(a)
            y=CY-RY*math.sqrt(max(.001,1-(x/RX)**2-((z-CZ)/RZ)**2))-offset
            pv.append((x,y,z))
    pf=[]
    for row in range(16):
        for col in range(64):
            pf.append((row*64+col,row*64+(col+1)%64,(row+1)*64+(col+1)%64,(row+1)*64+col))
    mesh(name,pv,pf,mat)

# Ivory crescent horns open inwards; these are shorter and fuller than Riff's curled horns.
for s,side in [(-1,'L'),(1,'R')]:
    points=[(s*.328,.060,1.348),(s*.433,.065,1.43),(s*.484,.061,1.565),
            (s*.461,.026,1.711),(s*.395,-.018,1.811),(s*.307,-.041,1.843)]
    h=tube('Horn_'+side,points,[.113,.141,.131,.094,.049,.001],hornmat,sides=64,steps=12)
    m=h.modifiers.new('Horn surface subdivision','SUBSURF')
    m.levels=1
    apply(h,m)

# Five uneven upright crown spikes, with small continuation buds over the rear crown.
for i,(x,height) in enumerate([(-.14,.17),(-.076,.257),(0,.306),(.080,.249),(.143,.157)]):
    z=1.50-.2*abs(x)
    tuft=ball('Crest_'+str(i),(x,.035,z+height*.40),(.034,.039,height*.63),skin,segments=40,rings=28)
    tuft.rotation_euler[1]=x*.53
for i,(y,z) in enumerate([(.14,1.534),(.21,1.502),(.268,1.455)]):
    ball('Rear_Crest_Bud_'+str(i),(0,y,z),(.027,.031,.050-i*.007),skin,segments=24,rings=16)

# Fitting aids belong to their own collection and are excluded from all default renders.
box('Grit_Seat_Cushion',(0,.055,.146),(.72,.65,.13),.052,seatmat,guide)
seat=box('Grit_Seat_Back',(0,.33,.51),(.72,.14,.77),.06,seatmat,guide)
seat.rotation_euler.x=math.radians(8)
bpy.ops.mesh.primitive_torus_add(major_radius=.259,minor_radius=.034,major_segments=64,minor_segments=16,location=(0,-.678,.632))
wheel=move(bpy.context.object,guide)
wheel.name='Grit_Steering_Wheel_Guide'
wheel.rotation_euler.x=math.radians(52)
wheel.data.materials.append(rubber)
bpy.context.view_layer.update()
for a in (0,2*math.pi/3,4*math.pi/3):
    p=wheel.matrix_world@Vector((.236*math.cos(a),.236*math.sin(a),0))
    tube('Grit_Steering_Spoke_Guide',[(0,-.678,.632),p],[.015,.014],metal,coll=guide,steps=2)
guide.hide_render=True
guide.hide_viewport=True

for i,path in enumerate(['art-source/concepts/racers/round-02/02-grit-v2.png','art-source/concepts/racers/round-01/02-grit-v1.png']):
    im=bpy.data.images.load(str(ROOT/path))
    im.pack()
    ob=bpy.data.objects.new('Grit_Reference_'+str(i),None)
    refs.objects.link(ob)
    ob.empty_display_type='IMAGE'
    ob.data=im
    ob.empty_display_size=3
    ob.location=(3+i*3,1,1.4)
    ob.rotation_euler=(math.pi/2,0,0)
    ob.hide_render=True
refs.hide_viewport=True

# Neutral photographic studio, shared exposure across each review angle.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.075))
ground=move(bpy.context.object,studio)
ground.name='Grit_Studio_Ground'
ground.data.materials.append(material('studio ivory','EDE3D1',.75))
ground.is_shadow_catcher=True
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.85,.9,1,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
for name,pos,power,size,color in [('Key',(-3,-4,5),280,3.0,(1,.97,.91)),('Fill',(3,-2,3),100,3,(.91,.96,1)),('Rim',(1,3,4),250,3,(1,.96,.86))]:
    data=bpy.data.lights.new('Grit_'+name,'AREA')
    data.energy,data.size,data.shape,data.color=power,size,'DISK',color
    ob=bpy.data.objects.new(data.name,data)
    studio.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES'
scene.cycles.samples=args.samples
scene.cycles.use_denoising=True
scene.render.resolution_x=scene.render.resolution_y=args.resolution
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.render.film_transparent=True
tree=bpy.data.node_groups.new('Grit Studio Composite','CompositorNodeTree')
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=tree.nodes.new('CompositorNodeRLayers')
over=tree.nodes.new('CompositorNodeAlphaOver')
over.inputs['Background'].default_value=linear('F8F1E3')
tree.links.new(rl.outputs['Image'],over.inputs['Foreground'])
out=tree.nodes.new('NodeGroupOutput')
tree.links.new(over.outputs['Image'],out.inputs['Image'])
scene.compositing_node_group=tree
for name,pos,target,scale in [('hero',(3,-6,2.5),(0,-.09,1),2.16),('front',(0,-6,1.25),(0,-.08,1),2.16),
                              ('side',(6,0,1.25),(0,-.10,1),2.16),('rear',(0,6,1.35),(0,0,1),2.16),
                              ('face',(0,-6,1.30),(0,-.20,1.20),1.42)]:
    data=bpy.data.cameras.new('Grit_Camera_'+name)
    data.type='ORTHO'
    data.ortho_scale=scale
    ob=bpy.data.objects.new(data.name,data)
    studio.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['Grit_Camera_hero']
scene['asset_id']='grit-driver'
scene['concept']='art-source/concepts/racers/round-02/02-grit-v2.png'
scene['revision']=args.revision
scene['notes']='Original cyclops driver sculpt. Seat and steering guide remain separate; not included in driver renders or exports.'
select(body)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
blend=OUT/('grit-driver-v'+args.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
stats={'revision':args.revision,'meshCount':len(driver.objects),
       'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in driver.objects)}
(REVIEW/'model-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('GRIT_BUILT '+json.dumps(stats),flush=True)
for view in args.views.split(','):
    if view=='none': continue
    scene.camera=bpy.data.objects['Grit_Camera_'+view]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('GRIT_RENDER '+view,flush=True)
