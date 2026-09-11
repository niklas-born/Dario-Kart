"""Reproducible item geometry from the supplied eight-item concept sheet.

Run in Blender background mode, -- --item comet-core --revision 01.
Review each revision before using --final to package exchange assets.
"""
import argparse
import hashlib
import json
import math
from math import sin, cos, pi
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
P = argparse.ArgumentParser()
P.add_argument('--item', required=True)
P.add_argument('--revision', default='01')
P.add_argument('--resolution', type=int, default=850)
P.add_argument('--samples', type=int, default=32)
P.add_argument('--views', default='hero')
P.add_argument('--final', action='store_true')
P.add_argument('--package-only', action='store_true')
P.add_argument('--review-only', action='store_true')
A = P.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT = ROOT/'art-source/blender/items'/A.item
REVIEW = OUT/'review'/('v'+A.revision)
REVIEW.mkdir(parents=True, exist_ok=True)
random.seed(41)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 1
S.view_settings.view_transform='Standard'
S.view_settings.look='None'
S.view_settings.exposure=-1

def coll(name):
    c=bpy.data.collections.new(name); S.collection.children.link(c); return c
BODY=coll('EXPORT')
FX=coll('EFFECTS')
STUDIO=coll('STUDIO')

def move(o,c=BODY):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)
    return o

def select(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active=o

def apply(o,m):
    select(o); bpy.ops.object.modifier_apply(modifier=m.name)

def color(s):
    v=[int(s[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)+(1,)

def mat(name,hex,rough=.35,metal=0,emission=0,trans=0):
    m=bpy.data.materials.new(name); m.diffuse_color=color(hex); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=color(hex)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    p.inputs['Emission Color'].default_value=color(hex)
    p.inputs['Emission Strength'].default_value=emission
    p.inputs['Transmission Weight'].default_value=trans
    p.inputs['Coat Weight'].default_value=.2
    return m

def finish(o,name,m,c=BODY,smooth=True):
    move(o,c); o.name=name
    if m:o.data.materials.append(m)
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=smooth
    return o

def mesh(name,v,f,m,c=BODY,smooth=True):
    d=bpy.data.meshes.new(name); d.from_pydata(v,[],f); d.update()
    o=bpy.data.objects.new(name,d); c.objects.link(o)
    if m:d.materials.append(m)
    for p in d.polygons:p.use_smooth=smooth
    return o

def bevel(o,width=.02,segments=3):
    m=o.modifiers.new('Soft manufactured edges','BEVEL'); m.width=width; m.segments=segments; apply(o,m)
    m=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); apply(o,m)
    return o

def ball(name,loc,scale,m,c=BODY,seg=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=finish(bpy.context.object,name,m,c); o.scale=scale
    select(o); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def ico(name,loc,r,m,c=BODY,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc)
    return finish(bpy.context.object,name,m,c,False)

def box(name,loc,size,m,r=.02):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=finish(bpy.context.object,name,m); o.scale=size
    select(o); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return bevel(o,r)

def cyl(name,loc,r,depth,m,r2=None,verts=48,edge=.015):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r if r2 is None else r2,depth=depth,location=loc)
    o=finish(bpy.context.object,name,m)
    if edge:bevel(o,edge,3)
    return o

def torus(name,loc,r,minor,m,rot=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=64,minor_segments=10,location=loc)
    o=finish(bpy.context.object,name,m)
    if rot:o.rotation_euler=rot
    return o

def tube(name,points,r,m,c=BODY,cyclic=False,res=3):
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.resolution_u=8
    d.bevel_depth=r; d.bevel_resolution=res
    p=d.splines.new('POLY');p.points.add(len(points)-1)
    for v,pt in zip(p.points,points):v.co=(*pt,1)
    p.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,d);c.objects.link(o);d.materials.append(m)
    select(o);bpy.ops.object.convert(target='MESH')
    return bpy.context.object

def polygon(name,pts,depth,m,axis='Y',bevelwidth=.01):
    # points are (x,z); front is -Y
    v=[(x,y,z) for y in (-depth/2,depth/2) for x,z in pts]
    n=len(pts);f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,v,f,m,smooth=False)
    if bevelwidth:bevel(o,bevelwidth,3)
    return o

def transform(objects,rotation=(0,0,0),offset=(0,0,0),pivot=(0,0,0)):
    from mathutils import Euler
    M=Matrix.Translation(Vector(offset)+Vector(pivot)) @ Euler(rotation).to_matrix().to_4x4() @ Matrix.Translation(-Vector(pivot))
    for o in objects:o.matrix_world=M@o.matrix_world

def rounded_square(name,half,y,width,m):
    rad=.12;pts=[]
    for cx,cz,start in [(half-rad,half-rad,0),(-half+rad,half-rad,90),(-half+rad,-half+rad,180),(half-rad,-half+rad,270)]:
        for j in range(9):
            a=math.radians(start+j*90/8);pts.append((cx+rad*cos(a),y,cz+rad*sin(a)))
    # square-section band, not a wire cage
    v=[]
    for i,p in enumerate(pts):
        t=(Vector(pts[(i+1)%len(pts)])-Vector(pts[i-1])).normalized()
        n=Vector((t.z,0,-t.x))
        for w,d in [(-1,-1),(1,-1),(1,1),(-1,1)]:v.append(Vector(p)+n*w*width/2+Vector((0,d*.033,0)))
    f=[]
    for i in range(len(pts)):
        for j in range(4):f.append((4*i+j,4*i+(j+1)%4,4*((i+1)%len(pts))+(j+1)%4,4*((i+1)%len(pts))+j))
    return bevel(mesh(name,v,f,m),.018,3)

