"""Original layered environments for travel and everyday physical interactions."""
from PIL import Image, ImageDraw


def environment(kind):
    from .render import font, glow
    im=Image.new('RGBA',(1920,1080),'#242b43');d=ImageDraw.Draw(im)
    if kind=='classroom':
        d.rectangle((0,0,1920,820),fill='#454359')
        d.polygon([(0,820),(1920,820),(1920,1080),(0,1080)],fill='#78685e')
        for x in range(-400,2200,240):
            d.line((960,820,x,1080),fill='#927f6f',width=2)
        for y in (870,960,1050): d.line((0,y,1920,y),fill='#927f6f',width=2)
        d.rounded_rectangle((600,180,1500,570),radius=10,fill='#193b3d',outline='#c9aa7d',width=16)
        d.text((1050,275),'WHAT IF?',font=font(66,True),fill='#dfebd6',anchor='mm')
        d.text((1050,380),'Choices  →  Consequences',font=font(34),fill='#b6d5c7',anchor='mm')
        d.line((720,455,1370,455),fill='#b9cdc3',width=3)
        d.rectangle((70,260,385,690),fill='#9db6b5',outline='#292e40',width=12)
        d.line((225,260,225,690),fill='#34384a',width=8)
        d.rectangle((1640,250,1870,820),fill='#9a7d64',outline='#292d3e',width=10)
        d.rectangle((1670,290,1840,515),fill='#9ba9a9')
        d.ellipse((1660,570,1676,586),fill='#e6d0a3')
        for x in (320,800,1280):
            d.polygon([(x,660),(x+300,660),(x+350,725),(x-40,725)],fill='#b89670',outline='#d0b18a')
            for xx in (x-20,x+315): d.line((xx,725,xx+5,825),fill='#343342',width=11)
        glow(im,(240,420),700,'#9faabd',50)
    elif kind=='field':
        d.rectangle((0,0,1920,660),fill='#8daeb6')
        d.ellipse((1510,120,1660,270),fill='#f4dfac')
        for x,y in ((100,180),(650,130),(1200,250)):
            for offset in (0,75,140):d.ellipse((x+offset,y,x+offset+150,y+60),fill='#c9d5cb')
        d.rectangle((0,610,1920,1080),fill='#507e66')
        d.polygon([(0,660),(1920,630),(1920,800),(0,890)],fill='#648b67')
        d.polygon([(0,930),(1920,760),(1920,880),(0,1070)],fill='#c1ae8b')
        d.rectangle((530,380,1230,640),fill='#b5a190')
        d.polygon([(480,380),(880,260),(1280,380)],fill='#56596a')
        for x in range(580,1210,125):
            for y in (430,535):d.rectangle((x,y,x+70,y+65),fill='#668592',outline='#d8c8b1',width=4)
        d.rectangle((830,535,930,640),fill='#62594f')
        d.text((880,375),'COMMUNITY SCHOOL',font=font(28,True),fill='#f1dfc3',anchor='mm')
        for x in (170,1570,1780):
            d.rectangle((x,480,x+27,690),fill='#6a5944')
            for dx,dy,r in ((-30,0,100),(70,20,105),(10,-90,105)):
                d.ellipse((x+dx-r,480+dy-r,x+dx+r,480+dy+r),fill='#3b6557')
        for x in (1400,1670):d.line((x,650,x,780),fill='#edf0dd',width=10)
        d.line((1400,650,1670,650),fill='#edf0dd',width=10)
        d.line((1400,780,1670,780),fill='#b7c9a6',width=3)
    elif kind=='bank':
        d.rectangle((0,0,1920,820),fill='#645f66')
        d.rectangle((0,820,1920,1080),fill='#bbb0a2')
        for x in range(0,1920,240):d.line((x,820,x-160,1080),fill='#8e877f',width=2)
        for y in (880,970):d.line((0,y,1920,y),fill='#9e958b',width=2)
        d.rectangle((580,110,1330,215),fill='#252f41',outline='#cfb67e',width=5)
        d.text((955,165),'THE CITY BANK',font=font(53,True),fill='#e9d6aa',anchor='mm')
        for x in (180,1520):
            d.rectangle((x,240,x+95,810),fill='#b5aa98',outline='#d1c4ac',width=8)
            d.rectangle((x-20,220,x+115,250),fill='#cfbda1')
        d.rounded_rectangle((1170,270,1740,740),radius=20,fill='#353d4e',outline='#8e9ba7',width=9)
        d.ellipse((1260,315,1690,715),fill='#5b6878',outline='#b2bdc4',width=12)
        d.ellipse((1305,355,1645,675),outline='#8999a8',width=7)
        d.ellipse((1410,450,1540,575),outline='#c5ccd0',width=10)
        d.line((1475,435,1475,590),fill='#c5ccd0',width=9)
        d.line((1390,512,1560,512),fill='#c5ccd0',width=9)
        d.rounded_rectangle((360,535,1110,750),radius=12,fill='#8b6652',outline='#c49d72',width=5)
        d.rectangle((340,520,1130,550),fill='#d9c5a4')
        d.rectangle((660,420,820,510),fill='#202c3d',outline='#788a99',width=4)
        d.line((740,510,740,525),fill='#566174',width=12)
        glow(im,(960,250),800,'#dec292',45)
    elif kind=='cafe':
        d.rectangle((0,0,1920,830),fill='#5e4a50')
        d.rectangle((0,830,1920,1080),fill='#302e3b')
        d.rectangle((90,160,900,650),fill='#79979e',outline='#c1a37f',width=14)
        for x in (350,620):d.line((x,160,x,650),fill='#52454a',width=10)
        d.line((90,400,900,400),fill='#52454a',width=10)
        d.rectangle((1040,310,1800,390),fill='#352e3b')
        d.text((1420,255),'THE CORNER CAFÉ',font=font(45,True),fill='#e9c18f',anchor='mm')
        d.rounded_rectangle((1250,420,1590,635),radius=18,fill='#6f8190',outline='#b7b5b2',width=6)
        d.rectangle((1300,465,1540,550),fill='#243b49')
        for x in (1340,1460):
            d.line((x,550,x,590),fill='#ddd8ca',width=10)
            d.rectangle((x-17,598,x+17,620),fill='#e8d2b2')
        d.rectangle((1120,630,1760,667),fill='#bd956e')
        for x in (300,970,1640):
            d.line((x,70,x,210),fill='#292a35',width=6)
            d.polygon([(x-80,260),(x-35,205),(x+35,205),(x+80,260)],fill='#d6b080')
            glow(im,(x,310),230,'#efbe83',75)
        # Resting cup bottom and the actor's hand use this same table height.
        d.rounded_rectangle((1140,710,1740,738),radius=10,fill='#d0a47b')
        for x in (1170,1690):d.rectangle((x,738,x+20,860),fill='#292a35')
    return im
