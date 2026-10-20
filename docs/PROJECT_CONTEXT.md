# Stickman-Poster project context

Updated 19 October 2026 from the current thread, repository, and the readable
conversation section of the user-provided previous-chat paste.

## First film concept and workflow controls

The user selected “Am I Invisible?” (typed “am in invisible”) for the first film.
`films/am-i-invisible/` contains the first assistant-authored editorial story,
script, description, keywords, short edit and production spec. It is not rendered.
The initial plan is 210 seconds / 5,040 frames. Main films must use 24 FPS and
at least 5,000 rendered frames. Target minutes carry ±25% advisory range, not
fatal validation; an incompatible short target is flagged and the frame floor
wins. Short-form edits retain their independent duration.

A NEW manual **Develop animated short film** workflow accepts fresh title,
description, 1080p/4K intended resolution, target minutes and optional voice set.
`studio.film_concept` generates fresh model-written stories/scripts/publishing
packages in-app, with silent scenes supported; it does not run the legacy
renderer. Resolution and frame counts remain planning metadata until a real 3D
render exists. Model-script output, story prose and publishing descriptions are
separate deliverables, plus useful keywords and a vertical edit plan.

## Latest creative pivot — supersedes the hypothetical-stickman direction

The user selected character-led emotional animated short films, citing uploaded
Day One Films references and thumbnails. They requested three similar-grade
original 3D character designs FIRST. See `designs/day-one-pivot/` for the actual
concept board, original thumbnail proof and replacement production brief.
The references use simplified 2D film animation and more detailed illustrated
thumbnails; the concepts interpret their palette and emotion in requested 3D.
The cast is now named Maya (female, left, chestnut wavy hair), Leo (male,
center) and Max (male, right). All three wear complete outfits with trousers
and shoes; muted tactile cloth follows Leo’s T-shirt. The thumbnail has been
updated to show Maya’s hair and covered arms, retaining its approved layout.
Names are project identities, not automatic on-screen labels.
These are generated concept images, not rigged models or a completed renderer.
The current Actions generator remains the legacy pipeline until a replacement
Blender animation proof is built and qualified. Silent scenes, original music
cues, physical interactions and thumbnail development are explicit new needs.
Retain per-run title/description, flexible durations, selectable 1–3 voices,
Turbo for optional speech, native long/short delivery and minimal video overlays.
Do not impose jokes or a moral by default. Do not copy the supplied plots or
publish their original media in the repository.

## Latest TTS change

The user requested replacing Nano with Turbo. Production model directory is now
`models/chatterbox-turbo`, pinned at `749d1c1a46eb10492095d68fbcf55691ccf137cd`.
Three saved profiles are configured for Turbo after shared encoder/decoder,
tokenizer and conditioning-API compatibility checks. Nano audio caches invalidate.
All three Turbo voice clips passed ASR (WER 0.00, 0.10, 0.00). See
`previews/turbo-voice-qualification/` for clips and measured CPU evidence.
The production job timeout is now 360 minutes for the heavier CPU engine.
The older Nano observations below are historical. Turbo still needs listening
review for voice similarity, echo and naturalness; a full-length CPU run is not
qualified by short clips.

## Recovered previous-chat context

- The old conversation was attached to a restricted cloud environment. Hugging
  Face requests returned HTTP 403 even after a different, unrestricted environment
  was published. Saved configuration and the running conversation attachment were
  different; changing Windows settings or command permissions did not resolve it.
- The user opened this continuation thread to use the new environment. The initial
  instruction was to check the active network policy and huggingface.co first.
- The previous assistant explicitly reported that private audio files and
  unpublished audition code remained in the old workspace and might need transfer.
  These are historical reports, not verified files in this workspace.
- Recordings must remain private and must not be committed to the public repository.
- The user clarified in this thread that there were three audio files from three
  different people. Keep speaker samples and eventual profiles separate. Do not
  assume which speaker is the intended primary narrator.

## Verified in this continuation

- Repository: /workspace/Stickman-Poster.
- Network: unrestricted startup HTTP policy; subsequent live status reported
  unrestricted/enforced. huggingface.co and the Nano asset route returned HTTP 200.
- Separate Linux Python 3.12 voice environment: work/voice-venv.
- Chatterbox code revision: 5de7a54aa4e5e2baadb0182dde554908b48b85c2.
- Nano model revision: 71ccd1d0081b430592cea481f4307e764e07bc64,
  downloaded into ignored models/chatterbox-nano.
