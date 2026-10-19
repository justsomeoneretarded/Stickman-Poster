"""Translate Actions inputs to argv without executing user-provided shell text."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


VOICE_CHOICES = {
    '1 speaker — Maya (female)': 'female',
    '1 speaker — Leo (Kit Laser)': 'male1',
    '1 speaker — Max (Warguy)': 'male2',
    '2 speakers — Maya + Leo': 'female,male1',
    '2 speakers — Maya + Max': 'female,male2',
    '2 speakers — Leo + Max': 'male1,male2',
    '3 speakers — Maya + Leo + Max': 'female,male1,male2',
}


def read_request(environ):
    """Every production run must supply its own idea; never inherit the demo."""
    request={field:environ.get('EPISODE_'+field.upper(),'').strip()
             for field in ('title','description','minutes','voices','width','short_seconds','screen_text')}
    missing=[k for k in ('title','description','minutes') if not request[k]]
    if missing:raise ValueError('Enter these fields in Run workflow: '+', '.join(missing))
    for key,default in {'voices':'female,male1,male2','width':'1280','short_seconds':'60','screen_text':'minimal'}.items():
        request[key]=request[key] or default
    from .text_policy import TEXT_CHOICES
    request['screen_text']=TEXT_CHOICES.get(request['screen_text'],request['screen_text'])
    if request['screen_text'] not in {'minimal','captions','none'}:raise ValueError('Choose a valid on-screen text option')
    request['voices']=VOICE_CHOICES.get(request['voices'],request['voices'])
    selected=request['voices'].split(',')
    if len(set(selected))!=len(selected) or not 1<=len(selected)<=3 or any(v not in {'female','male1','male2'} for v in selected):
        raise ValueError('Choose one, two, or three voices from the workflow cast menu')
    return request


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['all','write','speech','render'],default='all')
    stage=parser.parse_args().stage
    request = read_request(os.environ)
    args = [sys.executable, '-m', 'studio.cli', 'generate', '--title', request['title'],
            '--description', request['description'], '--minutes', str(request['minutes']),
            '--screen-text',request['screen_text'],'--voices', request['voices'], '--short-seconds',str(request['short_seconds']), '--width', str(request.get('width', 960)), '--fps', '24',
            '--cast-profiles', 'voices/cast-profiles.json', '--writer-model-dir', 'models/script-qwen3',
            '--model-dir', 'models/chatterbox-turbo', '--out', 'output/episode', '--stage',stage]
    subprocess.run(args, check=True)
    if stage not in ('all','render'):
        return
    summary = Path(os.environ.get('GITHUB_STEP_SUMMARY', 'work/actions-summary.md'))
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open('a') as f:
        f.write('Episode generated from title and description. Download the long-form and short-form artifacts.\n\n'
                'Each includes its own video, generated script, captions, storyboard, and technical reports.\n'
                'Review story accuracy, voice likeness, and animation before publishing.\n')
        for variant in ('long-form','short-form'):
            report=Path('output/episode/deliverables')/variant/'quality-review.json'
            if report.exists():
                data=json.loads(report.read_text())
                f.write(f'\n{variant}: {data["automatic_flags"]} automatic review flags. See quality-review.json and motion-review.jpg.\n')
                for domain in ('script','animation','audio'):
                    f.write(f'- {domain}: {data[domain]["status"]}\n')
        f.write('\nAutomated flags are advisory, not proof of artistic quality, natural speech, or absence of echo.\n')


if __name__ == '__main__':
    main()
