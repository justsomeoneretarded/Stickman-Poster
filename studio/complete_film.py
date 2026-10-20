"""Title/brief to real layered animation, measured dialogue, sound, subtitles and deliverables."""
import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path


def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')


def plan(args):
    from .film_concept import make_request
    from .film_director import develop
    request=make_request(args.title,args.description,args.minutes,args.quality,args.voices,args.fps,args.characters)
    root=Path(args.out);long=develop(request,root/'long-form',args.model_dir)
    short_request=copy.deepcopy(request);short_request['minutes']=args.short_seconds/60
    short_request['description']=('Create a standalone compact adaptation of the following long-film story, with its own resolved emotional beat. Preserve its characters, premise and tone. '
        'It is not an unresolved trailer. Original brief: '+request['description']+'\nLong film: '+long['story'])
    develop(short_request,root/'short-form',args.model_dir,short=True)
    speech=any(c['asset']=='speech' for p in ('long-form','short-form') for seq in read(root/p/'film.json')['scenes'] for s in seq['shots'] for c in s['cues'])
    write(root/'plan-status.json',{'speech_needed':speech,'phase':'directed; not yet rendered'})
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('speech='+str(speech).lower()+'\n')


def picture(package,portrait,width=None):
    from .film_art import frame
    from fractions import Fraction
    import numpy as np
    package=Path(package);film=read(package/'film.json');request=read(package/'request.json');fps=request['fps']
    width=width or ((1080 if portrait else 1920) if request['resolution']=='1080p' else (2160 if portrait else 3840))
    height=round(width*(16/9 if portrait else 9/16)/2)*2
    output=package/'video';output.mkdir(exist_ok=True);clips=output/'shots';clips.mkdir(exist_ok=True)
    art_hash=hashlib.sha256(Path(__file__).with_name('film_art.py').read_bytes()+Path(__file__).with_name('layered_film.py').read_bytes()).hexdigest()
    images=[];reports=[];count=0
    for sequence in film['scenes']:
        for shot in sequence['shots']:
            frames=round(shot['seconds']*fps);count+=frames;path=clips/(shot['id']+'.mp4');receipt=clips/(shot['id']+'.json')
            signature=hashlib.sha256(json.dumps([shot,width,height,fps,portrait,art_hash],sort_keys=True).encode()).hexdigest()
            cache=path.exists() and receipt.exists() and read(receipt).get('signature')==signature
            if not cache:
                print(f'Rendering {package.name} {shot["id"]}: {frames} actual frames',flush=True)
                cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-an',
                     '-c:v','libx264','-preset','fast','-threads','2','-crf','18','-pix_fmt','yuv420p',str(path)]
                with subprocess.Popen(cmd,stdin=subprocess.PIPE) as p:
                    try:
                        for i in range(frames):
                            im=frame(shot,i/fps,width,portrait);p.stdin.write(im.tobytes())
                            if i==frames//2:
                                im.thumbnail((400,712) if portrait else (640,360));im.save(clips/(shot['id']+'.jpg'),quality=90)
                        p.stdin.close()
                        if p.wait():raise RuntimeError('Shot encoding failed: '+shot['id'])
                    except BaseException:p.kill();p.wait();raise
                write(receipt,{'signature':signature,'frames':frames})
            images.append(clips/(shot['id']+'.jpg'));reports.append({'shot':shot['id'],'frames':frames,'seconds':shot['seconds'],'setting':shot['setting'],'description':shot['description'],'cached':cache})
    concat=output/'concat.txt';concat.write_text(''.join("file '"+str((clips/(s['shot']+'.mp4')).resolve())+"'\n" for s in reports))
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(package/'audio'/'mix.wav'),
                    '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(output/'final.mp4')],check=True)
    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(output/'final.mp4')]))['streams']
    video=next(s for s in streams if s['codec_type']=='video');audio=next(s for s in streams if s['codec_type']=='audio')
    if int(video['nb_read_frames'])!=count or Fraction(video['avg_frame_rate'])!=fps:raise RuntimeError('Final frame count or FPS mismatch')
    if (video['width'],video['height'])!=(width,height):raise RuntimeError('Final dimensions mismatch')
    if abs(float(video['duration'])-float(audio['duration']))>max(.1,1/fps):raise RuntimeError('Picture/audio duration mismatch')
    subprocess.run(['ffmpeg','-v','error','-i',str(output/'final.mp4'),'-f','null','-'],check=True)
    from PIL import Image
    cols=4;tw=180 if portrait else 240;th=320 if portrait else 135
    sheet=Image.new('RGB',(cols*tw,math.ceil(len(images)/cols)*th),'#172127')
    for i,path in enumerate(images):
        im=Image.open(path).convert('RGB');im.thumbnail((tw,th));sheet.paste(im,((i%cols)*tw,(i//cols)*th))
    sheet.save(output/'contact-sheet.jpg',quality=90)
    write(output/'render-report.json',{'status':'rendered and fully decoded','renderer':'original articulated layered SVG/Cairo',
        'width':width,'height':height,'fps':fps,'frames':count,'seconds':count/fps,'audio':True,'shots':reports,
        'not_certified':['Human artistic impact','Reference-film equivalence','Human voice-similarity/listening approval']})
    print(f'Complete video: {output/"final.mp4"} ({count} frames)',flush=True)


def posters(package):
    """Three original vector posters made by the same film renderer, not AI-image placeholders."""
    import cairosvg
    from html import escape
    from .film_art import svg
    package=Path(package);film=read(package/'film.json');request=read(package/'request.json');folder=package/'thumbnails';folder.mkdir(exist_ok=True)
    for i,brief in enumerate(film['thumbnails'],1):
        seq=next(s for s in film['scenes'] if s['id']==brief['source_scene_id']);shots=seq['shots'];shot=copy.deepcopy(shots[(i-1)%len(shots)])
        shot['framing']='closeup';shot['motion']='hold';shot['screen_text']=''
        raw=svg(shot,shot['seconds']*.55,False)
        # Render a composed SVG poster directly, including vector headline typography.
        text=brief['hook_text'].strip() or request['title'];size=min(112,2200/max(8,len(text)))
        headline='<rect x="0" y="0" width="1600" height="200" fill="#10191e" fill-opacity=".85"/>'
        headline+=f'<text x="800" y="142" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="{size}" fill="#f4e8cd">{escape(text)}</text>'
        raw=raw.replace('</svg>',headline+'</svg>')
        cairosvg.svg2png(bytestring=raw.encode(),write_to=str(folder/f'thumbnail-{i}.png'),output_width=1280,output_height=720)
    status=read(package/'delivery-status.json');status.update(thumbnail_images_rendered=3,thumbnail_backend='original film-art vector posters')
    write(package/'delivery-status.json',status)


def finalize(root):
    import shutil
    root=Path(root);deliver=root/'deliverables';deliver.mkdir(exist_ok=True)
    for kind in ('long-form','short-form'):
        package=root/kind;dest=deliver/kind;dest.mkdir(exist_ok=True)
        for name in ('final.mp4','contact-sheet.jpg','render-report.json'):shutil.copy2(package/'video'/name,dest/name)
        for name in ('description.txt','publishing-description.txt','script.md','story.txt','keywords.txt','subtitles.srt','screen-text.srt',
                     'subtitle-notes.txt','sound-plan.json','film.json','request.json','publishing.json','short-edit.md'):
            shutil.copy2(package/name,dest/name)
        shutil.copy2(package/'audio'/'mix-report.json',dest/'mix-report.json')
        report=read(package/'video'/'render-report.json');status=read(package/'delivery-status.json')
        status.update(stage='complete_animated_video',video_rendered=True,missing=[],thumbnail_images_rendered=3,thumbnail_location='../thumbnails',subtitle_timing='line-level timing from measured generated speech; rendered sound cues')
        write(package/'delivery-status.json',status);write(dest/'delivery-status.json',status)
        spec=read(package/'production-spec.json');spec.update(stage='rendered',render_status='rendered')
        spec['duration']['measured_video_seconds']=report['seconds']
        spec['rendered_video']={k:report[k] for k in ('width','height','fps','frames','seconds')}
        spec['long_form' if kind=='long-form' else 'short_form']['measured_rendered_frames']=report['frames'];write(dest/'production-spec.json',spec)
    shutil.copytree(root/'long-form'/'thumbnails',deliver/'thumbnails',dirs_exist_ok=True)
    required=[deliver/'long-form'/'final.mp4',deliver/'short-form'/'final.mp4']+[deliver/'thumbnails'/f'thumbnail-{i}.png' for i in (1,2,3)]
    if any(not p.is_file() or p.stat().st_size==0 for p in required):raise RuntimeError('Incomplete final deliverables')
    write(deliver/'completion.json',{'complete':True,'videos':['long-form/final.mp4','short-form/final.mp4'],
         'thumbnail_images':3,'subtitles':'separate line-timed SRT; no narrator or nameplates',
         'renderer':'layered 2D articulated character animation; original procedural score/foley and optional cloned Turbo dialogue',
         'thumbnail_style':read(root/'long-form'/'delivery-status.json')['thumbnail_backend'],
         'limits':['Finite scene/action library; inspect story-to-picture fidelity and artistic quality.','Vector poster thumbnails differ from the optional premium image-model finish.']})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['plan','voice','sound','picture','posters','finalize'],required=True)
    p.add_argument('--out',default='output/film');p.add_argument('--package');p.add_argument('--title');p.add_argument('--description')
    p.add_argument('--minutes',type=float,default=5);p.add_argument('--short-seconds',type=float,default=60)
    p.add_argument('--quality',choices=['1080p','4K'],default='1080p');p.add_argument('--fps',type=int,choices=[12,24],default=12)
    p.add_argument('--characters',default='Maya + Leo + Max');p.add_argument('--voices',default='female,male1,male2')
    p.add_argument('--model-dir',default='models/script-qwen3');p.add_argument('--voice-model-dir',default='models/chatterbox-turbo')
    p.add_argument('--portrait',action='store_true');p.add_argument('--width',type=int)
    a=p.parse_args();root=Path(a.out)
    if a.stage=='plan':plan(a)
    elif a.stage=='picture':picture(a.package,a.portrait,a.width)
    elif a.stage=='voice':
        from .film_sound import voice_assets
        for kind in ('long-form','short-form'):voice_assets(root/kind,a.voice_model_dir)
    elif a.stage=='sound':
        from .film_sound import mix
        for kind in ('long-form','short-form'):mix(root/kind)
    elif a.stage=='posters':posters(root/'long-form')
    elif a.stage=='finalize':finalize(root)


if __name__=='__main__':main()
