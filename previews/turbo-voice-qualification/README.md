# Turbo three-voice CPU qualification

These are newly synthesized Chatterbox Turbo clips using the three authorized
public voice profiles. They are not Nano clips relabeled as Turbo. The fixture
uses manually written dialogue; production scripts remain generated from the
workflow title and description.

Each clip passed the existing ASR threshold and complete FFmpeg decoding. See
qualification.json for actual CPU timing, memory and waveform review flags, and
speech-check.json for exact transcripts and error rates. This short local test
does not establish full-episode runtime or GitHub runner performance. Listen to
judge naturalness, echo and speaker similarity; these are not automatically
certified. The earlier voiced video qualification remains a historical Nano test.

Reproduce with ci/turbo_voice_preview.py and the speech_check command documented
in docs/VOICE_RESEARCH.md. Generated clips are intentionally public under the
user-authorized voice-profile workflow; original recordings are not included.
