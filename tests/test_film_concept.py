import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio.film_concept import make_request,write_package,generate,validate_film,schedule_scenes

ROOT=Path(__file__).resolve().parents[1]


class FilmConceptTests(unittest.TestCase):
    def setUp(self):
        self.film=json.loads((ROOT/'films/am-i-invisible/film.json').read_text())

    def test_first_film_has_real_frame_budget_within_soft_three_minute_range(self):
        r=make_request('Am I Invisible?','Quiet emotional film.',3)
        with tempfile.TemporaryDirectory() as d:
            spec=write_package(self.film,r,d,{'type':'test_fixture'})
            self.assertEqual(spec['long_form']['planned_frames'],5040)
            self.assertEqual(spec['long_form']['fps'],24)
            self.assertTrue(spec['duration']['in_preferred_range'])
            self.assertFalse(spec['duration']['strict'])
            self.assertIsNone(spec['long_form']['measured_rendered_frames'])
            self.assertEqual(spec['render_status'],'not_rendered')
            for name in ('story.txt','script.md','description.txt','keywords.txt','publishing.json','short-edit.md'):
                self.assertTrue((Path(d)/name).read_text().strip())

    def test_short_duration_is_not_stretched_to_an_arbitrary_frame_floor(self):
        r=make_request('Brief film','Visual story.',1,'4K')
        film=copy.deepcopy(self.film)
        for s in film['scenes']:s['seconds']=2;s.pop('frames',None)
        with tempfile.TemporaryDirectory() as d:
            spec=write_package(film,r,d,{'type':'test_fixture'})
            self.assertEqual(spec['long_form']['planned_frames'],432)
            self.assertEqual((spec['long_form']['width'],spec['long_form']['height']),(3840,2160))
            self.assertEqual((spec['short_form']['width'],spec['short_form']['height']),(2160,3840))
            self.assertFalse(spec['duration']['in_preferred_range'])
            self.assertTrue(json.loads((Path(d)/'review.json').read_text())['warnings'])
            saved=json.loads((Path(d)/'film.json').read_text())
            self.assertEqual(schedule_scenes(saved),saved)

    def test_five_minutes_is_7200_frames_with_no_artificial_floor(self):
        film=copy.deepcopy(self.film)
        film['scenes']=film['scenes'][:5]
        for scene in film['scenes']:scene['seconds']=60
        planned=schedule_scenes(film)
        self.assertEqual(sum(s['frames'] for s in planned['scenes']),7200)
        self.assertEqual(sum(s['seconds'] for s in planned['scenes']),300)

    def test_long_story_is_not_rejected_and_silence_is_valid(self):
        r=make_request('Slow cinema','Silence and rain.',3)
        film=copy.deepcopy(self.film)
        for s in film['scenes']:s['seconds']=100;s['dialogue']=[];s.pop('frames',None)
        with tempfile.TemporaryDirectory() as d:
            spec=write_package(film,r,d,{'type':'test_fixture'})
            self.assertGreater(spec['duration']['planned_seconds'],225)
            self.assertFalse(spec['duration']['in_preferred_range'])
            self.assertIn('No dialogue',(Path(d)/'script.md').read_text())

    def test_invalid_cast_and_dangling_edit_references_are_rejected(self):
        r=make_request('Title','Description',3,voices='female')
        with self.assertRaisesRegex(ValueError,'selected voices'):validate_film(self.film,r)
        film=copy.deepcopy(self.film);film['short_edit']['scene_ids']=['missing']
        with self.assertRaisesRegex(ValueError,'unknown scenes'):
            validate_film(film,make_request('Title','Description',3))

    def test_new_inputs_reach_model_and_cache_preserves_generated_story(self):
        film=self.film
        class Writer:
            calls=0
            def __init__(self,*a,**kw):pass
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def complete(self,messages,schema,tokens):
                Writer.calls+=1
                user=json.loads(messages[1]['content'])
                self_test.assertEqual(user['title'],'A completely different film')
                self_test.assertEqual(user['resolution'],'4K')
                self_test.assertIn('Empty dialogue arrays are valid',messages[0]['content'])
                return json.dumps(film)
        self_test=self
        with tempfile.TemporaryDirectory() as d,patch('studio.local_llm.LocalWriter',Writer):
            r=make_request('A completely different film','A custom quiet idea.',4,'4K')
            generate(r,d,None);generate(r,d,None)
            self.assertEqual(Writer.calls,1)
            self.assertEqual(json.loads((Path(d)/'publishing.json').read_text())['title'],r['title'])
