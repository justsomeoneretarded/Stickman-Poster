# Stickman Studio — development prototype

Current creative direction: original character-led animated short films with a
muted cinematic palette, expressive acting and purpose-designed thumbnails.
[Three-character concepts and pivot brief](designs/day-one-pivot/README.md).
This is a visual-development milestone; the workflow below still uses the legacy
renderer until the new animation system is built and qualified.

**New:** [Generate an episode with GitHub Actions](docs/ACTIONS.md): enter a title
and short description, choose one to three voices, and download the generated
scripts and two voiced video artifacts: 16:9 long-form and a standalone 9:16 short. The three reusable voice profiles are public; no voice secret is required.
Local model scripting and character dialogue are now implemented; artistic and
voice qualification remain ongoing.

An original, CPU-only animation benchmark with measured audio/scene timing,
captions, posting metadata and an optional private voice-cloning adapter.

**Status:** early prototype, not a finished automatic YouTube channel. The renderer
is implemented and locally tested. Voice enrollment/inference requires an accessible
sample and downloaded model weights. Nano CPU inference passed a bundled-voice smoke
test; three saved voice profiles passed reload and text-fidelity checks.
Human voice-similarity and listening approval remain pending.
The sample project is an original fictional fixture, not a generated result from
an arbitrary title. Original reference video art and source recordings are not included.
The user-authorized reusable voice conditioning is published in `voices/`. The Pillow backend is a minimal portability benchmark; Motion Canvas
remains a possible richer renderer behind the same scene specification.

## What works

- Original expressive vector scenes, native portrait compositions, gym/rooftop/park settings; articulated characters; face changes;
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

## Voice workflow (Nano CPU smoke passed; clone qualification pending)

Use a separate voice environment; the heavier model's dependencies should not
destabilize the small rendering environment.

1. Obtain a clean single-speaker sample, no overlapping speakers/music, natural
   pacing. Use 20–60 seconds for inspection, then select the best 6–15 seconds for
   Chatterbox conditioning. More audio is not automatically better.
2. Install `requirements-voice.txt` into the separate environment with Git available.
   This pins the inspected Chatterbox code revision; full transitive locking and
   user clone qualification remain to be done. A Linux Python 3.12 CPU installation
   snapshot is available in `requirements-voice-cpu.lock`. Upstream documents Python
   3.11 as tested; try that environment if 3.12 resolution fails.
3. Model downloads need access to Hugging Face and its asset hosts. No paid API is
   necessary. Development fixture tests do not download voice models; the manual production workflow downloads pinned public models.

```sh
python -m studio.cli prepare-reference private/source.mp3 private/reference.wav --start 0 --seconds 12
python -m studio.cli enroll private/reference.wav --profile private/voice-turbo --variant turbo --device cpu
python -m studio.cli speak examples/gravity.json --profile private/voice-turbo --out private/narration
python -m studio.cli render examples/gravity.json --out private/render --audio-manifest private/narration/manifest.json
```

`--model-dir models/chatterbox-turbo` can load previously downloaded local weights
for enrollment and speaking. Turbo is the production default. Published cast
conditioning was checked against identical encoder/decoder weights, tokenizer
files and the shared conditioning API of these pinned Nano and Turbo versions.
This does not establish compatibility with arbitrary models.

Enrollment saves Chatterbox conditioning tensors. Future synthesis reads those
tensors, not the source WAV. **Those tensors still contain speaker information.**
Keep profiles private, just like the source. Source deletion is deliberately
manual and should happen only after listening to a new render generated from the
saved profile with the reference no longer available. This program cannot delete
the original chat attachment and cannot guarantee secure erasure/backups.

Do not commit source audio, model files, conditioning profiles, or private renders
to a public repository. `.gitignore` helps but is not a complete data-leak check.
The public CI artifact contains only the silent original test fixture.

