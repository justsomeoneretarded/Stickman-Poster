"""Translate Actions inputs to argv without executing user-provided shell text."""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def read_request(environ):
    """Every production run must supply its own idea; never inherit the demo."""
    request={field:environ.get('EPISODE_'+field.upper(),'').strip()
             for field in ('title','description','minutes','voices','width','short_seconds')}
    missing=[k for k in ('title','description','minutes') if not request[k]]
    if missing:raise ValueError('Enter these fields in Run workflow: '+', '.join(missing))
    for key,default in {'voices':'female,male1,male2','width':'1280','short_seconds':'60'}.items():
        request[key]=request[key] or default
    return request


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['all','write','speech','render'],default='all')
    stage=parser.parse_args().stage
    request = read_request(os.environ)
    args = [sys.executable, '-m', 'studio.cli', 'generate', '--title', request['title'],
            '--description', request['description'], '--minutes', str(request['minutes']),
            '--voices', request['voices'], '--short-seconds',str(request['short_seconds']), '--width', str(request.get('width', 960)), '--fps', '24',
            '--cast-profiles', 'voices/cast-profiles.json', '--writer-model-dir', 'models/script-qwen3',
            '--model-dir', 'models/chatterbox-nano', '--out', 'output/episode', '--stage',stage]
    subprocess.run(args, check=True)
    if stage not in ('all','render'):
        return
    summary = Path(os.environ.get('GITHUB_STEP_SUMMARY', 'work/actions-summary.md'))
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open('a') as f:
        f.write('Episode generated from title and description. Download the long-form and short-form artifacts.\n\n'
                'Each includes its own video, generated script, captions, storyboard, and technical reports.\n'
                'Review story accuracy, voice likeness, and animation before publishing.\n')


if __name__ == '__main__':
    main()