- CPU dependencies installed and checked; snapshot: requirements-voice-cpu.lock.
- Bundled-voice technical inference passed: 5.2 seconds of audio, 28.37 seconds
  generation, 7.07 seconds model load, 4275 MiB peak RSS. This is not a user clone.
- 14 project tests passed. See docs/VOICE_RESEARCH.md for qualification limits.
- No original user reference recordings were found in the workspace or attached
  download locations during the continuation. User enrollment, saved-profile
  reload, similarity assessment, and listening qualification remain pending.

## Context boundaries and next steps

The supplied paste contains the later environment troubleshooting conversation,
not the complete original design/development discussion. Its remaining browser
application/session data is not project context and is deliberately excluded.
Do not copy the raw paste into version control.

Recover the old workspace's private audio and unpublished audition code, or obtain
fresh attachments. Compare transferred code before integrating it. Recover earlier
project decisions from additional conversation text if available. Then inspect the
three speaker samples, establish profile labels, enroll separately, and audition
original passages. Never describe bundled-voice output as a cloned user voice.

## Reference assets recovered — 19 October 2026

The user reattached all three MP3s in this thread. They were successfully
downloaded (each below 32 MiB) and preserved under ignored `private/sources/`.
Speaker labels: `female`, `male1-kit-laser`, `male2-warguy`. These labels derive
from filenames and do not independently verify identity. No primary narrator
has been chosen. The earlier missing-reference blocker is resolved.

Source durations: 126.69, 176.64, and 636.24 seconds respectively. Separate
12-second mono 24 kHz reference WAVs are in `private/references/`, beginning
at 48, 42, and 28 seconds respectively. Selection used automated low-silence
and clipping checks within the first 90 seconds; no listening claim is made.
The private inspection JSON records exact source locations and selection details.

Three Nano profiles enrolled successfully under `private/profiles/` using the
local pinned model. Audition generation and fresh-process profile reloading
are being qualified separately. Original MP3s and reference WAVs are retained.
Private assets/profiles/output must remain excluded from public version control.
The old workspace's unpublished audition code is still not recovered.

## Three-speaker saved-profile smoke test completed

All three profiles generated finite, nonempty WAVs from a fresh process that
loaded conditioning and never opened reference audio. The same original gravity
passage was used for comparison. Results are private under `private/auditions/`:

- female: 5.80s audio; 15.07s generation.
- male1-kit-laser: 5.60s audio; 14.47s generation.
- male2-warguy: 5.88s audio; 14.63s generation.

Technical reload checks passed; no claim of listening approval, text fidelity,
or speaker similarity is established. Original sources remain preserved.

## Three-speaker animation previews completed

Rendered the same original gravity passage and scene for all three profiles at
960×540, 24 fps. Files: `private/previews/<speaker>/final.mp4`, with matching
reports, captions, and contact sheets. All three passed full FFmpeg decode,
audio-presence, and duration checks. Comparison index: `private/previews/comparison.json`.
Three short audio comparisons were returned inline in the continuation chat.
Voice quality and likeness have not been assessed by listening in this runtime;
user listening review and narrator selection remain pending. These previews
are technical comparisons, not finished production episodes.

## Character cast requirement and implementation

User decision: use the three voices together for different characters; a video
may feature one, two, or all three. Do not select a single permanent narrator.

Implemented optional project `cast` (maximum three) and per-scene `speaker` and
`characters`. Each scene is one spoken turn. Private `--cast-profiles` mapping
routes voice IDs to independent saved profiles. Missing mappings fail before
synthesis. Visuals show the selected characters with active-speaker labels.
The existing single-narrator workflow is preserved. Overlapping speech and
phoneme lip sync remain unsupported. Title-based planning/produce is still
single-narrator; authored cast projects use speak then render.

`examples/three-friends.json` is an original three-person conversation with
fictional character names Maya (female), Leo (male1), Max (male2). Names are
provisional example labels, not a user-approved permanent cast. All three private
profiles generated dialogue in sequence; the manifest records speaker/voice
assignments. Output is under `private/three-friends/`. 17 tests passed, including
cast-size validation, missing/hidden-speaker rejection, voice routing, turn order,
and existing renderer/media checks. Listening approval remains pending.

Three-friends render completed: 11.3 seconds, 960×540 at 24 fps; full video
decode, duration tolerance, and audio-stream checks passed. Contact sheet was
visually inspected for three distinct characters and correct speaker labels.
Combined dialogue audio was returned inline for user listening review.

## Visual quality reference clarified by user

