"""Reusable original layered 2D sets, character rigs, contacts and motivated cameras."""
import io
import math
import xml.etree.ElementTree as ET
from html import escape
import cairosvg
from PIL import Image
from .layered_film import path,rect,ellipse,eye,ease,foot,maya,svg_frame

DEFS=svg_frame(0).split('<defs>',1)[1].split('</defs>',1)[0]
MOODS={'neutral':(.0,.0,.68),'sad':(.0,1,.46),'hopeful':(.85,.0,.91),'anxious':(.05,.55,.9),
       'happy':(1,.0,.82),'bored':(.0,.35,.4),'angry':(.0,.7,.7),'tired':(.0,.65,.35)}
POSITIONS={'left':.25,'center':.5,'right':.75}


def acting(actor,t,u):
    a=MOODS[actor['emotion_start']];b=MOODS[actor['emotion_end']];q=ease((u-.12)/.7)
    h,sad,op=[x+(y-x)*q for x,y in zip(a,b)]
    blink=1-.94*max(0,1-abs(((t+.7)%3.9)-1.8)/.13)
    look={'left':-7,'right':7,'down':0,'forward':0}[actor['look']]
    return dict(hope=h,hurt=sad,openness=op*blink,head_y=-10*h+10*sad,
        head_angle=-2*h+4*sad,gaze_x=look,gaze_y=6 if actor['look']=='down' else 2,hand_raise=0)


def arm_points(shoulder,hand,bend):
    x,y=shoulder;hx,hy=hand;dx,dy=hx-x,hy-y;distance=max(1,math.hypot(dx,dy));reach=min(188,distance)
    mid=(reach/2);height=math.sqrt(max(0,95**2-mid**2))
    ex=x+dx/distance*mid-dy/distance*height*bend;ey=y+dy/distance*mid+dx/distance*height*bend
    return ex,ey


def prop_svg(kind,x,y,t=0,progress=1):
    q=[]
    if kind=='cup':
        q=[path(f'M{x-24} {y-24}L{x-21} {y+15}Q{x} {y+25} {x+22} {y+15}L{x+25} {y-24}Z','url(#cup)','#84745f',2),
           ellipse(x,y-24,24,5,'#d5c7aa'),ellipse(x,y-24,19,3,'#332b27'),path(f'M{x+24} {y-17}Q{x+46} {y-20} {x+40} {y+1}Q{x+36} {y+9} {x+23} {y+5}','none','#b5a78c',6)]
    elif kind=='phone':
        q=[rect(x-18,y-34,36,65,'#151d25',6,extra='stroke="#71716b" stroke-width="2"'),rect(x-14,y-27,28,47,'#426071',3),ellipse(x,y+25,3,3,'#72746e')]
    elif kind in ('paper','sketchbook'):
        q=[path(f'M{x-47} {y-25}L{x+41} {y-35}L{x+49} {y+24}L{x-40} {y+32}Z','#cdbf9e','#6a6050',2)]
        if kind=='sketchbook':q.insert(0,rect(x-53,y-39,108,80,'#3c4844',4))
        q.append(path(f'M{x-25} {y+8}Q{x-7} {y-16} {x+12} {y+5} L{x+26*min(1,progress)} {y+5}','none','#776855',2))
    elif kind=='bag':
        q=[path(f'M{x-34} {y-25}L{x+32} {y-25}L{x+41} {y+34}Q{x} {y+43} {x-40} {y+33}Z','#7b6b50','#34332e',2),path(f'M{x-15} {y-23}Q{x} {y-59} {x+17} {y-23}','none','#918061',5)]
    return ''.join(q)


