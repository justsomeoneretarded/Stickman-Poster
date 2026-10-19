"""Translate Actions inputs to argv without executing user-provided shell text."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['all','write','speech','render'],default='all')
    stage=parser.parse_args().stage
    request = json.loads(Path('ci/demo-request.json').read_text())
    for field in ('title', 'description', 'minutes', 'voices', 'width'):
        value = os.environ.get('EPISODE_'+field.upper())
        if value:
            request[field] = value
    args = [sys.executable, '-m', 'studio.cli', 'generate', '--title', request['title'],
            '--description', request['description'], '--minutes', str(request['minutes']),
            '--voices', request['voices'], '--width', str(request.get('width', 960)), '--fps', '24',
            '--cast-profiles', 'voices/cast-profiles.json', '--writer-model-dir', 'models/script-qwen3',
            '--model-dir', 'models/chatterbox-nano', '--out', 'output/episode', '--stage',stage]
    if request.get('required_locations'):
        args += ['--required-locations',','.join(request['required_locations'])]
    if request.get('revision_project'):
        args += ['--revise-project',request['revision_project']]
    subprocess.run(args, check=True)
    if stage not in ('all','render'):
        return
    summary = Path(os.environ.get('GITHUB_STEP_SUMMARY', 'work/actions-summary.md'))
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open('a') as f:
        f.write('Episode generated from title and description. Download the voiced-episode artifact.\n\n'
                'Includes video, generated script, captions, storyboard, and technical reports.\n'
                'Review story accuracy, voice likeness, and animation before publishing.\n')


if __name__ == '__main__':
    main()