def comet():
    metal=mat('Cage | warm gunmetal','716977',.3,.7)
    edge=mat('Cage | silver rivets','C7B5AF',.23,.8)
    lava=mat('Core | golden molten fissures','FF7900',.28,0,5)
    rocks=[mat('Core | basalt '+str(i),h,.5,.08) for i,h in enumerate((['AD4112','C24D0E','D85B0B','E67C0F','93320C'] if int(A.revision)==1 else ['852603','A03502','B34502','C05802','64200A']))]
    spark=mat('VFX | hot gold','FFE55A',.3,0,7)
    ico('Molten core', (0,0,0),.49,lava,sub=4)
    # Dual cells of an icosphere form broad irregular lava plates, with real gaps.
    seed=ico('temporary cell scaffold',(0,0,0),1,None,sub=2)
    if int(A.revision)>1:
        for v in seed.data.vertices:v.co=(v.co+Vector(tuple(random.uniform(-.13,.13) for _ in range(3)))).normalized()
        seed.data.update()
    centers=[p.center.normalized() for p in seed.data.polygons]
    for vi,vert in enumerate(seed.data.vertices):
        normal=vert.co.normalized();adj=[centers[p.index] for p in seed.data.polygons if vi in p.vertices]
        tangent=normal.cross(Vector((0,0,1)))
        if tangent.length<.01:tangent=normal.cross(Vector((0,1,0)))
        tangent.normalize();b=normal.cross(tangent)
        adj.sort(key=lambda p:math.atan2(p.dot(b),p.dot(tangent)))
        shrink=(.875 if int(A.revision)>2 else .91) if int(A.revision)>1 else .82
        ring=[(normal+(p-normal)*shrink).normalized() for p in adj]
        height=random.uniform(.507,.543)
        v=[p*.49 for p in ring]+[p*height for p in ring]+[normal*(height+.022)]
        n=len(ring);f=[]
        for i in range(n):f.extend([(i,(i+1)%n,(i+1)%n+n,i+n),(i+n,(i+1)%n+n,2*n)])
        f.append(tuple(reversed(range(n))))
        bevel(mesh('Basalt plate %02d'%vi,v,f,random.choice(rocks),smooth=False),.008,2)
    bpy.data.objects.remove(seed,do_unlink=True)
    for y in [-.37,.37]:rounded_square('Forged square band',.48,y,.095,metal)
    for x in [-.44,.44]:
        for z in [-.44,.44]:
            box('Cage bridge',(x,0,z),(.10,.76,.10),metal,.025)
            for y in [-.412,.412]:
                o=cyl('Rounded cage rivet',(x,y,z),.034,.018,edge,verts=16,edge=.007);o.rotation_euler[0]=pi/2
    transform(list(BODY.objects),(.13,-.32,-.12),(0,0,.9))
    for i in range(11):
        a=2*pi*i/11+.1;r=random.uniform(.7,.86)
        o=ico('Orbiting basalt %02d'%i,(r*cos(a),random.uniform(-.1,.2),.9+r*sin(a)),random.uniform(.04,.1),random.choice(rocks),FX,2)
        o.rotation_euler=(random.random(),random.random(),random.random())
    for i in range(12):
        a=2*pi*i/12+.28;r=random.uniform(.65,.97)
        p=Vector((r*cos(a),-.05,.9+r*sin(a)))
        o=ball('Gold ember',p,(.009,.009,random.uniform(.024,.062)),spark,FX,12,8)
        o.rotation_euler[1]=pi/2-a
    if int(A.revision)>2:
        for i in range(10):
            a=2*pi*i/10+.3
            r=.5;direction=Vector((cos(a),0,sin(a)));side=Vector((-sin(a),0,cos(a)))
            base=Vector((r*cos(a),-.1,.9+r*sin(a)))
            tip=base+direction*random.uniform(.16,.28)+side*.035
            mesh('Molten flame lick',[base-side*.038,base+side*.038,tip,base+Vector((0,.035,0))],[(0,1,2),(0,3,2),(1,2,3),(0,3,1)],lava,FX,False)
    return (.0,0,.9),2.2

def hazard_base(radius=.32,z=.12):
    dark=mat('Base | charcoal rubber','282934',.42,.15)
    yellow=mat('Base | safety yellow','FFBD08',.32,.25)
    steel=mat('Base | rim steel','575263',.3,.65)
    cyl('Heavy rubber foot',(0,0,z-.05),radius,.12,dark,edge=.035)
    cyl('Hazard drum',(0,0,z+.03),radius*.94,.13,dark,edge=.012)
    for i in range(8):
        a=i*2*pi/8
        pts=[]
        for zz,shift in [(z-.025,0),(z+.09,.18)]:
            for j in range(7):
                ang=a+shift+j*.40/6;pts.append((radius*.948*cos(ang),radius*.948*sin(ang),zz))
        mesh('Diagonal yellow caution stripe',pts,[(j,j+1,8+j,7+j) for j in range(6)],yellow)
    cyl('Upper metal collar',(0,0,z+.11),radius*.9,.035,steel,edge=.008)
    return dark,steel

def leaf(name,start,end,width,m,vein):
    start,end=Vector(start),Vector(end);direction=end-start
    side=direction.cross(Vector((0,-1,.3))).normalized()
    verts=[];center=[]
    for j in range(17):
        t=j/16;p=start+direction*t+Vector((0,-.05,.12*sin(pi*t)))
        center.append(p+Vector((0,-.012,.012)))
        w=width*sin(pi*t)**.85
        for u in [-1,0,1]:verts.append(p+side*w*u+Vector((0,.045*u*u*sin(pi*t),-.04*u*u*sin(pi*t))))
    f=[]
    for j in range(16):
        for k in range(2):f.append((j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k))
    o=mesh(name,verts,f,m)
    mod=o.modifiers.new('Leaf thickness','SOLIDIFY');mod.thickness=.013;apply(o,mod)
    tube(name+' central vein',center,.009,vein,res=2)
    return o

