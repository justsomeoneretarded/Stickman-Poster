"""Validated declarative scenes; arbitrary model-generated code is never executed."""
import json
import math
from pathlib import Path

LOCATIONS = {"room", "street", "diagram", "stage"}
ACTIONS = {"idle", "point", "walk", "float", "think", "worried", "celebrate"}


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(project):
    if not isinstance(project, dict):
        raise ValueError("Project must be an object")
    if project.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(project.get("title"), str) or not project["title"].strip():
        raise ValueError("A nonempty title is required")
    if not isinstance(project.get("description", ""), str):
        raise ValueError("description must be text")
    keywords = project.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(x, str) for x in keywords):
        raise ValueError("keywords must be a list of strings")
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 180:
        raise ValueError("Expected 1–180 scenes")
    cast = project.get("cast", [])
    if not isinstance(cast, list) or len(cast) > 3:
        raise ValueError("cast must contain at most three characters")
    cast_ids = set()
    for member in cast:
        if not isinstance(member, dict) or not all(isinstance(member.get(k), str) and member[k].strip() for k in ("id", "name", "voice")):
            raise ValueError("Cast members require id, name, and voice")
        if member["id"] in cast_ids or len(member["name"]) > 24:
            raise ValueError("Cast IDs must be unique and names at most 24 characters")
        cast_ids.add(member["id"])
    ids = set()
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Every scene must be an object")
        sid = scene.get("id")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("Scene IDs must be unique nonempty strings")
        ids.add(sid)
        if cast:
            visible = scene.get("characters", [m["id"] for m in cast])
            if not isinstance(visible, list) or not 1 <= len(visible) <= 3 or not all(isinstance(x, str) and x in cast_ids for x in visible) or len(set(visible)) != len(visible):
                raise ValueError("Scene characters must reference one to three distinct cast IDs")
            if scene.get("speaker") not in visible:
                raise ValueError("Every cast scene needs a visible speaker")
        elif "speaker" in scene or "characters" in scene:
            raise ValueError("Speaker and characters require a cast")
        if scene.get("location") not in LOCATIONS:
            raise ValueError(f"Unknown location in {sid}")
        if scene.get("action") not in ACTIONS:
            raise ValueError(f"Unknown action in {sid}")
        if not finite_number(scene.get("duration")) or not 1 <= scene["duration"] <= 45:
            raise ValueError(f"Invalid duration in {sid}")
        for field in ("narration", "heading", "label"):
            if not isinstance(scene.get(field, ""), str):
                raise ValueError(f"{field} must be text")
        if len(scene.get("narration", "")) > 1500:
            raise ValueError("Split long narration into shorter scenes")
        if len(scene.get("heading", "")) > 72 or len(scene.get("label", "")) > 90:
            raise ValueError("Headings and labels must fit the layout")
        for field, allowed in (("shot", {"wide", "medium", "close"}),
                               ("prop", {"none", "cup", "phone", "orb"}),
                               ("movement", {"stay", "enter", "cross", "approach"})):
            if field in scene and scene[field] not in allowed:
                raise ValueError(f"Unsupported {field} in {sid}")
        for flag in ("secondary", "levitate", "cinematic"):
            if flag in scene and not isinstance(scene[flag], bool):
                raise ValueError(f"{flag} must be boolean")
        if "camera_zoom" in scene and (not finite_number(scene["camera_zoom"]) or not 1 <= scene["camera_zoom"] <= 1.12):
            raise ValueError("Camera zoom must be between 1 and 1.12")
    if sum(s["duration"] for s in scenes) > 1800:
        raise ValueError("Project exceeds the prototype's 30 minute limit")
    return project


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def timeline(project, fps):
    if not isinstance(fps, int) or not 1 <= fps <= 60:
        raise ValueError("fps must be an integer from 1 to 60")
    result, cursor = [], 0
    for scene in project["scenes"]:
        frames = max(1, round(scene["duration"] * fps))
        resolved = dict(scene)
        if project.get("cast"):
            visible = scene.get("characters", [m["id"] for m in project["cast"]])
            resolved["cast_members"] = [m for m in project["cast"] if m["id"] in visible]
        result.append({**resolved, "start_frame": cursor, "frames": frames})
        cursor += frames
    return result


def srt_time(seconds):
    milliseconds = round(seconds * 1000)
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def caption_chunks(text):
    words = text.split()
    if not words:
        return []
    # Balance chunks to avoid a one-word final caption.
    count = math.ceil(len(words) / 10)
    size = math.ceil(len(words) / count)
    return [words[i:i+size] for i in range(0, len(words), size)]


def caption_cues(scene, fps):
    """Estimated phrase timing; exact scene boundaries follow measured speech.

    Deliberately not described as forced word alignment. Alignment is a future
    adapter; phrase estimates must be reviewed against actual synthesized speech.
    """
    words = scene.get("narration", "").split()
    chunks = caption_chunks(scene.get("narration", ""))
    start = scene["start_frame"] / fps
    duration = scene["frames"] / fps
    cursor, result = 0, []
    for chunk in chunks:
        end = cursor + len(chunk)
        result.append((start + duration * cursor / len(words),
                       start + duration * end / len(words), " ".join(chunk)))
        cursor = end
    return result


def write_package(project, scenes, fps, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cues = [c for s in scenes for c in caption_cues(s, fps)]
    srt = "\n\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}"
                          for i, (a, b, text) in enumerate(cues, 1))
    (out / "captions.srt").write_text(srt + "\n", encoding="utf-8")
    names = {m["id"]: m["name"] for m in project.get("cast", [])}
    lines = [(names[s["speaker"]] + ": " if s.get("speaker") in names else "") + s["narration"] for s in scenes]
    (out / "script.txt").write_text("\n\n".join(lines), encoding="utf-8")
    chapters = []
    for scene in scenes:
        sec = int(scene["start_frame"] / fps)
        chapters.append(f"{sec // 60:02}:{sec % 60:02} {scene.get('heading', scene['id'])}")
    package = {"title": project["title"], "description": project.get("description", ""),
               "keywords": project.get("keywords", []), "chapter_candidates": chapters,
               "status": "development preview; review before publishing",
               "caption_timing": "estimated phrases, not forced alignment",
               "chapters_note": "Candidates may be too short for YouTube chapters; review platform requirements."}
    (out / "posting.json").write_text(json.dumps(package, indent=2), encoding="utf-8")
