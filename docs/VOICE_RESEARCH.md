## Current production selection: Chatterbox Turbo

The user selected Turbo to replace Nano. Production uses
`ResembleAI/chatterbox-turbo` revision
`749d1c1a46eb10492095d68fbcf55691ccf137cd` with the existing Chatterbox source
pin `5de7a54aa4e5e2baadb0182dde554908b48b85c2`, on GitHub Actions CPU runners.
GPU speed claims are not CPU benchmarks, and a listening comparison winner has
not been established.

All three public profiles keep their authorized conditioning tensors. Checked
Hub hashes and downloaded files show identical encoder, audio decoder and all
tokenizer files between the pinned Nano and Turbo versions. Encoder SHA-256:
`f0921cab452fa278bc25cd23ffd59d36f816d7dc5181dd1bef9751a7fb61f63c`;
audio decoder SHA-256:
`d65cb687a2ed581ee6cc297e919ffefa63386944f42364ae13b78a594945514f`.
The pinned source shares conditioning extraction and speech-token vocabulary.
Turbo loads its separate larger T3 checkpoint. Metadata records the Nano origin;
variant/revision-aware cache keys prevent reuse of Nano audio as Turbo output.
Missing Turbo weights cause an error rather than automatic Nano fallback.

The research and Nano evidence below are historical, not the current selection.

# Voice-model research — 18 October 2026

Goal: realistic English narration matching the supplied speaker, no paid inference
API, reusable private voice state, and a CPU-capable development path. These are
source-review judgments, not listening-test rankings. No clone has been generated:
the uploaded MP3 exceeds this executor's 32 MiB transfer limit. The earlier environment blocked model-download preparation; see the current
network preflight below.

## Candidate ranking for this deployment

| Rank | Model | Why consider it | Tradeoffs / license |
|---|---|---|---|
| 1 | Chatterbox Nano | 110M model explicitly targeted at CPU inference; zero-shot cloning; reusable conditioning API; first candidate for standard CPU CI hardware | Need actual similarity/listening qualification. Vendor speed claim is not our benchmark. MIT code and model card; retains upstream imperceptible watermark |
| 2 | Chatterbox Turbo | 350M English model; expressive/paralinguistic controls; same conditioning workflow | More compute than Nano; GPU speed figures cannot be applied to GitHub CPU runners. MIT |
| 3 | Qwen3-TTS 0.6B Base (then 1.7B if hardware permits) | Reference-plus-transcript cloning; reusable clone prompts; useful quality challenger | Heavier inference/dependencies, especially on CPU. Embedding-only mode avoids a transcript but may reduce matching. Apache-2.0 model card |
| 4 | VoxCPM 1.5 / VoxCPM2 | Strong voice-cloning research candidate; code/weights Apache-2.0 | VoxCPM2 is 2B and not our first CPU-runner choice. Compare actual samples; do not infer quality from sample rate alone |
| 5 | OpenVoice V2 | MIT, commercially usable voice conversion; reusable speaker embedding | Multi-stage base-TTS-plus-conversion pipeline; delivery depends on the base voice and conversion artifacts need evaluation |
| Exclude default | F5-TTS standard pretrained weights | Useful research baseline, flow-matching cloning | MIT code does not make the standard pretrained weights commercially permissive; official weights CC-BY-NC. Avoid for a monetized channel without another compatible license |
| Not default | Fish Speech current releases | Worth a later quality comparison | Current community/research licenses are not equivalent to MIT/Apache. Review the precise release's code and weights separately |
| Stock fallback only | Kokoro | Efficient natural TTS; lightweight and permissively licensed | Standard Kokoro is not arbitrary zero-shot speaker cloning. Never present its voice as the user's clone |

XTTS also needs model-license scrutiny rather than assuming the repository's code
license grants unrestricted use of pretrained weights. It is not the initial choice.

## Primary sources

- https://github.com/resemble-ai/chatterbox
- https://huggingface.co/ResembleAI/chatterbox-nano
- https://huggingface.co/ResembleAI/chatterbox-turbo
- https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/src/chatterbox/tts_turbo.py
- https://github.com/QwenLM/Qwen3-TTS
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base
- https://github.com/OpenBMB/VoxCPM
- https://github.com/myshell-ai/OpenVoice
- https://github.com/SWivid/F5-TTS
- https://huggingface.co/SWivid/F5-TTS
- https://github.com/fishaudio/fish-speech
- https://github.com/hexgrad/kokoro

