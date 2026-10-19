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
    short_seconds=getattr(args,'short_seconds',60)
    if not isinstance(short_seconds,(int,float)) or not math.isfinite(short_seconds) or not 10<=short_seconds<=180:
        raise ValueError('Short target seconds must be between 10 and 180')
    request = {'short_seconds':short_seconds,'title': args.title, 'description': args.description, 'minutes': args.minutes, 'voices': voices}
    if args.required_locations:
        request['required_locations']=args.required_locations.split(',')
    if args.revise_project:
        request['revise_project']=str(Path(args.revise_project).resolve())
    resume_writing = False
    if args.resume and (out/'request.json').is_file() and (out/'writing/writer-report.json').is_file():
        previous = json.loads((out/'writing/writer-report.json').read_text())
        resume_writing = (json.loads((out/'request.json').read_text()) == request and
                          previous.get('model') == MODEL_ID and previous.get('revision') == MODEL_REVISION and
                          (out/'writing/project.json').is_file())
    if args.stage not in ('all','write'):
        if not (out/'request.json').is_file() or json.loads((out/'request.json').read_text()) != request:
            raise ValueError("Pipeline stage request does not match the generated script")
    (out/'request.json').write_text(json.dumps(request, indent=2))
    command = [sys.executable, '-m', 'studio.writer', '--request', str(out/'request.json'), '--out', str(out/'writing')]
    if args.writer_model_dir:
        command += ['--model-dir', args.writer_model_dir]
    if args.stage in ('all','write'):
        if not resume_writing:
            subprocess.run(command, check=True)
        else:
            from .writer import compile_project, parse_story
            source=out/'writing/story.json'
            if not source.is_file():source=out/'writing/revision.json'
            story = parse_story(source.read_text(), voices)
            compiled = compile_project(story, args.title, args.description, voices)
            (out/'writing/project.json').write_text(json.dumps(compiled, indent=2))
    if args.stage in ('all','write'):
        subprocess.run([sys.executable,'-m','studio.shortform',str(out/'writing/project.json'),
                        str(out/'request.json'),str(out/'short/writing'),args.writer_model_dir or 'models/script-qwen3'],check=True)
    if args.stage=='write':
        return
    # Writer process exits before the speech model is loaded, keeping peak RAM bounded.
    project = out/'writing/project.json'
    if args.stage in ('all','speech'):
        for production in (out,out/'short'):
            project=production/'writing/project.json'
            command = [sys.executable, '-m', 'studio.cli', 'speak', str(project), '--cast-profiles', str(mapping), '--out', str(production/'speech')]
            if args.model_dir:
                command += ['--model-dir', args.model_dir]
            subprocess.run(command, check=True)
            subprocess.run([sys.executable, '-m', 'studio.speech_check', '--project', str(project),
                            '--manifest', str(production/'speech/manifest.json'), '--cast-profiles', str(mapping),
                            '--model-dir', args.model_dir or 'models/chatterbox-nano',
                            '--asr-model-dir', args.asr_model_dir], check=True)
    if args.stage=='speech':
        return
    project=out/'writing/project.json'
    if not (out/'speech/speech-check.json').is_file():
        raise ValueError("Verified speech is required before rendering")
    render_project(argparse.Namespace(project=str(project), out=str(out/'render'), width=args.width,
                   fps=args.fps, silent_preview=False, audio_manifest=str(out/'speech/manifest.json'), max_seconds=None))
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out/'render/final.mp4'), '-f', 'null', '-'], check=True)
    delivery = out/'deliverables/long-form'
    delivery.mkdir(parents=True,exist_ok=True)
    for name in ('final.mp4', 'captions.srt', 'script.txt', 'posting.json', 'contact-sheet.jpg', 'thumbnail-preview.jpg', 'report.json', 'resolved-project.json'):
        shutil.copy2(out/'render'/name, delivery/name)
    shutil.copy2(out/'speech/speech-check.json', delivery/'speech-check.json')
    for name in ('writer-report.json', 'project.json'):
        shutil.copy2(out/'writing'/name, delivery/name)
    from .project import load
    compiled=load(project)
    rendering=json.loads((delivery/'report.json').read_text())
    motion={'locations':sorted({s['location'] for s in compiled['scenes']}),
            'target_minutes':args.minutes,'actual_seconds':rendering['actual_seconds'],
            'scenes':[{'id':s['id'],'location':s['location'],'staging':s.get('staging','legacy'),
                       'travel_pixels':{cid:round(abs(track['end']-track['start'])*1920) for cid,track in s.get('blocking',{}).items()},
                       'held_props':{cid:track['prop'] for cid,track in s.get('blocking',{}).items() if track['prop']!='none'}}
                      for s in compiled['scenes']]}
    (delivery/'motion-check.json').write_text(json.dumps(motion,indent=2))
    summary = {'status': 'generated and decoded; editorial, voice, and artistic review required',
               'title': args.title, 'voices': voices, 'engine': 'chatterbox-nano CPU baseline, not audition winner',
               'video': 'final.mp4', 'script_source': 'local language model; comic outline and per-scene dialogue', 'reused_validated_writing': resume_writing,
               'unqualified': ['voice similarity', 'human listening review', 'factual claims', 'reference visual parity']}
    (delivery/'generation.json').write_text(json.dumps(summary, indent=2))
    short=out/'short'
    portrait_width,portrait_height=(1080,1920) if args.width>=1920 else (720,1280)
    render_project(argparse.Namespace(project=str(short/'writing/project.json'),out=str(short/'render'),
                   width=portrait_width,height=portrait_height,fps=args.fps,silent_preview=False,
                   audio_manifest=str(short/'speech/manifest.json'),max_seconds=None))
    subprocess.run(['ffmpeg','-v','error','-i',str(short/'render/final.mp4'),'-f','null','-'],check=True)
    short_delivery=out/'deliverables/short-form';short_delivery.mkdir(parents=True,exist_ok=True)
    for name in ('final.mp4','captions.srt','script.txt','report.json','resolved-project.json','contact-sheet.jpg','thumbnail-preview.jpg'):
        shutil.copy2(short/'render'/name,short_delivery/name)
    for name in ('writer-report.json','project.json','highlight-selection.json'):
        shutil.copy2(short/'writing'/name,short_delivery/name)
    shutil.copy2(short/'speech/speech-check.json',short_delivery/'speech-check.json')
    print(f'Deliverables: {out/"deliverables"} (long-form + short-form)', flush=True)
