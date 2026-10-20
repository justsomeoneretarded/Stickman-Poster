"""Real Blender geometry and keyed 24-FPS acting study. Run with blender -b --python ... -- ..."""
import bpy,math,sys,argparse,json,time,random
from mathutils import Vector
from pathlib import Path
P=math.pi
random.seed(7)
args=argparse.ArgumentParser();args.add_argument('--out',required=True);args.add_argument('--width',type=int,default=960);args.add_argument('--samples',type=int,default=16);args.add_argument('--engine',choices=['CYCLES','BLENDER_EEVEE_NEXT'],default='CYCLES');args.add_argument('--start',type=int,default=1);args.add_argument('--end',type=int,default=192);args.add_argument('--still',type=int);args.add_argument('--save-only',action='store_true');args.add_argument('--denoise',action='store_true');args.add_argument('--portrait',action='store_true')
a=args.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine=a.engine;sc.cycles.samples=a.samples;sc.cycles.use_denoising=a.denoise;sc.cycles.max_bounces=5;sc.cycles.diffuse_bounces=2;sc.cycles.glossy_bounces=2;sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.resolution_x=a.width;sc.render.resolution_y=round(a.width*(16/9 if a.portrait else 9/16)/2)*2;sc.render.resolution_percentage=100;sc.render.fps=24;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=192
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.view_settings.view_transform='AgX';sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.008,.012,.02,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
if hasattr(sc,'eevee') and hasattr(sc.eevee,'taa_render_samples'):sc.eevee.taa_render_samples=a.samples