def jaw(name,center,rx,ry,depth,outer,inner,lip,rotation=0):
    before=set(BODY.objects)
    # Concentric cup, with a fully modeled interior and soft closed center.
    for layer,m,offset in [('shell',outer,0),('inside',inner,-.014 if depth>0 else .014)]:
        verts=[(0,0,depth+offset)];n=48
        for j in range(1,13):
            t=j/12
            for i in range(n):
                a=2*pi*i/n;verts.append((rx*t*cos(a),ry*t*sin(a),depth*(1-t*t)**.6+offset))
        f=[(0,1+i,1+(i+1)%n) for i in range(n)]
        for j in range(11):
            for i in range(n):f.append((1+j*n+i,1+j*n+(i+1)%n,1+(j+1)*n+(i+1)%n,1+(j+1)*n+i))
        o=mesh(name+' '+layer,verts,f,m)
        if layer=='inside':
            # Interior stays a little smaller to leave the exterior visible.
            o.scale=(.96,.96,1)
    tube(name+' thick red lip',[(rx*cos(2*pi*i/64),ry*sin(2*pi*i/64),0) for i in range(64)],.055,lip,cyclic=True,res=4)
    teeth=mat(name+' | warm ivory teeth','FFF0C8',.28)
    # Five widely spaced front fangs plus two smaller rear teeth.
    for i,a in enumerate([pi*1.02,pi*1.18,pi*1.36,pi*1.57,pi*1.77,pi*1.94,.42]):
        x=rx*.82*cos(a);y=ry*.80*sin(a)
        length=(.18 if i%2 else .22) if int(A.revision)==1 else (.24 if i%2 else .26)
        sign=-1 if depth>0 else 1
        points=[Vector((x,y,0)),Vector((x*.98,y-.025,sign*length*.5)),Vector((x*.87,y-.02,sign*length))]
        verts=[];sides=12
        for pt,r in zip(points,[.068,.048,.002]):
            for k in range(sides):verts.append(pt+Vector((r*cos(k*2*pi/sides),r*sin(k*2*pi/sides),0)))
        f=[]
        for j in range(2):
            for k in range(sides):f.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
        f.extend([tuple(reversed(range(sides))),tuple(2*sides+i for i in range(sides))])
        o=mesh(name+' fang %02d'%i,verts,f,teeth)
        mod=o.modifiers.new('Soft enamel','SUBSURF');mod.levels=1;apply(o,mod)
    objects=set(BODY.objects)-before
    transform(objects,(rotation,0,0),center)
    for o in objects:o['assembly']=name;o['hingeLocalMeters']=[0,.27,.55]

def snapt():
    dark,steel=hazard_base(.27,.1)
    green=mat('Plant | emerald foliage','338B17',.47)
    vein=mat('Plant | leaf midrib','78B42B',.48)
    red=mat('Plant | scarlet jaw','D82148',.36)
    lip=mat('Plant | fleshy lip edge','F13252',.3)
    interior=mat('Plant | deep mouth cavity','641126',.62)
    tube('Flexible plant stalk',[(0,0,.22),(0,.04,.36),(0,.06,.39)],.10,green,res=4)
    for i,(start,end,w) in enumerate([((.05,.06,.29),(.53,.1,.31),.17),((-.04,.07,.3),(-.46,.08,.25),.15),((.04,.16,.42),(.43,.32,.69),.15),((-.06,.22,.68),(-.35,.27,1.06),.10),((.12,.24,.72),(.40,.3,1.05),.11)]):
        leaf('Sculpted leaf %d'%i,start,end,w,green,vein)
    ball('Dark flexible jaw hinge',(0,.26,.55),(.13,.12,.13),dark)
    if int(A.revision)>1:ball('Deep connected mouth interior',(0,.15,.69),(.32,.17,.28),interior)
    if int(A.revision)>2:
        ball('Lower mouth floor',(0,-.04,.437),(.346,.24,.052),interior)
        tongue=mat('Plant | tongue coral','C63250',.43)
        ball('Small tongue',(0,-.11,.478),(.12,.095,.019),tongue)
    jaw('LowerJaw',(0,-.04,.47),.39,.28,-.12,red,interior,lip,0)
    jaw('UpperJaw',(0,.015,.91),.405,.29,.16,red,interior,lip,-.38 if int(A.revision)==1 else -.5)
    alarmbase=cyl('Alarm black mount',(0,.085,1.09),.115,.065,dark,edge=.013)
    alarm=mat('Alarm | candy red lens','FF1529',.2,0,.35)
    hot=mat('Alarm | golden bulb','FFCC28',.2,0,5)
    ball('Red warning dome',(0,.085,1.17),(.092,.092,.13),alarm)
    ball('Golden warning light',(0,-.001,1.185),(.043,.025,.05),hot,seg=20,rings=12)
    torus('Warning dome rim',(0,.085,1.10),.094,.012,steel)
    return (0,0,.68),1.7

