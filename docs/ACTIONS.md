# Generate a video from a title and short description

Open **Actions → Generate voiced episode → Run workflow**. Enter the title,
short description, target script length, character voices, and output width.
Download `voiced-episode-<run number>` from the completed run's Artifacts section.

No manual script is required. The local Qwen3-4B-Instruct-2507 Q4_K_M model
writes a draft and a separate revision. llama.cpp constrains JSON output to the
supported scene schema. The app validates speaker IDs and scene content, routes
turns to the public character profiles, synthesizes narration, transcribes it with Whisper base.en to check spoken text, retries failed turns up to twice, measures its
actual duration, renders scenes and captions, normalizes the final mix, decodes
the video, and packages the result. A generation failure stops the job; it never
substitutes a canned script, silent video, or stock narrator.

The artifact contains `final.mp4`, generated `script.txt`, `captions.srt`,
`project.json`, `resolved-project.json`, contact sheet, thumbnail preview,
posting metadata, writer report, speech-verification report, rendering report, and generation summary.
It does not contain conditioning profiles or original recordings. On this public
repository, treat artifacts and generated scripts as public review material.

## Public voice profiles — no secret setup

The user explicitly authorized publication of all three reusable voice profiles.
They are in `voices/profiles/`, with routing in `voices/cast-profiles.json`.
Actions reads them directly after checkout. **VOICE_PROFILE_KEY is no longer
required.** The encrypted archive and decryption helper have been retired.

The profiles contain speaker conditioning and can be reused by anyone with
repository access. Original recordings remain outside the repository. Each
conditioning file is checked against the SHA-256 in its metadata before synthesis.

## Characters

Choose one voice, any pair, or all three in the workflow's `voices` input:

- `female` → Maya
- `male1` → Leo
- `male2` → Max

These are changeable fictional character names. A speaker keeps the same voice
across turns. Dialogue is sequential; overlapping speech and phoneme lip sync are
not implemented. Selected voices are all used in the generated story.

## Local end-to-end command

Install the CPU lock in a separate Python 3.12 environment, install the project
with `--no-deps`, download the pinned llama.cpp CPU archive listed in the workflow,
then run `PYTHONPATH=. python ci/download_models.py` using that environment.

```sh
python -m studio.cli generate \
  --title 'What if your coffee could float?' \
  --description 'A fictional morning with three friends, a floating cup, and a comic payoff.' \
  --minutes 1 --voices female,male1,male2 \
  --cast-profiles voices/cast-profiles.json \
  --writer-model-dir models/script-qwen3 \
  --model-dir models/chatterbox-nano \
  --out private/episode --width 1280 --fps 24
```

The profile mapping resolves directories relative to its own file.
The writer exits before voice inference, avoiding simultaneous model memory use.
Add `--resume` to reuse completed writing when the title, description, cast,
length, and writer model revision match; speech verification still runs.

## Scope and quality limits

- The Actions form is the current app interface for generation; no separate web
  frontend is deployed.
- Script length is a word budget, not an exact runtime promise. Inputs permit
  .2–10 minutes; ten-minute CPU throughput has not yet been benchmarked.
- Scripts are fictional thought experiments by default. There is no automatic
  research or independent fact verification. Generated claims need review.
- The renderer now supports shot sizes, moving entrances/crosses/approaches,
  reactions, approximate talking mouths, and cup/phone/orb motion. Its art and
  movement still require review against the IFOLOGY quality reference.
- Phrase captions are estimated within measured speech turns, not word aligned.
- Chatterbox Nano is the first CPU baseline, not an audition winner. OmniVoice
  (VoiceStudio's underlying engine), Turbo, and Qwen TTS comparisons remain pending.
  VoiceStudio itself is not installed. ASR uses a word-error threshold of 0.35; it is a screening check, not a guarantee of perfect delivery. No listening or similarity approval is
  implied by a successful encode.
- No automatic YouTube publishing or daily schedule is enabled.

Changing `ci/demo-request.json` runs the short original generated demo on push.
Normal episodes are started through Run workflow. Development checks remain a
separate small test workflow.

## Qualification evidence

The first original three-character script and revision were generated locally
from the title/description, then synthesized and screened with Whisper. All
three turns matched at word-error rate 0.0 after punctuation normalization.
The final mix is about 23 seconds. This is a short functional qualification,
not evidence of ten-minute throughput, artistic parity, or speaker likeness.

The development-check workflow also uploads the committed local qualification
sample as `local-title-to-video-qualification`. This artifact is explicitly a
locally generated sample, not a successful run of Actions-hosted synthesis.
The separate Generate voiced episode workflow now loads public profiles directly.
