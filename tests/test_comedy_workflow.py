import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio.actions_entry import read_request
from studio.shortform import highlight_plan, write_short
from studio.writer import compile_project, validate_outline
from studio.project import timeline
from studio.cinematic import frame


class ComedyWorkflowTests(unittest.TestCase):
    def test_every_run_requires_a_fresh_idea_instead_of_using_bank_demo(self):
        with self.assertRaisesRegex(ValueError,'title, description, minutes'):read_request({})
        request=read_request({'EPISODE_TITLE':'What if you could fly?',
                              'EPISODE_DESCRIPTION':'A funny commute above pigeon traffic.',
                              'EPISODE_MINUTES':'5','EPISODE_SHORT_SECONDS':'45'})
        self.assertEqual(request['title'],'What if you could fly?')
        self.assertEqual(request['short_seconds'],'45')
        self.assertNotIn('required_locations',request)
        self.assertNotIn('revision_project',request)

    def test_highlights_keep_opening_payoff_and_best_gag_in_story_order(self):
        beats=[{'speaker':'male1','location':'gym','staging':'lift','prop':'car',
                'text':'I asked for a spotter, not a parking attendant.',
                'short_score':score,'comic_role':'escalation'} for score in (0,4,2,10,1,0)]
        p=compile_project({'beats':beats,'visual_style':'expressive-v2'},'Bench a car','Funny.',['male1'])
        selected=highlight_plan(p,30)
        self.assertEqual([s['source_scene_id'] for s in selected],['beat-001','beat-004','beat-006'])
        with tempfile.TemporaryDirectory() as d,patch('studio.shortform.write_planned') as write:
            root=Path(d);(root/'p.json').write_text(json.dumps(p))
            (root/'r.json').write_text(json.dumps({'title':'Bench a car','description':'Funny.',
                 'voices':['male1'],'minutes':5,'short_seconds':30}))
            write_short(root/'p.json',root/'r.json',root/'short',None)
            self.assertEqual(write.call_args.args[0]['minutes'],.5)
            self.assertIn('STANDALONE',write.call_args.args[0]['description'])
            self.assertEqual(len(write.call_args.args[-1]),3)

    def test_car_is_visibly_lifted_and_flying_head_stays_inside_both_formats(self):
        p=compile_project({'visual_style':'expressive-v2','beats':[{'speaker':'male1','location':'gym',
            'staging':'lift','prop':'car','text':'My car is having a very unusual leg day.'}]},'Bench a car','Funny.',['male1'])
        scene=timeline(p,24)[0];scene['duration']=5
        for width,height in ((960,540),(576,1024)):
            centers=[]
            for t in (0,2):
                a=np.array(frame(scene,t,width,height))
                mask=(a[:,:,0]>200)&(a[:,:,1]>85)&(a[:,:,1]<150)&(a[:,:,2]>90)&(a[:,:,2]<160)
                centers.append(np.where(mask)[0].mean())
                head=np.all(a==[12,18,32],axis=2)
                self.assertGreater(head.sum(),1300)  # load must not obscure the lifter's face
                if width>height:
                    blue=np.all(a==[93,155,255],axis=2)
                    self.assertEqual(blue[:,int(width*.75):].sum(),0)  # no duplicate standing hero
            self.assertGreater(abs(centers[1]-centers[0]),30)
            scene['staging']='fly';scene['location']='rooftop'
            for t in (0,2.5,5):
                a=np.array(frame(scene,t,width,height))
                head=np.all(a==[11,17,29],axis=2)
                rows=np.where(head)[0]
                self.assertGreater(len(rows),20)
                self.assertGreater(rows.min(),10)
            scene['staging']='lift';scene['location']='gym'

    def test_outline_corrects_physical_location_without_turning_barbell_into_car(self):
        slots=[{'speaker':'male1','location':'street','staging':'lift','prop':'barbell'}]
        result=validate_outline(slots,['male1'])
        self.assertEqual(result[0]['location'],'gym')
        self.assertEqual(result[0]['prop'],'barbell')

    def test_voice_menu_supports_every_single_pair_and_full_cast(self):
        from studio.actions_entry import VOICE_CHOICES
        seen=set()
        for label,ids in VOICE_CHOICES.items():
            request=read_request({'EPISODE_TITLE':'Flying','EPISODE_DESCRIPTION':'Funny commute.',
                                  'EPISODE_MINUTES':'3','EPISODE_VOICES':label})
            self.assertEqual(request['voices'],ids)
            self.assertEqual(int(label[0]),len(ids.split(',')))
            seen.add(tuple(ids.split(',')))
        self.assertEqual(len(seen),7)

    def test_description_drives_tone_without_forced_gags_for_known_titles(self):
        from studio.writer import write_creative
        class Writer:
            messages=[]
            def __init__(self,*a,**kw):pass
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def complete(self,messages,schema,max_tokens):
                Writer.messages.extend(m['content'] for m in messages)
                fields=schema['properties']
                if 'pitch' in fields:return json.dumps({'pitch':'A calm, serious exploration of extraordinary strength.'})
                if 'beats' in fields:return json.dumps({'beats':[{'speaker':'male1','location':'gym',
                    'staging':'talk','shot':'medium','prop':'none','purpose':'Explore the physical experience of lifting a heavy object calmly.',
                    'comic_role':'setup','short_score':5} for _ in range(6)]})
                return json.dumps({'speech':'You can lift the car and examine its weight calmly.'})
        request={'title':'What if you could bench a car?','description':'A serious, calm exploration. No comedy.',
                 'voices':['male1'],'minutes':.3}
        with tempfile.TemporaryDirectory() as directory,patch('studio.local_llm.LocalWriter',Writer):
            write_creative(request,Path(directory),None,0)
            self.assertTrue((Path(directory)/'project.json').exists())
        prompts=' '.join(Writer.messages)
        self.assertIn(request['description'],prompts)
        for forced in ('final callback joke','pigeon rush hour','parking space easier','Make this funny'):
            self.assertNotIn(forced,prompts)
