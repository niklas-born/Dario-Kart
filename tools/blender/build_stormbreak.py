"""Build original Stormbreak scenery, road and editable Blender source from the approved V2 footprint.
Run in Blender background mode. Writes only generated stormbreak-prototype outputs.
"""
import bpy, bmesh, json, math, random, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'art-source/concepts/tracks/stormbreak-v2/layout.json'
OUT=ROOT/'game/Assets/_DarioKart/Art/Models/Tracks/stormbreak-prototype'
ART=ROOT/'art-source/blender/tracks/stormbreak-prototype'
for p in [OUT,ART,ART/'review']: p.mkdir(parents=True,exist_ok=True)
data=json.loads(SRC.read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(27)
colors={'Asphalt':(.085,.115,.135,1),'Cream':(.82,.77,.62,1),'Red':(.8,.19,.07,1),'Teal':(.025,.34,.39,1),'Orange':(.95,.32,.06,1),'Grass':(.24,.36,.13,1),'Rock':(.19,.23,.25,1),'RockLight':(.28,.31,.30,1),'Glass':(.025,.12,.18,1),'Metal':(.11,.15,.18,1),'Yellow':(1,.7,.12,1),'White':(.96,.95,.8,1),'Water':(.035,.32,.45,1),'Leaves':(.15,.29,.095,1)}
mats={}
for n,c in colors.items():
 m=bpy.data.materials.new(n);m.diffuse_color=c;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.72
 mats[n]=m
buckets={}
def mesh(group,mat,vs,fs):
 key=(group,mat);v,f=buckets.setdefault(key,([],[]));off=len(v)
 v.extend([(-x,-z,y) for x,y,z in vs]);f.extend([tuple(off+i for i in reversed(face)) for face in fs])
def box(group,p,size,mat,yaw=0):
 x,y,z=p;a,b,c=[s/2 for s in size];co,si=math.cos(yaw),math.sin(yaw)
 vs=[]
 for dx,dy,dz in [(-a,-b,-c),(a,-b,-c),(a,-b,c),(-a,-b,c),(-a,b,-c),(a,b,-c),(a,b,c),(-a,b,c)]:
  vs.append((x+dx*co+dz*si,y+dy,z-dx*si+dz*co))
 mesh(group,mat,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
def beam(group,a,b,r,mat,sides=8):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();ref=Vector((0,1,0)) if abs(d.y)<.9 else Vector((1,0,0));u=d.cross(ref).normalized();v=d.cross(u)
 vs=[tuple(p+r*(math.cos(t*2*math.pi/sides)*u+math.sin(t*2*math.pi/sides)*v)) for p in [a,b] for t in range(sides)]
 fs=[tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
 mesh(group,mat,vs,fs)
def h(z):
 t=max(0,min(1,(z-45)/280));return 16*t*t*(3-2*t)
raw=data['centerline_xz_m']; dist=[0]
for a,b in zip(raw,raw[1:]):dist.append(dist[-1]+math.dist(a,b))
N=1080;route=[];j=0
for i in range(N):
 d=i*dist[-1]/N
 while j+1<len(dist) and dist[j+1]<d:j+=1
 t=(d-dist[j])/(dist[j+1]-dist[j]);x,z=[raw[j][k]*(1-t)+raw[j+1][k]*t for k in range(2)]
 route.append(Vector((x,h(z)+.25,z)))
sides=[]
for i,p in enumerate(route):
 d=route[(i+1)%N]-route[(i-1)%N];sides.append(Vector((d.z,0,-d.x)).normalized())
def strip(group,mat,inner,outer,dy=0,selected=None):
 vs=[];fs=[]
 for i in range(N):
  if selected and not selected(i):continue
  j=(i+1)%N;k=len(vs)
  vs.extend([tuple(route[t]+sides[t]*side+Vector((0,dy,0))) for t,side in [(i,inner),(j,inner),(j,outer),(i,outer)]])
  fs.append((k,k+1,k+2,k+3))
 mesh(group,mat,vs,fs)
strip('Road','Asphalt',-9,9)
for sign in [-1,1]:
 strip('Shoulder','Cream',sign*9,sign*11,-.015)
 for parity,mat in [(0,'Cream'),(1,'Red')]:strip('Curbs',mat,sign*9,sign*9.85,.035,lambda i,p=parity:(i//3)%2==p)
 strip('EdgePaint','White',sign*8.72,sign*8.9,.012)
 # A solid closed safety wall and top teal rail, including start seam.
 for i in range(N):
  j=(i+1)%N;a=route[i]+sides[i]*sign*10.7;b=route[j]+sides[j]*sign*10.7
  d=b-a; yaw=math.atan2(d.x,d.z)
  box('Barrier',(a+b)/2+Vector((0,.48,0)),(.42,.96,d.length+.03),'Cream',yaw)
  beam('SafetyRail',a+Vector((0,1.15,0)),b+Vector((0,1.15,0)),.12,'Teal',6)
  if i%6==0:beam('RailPosts',a+Vector((0,.8,0)),a+Vector((0,1.28,0)),.12,'Teal',6)
strip('CenterDashes','Yellow',-.12,.12,.014,lambda i:i%8<3)
# Dry land fully supports the road. Surface follows the same smooth elevation function.
vs=[];fs=[]
xs=list(range(-245,566,10));zs=list(range(-65,446,10))
for z in zs:
 for x in xs:vs.append((x,h(z),z))
for k in range(len(zs)-1):
 for i in range(len(xs)-1):
  a=k*len(xs)+i;fs.append((a,a+len(xs),a+len(xs)+1,a+1))
mesh('Terrain','Grass',vs,fs)
box('Sea',(130,-4,-530),(2300,1,920),'Water')
box('Quay',(160,-.13,-32),(660,.4,48),'Cream')
box('Seawall',(160,-2,-57),(660,5,1.2),'Cream')
# Start line and reusable gantry.
for row in range(2):
 for k in range(18):box('Finish',(row*.65,.28,-8.5+k),(.65,.045,1),'White' if (row+k)%2==0 else 'Metal')
for z in [-11.7,11.7]:
 box('Gantry',(-3,4.7,z),(.9,9.4,.9),'Teal')
 for yy in [1,4,7]:beam('Gantry',(-3,yy,z-.5),(-3,yy+2,z+.5),.11,'Cream')
box('Gantry',(-3,8.8,0),(1.1,2.1,24.4),'Teal')
for z in [-3,-1.5,0,1.5,3]:box('StartLights',(-3.7,7.8,z),(.3,.42,.6),'Yellow')
# Three-door workshop and separate orange control tower.
box('Workshop',(78,5.5,34),(50,11,20),'Cream')
box('WorkshopRoof',(78,11.35,34),(52,.7,22),'Teal')
for x in [62,78,94]:
 box('GarageDoors',(x,3.6,23.8),(12,7,.25),'Teal')
 for yy in [1,2,3,4,5,6]:box('DoorSlats',(x,yy,23.61),(11.7,.06,.06),'Metal')
 box('DoorLamps',(x,8.1,23.4),(2,.4,.4),'Yellow')
for x in [64,89]:box('RoofVents',(x,12,34),(5,1.1,4),'Metal')
box('Tower',(134,7,35),(12,14,12),'Orange')
box('TowerCab',(134,15.6,35),(16,5,16),'Orange')
for z in [26.8,43.2]:box('TowerWindows',(134,15.7,z),(14,3,.12),'Glass')
for x in [125.8,142.2]:box('TowerWindows',(x,15.7,35),(.12,3,14),'Glass')
box('TowerRoof',(134,18.4,35),(17,.6,17),'Cream')
for x in [130,137]:beam('Antennas',(x,18.5,35),(x,24,35),.13,'Metal')
# Turbine plant outside northeast side, with fan grilles and orange pipework.
px,pz=455,337;by=h(pz)
box('Station',(px,by+11,pz),(58,22,42),'Cream')
box('StationRoof',(px,by+24,pz),(60,6,43),'Teal')
for x in [px-17,px+17]:
 beam('Exhausts',(x,by+22,pz+9),(x,by+42,pz+9),2,'Orange',12)
 beam('ExhaustCaps',(x,by+40,pz+9),(x,by+42,pz+9),2.7,'Metal',12)
for z in [pz-12,pz+12]:
 c=Vector((px-29.3,by+11,z));beam('FanHousing',c,c+Vector((-.6,0,0)),7.3,'Metal',24)
 beam('FanHub',c+Vector((-.8,0,0)),c+Vector((-1.2,0,0)),1.3,'Orange',12)
 for k in range(8):
  a=k*math.pi/4;u=Vector((0,math.cos(a),math.sin(a)))
  beam('FanBlades',c+Vector((-1,0,0))+u*1.4,c+Vector((-1,0,0))+u*6.3,.65,'Cream',4)
# Two cranes safely on the quay apron.
for x in [285,345]:
 z=-31;box('CraneBase',(x,1.5,z),(10,3,10),'Orange')
 for dx,dz in [(-4,-4),(4,-4),(-4,4),(4,4)]:beam('CraneLegs',(x+dx,3,z+dz),(x+dx*.5,12,z+dz*.5),.55,'Orange')
 box('CraneCab',(x,13,z),(7,5,7),'Orange');box('CraneGlass',(x,13.5,z+3.55),(5,2.7,.13),'Glass')
 a=Vector((x,16,z));b=Vector((x+5,34,z-16))
 for dx in [-1.2,1.2]:beam('CraneBoom',a+Vector((dx,0,0)),b+Vector((dx,0,0)),.5,'Orange')
 beam('CraneCable',b,(b.x,9,b.z),.09,'Metal');beam('CraneBrace',(x-3,15,z+1),b,.15,'Metal')
# Containers and lamps.
for x,z in [(180,33),(211,38),(290,-46),(355,-44),(395,-36),(-95,244)]:
 y=h(z);box('Containers',(x,y+2.7,z),(11,5.4,5),'Orange' if x%2 else 'Teal')
 for dx in range(-5,6):box('ContainerRibs',(x+dx,y+2.7,z-2.55),(.12,5.4,.12),'Cream')
for i in range(0,N,22):
 p=route[i]+sides[i]*12.6
 beam('Lamps',p,p+Vector((0,6,0)),.14,'Teal');box('LampHead',p+Vector((0,6,0)),(1.5,.35,.7),'White')
# Sparse infield rock clusters, always clear of road and main scenery.
for n in range(150):
 x=random.uniform(-195,420);z=random.uniform(55,395)
 if min((x-p.x)**2+(z-p.z)**2 for p in route)<25**2:continue
 if -140<x<-70 and 220<z<300:continue
 y=h(z);r=random.uniform(2.5,7);height=random.uniform(3,12);v=[]
 for yy,factor in [(y-.2,1),(y+height*.7,.82),(y+height,.35)]:
  for k in range(6):
   a=k*math.pi/3;v.append((x+math.cos(a)*r*factor,yy,z+math.sin(a)*r*factor))
 faces=[tuple(range(12,18))]+[(j*6+k,j*6+(k+1)%6,(j+1)*6+(k+1)%6,(j+1)*6+k) for j in range(2) for k in range(6)]
 mesh('RockClusters','RockLight' if n%3==0 else 'Rock',v,faces)
# Build editable source grouped by asset part and material, with road collision groups retained.
objects=[]
for (group,mat),(v,f) in buckets.items():
 me=bpy.data.meshes.new(group);me.from_pydata(v,[],f);me.update()
 ob=bpy.data.objects.new(group+'__'+mat,me);bpy.context.collection.objects.link(ob);me.materials.append(mats[mat]);objects.append(ob)
 # Recalculate outward normals independent of authored coordinate handedness.
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
# Open surfaces must face upward: Blender's volume-oriented consistency operator
# can flip isolated quads on hills. Explicitly orient these after recalculation.
for ob in objects:
 if ob.name.split('__')[0] in ['Road','Shoulder','Curbs','EdgePaint','CenterDashes','Terrain']:
  bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
  bmesh.ops.reverse_faces(bm,faces=[f for f in bm.faces if f.normal.z<0])
  bm.to_mesh(ob.data);bm.free();ob.data.update()
bpy.context.scene.unit_settings.system='METRIC'
# Save source before exporting; all parts remain editable mesh objects.
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'stormbreak-prototype.blend'))
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.fbx(filepath=str(OUT/'stormbreak.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,path_mode='STRIP')
length=sum((route[(i+1)%N]-p).length for i,p in enumerate(route))
report={'route':[{'x':p.x,'y':p.y,'z':p.z} for p in route],'checkpoints':[i*N//12 for i in range(12)],'widthMeters':18,'lengthMeters':length,'elevationMeters':16,'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'materials':[{'name':n,'color':list(c)} for n,c in colors.items()],'objects':len(objects),'triangles':sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons)}
(OUT/'stormbreak.json').write_text(json.dumps(report,indent=2));(ART/'build-report.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ['route','materials']},indent=2))
print('STORMBREAK EXPORTED',length,len(objects),report['triangles'])
