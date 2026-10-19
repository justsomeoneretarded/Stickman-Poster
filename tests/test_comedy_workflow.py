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

    def test_benching_and_flying_blueprints_show_the_ability_without_canned_speech(self):
        from studio.blueprints import comic_blueprint
        for title,stage,prop in [('What if you could bench a car?','lift','car'),
                                 ('What if you could bench 400 pounds?','lift','barbell'),
                                 ('What if you could fly?','fly','none')]:
            plan=comic_blueprint(title,['female','male1','male2'],3)
            self.assertEqual(plan[0]['staging'],stage)
            self.assertEqual(plan[0]['prop'],prop)
            self.assertTrue(all('text' not in slot for slot in plan))
            self.assertFalse(any(s['location'] in ('classroom','bank') for s in plan))
            self.assertEqual(plan[-1]['comic_role'],'payoff')
