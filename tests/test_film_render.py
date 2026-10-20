import subprocess
import tempfile
import unittest
from pathlib import Path
from studio.film_render import inspect_video
from studio.media import require_tool


class FilmRenderTests(unittest.TestCase):
    def test_delivered_frames_are_counted_at_24fps_not_assumed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'clip.mp4'
            subprocess.run([require_tool('ffmpeg'),'-v','error','-y','-f','lavfi','-i',
                'color=c=gray:size=64x64:rate=24','-frames:v','48','-c:v','libx264',str(path)],check=True)
            receipt=inspect_video(path,48)
            self.assertEqual(receipt['decoded_frames'],48)
            self.assertEqual(receipt['seconds'],2)
            with self.assertRaisesRegex(ValueError,'differs'):inspect_video(path,49)

    def test_wrong_framerate_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'clip.mp4'
            subprocess.run([require_tool('ffmpeg'),'-v','error','-y','-f','lavfi','-i',
                'color=c=gray:size=64x64:rate=25','-frames:v','25','-c:v','libx264',str(path)],check=True)
            with self.assertRaisesRegex(ValueError,'24 FPS'):inspect_video(path)