def pose(actor,t,u,seconds):
    mood=acting(actor,t,u);action=actor['action'];left=(-72,290);right=(76,290)
    motion=ease((u-.08)/.4);release=ease((u-.72)/.25)
    if action=='sip':
        amount=motion*(1-release);right=(76-56*amount,290-195*amount)
    elif action in ('reach','open_door'):
        right=(76+72*motion,290-120*motion)
    elif action=='draw':
        left=(-45,275);right=(22+7*math.sin(t*8),267+4*math.sin(t*12))
    elif action=='phone':
        right=(37+2*math.sin(t*3),205);mood['gaze_y']=7;mood['head_angle']=5
    elif action=='slump':
        mood['head_y']+=16*motion;mood['head_angle']+=5*motion;left=(-63,310);right=(65,310)
    elif action=='look_away':
        mood['gaze_x']=-9*motion;mood['head_angle']=-7*motion
    elif action in ('pick_up','put_down'):
        amount=motion if action=='pick_up' else 1-motion;right=(76-26*amount,293-105*amount)
    elif action in ('walk','run'):
        swing=20*math.sin(t*2*math.pi*(1.6 if action=='run' else 1));left=(-64+swing,278);right=(64-swing,278)
    elif action=='listen':
        mood['head_angle']+=2*math.sin(t*1.3);mood['gaze_y']=1
    return mood,left,right


