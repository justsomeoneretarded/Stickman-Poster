"""Silent visual acceptance samples; never represented as generated production episodes."""
import argparse
import json
from pathlib import Path
from studio.cli import render_project
from studio.writer import compile_project

root=Path('output/style-study');root.mkdir(parents=True,exist_ok=True)
beats=[
 {'speaker':'male1','location':'gym','staging':'lift','prop':'car','shot':'wide','text':'My spotter just asked whether the handbrake is on.','seconds':5},
 {'speaker':'female','location':'gym','staging':'react','shot':'close','text':'You brought a car to arm day?','seconds':3},
 {'speaker':'male1','location':'gym','staging':'lift','prop':'barbell','shot':'wide','text':'Four hundred pounds suddenly feels like the warm-up.','seconds':4},
 {'speaker':'male1','location':'rooftop','staging':'fly','shot':'wide','text':'Flying to work sounds great. Until you hit pigeon traffic.','seconds':5},
 {'speaker':'male2','location':'park','staging':'react','shot':'close','text':'The pigeons still want you to use your turn signal.','seconds':3},
]
p=compile_project({'beats':beats,'visual_style':'expressive-v2'},'Visual style study','Silent motion fixture, not a generated final episode.',['female','male1','male2'])
for scene,beat in zip(p['scenes'],beats):scene['duration']=beat['seconds']
p['scenes'][0].update(comic_role='hook',heading='BENCH A CAR?')
source=root/'project.json';source.write_text(json.dumps(p,indent=2))
for folder,width,height in (('landscape',960,None),('portrait',576,1024)):
 render_project(argparse.Namespace(project=str(source),out=str(root/folder),width=width,height=height,
                fps=24,silent_preview=True,audio_manifest=None,max_seconds=None))