def turbo():
    purple=mat('Battery | violet anodized caps','6550B0',.27,.5)
    violet=mat('Battery | purple cap inset','9F4ADB',.3,.3)
    steel=mat('Battery | dark cap seal','343849',.38,.45)
    cyan=mat('Battery | electric cyan seam','28E9FF',.2,0,2)
    glass=mat('Battery | turquoise glass','6EFADB',.16,.05,0,.92)
    if int(A.revision)>1:
        p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['IOR'].default_value=1.12;p.inputs['Coat Weight'].default_value=0;p.inputs['Specular IOR Level'].default_value=.2
    gel=mat('Battery | lime energy cell','55EF00',.3,0,.85)
    bubble=mat('Battery | charged bubbles','B5FF34',.24,0,1.6)
    yellow=mat('Battery | lightning gold','DCFF00',.25,0,.7)
    white=mat('Battery | lightning edge','F7FFB3',.23,0,3)
    cyl('Green energy reservoir',(0,0,.65),.241,.68,gel,edge=.025)
    # Open-ended, thin shell surrounding the gel. End caps close the object.
    n=64;verts=[]
    for z,r in [(.29,.262),(1.01,.262),(.29,.253),(1.01,.253)]:
        verts.extend([(r*cos(i*2*pi/n),r*sin(i*2*pi/n),z) for i in range(n)])
    faces=[]
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    mesh('Thin cyan glass shell',verts,faces,glass)
    for z in [.265,1.035]:
        cyl('Purple armored battery cap',(0,0,z),.293,.14,purple,r2=.28,verts=16,edge=.025)
        torus('Luminous cyan cap seal',(0,0,z+(.067 if z<.5 else -.067)),.268,.012,cyan)
        for i in range(8):
            a=i*2*pi/8
            o=ball('Cap screw',(cos(a)*.286,sin(a)*.286,z),(.019,.013,.019),steel,seg=12,rings=8)
            o.rotation_euler[2]=a-pi/2
    cyl('Bottom rubber terminal',(0,0,.17),.217,.06,steel,edge=.022)
    cyl('Top terminal collar',(0,0,1.135),.13,.055,steel,edge=.01)
    cyl('Purple positive terminal',(0,0,1.19),.108,.075,violet,r2=.10,edge=.015)
    torus('Terminal polished edge',(0,0,1.218),.095,.008,purple)
    pts=[(.038,.957),(-.135,.698),(-.027,.698),(-.083,.452),(.153,.761),(.034,.761)]
    bolt=polygon('Raised lightning symbol',pts,.017,yellow,bevelwidth=.008);bolt.location.y=-.273
    tube('Lightning cream outline',[(x,-.286,z) for x,z in pts],.007,white,cyclic=True,res=2)
    for i,(a,z,r) in enumerate([(-2.30,.87,.032),(-.83,.87,.038),(-2.32,.64,.022),(-.9,.58,.030),(-2.4,.44,.025),(-.62,.70,.021),(-2.2,.76,.017),(.3,.83,.033)]):
        ball('Floating energy bubble %02d'%i,(.254*cos(a),.254*sin(a),z),(r,r,r),bubble,seg=20,rings=12)
    for a in [-2.85,-.3]:
        tube('Vertical cyan glass highlight',[(.265*cos(a),.265*sin(a),z) for z in [.35,.92]],.009,cyan,res=2)
    transform(list(BODY.objects),(0,.20,-.02),pivot=(0,0,.66))
    for i,(side,z) in enumerate([(-1,.82),(-1,1.09),(1,.44),(1,.84)]):
        x=side*.41
        tube('Electric zigzag %d'%i,[(x,0,z+.07),(x+side*.035,0,z-.006),(x+side*.075,0,z+.014),(x+side*.11,0,z-.055)],.006,white,FX,res=2)
    return (0,0,.69),1.65

def orb():
    white=mat('Orb | pearl ceramic armor','D8E3E9',.29,.32)
    silver=mat('Orb | silver bezels','819DAF',.27,.65)
    seam=mat('Orb | blue recessed joints','427896',.4,.45)
    cyan=mat('Orb | cyan energy','00CFFF',.2,.15,.9)
    blue=mat('Orb | sapphire iris','0879C5',.15,.35,.3)
    irislight=mat('Orb | turquoise iris filaments','1BB4E6',.26,.25,.5)
    navy=mat('Orb | deep navy pupil','031425',.1,.15)
    glint=mat('Orb | lens catchlight','D8FFFF',.16,0,2.5)
    center=Vector((0,0,.78));r=.435
    ball('Recessed spherical chassis',center,(r-.015,)*3,seam)
    # Real spherical armor tiles and recessed seams, modeled around the eye aperture.
    bands,sectors=(5,9) if int(A.revision)<3 else (4,7)
    for j in range(bands):
        for i in range(sectors):
            gap=.022 if int(A.revision)==1 else .008
            a0=pi*j/bands+gap;a1=pi*(j+1)/bands-gap
            phase=0 if int(A.revision)<3 else .18*(j%2)
            b0=2*pi*i/sectors+gap+phase;b1=2*pi*(i+1)/sectors-gap+phase
            mid=Vector((sin((a0+a1)/2)*cos((b0+b1)/2),sin((a0+a1)/2)*sin((b0+b1)/2),cos((a0+a1)/2)))
            if int(A.revision)==1 and mid.y<-.66:continue
            verts=[];n=7
            for k in range(n):
                a=a0+(a1-a0)*k/(n-1)
                for l in range(n):
                    b=b0+(b1-b0)*l/(n-1)
                    verts.append(center+Vector((sin(a)*cos(b),sin(a)*sin(b),cos(a)))*r)
            f=[(k*n+l,k*n+l+1,(k+1)*n+l+1,(k+1)*n+l) for k in range(n-1) for l in range(n-1)]
            o=mesh('Ceramic armor panel %d-%d'%(j,i),verts,f,white)
            mod=o.modifiers.new('Armor thickness','SOLIDIFY');mod.thickness=.015;apply(o,mod)
            bevel(o,.007,2)
    eyez=.805
    eye_start=set(BODY.objects)
    ball('Eye pearl socket',(0,-.355,eyez),(.27,.10,.287),white)
    ball('Dark blue lens gasket',(0,-.461,eyez),(.243,.054,.259),seam)
    ball('Cyan outer iris',(0,-.499,eyez),(.215,.05,.235),cyan)
    ball('Deep sapphire iris',(0,-.527,eyez),(.192,.054,.211),blue)
    for i in range(32):
        a=i*2*pi/32
        pts=[(.148*cos(a),-.576,eyez+.163*sin(a)),(.177*cos(a),-.557,eyez+.195*sin(a))]
        tube('Radial iris fiber',pts,(.0032 if int(A.revision)==1 else .0014),irislight,res=1)
    ball('Glossy oval pupil',(.013,-.57,eyez),(.106,.048,.149),navy)
    ball('Large lens reflection',(-.042,-.61,eyez+.077),(.035,.014,.044),glint,seg=20,rings=12)
    ball('Small lens reflection',(.055,-.609,eyez-.045),(.014,.007,.018),glint,seg=16,rings=10)
    if int(A.revision)>1:
        for o in set(BODY.objects)-eye_start:o.location.y+=.062
    for x in [-.432,.432]:
        o=cyl('Side circular service port',(x,.025,.775),.128,.04,silver,edge=.015);o.rotation_euler[1]=pi/2
        o=cyl('Cyan port glass',(x+(.026 if x>0 else -.026),.025,.775),.09,.016,cyan,edge=.009);o.rotation_euler[1]=pi/2
        torus('Port pearl surround',(x,.025,.775),.117,.012,white,(0,pi/2,0))
    for i,start in enumerate([.45,1.95,3.50,5.1]):
        pts=[]
        for j in range(24):
            a=start+j*.40/23
            pts.append((.568*cos(a),-.035,.78+.568*sin(a)))
        tube('Floating cyan shield arc %d'%i,pts,.027,cyan,FX,res=4)
        for p in [pts[0],pts[-1]]:ball('Rounded shield arc tip',p,(.027,)*3,cyan,FX,16,10)
    return (0,-.01,.79),1.58

