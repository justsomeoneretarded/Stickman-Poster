# Blender café acting study

This is the first real geometry-based renderer in the project. It is a technical
acting study, not a replacement claim for the full film or approved character art.
Maya sits in a physical café with an empty adjacent seat, a table, lighting and
props. Her head, eyes, blinks, arms and held mug have animation controls/keyframes.
Curved sleeves follow the hand controls. The cup is parented to the right hand.
Faces, hair and clothing need further modeling before artistic approval.

The scene is built from original procedural meshes and materials. It does not
animate or zoom the AI-generated concept images. No final Leo/Max meshes, walking,
full-story blocking, dialogue, score, or finished first film are provided here.

Run the manual **Render 3D cafe acting proof** workflow. It renders 192 actual
frames at 24 FPS (8 seconds) in two aspect ratios. Preview is 640×360 landscape
or 360×640 portrait. 1080p and 4K are native scene render sizes, not upscales.
The clip is silent; the artifact includes an editable `.blend` and render receipts.
A full short film needs shot-specific acting and editing, not repetitions of this
study to fill a duration. The corrected rule is always duration × 24 frames, with
no 5,000-frame minimum. Intended film duration remains ±25% planning guidance.

Use Blender 4.3.2, verified archive SHA-256:
`4da1c956673c0485e63054e563ee69198cc8f80d8157dd7592dffc8a6a5592e6`.
The OS-packaged build lacked OpenImageDenoise support; use `--denoise` with the
official build. Eevee can use Mesa software graphics under Xvfb in the GitHub
job. Software graphics may be slow; Cycles is also exposed for a CPU quality
benchmark. First-frame shader compilation is part of the measured runtime.

```sh
python -m studio.film_render --blender /path/to/blender --out work/3d-proof --quality Preview --engine BLENDER_EEVEE_NEXT
```

The runner checks actual decoded FPS and actual encoded frame count, then fully
decodes the MP4. Receipts do not certify artistic quality, believable acting or
perfect body/object contact. Review the moving footage before final production.
