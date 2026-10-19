import copy
import unittest
from studio.animation import actor_state, blocking_for, drink_hand
from studio.writer import compile_project
from studio import project, render

CAST=[{'id':'maya','name':'Maya','voice':'female'}, {'id':'leo','name':'Leo','voice':'male1'}, {'id':'max','name':'Max','voice':'male2'}]
class MotionTests(unittest.TestCase):
    def test_short_sentences_share_one_voice_generation_context(self):
        from studio.voice import speech_chunks
        self.assertEqual(speech_chunks("Wait, the cup moved. Did you see that?"),["Wait, the cup moved. Did you see that?"])

    def test_both_chase_characters_travel_forward_over_a_full_shot(self):
        paths=blocking_for(CAST,'maya','chase')
        for cid in ('leo','max'):
            positions=[actor_state(paths[cid],t,10,'chase')['x'] for t in (0,2,5,8,10)]
            self.assertEqual(positions,sorted(positions))
            self.assertGreater(positions[-1]-positions[0],1500)
        for t in (0,2,5,8,10):
            self.assertGreater(actor_state(paths['leo'],t,10,'chase')['x']-actor_state(paths['max'],t,10,'chase')['x'],350)
    def test_drink_lifts_to_mouth_and_returns_to_table(self):
        rest,_=drink_hand(0);mouth,amount=drink_hand(.5);returned,_=drink_hand(1)
        self.assertEqual(rest,returned)
        self.assertEqual(amount,1)
        self.assertLess(mouth[1],rest[1]-130)
        self.assertLess(abs(mouth[0]-205),50)
    def test_new_locations_and_grounded_actions_render(self):
        for location,staging in [('classroom','enter'),('field','travel'),('bank','carry'),('street','chase'),('cafe','drink'),('bank','handoff')]:
            story={'beats':[{'speaker':'male1','text':'This is an original fictional scene for testing.', 'location':location,'action':'point','staging':staging}]}
            p=compile_project(story,'What if you could rob a bank?','Fiction',['female','male1','male2'])
            scene=project.timeline(p,24)[0]
            scene['duration']=10
            for t in (1,5,9):
                self.assertEqual(render.frame(scene,t,640,360,False).size,(640,360))
    def test_out_of_bounds_paths_fail_validation(self):
        p=compile_project({'beats':[{'speaker':'female','text':'A fictional scene with a walking character.','staging':'travel'}]},'Test','Fiction',['female'])
        p['scenes'][0]['blocking']['maya']['end']=100
        with self.assertRaises(ValueError):project.validate(p)
