import copy
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from studio.film_concept import make_request,write_package
from studio.film_director import compile_film,validate_shots,shot_schema
from studio.film_art import frame
from studio.film_sound import mix,write_wav
from studio.complete_film import picture,posters,finalize


def actor(name='Maya',action='stand',prop='none',pos='left'):
    return {'character':name,'action':action,'prop':prop,'from':pos,'to':pos,'look':'right','emotion_start':'sad','emotion_end':'hopeful'}

def shot():
    return {'setting':'cafe','actors':[actor()], 'focus':'Maya','framing':'medium','motion':'push','pacing':'normal','score':'quiet',
            'description':'She risks looking up.','camera_reason':'Read the change in her eyes.','screen_text':'','cues':[]}

def fixture(minutes=.05):
    request=make_request('A quiet choice','A lonely girl looks up.',minutes,voices='No speech',fps=12)
    outline={'logline':'A girl chooses to look up.','story':'She looks up and sees a possible connection.','ending':'She stays.',
        'publishing_description':'A small change in attention.','keywords':['loneliness','quiet','connection','animation','story'],
        'scenes':[{'id':'a','location':'cafe','beat':'turning point','action':'She looks up.','change':'Sad to hopeful.'}]}
    film=compile_film(outline,[{'shots':[shot(),shot(),shot()]}],request)
    film['thumbnails']=[dict(hook_text=f'STILL HERE {i}',source_scene_id='a',image_prompt=f'Distinct composition {i}',composition=str(i),emotional_promise='Connection') for i in (1,2,3)]
    return film,request

