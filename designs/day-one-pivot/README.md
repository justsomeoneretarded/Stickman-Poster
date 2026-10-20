# New direction: character-led animated short films

Status: visual development, not a completed production renderer. The previous
stickman/hypothetical-video workflow is now a legacy prototype. The existing
Actions generation workflow still runs that renderer until the replacement is
implemented and qualified; these concept images do not change its output.

The user requested a full creative pivot after supplying Day One Films'
Loneliness and Your Winter Arc Starts Now, plus two thumbnail references. This
first delivery establishes three original characters and a thumbnail direction.
Uploaded films, their extracted frames, audio and transcripts are not redistributed.

## Delivered concepts

- `three-character-concepts.png`: three original related designs, each with a
  body view and a facial close-up. These are AI-generated visual concepts with
  a dimensional 3D appearance, not mesh files, turnarounds or animation rigs.
- `thumbnail-direction.png`: an original illustrative proof using the first
  character, an empty diner seat and the temporary headline “AM I INVISIBLE?”.
  It is not a final episode thumbnail or a claim of measured click-through rate.

The film references use simplified 2D characters with outlines, layered scenery,
lighting and compositing. The supplied thumbnails have much more detailed facial
illustration. Our board interprets their restrained palette and emotional clarity
in the actual 3D direction the user requested, with distinct original proportions,
accessories and staging.

## Three-character design brief

| Name / internal ID | Shape and identity | Acting range | Palette |
| --- | --- | --- | --- |
| Maya / observer | Female; slim body, rounded oval head, chestnut wavy bob, charcoal scarf, taupe long-sleeve top, full trousers and closed shoes | Searching eyes, hesitation, retreat, small hopeful smiles | Warm ivory, sand, charcoal |
| Leo / companion | Male; compact broader body, rounded head, muted umber T-shirt, full trousers and closed shoes, open hands | Reassurance, humor when requested, frustration, guarded warmth | Oatmeal, stone, umber |
| Max / thinker | Male; taller narrow body, tapered rounded head, muted olive vest over a taupe long-sleeve top, full trousers and closed shoes | Restlessness, doubt, concentration, resolve | Ivory, warm gray, dull olive |

These are flexible cast designs, not mandatory personality roles or plot beats.
All clothing uses the middle character’s muted matte tactile T-shirt fabric as
the material guide. All three are fully dressed, including full-length trousers
and closed shoes. Maya has hair in both her board views and the matching
thumbnail. Names identify the cast in project data and documentation; no names
are printed on the images or added as video nameplates. Existing voice
choices remain available; a visual character must not require a fixed voice or
three speakers in every film.

## What carries over from the references

1. Begin with a specific relatable visual problem, not a long introduction.
2. Establish what the protagonist wants and what obstructs it. Show changing
   behavior, consequences, a setback and an earned final action. An ending should
   answer the opening's emotional question without copying the supplied plots.
3. Favor readable poses, gaze, hands, pauses and body weight over constant motion.
   Use details such as a chair, a doorway or a cup as part of the acting.
4. Return to a visual motif with meaningful changes, rather than repeating
   identical scenes. Counters are one reference device, not our mandatory format.
5. Reserve high-detail illustrated expressions for thumbnails and selected close-ups.
   Keep wider film scenes simple enough for a coherent production system.
6. Support silent shots, ambience and music. Speech is optional per shot. Do not
   fill every second with Turbo narration or burn captions into every shot.

No joke, moral, monster, motivational slogan or specific ending is mandatory.
The run's title and description continue to control topic, tone and conclusion.

## Replacement production architecture

The present Pillow renderer cannot supply these rigged 3D performances. Use
Blender for original reusable meshes, facial controls, body rigs, physical scene
layout, cameras and lights; FFmpeg for editing and delivery. Keep Chatterbox
Turbo for optional dialogue. Keep GitHub Actions as the orchestrator.

A 3-minute film at 24 fps contains 4,320 rendered frames; 5 minutes contains
7,200. Build coherent movement with key poses, animation curves, secondary motion
and contact constraints. Thousands of unrelated generated images would not
provide a consistent performance. A frame count alone is not a quality test.

The next implementation milestone is a short real animation proof using the
chosen designs: walking to a chair, sitting with weight, eye/gaze changes,
a hand gripping and lifting a cup, a pause and reaction, then a camera cut.
Include one widescreen shot and one deliberately framed portrait shot. Qualify
that proof before building a full film. Concepts are not evidence of working rigs.

Benchmark Blender's CPU renderer on the actual GitHub runner before promising
quality or runtime. Render and cache shots independently, allow low-resolution
animatics, then final frames and compositing. If CPU rendering cannot meet the
required grade at an acceptable duration, document that result; do not silently
substitute a slideshow or return to the legacy standing-character renderer.

## Story and music pipeline

Title + description -> several candidate dramatic premises -> one scene-level
outline -> storyboard/animatic -> optional dialogue and pauses -> original score
cues -> animated shots -> edit, mix and review -> long-form plus a separately
edited 9:16 short. Develop the thumbnail promise with the outline so the film
actually delivers it. Avoid requiring arbitrary dialogue word counts.

The scene representation must separate shot duration, acting beats, dialogue,
caption/essential text, ambience, foley and score. The legacy assumption of one
spoken line per scene must be replaced for this new renderer, not papered over.

Compose a sparse original motif to the animatic: few notes and instruments,
controlled tension and release, deliberate silence, room tone and precise foley.
Use piano/felt-like tones, soft pads or another palette suited to the particular
film, not a mandatory sad-piano loop. Arrange cues to story events, duck under
speech, and check the final mix by listening. No music composer or new film score
is delivered or integrated by this concept-only milestone.

## Thumbnail production

Use one dominant readable expression, one clear situation/visual contradiction,
strong value separation and a restrained palette. Text can be 0–4 short words
when it adds meaning; do not mechanically repeat the title. Avoid character
names and unrelated visual promises. Produce alternatives and inspect them at
mobile size. Clickability is a hypothesis until audience testing provides data.

The new thumbnail is a manually directed concept generated from our character
board. Automated episode thumbnail generation, rigorous identity consistency,
thumbnail variants and audience testing are still implementation work.

## Review gates

- Story: an understandable want, causal developments, readable silent actions,
  an earned ending and agreement between title, thumbnail promise and film.
- Animation: motion clips, not only contact sheets; visible foot/seat/hand
  contacts, gaze and expression changes, believable weight, shot variety,
  continuity and correctly composed portrait reframing.
- Sound: dialogue intelligibility and similarity when used, no distracting echo,
  foley synced to actions, restrained scoring and final listening review.
- Technical: full decode, correct dimensions, time synchronization and reports.

The existing advisory reports remain useful but cannot certify these artistic
standards. Do not claim a concept image, a model reviewer or a passing test suite
proves reference-grade animation.
