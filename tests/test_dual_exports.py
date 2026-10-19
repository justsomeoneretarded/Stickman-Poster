"""Encoded packaging integration with explicit synthetic audio fixtures, not voice qualification."""
import argparse
import json
import math
import struct
import tempfile
import unittest
import wave
from PIL import Image
from pathlib import Path
from studio.generate import generate
from studio.media import probe
from studio.writer import compile_project


class DualExportTests(unittest.TestCase):
    def test_render_stage_delivers_two_native_aspects_with_independent_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            request={'screen_text':'minimal','short_seconds':30,'title':'Flying test','description':'A synthetic integration fixture.',
                     'minutes':1,'voices':['female']}
            (root/'request.json').write_text(json.dumps(request))
            for folder,text in ((root,'I can fly over the city.'),(root/'short','Look, no traffic today.')):
                writing=folder/'writing';speech=folder/'speech'
                writing.mkdir(parents=True);speech.mkdir()
                p=compile_project({'visual_style':'expressive-v2','beats':[{'speaker':'female','location':'rooftop',
                    'staging':'fly','text':text,'comic_role':'hook'}]},request['title'],request['description'],['female'])
                (writing/'project.json').write_text(json.dumps(p))
                (writing/'writer-report.json').write_text('{"fixture":true}')
                (writing/'highlight-selection.json').write_text('{"fixture":true}')
                (speech/'speech-check.json').write_text('{"synthetic_test_fixture":true}')
                with wave.open(str(speech/'fixture.wav'),'wb') as audio:
                    audio.setparams((1,2,24000,24000,'NONE','not compressed'));audio.writeframes(b''.join(struct.pack('<h',int(1200*math.sin(2*math.pi*440*i/24000))) for i in range(24000)))
                (speech/'manifest.json').write_text(json.dumps({'entries':[{'scene_id':'beat-001','file':'fixture.wav'}]}))
            generate(argparse.Namespace(title=request['title'],description=request['description'],minutes=1,
                     voices='female',cast_profiles=str(Path('voices/cast-profiles.json').resolve()),out=str(root),
                     short_seconds=30,width=320,fps=1,required_locations='',revise_project=None,resume=False,
                     writer_model_dir=None,model_dir=None,asr_model_dir=None,stage='render'))
            for variant,dimensions in (('long-form',(320,180)),('short-form',(720,1280))):
                export=root/'deliverables'/variant
                metadata=probe(export/'final.mp4')
                video=next(s for s in metadata['streams'] if s['codec_type']=='video')
                self.assertEqual((video['width'],video['height']),dimensions)
                self.assertTrue(any(s['codec_type']=='audio' for s in metadata['streams']))
                self.assertTrue((export/'captions.srt').exists())
                with Image.open(export/'thumbnail-preview.jpg') as thumb:
                    self.assertEqual(thumb.height>thumb.width,variant=='short-form')
            self.assertNotEqual((root/'deliverables/long-form/script.txt').read_text(),
                                (root/'deliverables/short-form/script.txt').read_text())
