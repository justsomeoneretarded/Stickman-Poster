import copy
import json
import tempfile
import unittest
import shutil
import subprocess
import sys
from pathlib import Path

from studio import project, render
from studio.cli import load_audio_manifest

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.project = project.load(ROOT / "examples/gravity.json")

    def test_timeline_has_no_drift_or_overlap(self):
        self.project["scenes"][0]["duration"] = 5.019
        scenes = project.timeline(self.project, 30)
        for a,b in zip(scenes, scenes[1:]):
            self.assertEqual(a["start_frame"]+a["frames"],b["start_frame"])
        self.assertEqual(scenes[-1]["start_frame"]+scenes[-1]["frames"],sum(s["frames"] for s in scenes))

    def test_rejects_unknown_scene_actions(self):
        self.project["scenes"][0]["action"] = "execute_python"
        with self.assertRaises(ValueError): project.validate(self.project)

    def test_rejects_nonfinite_duration(self):
        for bad in [float("nan"),float("inf"),True,-1]:
            p=copy.deepcopy(self.project);p["scenes"][0]["duration"]=bad
            with self.assertRaises(ValueError): project.validate(p)

    def test_rejects_duplicate_ids(self):
        self.project["scenes"][1]["id"] = self.project["scenes"][0]["id"]
        with self.assertRaises(ValueError): project.validate(self.project)

    def test_rejects_invalid_zoom(self):
        self.project["scenes"][0]["camera_zoom"] = 5
        with self.assertRaises(ValueError): project.validate(self.project)

    def test_srt_rounding_carries_seconds(self):
        self.assertEqual(project.srt_time(59.9996),"00:01:00,000")

    def test_captions_stay_inside_scene(self):
        for s in project.timeline(self.project,30):
            cues=project.caption_cues(s,30)
            self.assertEqual(cues[0][0],s["start_frame"]/30)
            self.assertAlmostEqual(cues[-1][1],(s["start_frame"]+s["frames"])/30)
            self.assertTrue(all(b>a for a,b,_ in cues))

    def test_rejects_manifest_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"private").mkdir();(root/"outside.wav").write_bytes(b"x")
            p=root/"private/manifest.json"
            p.write_text(json.dumps({"entries":[{"scene_id":"opening","file":"../outside.wav"}]}))
            with self.assertRaises(ValueError): load_audio_manifest(p,self.project["scenes"][:1])

    def test_rejects_missing_audio_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"manifest.json";p.write_text('{"entries":[]}')
            with self.assertRaises(ValueError): load_audio_manifest(p,self.project["scenes"])

    def test_speech_chunking_preserves_all_words(self):
        from studio.voice import speech_chunks
        text="A short opening. " + " ".join(["continuity"]*90) + ". A final thought."
        chunks=speech_chunks(text)
        self.assertEqual(" ".join(chunks),text)
        self.assertTrue(all(len(c)<=220 for c in chunks))


class RenderTests(unittest.TestCase):
    def test_every_example_scene_renders(self):
        p=project.load(ROOT/"examples/gravity.json")
        for scene in p["scenes"]:
            im=render.frame(scene,1.0,640,360)
            self.assertEqual(im.size,(640,360))
            self.assertEqual(im.mode,"RGB")
            self.assertIsNotNone(im.getbbox())

    def test_render_is_reproducible_at_absolute_time(self):
        scene=project.load(ROOT/"examples/gravity.json")["scenes"][1]
        a=render.frame(scene,1.3,640,360).tobytes()
        render.frame(scene,2.1,640,360)
        b=render.frame(scene,1.3,640,360).tobytes()
        self.assertEqual(a,b)
        self.assertNotEqual(a,render.frame(scene,1.8,640,360).tobytes())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg integration requires tools")
class MediaIntegrationTests(unittest.TestCase):
    def test_audio_drives_runtime_and_cache_is_reused(self):
        from studio.media import probe
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            p=project.load(ROOT/"examples/gravity.json")
            p["scenes"]=p["scenes"][:2]
            (root/"project.json").write_text(json.dumps(p))
            audio=root/"audio";audio.mkdir()
            entries=[]
            for i,s in enumerate(p["scenes"]):
                subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"sine=frequency=440:duration={.8+i*.2}",
                                "-ar","24000",str(audio/f"{i}.wav")],check=True)
                entries.append({"scene_id":s["id"],"file":f"{i}.wav"})
            (audio/"manifest.json").write_text(json.dumps({"entries":entries}))
            command=[sys.executable,"-m","studio.cli","render",str(root/"project.json"),"--out",str(root/"render"),
                     "--width","320","--fps","6","--audio-manifest",str(audio/"manifest.json")]
            subprocess.run(command,check=True,capture_output=True)
            report=json.loads((root/"render/report.json").read_text())
            self.assertLess(report["actual_seconds"],3)
            self.assertTrue(any(s["codec_type"]=="audio" for s in probe(root/"render/final.mp4")["streams"]))
            subprocess.run(command,check=True,capture_output=True)
            report=json.loads((root/"render/report.json").read_text())
            self.assertTrue(all(s["cache_hit"] for s in report["scenes"]))

    def test_missing_clone_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            result=subprocess.run([sys.executable,"-m","studio.cli","render",str(ROOT/"examples/gravity.json"),
                                   "--out",directory,"--width","320","--fps","6"],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("No substitute voice",result.stderr)


if __name__=="__main__": unittest.main()