def character(actor,t,u,seconds,x,y,scale,contact=None,speaking=False):
    name=actor['character'];action=actor['action'];mood,left,right=pose(actor,t,u,seconds)
    moving=action in ('walk','run');seated=actor.get('posture','seated' if action in ('sit','sip','draw','slump') else 'standing')=='seated'
    if contact and action in ('offer','receive'):
        target=((contact[0]-x)/scale+(-30 if contact[0]>=x else 30),(contact[1]-y)/scale)
        amount=ease(u/.42)*(1-.5*ease((u-.75)/.25))
        if contact[0]>=x:right=(right[0]+(target[0]-right[0])*amount,right[1]+(target[1]-right[1])*amount)
        else:left=(left[0]+(target[0]-left[0])*amount,left[1]+(target[1]-left[1])*amount)
    q=[f'<g transform="translate({x},{y}) scale({scale})">']
    for side in (0,1):
        hx=-28 if side==0 else 28
        if moving:
            velocity=(POSITIONS[actor['to']]-POSITIONS[actor['from']])*actor['_world_width']/seconds/scale
            fx,fy=foot(t*(1.6 if action=='run' else 1),side,velocity/(1.6 if action=='run' else 1))
            if velocity>0:fx=-fx
            knee=(hx+fx)*.5;end=(fx,430+fy)
        else:
            knee=hx*1.8 if seated else hx;end=(hx*1.8 if seated else hx,430)
        q.append(path(f'M{hx} 278Q{knee} 352 {end[0]} {end[1]}','none','#46423c' if name=='Maya' else '#353b36',36))
        q.append(path(f'M{end[0]-23} {end[1]-6}Q{end[0]+5} {end[1]-10} {end[0]+38} {end[1]+9}Q{end[0]+40} {end[1]+21} {end[0]-25} {end[1]+17}Z','#44362c','#24292b',2))
    # Lower-body occlusion is explicit: the table surface is painted after the legs.
    if seated and actor.get('_setting','cafe') in ('cafe','studio','classroom'):
        q.append(path('M-164 309L174 309L203 361L-147 361Z','url(#table)','#272c2c',3))
        q.append(path('M-147 361H203V373H-147Z','#392f29','#252a2c',2))
    cloth='url(#cloth)' if name=='Maya' else '#795c44' if name=='Leo' else '#817059'
    q.append(path('M-59 126Q0 111 60 126L70 278Q0 307-70 280Z',cloth,'#302d2c',3))
    q.append(path('M-40 185Q0 201 40 184 M-50 258Q0 269 50 257','none','#9b8061',1.2,extra='opacity=".5"'))
    if name=='Maya':
        q.append(path('M-43 117Q0 145 43 118L39 148Q0 172-43 146Z','#343737','#252a2e',3))
        q.append(path('M-19 146L-43 236L-13 231L5 153Z','#3b3d3b','#252a2e',2))
    elif name=='Max':q.append(path('M-59 127L-19 118L-18 285L-68 278Z M18 118L60 127L69 278L18 285Z','#555d48','#2d3330',2))
    # Head is a separate articulated layer; Maya reuses the approved opening rig.
    if name=='Maya':
        root=ET.fromstring(maya(t,0,0,acting=mood));head=next(node for node in root if node.tag=='g')
        h=ET.tostring(head,encoding='unicode').replace('maya-left',name+'-left').replace('maya-right',name+'-right');q.append(h)
    else:
        q.append(f'<g transform="translate(0,{mood["head_y"]}) rotate({mood["head_angle"]})">')
        q.append(path('M-73-53Q-47-103 20-86Q83-70 76-1Q71 68 4 88Q-61 70-73 16Z','url(#skin)','#4d493f',2.5))
        q.append(eye(-31,4,mood['openness'],mood['gaze_x'],mood['gaze_y'],name+'-left'))
        q.append(eye(29,5,mood['openness'],mood['gaze_x'],mood['gaze_y'],name+'-right'))
        q.append(path(f'M-55 {-24+8*mood["hurt"]}Q-32 {-36-5*mood["hope"]} -10 -28 M10 -28Q32 {-36-5*mood["hope"]} 55 {-24+8*mood["hurt"]}','none','#51402d',4))
        q.append(path(f'M-16 59Q0 {59+10*mood["hope"]-10*mood["hurt"]} 16 59','none','#6b5846',2.5));q.append('</g>')
    if speaking:q.append(ellipse(0,64+mood['head_y'],9,2+5*abs(math.sin(t*12)),'#4b342a'))
    # Props travel with the hand, not with independent ungrounded screen coordinates.
    carried=actor['prop'];owner=True
    if action=='offer' and u>.58:owner=False
    if action=='receive' and u<.58:owner=False
    if carried!='none' and owner:
        if action=='draw':q.append(prop_svg(carried,0,278,t,u))
        else:
            hand=left if contact and contact[0]<x and action=='receive' else right
            offset=(30 if contact[0]>=x else -30) if contact and action in ('offer','receive') else 20
            q.append(prop_svg(carried,hand[0]+offset,hand[1]-6,t,u))
    for side,hand in ((-1,left),(1,right)):
        shoulder=(side*57,146);ex,ey=arm_points(shoulder,hand,side if action in ('offer','receive','reach') else -side)
        q.append(path(f'M{shoulder[0]} {shoulder[1]}Q{ex} {ey} {ex} {ey}','none',cloth,32))
        q.append(path(f'M{ex} {ey}L{hand[0]} {hand[1]}','none','#c3ac86' if name=='Leo' else cloth,27))
        q.append(ellipse(hand[0],hand[1],12,15,'#c7af88'))
        for finger in range(3):q.append(path(f'M{hand[0]-5+finger*4} {hand[1]-7}l1 9','none','#947a5c',.9))
    if action=='draw':q.append(path(f'M{right[0]-5} {right[1]-8}l-12 24','none','#b7a376',3))
    q.append('</g>');return ''.join(q)


