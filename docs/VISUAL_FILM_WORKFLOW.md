# Visual-first film development

Use **Develop animated short film** in GitHub Actions. Each run accepts a fresh
title and a brief description (two lines are enough), target minutes, quality,
12/24 FPS, visible characters and independently permitted voices. All three
approved identities remain available individually and in combinations:
Maya, Leo/Kit Laser, Max/Warguy. Choosing a voice never requires speech.
Choose **No speech** for a completely unspoken film.

The default is a primarily silent visual screenplay with simple original music
direction and context-dependent diegetic sound. A call, phone vibration, cup or
horn is added only when the model gives it a specific story purpose. It is not
an event-to-sound lookup table. The model can still make poor creative choices;
review the generated plan before treating it as a finished production.

The title and brief drive the story, not a fixed cafe template. The writer plans
an opening question, desire, exposition, escalation, pressure/setback, a turning
point, climax and aftermath. These are editorial tools: inapplicable beats can
be empty, redemption is not compulsory, and no joke or moral is imposed.
Scene plans carry visible actors, emotional changes, actions, camera direction,
sparse screen text, sound decisions and original music direction. A standalone
vertical edit has its own ending. Approved reference artwork remains read only.

## Deliverables

- `description.txt`: publishing description, keywords, complete story, structure
  and full visual screenplay, even when there is no voiceover.
- `publishing-description.txt`: just the viewer-facing publishing copy.
- `script.md`, `story.txt`, `story-arc.json`, `shot-plan.json`, `film.json`.
- `sound-plan.json`: scene-relative and timeline cue times, story reasons,
  speech/offscreen decisions, ambience, foley, music and intentional silence.
- `subtitles.srt`: actual planned speech and deliberately selected sound captions.
  Silent acting is not rewritten as narration. An empty file is valid.
- `screen-text.srt`: a separate sparse visual-text plan; not automatic captions.
- `subtitle-notes.txt`: planned timing, not measured/word-aligned final subtitles.
- `thumbnail-briefs.json` and three `thumbnails/option-N-prompt.txt` files: distinct
  concepts based on actual story scenes, with short truthful emotional hooks.
- `production-spec.json`, `review.json`, `delivery-status.json`, publishing metadata,
  keywords and `short-edit.md`.

## Three thumbnail images

The optional **thumbnail_images** checkbox requests three new reference-guided
images, not changes to the approved original. It uses the OpenAI image API
(`gpt-image-1`) and your API credits. Configure a repository Actions secret named
`OPENAI_API_KEY` before enabling it. No API call or charge is made by planning
alone. Missing credentials are detected before the expensive writing stage.
The chat's image-generation tool is not an API available inside Actions.

The image stage reads the approved thumbnail and character-sheet references,
creates three separate ideas based on the generated story, and writes
`thumbnails/thumbnail-1.png` through `thumbnail-3.png` at 1280×720. Its prompt keeps
critical content within a 16:9 safe area; the larger API output is cropped to fit.
Review typography, hands, character fidelity and crop safety before publishing.
These are image-model outputs, not guaranteed replicas of the approved art.
If an image request fails, completed images and the story package are retained.
Without the checkbox, three image briefs are produced; no finished thumbnail
images are claimed. `delivery-status.json` records the actual image count.

## Duration and current limits

Minutes ±25% is planning guidance, never a word-count or duration exception.
Five minutes means a preferred range of 3:45–6:15. At 12 FPS, exactly five minutes
would be 3,600 frames; at 24 FPS, 7,200. No artificial frame-count floor.
An out-of-range plan is flagged for pacing review rather than silently padded.

**This workflow produces a production package, not a finished arbitrary film.**
The layered renderer currently implements the separately qualified 14-second
opening only. Full-film scene/action coverage, contextual sound synthesis/mixing,
final retimed subtitles and finished long/standalone-short video integration
remain unfinished. Text plans are not evidence that those media were rendered.
The first example under `films/am-i-invisible/` is an authored sample; future
workflow runs use the pinned local Qwen writer with the new run's inputs.
