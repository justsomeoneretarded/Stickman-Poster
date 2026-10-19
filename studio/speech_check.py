"""Transcribe generated speech and retry dropped/changed dialogue before delivery."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def word_error_rate(expected, actual):
    words = lambda text: re.findall(r'[a-z0-9]+', text.lower())
    ref, hyp = words(expected), words(actual)
    previous = list(range(len(hyp)+1))
    for i, a in enumerate(ref, 1):
        current = [i]
        for j, b in enumerate(hyp, 1):
            current.append(min(previous[j]+1, current[-1]+1, previous[j-1]+(a != b)))
        previous = current
    return previous[-1] / max(1, len(ref))


def verify(args):
    from faster_whisper import WhisperModel
    import numpy as np
    from .project import load
    from .cli import load_audio_manifest
    p = load(args.project)
    manifest = Path(args.manifest).resolve()
    paths = load_audio_manifest(manifest, p['scenes'])
    model = WhisperModel(args.asr_model_dir, device='cpu', compute_type='int8', cpu_threads=4)
    reports = []
    for scene, path in zip(p['scenes'], paths):
        attempts = []
        for attempt in range(3):
            # Decode through our already-qualified FFmpeg path. Passing 16 kHz
            # samples avoids PyAV API drift and redundant WAV decoder assumptions.
            raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', 'pipe:1'])
            samples = np.frombuffer(raw, dtype='<f4').copy()
            segments, _ = model.transcribe(samples, language='en', beam_size=5, vad_filter=False,
                                            condition_on_previous_text=False)
            transcript = ' '.join(s.text.strip() for s in segments)
            error = word_error_rate(scene['narration'], transcript)
            attempts.append({'attempt': attempt+1, 'transcript': transcript, 'word_error_rate': error})
            if error <= .35:
                break
            if attempt == 2:
                reports.append({'scene_id': scene['id'], 'status': 'failed', 'attempts': attempts})
                (manifest.parent/'speech-check.json').write_text(json.dumps(reports, indent=2))
                raise RuntimeError(f'Speech text verification failed for {scene["id"]}; video was not delivered')
            retry = manifest.parent/'qc-retries'/scene['id']/str(attempt)
            retry.mkdir(parents=True, exist_ok=True)
            (retry/'project.json').write_text(json.dumps({**p, 'scenes': [scene]}, indent=2))
            command = [sys.executable, '-m', 'studio.cli', 'speak', str(retry/'project.json'),
                       '--cast-profiles', str(Path(args.cast_profiles).resolve()), '--out', str(retry/'speech')]
            if args.model_dir:
                command += ['--model-dir', args.model_dir]
            subprocess.run(command, check=True)
            new = json.loads((retry/'speech/manifest.json').read_text())['entries'][0]['file']
            shutil.copy2(retry/'speech'/new, path)
        reports.append({'scene_id': scene['id'], 'status': 'passed ASR threshold; listening review still required', 'attempts': attempts})
        print(f'Speech checked {scene["id"]}: WER {error:.3f}', flush=True)
    (manifest.parent/'speech-check.json').write_text(json.dumps(reports, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--cast-profiles', required=True)
    parser.add_argument('--model-dir')
    parser.add_argument('--asr-model-dir', default='models/asr-base-en')
    verify(parser.parse_args())
