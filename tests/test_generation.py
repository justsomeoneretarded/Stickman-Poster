import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.writer import parse_story, compile_project
from studio import project, render

class WriterTests(unittest.TestCase):
    def test_spoken_text_rejects_stage_directions_but_accepts_dialogue(self):
        from studio.writer import validate_spoken_style
        for text in ("Leo runs forward, saying hello.","Maya: Hello everyone.","'Max looks at the bag.'"):
            with self.assertRaises(ValueError):validate_spoken_style({'beats':[{'text':text}]})
        validate_spoken_style({'beats':[{'text':"Maya, please take the bag. I am giving it back."}]})

    def test_structured_word_arrays_form_spoken_dialogue(self):
        story=parse_story('{"beats":[{"speaker":"female","words":["Please,","take","the","bag."]}]}',['female'])
        self.assertEqual(story['beats'][0]['text'],'Please, take the bag.')
        with self.assertRaises(ValueError):
            parse_story('{"beats":[{"speaker":"female","words":["two words","in","one"]}]}',['female'])

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

class PublicProfileTests(unittest.TestCase):
    def test_all_published_profiles_match_checksums_and_source_version(self):
        from studio.voice import SOURCE_COMMIT, sha256
        root = Path(__file__).resolve().parents[1] / 'voices'
        mapping = json.loads((root/'cast-profiles.json').read_text())
        self.assertEqual(set(mapping), {'female', 'male1', 'male2'})
        for relative in mapping.values():
            profile = (root/relative).resolve()
            self.assertIn(root, profile.parents)
            metadata = json.loads((profile/'profile.json').read_text())
            self.assertEqual(metadata['visibility'], 'public')
            self.assertEqual(metadata['source_commit'], SOURCE_COMMIT)
            self.assertEqual(metadata['conditioning_sha256'], sha256(profile/'conditioning.pt'))
