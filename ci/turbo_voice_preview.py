"""Explicit short TTS test fixture; never supplies a production story."""
import argparse
import json
import resource
import time
from pathlib import Path
from studio.writer import compile_project
from studio.voice import synthesize_cast, MODEL_REVISIONS


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='work/turbo-qualification')
    parser.add_argument('--model-dir',default='models/chatterbox-turbo')
    args=parser.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=True)
    voices=['female','male1','male2']
    lines=['Wait, you can lift the whole car? I meant the shopping bags.',
           'Well, that explains why the gym cancelled my parking membership.',
           'Please put my car down. I have groceries in the back.']
    project=compile_project({'visual_style':'expressive-v2','beats':[
        {'speaker':voice,'location':'street','staging':'talk','text':line}
        for voice,line in zip(voices,lines)]},'Turbo voice qualification',
        'Manually written test dialogue for the replacement TTS engine, not a generated production script.',voices)
    (root/'project.json').write_text(json.dumps(project,indent=2))
    mapping=Path('voices/cast-profiles.json')
    profiles={key:mapping.parent/value for key,value in json.loads(mapping.read_text()).items()}
    started=time.perf_counter()
    synthesize_cast(project,profiles,root/'speech',model_dir=args.model_dir)
    (root/'timing.json').write_text(json.dumps({'engine':'chatterbox-turbo',
        'model_revision':MODEL_REVISIONS['turbo'],'device':'cpu',
        'wall_seconds_including_three_model_loads':round(time.perf_counter()-started,2),
        'peak_process_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)},indent=2))
    print('Completed all three Turbo voices',flush=True)


if __name__=='__main__':main()
