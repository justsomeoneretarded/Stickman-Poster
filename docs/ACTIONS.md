# Generate a landscape video and a standalone vertical short

Open **Actions → Generate voiced episode → Run workflow** on `main`.
Every run asks for:

- **title**: your idea, for example “What if you could bench a car?”
- **description**: the funny situations, tone and payoff you want.
- **minutes**: approximate long-video length. Longer dialogue is allowed.
- **short_seconds**: approximate vertical-short length, normally 30–60 seconds.
- **voices**: choose a labeled cast: **1 speaker** (Maya/female, Leo/Kit Laser, or Max/Warguy), **2 speakers** (any pair), or **3 speakers** (all three). The same selection applies to both videos.
- **width**: landscape output width.

Production is manual only. Pushing code does not regenerate the bank story, and
new ideas do not inherit its classroom, bank, street or café requirements.

Example direction: “A playful superstrength adventure: bench a real hatchback,
shock the gym regulars, and end on a parking joke. Escalating everyday absurdity,
warm banter, no ethics lecture.”

## Two deliverables on every successful run

- **long-form-<run number>**: 16:9 landscape video and its script/captions/reports.
- **short-form-<run number>**: native 9:16 video, separate standalone dialogue,
  its own voice track, captions, source-highlight selection and reports.

The short selects the opening, payoff and high-scored visual gags from the long
story outline, then rewrites them into a standalone mini-story. It does not
just squeeze or crop the long video. Highlight ranking is a heuristic, not a
human comedy rating. Review the actual result.

Both artifacts contain `final.mp4`. At landscape width 1280 or 960, portrait
output is 720×1280; landscape width 1920 produces portrait 1080×1920. Actual
runtime follows synthesized speech; the requested duration is not a rejection
limit. Artifacts expire after seven days. Download videos you want to keep.

## Writing and animation

For benching and flying, curated comic beat blueprints keep the jokes within
what the renderer can show. They contain ideas and actions, not prerecorded
dialogue. Other topics use a model-proposed pitch and outline, with a more limited
quality guarantee. The pinned local Qwen3-4B model writes all dialogue per scene,
checkpointing completed turns. Selected cast voices stay consistent. A benching
premise opens on a visible bench press; a flying premise opens in the air.
The default tone is funny, playful, feel-good hypothetical entertainment, with
no imposed classroom framing, ethical lecture or guilt ending.

The expressive vector renderer adds original rim-lit faces, hoodie silhouettes,
layered settings, shot changes, gestures, running, attached cups, bench-press
poses with car/barbell contact, and flying scenes. Portrait scenes are composed
independently with larger caption treatment. The art is procedural and original;
no frames or characters are copied from the supplied reference.

## Voices and runtime

The three reusable profiles are public with the user's authorization:
`female` → Maya, `male1` → Leo, `male2` → Max. No `VOICE_PROFILE_KEY` is needed.
Original recordings remain outside the repository. The engine is Chatterbox Nano
on CPU; VoiceStudio/OmniVoice, Turbo and Qwen TTS auditions are still pending.
Whisper screens spoken text, but does not prove naturalness or speaker similarity.
Audio echo/robotic quality is not claimed fixed by the visual redesign.

Writer, speech and rendering run separately so models do not occupy memory at
the same time. A failed run uploads diagnostics. The early script artifact
contains both versions before speech/rendering completes. No automatic YouTube
publishing is configured.

## Visual review samples

**Generator development checks** uploads
`expressive-style-study-both-formats`: 20-second silent landscape and portrait
fixtures showing benching a car, a barbell, close-up reactions, and flight.
These fixed motion studies are explicitly labeled; they are not model-written
production episodes. Use them to review the visual direction without waiting
for speech synthesis or spending a full episode render.

A successful technical run is not artistic approval. The renderer still has a
limited vocabulary of poses and props, and it does not equal the reference's
hand-directed animation. Arbitrary ideas may require more animation primitives.
Comedy quality, continuity, captions and voices need review before publishing.

## Local generation

Use the CPU voice lock, pinned models and llama.cpp runtime from the workflow:

```sh
python -m studio.cli generate \
  --title 'What if you could bench a car?' \
  --description 'Funny feel-good superstrength, a shocked friend, and a parking joke.' \
  --minutes 3 --short-seconds 45 --voices female,male1,male2 \
  --cast-profiles voices/cast-profiles.json \
  --writer-model-dir models/script-qwen3 --model-dir models/chatterbox-nano \
  --out output/episode --width 1280 --fps 24
```

Outputs are in `output/episode/deliverables/long-form/` and `short-form/`.