User reattached the IFOLOGY telekinesis reference video (265.90 seconds,
1920×1080, 30 fps). It is accessible at
`/workspace/attachments/14adc1a8-ee0b-4f2c-b69f-1f91f7822973/What IF You Could Move Things With Your Mind - IFOLOGY (1080p, h264).mp4`.
The user explicitly wants its visual movement quality, while saying its audio
is terrible and needs improvement. Do not treat reference audio as approved.

Inspected a visual overview sampled every 15 seconds and frame sequences at
12–14 and 58–61 seconds. Observed articulated entrance gestures, changing face
poses, tilted/reclining full-body poses, camera reframing, varied narrative props
(phone, car, TV, pen), layered interior/street/stage compositions, light/glow,
and explanatory inserts. This is sampled visual inspection, not full playback
or an audio listening review. The three-person voice-routing demo is below
this target; fixed stage placement, generic point/think actions, and captions
do not establish comparable animation quality.

Development priority: improve original scene staging, meaningful full-body
action and object interaction, expressions/reactions, camera composition, and
transitions, retaining optional one/two/three-character voice routing. Qualify
a short original scene visually and by listening before scaling episode length.
Technical decode tests alone do not establish artistic approval.

## Title/description generation and GitHub Actions implementation

User requested complete automatic scripting and rendering with GitHub Actions
as the current interface. Implemented `studio.cli generate` and the Generate
voiced episode workflow with title, description, duration, voices, and width inputs.
The script is generated by pinned Qwen3-4B-Instruct-2507 Q4_K_M through pinned
llama.cpp CPU runtime, with schema constraints, validation, and a separate
editorial revision. An initial smaller-model trial was rejected for unreliable
scene counts. There is no manual or canned script fallback.

The pipeline routes one/two/three-character dialogue to the saved Nano profiles,
checks generated speech with Whisper base.en and retries mismatches, sizes scenes
from actual audio, renders camera framing/motion/props/reactions, normalizes the
final mix, decodes the video, and creates an allowlisted delivery package. Nano
remains the CPU baseline, not the winner of the pending OmniVoice/Turbo/Qwen TTS
auditions. Visual parity and listening approval remain unqualified.

Local end-to-end qualification: an original coffee thought experiment generated
from title/brief, draft+revision, 62 spoken words, three voices, 22.9-second
960×540/24fps output. Whisper matched all three turns at WER 0.0 under the
normalization used. 22 tests passed. The generated local sample is in
`previews/title-to-video-qualification/` and is uploaded by development checks
under the explicit artifact label local-title-to-video-qualification.

Code pushed to main at 687e339. GitHub development checks succeeded:
https://github.com/justsomeoneretarded/Stickman-Poster/actions/runs/39247725255
The full episode workflow started but stopped at missing VOICE_PROFILE_KEY:
https://github.com/justsomeoneretarded/Stickman-Poster/actions/runs/39247725310
The integration returned HTTP 403 for repository Actions secret management.
Only authenticated ciphertext of the three saved profiles is committed; its
matching key stays at ignored `private/actions-key.txt`. User must install the
repository Actions secret using an account with permission; docs/ACTIONS.md
contains the command and GitHub settings instructions. No successful
Actions-hosted synthesis is claimed before that secret is configured.

## Public voice profiles authorized

On 19 October 2026, the user explicitly confirmed publication of the reusable
three-speaker conditioning profiles after their public reusability was explained.
Published them under voices/profiles with a relative cast-profiles mapping.
Original MP3s remain outside Git. Removed the encrypted profile archive, secret
preflight, decryption helper, and workflow dependency on VOICE_PROFILE_KEY.
Earlier private-profile and missing-secret notes above are historical and are
superseded by this decision. Next verification is the full generation workflow
on the hosted Actions runner with public profiles.

## First full hosted generation succeeded with public profiles

Run 39265452782 completed successfully after publishing public profiles:
https://github.com/justsomeoneretarded/Stickman-Poster/actions/runs/39265452782
Artifact: voiced-episode-2, ID 12192952488. This was a fresh Actions-hosted
script draft + revision, not reuse of the committed local sample. The writer
produced 43 words in 53.03 seconds. All three speaker profiles synthesized
dialogue; ASR WERs were 0.0, 0.0, and 0.0455. Final video is 18.0 seconds,
960×540, 24fps. Rendering, audio presence, timing, and full decode passed.
The artifact was downloaded and its files, reports, and contact sheet inspected;
video decoded locally as well. Human listening and artistic approval remain
pending. Development checks also passed on the public-profile commit 8e463e9.
VOICE_PROFILE_KEY is no longer required.

## Movement feedback and three-minute bank story request