def magnet():
    dark,steel=hazard_base(.43,.18)
    red=mat('Magnet | lacquer red','E51D32',.3,.22)
    silver=mat('Magnet | brushed pole caps','CDCCD7',.27,.65)
    hot=mat('Magnet | warning filament','FFDA21',.2,0,5)
    lens=mat('Magnet | red warning glass','FB1030',.17,0,.25)
    flux=mat('VFX | pink magnetic sparks','FFE4EE',.25,0,3)
    # Wide horseshoe behind the puck, flared upward at both poles.
    pts=[(-.45,.94)]
    pts.extend([(.40*cos(pi+j*pi/20),.65+.30*sin(pi+j*pi/20)) for j in range(21)])
    pts.extend([(.45,.94),(.27,.98)])
    pts.extend([(.235*cos(2*pi-j*pi/20),.66+.17*sin(2*pi-j*pi/20)) for j in range(21)])
    pts.extend([(-.27,.98)])
    o=polygon('Solid U-shaped red magnet',pts,.19,red,bevelwidth=.04);o.location.y=.10
    for side in [-1,1]:
        o=box('Silver north pole' if side<0 else 'Silver south pole',(side*.365,.10,.959),(.184,.215,.12),silver,.038)
        o.rotation_euler[1]=side*.19
        o=box('Pole red trim',(side*.347,-.011,.859),(.17,.012,.012),red,.004);o.rotation_euler[1]=side*.19
    if int(A.revision)>1:
        M=Matrix.Translation((0,0,.37))@Matrix.Diagonal((1,1,.64,1))@Matrix.Translation((0,0,-.37))
        for o in BODY.objects:
            if 'pole' in o.name.lower() or 'magnet' in o.name.lower():o.matrix_world=M@o.matrix_world
    cyl('Puck raised black shoulder',(0,0,.353),.38,.105,dark,r2=.345,edge=.025)
    cyl('Beacon foot wide',(0,0,.435),.255,.06,steel,edge=.025)
    cyl('Beacon shock mount',(0,0,.487),.218,.05,dark,edge=.017)
    cyl('Beacon red gasket',(0,0,.52),.155,.025,red,edge=.008)
    cyl('Beacon dark lower ring',(0,0,.546),.142,.04,steel,edge=.01)
    ball('Red warning dome',(0,0,.624),(.123,.123,.14),lens)
    ball('Golden warning bulb',(0,-.113,.64),(.04,.021,.055),hot,seg=20,rings=12)
    box('Front access panel',(0,-.437,.17),(.128,.047,.11),steel,.026)
    box('Front access inset',(0,-.463,.17),(.085,.009,.069),silver,.016)
    for a in [-2.35,-.78]:
        o=cyl('Bronze mounting bolt',(.432*cos(a),.432*sin(a),.16),.027,.025,mat('Magnet | bolt bronze','AD7B23',.3,.65),verts=6,edge=.006)
        o.rotation_euler=(pi/2,0,a+pi/2)
    for side in [-1,1]:
        tube('Magnetic pole flux',[(side*.34,.12,1.07),(side*.39,.12,1.14),(side*.42,.12,1.12),(side*.47,.12,1.23),(side*.50,.12,1.25)],.007,flux,FX,res=2)
    if int(A.revision)>1:
        for o in FX.objects:o.location.z-=.22
    return (0,0,.55),1.40

