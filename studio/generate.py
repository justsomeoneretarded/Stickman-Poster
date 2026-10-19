"""Title and description -> model-written story -> cast speech -> animation."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def generate(args):
    from .cli import render_project
    from .writer import MODEL_ID, MODEL_REVISION, VOICE_NAMES
    import math
    if not .2 <= args.minutes <= 10 or not math.isfinite(args.minutes):
        raise ValueError("Target length must be .2–10 minutes")
    if args.width < 320 or args.width > 1920 or args.width % 32 or (args.width*9//16) % 2:
        raise ValueError("Width must produce supported even 16:9 dimensions")
    if not 1 <= args.fps <= 60:
        raise ValueError("FPS must be 1–60")
    if not args.title.strip() or len(args.title) > 200 or not args.description.strip() or len(args.description) > 4000:
        raise ValueError("Provide a title up to 200 and description up to 4000 characters")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    voices = args.voices.split(',')
    if not 1 <= len(voices) <= 3 or len(set(voices)) != len(voices) or any(v not in VOICE_NAMES for v in voices):
        raise ValueError("Choose one to three distinct character voices")
    mapping = Path(args.cast_profiles).resolve()
    if not mapping.is_file():
        raise ValueError('Private cast profile mapping is required')
    data = json.loads(mapping.read_text())
    if not isinstance(data, dict) or any(v not in data for v in voices):
        raise ValueError('Every selected voice needs a profile mapping')
    for v in voices:
        folder = mapping.parent / data[v]
        if not (folder/'profile.json').is_file() or not (folder/'conditioning.pt').is_file():
            raise ValueError(f'Missing private profile for {v}')
    request = {'title': args.title, 'description': args.description, 'minutes': args.minutes, 'voices': voices}
    resume_writing = False
    if args.resume and (out/'request.json').is_file() and (out/'writing/writer-report.json').is_file():
        previous = json.loads((out/'writing/writer-report.json').read_text())
        resume_writing = (json.loads((out/'request.json').read_text()) == request and
                          previous.get('model') == MODEL_ID and previous.get('revision') == MODEL_REVISION and
                          (out/'writing/project.json').is_file())
    (out/'request.json').write_text(json.dumps(request, indent=2))
    command = [sys.executable, '-m', 'studio.writer', '--request', str(out/'request.json'), '--out', str(out/'writing')]
    if args.writer_model_dir:
        command += ['--model-dir', args.writer_model_dir]
    if not resume_writing:
        subprocess.run(command, check=True)
    else:
        from .writer import compile_project, parse_story
        story = parse_story((out/'writing/revision.json').read_text(), voices)
        compiled = compile_project(story, args.title, args.description, voices)
        (out/'writing/project.json').write_text(json.dumps(compiled, indent=2))
    # Writer process exits before the speech model is loaded, keeping peak RAM bounded.
    project = out/'writing/project.json'
    command = [sys.executable, '-m', 'studio.cli', 'speak', str(project), '--cast-profiles', str(mapping), '--out', str(out/'speech')]
    if args.model_dir:
        command += ['--model-dir', args.model_dir]
    subprocess.run(command, check=True)
    subprocess.run([sys.executable, '-m', 'studio.speech_check', '--project', str(project),
                    '--manifest', str(out/'speech/manifest.json'), '--cast-profiles', str(mapping),
                    '--model-dir', args.model_dir or 'models/chatterbox-nano',
                    '--asr-model-dir', args.asr_model_dir], check=True)
    render_project(argparse.Namespace(project=str(project), out=str(out/'render'), width=args.width,
                   fps=args.fps, silent_preview=False, audio_manifest=str(out/'speech/manifest.json'), max_seconds=None))
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out/'render/final.mp4'), '-f', 'null', '-'], check=True)
    delivery = out/'deliverables'
    delivery.mkdir(exist_ok=True)
    for name in ('final.mp4', 'captions.srt', 'script.txt', 'posting.json', 'contact-sheet.jpg', 'thumbnail-preview.jpg', 'report.json', 'resolved-project.json'):
        shutil.copy2(out/'render'/name, delivery/name)
    shutil.copy2(out/'speech/speech-check.json', delivery/'speech-check.json')
    for name in ('writer-report.json', 'project.json'):
        shutil.copy2(out/'writing'/name, delivery/name)
    summary = {'status': 'generated and decoded; editorial, voice, and artistic review required',
               'title': args.title, 'voices': voices, 'engine': 'chatterbox-nano CPU baseline, not audition winner',
               'video': 'final.mp4', 'script_source': 'local language model, draft plus revision', 'reused_validated_writing': resume_writing,
               'unqualified': ['voice similarity', 'human listening review', 'factual claims', 'reference visual parity']}
    (delivery/'generation.json').write_text(json.dumps(summary, indent=2))
    print(f'Deliverables: {delivery}', flush=True)