User rejected stationary cast staging, asked for moving chases and physical
character/environment interaction (for example lifting a cup to drink), and
reported echo-like, unnatural/robotic audio. Audio engine quality remains an
open issue; ASR alone does not qualify naturalness. The user asked to work
through improvements step by step and requested an approximately three-minute
generated video titled "What if you could rob a bank and never get caught".

Implemented per-actor full-shot blocking, monotonic running/chasing paths,
distance-driven alternating leg cycles, explicit police costume, hand-attached
carried bags, cup lift/sip/replace poses, and a bag handoff. Added original
classroom, outdoor field, bank lobby, and cafe environments. New writer scenes
include a staging directive compiled into validated blocking tracks. The
requested brief is a fictional magical thought experiment with non-operational
crime content, moving through classroom/field/bank/street/cafe and back.
Short sentences now share voice context up to the model's chunk limit; this
reduces resets but does not establish that echo or robotic delivery is fixed.

Long-form Actions now has separate writing, speech verification, and rendering
steps. Reduced writer context allocation for typical episodes to fit standard
CPU runners; larger episodes retain a larger context. Added motion metrics to
artifacts and tests for actual displacement, cup contact poses, new locations,
and paragraph continuity. Next step is hosted generation and inspection of
the requested three-minute episode, with actual duration reported honestly.

## Long-form qualification defects found and correction

Run 39272182436 completed but its output was only 141.5 seconds (372 words),
so it was not accepted as the requested three-minute delivery. Inspection also
found third-person stage directions being read aloud and a premise cop-out
claiming the theft never happened. The actor movement and new locations worked;
these script/duration defects are being corrected before final delivery.

Added dialogue-style validation, explicit required locations, a 160-word/minute
writing budget calibrated against actual output, and an automatic revision mode
that takes the previous machine-generated project as a seed. The rejected
generated project is preserved as ci/bank-generated-seed.json for provenance;
its dialogue was not manually rewritten. The new pass must produce spoken
dialogue, maintain the fictional theft/uncatchable premise, show all five
requested locations, and target a tighter word budget.

The first length-correction run (39276969090) was stopped by validation: the
model returned only 334 words after three revision attempts. This was not
accepted or silently padded. The writer now generates a fixed-size array of
single spoken words per turn, compiled into dialogue, so the JSON grammar
enforces the word budget instead of relying on the model counting words.

The seed-revision approach also failed local review: it copied the rejected
stage directions and premise denial, with truncated sentences. Removed that
seed from the active request and restart from title/description. Require
complete spoken thoughts and prohibit punctuation-only word tokens. Workflow
concurrency now supersedes stale queued versions of the same request.
As of this update the corrected episode is not complete; GitHub runner
assignment is queued, and no corrected three-minute artifact is verified.

## Required-location writer failure and repair

User reported hosted writing failed after 13m54s because cafe and street were
missing after three whole-story retries. Required-location requests now use an
app-owned ordered scene plan, assigning location/speaker/staging before model
speech. Dialogue is generated and repaired per scene, checkpointing validated
turns. Model output cannot omit or rename locations. Compilation checks coverage
again. Normal speech strings replace fixed word arrays in this mode: actual
local inspection found the arrays encouraged fused phrases and malformed tokens.
An adaptive remaining-word budget targets 480 words for the 3-minute request;
actual video duration must still be measured. Normal speech and punctuation were
confirmed in the local model's first turn. All 33 tests pass, including setting
coverage, chase/contact staging, and interrupted generation resume. Full hosted
episode and voice/artistic qualification are still pending; no final video claim.

## Per-line word limit failure

Run 39287901346 failed on scene 3 because a natural 31-word turn exceeded the
adaptive 23–29-word window. This was an overly strict validation rule. Per-scene
word counts are now guidance; natural 8–65-word turns are accepted within the
existing character limit. Remaining scene targets rebalance the overall budget,
with targets bounded to avoid asking for an excessively long or negative turn.
The report records the total word-count deviation; no exact-duration claim is
made. The regression reproduces the 31-word scene, verifies no extra retry, and
allows a slightly longer final sentence. All 33 tests pass.

## User duration preference: story before runtime

User explicitly accepts roughly five minutes and requests no exceptions caused
by exceeding the requested minutes. Removed per-turn word-count rejection,
whole-story duration-derived word rejection in the legacy path, and automatic
shortening of later planned turns to squeeze the story into the time target.
Duration is prompt guidance and reporting only. The shared parser now accepts
longer dialogue within the renderer's existing per-scene character capacity.
Regression test accepts over five minutes of dialogue for a three-minute target;
all 34 tests pass. Technical validation and malformed-output errors still apply;
this does not claim every possible pipeline failure is fixed. The active brief
now explicitly allows a longer complete story.

