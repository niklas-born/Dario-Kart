"""Build Brisk's original three-eyed, seated frost-monster driver.

Geometry helpers follow the established Grit workflow. Brisk's anatomy and
details are independently constructed from the two Brisk concept sheets.
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
parser.add_argument('--views', default='hero,front,side,rear,face')
parser.add_argument('--resolution', type=int, default=1100)
parser.add_argument('--samples', type=int, default=40)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
REV = int(args.revision)
OUT = ROOT/'art-source/blender/characters/brisk'
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


driver = collection('BRISK_DRIVER')
guide = collection('FIT_GUIDE_NOT_FOR_EXPORT')
studio = collection('STUDIO')
refs = collection('CONCEPT_REFERENCE')


def move(obj, target):
    for c in list(obj.users_collection): c.objects.unlink(obj)
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
    mat = bpy.data.materials.new('Brisk | '+name)
    mat.diffuse_color = linear(color)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = linear(color)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Subsurface Radius'].default_value = (.3,.55,.7)
    p.inputs['Specular IOR Level'].default_value = .3
    return mat


skin = material('clear glacier blue skin','079BE4',.5,sss=.025)
hornmat = material('pale ice horns','A9DCFA',.36,sss=.025)
bandmat = material('blue horn growth rings','519DD0',.44)
scalemat = material('frost scales','D0ECF8',.42,sss=.025)
bellymat = material('pale blue belly','ADDCEE',.53,sss=.025)
browmat = material('deep blue eyebrows','046CC3',.48,sss=.015)
white = material('cool eye white','EAF4EF',.3)
iris = material('blue iris','298BBE',.28)
irisrim = material('iris dark outer rim','155374',.34)
pupil = material('midnight pupil','061F2D',.22)
mouthmat = material('deep warm mouth','531B22',.64)
gum = material('warm red gums','BF4049',.5,sss=.025)
teeth = material('cool ivory teeth','FFF6E5',.32)
tongue = material('coral tongue','F17D7D',.5,sss=.04)
seatmat = material('fitting seat charcoal','343B3A',.68)
rubber = material('fitting steering grip','202725',.6)
metal = material('fitting wheel metal','848984',.35,.7)


def mesh(name, verts, faces, mat, coll=driver):
    data = bpy.data.meshes.new(name+'_Mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    coll.objects.link(obj)
    if mat: data.materials.append(mat)
    for p in data.polygons: p.use_smooth = True
    return obj


def ball(name, pos, scale, mat=skin, coll=driver, segments=40, rings=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    obj = move(bpy.context.object,coll)
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons: p.use_smooth = True
    return obj


def box(name, pos, size, radius, mat, coll=driver):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    obj = move(bpy.context.object,coll)
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new('Rounded fitting aid','BEVEL')
    mod.width,mod.segments = radius,5
    apply(obj,mod)
    mod = obj.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    apply(obj,mod)
    for p in obj.data.polygons: p.use_smooth = True
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
        if b.length<.01: b=tangent.cross(Vector((1,0,0)))
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


# Brisk is a broad soft barrel with a round dome, low compact hips and strong arms.
profile=spline([(.202,.005,.005,.035),(.26,.26,.22,.035),(.41,.39,.30,.045),
                (.62,.448,.348,.048),(.84,.48,.354,.06),(1.03,.487,.35,.065),
                (1.20,.455,.322,.075),(1.36,.352,.264,.09),
                (1.47,.20,.167,.095),(1.515,.002,.002,.09)],10)


def section(z):
    for a,b in zip(profile,profile[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0])
            return tuple(a[k]*(1-t)+b[k]*t for k in (1,2,3))
    return tuple(profile[0 if z<.202 else -1][k] for k in (1,2,3))


def front(x,z):
    rx,ry,cy=section(z)
    f=max(.001,1-(x/max(.001,rx))**2)
    return cy-ry*math.sqrt(f)-.052*math.exp(-((z-.998)/.145)**2)*f**1.5


verts=[]
N=112
for z,rx,ry,cy in profile:
    for j in range(N):
        a=2*math.pi*j/N
        x,y=rx*math.cos(a),cy+ry*math.sin(a)
        if math.sin(a)<0: y-=.052*math.exp(-((z-.998)/.145)**2)*(-math.sin(a))**3
        verts.append((x,y,z))
faces=[]
for i in range(len(profile)-1):
    for j in range(N):
        faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
faces += [tuple(reversed(range(N))),tuple((len(profile)-1)*N+j for j in range(N))]
body=mesh('Brisk_Skin',verts,faces,skin)
parts=[body]
for s,side in [(-1,'L'),(1,'R')]:
    parts.append(tube('Arm_'+side,[(s*.335,.04,.975),(s*.448,-.045,.843),
                      (s*.471,-.239,.686),(s*.407,-.427,.676),(s*.282,-.591,.741)],
                      [.126,.137,.128,.12,.095]))
    parts.append(ball('Palm_'+side,(s*.294,-.615,.744),(.104,.084,.081)))
    fingers=[([(.235,-.627,.782),(.237,-.700,.780),(.242,-.736,.749),(.249,-.720,.706)],.040),
             ([(.302,-.625,.773),(.305,-.704,.766),(.311,-.742,.734),(.314,-.720,.691)],.042),
             ([(.362,-.611,.751),(.371,-.683,.746),(.369,-.718,.713),(.357,-.699,.678)],.037)]
    for i,(path,radius) in enumerate(fingers):
        points=[(s*x,y,z) for x,y,z in path]
        parts.append(tube('Curled_Finger_'+side+str(i),points,[radius*.94,radius,radius*.96,radius*.83],steps=10))
        parts.append(ball('Finger_Tip_'+side+str(i),points[-1],(radius*.83,)*3,segments=24,rings=16))
    thumbpath=[(s*.230,-.591,.782),(s*.181,-.648,.800),(s*.170,-.708,.776),(s*.205,-.738,.742)]
    parts.append(tube('Thumb_'+side,thumbpath,[.048,.045,.040,.031]))
    parts.append(ball('Thumb_Tip_'+side,thumbpath[-1],(.031,)*3,segments=24,rings=16))
    parts.append(ball('Thigh_'+side,(s*.205,-.164,.275),(.172,.267,.15)))
    parts.append(ball('Foot_'+side,(s*.205,-.436,.194),(.144,.224,.106)))
    for i in range(3):
        parts.append(ball('Toe_'+side+str(i),(s*(.13+i*.073),-.584,.191),(.047,.074,.063),segments=24,rings=16))
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
mod=body.modifiers.new('Fuse original seated anatomy','REMESH')
mod.mode='VOXEL'
mod.voxel_size=.0048
mod.use_smooth_shade=True
apply(body,mod)
mod=body.modifiers.new('Relax anatomical joins','SMOOTH')
mod.factor,mod.iterations=.65,10
apply(body,mod)

# The wide grin is an opening in the body, with separate recessed mouth geometry.
WIDTH=.345
def top(u): return .982+.067*u*u+.007*math.sqrt(max(0,1-u*u))
def bottom(u): return .835+.214*u*u-.004*math.sqrt(max(0,1-u*u))
outline=[(WIDTH*(-1+2*i/64),top(-1+2*i/64)) for i in range(65)]
outline += [(WIDTH*(-1+2*i/64),bottom(-1+2*i/64)) for i in range(63,0,-1)]
n=len(outline)
cut=mesh('Smile_cutter',[(x,y,z) for y in (-.9,-.055) for x,z in outline],
         [tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],None)
mod=body.modifiers.new('Broad smile cavity','BOOLEAN')
mod.operation,mod.solver,mod.object='DIFFERENCE','EXACT',cut
apply(body,mod)
bpy.data.objects.remove(cut,do_unlink=True)
mesh('Mouth_Cavity',[(0,-.054,.94)]+[(x,front(x,z)+(.070 if REV>=2 else .012),z) for x,z in outline],
     [(0,i+1,(i+1)%n+1) for i in range(n)],mouthmat)
lip_parts=[body]
for name,fn in [('Upper_Lip',top),('Lower_Lip',bottom)]:
    points=[]
    for i in range(41):
        u=-.98+1.96*i/40
        x,z=WIDTH*u,fn(u)
        points.append((x,front(x,z)+(.007 if REV>=2 else -.003),z))
    lip_parts.append(tube(name,points,[.014 if REV>=2 else .016]*41,steps=2))
    tube(name.replace('Lip','Gum'),[(x,y+.034,z+(-.009 if name.startswith('Upper') else .009)) for x,y,z in points],
         [.012]*len(points),gum,steps=2,sides=16)
for s in (-1,1):
    x,z=s*.335,1.04
    lip_parts.append(ball('Smile_Corner',(x,front(x,z)+(.013 if REV>=2 else .002),z),(.024,.022,.025),segments=28,rings=18))
bpy.ops.object.select_all(action='DESELECT')
for ob in lip_parts: ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
mod=body.modifiers.new('Blend soft lips and cheeks','REMESH')
mod.mode='VOXEL'
mod.voxel_size=.0042
mod.use_smooth_shade=True
apply(body,mod)
mod=body.modifiers.new('Relax soft smile','SMOOTH')
mod.factor,mod.iterations=.55,5
apply(body,mod)
mod=body.modifiers.new('Working sculpt density','DECIMATE')
mod.ratio=.45
apply(body,mod)
for p in body.data.polygons: p.use_smooth=True
ball('Tongue',(0,-.202 if REV>=2 else -.256,.852),(.115,.041 if REV>=2 else .055,.019 if REV>=2 else .025),tongue)


def pointed_tooth(name, x, base, tip, width):
    rings=[(0,width*.47,.021),(.12,width*.50,.025),(.47,width*.34,.020),(.80,width*.13,.011),(1,.001,.001)]
    tv=[]
    for t,rx,ry in rings:
        for j in range(24):
            a=2*math.pi*j/24
            vx=x+rx*math.cos(a)
            gum_curve=bottom if tip>base else top
            curved_base=base+gum_curve(vx/WIDTH)-gum_curve(x/WIDTH)
            z=curved_base*(1-t)+tip*t
            inset=(.025+.025*(1-t)**3) if REV>=2 else .046
            tv.append((vx,front(vx,z)+inset+ry*math.sin(a),z))
    tf=[]
    for i in range(len(rings)-1):
        for j in range(24): tf.append((i*24+j,i*24+(j+1)%24,(i+1)*24+(j+1)%24,(i+1)*24+j))
    tf += [tuple(reversed(range(24))),tuple((len(rings)-1)*24+j for j in range(24))]
    if REV>=2 and tip<base: tf=[tuple(reversed(f)) for f in tf]
    ob=mesh(name,tv,tf,teeth)
    m=ob.modifiers.new('Rounded pointed tooth','SUBSURF')
    m.levels=2
    apply(ob,m)


for i,x in enumerate([-.286,-.215,-.131,-.044,.044,.131,.215,.286]):
    u=x/WIDTH
    z=top(u)+.009
    h=(top(u)-bottom(u))*((.50 if abs(u)<.65 else .73) if REV>=2 else (.42 if abs(u)<.65 else .62))
    pointed_tooth('Tooth_Upper_'+str(i),x,z,z-h,.086 if abs(u)<.7 else .060)
for i,x in enumerate([-.267,-.176,-.087,0,.087,.176,.267]):
    u=x/WIDTH
    z=bottom(u)-.01
    h=(top(u)-bottom(u))*((.58 if abs(u)<.7 else .77) if REV>=2 else (.32 if abs(u)<.7 else .53))
    pointed_tooth('Tooth_Lower_'+str(i),x,z,z+h,.100 if abs(u)<.7 else .075)

# All three blue eyes have their own half lid and independently editable blink.
def eye(side,CX,CY,CZ,RX,RY,RZ):
    ball('Eye_'+side,(CX,CY,CZ),(RX,RY,RZ),white,segments=56,rings=36)
    lat0=math.asin(-.018/RZ if side!='Center' else -.002/RZ)
    ev=[]
    rows,cols=22,64
    for row in range(rows+1):
        lat=lat0+(math.pi/2-lat0)*row/rows
        for col in range(cols):
            lon=2*math.pi*col/cols
            ev.append((CX+(RX+.005)*math.cos(lat)*math.cos(lon),CY+(RY+.005)*math.cos(lat)*math.sin(lon),CZ+(RZ+.005)*math.sin(lat)))
    ef=[]
    for row in range(rows):
        for col in range(cols): ef.append((row*cols+col,row*cols+(col+1)%cols,(row+1)*cols+(col+1)%cols,(row+1)*cols+col))
    lid=mesh('Upper_Lid_'+side,ev,ef,skin)
    lid.shape_key_add(name='Basis')
    blink=lid.shape_key_add(name='Blink')
    blink.value=0
    for idx,v in enumerate(blink.data):
        row,col=divmod(idx,cols)
        lat=-math.pi/2+math.pi*row/rows
        lon=2*math.pi*col/cols
        v.co=(CX+(RX+.005)*math.cos(lat)*math.cos(lon),CY+(RY+.005)*math.cos(lat)*math.sin(lon),CZ+(RZ+.005)*math.sin(lat))
    gaze_x=CX+(.007 if side=='L' else -.007 if side=='R' else 0)
    gaze_z=CZ-RZ*.22
    def patch(name,px,pz,rx,rz,offset,mat):
        pv=[]
        for row in range(13):
            r=max(.0001,row/12)
            for col in range(48):
                a=2*math.pi*col/48
                x,z=px+rx*r*math.cos(a),pz+rz*r*math.sin(a)
                y=CY-RY*math.sqrt(max(.001,1-((x-CX)/RX)**2-((z-CZ)/RZ)**2))-offset
                pv.append((x,y,z))
        pf=[]
        for row in range(12):
            for col in range(48): pf.append((row*48+col,row*48+(col+1)%48,(row+1)*48+(col+1)%48,(row+1)*48+col))
        if REV>=2: pf=[tuple(reversed(f)) for f in pf]
        return mesh(name+'_'+side,pv,pf,mat)
    patch('Iris_Rim',gaze_x,gaze_z,RX*.45,RZ*.46,.001,irisrim)
    patch('Iris',gaze_x,gaze_z,RX*.403,RZ*.42,.0017,iris)
    patch('Pupil',gaze_x,gaze_z,RX*.245,RZ*.33,.0024,pupil)
    patch('Eye_Catchlight',gaze_x-RX*.10,gaze_z+RZ*.13,RX*.057,RZ*.069,.0031,white)


eye('L',-.148,-.273,1.185,.148,.126,.133)
eye('R',.148,-.273,1.185,.148,.126,.133)
eye('Center',0,-.328,1.074,.070,.065,.054)
for s,side in [(-1,'L'),(1,'R')]:
    if REV>=2:
        tube('Eyebrow_'+side,[(s*.044,-.222,1.343),(s*.071,-.235,1.353),
                              (s*.13,-.237,1.36),(s*.194,-.22,1.35),
                              (s*.231,-.201,1.337),(s*.244,-.192,1.330)],
                              [.001,.025,.033,.028,.018,.001],browmat,sides=32,steps=10)
    else:
        tube('Eyebrow_'+side,[(s*.060,-.229,1.347),(s*.12,-.241,1.36),
                              (s*.20,-.223,1.351),(s*.237,-.202,1.335)],
                              [.019,.034,.030,.010],browmat,sides=28,steps=10)

# A close-fitting pale oval follows the belly instead of floating in front of it.
bv=[]
rows,cols=25,96
for row in range(rows+1):
    r=max(.0001,row/rows)
    for j in range(cols):
        a=2*math.pi*j/cols
        x=.248*r*math.cos(a)
        z=.556+.240*r*math.sin(a)
        bv.append((x,front(x,z)-.005-.011*(1-r*r),z))
bf=[]
for row in range(rows):
    for j in range(cols): bf.append((row*cols+j,row*cols+(j+1)%cols,(row+1)*cols+(j+1)%cols,(row+1)*cols+j))
if REV>=2:
    # A real center vertex and triangle fan remove the tiny open radial seam.
    bv=bv[cols:]
    bf=[tuple(i-cols for i in f) for f in bf[cols:]]
    center=len(bv)
    bv.append((0,front(0,.556)-.016,.556))
    bf += [(center,(j+1)%cols,j) for j in range(cols)]
    bf=[tuple(reversed(f)) for f in bf]
belly=mesh('Belly_Patch',bv,bf,bellymat)
mod=belly.modifiers.new('Thin soft belly edge','SOLIDIFY')
mod.thickness=.005
apply(belly,mod)


def horn(name,points,radii,bands=True):
    h=tube('Horn_'+name,points,radii,hornmat,sides=48,steps=12)
    m=h.modifiers.new('Round ice horn surface','SUBSURF')
    m.levels=1
    apply(h,m)
    if bands:
        centerline=spline([tuple(p)+(r,) for p,r in zip(points,radii)],12)
        for i,t in enumerate((.27,.51,.73)):
            at=round(t*(len(centerline)-1))
            p=centerline[at]
            tangent=Vector(centerline[at+1][:3])-Vector(centerline[at-1][:3])
            bpy.ops.mesh.primitive_torus_add(major_radius=p[3],minor_radius=.0026,
                major_segments=48,minor_segments=8,location=p[:3])
            ob=move(bpy.context.object,driver)
            ob.name='Horn_Band_'+name+'_'+str(i)
            ob.rotation_euler=tangent.to_track_quat('Z','Y').to_euler()
            ob.data.materials.append(bandmat)
            for f in ob.data.polygons: f.use_smooth=True
    return h


# Consistent seven-horn front silhouette: five upright crown horns and two side horns.
horn('Crown_Center',[(0,.034,1.47),(0,.043,1.57),(0,.058,1.70),(0,.08,1.823)],
     [.086,.072,.041,.001])
for s,side in [(-1,'L'),(1,'R')]:
    horn('Crown_Inner_'+side,[(s*.192,.057,1.435),(s*.217,.073,1.533),(s*.247,.085,1.637),(s*.252,.098,1.716)],
         [.077,.063,.038,.001])
    horn('Crown_Outer_'+side,[(s*.333,.069,1.348),(s*.391,.083,1.448),(s*.433,.091,1.572),(s*.431,.109,1.662)],
         [.092,.076,.043,.001])
    horn('Side_'+side,[(s*.436,.077,1.119),(s*.522,.07,1.159),(s*.611,.073,1.22),(s*.669,.079,1.291)],
         [.084,.071,.04,.001])
# Smaller pale spikes descend the back, separate from the five front crown points.
for i,(y,z,length) in enumerate([(.245,1.46,.17),(.345,1.32,.18),(.414,1.15,.145)]):
    horn('Rear_'+str(i),[(0,y-.025,z-.035),(0,y+.019,z+.016),(0,y+length*.68,z+length*.62),(0,y+length,z+length*.90)],
         [.074-i*.008,.065-i*.008,.030-i*.004,.001],bands=False)

# Raised frost scales are arranged in deliberate temple and upper-back clusters.
temple=[(.302,1.357,.012,.009),(.341,1.326,.015,.010),(.372,1.285,.016,.011),
        (.315,1.294,.014,.011),(.344,1.255,.017,.012),(.386,1.235,.015,.012),
        (.319,1.237,.017,.013),(.362,1.197,.018,.012),(.396,1.18,.016,.012),
        (.337,1.176,.014,.011),(.374,1.139,.017,.011),(.399,1.105,.014,.010),
        (.271,1.387,.010,.007),(.281,1.33,.010,.008)]
for s,side in [(-1,'L'),(1,'R')]:
    for i,(x,z,rx,rz) in enumerate(temple):
        x*=s
        y=front(x,z)
        dx=.002
        dz=.002
        normal=Vector(((front(x+dx,z)-front(x-dx,z))/(2*dx),-1,
                       (front(x,z+dz)-front(x,z-dz))/(2*dz))).normalized()
        ob=ball('Scale_Temple_'+side+str(i),Vector((x,y,z))+normal*.003,(rx,rz,.0048),scalemat,segments=24,rings=16)
        ob.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    for i,(angle,z,rx,rz) in enumerate([(1.02,1.36,.017,.011),(1.15,1.32,.019,.013),
        (.9,1.30,.017,.012),(1.0,1.245,.019,.013),(1.21,1.255,.016,.013),
        (.83,1.22,.018,.012),(1.10,1.18,.017,.014),(.92,1.16,.016,.012),
        (1.02,1.10,.013,.012),(.72,1.28,.013,.010),(1.32,1.37,.015,.010)]):
        rxbody,rybody,cy=section(z)
        x,y=s*rxbody*math.sin(angle),cy+rybody*math.cos(angle)
        normal=Vector((s*math.sin(angle)/rxbody,math.cos(angle)/rybody,.65)).normalized()
        ob=ball('Scale_Back_'+side+str(i),Vector((x,y,z))+normal*.002,(rx,rz,.005),scalemat,segments=24,rings=16)
        ob.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    for i,(x,z) in enumerate([(.296,.711),(.316,.682),(.326,.722)]):
        x*=s
        ob=ball('Scale_Belly_'+side+str(i),(x,front(x,z)-.002,z),(.008,.004,.014),scalemat,segments=20,rings=12)

# Seat and steering wheel are independent fitting aids, never part of the driver.
box('Brisk_Seat_Cushion',(0,.055,.146),(.75,.66,.13),.052,seatmat,guide)
seat=box('Brisk_Seat_Back',(0,.358,.51),(.77,.14,.77),.06,seatmat,guide)
seat.rotation_euler.x=math.radians(8)
bpy.ops.mesh.primitive_torus_add(major_radius=.259,minor_radius=.034,major_segments=64,minor_segments=16,location=(0,-.678,.632))
wheel=move(bpy.context.object,guide)
wheel.name='Brisk_Steering_Wheel_Guide'
wheel.rotation_euler.x=math.radians(52)
wheel.data.materials.append(rubber)
bpy.context.view_layer.update()
for a in (0,2*math.pi/3,4*math.pi/3):
    p=wheel.matrix_world@Vector((.236*math.cos(a),.236*math.sin(a),0))
    tube('Brisk_Steering_Spoke_Guide',[(0,-.678,.632),p],[.015,.014],metal,coll=guide,steps=2)
guide.hide_render=True
guide.hide_viewport=True
for i,path in enumerate(['art-source/concepts/racers/round-02/03-brisk-v2.png','art-source/concepts/racers/round-01/03-brisk-v1.png']):
    im=bpy.data.images.load(str(ROOT/path))
    im.pack()
    ob=bpy.data.objects.new('Brisk_Reference_'+str(i),None)
    refs.objects.link(ob)
    ob.empty_display_type='IMAGE'
    ob.data=im
    ob.empty_display_size=3
    ob.location=(3+i*3,1,1.4)
    ob.rotation_euler=(math.pi/2,0,0)
    ob.hide_render=True
refs.hide_viewport=True

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.075))
ground=move(bpy.context.object,studio)
ground.name='Brisk_Studio_Ground'
ground.data.materials.append(material('studio ivory','EDE3D1',.75))
ground.is_shadow_catcher=True
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.85,.9,1,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
for name,pos,power,size,color in [('Key',(-3,-4,5),215,3.0,(1,.97,.91)),('Fill',(3,-2,3),85,3,(.91,.96,1)),('Rim',(1,3,4),150,3,(1,.96,.86))]:
    data=bpy.data.lights.new('Brisk_'+name,'AREA')
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
tree=bpy.data.node_groups.new('Brisk Studio Composite','CompositorNodeTree')
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=tree.nodes.new('CompositorNodeRLayers')
over=tree.nodes.new('CompositorNodeAlphaOver')
over.inputs['Background'].default_value=linear('F8F1E3')
tree.links.new(rl.outputs['Image'],over.inputs['Foreground'])
out=tree.nodes.new('NodeGroupOutput')
tree.links.new(over.outputs['Image'],out.inputs['Image'])
scene.compositing_node_group=tree
for name,pos,target,scale in [('hero',(3,-6,2.5),(0,-.09,.965),2.08),('front',(0,-6,1.23),(0,-.08,.965),2.08),
                              ('side',(6,0,1.23),(0,-.10,.965),2.08),('rear',(0,6,1.3),(0,.06,.965),2.08),
                              ('face',(0,-6,1.28),(0,-.20,1.18),1.52)]:
    data=bpy.data.cameras.new('Brisk_Camera_'+name)
    data.type='ORTHO'
    data.ortho_scale=scale
    ob=bpy.data.objects.new(data.name,data)
    studio.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['Brisk_Camera_hero']
scene['asset_id']='brisk-driver'
scene['concept']='art-source/concepts/racers/round-02/03-brisk-v2.png'
scene['revision']=args.revision
scene['notes']='Original seated three-eye ice monster. Separate fitting guides; lower legs are inferred from cockpit-hidden anatomy.'
select(body)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
blend=OUT/('brisk-driver-v'+args.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
stats={'revision':args.revision,'meshCount':len(driver.objects),
       'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in driver.objects),
       'eyes':3,'frontCrownHorns':5,'sideHorns':2,'rearSpikes':3}
(REVIEW/'model-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('BRISK_BUILT '+json.dumps(stats),flush=True)
for view in args.views.split(','):
    if view=='none': continue
    guide.hide_render=(view!='fit')
    scene.camera=bpy.data.objects['Brisk_Camera_'+('hero' if view=='fit' else view)]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('BRISK_RENDER '+view,flush=True)
