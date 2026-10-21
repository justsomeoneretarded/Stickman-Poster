# Create a complete animated film

Run **Create complete animated film** in GitHub Actions (`film-concept.yml`).
Enter a title, brief description, target minutes, short target seconds, quality,
FPS, visible characters and permitted voices. Maya, Leo/Kit Laser and Max/Warguy
are available individually and in combinations. Choose **No speech** for no
spoken lines. Permitting a voice never forces a narrator or dialogue.

The workflow runs through actual video production, not only a screenplay:

1. The pinned local Qwen writer develops the original story and directs each
   sequence into explicit executable shots. It does not generate durations.
   App-owned symbolic pacing creates a positive frame budget near the requested
   target; no word-count checks or artificial frame-count floor.
2. A separate compact adaptation of the actual long story is written and directed
   for the standalone vertical short, with its own understandable ending.
3. Only explicitly directed in-world speech uses Chatterbox Turbo and the selected
   public voice conditioning. No speech means no TTS download/inference.
4. Generated speech is measured. A shot extends when needed; dialogue is never
   cut or sped up to meet the target. Actual line timings update the subtitles.
5. Original sparse synthesized music and procedural foley are mixed from explicit
   context-aware cues with story reasons. Music ducks under dry dialogue; no
   echo/reverb is added. Intentional silence is supported. No automatic rule
   adds a sound merely because a phone/car/cup appears.
6. The articulated SVG/Cairo renderer composites every actual frame, caching static sets while animating
   expressions, eyes, gestures, articulated walking, prop handling, handoffs and
   camera shots. Native portrait blocking is rendered for the short.
7. Three actual original vector thumbnail posters are rendered from film art.
   Optional image-model thumbnails replace these with the more detailed
   reference-guided illustration style (see below).
8. Both videos are fully decoded and checked for dimensions, FPS, total frame
   count, audio presence and synchronized durations. The run requires both MP4s
   and all three thumbnail PNGs before marking delivery complete.

## Output artifact

`complete-animated-film-N` contains:

- `long-form/final.mp4`: complete landscape film, at selected 1080p or 4K.
- `short-form/final.mp4`: separately directed standalone 9:16 short.
- `thumbnails/thumbnail-1.png`, `thumbnail-2.png`, `thumbnail-3.png`.
- Each film's `description.txt`: publishing description, keywords, complete story,
  structure and visual screenplay, even without voiceover.
- Separate `publishing-description.txt`, `script.md`, story, keywords and metadata.
- `subtitles.srt`: actual speech and selected meaningful sound captions. Empty is
  valid for silence. Line times follow measured speech, not word alignment.
- `screen-text.srt`: separately directed sparse visual text. It is not a default
  nameplate/caption bar. No names are automatically displayed over characters.
- `film.json`: executable directed shots, actor actions/props/emotions, camera and
  contextual sound decisions, retained for inspection/reproduction.
- Contact sheets, audio mix reports, frame/decode reports and completion receipt.

## Scene and action library

Current environments: cafe, street, bedroom, park, bus stop, studio, classroom.
Actions: sit, stand, walk, run, reach, sip, draw, use phone, offer/receive a prop,
look away, slump, open door, pick up, put down, listen. Props: cup, phone,
sketchbook, paper and bag. Clothing/colors and the female character's hair follow
the approved designs. Camera choices include wide, medium, closeup, insert and
motivated hold/push/pull/pan. The writer is told to stage stories using these
capabilities; arbitrary new actions/sets need additional art/rig implementations.

This is procedural 2D/2.5D animation, not general text-to-video AI or Blender.
A completed render is not certification of reference-film artistic quality.
Inspect story-to-picture fidelity, pacing, continuity, emotional impact, music,
voice similarity and sound quality. Procedural foley/music can sound synthesized;
there is no claim that a human composer or sound designer approved it.

## Three thumbnail images and the approved original

Three film-art vector posters are included without an image API. They share the
film's drawing style; **they do not have the detailed 3D-like finish of the
approved AI thumbnail**. That approved source image is never overwritten.

To generate three new detailed illustrations in Actions, enable
`thumbnail_images` and configure repository secret `OPENAI_API_KEY`. This uses
`gpt-image-1` and your image API credits. It reads the approved thumbnail and cast
sheet as references, generates three distinct story-grounded concepts and saves
1280×720 PNGs. Planning/rendering without the checkbox makes no image API calls.
The chat image tool cannot be called inside Actions. The optional API integration
is mocked in tests; real API execution still needs a configured credential.

## Duration, performance and failure recovery

Minutes ±25% is guidance. Five minutes means 3:45–6:15. Model prose never controls
numeric shot durations; the renderer's frame budgets do. Measured speech can
extend them. At 12 FPS a five-minute film contains 3,600 frames; at 24, 7,200.
Actual duration and frame counts are recorded, with no duplicate-frame padding.

Scene directions are cached across matching runs, including partial writing
failures. Shot videos are cached locally with source/art/resolution/frame-rate
hashes. Each sequence logs progress. A failed run uploads diagnostics and any
completed videos, and never labels an incomplete package complete. Model access,
image API errors and actual media integrity failures remain genuine failures.
Full-length timing varies substantially with model generation, story complexity,
resolution and runner CPU. Earlier short-test estimates are not a full-run SLA.

### Story development for every new idea

The director now drafts an outline and runs a separate cached `story-edit` pass before planning shots. The editor receives the current request, draft and actual production capabilities. It revises the complete plot for a concrete desire, attempts and consequences, escalation, an action-led climax and a payoff. It must preserve the requested genre and ending rather than turn every idea into a loneliness/redemption film.

`AM_I_INVISIBLE_STORY_REVISION.md` is a story-specific authored example, not a template loaded by the workflow. Weekdays, office lunches, a helpful coworker and an inner critic are not automatic ingredients. A new title/description changes the outline and editor cache keys. Editing uses the same outline schema; it introduces no word-count, runtime or subjective-score failure threshold. The editor's artistic effectiveness still needs review on real generated stories; passing technical tests does not certify storytelling quality. Available renderer actions and settings remain a separate production limitation.