## Reference review, playful hypotheticals and two-format workflow

User confirmed the 3-minute episode completed but strongly rejected the art,
movement and writing. They want funny, feel-good hypotheticals (bench a car,
bench 400 pounds, fly), not ethical lessons. Every run should accept a new idea,
description and length, always delivering landscape and a strong vertical short.
Reviewed the reattached IFOLOGY reference: expressive black faces with white
features, hoodie silhouettes, varied shot sizes, layered lighting/space and
specific visual actions, not a static presenter lineup.

Implemented expressive-v2 original procedural art with rim lighting, face and
mouth motion, articulated poses, attached coffee cups, physical bench press
(car or barbell), and airborne travel. Added gym/rooftop/park settings and native
portrait composition. Removed title/name HUD. Captions, thumbnails and contact
sheets respect the output orientation. This remains a limited vector-animation
prototype, not reference-quality hand-directed animation.

Production Actions is manual-only. Title and description are required fresh
inputs; no bank demo, required locations or seed are inherited. Form includes
long minutes, short seconds, cast, output width (default 1920). Both lengths are
soft guidance. Known bench/fly ideas use curated renderable comic beat blueprints;
all spoken lines are LLM-generated. Other ideas use a model pitch/outline with
less reliable visual/plot fidelity. Actual initial free-outline trial was weak
and proposed unsupported crashes; it was not accepted as a quality result.

Shorts select unique high-scored comic beats plus opening/payoff, rewrite speech
for standalone continuity, synthesize a separate track, and render native 9:16.
Successful production artifacts are long-form-N and short-form-N. No change of
speech engine or claim that echo/robotic quality is fixed. The new local writing
trial uses bench-car warmth/parking/membership gags and no imposed ethics ending.

40 tests pass, including encoded dual-format/audio packaging, independently
written scripts, portrait thumbnails, input isolation, premise blueprints,
visible car-load motion, and on-screen flying character framing. Development
checks create a clearly labeled 20-second silent motion study in both formats.
Voiced miniature qualification and hosted artifact verification follow below.

Local dual-format voiced qualification completed: long-form 1280x720/24fps,
22.5 seconds, 6 spoken turns; separate short 720x1280/24fps, 29.8 seconds,
3 rewritten turns. Both full decode checks passed. Final ASR WER maximum was
0.154 on landscape and 0.069 on portrait. Encoded contact sheets and portrait
thumbnail were inspected. Fixed an observed wheel/face occlusion and a duplicate
standing hero; tests protect both. Re-rendered and decoded both outputs after
those fixes. Sanitized public outputs are under previews/comedy-two-format-qualification,
clearly labeled miniature trials. Final local suite: 40 passing tests.

Hosted verification: development run 39316154733 on bcb7e0a passed every step,
including 40 tests, landscape/portrait style rendering and full FFmpeg decode.
Published artifacts: expressive-style-study-both-formats (12217782537), and
local-voiced-comedy-two-format-qualification (12217587949). The latter contains
the locally generated/verified miniature voiced trials, not Actions-hosted
speech synthesis. Production remains manual; this code push did not start an
episode. Review links expire after 7 days; the voiced qualification files are
also preserved in the public repository. Full-length production with the revised
visual/comedy approach still requires a new manual run and artistic review.

## Explicit speaker-count menu

User asked to confirm duration is flexible and to choose one/two/three voices.
Confirmed actual duration/word overrun is not a rejection condition. Improved
Actions cast menu labels to show speaker count plus voice names for all seven
combinations. Backend normalizes labels to stable voice IDs and retains support
for old raw-ID API inputs. Same cast is used in long and short versions. All
41 tests pass, including every menu selection; workflow YAML/default/options
were checked against the backend mapping. No production episode was started.

## Explicit override: description controls tone, no forced humor

User instructed not to hardcode jokes/comedy unless explicitly requested in the
manual workflow description. Removed the active bench/fly gag library and its
module, removed automatic playful-comedy mode, and replaced imposed jokes/morals
in both long and short prompts with description-driven direction. The outline
cache version changed so old comic outlines are not silently reused. Visual
rendering stays expressive-v2 independently of genre. The form description now
asks for idea/events/tone/ending and makes humor optional. All 41 tests pass,
including a serious bench-car prompt regression that checks preset parking,
pigeon and callback-joke instructions are absent. This supersedes earlier
notes recommending automatic comedy blueprints. No production episode started.