def gear():
    # The spectral color transition is represented with simple exportable PBR materials.
    colors=['37E5FA','55D9FF','78BEFC','9494F0','A675E8','BD61EF','D968EF']
    palette=[mat('Gear | spectral band %d'%i,h,.25,.15,.45,(.12 if int(A.revision)==1 else .42)) for i,h in enumerate(colors)]
    edges=[mat('Gear | luminous edge %d'%i,h,.22,0,1.2) for i,h in enumerate(colors)]
    nteeth=10;outer=[];angles=[]
    for i in range(nteeth):
        a=2*pi*i/nteeth
        for off,r in [(-.5,.413),(-.29,.413),(-.25,.52),(.25,.52),(.29,.413)]:
            t=a+off*2*pi/nteeth;outer.append((r*cos(t),r*sin(t)));angles.append(t)
    if int(A.revision)>1:
        rounded=[]
        for k,p in enumerate(outer):
            prev,nxt=outer[k-1],outer[(k+1)%len(outer)]
            rounded.extend([(p[0]*.88+prev[0]*.12,p[1]*.88+prev[1]*.12),(p[0]*.88+nxt[0]*.12,p[1]*.88+nxt[1]*.12)])
        outer=rounded;angles=[math.atan2(z,x) for x,z in outer]
    n=len(outer);v=[]
    for y in [-.078,.078]:
        v.extend([(x,y,z+.76) for x,z in outer])
        v.extend([(.237*cos(a),y,.76+.237*sin(a)) for a in angles])
    f=[]
    for i in range(n):
        j=(i+1)%n
        f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    o=mesh('Phase gear body with open center',v,f,None,smooth=False)
    for m in palette:o.data.materials.append(m)
    for p in o.data.polygons:
        x=sum(o.data.vertices[i].co.x for i in p.vertices)/len(p.vertices)
        p.material_index=min(6,max(0,int((x+.52)/1.04*7)))
    bevel(o,.016 if int(A.revision)==1 else .023,3)
    for i in range(n):
        j=(i+1)%n;idx=min(6,max(0,int((outer[i][0]+.52)/1.04*7)))
        tube('Glowing tooth edge',[(outer[i][0],-.081,outer[i][1]+.76),(outer[j][0],-.081,outer[j][1]+.76)],.005,edges[idx],res=2)
    for i in range(64):
        a=i*2*pi/64;b=(i+1)*2*pi/64;idx=min(6,max(0,int((.237*cos(a)+.52)/1.04*7)))
        tube('Glowing inner bore',[(.237*cos(a),-.085,.76+.237*sin(a)),(.237*cos(b),-.085,.76+.237*sin(b))],.006,edges[idx],res=2)
    transform(list(BODY.objects),(.03,-.16,-.10),pivot=(0,0,.76))
    return (0,0,.76),1.43

def painter():
    aluminum=mat('Painter | satin aluminum','C5C9D0',.3,.68)
    cream=mat('Painter | ivory can enamel','EEEADB',.4,.16)
    blue=mat('Painter | glossy blue paint','087DAC',.3,.25)
    nozzle=mat('Painter | blue spray button','039BE6',.27,.25)
    hole=mat('Painter | nozzle opening','08253E',.45)
    cyan=mat('Painter | cyan fresh paint','15DBFF',.22,0,1.2)
    lane=mat('Painter | pale road dashes','D2F6FF',.3,.1,.2)
    dark=mat('Painter | crimp recess','556576',.36,.6)
    cyl('Aerosol can body',(0,0,.59),.242,.73,cream,edge=.032)
    for z in [.237,.941]:
        torus('Rolled aluminum can rim',(0,0,z),.229,.022,aluminum)
        torus('Can seam shadow',(0,0,z+(.025 if z<.5 else -.02)),.24,.005,dark)
    cyl('Can shoulder',(0,0,.985),.227,.092,aluminum,r2=.16,edge=.022)
    cyl('Upper valve plate',(0,0,1.044),.154,.03,aluminum,edge=.009)
    cyl('Valve stem',(0,0,1.075),.043,.06,dark,edge=.005)
    box('Blue aerosol nozzle',(0,-.006,1.14),(.144,.145,.145),nozzle,.025)
    o=cyl('Nozzle inset socket',(0,-.086,1.153),.038,.014,lane,verts=32,edge=.007);o.rotation_euler[0]=pi/2
    o=cyl('Black spray aperture',(0,-.096,1.153),.025,.013,hole,verts=32,edge=.004);o.rotation_euler[0]=pi/2
    # Blue label follows the cylindrical surface, with liquid drip geometry at its upper boundary.
    verts=[];n=80
    for j in range(2):
        for i in range(n):
            a=-2.25+3.9*i/(n-1)
            upper=.893-.08*math.exp(-((a+.3)/.12)**2)-.055*math.exp(-((a-.65)/.16)**2)-.12*math.exp(-((a+1.1)/.17)**2)
            z=(.266 if j==0 else upper) if int(A.revision)==1 else (upper if j==0 else .912)
            verts.append((.245*cos(a),.245*sin(a),z))
    mesh('Blue paint wrap with rounded drips',verts,[(i,i+1,n+i+1,n+i) for i in range(n-1)],blue)
    # Tapered road triangle printed on the curved can, its broad end at the bottom.
    verts=[];rows=25;cols=17
    for k in range(rows):
        t=k/(rows-1);z=.268+.589*t;w=.224*(1-t)+.01*t
        for j in range(cols):
            x=-w+2*w*j/(cols-1);verts.append((x,-math.sqrt(.248**2-x*x),z))
    mesh('Tapering blue speed road',verts,[(k*cols+j,k*cols+j+1,(k+1)*cols+j+1,(k+1)*cols+j) for k in range(rows-1) for j in range(cols-1)],blue)
    for i,(z,h,w) in enumerate([(.35,.093,.029),(.535,.071,.021),(.695,.048,.013),(.797,.026,.007)]):
        o=box('Road center dash %d'%i,(0,-.251,z),(w,.008,h),lane,.003)
    transform(list(BODY.objects),(0,.13,-.025),pivot=(0,0,.66))
    # The swoosh is optional geometry, kept separate from the can.
    pts=[]
    for i in range(75):
        t=i/74;a=pi*.55+pi*1.2*t
        pts.append((.46*cos(a),.11+.08*sin(a),.67+.44*sin(a)))
    tube('Cyan painted orbit',pts,.023,cyan,FX,res=3)
    tube('Thin outer paint highlight',[(p[0]*1.13,p[1]+.014,.67+(p[2]-.67)*1.08) for p in pts],.009,lane,FX,res=2)
    ball('Fresh paint puddle',(.23,.09,.23),(.32,.14,.018),cyan,FX)
    return (0,0,.68),1.58

