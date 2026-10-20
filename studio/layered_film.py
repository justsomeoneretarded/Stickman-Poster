"""Original 2D character acting with layered staging; no 3D model or photo plate."""
import argparse
import io
import json
import math
import subprocess
import wave
from pathlib import Path
import numpy as np
from PIL import Image

DURATION=14


def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)


def state(t):
    hope=ease((t-2.2)/1.3)*(1-ease((t-7.0)/1.3))
    hurt=ease((t-7.3)/2.0)
    blink=1.
    for at in (1.5,4.1,7.8,11.8):blink=min(blink,1-.94*max(0,1-abs(t-at)/.13))
    return {'hope':hope,'hurt':hurt,'openness':(.66+.3*hope-.23*hurt)*blink,
            'head_y':-12*hope+7*hurt,'head_angle':-2.0*hope+3.5*hurt,
            'gaze_x':5*hope-2*hurt,'gaze_y':2+5*hurt,
            'hand_raise':22*hope,'camera_zoom':1+.20*ease((t-8.3)/2.1),
            'passer_x':1500-310*(t-3),'phase':'waiting' if t<2.2 else 'hope' if t<7 else 'missed_connection'}


def foot(t,side,velocity=-310):
    """Stance cancels root travel; swing clears the floor rather than sliding."""
    phase=(t+side*.5)%1.;stride=abs(velocity)*.6
    if phase<.6:return -stride/2+stride*phase/.6,0
    p=(phase-.6)/.4
    return stride/2-stride*ease(p),-44*math.sin(math.pi*p)


