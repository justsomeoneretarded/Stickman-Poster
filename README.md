# Stickman Studio — development prototype

An original, CPU-only animation benchmark with measured audio/scene timing,
captions, posting metadata and an optional private voice-cloning adapter.

**Status:** early prototype, not a finished automatic YouTube channel. The renderer
is implemented and locally tested. Voice enrollment/inference requires an accessible
sample and downloaded model weights and has not yet been qualified in this environment.
The sample project is an original fictional fixture, not a generated result from
an arbitrary title. No reference video art, scripts, voice recordings or models are
included. The Pillow backend is a minimal portability benchmark; Motion Canvas
remains a possible richer renderer behind the same scene specification.

## What works

- Four illustrated location templates; articulated characters; face changes;
  floating props; glow/particles; camera pushes; cuts/fades; captions.
- Declarative validated JSON, not executable LLM-written code.
- Measured audio duration drives scene lengths when narration is supplied.
- Scene video caching; separate outputs and technical benchmark report.
- SRT, script, title/description/keyword data, contact sheet and thumbnail preview.
- Explicit silent mode: never silently replaces a requested clone with stock TTS.
- GitHub Actions fixed-fixture development test. No production schedule.

## Quick render

Python 3.11/3.12/3.13, FFmpeg and ffprobe on PATH. Fonts default to Windows Arial
or Linux DejaVu; set STUDIO_FONT and STUDIO_FONT_BOLD to approved font files if needed.

```sh
python -m venv .venv
# Activate using your platform's normal method, or use the venv Python directly.
python -m pip install -e .
python -m unittest discover -s tests -v
python -m studio.cli render examples/gravity.json --out output/preview --width 1280 --fps 30 --silent-preview
```

For a short CI smoke render add `--width 640 --fps 12 --max-seconds 10`.
For final-size trials use `--width 1920 --fps 30`. Do not infer ten-minute
throughput from a cache-hit run; report hardware and cold/warm timings separately.

On the user's portable Windows tool layout, add tools to the current shell first:

```powershell
$env:Path = "$env:USERPROFILE\VideoTools\ffmpeg\bin;$env:USERPROFILE\VideoTools\node;$env:Path"
py -3.12 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -e .
& ".\.venv\Scripts\python.exe" -m studio.cli render examples/gravity.json --out output/preview --silent-preview
```

No Node dependency is needed for this first backend. Company download policy and
certificate verification still apply; no security bypass is part of this project.

## Voice workflow (adapter prepared; inference qualification pending)

Use a separate voice environment; the heavier model's dependencies should not
destabilize the small rendering environment.

1. Obtain a clean single-speaker sample, no overlapping speakers/music, natural
   pacing. Use 20–60 seconds for inspection, then select the best 6–15 seconds for
   Chatterbox conditioning. More audio is not automatically better.
2. Install `requirements-voice.txt` into the separate environment with Git available.
   This pins the inspected Chatterbox code revision; full transitive locking and
   actual installation qualification remain to be done. Upstream documents Python
   3.11 as tested; try that environment if 3.12 resolution fails.
3. Model downloads need access to Hugging Face and its asset hosts. No paid API is
   necessary. No model download is attempted by the public CI workflow.

```sh
python -m studio.cli prepare-reference private/source.mp3 private/reference.wav --start 0 --seconds 12
python -m studio.cli enroll private/reference.wav --profile private/voice-nano --variant nano --device cpu
python -m studio.cli speak examples/gravity.json --profile private/voice-nano --out private/narration
python -m studio.cli render examples/gravity.json --out private/render --audio-manifest private/narration/manifest.json
```

`--model-dir models/chatterbox-nano` can load previously downloaded local weights
for enrollment and speaking. Compare Turbo by enrolling a separate `--variant turbo`
profile. Do not reuse Nano conditioning blindly with a different model variant.

Enrollment saves Chatterbox conditioning tensors. Future synthesis reads those
tensors, not the source WAV. **Those tensors still contain speaker information.**
Keep profiles private, just like the source. Source deletion is deliberately
manual and should happen only after listening to a new render generated from the
saved profile with the reference no longer available. This program cannot delete
the original chat attachment and cannot guarantee secure erasure/backups.

Do not commit source audio, model files, conditioning profiles, or private renders
to a public repository. `.gitignore` helps but is not a complete data-leak check.
The public CI artifact contains only the silent original test fixture.

## Original title to scene plan

The planner is an optional OpenAI-compatible HTTP adapter, with **no default paid
provider**. Supply your own permitted endpoint/model. A local or cloud `llama.cpp`
server can implement this interface. Set STUDIO_API_KEY only if required; never
put it in the repository. Endpoint/model output has not been integration-tested
here. Factual research is not automatic in this prototype: supply source notes.

```sh
python -m studio.cli plan --title "Your title" --minutes 10 --endpoint http://localhost:8080/v1 --model YOUR_MODEL --notes sources.txt --out private/project.json
```

Review the generated JSON and factual claims. Then use `speak` and `render` on that
project. Scene durations follow actual speech; a requested ten-minute script is
not a guarantee of exactly ten minutes. Never pad a weak script just to meet length.

Once the endpoint and voice adapter are qualified, the same stages can be called
with one command (this full model-backed path has not yet been run end to end):

```sh
python -m studio.cli produce --title "Your title" --minutes 10 --endpoint http://localhost:8080/v1 --model YOUR_MODEL --notes sources.txt --profile private/voice-nano --out private/episode
```

The planner requests a draft and a separate editorial revision. These are model
instructions, not a guarantee of better writing or verified factual accuracy.

## GitHub Actions

Push the source to the repository you choose. The development-test workflow runs
on code changes or manually through Actions → Generator development checks → Run
workflow. It checks a fixed 10-second silent fixture, decodes the video and uploads
public technical outputs for three days. It neither clones the private voice nor
publishes videos. GitHub terms and account availability still apply.

There is no daily cron job and no general content-generation endpoint. Deployment
to a channel-production host is a separate step. This workflow has been prepared,
but cannot be claimed as run on GitHub until a repository and run result exist.

## Known limits / next milestones

- Only four locations, seven action types and one principal prop: insufficient
  visual vocabulary for arbitrary high-quality ten-minute episodes today.
- No promise of parity with the IFOLOGY reference. Lighting, acting, contact and
  composition need iterative art review.
- Phrase captions are estimated, not forced word alignment. Scene boundaries do
  follow measured narration. Add/qualify a forced-alignment adapter next.
- No automatic ASR verification, speaker similarity score, music/SFX composer,
  chapter eligibility check, independent fact checker or YouTube uploader yet.
- Thumbnail is a scene preview, not an optimized final publishing thumbnail.
- Voice profile caching API is source-reviewed; actual clone fidelity and speed
  remain untested. See docs/VOICE_RESEARCH.md.
- Renderer dependencies have bounded ranges, not a complete cross-platform lock.
  Pin/lock after qualifying the intended runner.

## License

Original code and procedural artwork: MIT (LICENSE). Model/software dependencies
retain their own licenses. No upstream animation code has been copied. Direction
research included kaomei/stickman-video-director and nispa/stickman-video; no skill
was installed or used to generate this fixture. See docs/VOICE_RESEARCH.md for
audio licensing and evidence boundaries.