class CompleteFilmTests(unittest.TestCase):
    def test_model_never_supplies_duration_and_no_speech_is_grammar_enforced(self):
        _,r=fixture();schema=shot_schema(r);props=schema['properties']['shots']['items']['properties']
        self.assertNotIn('seconds',props)
        self.assertNotIn('speech',props['cues']['items']['properties']['asset']['enum'])
        f,r=fixture(5)
        self.assertAlmostEqual(sum(s['seconds'] for seq in f['scenes'] for s in seq['shots']),300)

    def test_handoffs_and_moving_characters_are_physical_requirements(self):
        _,r=fixture();s=shot();s['actors']=[actor(action='offer',prop='paper')]
        with self.assertRaisesRegex(ValueError,'handoff'):validate_shots({'shots':[s,s,s]},r)
        s['actors']=[actor(action='walk')]
        with self.assertRaisesRegex(ValueError,'change position'):validate_shots({'shots':[s,s,s]},r)

    def test_new_art_varies_expression_and_action_not_only_camera(self):
        s=shot();s['seconds']=3;s['id']='one';s['framing']='closeup';s['motion']='hold'
        a=np.array(frame(s,.1,320)).astype(float);b=np.array(frame(s,2.5,320)).astype(float)
        self.assertGreater(np.mean(abs(a-b)),.2)
        s['actors'][0].update(action='phone',prop='phone')
        c=np.array(frame(s,2.5,320)).astype(float)
        self.assertGreater(np.mean(abs(b-c)),.4)
        self.assertEqual(frame(s,1,180,True).size,(180,320))

    def test_speech_retimes_picture_and_subtitles_instead_of_truncating(self):
        f,r=fixture();r['voices']=['female'];s=f['scenes'][0]['shots'][0]
        s['cues']=[dict(asset='speech',at='begin',speaker='Maya',text='Can I sit here?',caption='',reason='She takes a risk.',offscreen=False,start_seconds=.1,end_seconds=.6)]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_package(f,r,p,{'type':'test'});wav=p/'measured.wav';write_wav(wav,np.sin(np.arange(72000)*.04).astype(np.float32)*.1)
            (p/'voice-assets.json').write_text(json.dumps({s['id']+'-0':str(wav)}));report=mix(p)
            saved=json.loads((p/'film.json').read_text());first=saved['scenes'][0]['shots'][0]
            self.assertGreaterEqual(first['seconds'],3.5)
            self.assertAlmostEqual(first['cues'][0]['end_seconds'],3.1,places=3)
            self.assertIn('00:00:00,100 --> 00:00:03,100',(p/'subtitles.srt').read_text())
            self.assertEqual(report['clipped_samples'],0)

    def test_complete_real_encoded_deliverables_are_required(self):
        f,r=fixture(.03)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('long-form','short-form'):
                p=root/name;write_package(f,r,p,{'type':'test'});mix(p)
                picture(p,name=='short-form',180 if name=='short-form' else 320)
            posters(root/'long-form');finalize(root)
            status=json.loads((root/'deliverables'/'completion.json').read_text())
            self.assertTrue(status['complete'])
            for name in ('long-form','short-form'):
                report=json.loads((root/'deliverables'/name/'render-report.json').read_text())
                self.assertEqual(report['fps'],12);self.assertEqual(report['frames'],21)
            self.assertEqual(len(list((root/'deliverables'/'thumbnails').glob('thumbnail-*.png'))),3)
            (root/'short-form'/'video'/'final.mp4').unlink()
            with self.assertRaises(FileNotFoundError):finalize(root)

    def test_fast_native_pixels_match_png_render_without_quality_loss(self):
        import io,cairosvg
        from PIL import Image
        from studio.film_art import svg
        s=shot();s['seconds']=3;s['id']='pixels';raw=svg(s,1)
        expected=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=raw.encode(),output_width=320,output_height=180))).convert('RGB')
        actual=frame(s,1,320)
        self.assertEqual(np.max(abs(np.array(expected).astype(float)-np.array(actual))),0)

    def test_cached_set_compositor_keeps_native_animation_and_correct_alpha(self):
        import io,cairosvg
        from PIL import Image
        from studio.film_fast import raster,frame as layered
        source='<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4" fill="red" fill-opacity=".5"/></svg>'
        expected=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=source.encode()))).convert('RGBA')
        self.assertEqual(list(raster(source,4,4).getdata()),list(expected.getdata()))
        s=shot();s['seconds']=3;s['id']='composite';s['framing']='closeup';s['motion']='hold'
        a=np.array(layered(s,.1,320)).astype(float);b=np.array(layered(s,2.5,320)).astype(float)
        self.assertGreater(np.mean(abs(a-b)),.2)
        self.assertEqual(layered(s,1,180,True).size,(180,320))

    def test_title_drives_staged_directing_and_complete_film_can_resume(self):
        from unittest.mock import patch
        from studio.film_director import develop
        _,r=fixture(5)
        outline={'logline':'A new story.','story':'She risks looking up.','ending':'She stays.',
             'publishing_description':'A new story based on a brief.','keywords':['quiet','story','girl','choice','animation'],
             'scenes':[dict(id=f's{i}',location='cafe',beat='turning point',action='She looks up.',change='She becomes hopeful.') for i in range(6)]}
        thumbs=[dict(hook_text=f'CHOICE {i}',emotional_promise='A small connection',composition=str(i),image_prompt=f'Composition {i}',source_scene_id='s0') for i in range(3)]
        class Writer:
            calls=0
            def __init__(self,*a,**kw):pass
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def complete(self,messages,schema,tokens):
                Writer.calls+=1
                if Writer.calls==1:
                    self_test.assertEqual(json.loads(messages[1]['content'])['title'],r['title'])
                    return json.dumps(outline)
                if Writer.calls==8:return json.dumps({'thumbnails':thumbs})
                return json.dumps({'shots':[shot(),shot(),shot()]})
        self_test=self
        with tempfile.TemporaryDirectory() as d,patch('studio.film_director.LocalWriter',Writer):
            film=develop(r,d,None);develop(r,d,None)
            self.assertEqual(Writer.calls,8)
            self.assertEqual(len([s for seq in film['scenes'] for s in seq['shots']]),18)
            self.assertAlmostEqual(sum(seq['seconds'] for seq in film['scenes']),300)
            self.assertTrue((Path(d)/'description.txt').exists())

    def test_end_cues_and_text_survive_fractional_frame_scene_boundaries(self):
        from studio.film_concept import validate_film
        for minutes in (1,3,5,4.2,.03):
            for sequence_count in (6,8,10):
                _,r=fixture(minutes)
                outline={'logline':'A story','story':'A story','ending':'An ending','publishing_description':'A film','keywords':['a','b','c','d','e'],
                    'scenes':[dict(id=str(i),location='cafe',beat='beat',action='act',change='change') for i in range(sequence_count)]}
                s=shot();s['screen_text']='Still here?'
                s['cues']=[dict(asset='paper_rustle',at='end',speaker='',text='',caption='',offscreen=False,reason='She folds the note.')]
                film=compile_film(outline,[{'shots':[copy.deepcopy(s) for j in range(3)]} for i in range(sequence_count)],r)
                validate_film(film,r)
