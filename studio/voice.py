"""Optional Chatterbox adapter. Never silently substitutes a stock voice.

Verified against source commit 5de7a54aa4e5e2baadb0182dde554908b48b85c2.
Model inference is NOT validated until a real sample and weights are available.
"""
import hashlib
import json
import os
import re
from pathlib import Path

SOURCE_COMMIT = "5de7a54aa4e5e2baadb0182dde554908b48b85c2"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def speech_chunks(text, limit=220):
    """Keep short paragraphs together; split only when model length requires it."""
    result,current=[],""
    for sentence in re.split(r"(?<=[.!?])\s+",text.strip()):
        words=sentence.split()
        sentence=" ".join(words)
        if not sentence:
            continue
        proposed=f"{current} {sentence}".strip()
        if len(proposed)<=limit:
            current=proposed
            continue
        if current:
            result.append(current);current=""
        for word in words:
            proposed=f"{current} {word}".strip()
            if len(proposed)>limit and current:
                result.append(current);current=word
            else:
                current=proposed
    if current:
        result.append(current)
    return result


def load_model(variant="nano", device="cpu", model_dir=None):
    if variant not in {"nano", "turbo"}:
        raise ValueError("Voice variant must be nano or turbo")
    try:
        import torch
        from chatterbox.tts_turbo import ChatterboxTurboTTS
    except ImportError as exc:
        raise RuntimeError("Install the separate voice requirements first; no fallback voice was used") from exc
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    if model_dir:
        return ChatterboxTurboTTS.from_local(model_dir, device=device, nano=variant == "nano")
    return ChatterboxTurboTTS.from_pretrained(device=device, nano=variant == "nano")


def enroll(reference, directory, variant="nano", device="cpu", model_dir=None):
    from .media import audio_duration
    if not 6 <= audio_duration(reference) <= 30:
        raise ValueError("Enrollment expects a clean 6–30 second WAV excerpt")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "conditioning.pt").exists():
        raise ValueError("Profile already exists; choose a new directory")
    model = load_model(variant, device, model_dir)
    model.prepare_conditionals(str(reference))
    # Source API persists tensors/features; future synthesis needn't open the WAV.
    tmp = directory / "conditioning.tmp.pt"
    model.conds.to("cpu").save(tmp)
    tmp.replace(directory / "conditioning.pt")
    metadata = {"schema_version": 1, "engine": "chatterbox", "variant": variant,
                "source_commit": SOURCE_COMMIT, "reference_sha256": sha256(reference),
                "conditioning_sha256": sha256(directory / "conditioning.pt"),
                "sample_rate": model.sr, "status": "enrolled; listening validation pending",
                "privacy": "Contains speaker conditioning; keep private even after deleting the source"}
    (directory / "profile.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def synthesize_scenes(project, profile, out, device="cpu", model_dir=None):
    import numpy as np
    import soundfile as sf
    from chatterbox.tts_turbo import Conditionals
    profile, out = Path(profile), Path(out)
    metadata = json.loads((profile / "profile.json").read_text())
    if metadata.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("Profile source version mismatch; revalidate adapter compatibility")
    conditioning = profile / "conditioning.pt"
    if sha256(conditioning) != metadata["conditioning_sha256"]:
        raise ValueError("Voice conditioning checksum mismatch")
    model = load_model(metadata["variant"], device, model_dir)
    model.conds = Conditionals.load(conditioning, map_location="cpu").to(device)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, scene in enumerate(project["scenes"]):
        if not scene["narration"].strip():
            raise ValueError("Voice scenes need nonempty narration")
        digest = hashlib.sha256((scene["narration"] + metadata["conditioning_sha256"] +
                                 metadata["variant"] + SOURCE_COMMIT + "paragraph-v2").encode()).hexdigest()
        path = out / f"{index:03}.wav"
        cache = out / f"{index:03}.json"
        hit = cache.exists() and path.exists() and json.loads(cache.read_text()).get("key") == digest
        if not hit:
            chunks = []
            for text in speech_chunks(scene["narration"]):
                wav = model.generate(text, temperature=0.7)
                samples = wav.detach().cpu().numpy().reshape(-1)
                if not np.isfinite(samples).all() or len(samples) < model.sr*.15:
                    raise RuntimeError("Voice generation returned invalid or empty audio")
                if chunks:
                    chunks.append(np.zeros(round(model.sr*.12), dtype="float32"))
                chunks.append(samples)
            samples = np.concatenate(chunks)
            if not np.isfinite(samples).all() or len(samples) < model.sr*.15:
                raise RuntimeError("Voice generation returned invalid or empty audio")
            sf.write(str(path), samples, model.sr, subtype="PCM_16")
            cache.write_text(json.dumps({"key": digest, "engine": "chatterbox", "variant": metadata["variant"]}))
        entries.append({"scene_id": scene["id"], "file": path.name})
    manifest = {"schema_version": 1, "voice": "cloned voice; listening review required",
                "engine": "chatterbox", "entries": entries}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def synthesize_cast(project, profiles, out, device="cpu", model_dir=None):
    """Route each dialogue turn to its assigned private voice, never a fallback."""
    from .project import validate
    validate(project)
    if not project.get("cast"):
        raise ValueError("Cast synthesis requires a project cast")
    if not isinstance(profiles, dict):
        raise ValueError("Voice profiles must be a mapping")
    by_id = {m["id"]: m for m in project["cast"]}
    voices = list(dict.fromkeys(by_id[s["speaker"]]["voice"] for s in project["scenes"]))
    for voice in voices:
        if voice not in profiles:
            raise ValueError(f"Missing profile for voice {voice}; no fallback voice was used")
        folder = Path(profiles[voice])
        if not (folder / "profile.json").is_file() or not (folder / "conditioning.pt").is_file():
            raise ValueError(f"Incomplete profile for voice {voice}")
    out = Path(out)
    entries = {}
    for i, voice in enumerate(voices):
        scenes = [s for s in project["scenes"] if by_id[s["speaker"]]["voice"] == voice]
        folder = f"voice-{i:02}"
        manifest = synthesize_scenes({**project, "scenes": scenes}, profiles[voice], out / folder, device, model_dir)
        for scene, entry in zip(scenes, manifest["entries"]):
            entries[scene["id"]] = {**entry, "file": folder + "/" + entry["file"], "speaker": scene["speaker"], "voice": voice}
    manifest = {"schema_version": 1, "engine": "chatterbox", "voice": "character cast; listening review required",
                "entries": [entries[s["id"]] for s in project["scenes"]]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
