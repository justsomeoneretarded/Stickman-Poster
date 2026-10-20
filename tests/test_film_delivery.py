import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio.film_concept import make_request,write_package,validate_film,schema
from studio.film_thumbnails import generate_thumbnails

ROOT=Path(__file__).resolve().parents[1]

class FilmDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.film=json.loads((ROOT/'films/am-i-invisible/film.json').read_text())
        self.film['scenes']=self.film['scenes'][:2]
        self.film['short_edit']['scene_ids']=['01','02']
        for scene in self.film['scenes']:
            scene['actors']=['Maya'];scene['dialogue']=[];scene['cues']=[];scene['screen_text']=[]
        self.film['thumbnails']=[{'source_scene_id':'01','image_prompt':f'Original composition {i}',
           'hook_text':'AM I INVISIBLE?','composition':str(i),'emotional_promise':'Feeling unseen'} for i in range(3)]
        self.request=make_request('A quiet film','A girl feels lonely.',5,voices='male1',characters='Maya (female)',fps=12)

    def cue(self,**kw):
        return dict(kind='speech',start_seconds=2,end_seconds=4,detail='A distant call',reason='She thinks she is recognized',
                    caption='',speaker='Leo',text='Over here.',offscreen=True,**kw)

    def test_offscreen_voice_is_independent_of_visible_cast(self):
        s=self.film['scenes'][0];s['cues']=[self.cue()];s['dialogue']=[{'character':'Leo','text':'Over here.'}]
        validate_film(self.film,self.request)
        s['cues'][0]['offscreen']=False
        with self.assertRaisesRegex(ValueError,'visible'):validate_film(self.film,self.request)

    def test_sound_cannot_extend_beyond_scene_or_change_spoken_script(self):
        s=self.film['scenes'][0];s['cues']=[self.cue()]
        with self.assertRaisesRegex(ValueError,'match exactly'):validate_film(self.film,self.request)
        s['dialogue']=[{'character':'Leo','text':'Over here.'}];s['cues'][0]['end_seconds']=99
        with self.assertRaisesRegex(ValueError,'inside its scene'):validate_film(self.film,self.request)

    def test_silence_produces_empty_valid_tracks_and_full_description(self):
        with tempfile.TemporaryDirectory() as d:
            write_package(self.film,self.request,d,{'type':'test'})
            p=Path(d)
            self.assertEqual((p/'subtitles.srt').read_text(),'')
            self.assertEqual((p/'screen-text.srt').read_text(),'')
            self.assertIn(self.film['scenes'][0]['action'],(p/'description.txt').read_text())
            self.assertIn('not voiceover',(p/'description.txt').read_text())
            self.assertEqual(len(list((p/'thumbnails').glob('*-prompt.txt'))),3)
            self.assertFalse(json.loads((p/'delivery-status.json').read_text())['video_rendered'])

    def test_subtitles_are_sparse_ordered_and_offset_to_scene(self):
        s=self.film['scenes'][1];s['dialogue']=[{'character':'Leo','text':'Over here.'}]
        s['cues']=[dict(kind='foley',start_seconds=6,end_seconds=7,detail='A vibration',reason='Interrupts eye contact',caption='[phone vibrates]',speaker='',text='',offscreen=False),self.cue()]
        s['screen_text']=[dict(start_seconds=1,end_seconds=3,text='Still here?',purpose='An unsent phone draft')]
        with tempfile.TemporaryDirectory() as d:
            write_package(self.film,self.request,d,{'type':'test'});p=Path(d)
            sub=(p/'subtitles.srt').read_text();screen=(p/'screen-text.srt').read_text()
            self.assertIn('00:00:19,000 --> 00:00:21,000',sub)
            self.assertLess(sub.index('Over here.'),sub.index('[phone vibrates]'))
            self.assertNotIn(s['action'],sub)
            self.assertIn('Still here?',screen);self.assertNotIn('Still here?',sub)

    def test_visible_cast_and_three_distinct_thumbnails_are_checked(self):
        self.film['scenes'][0]['actors']=['Max']
        with self.assertRaisesRegex(ValueError,'selected characters'):validate_film(self.film,self.request)
        self.film['scenes'][0]['actors']=['Maya'];self.film['thumbnails'].pop()
        with self.assertRaisesRegex(ValueError,'exactly three'):validate_film(self.film,self.request)

    def test_no_speech_is_an_available_request(self):
        r=make_request('Silence','A girl waits.',5,voices='No speech',characters='Maya (female)')
        self.assertEqual(r['voices'],[]);validate_film(self.film,r)
        self.assertEqual(schema()['properties']['thumbnails']['minItems'],3)

    def test_missing_image_credentials_never_fakes_thumbnails(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'OPENAI_API_KEY'):generate_thumbnails('unused','unused')

    def test_optional_image_backend_writes_three_images_and_actual_status(self):
        import io,base64
        from PIL import Image
        encoded=io.BytesIO();Image.new('RGB',(48,32),'#324155').save(encoded,format='PNG')
        response=json.dumps({'data':[{'b64_json':base64.b64encode(encoded.getvalue()).decode()}]}).encode()
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'OPENAI_API_KEY':'unit-test-not-a-real-key'}):
            p=Path(d);write_package(self.film,self.request,p,{'type':'test'})
            ref=p/'reference.png';ref.write_bytes(encoded.getvalue())
            with patch('urllib.request.urlopen',side_effect=lambda *a,**kw:io.BytesIO(response)) as api:
                generate_thumbnails(p,ref)
            self.assertEqual(api.call_count,3)
            self.assertEqual(json.loads((p/'delivery-status.json').read_text())['thumbnail_images_rendered'],3)
            for i in range(1,4):
                with Image.open(p/'thumbnails'/f'thumbnail-{i}.png') as im:self.assertEqual(im.size,(1280,720))
            self.assertEqual(ref.read_bytes(),encoded.getvalue())