def mat(name,col,rough=.6,cloth=False,metal=0,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
 if cloth:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=125;tex.inputs['Roughness'].default_value=.8
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.012;m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
skin=mat('warm ivory clay',(.67,.51,.33),.68,True);shirt=mat('Maya muted taupe cotton',(.19,.12,.075),.87,True);pants=mat('warm charcoal trousers',(.075,.06,.048),.85,True);scarf=mat('charcoal knit scarf',(.06,.048,.036),.95,True);hair=mat('chestnut hair',(.065,.023,.008),.77);hair2=mat('hair amber strands',(.11,.045,.015),.6);white=mat('ivory eyes',(.83,.78,.65),.27);iris=mat('warm brown iris',(.15,.055,.015),.24);black=mat('pupil',(.006,.004,.003),.2);brow=mat('eyebrows',(.06,.027,.009),.8);mouth=mat('mouth',(.045,.013,.009),.75);wood=mat('walnut',(.095,.038,.015),.43,True);leather=mat('oxblood booth',(.14,.035,.015),.55,True);cream=mat('cream ceramic',(.72,.61,.43),.22);coffee=mat('coffee',(.024,.009,.003),.15);brass=mat('aged brass',(.28,.13,.035),.3,False,.75);wall=mat('midnight walls',(.018,.026,.032),.85);glass=mat('blue rain window',(.018,.035,.055),.25,True,.45);lamp=mat('lamp glow',(.99,.54,.16),.2,False,0,3);paper=mat('sketchbook paper',(.66,.58,.41),.9)

def parent(obj,root):
 if root:obj.parent=root
 return obj

def empty(name,loc=(0,0,0),root=None):
 ob=bpy.data.objects.new(name,None);sc.collection.objects.link(ob);ob.location=loc;return parent(ob,root)

def uv(name,loc,scale,material,root=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=(0,0,0));o=bpy.context.object;o.name=name;o.location=loc;o.scale=scale;o.data.materials.append(material)
 for poly in o.data.polygons:poly.use_smooth=True
 return parent(o,root)

def cube(name,loc,size,material,bevel=.03,root=None):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.location=loc;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  m=o.modifiers.new('soft rounded edges','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return parent(o,root)

def curve(name,pts,radius,material,root=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=radius;cu.bevel_resolution=2;cu.resolution_u=8;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob);cu.materials.append(material);return parent(ob,root)

def torus(name,loc,major,minor,material,rot=(0,0,0),root=None):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=48,minor_segments=12);o=bpy.context.object;o.name=name;o.location=loc;o.rotation_euler=rot;o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 return parent(o,root)

def aim(ob,point):ob.rotation_euler=(Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,col,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=col;d.shape='DISK';d.size=size
 if a.engine=='BLENDER_EEVEE_NEXT':
  d.use_shadow=name in ('soft face key','pendant soft pool')
  if hasattr(d,'use_shadow_jitter'):d.use_shadow_jitter=False
  if hasattr(d,'shadow_maximum_resolution'):d.shadow_maximum_resolution=.025
 o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;aim(o,target)

# Physical cafe set: floor, window, banquette, empty chair, table and pendant.
for x in range(-7,8):cube('floor plank',(x*.48,0,-.045),(.47,7,.09),wood,.008)
cube('rear wall',(0,2,1.7),(7,.18,3.5),wall)
for x in (-2,0,2):
 cube('window pane',(x,1.88,1.9),(1.87,.05,2.35),glass,.01)
 for xx in (x-.95,x+.95):cube('window mullion',(xx,1.82,1.9),(.055,.1,2.5),wood,.01)
 cube('window sill',(x,1.72,.7),(2,.28,.08),wood)
 for i in range(18):
  xx=x+random.uniform(-.85,.85);zz=random.uniform(.85,3);length=random.uniform(.025,.15)
  curve('rain on glass',[(xx,1.84,zz),(xx-.012,1.84,zz-length)],.0018,cream)
for i in range(30):
 x=random.uniform(-3,3);z=random.uniform(.85,2.7);uv('soft city light',(x,1.79,z),(.014,.014,.025),lamp)
for x in (-.78,.9):
 cube('banquette seat',(x,.3,.46),(.9,.7,.16),leather,.08)
 cube('banquette back',(x,.62,.93),(.9,.18,.95),leather,.08)
 for dx in (-.32,.32):cube('seat leg',(x+dx,.3,.23),(.06,.42,.45),wood,.02)
cube('table top',(0,-.48,.79),(2.7,1.05,.09),wood,.06)
for x in (-1.05,1.05):cube('table pedestal',(x,-.48,.37),(.1,.15,.76),brass,.02)
curve('pendant cable',[(1.05,-.1,3.2),(1.05,-.1,2.42)],.008,black)
bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=.34,radius2=.06,depth=.17);shade=bpy.context.object;shade.name='brass pendant shade';shade.location=(1.05,-.1,2.37);shade.data.materials.append(brass)
uv('pendant diffuser',(1.05,-.1,2.29),(.29,.29,.015),lamp)
area('pendant soft pool',(1.05,-.1,2.25),110,(1,.57,.27),.65,(.65,-.4,.8))
area('soft face key',(-2,-2.5,3.4),300,(1,.74,.48),3,(-.7,.05,1.3))
area('amber hair rim',(-.3,1.2,2.8),380,(1,.44,.15),1.5,(-.78,.1,1.5))
area('blue window fill',(1.8,1.3,2.5),160,(.35,.51,1),2,(-.7,.1,1.3))

root=empty('MAYA master',(-.78,.12,0))
uv('shirt torso',(0,.03,.98),(.22,.15,.29),shirt,root);uv('trouser hips',(0,.04,.67),(.22,.18,.14),pants,root)
for side in (-1,1):
 curve('trouser leg',[(side*.115,.01,.64),(side*.14,-.22,.39),(side*.14,-.32,.12)],.091,pants,root)
 uv('closed brown shoe',(side*.14,-.39,.075),(.105,.17,.075),wood,root)
uv('neck',(0,0,1.25),(.065,.065,.1),skin,root)
head=empty('MAYA head control',(0,-.01,1.52),root)
uv('Maya face',(0,0,0),(.325,.275,.345),skin,head)
uv('small nose',(0,-.28,-.07),(.032,.041,.04),skin,head)
eyes=[];pupils=[]
for side in (-1,1):
 eye=empty('eye blink control',(side*.119,-.237,.025),head);eyes.append(eye)
 uv('eye white',(0,0,0),(.095,.027,.10),white,eye)
 pupil=empty('gaze control',(0,-.032,0),eye);pupils.append(pupil)
 uv('brown iris',(0,0,0),(.066,.008,.079),iris,pupil);uv('dark pupil',(0,-.008,0),(.030,.005,.039),black,pupil)
 uv('eye catchlight',(-.013,-.016,.022),(.012,.004,.014),white,pupil)
curve('left expressive brow',[(-.222,-.238,.177),(-.13,-.286,.201),(-.055,-.26,.222)],.016,brow,head)
curve('right expressive brow',[(.055,-.26,.222),(.13,-.286,.201),(.222,-.238,.177)],.016,brow,head)
curve('soft mouth',[(-.049,-.267,-.15),(0,-.287,-.14),(.049,-.267,-.15)],.007,mouth,head)
# Hair cap and groomed curved locks, with a visible face opening and shoulder-length bob.
verts=[];faces=[];rings=20;segments=64
for row in range(rings+1):
 for col in range(segments):
  az=col/segments*2*P;end=1.32+1.18*(math.sin(az)+1)/2;theta=.025+(end-.025)*row/rings
  radius=.344+.006*math.sin(az*5+theta*4)
  verts.append((radius*math.sin(theta)*math.cos(az),radius*.86*math.sin(theta)*math.sin(az),radius*math.cos(theta)))
for row in range(rings):
 for col in range(segments):
  i=row*segments+col;j=row*segments+(col+1)%segments;faces.append((i,j,j+segments,i+segments))
me=bpy.data.meshes.new('bob hair mesh');me.from_pydata(verts,[],faces);me.materials.append(hair);ob=bpy.data.objects.new('Maya chestnut bob',me);sc.collection.objects.link(ob);ob.parent=head
for f in me.polygons:f.use_smooth=True
for k in range(32):
 az=2*P*k/32;end=1.32+1.18*(math.sin(az)+1)/2;pts=[]
 for j in range(7):
  th=.15+(end-.15)*j/6;ang=az+.08*math.sin(th*2+k*.2);r=.351
  pts.append((r*math.sin(th)*math.cos(ang),r*.86*math.sin(th)*math.sin(ang),r*math.cos(th)))
 if math.sin(az)>-.6:curve('sculpted hair strand',pts,.0035,hair2 if k%3==0 else hair,head)
for k in range(7):
 shift=k*.008
 curve('side parted sweeping hair',[(.06+shift,-.10,.322),(-.095+shift,-.285,.26),(-.27+shift,-.24,.11),(-.333,-.10,-.09),(-.33,.02,-.28)],.014,hair if k%2 else hair2,head)
for side in (-1,1):
 for j in range(3):
  curve('wavy side lock',[(side*(.27+j*.012),-.015,1.48),(side*(.33+j*.015),-.005,1.28),(side*(.29+j*.017),.04,1.13)],.035,hair,root)
for j in range(3):torus('knit scarf wrap',(0,0,1.22-j*.028),.113,.031,scarf,root=root)
curve('scarf tail',[(-.06,-.15,1.18),(-.105,-.16,.99),(-.09,-.18,.85)],.041,scarf,root)

hands=[];arms=[]
for side in (-1,1):
 hand=empty(('left' if side<0 else 'right')+' hand control',(side*.16,-.5,.89),root);hands.append(hand)
 uv('palm',(0,0,0),(.047,.035,.067),skin,hand)
 for i in range(4):
  yy=(i-1.5)*.019
  curve('finger',[(.018,yy,.045),(.063,yy,.037),(.072,yy,-.004),(.05,yy,-.023)],.009,skin,hand)
 curve('thumb',[(-.018,-.025,.014),(.016,-.064,.037),(.049,-.056,.018)],.013,skin,hand)
 arm=curve('cotton sleeve',[(side*.19,0,1.12),(side*.31,-.2,.94),(side*.16,-.5,.89)],.062,shirt,root);arms.append(arm)
# Hollow ceramic mug with physical rim/handle; parented to the gripping hand.
mug=empty('MUG held with right hand',(.105,0,-.037),hands[1]);profile=[(0,0),(.057,0),(.068,.012),(.075,.126),(.068,.135),(.061,.125),(.055,.02),(0,.02)];v=[];f=[]
for zrow,(r,z) in enumerate(profile):
 for i in range(64):v.append((r*math.cos(i*2*P/64),r*math.sin(i*2*P/64),z))
for j in range(len(profile)-1):
 for i in range(64):n=j*64+i;nn=j*64+(i+1)%64;f.append((n,nn,nn+64,n+64))
mesh=bpy.data.meshes.new('hollow ceramic mug');mesh.from_pydata(v,[],f);mesh.materials.append(cream);ob=bpy.data.objects.new('mug ceramic',mesh);sc.collection.objects.link(ob);ob.parent=mug
for poly in mesh.polygons:poly.use_smooth=True
torus('mug handle',(.083,0,.075),.043,.01,cream,(P/2,0,0),mug)
uv('coffee surface',(0,0,.118),(.061,.061,.003),coffee,mug)
uv('saucer',(-.515,-.38,.842),(.115,.115,.009),cream)
book=cube('closed sketchbook',(-1.22,-.55,.858),(.24,.29,.027),pants,.009)
cube('book page block',(-1.22,-.55,.863),(.22,.275,.02),paper,.004)
curve('pencil',[(-1.12,-.58,.89),(-1.04,-.35,.89)],.006,wood)
# Expression, gaze, physical arm and mug movement sampled as controls; Blender interpolates each rendered frame.
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
for frame in range(1,194,3):
 t=(frame-1)/24
 lift=ease((t-2.7)/1.5)*(1-ease((t-5.7)/1.6))
 glance=ease((t-.8)/.8)*(1-ease((t-2.8)/.8))
 head.rotation_euler=(.025*math.sin(t*1.2)-.07*lift,0,.10+.09*glance)
 head.location=(0,-.01-.055*lift,1.52+.003*math.sin(t*2));head.keyframe_insert('rotation_euler',frame=frame);head.keyframe_insert('location',frame=frame)
 for pupil in pupils:
  pupil.location.x=.022*glance;pupil.keyframe_insert('location',frame=frame)
 for j,(hand,arm) in enumerate(zip(hands,arms)):
  side=-1 if j==0 else 1
  loc=(-.16,-.48,.89) if j==0 else (.16-.245*lift,-.5+.08*lift,.89+.405*lift)
  hand.location=loc;hand.rotation_euler=(.12*lift if j else 0,0,-.04*lift if j else 0);hand.keyframe_insert('location',frame=frame);hand.keyframe_insert('rotation_euler',frame=frame)
  points=[(side*.19,0,1.12),(side*.30,-.21+.05*lift,.95+.09*lift),loc]
  for p,co in zip(arm.data.splines[0].bezier_points,points):p.co=co;p.keyframe_insert('co',frame=frame)
for center in (30,77,130,174):
 for eye in eyes:
  for frame,scale in ((center-2,1),(center,.06),(center+2,1)):
   eye.scale.z=scale;eye.keyframe_insert('scale',frame=frame)
for eye in eyes:
 eye.scale.z=1;eye.keyframe_insert('scale',frame=1);eye.keyframe_insert('scale',frame=192)
# Camera move is a genuine spatial push; no image plate or photo zoom is used.
bpy.ops.object.camera_add(location=(1.0,-3.6,1.95));cam=bpy.context.object;cam.name='camera cafe acting proof';sc.camera=cam;cam.data.lens=58 if not a.portrait else 42
focus=empty('focus on Maya',(-.78,-.05,1.46));cam.data.dof.use_dof=True;cam.data.dof.focus_object=focus;cam.data.dof.aperture_fstop=4
for frame,loc in ((1,(1.0,-3.6,1.95)),(192,(.88,-3.4,1.9))):
 cam.location=loc;aim(cam,(-.3,0,1.3) if not a.portrait else (-.73,-.04,1.25));cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_euler',frame=frame)
sc.render.film_transparent=False
sc['status']='First procedural 3D acting study; not an approved final character match or complete film.';sc['fps_rule']='Frame count follows duration at 24 FPS; no arbitrary frame floor.'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'cafe-acting-proof.blend'))
if a.save_only:sys.exit(0)
frames=[a.still] if a.still else range(a.start,a.end+1)
started=time.perf_counter();poses=[]
for frame in frames:
 sc.frame_set(frame)
 if frame in (1,48,96,144,192):
  poses.append({'frame':frame,'right_hand_world':list(hands[1].matrix_world.translation),'cup_world':list(mug.matrix_world.translation),'head_rotation':list(head.rotation_euler),'eye_scale':eyes[0].scale.z})
 sc.render.filepath=str(out/f'{frame:06}.png');bpy.ops.render.render(write_still=True)
(out/'render-receipt.json').write_text(json.dumps({'renderer':f'Blender {a.engine}','blender':bpy.app.version_string,'fps':24,'start_frame':a.still or a.start,'end_frame':a.still or a.end,'rendered_frames':len(frames),'width':sc.render.resolution_x,'height':sc.render.resolution_y,'samples':a.samples,'wall_seconds':round(time.perf_counter()-started,2),'status':'actual geometry animation proof; not a finished film','audio':'not included','pose_samples':poses,'cup_parent':mug.parent.name},indent=2))
