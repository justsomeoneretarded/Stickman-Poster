import json
import shutil
import subprocess
from pathlib import Path


def require_tool(name):
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"{name} is required and must be on PATH")
    return result


def run(args):
    subprocess.run([str(a) for a in args], check=True)


def probe(path):
    result = subprocess.run([require_tool("ffprobe"), "-v", "error", "-show_streams",
                             "-show_format", "-of", "json", str(path)],
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def audio_duration(path):
    info = probe(path)
    if not any(s["codec_type"] == "audio" for s in info["streams"]):
        raise ValueError("Expected an audio stream")
    return float(info["format"]["duration"])


def prepare_reference(source, dest, start=0, seconds=12):
    if not 6 <= seconds <= 30 or start < 0:
        raise ValueError("Choose a 6–30 second excerpt and nonnegative start")
    if audio_duration(source) < start + seconds:
        raise ValueError("The requested excerpt extends beyond the audio")
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    # No pitch change, denoising or music removal that could distort identity.
    run([require_tool("ffmpeg"), "-v", "error", "-y", "-ss", start,
         "-i", source, "-t", seconds, "-vn", "-ac", "1", "-ar", "24000", dest])
    return probe(dest)
