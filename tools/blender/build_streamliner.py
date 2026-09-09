"""Build Riff's Streamliner around the accepted seated driver.

Blender --background --factory-startup --python-exit-code 1 --python
tools/blender/build_streamliner.py -- --revision 01 --views hero,front,side,rear
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='01')
parser.add_argument('--views',default='hero,front,side,rear')
parser.add_argument('--samples',type=int,default=40)
parser.add_argument('--resolution',type=int,default=1200)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=ROOT/'art-source/blender/karts/streamliner'
REVIEW=OUT/'review'/('v'+args.revision)
REVIEW.mkdir(parents=True,exist_ok=True)
DRIVER=ROOT/'art-source/blender/characters/riff/riff-driver.blend'
bpy.ops.wm.open_mainfile(filepath=str(DRIVER))
scene=bpy.context.scene
scene.frame_set(1)
for obj in list(bpy.data.collections['STUDIO'].objects):
    bpy.data.objects.remove(obj,do_unlink=True)


def collection(name):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


bodywork=collection('STREAMLINER_BODYWORK')
running=collection('STREAMLINER_RUNNING_GEAR')
details=collection('STREAMLINER_DETAILS')
cockpit=collection('STREAMLINER_COCKPIT')
controls=collection('STREAMLINER_CONTROLS')
studio=bpy.data.collections['STUDIO']
root=bpy.data.objects.new('Streamliner_Root',None)
controls.objects.link(root)
root.empty_display_type='PLAIN_AXES'
root.empty_display_size=.30
root['asset_id']='riff-streamliner'
root['forward']='-Y, Z up, meters'
root['steering_degrees']=0.0
root['wheel_spin_degrees']=0.0
root.id_properties_ui('steering_degrees').update(min=-32,max=32,description='Front wheel steering')
root.id_properties_ui('wheel_spin_degrees').update(min=-3600,max=3600,description='Wheel rotation')


def parent(obj,p=root):
    bpy.context.view_layer.update()
    matrix=obj.matrix_world.copy()
    obj.parent=p
    obj.matrix_world=matrix


def move(obj,c):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    c.objects.link(obj)
    return obj


offset=Vector((0,.10,.38))
rig=bpy.data.objects['Riff_Driver_Rig']
rig.location+=offset
parent(rig)
for obj in list(bpy.data.collections['FIT_GUIDE_NOT_FOR_EXPORT'].objects):
    obj.location+=offset
    move(obj,cockpit)
    obj.name=obj.name.replace('_Guide','').replace('Wheel_Spoke','Steering_Spoke')
    parent(obj)


def linear(color):
    values=[int(color[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1,)


def mat(name,color,rough=.4,metal=0,coat=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=linear(color)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=linear(color)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.24
    return m


ivory=mat('Streamliner | ivory enamel','EEE2C8',.30,.12,.22)
teal=mat('Streamliner | petrol teal enamel','157B86',.32,.28,.25)
coral=mat('Streamliner | coral stripe','E9785E',.36,.08,.18)
rubber=mat('Streamliner | tire rubber','252628',.62)
black=mat('Streamliner | intake and cockpit','171E21',.66)
chrome=mat('Streamliner | brushed aluminum','B5BBBC',.26,.78)
gold=mat('Streamliner | warm alloy','BBAC84',.33,.72)
steel=mat('Streamliner | dark mechanical steel','424D50',.38,.60)
glass=mat('Streamliner | smoked windscreen','859594',.16,.08)
glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.68
glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.46


def mesh(name,verts,faces,material,c=details):
    data=bpy.data.meshes.new(name+'_Mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    c.objects.link(obj)
    if material:
        data.materials.append(material)
    for p in data.polygons:
        p.use_smooth=True
    return obj


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def apply(obj,modifier):
    select(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def ball(name,pos,scale,material,c=details,segments=24,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    o=move(bpy.context.object,c)
    o.name=name
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth=True
    return o


def box(name,pos,size,radius,material,c=details):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=move(bpy.context.object,c)
    o.name=name
    o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:
        o.data.materials.append(material)
    b=o.modifiers.new('Rounded edges','BEVEL')
    b.width=radius
    b.segments=4
    apply(o,b)
    n=o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    apply(o,n)
    return o


def catmull(points,steps=8):
    ps=[Vector(p) for p in points]
    values=[]
    for i in range(len(ps)-1):
        a,b,c,d=ps[max(0,i-1)],ps[i],ps[i+1],ps[min(len(ps)-1,i+2)]
        for j in range(steps):
            t=j/steps
            values.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return values+[ps[-1]]


def tube(name,points,radius,material,c=details,sides=12,closed=False,caps=True):
    points=[Vector(p) for p in points]
    verts=[]
    radii=[radius]*len(points) if isinstance(radius,(int,float)) else radius
    for i,p in enumerate(points):
        d=points[(i+1)%len(points) if closed else min(i+1,len(points)-1)]-points[(i-1)%len(points) if closed else max(i-1,0)]
        d.normalize()
        b=d.cross(Vector((0,0,1)))
        if b.length<.05:
            b=d.cross(Vector((0,1,0)))
        b.normalize()
        n=d.cross(b).normalized()
        for j in range(sides):
            a=2*math.pi*j/sides
            verts.append(p+radii[i]*(b*math.cos(a)+n*math.sin(a)))
    faces=[]
    for i in range(len(points) if closed else len(points)-1):
        for j in range(sides):
            faces.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%len(points))*sides+(j+1)%sides,((i+1)%len(points))*sides+j))
    if not closed and caps:
        faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,material,c)


def rod(name,a,b,radius,material,c=running):
    return tube(name,[a,b],radius,material,c,sides=12)


def lathe_x(name,center,profile,material,c=running,segments=64):
    verts=[]
    for x,r in profile:
        for i in range(segments):
            a=2*math.pi*i/segments
            verts.append((center[0]+x,center[1]+r*math.cos(a),center[2]+r*math.sin(a)))
    faces=[]
    for j in range(len(profile)):
        for i in range(segments):
            faces.append((j*segments+i,j*segments+(i+1)%segments,((j+1)%len(profile))*segments+(i+1)%segments,((j+1)%len(profile))*segments+i))
    return mesh(name,verts,faces,material,c)


# Cigar-shaped shell: cream above the seam, teal below; a true open cockpit.
profile=catmull([(-2.42,.095,.47,.057),(-2.34,.16,.48,.09),(-2.10,.30,.54,.19),
                 (-1.58,.43,.65,.29),(-.94,.56,.74,.38),(-.48,.66,.76,.40),
                 (.12,.73,.74,.38),(.74,.72,.75,.43),(1.18,.59,.71,.36),
                 (1.55,.37,.64,.22),(1.78,.025,.59,.04)],8)


def section(y):
    for a,b in zip(profile[:-1],profile[1:]):
        if a[0]<=y<=b[0]:
            t=(y-a[0])/(b[0]-a[0])
            return tuple(a[k]*(1-t)+b[k]*t for k in (1,2,3))
    p=profile[0] if y<profile[0][0] else profile[-1]
    return p[1],p[2],p[3]


def top(x,y):
    rx,zc,rz=section(y)
    return zc+rz*math.sqrt(max(.001,1-(x/rx)**2))


N=96
verts=[(rx*math.cos(2*math.pi*i/N),y,zc+rz*math.sin(2*math.pi*i/N)) for y,rx,zc,rz in profile for i in range(N)]
faces=[(j*N+i,(j+1)*N+i,(j+1)*N+(i+1)%N,j*N+(i+1)%N) for j in range(len(profile)-1) for i in range(N)]
faces += [tuple(range(N)),tuple((len(profile)-1)*N+i for i in reversed(range(N)))]
shell=mesh('Streamliner_Monocoque',verts,faces,ivory,bodywork)
shell.data.materials.append(teal)
for i,p in enumerate(shell.data.polygons):
    if i<(len(profile)-1)*N:
        p.material_index=0 if math.sin(2*math.pi*((i%N)+.5)/N)>-.04 else 1


def cut(target,cutter,label):
    m=target.modifiers.new(label,'BOOLEAN')
    m.operation='DIFFERENCE'
    m.solver='EXACT'
    m.object=cutter
    apply(target,m)
    bpy.data.objects.remove(cutter,do_unlink=True)


bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=2,location=(0,-.065,1.44))
cutter=bpy.context.object
cutter.scale=(.625,.685,1)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
cut(shell,cutter,'Open cockpit')
intake=box('Intake cutter',(0,-2.42,.477),(.145,.18,.040),.018,None)
cut(shell,intake,'Nose intake')
for sign in (-1,1):
    vent=box('Vent cutter',(sign*.706,.44,.878),(.27,.29,.14),.045,None)
    cut(shell,vent,'Side cooling recess')
    box('Side_vent_interior',(sign*.605,.44,.878),(.026,.27,.12),.039,black)
    for j in range(3):
        rod('Side_vent_louver',(sign*.62,.355+j*.07,.834),(sign*.62,.355+j*.07,.916),.009,steel,details)
shell.data.validate()
for p in shell.data.polygons:
    p.use_smooth=True

# Cockpit trim follows the shell rather than floating as a flat ring.
rim=[]
for i in range(128):
    a=2*math.pi*i/128
    x,y=.626*math.cos(a),-.065+.686*math.sin(a)
    rim.append((x,y,top(x,y)+.01))
tube('Cockpit_polished_coaming',rim,.023,chrome,cockpit,sides=12,closed=True)
inner_verts=[]
for zmode in (0,1):
    for x,y,z in rim:
        ix,iy=x*.987,-.065+(y+.065)*.987
        rx,zc,rz=section(iy)
        inside_floor=max(.485,zc-rz*math.sqrt(max(.001,1-(ix/rx)**2))+.025)
        inner_verts.append((ix,iy,inside_floor if zmode==0 else z-.014))
mesh('Cockpit_inner_tub',inner_verts,[(i,(i+1)%128,(i+1)%128+128,i+128) for i in range(128)],black,cockpit)
box('Cockpit_floor',(0,.02,.53),(.81,.98,.07),.05,black,cockpit)
rod('Steering_column',(0,-.554,1.12),(0,-.50,.76),.023,steel,cockpit)

# Coral center stripe conforms to the hood and the tapering tail.
for label,start,end in [('Hood',-2.355,-.759),('Tail',.643,1.71)]:
    sv=[]
    for i in range(97):
        y=start+(end-start)*i/96
        rx,_,_=section(y)
        half=min(.062,rx*.55)
        for j in range(9):
            x=-half+2*half*j/8
            sv.append((x,y,top(x,y)+.003))
    mesh(label+'_Coral_Stripe',sv,[(i*9+j,i*9+j+1,(i+1)*9+j+1,(i+1)*9+j) for i in range(96) for j in range(8)],coral,bodywork)
box('Nose_intake_darkness',(0,-2.375,.477),(.135,.023,.033),.012,black)
lip=[(.078*math.cos(2*math.pi*i/48),-2.421,.477+.024*math.sin(2*math.pi*i/48)) for i in range(48)]
tube('Nose_intake_lip',lip,.0065,gold,details,sides=8,closed=True)

# Small wind deflector, just above the front coaming.
wv=[]
for level in (0,1):
    for i in range(49):
        a=-math.pi/2-.82+1.64*i/48
        x,y=.627*math.cos(a),-.065+.689*math.sin(a)
        z=top(x,y)+.025+level*(.12*math.sin(math.pi*i/48)**.45)
        wv.append((x,y+.025*level,z))
wind=mesh('Curved_smoke_windscreen',wv,[(i,i+1,i+50,i+49) for i in range(48)],glass,cockpit)
solid=wind.modifiers.new('Glass thickness','SOLIDIFY')
solid.thickness=.006
apply(wind,solid)
tube('Windscreen_upper_frame',wv[49:],.008,chrome,cockpit,sides=8)

# Four wheel assemblies have independent steering and spin pivots.
wheel_specs=[]
for axle,y,r,width,track in [('F',-1.51,.435,.32,1.015),('R',.91,.603,.46,1.055)]:
    for sign,side in [(-1,'L'),(1,'R')]:
        name=axle+side
        center=Vector((sign*track,y,r))
        steer=bpy.data.objects.new('Steer_'+name,None)
        controls.objects.link(steer)
        steer.location=center
        steer.empty_display_size=.17
        parent(steer)
        if axle=='F':
            curve=steer.driver_add('rotation_euler',2).driver
            var=curve.variables.new()
            var.name='angle'
            var.targets[0].id=root
            var.targets[0].data_path='["steering_degrees"]'
            curve.expression='angle * 0.0174532925199433'
        spin=bpy.data.objects.new('Spin_'+name,None)
        controls.objects.link(spin)
        spin.location=center
        spin.empty_display_size=.13
        parent(spin,steer)
        curve=spin.driver_add('rotation_euler',0).driver
        var=curve.variables.new()
        var.name='angle'
        var.targets[0].id=root
        var.targets[0].data_path='["wheel_spin_degrees"]'
        curve.expression='angle * 0.0174532925199433'
        before=set(running.objects)
        cross=[(-width*.50,r*.59),(-width*.55,r*.68),(-width*.54,r*.83),(-width*.46,r*.95)]
        for j in range(33):
            x=-width*.36+width*.72*j/32
            radius=r*(1-.025*(x/(width*.36))**4)
            for groove in (-.20*width,0,.20*width):
                radius-=.010*math.exp(-((x-groove)/(.014*width))**2)
            cross.append((x,radius))
        cross += [(width*.46,r*.95),(width*.54,r*.83),(width*.55,r*.68),(width*.50,r*.59)]
        lathe_x('Tire_'+name,center,cross,rubber)
        outer=sign*width*.505
        # Deep teal dish with an ivory shoulder and a warm metal center.
        rimprof=[(-width*.46,r*.59),(-width*.46,r*.45),(width*.46,r*.45),(width*.46,r*.59)]
        lathe_x('Rim_barrel_'+name,center,rimprof,steel,segments=48)
        rimfront=[(outer,r*.602),(outer+sign*.012,r*.615),(outer+sign*.023,r*.603),
                  (outer+sign*.023,r*.54),(outer+sign*.012,r*.528),(outer,r*.54)]
        lathe_x('Rim_ivory_lip_'+name,center,rimfront,ivory,segments=64)
        dish=[(outer+sign*.009,r*.536),(outer-sign*.043,r*.40),(outer-sign*.053,r*.15),
              (outer-sign*.06,r*.10),(outer-sign*.069,r*.52)]
        lathe_x('Rim_teal_dish_'+name,center,dish,teal,segments=64)
        for radius in (r*.538,r*.39):
            ring=[(center.x+outer+sign*.012,center.y+radius*math.cos(2*math.pi*i/64),center.z+radius*math.sin(2*math.pi*i/64)) for i in range(64)]
            tube('Rim_alloy_ring_'+name,ring,.010,gold,running,sides=8,closed=True)
        ball('Domed_hub_'+name,(center.x+outer-sign*.009,center.y,center.z),(.046,r*.30,r*.30),ivory,running,32,16)
        for i in range(5):
            a=2*math.pi*i/5
            ball('Hub_bolt_'+name,(center.x+outer+sign*.016,center.y+r*.347*math.cos(a),center.z+r*.347*math.sin(a)),(.012,.011,.011),chrome,running,12,8)
        for obj in set(running.objects)-before:
            parent(obj,spin)
        wheel_specs.append({'id':name,'center':list(center),'radius':r,'width':width,'steer':steer.name,'spin':spin.name})

# Visible wishbones, tie rods, upright joints, and six-turn coil-over springs.
for sign,side in [(-1,'L'),(1,'R')]:
    hub=Vector((sign*.941,-1.51,.435))
    for height,back,forward in [(.43,-1.26,-1.94),(.61,-1.32,-1.80)]:
        for anchor_y in (back,forward):
            rod('Front_wishbone_'+side,(sign*.31,anchor_y,height),hub,.022,chrome)
    rod('Steering_tie_rod_'+side,(sign*.32,-1.35,.56),(sign*.94,-1.39,.43),.016,steel)
    ball('Front_upright_'+side,hub,(.048,.058,.076),steel,running)
    a=Vector((sign*.395,-1.23,.76))
    b=Vector((sign*.875,-1.50,.45))
    rod('Damper_'+side,a,b,.022,chrome)
    d=(b-a).normalized()
    u=d.cross(Vector((0,0,1))).normalized()
    v=d.cross(u).normalized()
    helix=[a+(b-a)*(.14+.67*i/96)+.043*(u*math.cos(12*math.pi*i/96)+v*math.sin(12*math.pi*i/96)) for i in range(97)]
    tube('Front_coil_spring_'+side,helix,.011,steel,running,sides=8)
    rod('Rear_axle_'+side,(sign*.35,.91,.603),(sign*1.02,.91,.603),.045,steel)
    for yy in (.65,1.14):
        rod('Rear_radius_rod_'+side,(sign*.42,yy,.48),(sign*.92,.91,.59),.025,chrome)
box('Rear_differential',(0,.91,.56),(.40,.36,.27),.06,steel,running)

# Twin rearward, upswept pipes: open dark bores, bright rims, and teal collars.
for sign,side in [(-1,'L'),(1,'R')]:
    points=catmull([(sign*.40,.61,.66),(sign*.47,.82,.86),(sign*.48,1.08,1.18),(sign*.49,1.34,1.43)],8)
    tube('Exhaust_pipe_'+side,points,.083,chrome,details,sides=24,caps=False)
    end=points[-1]
    d=(points[-1]-points[-2]).normalized()
    u=d.cross(Vector((1,0,0))).normalized()
    v=d.cross(u).normalized()
    ev=[]
    for radius,depth in [(.093,0),(.093,-.19),(.066,-.19),(.066,.004)]:
        for i in range(48):
            a=2*math.pi*i/48
            ev.append(end+d*depth+radius*(u*math.cos(a)+v*math.sin(a)))
    ef=[(j*48+i,j*48+(i+1)%48,((j+1)%4)*48+(i+1)%48,((j+1)%4)*48+i) for j in range(4) for i in range(48)]
    mesh('Hollow_exhaust_tip_'+side,ev,ef,chrome)
    # The inset dark disk hides the capped construction pipe well inside the bore.
    disk=[end-d*.025]+[end-d*.025+.066*(u*math.cos(2*math.pi*i/48)+v*math.sin(2*math.pi*i/48)) for i in range(48)]
    mesh('Exhaust_bore_'+side,disk,[(0,1+i,1+(i+1)%48) for i in range(48)],black)
    for dist in (.15,.18):
        loop=[end-d*dist+.091*(u*math.cos(2*math.pi*i/48)+v*math.sin(2*math.pi*i/48)) for i in range(48)]
        tube('Exhaust_teal_collar_'+side,loop,.012,teal,sides=8,closed=True)

for sign in (-1,1):
    for y in (-1.82,-1.40,-.98,-.48,.05,.56,1.08,1.38):
        rx,zc,rz=section(y)
        ball('Body_fastener',(sign*rx*.988,y,zc+.13*rz),(.008,.009,.009),gold,segments=12,rings=8)
    # A subtle panel seam below the cockpit emphasizes the enamel construction.
    seam=[]
    for i in range(49):
        y=-.50+1.89*i/48
        rx,zc,rz=section(y)
        seam.append((sign*rx*.999,y,zc+.016))
    tube('Waist_panel_seam',seam,.0035,gold,sides=6)

# Explicit attachment points are useful when integrating the visual asset into gameplay.
for name,pos in [('Driver_Seat',(0,.10,.38)),('Item_Spawn',(0,1.77,.72)),('Camera_Target',(0,.10,1.12)),
                 ('Exhaust_L',(-.49,1.34,1.43)),('Exhaust_R',(.49,1.34,1.43))]:
    o=bpy.data.objects.new('Socket_'+name,None)
    controls.objects.link(o)
    o.location=pos
    o.empty_display_type='ARROWS'
    o.empty_display_size=.13
    parent(o)

for c in (bodywork,running,details,cockpit):
    for obj in c.objects:
        if obj.parent is None:
            parent(obj)
        if obj.type=='MESH':
            obj.data.validate()

# A soft studio, with camera-independent ivory background and a shadowed floor.
groundmat=mat('Streamliner studio | warm ivory','EEE5D5',.75)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006))
ground=move(bpy.context.object,studio)
ground.name='Kart_Studio_Ground'
ground.data.materials.append(groundmat)
scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes
nodes.clear()
world=nodes.new('ShaderNodeBackground')
world.inputs['Color'].default_value=(.75,.85,1,1)
world.inputs['Strength'].default_value=.35
out=nodes.new('ShaderNodeOutputWorld')
scene.world.node_tree.links.new(world.outputs[0],out.inputs[0])


def area(name,pos,power,size,color):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector((0,-.25,.9))-obj.location).to_track_quat('-Z','Y').to_euler()


area('Kart_Key',(-3,-4,6),650,5,(1,.95,.87))
area('Kart_Fill',(4,-2,4),350,4,(.80,.92,1))
area('Kart_Rim',(0,4,5),800,4,(1,.95,.84))
camera_specs={'hero':((5,-7,3.25),(0,-.38,1.02),5.10),
              'front':((0,-8,2.9),(0,-.20,1.02),4.55),
              'side':((8,-.3,2.0),(0,-.30,1.02),5.15),
              'rear':((0,8,3.1),(0,.05,1.03),4.60),
              'top':((0,-.2,8),(0,-.2,0),5.0)}
for name,(pos,target,scale) in camera_specs.items():
    data=bpy.data.cameras.new('Kart_Camera_'+name)
    obj=bpy.data.objects.new(data.name,data)
    studio.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'
    data.ortho_scale=scale
scene.camera=bpy.data.objects['Kart_Camera_hero']
scene.render.engine='CYCLES'
scene.cycles.samples=args.samples
scene.cycles.use_denoising=True
scene.render.resolution_x=args.resolution
scene.render.resolution_y=round(args.resolution*.78)
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.film_transparent=True
ground.is_shadow_catcher=True
tree=bpy.data.node_groups.new('Streamliner studio composite','CompositorNodeTree')
scene.compositing_node_group=tree
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
layers=tree.nodes.new('CompositorNodeRLayers')
over=tree.nodes.new('CompositorNodeAlphaOver')
over.inputs['Background'].default_value=(2.15,1.96,1.66,1)
output=tree.nodes.new('NodeGroupOutput')
tree.links.new(layers.outputs['Image'],over.inputs['Foreground'])
tree.links.new(over.outputs['Image'],output.inputs['Image'])
scene['asset_id']='riff-streamliner'
scene['vehicle_revision']=args.revision
scene['driver_source']=str(DRIVER.relative_to(ROOT))
scene['concept_source']='art-source/concepts/racers/round-02/01-riff-v2.png'
scene['scope']='Riff and Streamliner visual assembly; gameplay physics not implemented'
select(root)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_perspective='CAMERA'
            space.shading.type='MATERIAL'
            space.overlay.show_overlays=False
path=OUT/('riff-streamliner-v'+args.revision+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
stats={'revision':args.revision,'source':str(path.relative_to(ROOT)),
       'kartTriangles':sum(len(p.vertices)-2 for c in (bodywork,running,details,cockpit) for o in c.objects if o.type=='MESH' for p in o.data.polygons),
       'driverTriangles':sum(len(p.vertices)-2 for o in bpy.data.collections['RIFF_DRIVER'].objects if o.type=='MESH' for p in o.data.polygons),
       'wheelAssemblies':wheel_specs,'driverOffset':list(offset),'units':'meters'}
(REVIEW/'build-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('STREAMLINER_BUILD '+json.dumps(stats),flush=True)
for view in args.views.split(','):
    scene.camera=bpy.data.objects['Kart_Camera_'+view]
    scene.render.filepath=str(REVIEW/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    print('STREAMLINER_RENDER '+view,flush=True)
