import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio import project, render
from studio.voice import synthesize_cast

ROOT=Path(__file__).resolve().parents[1]
class CastTests(unittest.TestCase):
    def setUp(self):
        self.p=project.load(ROOT/'examples/three-friends.json')
    def test_one_two_or_three_characters(self):
        for count in (1,2,3):
            p=copy.deepcopy(self.p)
            p['cast']=p['cast'][:count]
            p['scenes']=p['scenes'][:count]
            for s in p['scenes']: s['characters']=[m['id'] for m in p['cast']]
            project.validate(p)
            for s in project.timeline(p,24):
                self.assertEqual(render.frame(s,1,320,180,False).size,(320,180))
    def test_unknown_or_hidden_speaker_rejected(self):
        for speaker in ('unknown','leo'):
            p=copy.deepcopy(self.p)
            p['scenes'][0].update(speaker=speaker,characters=['maya'])
            with self.assertRaises(ValueError): project.validate(p)
    def test_routes_profiles_and_preserves_turn_order(self):
        self.p['scenes'].append({**self.p['scenes'][0],'id':'maya-again'})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            profiles={}
            for member in self.p['cast']:
                path=root/member['voice'];path.mkdir()
                (path/'profile.json').write_text('{}');(path/'conditioning.pt').write_bytes(b'test')
                profiles[member['voice']]=str(path)
            def fake(p,profile,out,device,model_dir):
                Path(out).mkdir(parents=True)
                return {'entries':[{'scene_id':s['id'],'file':f'{i:03}.wav'} for i,s in enumerate(p['scenes'])]}
            with patch('studio.voice.synthesize_scenes',side_effect=fake) as mocked:
                manifest=synthesize_cast(self.p,profiles,root/'out')
                self.assertEqual(mocked.call_count,3)
                self.assertEqual([c.args[1] for c in mocked.call_args_list],list(profiles.values()))
                self.assertEqual([e['speaker'] for e in manifest['entries']],['maya','leo','max','maya'])
                self.assertEqual(manifest['entries'][-1]['file'],'voice-00/001.wav')
            with patch('studio.voice.synthesize_scenes') as mocked:
                with self.assertRaises(ValueError): synthesize_cast(self.p,{},root/'missing')
                mocked.assert_not_called()
