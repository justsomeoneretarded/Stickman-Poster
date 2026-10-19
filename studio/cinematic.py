"""Original expressive vector scenes, composed independently for landscape/portrait."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw

INK='#111421'
CREAM='#fff4d9'
COLORS={'female':'#ee7295','male1':'#5d9bff','male2':'#b38aff'}


def ease(p):
    p=max(0,min(1,p));return p*p*(3-2*p)


def limb(d,points,color=INK,width=11):
    d.line(points,fill=color,width=width,joint='curve')
    r=width/2
    for x,y in points:d.ellipse((x-r,y-r,x+r,y+r),fill=color)


@lru_cache(maxsize=32)
def backdrop(location,portrait):
    w,h=(1080,1920) if portrait else (1920,1080)
    im=Image.new('RGB',(w,h));d=ImageDraw.Draw(im)
    top,bottom=((22,20,46),(75,48,88)) if location not in ('field','park') else ((30,67,91),(113,151,150))
    for y in range(h):
        t=y/h;d.line((0,y,w,y),fill=tuple(round(a*(1-t)+b*t) for a,b in zip(top,bottom)))
    floor=1390 if portrait else 850
    # Layered skyline: distant buildings, warm windows, then foreground silhouettes.
    for layer in range(3):
        for i,x in enumerate(range(-150,w+200,180+layer*35)):
            y=floor-350-layer*60-((i*173+layer*29)%200)
            color=('#4e466a','#39334f','#27273d')[layer]
            d.rectangle((x,y,x+150+layer*25,floor),fill=color)
            for xx in range(x+22,x+140,38):
                for yy in range(y+35,floor-30,58):
                    if (xx//38+yy//58)%4:d.rectangle((xx,yy,xx+17,yy+26),fill=('#8f7a91','#d0a581','#887d9c')[layer])
    d.rectangle((0,floor,w,h),fill='#202336')
    d.line((0,floor,w,floor),fill='#8a7195',width=3)
    if location in ('gym','room','cafe','classroom','bank'):
        d.rectangle((0,0,w,floor),fill='#292d44')
        for x in range(100,w,520):
            d.rounded_rectangle((x,170,x+390,floor-160),radius=18,fill='#171f36',outline='#55516b',width=9)
            d.line((x+195,175,x+195,floor-160),fill='#55516b',width=6)
            for z in range(x+30,x+370,65):
                bh=(z*7)%230+100
                d.rectangle((z,floor-180-bh,z+50,floor-175),fill='#494260')
                for yy in range(floor-160-bh,floor-190,45):d.rectangle((z+12,yy,z+23,yy+17),fill='#d8ad8e')
        if location=='gym':
            for x in ((130,w-310) if not portrait else (50,850)):
                d.line((x,floor-400,x,floor-20),fill='#798194',width=16)
                for yy in (floor-350,floor-260,floor-170):
                    d.line((x-65,yy,x+65,yy),fill='#c5bdc1',width=8)
                    for xx in (x-60,x+60):d.rounded_rectangle((xx-20,yy-42,xx+20,yy+42),radius=9,fill='#131a2b',outline='#77758a',width=3)
    elif location in ('field','park'):
        d.rectangle((0,floor-100,w,h),fill='#375858')
        for i,x in enumerate(range(80,w,320)):
            d.line((x,floor-230,x,floor-75),fill='#322d3e',width=17)
            d.ellipse((x-120,floor-450,x+120,floor-150),fill='#2b494e')
        d.polygon([(0,floor+100),(w,floor-10),(w,floor+80),(0,floor+280)],fill='#a38f89')
    # Warm key light, subtle broad spotlight rather than flat walls.
    overlay=Image.new('RGBA',(w,h));od=ImageDraw.Draw(overlay)
    od.polygon([(w*.24,0),(w*.40,0),(w*.85,floor),(w*.05,floor)],fill=(225,181,142,15))
    im=Image.alpha_composite(im.convert('RGBA'),overlay)
    return im


def actor(d,x,floor,s,t,color,pose='talk',expression='happy',speaking=False,phase=0,hand=None,drink_amount=None):
    def pt(a,b):return (x+a*s,floor+b*s)
    def line(points,c=INK,width=10):limb(d,[pt(*p) for p in points],c,max(2,round(width*s)))
    def ellipse(box,c):d.ellipse((x+box[0]*s,floor+box[1]*s,x+box[2]*s,floor+box[3]*s),fill=c)
    stride=math.sin(phase);bob=abs(math.cos(phase))*5 if pose in ('walk','run') else math.sin(t*1.8)*1.5
    run=pose=='run';hip=(0,-133-bob);shoulder=(12 if run else 0,-270-bob)
    for side in (-1,1):
        swing=stride*side
        foot=(side*27+swing*(90 if run else 65),-max(0,swing)*(55 if run else 25)) if pose in ('walk','run') else (side*28,0)
        knee=((hip[0]+foot[0])/2-20, -70-max(0,swing)*(35 if run else 12))
        line([hip,knee,foot],'#141927',12)
        line([(foot[0]-8,foot[1]),(foot[0]+21,foot[1])],CREAM,10)
    d.polygon([pt(shoulder[0]-39,shoulder[1]),pt(shoulder[0]+39,shoulder[1]),pt(35,hip[1]+5),pt(-34,hip[1]+5)],fill=color)
    line([(shoulder[0]-10,shoulder[1]+18),(shoulder[0]-10,shoulder[1]+45)],CREAM,3)
    line([(shoulder[0]+10,shoulder[1]+18),(shoulder[0]+10,shoulder[1]+45)],CREAM,3)
    # Arms are articulated, with expressive gestures and opposite gait swings.
    hands=[]
    for side in (-1,1):
        start=(shoulder[0]+side*33,shoulder[1]+10)
        if pose in ('run','walk'):
            wrist=(side*40-stride*side*(70 if run else 35),-190+stride*side*25)
            elbow=(side*60,-215)
        elif pose=='cheer':wrist=(side*75,-370);elbow=(side*100,-300)
        elif pose=='drink' and side==1:
            a=drink_amount if drink_amount is not None else (1-math.cos(min(1,t/1.1)*math.pi))/2
            wrist=(70-35*a,-175-140*a);elbow=(95,-220)
        elif hand is not None and side==1:wrist=hand;elbow=((start[0]+hand[0])/2+30,(start[1]+hand[1])/2+22)
        elif speaking and side==1:
            wrist=(90+math.sin(t*2)*12,-245+math.sin(t*3)*17);elbow=(65,-200)
        else:wrist=(side*43,-150);elbow=(side*55,-215)
        line([start,elbow],color,15);line([elbow,wrist],INK,9);ellipse((wrist[0]-6,wrist[1]-6,wrist[0]+6,wrist[1]+6),CREAM)
        hands.append(pt(*wrist))
    head=(shoulder[0],shoulder[1]-78)
    ellipse((head[0]-52,head[1]-52,head[0]+52,head[1]+52),'#0b111d')
    # Rim-lit head and expressive white eyes; no pasted nameplates.
    d.arc((x+(head[0]-53)*s,floor+(head[1]-53)*s,x+(head[0]+53)*s,floor+(head[1]+53)*s),190,305,fill='#e6caa7',width=max(2,int(3*s)))
    blink=t%4.3>4.12
    for side in (-1,1):
        eye=head[0]+side*18
        if blink:line([(eye-6,head[1]),(eye+6,head[1])],CREAM,3)
        else:ellipse((eye-5,head[1]-5,eye+5,head[1]+8),CREAM)
        slope=-side*5 if expression=='surprised' else -side*3
        line([(eye-9,head[1]-17+slope),(eye+8,head[1]-17-slope)],CREAM,3)
    mouth_y=head[1]+24
    if expression=='surprised' or (speaking and math.sin(t*15)>.1):ellipse((head[0]-7,mouth_y-5,head[0]+7,mouth_y+7),CREAM)
    else:d.arc((x+(head[0]-14)*s,floor+(mouth_y-10)*s,x+(head[0]+14)*s,floor+(mouth_y+7)*s),0,180,fill=CREAM,width=max(2,int(3*s)))
    if pose=='drink':
        hx,hy=hands[1];d.rounded_rectangle((hx-16*s,hy-20*s,hx+16*s,hy+10*s),radius=4*s,fill='#edc6a6')
    return hands


def car(d,x,y,s=1):
    def box(b):return tuple((x+v*s if i%2==0 else y+v*s) for i,v in enumerate(b))
    d.rounded_rectangle(box((-350,-55,350,70)),radius=35*s,fill='#df6e79',outline='#ffc2b6',width=max(1,int(3*s)))
    d.polygon([(x-230*s,y-55*s),(x-140*s,y-165*s),(x+130*s,y-165*s),(x+245*s,y-55*s)],fill='#e9878b')
    for a,b in ((-140,-15),(10,125)):
        d.polygon([(x+a*s,y-145*s),(x+b*s,y-145*s),(x+(b+65)*s,y-65*s),(x+(a-50)*s,y-65*s)],fill='#9ebdc7')
    d.line((x,y-145*s,x,y-65*s),fill='#493c59',width=max(2,int(7*s)))
    for xx in (-220,220):
        d.ellipse(box((xx-65,10,xx+65,140)),fill='#151d2e',outline='#d3d2d7',width=max(2,int(9*s)))
        d.ellipse(box((xx-24,51,xx+24,99)),fill='#7d839b')
    d.rounded_rectangle(box((280,-20,338,8)),radius=5*s,fill='#ffe6b0')
    d.line((x-320*s,y+26*s,x+320*s,y+26*s),fill='#b34f68',width=max(1,int(4*s)))


def bench_press(d,cx,floor,t,scale=1,load='car',color='#5d9bff'):
    # One shared car transform drives the wrists: the load stays in the hands.
    lift=ease((math.sin(t*1.45-math.pi/2)+1)/2)
    y=floor-320-100*lift
    s=scale
    def p(a,b):return (cx+a*s,floor+b*s)
    def ln(points,c=INK,width=12):limb(d,[p(*a) for a in points],c,max(2,int(width*s)))
    d.rounded_rectangle((cx-350*s,floor-145*s,cx+170*s,floor-115*s),radius=12*s,fill='#ad7d97')
    for x in (-250,130):ln([(x,-115),(x,0)],'#7b8297',15)
    ln([(-245,-185),(90,-145)],color,46)
    ln([(75,-145),(160,-105),(190,0)],INK,15)
    ln([(100,-145),(195,-105),(240,0)],INK,15)
    hy=(y-floor)/s+(70 if load=='barbell' else 58)
    for a,b in ((-145,-160),(-80,115)):
        ln([(a,-182),((a+b)/2,hy+85),(b,hy)],color,15)
        d.ellipse((cx+(b-8)*s,floor+(hy-8)*s,cx+(b+8)*s,floor+(hy+8)*s),fill=CREAM)
    hx,hy=p(-295,-197)
    d.ellipse((hx-48*s,hy-48*s,hx+48*s,hy+48*s),fill='#0c1220',outline='#e6caa7',width=max(2,int(3*s)))
    for xx in (-12,15):d.ellipse((hx+(xx-4)*s,hy-8*s,hx+(xx+4)*s,hy+3*s),fill=CREAM)
    if load=='barbell':
        yy=y+70*s
        d.line((cx-300*s,yy,cx+300*s,yy),fill='#dadce6',width=max(2,int(12*s)))
        for side in (-1,1):
            for offset in (220,255):
                xx=cx+side*offset*s
                d.rounded_rectangle((xx-14*s,yy-75*s,xx+14*s,yy+75*s),radius=6*s,fill='#171f32',outline='#8391b2',width=max(2,int(3*s)))
    else:car(d,cx,y,.83*s)
    return (cx,y)


def frame(scene,t,width,height,preview=False):
    from .render import font,fit_text
    portrait=height>width
    w,h=(1080,1920) if portrait else (1920,1080)
    im=backdrop(scene['location'],portrait).copy();d=ImageDraw.Draw(im)
    floor=1370 if portrait else 842
    members=scene.get('cast_members',[])
    hero=next((m for m in members if m['voice']=='male1'),members[0] if members else {'id':'hero','voice':'male1'})
    speaker=next((m for m in members if m['id']==scene.get('speaker')),hero)
    staging=scene.get('staging','talk');progress=t/max(.01,scene['duration'])
    color=COLORS.get(speaker['voice'],'#5d9bff')
    focus=w/2
    if staging=='lift':
        center=w*.51
        d.ellipse((center-420,floor-25,center+430,floor+45),fill='#171e2f')
        bench_press(d,center,floor,t,1.25 if portrait else 1.15,scene.get('prop','car'),COLORS.get(hero['voice'],'#5d9bff'))
        observer=speaker if speaker['id']!=hero['id'] else next((m for m in members if m['id']!=hero['id']),None)
        if not portrait and observer:
            actor(d,1530,floor,.9,t,COLORS.get(observer['voice'],'#ee7295'),expression='surprised',speaking=observer['id']==speaker['id'])
    elif staging=='fly':
        focus=w*(.22+.56*ease(progress)) if not portrait else w*.50+math.sin(t*.8)*100
        yf=floor-(320 if portrait else 150)-math.sin(progress*math.pi)*(260 if portrait else 100)
        for i in range(8):
            xx=(w-(t*260+i*210)%w)
            d.line((xx,360+i*90,xx+70,360+i*90),fill='#8a839e',width=3)
        actor(d,focus,yf,1.15,t,color,'cheer','surprised',True)
    else:
        pose={'travel':'walk','enter':'walk','chase':'run','react':'cheer','drink':'drink','carry':'walk'}.get(staging,'talk')
        if staging in ('travel','chase','carry'):
            focus=w*(.18+.64*progress)
            phase=(focus/w)*math.tau*5
        elif staging=='enter':focus=w*(.22+.28*ease(min(1,progress*3)));phase=t*6
        else:phase=t*6
        if staging=='reveal' or scene.get('prop')=='car':car(d,w*.68,floor-135,.7 if portrait else .9)
        # Camera cuts between solo, reaction, and shared compositions.
        shot=scene.get('shot','medium')
        scale=(2.2 if portrait else 1.7) if shot=='close' else (1.55 if portrait else 1.12)
        if shot=='close':focus=w*.47;floor+=150 if portrait else 180
        amount=None
        if staging=='drink':
            focus=w*.60
            amount=ease(progress/.22) if progress<.22 else 1 if progress<.7 else 1-ease((progress-.7)/.3)
            table_y=floor-165*scale;table_x=focus+70*scale
            d.rounded_rectangle((table_x-65,table_y,table_x+250,table_y+18),radius=7,fill='#d5a87f')
            for xx in (table_x-30,table_x+210):d.line((xx,table_y+18,xx,floor+10),fill='#8c6c75',width=12)
        actor(d,focus,floor,scale,t,color,pose,'surprised' if staging=='react' else 'happy',True,phase,drink_amount=amount)
        if shot=='wide' and len(members)>1 and not portrait:
            other=next((m for m in members if m['id']!=speaker['id']),hero)
            actor(d,w*.80,floor,.86,t,COLORS.get(other['voice'],'#ee7295'),expression='surprised' if staging=='react' else 'happy')
    if scene.get('comic_role')=='hook' and portrait:
        title=scene.get('heading','').replace('What if you could ','').replace('What if ','').upper()
        words=title.split();lines=[' '.join(words[i:i+4]) for i in range(0,len(words),4)]
        for i,text in enumerate(lines[:3]):
            fit_text(d,text,w/2,h*.20+i*85,72,w*.87,CREAM,True)
    # Short emphatic captions, without title bars, actor badges, or repeated headings.
    words=scene.get('narration','').split();count=5 if portrait else 7
    if words:
        from .project import caption_chunks
        chunks=caption_chunks(scene.get('narration',''),count)
        idx=min(len(words)-1,int(progress*len(words)));cursor=0;text=' '.join(chunks[-1])
        for chunk in chunks:
            cursor+=len(chunk)
            if idx<cursor:
                text=' '.join(chunk);break
        size=52 if portrait else 43;y=h*.85 if portrait else h*.91
        # Centered outlined type remains readable over the scene.
        f=font(size,True)
        if d.textlength(text,font=f)>w*.88:
            mid=max(1,len(text.split())//2);lines=[' '.join(text.split()[:mid]),' '.join(text.split()[mid:])]
        else:lines=[text]
        for j,line in enumerate(lines):
            d.text((w/2,y+j*(size+14)),line,font=f,anchor='mm',fill=CREAM,stroke_width=4,stroke_fill='#101524')
    if preview:d.text((30,30),'SILENT STYLE STUDY',font=font(21,True),fill='#d1bed0')
    return im.convert('RGB').resize((width,height),Image.Resampling.LANCZOS)
