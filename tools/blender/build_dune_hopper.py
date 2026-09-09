"""Model Grit's Dune Hopper around the accepted independent driver.

Blender --background --factory-startup --python tools/blender/build_dune_hopper.py
-- --revision 01 --views hero,front,side,rear
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='01')
parser.add_argument('--views',default='hero,front,side,rear')
parser.add_argument('--samples',type=int,default=36)
parser.add_argument('--resolution',type=int,default=1200)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=ROOT/'art-source/blender/karts/dune-hopper'
REVIEW=OUT/'review'/('v'+args.revision)
REVIEW.mkdir(parents=True,exist_ok=True)
DRIVER=ROOT/'art-source/blender/characters/grit/grit-driver.blend'
bpy.ops.wm.open_mainfile(filepath=str(DRIVER))
scene=bpy.context.scene
scene.frame_set(1)


def collection(name):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


frame=collection('DUNE_FRAME')
bodywork=collection('DUNE_PANELS')
running=collection('DUNE_RUNNING_GEAR')
engine=collection('DUNE_ENGINE')
cockpit=collection('DUNE_COCKPIT')
seat_collection=collection('DUNE_SEAT')
details=collection('DUNE_DETAILS')
controls=collection('DUNE_CONTROLS')
studio=collection('DUNE_STUDIO')
refs=collection('DUNE_REFERENCE')
kart_collections=[frame,bodywork,running,engine,cockpit,seat_collection,details]


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def move(obj,c):
    for old in list(obj.users_collection): old.objects.unlink(obj)
    c.objects.link(obj)
    return obj


def parent(obj,p):
    bpy.context.view_layer.update()
    world=obj.matrix_world.copy()
    obj.parent=p
    obj.matrix_world=world


def empty(name,pos=(0,0,0),p=None):
    ob=bpy.data.objects.new(name,None)
    controls.objects.link(ob)
    ob.location=pos
    ob.empty_display_size=.14
    if p: parent(ob,p)
    return ob


root=empty('Dune_Hopper_Root')
root['asset_id']='dune-hopper'
root['steering_degrees']=0.0
root['wheel_spin_degrees']=0.0
root['instructions']='steering_degrees turns the front wheels and steering wheel. wheel_spin_degrees rolls the four road wheels. The carried spare is fixed.'
root.id_properties_ui('steering_degrees').update(min=-30,max=30)
root.id_properties_ui('wheel_spin_degrees').update(min=-3600,max=3600)
offset=Vector((0,.12,.58))
rig=bpy.data.objects['Grit_Driver_Rig']
rig.location+=offset
parent(rig,root)
seat_root=empty('Dune_Seat_Root',offset,root)
seat_root['instructions']='Move this root to move only the seat. Grit_Driver_Rig moves the driver independently.'


def linear(color):
    c=[int(color[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)


def material(name,color,rough=.4,metal=0,coat=0):
    m=bpy.data.materials.new('Dune Hopper | '+name)
    m.diffuse_color=linear(color)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=linear(color)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    p.inputs['Specular IOR Level'].default_value=.30
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.28
    return m


yellow=material('sunflower enamel','F7BB11',.36,.12,.22)
orange=material('orange springs and rims','E65B08',.32,.32,.15)
graphite=material('graphite tubular frame','424849',.36,.68)
steel=material('warm skid plate steel','9B9C8C',.40,.72)
alloy=material('brushed aluminum','A9B3B0',.30,.78)
black=material('recesses and motor','1D2525',.60,.18)
rubber=material('rubber sidewalls','282B2B',.69)
treadmat=material('rubber tread','303332',.66)
seatmat=material('charcoal seat padding','303A3A',.67)
strapmat=material('orange spare strap','D96D1F',.56)
lens=material('warm headlamp glass','FFE3A1',.22,.12)
lens.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=linear('FFE8B6')
lens.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.30
red=material('rear lamp lens','DE3E0B',.24,.15)
red.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=linear('ED4D0F')
red.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.12


def mesh(name,verts,faces,mat,c=details,smooth=True):
    d=bpy.data.meshes.new(name+'_Mesh')
    d.from_pydata(verts,[],faces)
    d.update()
    ob=bpy.data.objects.new(name,d)
    c.objects.link(ob)
    if mat: d.materials.append(mat)
    for p in d.polygons: p.use_smooth=smooth
    return ob


def apply(obj,mod):
    select(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def bevel(obj,width,segments=3):
    m=obj.modifiers.new('Soft manufactured edges','BEVEL')
    m.width,m.segments=width,segments
    apply(obj,m)
    m=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    m.keep_sharp=True
    apply(obj,m)
    return obj


def box(name,pos,size,radius,mat,c=details,segments=3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    ob=move(bpy.context.object,c)
    ob.name=name
    ob.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    bevel(ob,radius,segments)
    return ob


def ball(name,pos,scale,mat,c=details,segments=28,rings=18):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    ob=move(bpy.context.object,c)
    ob.name=name
    ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth=True
    return ob


def spline(points,steps=8):
    ps=[Vector(p) for p in points]
    out=[]
    for i in range(len(ps)-1):
        a,b,c,d=ps[max(i-1,0)],ps[i],ps[i+1],ps[min(i+2,len(ps)-1)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out+[ps[-1]]


def tube(name,points,radius,mat,c=details,sides=16,caps=True,closed=False):
    ps=[Vector(p) for p in points]
    verts=[]
    previous=None
    for i,p in enumerate(ps):
        d=(ps[(i+1)%len(ps) if closed else min(i+1,len(ps)-1)]-ps[(i-1)%len(ps) if closed else max(i-1,0)]).normalized()
        if previous is None:
            b=d.cross(Vector((0,1,0)))
            if b.length<.01: b=d.cross(Vector((0,0,1)))
            b.normalize()
        else:
            b=(previous-d*previous.dot(d)).normalized()
        previous=b
        n=d.cross(b).normalized()
        for j in range(sides):
            a=j*2*math.pi/sides
            verts.append(p+radius*(b*math.cos(a)+n*math.sin(a)))
    faces=[]
    for i in range(len(ps) if closed else len(ps)-1):
        for j in range(sides):
            faces.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%len(ps))*sides+(j+1)%sides,((i+1)%len(ps))*sides+j))
    if caps and not closed:
        faces += [tuple(reversed(range(sides))),tuple((len(ps)-1)*sides+j for j in range(sides))]
    return mesh(name,verts,faces,mat,c)


def bar(name,a,b,r=.038,mat=graphite,c=frame):
    return tube(name,[a,b],r,mat,c,sides=20)


def ring(name,center,axis,radius,wire,mat,c=details,segments=48,sides=12):
    center,axis=Vector(center),Vector(axis).normalized()
    u=axis.cross(Vector((0,0,1)))
    if u.length<.01: u=axis.cross(Vector((0,1,0)))
    u.normalize()
    v=axis.cross(u).normalized()
    points=[center+radius*(u*math.cos(i*2*math.pi/segments)+v*math.sin(i*2*math.pi/segments)) for i in range(segments)]
    return tube(name,points,wire,mat,c,sides=sides,closed=True)


def cylinder(name,pos,axis,radius,depth,mat,c=details,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    ob=move(bpy.context.object,c)
    ob.name=name
    ob.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    ob.data.materials.append(mat)
    bevel(ob,min(.009,depth*.2),2)
    for p in ob.data.polygons: p.use_smooth=True
    return ob


def plate(name,outline,origin,u,v,thickness,mat,c=bodywork,edge=.025):
    origin,u,v=Vector(origin),Vector(u).normalized(),Vector(v).normalized()
    normal=u.cross(v).normalized()
    n=len(outline)
    verts=[origin+u*x+v*y+normal*d for d in (-thickness*.5,thickness*.5) for x,y in outline]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return bevel(mesh(name,verts,faces,mat,c,smooth=False),edge,3)


def bolt(name,pos,axis=(0,-1,0),radius=.023,c=details):
    cylinder(name,pos,axis,radius,.012,alloy,c,vertices=12)
    cylinder(name+'_hex_socket',Vector(pos)+Vector(axis)*.009,axis,radius*.40,.004,black,c,vertices=6)


# Tubular ladder chassis and triangular side cages. The crossbar stays below Grit's horns.
for s,side in [(-1,'L'),(1,'R')]:
    tube('Lower_chassis_'+side,spline([(s*.40,-1.29,.43),(s*.55,-.93,.50),(s*.62,.39,.51),(s*.53,1.30,.47)],5),.049,graphite,frame,sides=20)
    tube('Cockpit_side_rail_'+side,spline([(s*.43,-1.11,.86),(s*.57,-.58,1.02),(s*.64,.22,1.09),(s*.61,.57,1.29)],5),.043,graphite,frame,sides=20)
    tube('Main_roll_upright_'+side,spline([(s*.55,-.59,.50),(s*.65,.16,1.04),(s*.63,.54,1.73),(s*.52,.62,1.91)],5),.046,graphite,frame,sides=20)
    tube('Rear_roll_brace_'+side,spline([(s*.52,.62,1.91),(s*.56,.95,1.35),(s*.54,1.36,.52)],6),.045,graphite,frame,sides=20)
    bar('Side_triangle_front_'+side,(s*.55,-.93,.51),(s*.64,.22,1.09),.037)
    bar('Side_triangle_rear_'+side,(s*.64,.22,1.09),(s*.53,.52,.51),.041)
    for y,z in [(-.93,.50),(.22,1.09),(.52,.51),(.62,1.91),(1.30,.48)]:
        ball('Frame_joint_'+side+str(y),(s*(.52 if y>.5 else .59),y,z),(.065,.065,.065),graphite,frame,20,12)
for y,z,w in [(-1.28,.43,.43),(-.67,.51,.59),(.34,.52,.62),(1.30,.48,.54),(.62,1.91,.52)]:
    bar('Chassis_crossmember_'+str(y),(-w,y,z),(w,y,z),.043)
bar('Rear_engine_cross_brace_A',(-.5,.72,.52),(.5,1.28,.81),.035)
bar('Rear_engine_cross_brace_B',(.5,.72,.52),(-.5,1.28,.81),.035)
floor=box('Raised_cockpit_floor',(0,-.08,.57),(1.05,1.70,.085),.075,black,frame)

# Sparse triangular yellow body panels leave the mechanical structure exposed.
for s,side in [(-1,'L'),(1,'R')]:
    rear_outline=[(-.02,.97),(.60,1.16),(.54,.62)]
    front_outline=[(-.88,.82),(-.06,.98),(-.40,.56)]
    for label,outline in [('Rear',rear_outline),('Front',front_outline)]:
        ob=plate(label+'_side_panel_'+side,outline,(s*.648,0,0),(0,1,0),(0,0,1),.035,yellow,edge=.04)
        for j,(y,z) in enumerate(outline):
            cy=sum(p[0] for p in outline)/3
            cz=sum(p[1] for p in outline)/3
            bolt(label+'_panel_fastener_'+side+str(j),(s*.674,y*.79+cy*.21,z*.79+cz*.21),(s,0,0),.023)
    # Small protective shelves above each coil-over, with bowed outer edges.
    for label,y,z in [('Front',-.98,1.135),('Rear',.96,1.185)]:
        fv=[]
        for j in range(9):
            x=.47+j*.052
            height=z+.046*math.sin(math.pi*j/8)-.035*(j/8)**4
            for dy in (-.22,.20): fv.append((s*x,y+dy,height))
        ff=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(8)]
        ob=mesh(label+'_small_fender_'+side,fv,ff,yellow,bodywork)
        m=ob.modifiers.new('Fender panel thickness','SOLIDIFY')
        m.thickness=.030
        apply(ob,m)
        bevel(ob,.021,3)
        for x in (.54,.80):
            t=(x-.47)/(.052*8)
            height=z+.046*math.sin(math.pi*t)-.035*t**4
            bolt(label+'_fender_bolt_'+side+str(x),(s*x,y,height+.006),(0,0,1),.022)

hood=plate('Short_blunt_nose_panel',[(-.42,-.20),(.42,-.20),(.32,.20),(-.32,.20)],
           (0,-1.12,.94),(1,0,0),(0,.40,.916),.045,yellow,edge=.060)
for s in (-1,1): bolt('Nose_panel_bolt_'+str(s),(s*.30,-1.165,.96),(0,-1,.2),.025)


def skid(name,y,z,rear=False):
    shape=[(-.40,-.21),(.40,-.21),(.52,-.02),(.43,.22),(-.43,.22),(-.52,-.02)]
    ob=plate(name,shape,(0,y,z),(1,0,0),(0,-.22 if rear else .22,.975),.048,steel,edge=.043)
    for x in (-.245,0,.245):
        cut=box('Skid_vent_cutter',(x,y,z),(.070,.45,.255),.033,black,details)
        m=ob.modifiers.new('Open cooling slot','BOOLEAN')
        m.operation,m.solver,m.object='DIFFERENCE','EXACT',cut
        apply(ob,m)
        bpy.data.objects.remove(cut,do_unlink=True)
    axis=(0,1,0) if rear else (0,-1,0)
    for x,zz in [(-.35,-.125),(.35,-.125),(-.39,.10),(.39,.10)]:
        bolt(name+'_fastener_'+str(x)+str(zz),(x,y+(.031 if rear else -.031),z+zz),axis,.023)
    return ob


skid('Front_three_slot_skid',-1.47,.55)
skid('Rear_three_slot_skid',1.45,.51,True)
tube('Front_protection_bumper',spline([(-.53,-1.34,.45),(-.57,-1.34,.78),(0,-1.32,.88),(.57,-1.34,.78),(.53,-1.34,.45)],6),.039,graphite,frame,sides=20)

# A single square lamp with a recessed reflector and a rounded warm lens.
for name,pos,size,r,mat in [('Headlamp_housing',(0,-1.19,1.08),(.40,.19,.41),.072,graphite),
                           ('Headlamp_bezel',(0,-1.296,1.08),(.344,.035,.357),.065,alloy),
                           ('Headlamp_reflector',(0,-1.320,1.08),(.292,.023,.303),.057,orange),
                           ('Headlamp_lens',(0,-1.337,1.08),(.250,.020,.267),.054,lens)]:
    box(name,pos,size,r,mat,details,segments=5)
ring('Headlamp_inner_optic',(0,-1.354,1.08),(0,-1,0),.096,.009,lens,segments=48)
ball('Headlamp_convex_optic',(0,-1.354,1.08),(.092,.020,.101),lens,details,32,20)

# Seat is its own transform group, independent of the character and steering wheel.
cushion=box('Dune_Seat_Cushion',offset+Vector((0,.055,.146)),(.74,.65,.13),.065,seatmat,seat_collection,5)
back=box('Dune_Seat_Back',offset+Vector((0,.33,.52)),(.76,.155,.83),.076,seatmat,seat_collection,5)
back.rotation_euler.x=math.radians(8)
for ob in (cushion,back): parent(ob,seat_root)
for s,side in [(-1,'L'),(1,'R')]:
    bolster=ball('Seat_side_bolster_'+side,offset+Vector((s*.34,.255,.49)),(.075,.115,.36),seatmat,seat_collection,32,20)
    parent(bolster,seat_root)
    rail=bar('Seat_mount_rail_'+side,(s*.26,-.1,.62),(s*.26,.61,.62),.026,alloy,seat_collection)
    parent(rail,seat_root)
wheel_center=offset+Vector((0,-.678,.632))
steering_frame=empty('Dune_Steering_Frame',wheel_center,root)
steering_frame.rotation_euler.x=math.radians(52)
steering_spin=empty('Dune_Steering_Spin')
steering_spin.parent=steering_frame
steering_spin.location=(0,0,0)
steering_parts=[]
steering_parts.append(ring('Steering_wheel',(0,0,0),(0,0,1),.259,.034,rubber,cockpit,64,16))
for a in (0,2*math.pi/3,4*math.pi/3):
    steering_parts.append(bar('Steering_spoke',(0,0,0),(.232*math.cos(a),.232*math.sin(a),0),.015,alloy,cockpit))
steering_parts.append(cylinder('Steering_hub',(0,0,.005),(0,0,1),.064,.04,graphite,cockpit))
steering_parts.append(cylinder('Steering_orange_cap',(0,0,.03),(0,0,1),.041,.014,orange,cockpit))
for ob in steering_parts: ob.parent=steering_spin
bpy.context.view_layer.update()
bar('Angled_steering_column',wheel_center+steering_frame.matrix_world.to_3x3()@Vector((0,0,-.035)),(0,-.50,.64),.024,alloy,cockpit)


def control(obj,index,prop,factor):
    d=obj.driver_add('rotation_euler',index).driver
    var=d.variables.new()
    var.name='value'
    var.targets[0].id=root
    var.targets[0].data_path='["'+prop+'"]'
    d.expression='value * '+repr(factor)


control(steering_spin,2,'steering_degrees',math.pi/180*1.25)


def lathe(name,profile,mat,c=running,segments=72,closed=True):
    verts=[(x,r*math.sin(j*2*math.pi/segments),r*math.cos(j*2*math.pi/segments)) for x,r in profile for j in range(segments)]
    faces=[]
    for i in range(len(profile) if closed else len(profile)-1):
        for j in range(segments):
            faces.append((i*segments+j,i*segments+(j+1)%segments,((i+1)%len(profile))*segments+(j+1)%segments,((i+1)%len(profile))*segments+j))
    return mesh(name,verts,faces,mat,c)


def wheel(name,center,radius,width,sign=1,spare=False):
    if spare:
        pivot=empty('Dune_Spare_Mount',center,root)
        pivot.rotation_euler.z=math.pi/2
    else:
        steer=empty('Dune_Steer_'+name,center,root)
        pivot=empty('Dune_Spin_'+name,center,steer)
        if name.startswith('F'): control(steer,2,'steering_degrees',math.pi/180)
        control(pivot,0,'wheel_spin_degrees',math.pi/180)
    pieces=[]
    w=width*.5
    profile=[(-w*.93,radius*.59),(-w*1.06,radius*.69),(-w*1.05,radius*.81),(-w*.91,radius*.93),
             (-w*.52,radius*.994),(0,radius),(w*.52,radius*.994),(w*.91,radius*.93),
             (w*1.05,radius*.81),(w*1.06,radius*.69),(w*.93,radius*.59)]
    pieces.append(lathe('Tire_'+name,profile,rubber,segments=72))
    # Repeated rounded blocks are joined into one editable tread mesh per tire.
    tw,tl=width*.29,.130 if not spare else .091
    outline=[(-.5*tw,-.40*tl),(-.10*tw,-.52*tl),(.50*tw,-.42*tl),
             (.50*tw,.20*tl),(.16*tw,.46*tl),(-.50*tw,.48*tl),(-.40*tw,.10*tl)]
    template=plate('Tread_template',outline,(0,0,0),(1,0,0),(0,1,0),
                   .046 if not spare else .035,treadmat,running,edge=.012)
    tv=[v.co.copy() for v in template.data.vertices]
    tf=[p.vertices[:] for p in template.data.polygons]
    bpy.data.objects.remove(template,do_unlink=True)
    verts,faces=[],[]
    for row,axial in enumerate((-width*.32,0,width*.32)):
        for j in range(24):
            theta=(j+(row%2)*.50)*2*math.pi/24
            rot=Matrix.Rotation(-theta,4,'X')@Matrix.Rotation((.18 if row!=1 else -.18),4,'Z')
            center_local=Vector((axial,(radius+.009)*math.sin(theta),(radius+.009)*math.cos(theta)))
            start=len(verts)
            verts += [rot.to_3x3()@v+center_local for v in tv]
            faces += [tuple(start+i for i in f) for f in tf]
    tread=mesh('Chunky_tread_'+name,verts,faces,treadmat,running,smooth=True)
    m=tread.modifiers.new('Rounded tread normals','WEIGHTED_NORMAL')
    m.keep_sharp=True
    apply(tread,m)
    pieces.append(tread)
    # Outer dish, tire bead, center dome, and inset wheel bolts.
    rim_profile=[(sign*w*.75,radius*.22),(sign*w*.50,radius*.30),(sign*w*.56,radius*.50),
                 (sign*w*.91,radius*.58),(sign*w*1.05,radius*.61),(sign*w*1.10,radius*.57),
                 (sign*w*.96,radius*.48),(sign*w*.91,radius*.25)]
    pieces.append(lathe('Orange_rim_'+name,rim_profile,graphite if spare else orange,segments=64))
    pieces.append(ring('Rim_bead_'+name,(sign*w*1.04,0,0),(1,0,0),radius*.61,.012,black,running))
    pieces.append(ball('Hub_dome_'+name,(sign*w*.97,0,0),(.062,radius*.222,radius*.222),alloy,running,32,20))
    pieces.append(ring('Hub_ring_'+name,(sign*w*.94,0,0),(1,0,0),radius*.244,.012,graphite,running))
    for j in range(6):
        a=j*2*math.pi/6
        pieces.append(cylinder('Rim_bolt_'+name+str(j),(sign*w*.97,radius*.38*math.sin(a),radius*.38*math.cos(a)),(1,0,0),.017,.014,alloy,running,12))
    for ob in pieces: ob.parent=pivot
    pivot['wheel_role']='carried spare' if spare else 'ground contact'
    pivot['tire_radius_m']=radius+.037
    return pivot


wheel_specs={'FL':((-1.18,-1.18,.552),.515,.49,-1),'FR':((1.18,-1.18,.552),.515,.49,1),
             'RL':((-1.18,1.03,.582),.545,.53,-1),'RR':((1.18,1.03,.582),.545,.53,1)}
for name,(pos,r,w,s) in wheel_specs.items(): wheel(name,pos,r,w,s)
spare_center=Vector((0,1.10,1.54))
spare_radius,spare_width=.365,.28
spare=wheel('SPARE',spare_center,spare_radius,spare_width,1,True)

# Double wishbones, ball joints, steering rods, and exposed orange coil-overs.
for s,side in [(-1,'L'),(1,'R')]:
    for prefix,y,z in [('F',-1.18,.552),('R',1.03,.582)]:
        outer=(s*.995,y,z)
        for level in (-.13,.08):
            for dy in (-.28,.28):
                bar(prefix+'_wishbone_'+side+str(level)+str(dy),(s*.32,y+dy,z+level*.7),
                    (s*1.00,y,z+level),.032 if level<0 else .028,graphite,running)
        bar(prefix+'_halfshaft_'+side,(s*.18,y,z-.025),outer,.035,alloy,running)
        cylinder(prefix+'_brake_disc_'+side,(s*.962,y,z),(1,0,0),.168,.035,steel,running)
        box(prefix+'_brake_caliper_'+side,(s*.96,y+.115,z+.095),(.10,.09,.16),.018,black,running)
        for dz in (-.13,.08): ball(prefix+'_ball_joint_'+side+str(dz),(s*1.00,y,z+dz),(.057,.057,.057),alloy,running,20,12)
        top=Vector((s*.63,y+(.27 if prefix=='F' else -.26),1.08 if prefix=='F' else 1.13))
        bottom=Vector((s*.95,y,.43 if prefix=='F' else .46))
        axis=(top-bottom).normalized()
        length=(top-bottom).length
        bar(prefix+'_shock_piston_'+side,bottom,top,.034,alloy,running)
        bar(prefix+'_shock_body_'+side,bottom+axis*.08,top-axis*.12,.068,black,running)
        for t in (.12,length-.09):
            cylinder(prefix+'_spring_seat_'+side+str(t),bottom+axis*t,axis,.106,.039,graphite,running)
        u=axis.cross(Vector((0,1,0))).normalized()
        v=axis.cross(u).normalized()
        coils=[]
        for j in range(145):
            t=j/144
            a=t*2*math.pi*6.25
            coils.append(bottom+axis*(.15+t*(length-.27))+.100*(u*math.cos(a)+v*math.sin(a)))
        tube(prefix+'_orange_coil_'+side,coils,.022,orange,running,sides=10)
        for label,p in [('top',top),('lower',bottom)]:
            cylinder(prefix+'_shock_eye_'+label+'_'+side,p,(0,1,0),.061,.09,graphite,running)
            bolt(prefix+'_shock_bolt_'+label+'_'+side,p+Vector((0,-.052,0)),(0,-1,0),.028,running)
    bar('Steering_tie_rod_'+side,(s*.24,-1.08,.66),(s*.985,-1.31,.62),.021,alloy,running)
box('Steering_rack',(0,-1.05,.655),(.47,.10,.105),.025,black,running)

# An exposed air-cooled engine beneath the carried spare.
box('Engine_crankcase',(0,.93,.86),(.44,.55,.44),.062,black,engine)
box('Gearbox',(0,1.18,.65),(.43,.38,.25),.044,graphite,engine)
for s,side in [(-1,'L'),(1,'R')]:
    cylinder('Engine_cylinder_'+side,(s*.32,1.04,.90),(1,0,0),.155,.34,graphite,engine)
    for j in range(8):
        cylinder('Cooling_fin_'+side+str(j),(s*(.18+.039*j),1.04,.90),(1,0,0),.168,.019,alloy,engine,24)
    box('Valve_cover_'+side,(s*.49,1.04,.90),(.075,.25,.24),.034,graphite,engine)
    for z in (.84,.96): bolt('Valve_cover_bolt_'+side+str(z),(s*.531,1.04,z),(s,0,0),.019,engine)
    path=spline([(s*.46,.97,.79),(s*.64,1.14,.73),(s*.77,1.39,.93),(s*.83,1.48,1.18)],6)
    tube('Exhaust_header_'+side,path,.048,graphite,engine,sides=24,caps=False)
    start=Vector((s*.75,1.36,.96))
    end=Vector((s*.92,1.56,1.40))
    axis=(end-start).normalized()
    tube('Open_muffler_'+side,[start,end],.092,alloy,engine,sides=40,caps=False)
    # A real lip and recessed bore leave the end visibly open.
    ring('Exhaust_tip_lip_'+side,end,axis,.083,.012,alloy,engine,48)
    cylinder('Exhaust_dark_bore_'+side,end-axis*.045,axis,.077,.006,black,engine)
    for t in (.18,.83): ring('Muffler_band_'+side,start+(end-start)*t,axis,.094,.013,graphite,engine,40)
    bar('Exhaust_support_'+side,(s*.56,1.29,.69),start+(end-start)*.40,.021,graphite,engine)
    for material_name,yy,radius,depth,mat in [('Lamp_housing',1.472,.103,.11,graphite),('Lamp_rim',1.535,.087,.022,alloy),('Lamp_lens',1.551,.071,.018,red)]:
        cylinder('Rear_'+material_name+'_'+side,(s*.285,yy,.992),(0,1,0),radius,depth,mat,details,40)
cylinder('Air_filter_neck',(0,.86,1.15),(0,0,1),.09,.15,graphite,engine)
cylinder('Air_filter_lid',(0,.86,1.235),(0,0,1),.143,.075,black,engine)
ring('Air_filter_orange_band',(0,.86,1.224),(0,0,1),.145,.013,orange,engine)

# Spare cradle and the broad orange retention strap, visible from the rear.
for s,side in [(-1,'L'),(1,'R')]:
    bar('Spare_cradle_'+side,(s*.24,.91,1.07),(s*.24,1.16,1.23),.030,graphite,frame)
bar('Spare_mount_axle',(0,.71,spare_center.z),spare_center,.055,graphite,frame)
sy,sz=spare_center.y,spare_center.z
sd,sh=spare_width*.5+.035,spare_radius+.042
strap_path=spline([(sy+sd*.78,sz-sh),(sy+sd,sz-sh*.60),(sy+sd,sz+sh*.60),
                   (sy+sd*.55,sz+sh),(sy-sd*.55,sz+sh),(sy-sd,sz+sh*.60),
                   (sy-sd,sz-sh*.60),(sy-sd*.55,sz-sh),(sy+sd*.78,sz-sh)],5)
sv=[]
for p in strap_path:
    for x in (-.052,.052): sv.append((x,p.x,p.y))
sf=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(strap_path)-1)]
strap=mesh('Spare_retention_strap',sv,sf,strapmat,details)
m=strap.modifiers.new('Woven strap thickness','SOLIDIFY')
m.thickness=.009
apply(strap,m)
bevel(strap,.006,2)
for x in (-.052,.052):
    bar('Buckle_side_'+str(x),(x,sy+sd+.017,sz-.07),(x,sy+sd+.017,sz+.11),.010,alloy,details)
for z in (sz-.07,sz+.11): bar('Buckle_cross_'+str(z),(-.052,sy+sd+.017,z),(.052,sy+sd+.017,z),.010,alloy,details)
bar('Buckle_tongue',(0,sy+sd+.021,sz+.05),(0,sy+sd+.024,sz-.04),.007,alloy,details)

for name,pos in [('Driver_Seat',offset),('Camera_Target',(0,.1,1.52)),('Item_Spawn',(0,1.55,1.57)),
                 ('Exhaust_L',(-.92,1.56,1.40)),('Exhaust_R',(.92,1.56,1.40))]:
    ob=empty('Dune_Socket_'+name,pos,root)
    ob.empty_display_type='ARROWS'
for c in kart_collections:
    for ob in c.objects:
        if ob.parent is None: parent(ob,root)
        if ob.type=='MESH': ob.data.validate()

# Pack the approved vehicle sheet without putting references in the runtime hierarchy.
im=bpy.data.images.load(str(ROOT/'art-source/concepts/racers/round-02/02-grit-v2.png'))
im.pack()
ob=bpy.data.objects.new('Dune_Concept_Reference',None)
refs.objects.link(ob)
ob.empty_display_type='IMAGE'
ob.data=im
ob.empty_display_size=4
ob.location=(5,0,2)
ob.rotation_euler=(math.pi/2,0,0)
ob.hide_render=True
refs.hide_viewport=True

# Actual Cycles review lighting with a neutral warm background.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.014))
ground=move(bpy.context.object,studio)
ground.name='Dune_Studio_Ground'
ground.data.materials.append(material('studio floor','EDE3D1',.75))
ground.is_shadow_catcher=True
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.86,.91,1,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
for name,pos,power,size,color in [('Key',(-4,-5,7),420,4,(1,.97,.92)),('Fill',(4,-3,4),210,4,(.90,.95,1)),('Rim',(1,4,5),400,3.5,(1,.96,.88))]:
    d=bpy.data.lights.new('Dune_'+name,'AREA')
    d.energy,d.shape,d.size,d.color=power,'DISK',size,color
    ob=bpy.data.objects.new(d.name,d)
    studio.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector((0,0,1.1))-ob.location).to_track_quat('-Z','Y').to_euler()
camera_specs={'hero':((5,-7,3.7),(0,-.1,1.13),4.65),'front':((0,-8,2.4),(0,-.1,1.15),4.25),
              'side':((8,-.05,2.25),(0,-.02,1.17),4.55),'rear':((0,8,3.0),(0,.10,1.16),4.35),
              'top':((0,0,9),(0,0,0),4.6)}
for name,(pos,target,scale) in camera_specs.items():
    d=bpy.data.cameras.new('Dune_Camera_'+name)
    d.type,d.ortho_scale='ORTHO',scale
    ob=bpy.data.objects.new(d.name,d)
    studio.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['Dune_Camera_hero']
scene.render.engine='CYCLES'
scene.cycles.samples=args.samples
scene.cycles.use_denoising=True
scene.render.resolution_x=args.resolution
scene.render.resolution_y=round(args.resolution*.82)
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.render.film_transparent=True
tree=bpy.data.node_groups.new('Dune Studio Composite','CompositorNodeTree')
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
layers=tree.nodes.new('CompositorNodeRLayers')
over=tree.nodes.new('CompositorNodeAlphaOver')
over.inputs['Background'].default_value=linear('F8F1E3')
out=tree.nodes.new('NodeGroupOutput')
tree.links.new(layers.outputs['Image'],over.inputs['Foreground'])
tree.links.new(over.outputs['Image'],out.inputs['Image'])
scene.compositing_node_group=tree
scene['asset_id']='grit-dune-hopper'
scene['driver_source']=str(DRIVER.relative_to(ROOT))
scene['concept']='art-source/concepts/racers/round-02/02-grit-v2.png'
scene['revision']=args.revision
scene['scope']='Dune Hopper visual model. Driver and seat are independent. Gameplay physics remains separate.'
select(root)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_perspective='CAMERA'
            space.shading.type='MATERIAL'
            space.overlay.show_overlays=False
path=OUT/('grit-dune-hopper-v'+args.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
stats={'source':str(path.relative_to(ROOT)),'driverOffset':list(offset),'wheelSpecs':wheel_specs,
       'kartTriangles':sum(len(p.vertices)-2 for c in kart_collections for ob in c.objects if ob.type=='MESH' for p in ob.data.polygons),
       'driverTriangles':45690,'kartMeshObjects':sum(ob.type=='MESH' for c in kart_collections for ob in c.objects)}
(REVIEW/'build-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('DUNE_HOPPER_BUILT '+json.dumps(stats),flush=True)
for view in args.views.split(','):
    if view=='none': continue
    scene.camera=bpy.data.objects['Dune_Camera_'+view]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('DUNE_HOPPER_RENDER '+view,flush=True)