def background(setting,w,h,t,door=False):
    floor=h*.87;q=[rect(0,0,w,h,'url(#wall)')]
    if setting in ('cafe','studio','classroom','bedroom'):
        q.append(rect(w*.07,h*.08,w*.86,h*.67,'url(#night)',14))
        for i in range(1,5):q.append(rect(w*(.07+.172*i),h*.08,7,h*.67,'#3e3e35'))
        for j in range(25):
            px=w*(.08+(j*.137)% .82);py=h*(.1+((j*.091+t*.022)%.61))
            q.append(path(f'M{px} {py}l-2 {h*.018}','none','#71828a',1,extra='opacity=".25"'))
        q.append(rect(0,floor,w,h-floor,'#222a2b'))
        if setting=='cafe':
            q.append(rect(w*.07,h*.62,w*.86,h*.08,'url(#table)',8))
            q.append(rect(w*.67,h*.63,w*.12,h*.17,'url(#seat)',18))
        elif setting=='bedroom':
            q.append(rect(w*.05,h*.67,w*.5,h*.23,'#394349',20));q.append(path(f'M{w*.06} {h*.72}Q{w*.29} {h*.64} {w*.56} {h*.76}V{h*.9}H{w*.05}Z','#4b5559','#263039',3))
            q.append(ellipse(w*.16,h*.71,w*.08,h*.035,'#9b9c90'))
        elif setting=='classroom':
            q.append(rect(w*.18,h*.15,w*.64,h*.25,'#364a45',8,extra='stroke="#736552" stroke-width="8"'))
            for xx in (.12,.7):q.append(rect(w*xx,h*.7,w*.2,h*.055,'url(#table)',6))
        else:
            q.append(rect(w*.1,h*.61,w*.8,h*.06,'url(#table)',6));q.append(rect(w*.69,h*.39,w*.14,h*.22,'#b9b097',3))
        lx=w*.76;q.append(ellipse(lx,h*.53,w*.4,h*.65,'url(#light)'))
        q.append(path(f'M{lx} 0V{h*.19}','none','#524532',4))
        q.append(path(f'M{lx-w*.055} {h*.24}Q{lx} {h*.12} {lx+w*.055} {h*.24}Z','#655038','#272c2d',3));q.append(ellipse(lx,h*.24,w*.055,h*.008,'#d1a36b'))
    else:
        q.append(rect(0,0,w,floor,'url(#night)'))
        for i in range(6):
            x=i*w/5-w*.06;top=h*(.18+.08*math.sin(i*2))
            q.append(rect(x,top,w*.18,floor-top,'#253038',2))
            for row in range(3):q.append(rect(x+w*.05,top+h*(.06+.12*row),w*.035,h*.04,'#8c7857',3,extra='opacity=".4"'))
        q.append(path(f'M0 {floor}L{w} {floor-h*.08}V{h}H0Z','#343b3d','#202b2d',2))
        if setting=='park':
            q.append(path(f'M0 {h*.73}Q{w*.2} {h*.54} {w*.5} {h*.74}T{w} {h*.7}V{floor}H0Z','#31413a','#28332f',2))
            for i in (.1,.86):
                q.append(path(f'M{w*i} {floor}L{w*i} {h*.3}','none','#514a3c',17));q.append(ellipse(w*i,h*.3,w*.12,h*.17,'#34453c'))
            q.append(rect(w*.38,h*.73,w*.4,h*.035,'#76634b',5));q.append(rect(w*.4,h*.77,w*.36,h*.025,'#61523f',4))
        elif setting=='bus_stop':
            q.append(rect(w*.12,h*.26,w*.76,h*.44,'#394b51',8,extra='opacity=".65"'))
            q.append(rect(w*.1,h*.25,w*.8,h*.025,'#6a6d62',4))
            for x in (.12,.87):q.append(rect(w*x,h*.26,w*.012,h*.59,'#6c6e63'))
        else:
            q.append(rect(w*.72,h*.32,w*.18,h*.43,'#182731',5,extra='stroke="#71634e" stroke-width="5"'))
            q.append(rect(w*.75,h*.36,w*.1,h*.25,'#a17b45',4,extra='opacity=".35"'))
        if setting!='park':
            for j in range(35):
                x=(j*117+t*35)%w;y=(j*67+t*80)%(h*.85)
                q.append(path(f'M{x} {y}l-4 26','none','#84979d',1,extra='opacity=".25"'))
    if door:
        angle=ease(min(t/2,1));q.append(path(f'M{w*.9} {h*.33}L{w*(.73+.14*angle)} {h*.36}V{floor}L{w*.9} {floor}Z','#4f4233','#252d31',3))
    return ''.join(q)


