import hashlib
import hmac
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.writer import parse_story, compile_project
from studio.ci import restore_profiles
from studio import project, render

class WriterTests(unittest.TestCase):
    def test_asr_check_detects_dropped_words(self):
        from studio.speech_check import word_error_rate
        self.assertEqual(word_error_rate("The cup floats.", "the cup floats"), 0)
        self.assertGreater(word_error_rate("The little cup floats above the table.", "the cup"), .35)

    def test_selected_cast_and_motion_compile_to_valid_renderable_scenes(self):
        for voices in (['female'], ['male1', 'male2'], ['female', 'male1', 'male2']):
            beats=[{'speaker':v,'text':'The little cup started floating above the table.',
                    'location':'room','action':'point','shot':'close','prop':'cup','movement':'enter'} for v in voices]
            story=parse_story('```json\n'+json.dumps({'beats':beats})+'\n```',voices)
            p=compile_project(story,'A floating cup','Fictional test',voices)
            self.assertEqual([m['voice'] for m in p['cast']],voices)
            for s in project.timeline(p,24):
                first=render.frame(s,.4,320,180,False)
                last=render.frame(s,1.4,320,180,False)
                self.assertNotEqual(first.tobytes(),last.tobytes())
    def test_writer_rejects_unknown_missing_and_empty_speech(self):
        for beats in ([{'speaker':'other','text':'The cup floats away.'}],
                      [{'speaker':'female','text':''}],
                      [{'speaker':'female','text':'The cup floats away.'}]):
            with self.assertRaises(ValueError):
                parse_story(json.dumps({'beats':beats}),['female','male1'])
    def test_scene_motion_is_validated(self):
        story={'beats':[{'speaker':'female','text':'The cup floats away.'}]}
        p=compile_project(story,'Title','Description',['female'])
        p['scenes'][0]['movement']='execute_code'
        with self.assertRaises(ValueError): project.validate(p)

@unittest.skipUnless(__import__('shutil').which('openssl'), 'Needs OpenSSL')
class PrivateArchiveTests(unittest.TestCase):
    def test_authenticated_roundtrip_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'source'; source.mkdir()
            files=['cast-profiles.json']+[f'profiles/{s}/{name}' for s in ('female','male1-kit-laser','male2-warguy') for name in ('conditioning.pt','profile.json')]
            for file in files:
                p=source/file;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
            with tarfile.open(root/'clear.tar.gz','w:gz') as tar:
                for file in files: tar.add(source/file,arcname=file)
            key='synthetic-test-key-not-a-real-secret'
            (root/'key').write_text(key+'\n')
            subprocess.run(['openssl','enc','-aes-256-cbc','-salt','-pbkdf2','-iter','200000',
                            '-in',str(root/'clear.tar.gz'),'-out',str(root/'cipher'),'-pass','file:'+str(root/'key')],check=True)
            signing=hashlib.sha256(b'stickman-profile-auth-v1:'+key.encode()).digest()
            (root/'signature').write_text(hmac.new(signing,(root/'cipher').read_bytes(),hashlib.sha256).hexdigest())
            restore_profiles(root/'cipher',root/'signature',root/'restored',key)
            self.assertEqual((root/'restored/profiles/female/conditioning.pt').read_bytes(),b'fixture')
            (root/'cipher').write_bytes((root/'cipher').read_bytes()+b'tamper')
            with self.assertRaises(ValueError): restore_profiles(root/'cipher',root/'signature',root/'rejected',key)
            self.assertFalse((root/'rejected').exists())
