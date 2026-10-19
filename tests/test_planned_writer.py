import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.writer import scene_plan, write_planned


class PlannedWriterTests(unittest.TestCase):
    def test_short_request_still_covers_all_settings_and_cast(self):
        locations=['classroom','field','bank','street','cafe']
        plan=scene_plan(2,['female','male1','male2'],locations,'Bank: never caught')
        self.assertEqual({s['location'] for s in plan},set(locations))
        self.assertEqual({s['speaker'] for s in plan},{'female','male1','male2'})
        self.assertTrue(all(s['location']=='cafe' for s in plan if s['staging']=='drink'))

    def test_three_minute_plan_returns_to_classroom_with_chase_and_contact(self):
        locations=['classroom','field','bank','street','cafe']
        plan=scene_plan(18,['female','male1','male2'],locations,'Bank: never caught')
        visits=[s['location'] for i,s in enumerate(plan) if not i or s['location']!=plan[i-1]['location']]
        self.assertEqual(visits,locations+['classroom'])
        self.assertEqual(sum(s['staging']=='chase' for s in plan),3)
        self.assertTrue(any(s['staging']=='drink' and s['location']=='cafe' for s in plan))
        self.assertTrue(any(s['staging']=='handoff' for s in plan))

    def test_dialogue_only_model_cannot_omit_locations_and_resume_preserves_turns(self):
        request={'title':'What if you could rob a bank and never get caught',
                 'description':'Fictional classroom thought experiment with a chase and coffee.',
                 'minutes':3,'voices':['female','male1','male2'],
                 'required_locations':['classroom','field','bank','street','cafe']}
        class FakeWriter:
            calls=0
            fail=True
            def __init__(self,*args,**kwargs):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def complete(self,messages,schema,max_tokens):
                FakeWriter.calls+=1
                if FakeWriter.fail and FakeWriter.calls==3:raise RuntimeError('interrupted')
                count=int(re.search(r'Write approximately (\d+) words',messages[-1]['content'])[1])
                if FakeWriter.calls==4:count=31  # original scene-3 failure: accept and rebalance
                if FakeWriter.calls==19:count+=5  # final turn may also finish naturally
                return json.dumps({'speech':' '.join(['I']+['really']*(count-3)+['like','coffee.'])})
        with tempfile.TemporaryDirectory() as d,patch('studio.local_llm.LocalWriter',FakeWriter):
            out=Path(d)
            with self.assertRaisesRegex(RuntimeError,'interrupted'):
                write_planned(request,out,None,0)
            self.assertEqual(len(json.loads((out/'planned-scenes.json').read_text())['beats']),2)
            FakeWriter.fail=False
            write_planned(request,out,None,0)
            project=json.loads((out/'project.json').read_text())
            self.assertEqual(len(project['scenes']),18)
            self.assertEqual({s['location'] for s in project['scenes']},set(request['required_locations']))
            self.assertEqual(FakeWriter.calls,19)  # 18 turns plus the interrupted call, no replay
            self.assertEqual(json.loads((out/'writer-report.json').read_text())['word_count'],485)
            self.assertEqual(len(json.loads((out/'story.json').read_text())['beats'][2]['text'].split()),31)
            self.assertEqual(json.loads((out/'writer-report.json').read_text())['word_count_deviation'],5)
