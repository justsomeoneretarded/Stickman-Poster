"""Render and verify the first real 3D acting study, not the complete film."""
import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from .media import require_tool

QUALITIES={'Preview':640,'1080p':1920,'4K':3840}
FPS=24


def inspect_video(path,expected_frames=None):
    data=json.loads(subprocess.check_output([require_tool('ffprobe'),'-v','error','-count_frames',
        '-show_streams','-show_format','-of','json',str(path)]))
    stream=next(s for s in data['streams'] if s['codec_type']=='video')
    if Fraction(stream['avg_frame_rate'])!=FPS or Fraction(stream['r_frame_rate'])!=FPS:
        raise ValueError('3D delivery must be exactly 24 FPS')
    count=int(stream['nb_read_frames'])
    if expected_frames is not None and count!=expected_frames:raise ValueError('Encoded frame count differs from rendered frames')
    subprocess.run([require_tool('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],check=True)
    return {'fps':FPS,'decoded_frames':count,'seconds':count/FPS,'width':stream['width'],'height':stream['height']}


def package(out,start=1,end=192):
    out=Path(out);count=end-start+1
    for index in range(start,end+1):
        if not (out/f'{index:06}.png').is_file():raise ValueError(f'Missing rendered frame {index}')
    subprocess.run([require_tool('ffmpeg'),'-v','error','-y','-framerate',str(FPS),'-start_number',str(start),
        '-i',str(out/'%06d.png'),'-frames:v',str(count),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',
        '-an',str(out/'motion-proof.mp4')],check=True)
    info=inspect_video(out/'motion-proof.mp4',count)
    info.update(status='silent 3D acting proof; not the complete film or final character-quality approval',
                soundtrack='none',generated_from='Blender geometry and animated transforms; no concept-image plates')
    (out/'video-check.json').write_text(json.dumps(info,indent=2)+'\n')
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True);p.add_argument('--blender',default='blender')
    p.add_argument('--quality',choices=QUALITIES,default='Preview');p.add_argument('--aspect',choices=['landscape','portrait'],default='landscape')
    p.add_argument('--samples',type=int);p.add_argument('--engine',choices=['CYCLES','BLENDER_EEVEE_NEXT'],default='CYCLES')
    p.add_argument('--denoise',action='store_true');p.add_argument('--package-only',action='store_true')
    a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if not a.package_only:
        script=Path(__file__).parent/'blender/cafe_proof.py'
        command=[a.blender,'-b','-t','4','--python-exit-code','1','--python',str(script),'--','--out',str(out),
            '--width',str(QUALITIES[a.quality]*9//16 if a.aspect=='portrait' else QUALITIES[a.quality]),'--samples',str(a.samples or (4 if a.quality=='Preview' else 16)),'--engine',a.engine]
        if a.denoise:command+=['--denoise']
        if a.aspect=='portrait':command+=['--portrait']
        subprocess.run(command,check=True)
    print(json.dumps(package(out),indent=2))


if __name__=='__main__':main()