Inspected Chatterbox source: 5de7a54aa4e5e2baadb0182dde554908b48b85c2.
Inspected Qwen source: 022e286b98fbec7e1e916cb940cdf532cd9f488e.

## How hard is it?

- Producing recognizable cloned speech from a good reference: feasible, usually
  no speaker-specific training required with these models.
- Matching accent, rhythm, texture, emphasis and long-form consistency closely:
  materially harder; no honest guarantee before comparing outputs to the sample.
- Running occasional CPU development tests: plausible with Nano, to benchmark.
- Guaranteeing exact identity, professional performance and unattended daily
  ten-minute production on a free CPU runner: not established and not promised.

Do not quote "accuracy percentages" without a defined evaluation. Speaker-embedding
similarity is not the same as human-perceived match or narration quality.

## Required audition

Select a dry 6–15 second passage from a clean 20–60 second upload. Avoid clipping,
music, reverberation, effects, overlaps, extreme delivery and long pauses. Preserve
the original sample rate until resampling once for the chosen model. Do not aggressively
denoise away the identity cues. Qwen's full prompt path should receive an accurate
transcript; do not auto-fill a guessed transcript.

Generate three original 15–25 second passages: a calm explanation, a suspenseful
question and a passage with numbers/proper nouns. Compare Nano/Turbo/Qwen using
the same text and reference. Keep the narrator identity fixed; introduce controlled
performance variation rather than changing voices by scene. Check intelligibility,
accent, timbre, pace, breaths, unwanted repetition, omitted words, tail echoes,
pronunciation and clipping. Record wall time, audio duration, real-time factor,
peak RAM and model revision. Use listening review plus ASR for text fidelity; optional
speaker embeddings are supporting evidence, not a substitute for listening.

For long-form output generate coherent short paragraphs, concatenate lossless WAV,
add deliberate pauses, normalize once at final mix and align visuals to measured
speech. Do not force speed changes merely to hit a desired runtime. Use original
or appropriately licensed music separately; never reproduce a reference video's mix.

## Deleting the source

Chatterbox's inspected Conditionals.save/load API stores the conditioning needed
for future synthesis. Test reloading it in a fresh process without reference-file
access before deleting any working source copy. Conditioning contains speaker
information and acoustic features; deleting the MP3 does not remove those features
or guarantee the voice cannot be recreated. Profiles stay private. No audio or
profile is placed in public GitHub artifacts. Chat attachment deletion is controlled
by the chat product, not this program.

## Network preflight — 19 October 2026

The active executor's `/etc/codex/network-policy.json` reports version 1,
unrestricted HTTP access through the inherited proxy, no configured VPN, and
no explicit TCP destinations. Live environment status reports running/connected
and unrestricted policy, but enforcement state is `unknown`; enforcement readiness
is therefore not established by that status alone.

Actual HTTPS requests with inherited proxy settings and TLS verification enabled:

- `https://huggingface.co`: HEAD returned HTTP 200.
- Nano model API: GET succeeded; repository is not gated, revision
  `71ccd1d0081b430592cea481f4307e764e07bc64`.
- `t3_nano_v1.safetensors` at that revision: HEAD followed asset redirects and
  returned HTTP 200. This checks the asset route without downloading weights.

No voice weights were downloaded by this preflight. Full model transfer and
inference remain unqualified, and the earlier reference-audio transfer limitation
is not resolved by network access. Existing project validation: 14 tests passed.

## Nano CPU qualification — 19 October 2026

The live environment now reports unrestricted HTTP policy as `enforced`.
Installed the pinned Chatterbox source into `work/voice-venv` on Linux Python
3.12.14, with CPU-only Torch/Torchaudio 2.6.0. `uv pip check` passes. The
resolved dependency snapshot is `requirements-voice-cpu.lock`, including the
resolved Perth commit rather than its moving master branch.

Downloaded Nano revision `71ccd1d0081b430592cea481f4307e764e07bc64`
into ignored `models/chatterbox-nano`. Downloaded only the weights needed by
the inspected loader, tokenizer/configuration files, and bundled conditioning.
A local CPU smoke test with HF Hub offline mode succeeded using upstream bundled
conditioning. This is a stock technical test, not the user's clone.

Measured one short run: 7.07 seconds model load, 28.37 seconds generation,
5.2 seconds output at 24 kHz, real-time factor 5.46, peak process RSS 4275 MiB.
These numbers are not a long-form throughput estimate. Audio is finite and
nonempty; intelligibility and similarity have not been independently reviewed.
All 14 project tests passed after setup. No accessible user reference sample
was present, so enrollment, clone listening review, and saved-profile reload
qualification remain pending.
