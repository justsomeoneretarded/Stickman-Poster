import unittest
import numpy as np
from studio.layered_film import state,foot,frame,svg_frame
from studio.film_concept import make_request,schedule_scenes

class LayeredActingTests(unittest.TestCase):
    def test_emotion_and_camera_are_staged(self):
        waiting,hope,hurt=state(0),state(5),state(10)
        self.assertGreater(hope['openness'],waiting['openness'])
        self.assertGreater(hope['hand_raise'],hurt['hand_raise'])
        self.assertGreater(hurt['head_y'],hope['head_y'])
        self.assertEqual(state(7)['camera_zoom'],1)
        self.assertGreater(hurt['camera_zoom'],1)
    def test_scaled_stance_stays_planted(self):
        for scale in (1.1,1.3):
            positions=[-310*t+scale*foot(t,0,-310/scale)[0] for t in (.1,.3,.5)]
            self.assertLess(max(positions)-min(positions),1e-9)
    def test_rendered_faces_change_and_portrait_is_native(self):
        hope=np.asarray(frame(5,320));hurt=np.asarray(frame(10,320))
        self.assertGreater(np.abs(hope.astype(float)-hurt).mean(),2)
        self.assertEqual(frame(0,180,True).size,(180,320))
        self.assertNotIn('<text',svg_frame(5))
        self.assertNotEqual(svg_frame(5),svg_frame(5,True))
    def test_frame_budget_follows_selected_rate(self):
        request=make_request('A film','A description',5,fps=12)
        self.assertEqual(request['fps'],12)
        self.assertEqual(schedule_scenes({'scenes':[{'seconds':300}]},12)['scenes'][0]['frames'],3600)
        self.assertEqual(schedule_scenes({'scenes':[{'seconds':300}]},24)['scenes'][0]['frames'],7200)