## Legacy endpoint-based title planner (optional)

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
python -m studio.cli produce --title "Your title" --minutes 10 --endpoint http://localhost:8080/v1 --model YOUR_MODEL --notes sources.txt --profile private/voice-turbo --out private/episode
```

When required locations are supplied, the app assigns every location, speaker, and
movement before generating dialogue one scene at a time. Each spoken turn is
validated and checkpointed; retries repair that turn instead of restarting the story.
Without required locations, the writer generates a pitch, outline and dialogue from the title and description. Tone and ending follow the description, without preset jokes or moral lessons. These are model
instructions, not a guarantee of better writing or verified factual accuracy.

## GitHub Actions

Push the source to the repository you choose. The development-test workflow runs
on code changes or manually through Actions → Generator development checks → Run
workflow. It checks a fixed 10-second silent fixture, decodes the video and uploads
public technical outputs for three days. It neither clones the private voice nor
publishes videos. GitHub terms and account availability still apply.

Production starts manually through **Generate voiced episode → Run workflow**, with a fresh title and description every time. There is no daily cron job. Deployment
to a channel-production host is a separate step. The previous single-format workflow has produced a complete episode; the revised two-format path has separate verification evidence in the project context.

Production text defaults to **Essential labels only**: no character nameplates,
repeated title bars or burned-in dialogue. The writer may request a short label
when needed to understand the action (for example, “400 lb”); character names are
filtered from those labels. Choose **Captions** to burn dialogue into the video,
or **No overlays** to suppress labels too. A separate SRT file remains available.

Each delivery includes `quality-review.json` and `motion-review.jpg`. The script
review checks the description, continuity, repetition, dialogue and staging. It
uses the same Qwen model as the writer and accepts only findings quoting actual
scene dialogue; it is advisory, not independent creative approval. Animation
checks decode the finished video, measure actor/load movement, flag possible
edge cropping and repetitive staging, and supply a frame sheet. Audio checks decode the finished mix for
clipping, long silence and level variation. These checks do not reject a video
for missing a word count or target duration.

Review flags need judgment: quiet pauses and edge exits may be intentional.
The checks do not establish that writing is funny, motion has believable weight,
or a voice sounds natural. Echo, acting and voice similarity still need listening;
no perceptual audio or vision critic has been qualified. Reports explicitly mark
unavailable reviews, and never convert missing reviews into quality approval.

## Known limits / next milestones

- Eight location templates, per-actor walking/running, and basic hand-attached
  object interactions remain a limited visual vocabulary for arbitrary episodes.
- No promise of parity with the IFOLOGY reference. Lighting, acting, contact and
  composition need iterative art review.
- Phrase captions are estimated, not forced word alignment. Scene boundaries do
  follow measured narration. Add/qualify a forced-alignment adapter next.
- Automatic ASR text checks are implemented; no speaker similarity score, music/SFX composer,
  chapter eligibility check, independent fact checker or YouTube uploader yet.
- Thumbnail is a scene preview, not an optimized final publishing thumbnail.
- Turbo is the production TTS engine on GitHub Actions CPU runners.
  Clone fidelity and naturalness need listening review; changing models does not
  guarantee that every echo or robotic inflection disappears. See docs/VOICE_RESEARCH.md.
- Renderer dependencies have bounded ranges, not a complete cross-platform lock.
  Pin/lock after qualifying the intended runner.

## License

Original code and procedural artwork: MIT (LICENSE). Model/software dependencies
retain their own licenses. No upstream animation code has been copied. Direction
research included kaomei/stickman-video-director and nispa/stickman-video; no skill
was installed or used to generate this fixture. See docs/VOICE_RESEARCH.md for
audio licensing and evidence boundaries.

## Qualified Linux CPU voice setup

```sh
uv venv work/voice-venv --python 3.12
uv pip install --python work/voice-venv/bin/python --index-strategy unsafe-best-match -r requirements-voice-cpu.lock
uv pip check --python work/voice-venv/bin/python
```

Use `work/voice-venv/bin/python -m studio.cli` from the project root for the
voice commands above, adding `--model-dir models/chatterbox-turbo` to enroll
and speak. The model directory is private/ignored. The qualified model revision
is `749d1c1a46eb10492095d68fbcf55691ccf137cd` (Turbo). Historical Nano
benchmarks are not Turbo benchmarks. See `docs/VOICE_RESEARCH.md`.

## Character voices: one, two, or three speakers

Use a project `cast` with one to three members, each with `id`, `name`, and
`voice`. Each scene is one dialogue turn: `speaker` selects the character and
`characters` lists the visible cast (one to three IDs). A video can use any
subset of the three voices. Characters keep their voice across turns; the
renderer does not add character-name labels. This is turn-taking, not overlapping speech
or phoneme lip sync. `examples/three-friends.json` demonstrates all three.

Keep profile paths in a private JSON mapping, for example `private/cast-profiles.json`:

```json
{
  "female": "profiles/female",
  "male1": "profiles/male1-kit-laser",
  "male2": "profiles/male2-warguy"
}
```

Paths resolve relative to that mapping file. Generate narration and render:

```sh
work/voice-venv/bin/python -m studio.cli speak examples/three-friends.json --cast-profiles private/cast-profiles.json --out private/three-friends/speech --model-dir models/chatterbox-turbo
.venv/bin/python -m studio.cli render examples/three-friends.json --audio-manifest private/three-friends/speech/manifest.json --out private/three-friends/render --width 960 --fps 24
```

The cast example uses fictional character names. Recordings, conditioning, and
voiced output remain private. Missing voice profiles fail before synthesis.
Legacy single-narrator projects continue using `--profile`. Automatic title-based
planning/`produce` remains single-narrator; authored cast projects use `speak`
and `render` above. Voice likeness still requires listening review.
