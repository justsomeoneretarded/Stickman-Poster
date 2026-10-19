import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw

from . import media, project, render


def load_audio_manifest(path, scenes):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if len(entries) != len(scenes) or [e.get("scene_id") for e in entries] != [s["id"] for s in scenes]:
        raise ValueError("Audio manifest must match every scene ID in order")
    files = []
    for e in entries:
        audio = (path.parent / e["file"]).resolve()
        if path.parent not in audio.parents or not audio.is_file():
            raise ValueError("Audio files must exist inside the manifest directory")
        files.append(audio)
    return files


def render_project(args):
    started = time.perf_counter()
    p = project.load(args.project)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.width < 320 or args.width > 1920 or args.width % 32:
        raise ValueError("Width must be a multiple of 32 between 320 and 1920")
    height = args.width * 9 // 16
    if height % 2:
        raise ValueError("Video dimensions must be even")
    if not args.silent_preview and not args.audio_manifest:
        raise ValueError("Provide --audio-manifest or explicitly choose --silent-preview. No substitute voice is generated.")
    if args.silent_preview and args.audio_manifest:
        raise ValueError("Choose either a silent preview or audio")
    p = json.loads(json.dumps(p))
    audio_files = []
    if args.audio_manifest:
        audio_files = load_audio_manifest(args.audio_manifest, p["scenes"])
        for scene, path in zip(p["scenes"], audio_files):
            scene["duration"] = media.audio_duration(path) + .35
        project.validate(p)
    if args.max_seconds is not None:
        if not 1 <= args.max_seconds <= 1800:
            raise ValueError("--max-seconds must be between 1 and 1800")
        if audio_files:
            raise ValueError("--max-seconds is for silent CI smoke tests only")
        remaining = args.max_seconds
        selected = []
        for scene in p["scenes"]:
            if remaining <= 0: break
            scene["duration"] = min(scene["duration"], remaining)
            selected.append(scene)
            remaining -= scene["duration"]
        p["scenes"] = selected
    scenes = project.timeline(p, args.fps)
    project.write_package(p, scenes, args.fps, out)
    (out / "resolved-project.json").write_text(json.dumps(p, indent=2))
    video_dir, audio_dir = out / "video", out / "audio-normalized"
    video_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)
    implementation = b"".join(Path(__file__).with_name(n).read_bytes() for n in ("render.py", "project.py", "cli.py"))
    implementation_hash = hashlib.sha256(implementation).hexdigest()
    scene_times, contacts = [], []
    for i, scene in enumerate(scenes):
        begin = time.perf_counter()
        path = video_dir / f"{i:03}.mp4"
        stamp = video_dir / f"{i:03}.json"
        key = hashlib.sha256(json.dumps({"scene": scene, "width": args.width, "fps": args.fps,
                                        "silent": args.silent_preview, "code": implementation_hash,
                                        "font": str(render.font(30).path) if hasattr(render.font(30),"path") else "default"},
                                       sort_keys=True).encode()).hexdigest()
        cached = path.is_file() and stamp.is_file() and json.loads(stamp.read_text()).get("key") == key
        if not cached:
            temporary = video_dir / f"{i:03}.partial.mp4"
            command = [media.require_tool("ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{args.width}x{height}", "-r", str(args.fps), "-i", "pipe:0", "-an",
                       "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-threads", "2", "-movflags", "+faststart", str(temporary)]
            with open(video_dir / f"{i:03}.encode.log", "wb") as log:
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
                try:
                    for frame_idx in range(scene["frames"]):
                        im = render.frame(scene, frame_idx / args.fps, args.width, height, args.silent_preview)
                        proc.stdin.write(im.tobytes())
                    proc.stdin.close()
                    if proc.wait() != 0:
                        raise RuntimeError(f"Scene {i} encoding failed; inspect its encode.log")
                except BaseException:
                    if proc.stdin and not proc.stdin.closed: proc.stdin.close()
                    if proc.poll() is None: proc.kill()
                    proc.wait()
                    temporary.unlink(missing_ok=True)
                    raise
            temporary.replace(path)
            stamp.write_text(json.dumps({"key": key, "frames": scene["frames"]}))
        if audio_files:
            seconds = scene["frames"] / args.fps
            media.run([media.require_tool("ffmpeg"), "-v", "error", "-y", "-i", audio_files[i], "-af",
                       f"aresample=24000,apad,atrim=duration={seconds}", "-ac", "1", "-c:a", "pcm_s16le",
                       audio_dir / f"{i:03}.wav"])
        contacts.append(render.frame(scene, scene["duration"]*.55, 640, 360, args.silent_preview))
        scene_times.append({"id": scene["id"], "frames": scene["frames"], "cache_hit": cached,
                            "render_seconds": round(time.perf_counter()-begin, 3)})
        print(f"Scene {i+1}/{len(scenes)}: {scene['id']} ({'cached' if cached else 'rendered'})", flush=True)
    manifest = out / "video-concat.txt"
    manifest.write_text("\n".join(f"file 'video/{i:03}.mp4'" for i in range(len(scenes))))
    silent_video = out / "animation.mp4"
    media.run([media.require_tool("ffmpeg"), "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", manifest,
               "-c", "copy", silent_video])
    if audio_files:
        am = out / "audio-concat.txt"
        am.write_text("\n".join(f"file 'audio-normalized/{i:03}.wav'" for i in range(len(scenes))))
        voice = out / "narration.wav"
        media.run([media.require_tool("ffmpeg"), "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", am,
                   "-c:a", "pcm_s16le", voice])
        media.run([media.require_tool("ffmpeg"), "-v", "error", "-y", "-i", silent_video, "-i", voice,
                   "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                   "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-movflags", "+faststart", out / "final.mp4"])
    else:
        shutil.copyfile(silent_video, out / "final.mp4")
    sheet = Image.new("RGB", (1280, ((len(contacts)+1)//2)*400), "#101a2c")
    sd = ImageDraw.Draw(sheet)
    for i, im in enumerate(contacts):
        x,y=i%2*640,i//2*400
        sheet.paste(im,(x,y))
        sd.text((x+20,y+370),scenes[i]["id"],font=render.font(18),fill="white")
    sheet.save(out / "contact-sheet.jpg", quality=90)
    contacts[0].save(out / "thumbnail-preview.jpg", quality=95)
    metadata = media.probe(out / "final.mp4")
    expected = sum(s["frames"] for s in scenes) / args.fps
    actual = float(metadata["format"]["duration"])
    if abs(actual-expected) > max(.15, 2/args.fps):
        raise RuntimeError(f"Duration mismatch: expected {expected}, got {actual}")
    has_audio = any(s["codec_type"]=="audio" for s in metadata["streams"])
    if bool(audio_files) != has_audio:
        raise RuntimeError("Audio stream presence does not match requested mode")
    report = {"status": "passed technical checks; artistic and voice review still required",
              "width": args.width, "height": height, "fps": args.fps,
              "expected_seconds": expected, "actual_seconds": actual,
              "wall_seconds": round(time.perf_counter()-started, 3),
              "voice_status": "external narration supplied" if audio_files else "NO NARRATION — silent development preview",
              "caption_alignment": "estimated phrase timing within audio-sized scenes",
              "scenes": scene_times, "checks": ["decode metadata", "duration", "audio stream presence"],
              "not_checked": ["speaker similarity", "ASR text fidelity", "word alignment", "factual accuracy", "reference quality parity"]}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!="scenes"}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Stickman development prototype")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("render")
    p.add_argument("project"); p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=1280); p.add_argument("--fps", type=int, default=30)
    p.add_argument("--silent-preview", action="store_true"); p.add_argument("--audio-manifest")
    p.add_argument("--max-seconds", type=float)
    p = sub.add_parser("prepare-reference")
    p.add_argument("source"); p.add_argument("destination")
    p.add_argument("--start", type=float, default=0); p.add_argument("--seconds", type=float, default=12)
    p = sub.add_parser("enroll")
    p.add_argument("reference"); p.add_argument("--profile", required=True)
    p.add_argument("--variant", choices=["nano", "turbo"], default="nano")
    p.add_argument("--device", default="cpu"); p.add_argument("--model-dir")
    p = sub.add_parser("speak")
    p.add_argument("project")
    voices = p.add_mutually_exclusive_group(required=True)
    voices.add_argument("--profile")
    voices.add_argument("--cast-profiles", help="Private JSON mapping voice IDs to profile directories")
    p.add_argument("--out", required=True)
    p.add_argument("--device", default="cpu"); p.add_argument("--model-dir")
    p = sub.add_parser("plan")
    p.add_argument("--title", required=True); p.add_argument("--minutes", type=float, default=10)
    p.add_argument("--endpoint", required=True); p.add_argument("--model", required=True)
    p.add_argument("--notes"); p.add_argument("--out", required=True)
    p = sub.add_parser("produce", help="Configured endpoint + private voice profile → video package")
    p.add_argument("--title", required=True); p.add_argument("--minutes", type=float, default=10)
    p.add_argument("--endpoint", required=True); p.add_argument("--model", required=True)
    p.add_argument("--notes"); p.add_argument("--out", required=True); p.add_argument("--profile", required=True)
    p.add_argument("--device", default="cpu"); p.add_argument("--model-dir")
    p.add_argument("--width", type=int, default=1280); p.add_argument("--fps", type=int, default=30)
    p = sub.add_parser("generate", help="Title + description -> generated cast script -> voiced video")
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--minutes", type=float, default=1)
    p.add_argument("--voices", default="female,male1,male2")
    p.add_argument("--cast-profiles", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model-dir")
    p.add_argument("--writer-model-dir")
    p.add_argument("--asr-model-dir", default="models/asr-base-en")
    p.add_argument("--resume", action="store_true", help="Reuse completed writing only when request and model revision match")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()
    if args.command == "generate":
        from .generate import generate
        generate(args)
    elif args.command == "render": render_project(args)
    elif args.command == "prepare-reference":
        media.prepare_reference(args.source, args.destination, args.start, args.seconds)
        print("Prepared reference excerpt; no source file was deleted")
    elif args.command == "enroll":
        from .voice import enroll
        enroll(args.reference, args.profile, args.variant, args.device, args.model_dir)
        print("Private profile enrolled; listening validation is still required")
    elif args.command == "speak":
        from .voice import synthesize_scenes
        loaded = project.load(args.project)
        if args.cast_profiles:
            from .voice import synthesize_cast
            mapping_path = Path(args.cast_profiles).resolve()
            mapping = json.loads(mapping_path.read_text())
            if not isinstance(mapping, dict) or not all(isinstance(v, str) for v in mapping.values()):
                raise ValueError("Cast profiles JSON must map voice IDs to profile directory strings")
            mapping = {k: str(mapping_path.parent / v) for k, v in mapping.items()}
            synthesize_cast(loaded, mapping, args.out, args.device, args.model_dir)
        elif loaded.get("cast"):
            raise ValueError("Cast projects require --cast-profiles; no single-voice substitution")
        else:
            synthesize_scenes(loaded, args.profile, args.out, args.device, args.model_dir)
    elif args.command in {"plan", "produce"}:
        from .planner import plan
        notes = Path(args.notes).read_text() if args.notes else ""
        result = plan(args.title, args.minutes, args.endpoint, args.model, notes)
        dest = Path(args.out) if args.command == "plan" else Path(args.out) / "project.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if args.command == "produce":
            from .voice import synthesize_scenes
            speech = Path(args.out).resolve() / "speech"
            synthesize_scenes(result, args.profile, speech, args.device, args.model_dir)
            render_project(argparse.Namespace(project=str(dest), out=str(Path(args.out)/"render"),
                           width=args.width, fps=args.fps, silent_preview=False,
                           audio_manifest=str(speech/"manifest.json"), max_seconds=None))


if __name__ == "__main__":
    main()