def svg(shot,t,portrait=False):
    seconds=shot['seconds'];u=max(0,min(1,t/seconds));w,h=(900,1600) if portrait else (1600,900)
    scale=1.3 if portrait else 1.1;floor=h*.88
    roots=[]
    for a in shot['actors']:
        a={**a,'_world_width':w,'_setting':shot['setting']};moving=a['action'] in ('walk','run')
        x=w*(POSITIONS[a['from']]+(POSITIONS[a['to']]-POSITIONS[a['from']])*u) if moving else w*POSITIONS[a['from']]
        if portrait and len(shot['actors'])>1:scale=1.07
        roots.append((a,x,floor-447*scale,scale))
    handoff_indices=[i for i,r in enumerate(roots) if r[0]['action'] in ('offer','receive')]
    if len(handoff_indices)==2:
        mid=sum(roots[i][1] for i in handoff_indices)/2
        for sign,i in zip((-1,1),sorted(handoff_indices,key=lambda i:roots[i][1])):
            a,x,y,s=roots[i];roots[i]=(a,mid+sign*150*s,y,s)
    focus=next((r for r in roots if r[0]['character']==shot['focus']),roots[0]);fx,fy=focus[1],focus[2]+60*focus[3]
    zoom={'wide':.85,'medium':1.1,'closeup':1.75,'insert':1.9}[shot['framing']]
    zoom*=1+.13*ease(u) if shot['motion']=='push' else 1.13-.13*ease(u) if shot['motion']=='pull' else 1
    if shot['framing']=='insert':fy+=180*focus[3]
    target_y=h*(.43 if shot['framing'] in ('closeup','insert') else .36)
    if shot['framing'] in ('medium','wide'):fx=w*.5;fy=h*.39;target_y=fy
    pan=(u-.5)*w*.12 if shot['motion']=='pan' else 0
    q=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{DEFS}</defs>',rect(0,0,w,h,'#172128')]
    # Distant layer moves less than the character plane.
    q.append(f'<g transform="translate({w*.5-fx*(1+(zoom-1)*.65)+pan*.5},{target_y-fy*(1+(zoom-1)*.65)}) scale({1+(zoom-1)*.65})">')
    q.append(background(shot['setting'],w,h,t,any(a['action']=='open_door' for a in shot['actors'])));q.append('</g>')
    q.append(f'<g transform="translate({w*.5-fx*zoom+pan},{target_y-fy*zoom}) scale({zoom})">')
    handoff=[r for r in roots if r[0]['action'] in ('offer','receive')]
    contact=(sum(r[1] for r in handoff)/len(handoff),floor-210*scale) if handoff else None
    for a,x,y,s in roots:
        speaking=any(c['asset']=='speech' and c['speaker']==a['character'] and c['start_seconds']<=t<c['end_seconds'] for c in shot['cues'])
        q.append(character(a,t,u,seconds,x,y,s,contact,speaking))
    q.append('</g>');q.append(rect(0,0,w,h,'url(#vignette)'))
    if shot.get('screen_text') and .15<u<.85:
        text=escape(shot['screen_text']);q.append(f'<text x="{w/2}" y="{h*.91}" text-anchor="middle" font-family="DejaVu Sans" font-size="{28 if portrait else 24}" fill="#e0d6c1">{text}</text>')
    q.append('</svg>');return ''.join(q)


def frame(shot,t,width,portrait=False):
    # Read Cairo's opaque native pixels directly; avoid PNG compression/decompression per frame.
    from cairosvg.parser import Tree
    from cairosvg.surface import PNGSurface
    height=round(width*(16/9 if portrait else 9/16)/2)*2
    surface=PNGSurface(Tree(bytestring=svg(shot,t,portrait).encode()),None,96,output_width=width,output_height=height)
    surface.cairo.flush()
    im=Image.frombytes('RGBA',(width,height),bytes(surface.cairo.get_data()),'raw','BGRA',surface.cairo.get_stride(),1).convert('RGB')
    surface.finish()
    return im