def curved_arrow(name,start,end,z0,z1,r,m):
    n=65;verts=[];h=.143;thick=.042
    for i in range(n):
        t=i/(n-1);a=start+(end-start)*t;z=z0+(z1-z0)*t
        for dr,dz in [(-thick/2,-h/2),(thick/2,-h/2),(thick/2,h/2),(-thick/2,h/2)]:
            verts.append(((r+dr)*cos(a),(r+dr)*sin(a),z+dz))
    f=[]
    for i in range(n-1):
        for k in range(4):f.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    f.extend([tuple(reversed(range(4))),tuple((n-1)*4+k for k in range(4))])
    bevel(mesh(name+' curved ribbon',verts,f,m),.01,3)
    center=Vector((r*cos(end),r*sin(end),z1))
    tangent=Vector((-sin(end),cos(end),0))*(1 if end>start else -1);radial=Vector((cos(end),sin(end),0))
    shape=[(-.016,-h/2),(.027,-h/2),(.027,-.147),(.228,0),(.027,.147),(.027,h/2),(-.016,h/2)]
    verts=[center+tangent*s+Vector((0,0,z))+radial*d for d in [-.023,.023] for s,z in shape]
    n=len(shape);f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    bevel(mesh(name+' arrowhead',verts,f,m,smooth=False),.015,3)

def beacon():
    red=mat('Swap | coral red arrow','F62742',.26,.23)
    blue=mat('Swap | cobalt blue arrow','2859E8',.25,.27)
    crystal=[mat('Swap | crystal facet '+str(i),h,.2,.15,.12,.20) for i,h in enumerate(['55DAFF','238CFF','2356DB','816AEB','CAE9FF','2ECAEF'])]
    pink=mat('VFX | pink crystal shards','FF55C9',.23,0,1.3)
    levels=[(1.39,0),(1.19,.104),(1.025,.163),(.835,.092),(.68,0)] if int(A.revision)!=2 else [(1.39,0),(1.19,.104),(1.025,.163),(.73,.085),(.39,0)]
    verts=[];n=6
    for z,r in levels:
        for i in range(n):
            a=2*pi*i/n+pi/6;verts.append((r*cos(a),r*sin(a),z))
    f=[]
    for j in range(4):
        for i in range(n):
            k=(i+1)%n
            if j==0:f.append((i,n+i,n+k))
            elif j==3:f.append((j*n+i,(j+1)*n+i,j*n+k))
            else:f.append((j*n+i,(j+1)*n+i,(j+1)*n+k,j*n+k))
    o=mesh('Tall faceted swap crystal',verts,f,None,smooth=False)
    for m in crystal:o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=(p.index%6+(p.index//6)%2)%6
    if int(A.revision)>2:
        # The concept's small lower spectral point is distinct from its broad upper diamond.
        tail=mesh('Lower spectral crystal point',[(0,0,.79),(-.07,0,.52),(0,-.055,.52),(.07,0,.52),(0,.055,.52),(0,0,.35)],
                  [(0,1,2),(0,2,3),(0,3,4),(0,4,1),(5,2,1),(5,3,2),(5,4,3),(5,1,4)],crystal[3],smooth=False)
    curved_arrow('Red exchange',.56*pi,1.84*pi,.86,.71,.365,red)
    if int(A.revision)==1:curved_arrow('Blue exchange',-.36*pi,.73*pi,.72,.53,.405,blue)
    else:curved_arrow('Blue exchange',.65*pi,-.50*pi,.73,.43,.405,blue)
    for i,(x,z,s) in enumerate([(-.45,1.27,.027),(.38,1.25,.036),(-.44,.53,.04),(.45,.38,.027)]):
        o=ico('Pink suspended crystal fleck %d'%i,(x,.015,z),1,pink,FX,1)
        o.scale=(s*.4,s*.32,s);o.rotation_euler[1]=.55
    return (0,0,.87),1.6

BUILDERS={'comet-core':comet,'snaptrap':snapt,'turbo-battery':turbo,'guardian-orb':orb,'magnet-mine':magnet,'phase-gear':gear,'route-painter':painter,'swap-beacon':beacon}

def uv_and_apply():
    import bmesh
    for o in list(BODY.objects)+list(FX.objects):
        select(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
        bm.to_mesh(o.data);bm.free();o.data.update()
        if not o.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=.025)
            bpy.ops.object.mode_set(mode='OBJECT')

def material_values(m):
    p=m.node_tree.nodes.get('Principled BSDF')
    return {k:list(p.inputs[k].default_value) if k.endswith('Color') else p.inputs[k].default_value for k in ['Base Color','Metallic','Roughness','Emission Color','Emission Strength','Transmission Weight']}

def package():
    exp=OUT/'exports';exp.mkdir(exist_ok=True)
    # Preserve editability in source; consolidate exchange meshes by material per collection.
    originals=list(BODY.objects)+list(FX.objects)
    copies=[]
    for collection in [BODY,FX]:
        bymat={}
        for src in collection.objects:
            o=src.copy();o.data=src.data.copy();S.collection.objects.link(o)
            bymat.setdefault(o.data.materials[0].name,[]).append(o)
        for mn,objects in bymat.items():
            bpy.ops.object.select_all(action='DESELECT')
            for o in objects:o.select_set(True)
            bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
            o=bpy.context.object;o.name=('FX_' if collection==FX else 'Item_')+mn.replace(' | ','_').replace(' ','_')
            S.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            copies.append(o)
    pivot=Vector({'comet-core':(0,0,.9),'turbo-battery':(0,0,.69),'guardian-orb':(0,0,.79),
                  'phase-gear':(0,0,.76),'route-painter':(0,0,.68),'swap-beacon':(0,0,.87)}.get(A.item,(0,0,0)))
    for o in copies:
        o.location-=pivot;select(o);S.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.select_all(action='DESELECT')
    for o in copies:o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    fbx=exp/(A.item+'.fbx');glb=exp/(A.item+'.glb')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,path_mode='STRIP')
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_yup=True)
    triangles=sum(len(p.vertices)-2 for o in copies for p in o.data.polygons)
    bounds=[o.matrix_world@Vector(c) for o in copies for c in o.bound_box]
    manifest={'item':A.item,'revision':A.revision,'source':str((OUT/(A.item+'.blend')).relative_to(ROOT)),
              'triangles':triangles,'meshObjects':len(copies),'editableSourceObjects':len(originals),
              'boundsMeters':[[min(v[k] for v in bounds) for k in range(3)],[max(v[k] for v in bounds) for k in range(3)]],
              'units':'meters','sourceForward':'-Y','sourceUp':'Z','exchangeUp':'Y','exportPivotSourceMeters':list(pivot),
              'materials':{m.name:material_values(m) for o in copies for m in o.data.materials},
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/(A.item+'.blend'),fbx,glb]},
              'notes':'Original modeled geometry from supplied concept. FX_ meshes are optional decorative effects. FBX needs explicit URP materials using these linear values. No gameplay implementation or engine appearance validation.'}
    (exp/(A.item+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    for o in copies:bpy.data.objects.remove(o,do_unlink=True)

def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()

def studio(target,extent):
    S.render.engine='CYCLES';S.cycles.samples=A.samples;S.cycles.use_denoising=True
    S.render.resolution_x=A.resolution;S.render.resolution_y=A.resolution;S.render.resolution_percentage=100
    S.world.color=(.18,.18,.18)
    S.view_settings.view_transform='Standard'
    S.view_settings.look='None'
    S.view_settings.exposure=-1
    S.render.image_settings.file_format='PNG'
    floor=mat('Studio | plum','80506C',.72)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.15));finish(bpy.context.object,'Studio floor',floor,STUDIO)
    for name,pos,power,size,col in [('Key',(-3,-4,6),650,4,(1,.85,.73)),('Fill',(3,-2,3),450,3,(.64,.8,1)),('Rim',(1,3,4),850,3,(1,.52,.55))]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col
        o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=pos;aim(o,target)
    d=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',d);STUDIO.objects.link(cam)
    d.type='ORTHO';d.ortho_scale=extent;S.camera=cam
    # A mild fog-glow pass; the source mesh carries emission independently.
    S.use_nodes=True
    tree=bpy.data.node_groups.new('Item review compositor','CompositorNodeTree');S.compositing_node_group=tree
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=tree.nodes.new('CompositorNodeRLayers');glow=tree.nodes.new('CompositorNodeGlare');glow.inputs['Type'].default_value='Fog Glow';glow.inputs['Quality'].default_value='High';glow.inputs['Strength'].default_value=.5;glow.inputs['Threshold'].default_value=.65
    output=tree.nodes.new('NodeGroupOutput');tree.links.new(layers.outputs['Image'],glow.inputs['Image']);tree.links.new(glow.outputs['Image'],output.inputs['Image'])
    return cam

