"""Native-resolution layered compositor: cached sets, fresh articulated actors each frame."""
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from PIL import Image
from cairosvg.parser import Tree
from cairosvg.surface import PNGSurface
from .film_art import svg,background,DEFS
from .layered_film import rect,path

NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)


def raster(source,width,height):
    surface=PNGSurface(Tree(bytestring=source.encode()),None,96,output_width=width,output_height=height)
    surface.cairo.flush()
    # Cairo stores premultiplied BGRA. Decode as RGBa before unpremultiplying.
    image=Image.frombytes('RGBa',(width,height),bytes(surface.cairo.get_data()),'raw','BGRa',surface.cairo.get_stride(),1).convert('RGBA')
    surface.finish();return image


def canvas(content,w,h):
    return f'<svg xmlns="{NS}" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{DEFS}</defs>{content}</svg>'


@lru_cache(maxsize=4)
def set_image(setting,width,height,portrait):
    w,h=(900,1600) if portrait else (1600,900)
    return raster(canvas(background(setting,w,h,0),w,h),width,height)


@lru_cache(maxsize=2)
def vignette(width,height,portrait):
    w,h=(900,1600) if portrait else (1600,900)
    return raster(canvas(rect(0,0,w,h,'url(#vignette)'),w,h),width,height)


def frame(shot,t,width,portrait=False):
    w,h=(900,1600) if portrait else (1600,900);height=round(width*h/w/2)*2
    tree=ET.fromstring(svg(shot,t,portrait));groups=[x for x in tree if x.tag==f'{{{NS}}}g']
    transform=groups[0].attrib['transform'];tx,ty,scale=[float(x) for x in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',transform)]
    tx*=width/w;ty*=height/h
    result=set_image(shot['setting'],width,height,portrait).transform((width,height),Image.Transform.AFFINE,
        (1/scale,0,-tx/scale,0,1/scale,-ty/scale),resample=Image.Resampling.BILINEAR,fillcolor=(23,33,40,255))
    rain=[]
    for i in range(12):
        x=(i*137+t*35)%w;y=(i*89+t*55)%(h*.76)
        rain.append(path(f'M{x} {y}l-2 18','none','#91a0a7',.8,extra='opacity=".14"'))
    if any(a['action']=='open_door' for a in shot['actors']):
        from .layered_film import ease
        angle=ease(min(t/2,1));rain.append(path(f'M{w*.9} {h*.33}L{w*(.73+.14*angle)} {h*.36}V{h*.88}L{w*.9} {h*.88}Z','#4f4233','#252d31',3))
    dynamic=f'<g transform="{transform}">'+''.join(rain)+'</g>'+ET.tostring(groups[1],encoding='unicode')
    foreground=raster(canvas(dynamic,w,h),width,height)
    result.alpha_composite(foreground);result.alpha_composite(vignette(width,height,portrait))
    texts=[n for n in tree if n.tag==f'{{{NS}}}text']
    if texts:result.alpha_composite(raster(canvas(''.join(ET.tostring(n,encoding='unicode') for n in texts),w,h),width,height))
    return result.convert('RGB')
