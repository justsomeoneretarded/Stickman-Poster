"""Fault-injection tests for review evidence; these do not rate artistic appeal."""
import copy
import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio.quality import audio_review, animation_review, review_scripts
from studio.writer import compile_project
from studio.render import frame
from studio.text_policy import safe_label
from studio.media import require_tool
import subprocess


class QualityTests(unittest.TestCase):
    def test_audio_flags_silence_and_clipping_but_not_clean_tone(self):
        with tempfile.TemporaryDirectory() as folder:
            sr=16000;t=np.arange(sr*4)/sr
            fixtures={'silence':np.zeros(sr*4), 'clipped':np.where(np.sin(440*2*np.pi*t)>=0,.99999,-.99999),
                      'clean':.15*np.sin(440*2*np.pi*t)}
            results={}
            for name,signal in fixtures.items():
                path=Path(folder)/(name+'.wav')
                with wave.open(str(path),'wb') as out:
                    out.setparams((1,2,sr,0,'NONE','not compressed'))
                    out.writeframes((signal*32767).astype('<i2').tobytes())
                results[name]={i['category'] for i in audio_review(path)['issues']}
            self.assertIn('clipping',results['clipped'])
            self.assertTrue({'mostly_silent','long_silence'}<=results['silence'])
            self.assertEqual(results['clean'],set())

    def test_default_frames_do_not_display_names_titles_or_dialogue(self):
        for style in ('expressive-v2','legacy'):
            project=compile_project({'visual_style':style,'beats':[{'speaker':'female','location':'field',
                 'staging':'talk','text':'Dialogue before the change.'}]},'Original title','Fixture',['female'])
            scene=project['scenes'][0];scene['duration']=4
            changed=copy.deepcopy(scene)
            changed['heading']='Different title';changed['narration']='Entirely different words.'
            for member in changed.get('cast_members',[]):member['name']='SHOULD NEVER BE VISIBLE'
            a=np.array(frame(scene,1,320,180,preview=False))
            b=np.array(frame(changed,1,320,180,preview=False))
            self.assertTrue(np.array_equal(a,b),style)
            changed['screen_text']='none';changed['on_screen_text']='400 lb'
            self.assertTrue(np.array_equal(a,np.array(frame(changed,1,320,180,preview=False))),style)
            changed['on_screen_text']=''
            changed['screen_text']='captions'
            self.assertFalse(np.array_equal(a,np.array(frame(changed,1,320,180,preview=False))),style)
        self.assertEqual(safe_label('Maya',[{'name':'Maya','id':'maya'}]),'')
        self.assertEqual(safe_label('400 lb',[{'name':'Maya','id':'maya'}]),'400 lb')

    def test_script_critic_discards_fabricated_quotes(self):
        class Reviewer:
            def __init__(self,*args,**kwargs):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def complete(self,messages,schema,max_tokens):
                self_test.assertIn('Do not enforce word counts or runtime',messages[0]['content'])
                self_test.assertIn('Do not demand humor',messages[0]['content'])
                return json.dumps({'summary':'Check continuity.','issues':[
                    {'scene_id':'one','category':'continuity','quote':'The car is gone.',
                     'concern':'Contradicts visible car.','suggestion':'Reconcile action.'},
                    {'scene_id':'one','category':'awkward_speech','quote':'Not in the script.',
                     'concern':'Invented claim','suggestion':'Ignore.'}]})
        self_test=self
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'request.json').write_text(json.dumps({'title':'Test','description':'Serious scene.'}))
            for production in (root,root/'short'):
                (production/'writing').mkdir(parents=True)
                (production/'writing/project.json').write_text(json.dumps({'scenes':[{'id':'one','narration':'The car is gone.'}]}))
            with patch('studio.local_llm.LocalWriter',Reviewer):review_scripts(root,None)
            report=json.loads((root/'writing/script-review.json').read_text())
            self.assertEqual(len(report['issues']),1)
            self.assertEqual(report['unsupported_model_findings_discarded'],1)
            self.assertTrue(report['same_model_family_as_writer'])

    def test_decoded_frozen_active_scene_is_flagged(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            scene={'id':'frozen-flight','staging':'fly','speaker':'hero','duration':4}
            # Encode a frozen actor-colored rectangle: a camera-only/static export must not pass as flying.
            image=np.zeros((180,320,3),dtype=np.uint8);image[60:110,130:170]=(93,155,255)
            video=root/'freeze.mp4'
            subprocess.run([require_tool('ffmpeg'),'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24',
                '-s','320x180','-r','2','-i','pipe:0','-c:v','libx264','-pix_fmt','yuv420p',str(video)],
                input=np.tile(image[None],(24,1,1,1)).tobytes(),check=True)
            report=animation_review(video,{'cast':[{'id':'hero','voice':'male1'}],'scenes':[{**scene,'id':f'frozen-{i}'} for i in range(3)]},
                                    {'fps':2,'scenes':[{'frames':8} for _ in range(3)]},root)
            self.assertTrue({'weak_motion','repeated_staging'}<={i['category'] for i in report['issues']})
            self.assertTrue((root/'motion-review.jpg').exists())