def render_review(target,extent,destination):
    cam=studio(target,extent)
    destination.mkdir(parents=True,exist_ok=True)
    for view in A.views.split(','):
        delta={'hero':(2.7,-6,2.5),'front':(0,-6,.7),'side':(6,0,1.1),'rear':(2,6,2)}[view]
        cam.location=Vector(target)+Vector(delta);aim(cam,target)
        S.render.filepath=str(destination/(view+'.png'));bpy.ops.render.render(write_still=True)
    ref=bpy.data.images.load(str(ROOT/'art-source/concepts/items/item-concepts.png'),check_existing=True);ref.pack()
    # Open review files at their useful hero view rather than the last diagnostic angle.
    cam.location=Vector(target)+Vector((2.7,-6,2.5));aim(cam,target)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.item+'-review.blend')))

if A.review_only:
    bpy.ops.wm.open_mainfile(filepath=str(OUT/(A.item+'.blend')))
    S=bpy.context.scene;BODY=bpy.data.collections['EXPORT'];FX=bpy.data.collections['EFFECTS'];STUDIO=bpy.data.collections['STUDIO']
    S.view_settings.view_transform='Standard';S.view_settings.look='None';S.view_settings.exposure=-1
    framing={'comet-core':((0,0,.9),2.2),'snaptrap':((0,0,.68),1.7),'turbo-battery':((0,0,.69),1.65),
             'guardian-orb':((0,-.01,.79),1.58),'magnet-mine':((0,0,.55),1.4),'phase-gear':((0,0,.76),1.43),
             'route-painter':((0,0,.68),1.58),'swap-beacon':((0,0,.87),1.6)}
    target,extent=framing[A.item]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_location=target;space.region_3d.view_distance=extent*1.4
                space.region_3d.view_rotation=Vector((2.7,-6,2.5)).to_track_quat('Z','Y');space.shading.type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.item+'.blend')))
    manifest=OUT/'exports'/(A.item+'.manifest.json')
    data=json.loads(manifest.read_text());data['sha256'][A.item+'.blend']=hashlib.sha256((OUT/(A.item+'.blend')).read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data,indent=2)+'\n')
    render_review(target,extent,OUT/'review/final')
    print('ITEM_REVIEW_COMPLETE',A.item)
    sys.exit(0)

if A.package_only:
    bpy.ops.wm.open_mainfile(filepath=str(OUT/(A.item+'.blend')))
    S=bpy.context.scene;BODY=bpy.data.collections['EXPORT'];FX=bpy.data.collections['EFFECTS']
    uv_and_apply()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.item+'.blend')))
    package()
    print('ITEM_REPACKAGED',A.item)
    sys.exit(0)

target,extent=BUILDERS[A.item]()
uv_and_apply()
S.cursor.location=target
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_location=target;space.region_3d.view_distance=extent*1.4
            space.region_3d.view_rotation=Vector((2.7,-6,2.5)).to_track_quat('Z','Y')
            space.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
S['concept_source']='art-source/concepts/items/item-concepts.png'
S['asset_item']=A.item;S['revision']=A.revision
S['authoring_notes']='Editable model meshes in EXPORT; optional decorative geometry in EFFECTS. Review studio is excluded from exchange files.'
source=OUT/(A.item+'-v'+A.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(source))
if A.final:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.item+'.blend')))
    package()
render_review(target,extent,REVIEW)
print('ITEM_BUILD_COMPLETE',A.item,A.revision)
