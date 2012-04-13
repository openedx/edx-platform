import unittest

import numpy

import courseware.modules
import courseware.capa.calc as calc
from grades import Score, aggregate_scores

class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_module_class(self):
        vc = courseware.modules.get_module_class('video')
        vc_str = "<class 'courseware.modules.video_module.Module'>"
        self.assertEqual(str(vc), vc_str)
        video_id = courseware.modules.get_default_ids()['video']
        self.assertEqual(video_id, 'youtube')

    def test_calc(self):
        variables={'R1':2.0, 'R3':4.0}
        functions={'sin':numpy.sin, 'cos':numpy.cos}

        self.assertTrue(abs(calc.evaluator(variables, functions, "10000||sin(7+5)+0.5356"))<0.01)
        self.assertEqual(calc.evaluator({'R1': 2.0, 'R3':4.0}, {}, "13"), 13)
        self.assertEqual(calc.evaluator(variables, functions, "13"), 13)
        self.assertEqual(calc.evaluator({'a': 2.2997471478310274, 'k': 9, 'm': 8, 'x': 0.66009498411213041}, {}, "5"), 5)
        self.assertEqual(calc.evaluator({},{}, "-1"), -1)
        self.assertEqual(calc.evaluator({},{}, "-0.33"), -.33)
        self.assertEqual(calc.evaluator({},{}, "-.33"), -.33)
        self.assertEqual(calc.evaluator(variables, functions, "R1*R3"), 8.0)
        self.assertTrue(abs(calc.evaluator(variables, functions, "sin(e)-0.41"))<0.01)
        self.assertTrue(abs(calc.evaluator(variables, functions, "k*T/q-0.025"))<0.001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "e^(j*pi)")+1)<0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "j||1")-0.5-0.5j)<0.00001)
        exception_happened = False
        try: 
            calc.evaluator({},{}, "5+7 QWSEKO")
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

        try: 
            calc.evaluator({'r1':5},{}, "r1+r2")
        except calc.UndefinedVariable:
            pass
        
        self.assertEqual(calc.evaluator(variables, functions, "r1*r3"), 8.0)

        exception_happened = False
        try: 
            calc.evaluator(variables, functions, "r1*r3", cs=True)
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

class GraderTest(unittest.TestCase):

    def test_weighted_grading(self):
        scores = []
        Score.__sub__=lambda me, other: (me.earned - other.earned) + (me.possible - other.possible)

        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=0, weight=1, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=0, possible=5, weight=1, graded=False, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=1, weight=1, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=3, possible=5, weight=1, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=3.0/5, possible=2, weight=1, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=3.0/5, possible=1, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, weight=2, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=7.0/5, possible=4, weight=1, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=7.0/5, possible=3, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, weight=0, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=7.0/5, possible=4, weight=1, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=7.0/5, possible=3, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, weight=3, graded=False, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=13.0/5, possible=7, weight=1, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=7.0/5, possible=3, weight=1, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, weight=.5, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=14.0/5, possible=7.5, weight=1, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=8.0/5, possible=3.5, weight=1, graded=True, section="summary"))