def path(d,fill,stroke='#29272a',width=3,extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def ellipse(x,y,rx,ry,fill,extra=''):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'


def rect(x,y,w,h,fill,r=0,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" {extra}/>'


def eye(cx,cy,openness,gx,gy,key):
    hh=19*openness;eye_path=f'M {cx-24} {cy} Q {cx-2} {cy-hh*1.6} {cx+24} {cy} Q {cx+3} {cy+hh} {cx-24} {cy}'
    return (f'<defs><clipPath id="{key}"><path d="{eye_path}"/></clipPath></defs>'+path(eye_path,'#ded8c5','#635746',2)+
        f'<g clip-path="url(#{key})">'+ellipse(cx+gx,cy+gy,11,14,'#775132')+
        ellipse(cx+gx,cy+gy+1,5.3,8,'#171b20')+ellipse(cx+gx-3,cy+gy-4,2.3,3,'#f2e8cf')+'</g>'+
        path(f'M{cx-24} {cy} Q{cx} {cy-hh*1.6} {cx+24} {cy}','none','#332f2e',2.4))


def maya(t,x,y,scale=1,under=False):
    s=state(t);h=s['hope'];sad=s['hurt'];lift=s['head_y'];breath=math.sin(t*1.5)*1.2
    q=[f'<g transform="translate({x},{y}) scale({scale})">']
    # Full trousers and closed shoes remain beneath the foreground table.
    for side in (-1,1):
        q.append(path(f'M{side*28} 285 Q{side*61} 338 {side*53} 385 L{side*65} 431','none','#3d3b39',39))
        q.append(path(f'M{side*65-21} 424 Q{side*65+9} 420 {side*65+36} 438 Q{side*65+33} 450 {side*65-24} 447Z','#433830','#22252a',3))
    if under:return ''.join(q)+ '</g>'
    q=[f'<g transform="translate({x},{y}) scale({scale})">']
    q.append(path(f'M-62 {126+lift} Q0 {108+lift} 63 {130+lift} L75 277 Q0 309 -72 279Z','url(#cloth)','#302d2c',3))
    # Wrist on the mug stays anchored while shoulders and sleeves change with posture.
    q.append(path(f'M-60 {145+lift+breath} Q-98 211 -72 {300-s["hand_raise"]}','none','#655044',34))
    q.append(path(f'M60 {145+lift+breath} Q114 220 69 285','none','#6c5648',34))
    # Scarf, stitched cuffs and cloth folds.
    q.append(path(f'M-42 {117+lift} Q0 {149+lift} 44 {118+lift} L39 {147+lift} Q0 {173+lift} -43 {146+lift}Z','#343737','#252a2e',3))
    q.append(path(f'M-19 {145+lift} L-44 {236+lift} L-13 {231+lift} L5 {153+lift}Z','#3b3d3b','#252a2e',2))
    q.append(path(f'M-32 {157+lift} L-42 {217+lift} M-27 {164+lift} L-36 {222+lift}','none','#5d5d53',1))
    q.append(path('M-50 181Q-9 202 40 183 M-56 252Q0 270 56 250','none','#8a6e56',1.3))
    # A shaped wavy bob, ivory face, brows, lids and pupils form independent acting controls.
    q.append(f'<g transform="translate(0,{lift+breath}) rotate({s["head_angle"]})">')
    q.append(path('M-87-37 Q-116-105-48-127 Q25-155 87-100 Q117-53 102 26 Q100 86 121 119 Q101 143 77 126 Q68 156 39 125 L-63 135 Q-104 151-100 110 Q-126 87-109 54Z','url(#hair)','#26272a',3))
    q.append(path('M-72-67 Q-31-114 25-93 Q89-84 89-7 Q89 63 37 91 Q-15 116-64 64 Q-93 26-81-20Z','url(#skin)','#544b40',2.6))
    q.append(path('M14 22 Q29 34 12 37','none','#a58c6b',2))
    q.append(eye(-34,4,s['openness'],s['gaze_x'],s['gaze_y'],'maya-left'))
    q.append(eye(32,5,s['openness'],s['gaze_x'],s['gaze_y'],'maya-right'))
    q.append(path(f'M-62 {-24-9*h+8*sad} Q-37 {-35-10*h} -13 {-28-5*sad-7*h}','none','#4a3428',5))
    q.append(path(f'M13 {-28-5*sad-7*h} Q37 {-34-10*h} 60 {-23-8*h+8*sad}','none','#4a3428',5))
    q.append(path(f'M-17 63 Q0 {63+10*h-11*sad} 17 62','none','#675448',2.5))
    q.append(path('M-59 32 Q-36 45-17 33 M15 35Q38 45 56 33','none','#a69073',1.4,extra='opacity=".5"'))
    # Side-parted fringe; no bald or generic stick-figure replacement.
    q.append(path('M-85-14 Q-97-91-26-116 Q22-139 60-110 Q3-108-17-74 Q-43-37-86-18Z','#53382c','#2a292a',2.5))
    q.append(path('M-62-73 Q-13-91 6-110 M-77-43 Q-40-53-19-84 M42-110Q88-85 91-44','none','#8b6040',2))
    q.append(path('M80-66 Q105-17 86 39 Q79 83 104 114 Q82 123 73 102 Q61 61 75 29Z','#61412f','#332d29',2))
    q.append('</g>')
    # Small incomplete greeting, followed by a return to the table.
    yy=300-s['hand_raise']
    q.append(path(f'M-86 {yy-8} Q-88 {yy-23} -80 {yy-20} L-74 {yy-8} Q-76 {yy-30}-68 {yy-26} L-61 {yy-9} Q-60 {yy-27}-54 {yy-22} L-51 {yy-6} Q-39 {yy-10}-43 {yy+1} Q-57 {yy+18}-76 {yy+10}Z','#c5ae88','#685a48',1.8))
    q.append(path(f'M-70 {yy+5} L-62 {yy+8} M-61 {yy+2} L-54 {yy+4}','none','#927c60',1))
    # The cup has a fixed table contact. Hand and fingers wrap its left edge.
    q.append(path('M76 263 L79 302 Q101 316 123 302 L126 263Z','url(#cup)','#93836d',2))
    q.append(ellipse(101,264,25,6,'#d8ccb2'));q.append(ellipse(101,264,20,3.5,'#3a302a'))
    q.append(path('M126 272 Q148 269 142 290 Q137 300 124 294','none','#b5a78c',7))
    q.append(path('M62 278 Q69 270 78 276 L82 283 Q88 286 81 290 Q73 295 66 289Z','#cbb692','#72614d',1.8))
    q.append(path('M69 279Q75 282 80 280 M69 285Q75 288 81 286','none','#967e60',1))
    q.append('</g>');return ''.join(q)


def passer(t,x,y,scale,velocity=-310):
    if t<2.9 or t>9:return ''
    u=t-3;parts=[f'<g transform="translate({x},{y}) scale({scale})" opacity=".98">']
    for side in (0,1):
        fx,fy=foot(u,side,velocity/scale);hx=12 if side else -12
        parts.append(path(f'M{hx} 228 Q{fx*.45} 299 {fx} {375+fy}','none','#3a3e3b',31))
        parts.append(path(f'M{fx+16} {375+fy} L{fx-34} {379+fy} Q{fx-48} {395+fy} {fx+18} {393+fy}Z','#3a302a','#24282b',2))
    swing=16*math.sin(u*2*math.pi)
    parts.append(path(f'M-44 100 Q-55 167 {-48+swing} 234','none','#8b7a61',25))
    parts.append(ellipse(-48+swing,239,12,17,'#bba988'))
    parts.append(path('M-45 92 Q0 72 47 94 L51 228 Q0 245-50 226Z','#83745d','#2b3030',3))
    parts.append(path('M-45 92 L-17 87 -15 228 -49 226Z M15 87L47 94 51 228 17 232Z','#555b45','#2b3030',2))
    parts.append(path(f'M45 111 Q62 174 {47-swing} 237','none','#8b7a61',25));parts.append(ellipse(47-swing,242,12,16,'#bba988'))
    parts.append(path('M-55-53 Q-36-91 16-78 Q67-64 59-6 Q55 54 4 72 Q-47 56-55 16Z','#bfb295','#3b3b35',2.5))
    parts.append(eye(-28,0,.62,-5,1,'max-left'));parts.append(eye(26,1,.62,-5,1,'max-right'))
    parts.append(path('M-41-24Q-24-32-8-25 M8-25Q25-32 39-23','none','#5b5040',4))
    parts.append(path('M-16 44Q0 48 16 44','none','#72614c',2))
    parts.append('</g>');return ''.join(parts)


def svg_frame(t,portrait=False):
    w,h=(900,1600) if portrait else (1600,900);floor=1280 if portrait else 800
    mx,my,scale=(330,650,1.4) if portrait else (560,340,1)
    table=my+310*scale;chair=715 if portrait else 1095;lampx=730 if portrait else 1120
    s=state(t);z=s['camera_zoom'];cx=mx;cy=my+100
    q=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', '''<defs>
    <linearGradient id="wall" x2="0" y2="1"><stop stop-color="#10191e"/><stop offset="1" stop-color="#263035"/></linearGradient>
    <linearGradient id="night" x2="0" y2="1"><stop stop-color="#14232d"/><stop offset="1" stop-color="#26313a"/></linearGradient>
    <linearGradient id="skin" x1="0" x2="1"><stop stop-color="#e6d5b5"/><stop offset="1" stop-color="#c3ad89"/></linearGradient>
    <linearGradient id="hair" x1="0" x2="1"><stop stop-color="#423029"/><stop offset=".5" stop-color="#715039"/><stop offset="1" stop-color="#3c302b"/></linearGradient>
    <linearGradient id="cloth" x1="0" x2="1"><stop stop-color="#665345"/><stop offset=".6" stop-color="#7a6250"/><stop offset="1" stop-color="#55463e"/></linearGradient>
    <linearGradient id="cup" x1="0" x2="1"><stop stop-color="#cfbea0"/><stop offset="1" stop-color="#a7987f"/></linearGradient>
    <linearGradient id="seat" x2="0" y2="1"><stop stop-color="#71422f"/><stop offset="1" stop-color="#3f302b"/></linearGradient>
    <linearGradient id="table" x2="0" y2="1"><stop stop-color="#66432f"/><stop offset="1" stop-color="#342c29"/></linearGradient>
    <radialGradient id="light"><stop stop-color="#e7ac59" stop-opacity=".18"/><stop offset="1" stop-color="#e7ac59" stop-opacity="0"/></radialGradient>
    <radialGradient id="vignette"><stop offset=".55" stop-color="#02080d" stop-opacity="0"/><stop offset="1" stop-color="#02080d" stop-opacity=".5"/></radialGradient>
    </defs>''',rect(0,0,w,h,'url(#wall)')]
    q.append(f'<g transform="translate({cx*(1-z)*.45},{cy*(1-z)*.45}) scale({1+(z-1)*.45})">')
    windowbottom=floor-100
    for i in range(4):
        xx=70+i*(w-140)/4;ww=(w-140)/4-12
        q.append(rect(xx,85,ww,windowbottom-85,'url(#night)',10))
        q.append(rect(xx-5,78,7,windowbottom-62,'#403b32'))
        for j in range(8):
            px=xx+20+(j*53)%max(1,int(ww-35));py=160+(j*117)%(windowbottom-230)
            q.append(ellipse(px,py,6,11,'#b58b52',extra='opacity=".19"'))
        for j in range(13):
            px=xx+12+(j*37)%max(1,int(ww-20));py=100+((j*79+t*30)%(windowbottom-130))
            q.append(path(f'M{px} {py} l-3 21','none','#819196',1,extra='opacity=".22"'))
    q.append(rect(50,windowbottom,w-100,14,'#5a4633',4));q.append('</g>')
    # Near layers follow a stronger camera scale than the distant window.
    q.append(f'<g transform="translate({cx*(1-z)},{cy*(1-z)}) scale({z})">')
    q.append(rect(-500,floor,w+1000,h+600,'#20272a'))
    for yy in range(floor+15,h+400,60):q.append(path(f'M-500 {yy}H{w+500}','none','#343735',1))
    q.append(ellipse(lampx,table-160,470,500,'url(#light)'))
    # Seats establish specific places; the empty one remains visibly empty.
    for xx,ww in ((mx-100*scale,200*scale),(chair-105,210)):
        q.append(rect(xx,table-175,ww,184,'url(#seat)',22,extra='stroke="#292c2b" stroke-width="4"'))
        q.append(rect(xx-8,table+8,ww+16,30,'#60402f',10))
        q.append(path(f'M{xx+20} {table+32}L{xx+8} {floor} M{xx+ww-20} {table+32}L{xx+ww-8} {floor}','none','#272a2b',15))
    # Table legs, Maya and the top layer occlude in the correct order.
    q.append(path(f'M{mx-180} {table+40}L{mx-210} {floor+70} M{chair+30} {table+40}L{chair+60} {floor+70}','none','#2a2929',19))
    # Legs behind table, torso/face above it. The surface is below wrist/cup contact.
    q.append(maya(t,mx,my,scale,under=True))
    q.append(path(f'M{mx-210} {table+4}L{chair+80} {table+4}L{chair+150} {table+80}L{mx-165} {table+80}Z','url(#table)','#282a29',4))
    q.append(path(f'M{mx-165} {table+80}L{chair+150} {table+80}L{chair+150} {table+94}L{mx-165} {table+94}Z','#382e28','#252b2d',2))
    q.append(maya(t,mx,my,scale))
    # A saucer sits directly under the cup; the drawn cup bottom aligns with table height.
    q.append(ellipse(mx+101*scale,table+3,35*scale,7*scale,'#b5a589'))
    # Repaint small cup base? Saucer does not cover the cup body at local y<=310.
    q.append(rect(mx-155*scale,table+5,64*scale,40*scale,'#343b39',3,extra='transform="rotate(-8 '+str(mx-155*scale)+' '+str(table+5)+')"'))
    q.append(path(f'M{mx-149*scale} {table+11}l{53*scale} -7','none','#cabd9d',2))
    q.append(path(f'M{mx-120*scale} {table+53}l{55*scale} -17','none','#a28b62',4))
    # Lamp stays fixed in the set, with a readable pool on the empty place.
    ly=430 if portrait else 120
    q.append(path(f'M{lampx} -100V{ly}','none','#39382f',4))
    q.append(path(f'M{lampx-80} {ly+58}Q{lampx-55} {ly-7} {lampx} {ly}Q{lampx+54} {ly-7} {lampx+80} {ly+58}Z','#544331','#1c272c',3))
    q.append(ellipse(lampx,ly+58,78,8,'#d2a264'))
    # Max crosses the foreground with planted stance phases and eased airborne steps.
    px=s['passer_x']*(.88 if portrait else 1)
    q.append(passer(t,px,floor-393*(1.3 if portrait else 1.10),1.3 if portrait else 1.10,-310*(.88 if portrait else 1)))
    q.append('</g>');q.append(rect(0,0,w,h,'url(#vignette)'));q.append('</svg>')
    return ''.join(q)


def frame(t,width=1280,portrait=False):
    import cairosvg
    height=round(width*(16/9 if portrait else 9/16)/2)*2
    png=cairosvg.svg2png(bytestring=svg_frame(t,portrait).encode(),output_width=width,output_height=height)
    return Image.open(io.BytesIO(png)).convert('RGB')


def sound(out):
    """Original restrained synthetic score sketch/room tone, not a finished score."""
    sr=24000;n=int(DURATION*sr);rng=np.random.default_rng(19)
    noise=rng.normal(0,1,n);filtered=np.convolve(noise,np.ones(21)/21,mode='same');audio=filtered*.009
    def note(at,freq,amp,decay=2):
        start=int(at*sr);length=min(n-start,int(4*sr));t=np.arange(length)/sr
        tone=sum(np.sin(2*np.pi*freq*k*t)*math.exp(-.75*(k-1)) for k in range(1,5))
        env=(1-np.exp(-t*45))*np.exp(-t/decay)
        audio[start:start+length]+=amp*tone*env
    note(.5,220,.035);note(2.4,329.63,.024);note(8.6,196,.032);note(10.4,246.94,.025)
    # Quiet entrance bell and footsteps correspond to the passing action.
    note(2.3,1174.66,.011,.35)
    for at in np.arange(3.0,8.3,.5):
        start=int(at*sr);length=int(.09*sr);tt=np.arange(length)/sr
        audio[start:start+length]+=.022*np.sin(2*np.pi*85*tt)*np.exp(-tt*45)
    fade=np.minimum(np.arange(n)/(sr*.4),1)*np.minimum(np.arange(n)[::-1]/(sr*1.1),1);audio*=fade
    with wave.open(str(out),'wb') as f:
        f.setparams((1,2,sr,0,'NONE','not compressed'));f.writeframes((np.clip(audio,-.95,.95)*32767).astype('<i2').tobytes())


def render(out,width=1280,fps=12,portrait=False):
    if fps not in (12,24):raise ValueError('Choose 12 or 24 FPS')
    if width < 64 or width % 2:raise ValueError('Width must be an even integer of at least 64 pixels')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'opening.svg').write_text(svg_frame(0,portrait));height=round(width*(16/9 if portrait else 9/16)/2)*2
    count=DURATION*fps;ffmpeg='ffmpeg'
    cmd=[ffmpeg,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(out/'silent.mp4')]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as p:
        try:
            for i in range(count):
                im=frame(i/fps,width,portrait);p.stdin.write(im.tobytes())
                if i in (0,3*fps,9*fps,13*fps):im.save(out/f'frame-{i:03}.png')
            p.stdin.close()
            if p.wait():raise RuntimeError('Video encoding failed')
        except BaseException:
            p.kill();p.wait();raise
    sound(out/'score-sketch.wav')
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(out/'silent.mp4'),'-i',str(out/'score-sketch.wav'),'-c:v','copy','-c:a','aac','-b:a','128k','-shortest',str(out/'opening.mp4')],check=True)
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(out/'opening.mp4')]))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    from fractions import Fraction
    if int(video['nb_read_frames'])!=count or Fraction(video['avg_frame_rate'])!=fps:raise RuntimeError('Frame count/FPS verification failed')
    subprocess.run([ffmpeg,'-v','error','-i',str(out/'opening.mp4'),'-f','null','-'],check=True)
    (out/'render-report.json').write_text(json.dumps({'renderer':'original layered SVG/Cairo 2D animation','fps':fps,'decoded_frames':count,'seconds':DURATION,'width':width,'height':height,'stage':'first opening acting study, not the whole film','audio':'original synthetic motif, room tone and timed step/bell sketch; not final soundtrack','thumbnail_modified':False,'acting_beats':[{'at':t,**state(t)} for t in (0,3.5,6.5,9,13)],'limits':['Approved concept remains the identity target; simplified video drawings are a new adaptation.','Full-film shot coverage, other scene interactions and final sound/dialogue remain to build.']},indent=2)+'\n')
    print(f'Rendered {count} frames at {fps} FPS: {out/"opening.mp4"}',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--width',type=int,default=1280);p.add_argument('--fps',type=int,choices=[12,24],default=12);p.add_argument('--portrait',action='store_true');p.add_argument('--still',type=float)
    a=p.parse_args()
    if a.still is not None:
        out=Path(a.out);out.mkdir(parents=True,exist_ok=True);frame(a.still,a.width,a.portrait).save(out/'study.png')
    else:render(a.out,a.width,a.fps,a.portrait)


if __name__=='__main__':main()
