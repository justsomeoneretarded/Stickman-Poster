"""Small deterministic Pillow backend for CI, not a replacement Motion Canvas fork.

All illustrations are procedural original artwork. Frame times are absolute,
so rerendering a scene does not depend on having rendered earlier frames.
"""
import math
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from .project import caption_chunks

W, H = 1920, 1080
TEAL, GOLD, WHITE = "#56e2d0", "#ffc587", "#f5f0e8"


@lru_cache(maxsize=100)
def font(size, bold=False):
    override = os.environ.get("STUDIO_FONT_BOLD" if bold else "STUDIO_FONT")
    names = [override] if override else []
    names += (["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
              if bold else ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for name in names:
        if name and Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)


def circle(draw, x, y, r, fill, outline=None, width=1):
    draw.ellipse((x-r, y-r, x+r, y+r), fill=fill, outline=outline, width=width)


def line(draw, points, fill, width):
    draw.line(points, fill=fill, width=width, joint="curve")
    r = width / 2
    for x, y in [points[0], points[-1]]:
        circle(draw, x, y, r, fill)


def fit_text(draw, text, x, y, size, maxwidth, fill=WHITE, bold=False, anchor="mm"):
    while size > 18 and draw.textlength(text, font=font(size, bold)) > maxwidth:
        size -= 1
    draw.text((x, y), text, font=font(size, bold), fill=fill, anchor=anchor)


def glow(image, xy, radius, color, opacity=100):
    """Radial glow at low resolution; normally cached with static backgrounds."""
    small = Image.new("RGBA", (W//4, H//4))
    d = ImageDraw.Draw(small)
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    for r in range(int(radius/4), 0, -2):
        alpha = int(opacity * (1-r/(radius/4))**2)
        x, y = xy[0]/4, xy[1]/4
        circle(d, x, y, r, (*rgb, alpha))
    image.alpha_composite(small.resize((W, H), Image.Resampling.BILINEAR))


@lru_cache(maxsize=8)
def background(location):
    if location in {"classroom", "field", "bank", "cafe"}:
        from .locations import environment
        return environment(location)
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([16, 24, 45])[None, None, :]
    bottom = np.array([50, 38, 64])[None, None, :]
    pixels = np.broadcast_to(top*(1-y)+bottom*y, (H, W, 3)).astype("uint8").copy()
    im = Image.fromarray(pixels).convert("RGBA")
    d = ImageDraw.Draw(im)
    if location == "room":
        d.rectangle((140, 150, 1190, 700), fill="#191f38", outline="#4b4261", width=12)
        # Sunset window, distant city silhouettes.
        sky = Image.new("RGBA", (1010, 510), "#604b74")
        sd = ImageDraw.Draw(sky)
        for i in range(10):
            x, topy = i*112-20, 220+(i*71)%170
            sd.rectangle((x, topy, x+85, 510), fill="#302a49")
            for row in range(5):
                for col in range(3):
                    if (row+col+i)%3:
                        sd.rectangle((x+12+col*22, topy+18+row*43, x+19+col*22, topy+29+row*43), fill="#e8bc94")
        im.alpha_composite(sky, (160, 170))
        d = ImageDraw.Draw(im)
        for x in (485, 830): d.rectangle((x, 156, x+12, 699), fill="#25283f")
        d.rectangle((145, 430, 1188, 440), fill="#25283f")
        d.rectangle((1300, 300, 1730, 320), fill="#171c31")
        for i in range(7):
            d.rounded_rectangle((1320+i*49, 225+(i%3)*14, 1352+i*49, 300), radius=3,
                                fill=["#5d6583", "#927568", "#456a78"][i%3])
        d.rectangle((0, 830, W, H), fill="#151c30")
        d.line((0, 830, W, 830), fill="#6c536d", width=3)
        d.polygon([(130, 700), (1190, 700), (1500, 830), (0, 830)], fill="#3a344c")
        glow(im, (700, 400), 780, "#d29b8d", 65)
    elif location == "street":
        for i in range(9):
            x, roof = i*250-50, 180+(i*79)%190
            d.rectangle((x, roof, x+220, 850), fill=["#292d49", "#34304b", "#222a40"][i%3])
            for row in range(6):
                for col in range(3):
                    if (row*7+col+i)%4:
                        xx, yy = x+30+col*60, roof+40+row*88
                        d.rectangle((xx, yy, xx+24, yy+39), fill="#b59a80" if (row+col+i)%3 else "#455a76")
        d.rectangle((0, 830, W, H), fill="#141c2d")
        d.rectangle((0, 830, W, 838), fill="#747083")
        for x in (220, 1650):
            line(d, [(x, 835), (x, 330), (x+80, 330)], "#131a29", 12)
            d.ellipse((x+50, 325, x+120, 350), fill=GOLD)
            glow(im, (x+85, 370), 280, GOLD, 160)
    elif location == "stage":
        for x in range(0, W, 90):
            d.rectangle((x, 100, x+45, 830), fill="#26243f")
        d.ellipse((230, 660, 1700, 965), fill="#3a3659", outline="#5f607e", width=4)
        for x in (430, 960, 1490):
            beam = Image.new("RGBA", (W, H)); bd = ImageDraw.Draw(beam)
            bd.polygon([(x-16, 100), (x+16, 100), (x+210, 870), (x-210, 870)], fill=(210, 218, 234, 17))
            im.alpha_composite(beam)
        glow(im, (960, 500), 650, "#8479b9", 70)
    else:
        d.rounded_rectangle((170, 230, 1750, 825), radius=28, fill="#18263b", outline="#36536b", width=3)
        for x in range(210, 1740, 80): d.line((x, 250, x, 800), fill="#203248", width=1)
        for yy in range(260, 810, 80): d.line((190, yy, 1730, yy), fill="#203248", width=1)
        glow(im, (1200, 500), 600, "#319e9f", 55)
    return im


def character(t, action="idle", color="#ea996b", secondary=False, speaking=False, gait_phase=None, hand_target=None, held_prop="none", role=""):
    im = Image.new("RGBA", (420, 650))
    d = ImageDraw.Draw(im)
    root = (205, 405)
    sway = math.sin(t*2.2)*2 + (12 if action=="run" else 0)
    neck = (205+sway, 265)
    shoulder_l, shoulder_r = (169+sway, 285), (241+sway, 285)
    hip_l, hip_r = (185, 405), (225, 405)
    if action in {"walk", "run"}:
        phase = gait_phase if gait_phase is not None else t*(10 if action=="run" else 7)
        legs=[]
        for hip,offset,base in ((hip_l,0,180),(hip_r,.5,235)):
            cycle=(phase/math.tau+offset)%1
            stance=.48 if action=="run" else .62
            span=160*stance
            if cycle<stance:
                footx=base+span/2-span*cycle/stance
                footy=575
            else:
                swing=(cycle-stance)/(1-stance)
                footx=base-span/2+span*(swing*swing*(3-2*swing))
                footy=575-(60 if action=="run" else 35)*math.sin(swing*math.pi)
            ankle=(footx,footy)
            knee=joint(hip,ankle,100,100,-1)
            legs.append([hip,knee,ankle])
    elif action == "float":
        legs = [[hip_l, (150, 465), (170+math.sin(t*4)*22, 530)],
                [hip_r, (260, 470), (285+math.cos(t*4)*20, 530)]]
    else:
        legs = [[hip_l, (174, 493), (160, 575)], [hip_r, (234, 493), (247, 575)]]
    for leg in legs:
        line(d, [(x-3,y) for x,y in leg], GOLD, 13)
        line(d, leg, "#151b2c", 10)
        line(d, [leg[-1], (leg[-1][0]+22,leg[-1][1])], "#111827", 14)
    d.rounded_rectangle((162+sway, 270, 248+sway, 420), radius=17, fill=color)
    d.polygon([(163+sway, 283), (177+sway, 277), (177+sway, 408), (163+sway, 411)], fill="#fbcf9c")
    d.line((192+sway, 282, 192+sway, 321), fill=WHITE, width=3)
    d.line((211+sway, 282, 211+sway, 321), fill=WHITE, width=3)
    d.line((188+sway, 391, 230+sway, 391), fill="#b87964", width=3)
    arms = [[shoulder_l, (142, 355), (148, 400)], [shoulder_r, (269, 352), (274, 400)]]
    if action == "point": arms[1] = [shoulder_r, (295, 300), (358, 273+math.sin(t*2)*3)]
    elif action == "think": arms[1] = [shoulder_r, (279, 330), (244, 245)]
    elif action in {"float", "celebrate"}:
        arms = [[shoulder_l, (120, 245), (110, 185+math.sin(t*4)*12)],
                [shoulder_r, (291, 239), (314, 181-math.sin(t*4)*12)]]
    elif action == "worried": arms[1] = [shoulder_r, (290, 245), (259, 180)]
    elif action in {"walk", "run"}:
        k = math.sin(gait_phase if gait_phase is not None else t*7)*(42 if action=="run" else 24)
        arms[0] = [shoulder_l, (140-k, 340), (145-k, 392)]
        arms[1] = [shoulder_r, (274+k, 340), (280+k, 392)]
    if hand_target is not None:
        elbow=joint(shoulder_r,hand_target,90,95,1)
        arms[1]=[shoulder_r,elbow,hand_target]
    for arm in arms:
        line(d, arm[:2], color, 19)
        line(d, arm[1:], GOLD, 11)
        circle(d, *arm[-1], 11, "#161b2b")
    headx, heady = neck[0], 207+sway
    circle(d, headx-3, heady-2, 61, GOLD)
    circle(d, headx, heady, 59, "#121a2b")
    if secondary:
        d.arc((headx-64, heady-62, headx+64, heady+45), 180, 350, fill="#9bc8ba", width=13)
    blink = int(t*30)%129 in (0, 1, 2)
    for x in (headx-20, headx+20):
        if blink: d.line((x-6,heady-2,x+6,heady-2), fill=WHITE, width=4)
        else: circle(d,x,heady,5,WHITE)
    if speaking:
        opening = 3 + 8 * abs(math.sin(t * 12.7))
        d.ellipse((headx-11, heady+20-opening/2, headx+11, heady+24+opening), fill=WHITE)
    elif action == "worried":
        d.arc((headx-16,heady+20,headx+16,heady+48),180,360,fill=WHITE,width=4)
        d.line((headx-29,heady-17,headx-13,heady-24),fill=WHITE,width=4)
        d.line((headx+13,heady-24,headx+29,heady-17),fill=WHITE,width=4)
    elif action in {"float", "celebrate", "idle"}:
        d.arc((headx-18,heady+4,headx+18,heady+33),0,180,fill=WHITE,width=4)
    else:
        d.line((headx-9,heady+25,headx+9,heady+25),fill=WHITE,width=4)
    if role=="police":
        d.rounded_rectangle((headx-48,heady-86,headx+48,heady-55),radius=7,fill="#28557f",outline=GOLD,width=2)
        d.rectangle((headx-64,heady-57,headx+65,heady-48),fill="#1d3654")
        d.regular_polygon((headx,heady-68,10),5,fill=GOLD)
        d.regular_polygon((224+sway,320,11),5,fill=GOLD)
    if held_prop!="none":
        hand=hand_target or arms[1][-1]
        held_object(d,hand,held_prop)
        circle(d,*hand,9,"#161b2b")
    return im


def joint(start,end,upper,lower,bend=1):
    dx,dy=end[0]-start[0],end[1]-start[1]
    distance=max(.001,math.hypot(dx,dy))
    reach=min(distance,upper+lower-.01)
    along=(upper*upper-lower*lower+reach*reach)/(2*reach)
    height=math.sqrt(max(0,upper*upper-along*along))
    ux,uy=dx/distance,dy/distance
    return (start[0]+along*ux-bend*height*uy,start[1]+along*uy+bend*height*ux)


def held_object(d,hand,kind):
    x,y=hand
    if kind=="cup":
        d.arc((x-15,y-11,x+4,y+11),250,110,fill=GOLD,width=5)
        d.rounded_rectangle((x-48,y-19,x-11,y+21),radius=4,fill="#e6c3a0",outline=WHITE,width=2)
        d.ellipse((x-48,y-24,x-11,y-13),fill="#f5e2c5")
        d.ellipse((x-44,y-22,x-15,y-16),fill="#593e36")
    elif kind=="bag":
        d.arc((x-18,y-2,x+18,y+36),180,360,fill="#dfc584",width=6)
        d.rounded_rectangle((x-37,y+19,x+37,y+92),radius=12,fill="#bb935d",outline="#f5dfab",width=3)
        d.text((x,y+55),"$",font=font(35,True),fill="#573e2a",anchor="mm")
    elif kind=="phone":
        d.rounded_rectangle((x-33,y-53,x-2,y+2),radius=5,fill="#172332",outline=GOLD,width=2)
        d.rectangle((x-29,y-46,x-6,y-8),fill="#5f9ab5")


def put_character(image, x, floor, scale, t, action, secondary=False, levitate=False, color=None, speaking=False, tilt=0, facing_left=False, gait_phase=None, hand_target=None, held_prop="none", role=""):
    body = character(t, action, color or ("#79baa9" if secondary else "#ea996b"), secondary, speaking, gait_phase, hand_target, held_prop, role)
    if facing_left:
        body = ImageOps.mirror(body)
    if tilt:
        body = body.rotate(tilt, Image.Resampling.BICUBIC, center=(205, 575))
    w, h = round(body.width*scale), round(body.height*scale)
    body = body.resize((w,h),Image.Resampling.LANCZOS)
    lift = (95+math.sin(t*2)*18) if levitate else 0
    px, py = round(x-205*scale), round(floor-575*scale-lift)
    d = ImageDraw.Draw(image)
    d.ellipse((x-60*scale,floor-5,x+65*scale,floor+16),fill=(5,9,18,180))
    image.alpha_composite(body,(px,py))


def prop(image, x, y, angle=0):
    cup = Image.new("RGBA",(180,150)); d=ImageDraw.Draw(cup)
    d.arc((105,38,167,108),260,100,fill=GOLD,width=12)
    d.rounded_rectangle((35,25,121,112),radius=12,fill="#dfb895",outline="#ffe0b8",width=3)
    d.ellipse((35,18,121,39),fill="#f5d9bd")
    d.ellipse((44,23,112,35),fill="#614941")
    d.line((45,67,110,67),fill="#6faeab",width=9)
    cup=cup.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    aura=Image.new("RGBA",cup.size);ad=ImageDraw.Draw(aura)
    ad.ellipse((0,0,cup.width,cup.height),fill=(86,226,208,55))
    image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(24)),(round(x-cup.width/2),round(y-cup.height/2)))
    image.alpha_composite(cup,(round(x-cup.width/2),round(y-cup.height/2)))


def frame(scene, local_t, width, height, preview=True):
    if scene.get("visual_style")=="expressive-v2":
        from .cinematic import frame as expressive_frame
        return expressive_frame(scene,local_t,width,height,preview)
    im=background(scene["location"]).copy()
    t=local_t
    d=ImageDraw.Draw(im)
    if scene["location"] == "room":
        table_y=710 if scene.get("staging")=="drink" else 650
        d.rounded_rectangle((1110,table_y,1620,table_y+27),radius=8,fill="#b29288")
        d.rectangle((1140,676,1154,845),fill="#1a2132")
        d.rectangle((1580,676,1594,845),fill="#1a2132")
    focus_x = W / 2
    if scene.get("blocking") and scene.get("cast_members"):
        from .animation import draw_cast
        focus_x=draw_cast(im,scene,t)
    elif scene.get("cast_members"):
        members = scene["cast_members"]
        positions = {1: [850], 2: [640, 1280], 3: [430, 960, 1490]}[len(members)]
        colors = {"female": "#ea996b", "male1": "#79baa9", "male2": "#a795df"}
        duration = max(scene["duration"], .01)
        progress = min(1, t / duration)
        entrance = min(1, t / min(1.6, duration*.35))
        ease = entrance * entrance * (3 - 2 * entrance)
        cinematic = scene.get("cinematic", False)
        speaker_x = positions[0]
        speaker_y = 850
        for i, (member, base_x) in enumerate(zip(members, positions)):
            speaking = member["id"] == scene["speaker"]
            x = base_x
            action = scene["action"] if speaking else "idle"
            moving = False
            if cinematic and speaking:
                movement = scene.get("movement", "stay")
                if movement == "enter":
                    x += (-280 if base_x < 960 else 280) * (1-ease)
                    moving = entrance < 1
                elif movement == "cross":
                    x += 140 * math.sin(progress * math.pi)
                    moving = .05 < progress < .95
                elif movement == "approach":
                    x += (960-base_x) * .30 * ease
                    moving = entrance < 1
                if moving:
                    action = "walk"
                elif scene.get("prop", "none") != "none" and action == "idle":
                    action = "point"
            elif cinematic and .25 < progress < .45:
                action = "think" if i % 2 else "worried"
            floor = 850 + (abs(math.sin(t*7))*5 if moving else 0)
            tilt = (math.sin(t*2+i)*1.5 if cinematic else 0)
            put_character(im, x, floor, .83, t+i*.4, action,
                          color=colors.get(member["voice"], ["#ea996b", "#79baa9", "#a795df"][i]),
                          speaking=speaking and cinematic, tilt=tilt,
                          levitate=action == "float", facing_left=cinematic and x > 1150)
            d = ImageDraw.Draw(im)
            if speaking:
                speaker_x, speaker_y = x, floor
        focus_x = speaker_x
        if cinematic and scene.get("prop", "none") != "none":
            # Prop motion is tied to the acting beat, with anticipation and settling.
            drift = math.sin(t*1.7)*18
            px = 1170 + math.sin(t*.65)*35
            py = speaker_y - 235 - 55 * math.sin(progress*math.pi) + drift
            kind = scene["prop"]
            if kind == "cup":
                prop(im, px, py, math.sin(t*1.2)*9)
            elif kind == "orb":
                glow(im, (px, py), 110, "#56e2d0", 100)
                d = ImageDraw.Draw(im)
                circle(d, px, py, 30, TEAL, WHITE, 3)
                for j in range(7):
                    a = t*1.3 + j*math.tau/7
                    circle(d, px+62*math.cos(a), py+40*math.sin(a), 3, GOLD)
            elif kind == "phone":
                d = ImageDraw.Draw(im)
                d.rounded_rectangle((px-27,py-46,px+27,py+46), radius=8, fill="#111827", outline=GOLD,width=3)
                d.rectangle((px-20,py-33,px+20,py+29),fill="#467c9a")
                circle(d,px,py+37,3,WHITE)
    elif scene["location"] == "diagram":
        put_character(im,430,815,.79,t,"point")
        d=ImageDraw.Draw(im)
        d.ellipse((920,310,1430,790),outline="#3c6974",width=3)
        for i in range(8):
            a=t*.25+i*math.tau/8
            circle(d,1175+255*math.cos(a),550+240*math.sin(a),5,TEAL)
        remaining=max(0,10-int(t*2))
        fit_text(d,str(remaining).zfill(2),1170,505,160,400,TEAL,True)
        fit_text(d,"SECONDS",1170,635,26,400,WHITE,True)
    else:
        x=690 if scene["location"]!="stage" else 730
        if scene["action"]=="walk": x+=t*24
        put_character(im,x,850,.93,t,scene["action"],levitate=scene["action"]=="float")
        if scene.get("secondary"):
            put_character(im,1250,850,.84,t+.7,"worried" if scene.get("levitate") else "celebrate",True,
                          levitate=scene.get("levitate",False))
        if scene.get("levitate"):
            px,py=1390+math.sin(t*.9)*42,520+math.sin(t*1.7)*23
            prop(im,px,py,math.sin(t)*12)
            d=ImageDraw.Draw(im)
            for i in range(18):
                a=t*.45+i*2.39996;r=92+(i*29)%90
                circle(d,px+math.cos(a)*r,py+math.sin(a)*r*.65,2+i%3,(112,236,220,130))
    # Subtle deterministic camera push; HUD and captions remain screen-space.
    zoom=1+(scene.get("camera_zoom",1)-1)*min(1,t/max(scene["duration"],.01))
    if scene.get("cinematic"):
        shot_zoom = 1.0 if scene.get("staging") in {"chase","travel"} else {"wide": 1.0, "medium": 1.12, "close": 1.48}.get(scene.get("shot"), 1.0)
        zoom *= shot_zoom
    if zoom>1:
        cw,ch=W/zoom,H/zoom
        cx = min(W-cw/2, max(cw/2, W/2 + (focus_x-W/2)*.65)) if scene.get("cinematic") else W/2
        cy = H/2 + (30 if scene.get("shot") == "close" else 0)
        cy = min(H-ch/2, max(ch/2, cy))
        im=im.crop((cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2)).resize((W,H),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,61),fill="#080e1b")
    d.rectangle((0,1018,W,H),fill="#080e1b")
    from .text_policy import label_for
    label=label_for(scene)
    if label:fit_text(d,label,W/2,150,35,1600,bold=True)
    # Estimated phrase captions, deliberately not claimed as forced alignment.
    words=scene.get("narration","").split()
    chunks=caption_chunks(scene.get("narration",""))
    position=min(len(words)-1,int(t/max(scene["duration"],.01)*len(words)))
    if chunks and scene.get("screen_text","minimal")=="captions":
        cursor=0
        chosen=chunks[-1]
        for chunk in chunks:
            cursor+=len(chunk)
            if position<cursor:
                chosen=chunk
                break
        text=" ".join(chosen)
        tw=d.textlength(text,font=font(31))
        d.rounded_rectangle((W/2-tw/2-28,925,W/2+tw/2+28,990),radius=15,fill="#101a2c")
        fit_text(d,text,W/2,957,31,1600)
    if preview:
        d.text((W-100,30),"DEVELOPMENT PREVIEW · NO NARRATION",font=font(19),fill="#b6c4d4",anchor="rm")
    fade=min(1,t/.3,(scene["duration"]-t)/.3)
    if fade<1:
        im=Image.blend(Image.new("RGBA",im.size,"#080e1b"),im,max(0,fade))
    return im.convert("RGB").resize((width,height),Image.Resampling.LANCZOS)
