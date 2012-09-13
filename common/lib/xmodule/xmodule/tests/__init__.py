#
# unittests for xmodule (and capa)
#
# Note: run this using a like like this:
#
# django-admin.py test --settings=lms.envs.test_ike --pythonpath=. common/lib/xmodule

import unittest
import os
import fs
import fs.osfs
import json

import json
import numpy

import xmodule
import capa.calc as calc
import capa.capa_problem as lcp
from capa.correctmap import CorrectMap
from capa.util import convert_files_to_filenames
from capa.xqueue_interface import dateformat
from datetime import datetime
from xmodule import graders, x_module
from xmodule.x_module import ModuleSystem
from xmodule.graders import Score, aggregate_scores
from xmodule.progress import Progress
from nose.plugins.skip import SkipTest
from mock import Mock

i4xs = ModuleSystem(
    ajax_url='courses/course_id/modx/a_location',
    track_function=Mock(),
    get_module=Mock(),
    render_template=Mock(),
    replace_urls=Mock(),
    user=Mock(),
    filestore=fs.osfs.OSFS(os.path.dirname(os.path.realpath(__file__))+"/test_files"),
    debug=True,
    xqueue={'interface':None, 'callback_url':'/', 'default_queuename': 'testqueue', 'waittime': 10},
    node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
    anonymous_student_id = 'student'
)


class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_class(self):
        vc = xmodule.x_module.XModuleDescriptor.load_class('video')
        vc_str = "<class 'xmodule.video_module.VideoDescriptor'>"
        self.assertEqual(str(vc), vc_str)

    def test_calc(self):
        variables = {'R1': 2.0, 'R3': 4.0}
        functions = {'sin': numpy.sin, 'cos': numpy.cos}

        self.assertTrue(abs(calc.evaluator(variables, functions, "10000||sin(7+5)+0.5356")) < 0.01)
        self.assertEqual(calc.evaluator({'R1': 2.0, 'R3': 4.0}, {}, "13"), 13)
        self.assertEqual(calc.evaluator(variables, functions, "13"), 13)
        self.assertEqual(calc.evaluator({'a': 2.2997471478310274, 'k': 9, 'm': 8, 'x': 0.66009498411213041}, {}, "5"), 5)
        self.assertEqual(calc.evaluator({}, {}, "-1"), -1)
        self.assertEqual(calc.evaluator({}, {}, "-0.33"), -.33)
        self.assertEqual(calc.evaluator({}, {}, "-.33"), -.33)
        self.assertEqual(calc.evaluator(variables, functions, "R1*R3"), 8.0)
        self.assertTrue(abs(calc.evaluator(variables, functions, "sin(e)-0.41")) < 0.01)
        self.assertTrue(abs(calc.evaluator(variables, functions, "k*T/q-0.025")) < 0.001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "e^(j*pi)") + 1) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "j||1") - 0.5 - 0.5j) < 0.00001)
        variables['t'] = 1.0
        self.assertTrue(abs(calc.evaluator(variables, functions, "t") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "t", cs=True) - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T", cs=True) - 298) < 0.2)
        exception_happened = False
        try:
            calc.evaluator({}, {}, "5+7 QWSEKO")
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

        try:
            calc.evaluator({'r1': 5}, {}, "r1+r2")
        except calc.UndefinedVariable:
            pass

        self.assertEqual(calc.evaluator(variables, functions, "r1*r3"), 8.0)

        exception_happened = False
        try:
            calc.evaluator(variables, functions, "r1*r3", cs=True)
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

#-----------------------------------------------------------------------------
# tests of capa_problem inputtypes


class MultiChoiceTest(unittest.TestCase):
    def test_MC_grade(self):
        multichoice_file = os.path.dirname(__file__) + "/test_files/multichoice.xml"
        test_lcp = lcp.LoncapaProblem(open(multichoice_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'choice_foil3'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        false_answers = {'1_2_1': 'choice_foil2'}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')

    def test_MC_bare_grades(self):
        multichoice_file = os.path.dirname(__file__) + "/test_files/multi_bare.xml"
        test_lcp = lcp.LoncapaProblem(open(multichoice_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'choice_2'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        false_answers = {'1_2_1': 'choice_1'}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')

    def test_TF_grade(self):
        truefalse_file = os.path.dirname(__file__) + "/test_files/truefalse.xml"
        test_lcp = lcp.LoncapaProblem(open(truefalse_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': ['choice_foil2', 'choice_foil1']}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        false_answers = {'1_2_1': ['choice_foil1']}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')
        false_answers = {'1_2_1': ['choice_foil1', 'choice_foil3']}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')
        false_answers = {'1_2_1': ['choice_foil3']}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')
        false_answers = {'1_2_1': ['choice_foil1', 'choice_foil2', 'choice_foil3']}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')


class ImageResponseTest(unittest.TestCase):
    def test_ir_grade(self):
        imageresponse_file = os.path.dirname(__file__) + "/test_files/imageresponse.xml"
        test_lcp = lcp.LoncapaProblem(open(imageresponse_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': '(490,11)-(556,98)',
                           '1_2_2': '(242,202)-(296,276)'}
        test_answers = {'1_2_1': '[500,20]',
                        '1_2_2': '[250,300]',
                        }
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_2'), 'incorrect')


class SymbolicResponseTest(unittest.TestCase):
    def test_sr_grade(self):
        raise SkipTest()  # This test fails due to dependencies on a local copy of snuggletex-webapp. Until we have figured that out, we'll just skip this test
        symbolicresponse_file = os.path.dirname(__file__) + "/test_files/symbolicresponse.xml"
        test_lcp = lcp.LoncapaProblem(open(symbolicresponse_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'cos(theta)*[[1,0],[0,1]] + i*sin(theta)*[[0,1],[1,0]]',
                           '1_2_1_dynamath': '''
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
    <mrow>
      <mi>cos</mi>
      <mrow>
        <mo>(</mo>
        <mi>&#x3B8;</mi>
        <mo>)</mo>
      </mrow>
    </mrow>
    <mo>&#x22C5;</mo>
    <mrow>
      <mo>[</mo>
      <mtable>
        <mtr>
          <mtd>
            <mn>1</mn>
          </mtd>
          <mtd>
            <mn>0</mn>
          </mtd>
        </mtr>
        <mtr>
          <mtd>
            <mn>0</mn>
          </mtd>
          <mtd>
            <mn>1</mn>
          </mtd>
        </mtr>
      </mtable>
      <mo>]</mo>
    </mrow>
    <mo>+</mo>
    <mi>i</mi>
    <mo>&#x22C5;</mo>
    <mrow>
      <mi>sin</mi>
      <mrow>
        <mo>(</mo>
        <mi>&#x3B8;</mi>
        <mo>)</mo>
      </mrow>
    </mrow>
    <mo>&#x22C5;</mo>
    <mrow>
      <mo>[</mo>
      <mtable>
        <mtr>
          <mtd>
            <mn>0</mn>
          </mtd>
          <mtd>
            <mn>1</mn>
          </mtd>
        </mtr>
        <mtr>
          <mtd>
            <mn>1</mn>
          </mtd>
          <mtd>
            <mn>0</mn>
          </mtd>
        </mtr>
      </mtable>
      <mo>]</mo>
    </mrow>
  </mstyle>
</math>
''',
                           }
        wrong_answers = {'1_2_1': '2',
                         '1_2_1_dynamath': '''
                         <math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
    <mn>2</mn>
  </mstyle>
</math>''',
                        }
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(wrong_answers).get_correctness('1_2_1'), 'incorrect')


class OptionResponseTest(unittest.TestCase):
    '''
    Run this with

    python manage.py test courseware.OptionResponseTest
    '''
    def test_or_grade(self):
        optionresponse_file = os.path.dirname(__file__) + "/test_files/optionresponse.xml"
        test_lcp = lcp.LoncapaProblem(open(optionresponse_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'True',
                           '1_2_2': 'False'}
        test_answers = {'1_2_1': 'True',
                        '1_2_2': 'True',
                        }
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_2'), 'incorrect')


class FormulaResponseWithHintTest(unittest.TestCase):
    '''
    Test Formula response problem with a hint
    This problem also uses calc.
    '''
    def test_or_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/formularesponse_with_hint.xml"
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': '2.5*x-5.0'}
        test_answers = {'1_2_1': '0.4*x-5.0'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        cmap = test_lcp.grade_answers(test_answers)
        self.assertEquals(cmap.get_correctness('1_2_1'), 'incorrect')
        self.assertTrue('You have inverted' in cmap.get_hint('1_2_1'))


class StringResponseWithHintTest(unittest.TestCase):
    '''
    Test String response problem with a hint
    '''
    def test_or_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/stringresponse_with_hint.xml"
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'Michigan'}
        test_answers = {'1_2_1': 'Minnesota'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        cmap = test_lcp.grade_answers(test_answers)
        self.assertEquals(cmap.get_correctness('1_2_1'), 'incorrect')
        self.assertTrue('St. Paul' in cmap.get_hint('1_2_1'))


class CodeResponseTest(unittest.TestCase):
    '''
    Test CodeResponse
    TODO: Add tests for external grader messages
    '''
    @staticmethod
    def make_queuestate(key, time):
        timestr = datetime.strftime(time, dateformat)
        return {'key': key, 'time': timestr}

    def test_is_queued(self):
        ''' 
        Simple test of whether LoncapaProblem knows when it's been queued
        '''
        problem_file = os.path.join(os.path.dirname(__file__), "test_files/coderesponse.xml")
        with open(problem_file) as input_file:
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=i4xs)
            
            answer_ids = sorted(test_lcp.get_question_answers())

            # CodeResponse requires internal CorrectMap state. Build it now in the unqueued state
            cmap = CorrectMap()
            for answer_id in answer_ids:
                cmap.update(CorrectMap(answer_id=answer_id, queuestate=None))
            test_lcp.correct_map.update(cmap)

            self.assertEquals(test_lcp.is_queued(), False)

            # Now we queue the LCP
            cmap = CorrectMap()
            for i, answer_id in enumerate(answer_ids): 
                queuestate = CodeResponseTest.make_queuestate(i, datetime.now())
                cmap.update(CorrectMap(answer_id=answer_ids[i], queuestate=queuestate))
            test_lcp.correct_map.update(cmap)

            self.assertEquals(test_lcp.is_queued(), True)


    def test_update_score(self):
        '''
        Test whether LoncapaProblem.update_score can deliver queued result to the right subproblem
        '''
        problem_file = os.path.join(os.path.dirname(__file__), "test_files/coderesponse.xml")
        with open(problem_file) as input_file:
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=i4xs)

            answer_ids = sorted(test_lcp.get_question_answers())

            # CodeResponse requires internal CorrectMap state. Build it now in the queued state
            old_cmap = CorrectMap()
            for i, answer_id in enumerate(answer_ids):
                queuekey = 1000 + i
                queuestate = CodeResponseTest.make_queuestate(1000+i, datetime.now())
                old_cmap.update(CorrectMap(answer_id=answer_ids[i], queuestate=queuestate))

            # Message format common to external graders
            grader_msg = '<span>MESSAGE</span>' # Must be valid XML
            correct_score_msg = json.dumps({'correct':True, 'score':1, 'msg': grader_msg})
            incorrect_score_msg = json.dumps({'correct':False, 'score':0, 'msg': grader_msg})

            xserver_msgs = {'correct': correct_score_msg,
                            'incorrect': incorrect_score_msg,}

            # Incorrect queuekey, state should not be updated
            for correctness in ['correct', 'incorrect']:
                test_lcp.correct_map = CorrectMap()
                test_lcp.correct_map.update(old_cmap)  # Deep copy

                test_lcp.update_score(xserver_msgs[correctness], queuekey=0)
                self.assertEquals(test_lcp.correct_map.get_dict(), old_cmap.get_dict())  # Deep comparison

                for answer_id in answer_ids:
                    self.assertTrue(test_lcp.correct_map.is_queued(answer_id))  # Should be still queued, since message undelivered

            # Correct queuekey, state should be updated
            for correctness in ['correct', 'incorrect']:
                for i, answer_id in enumerate(answer_ids):
                    test_lcp.correct_map = CorrectMap()
                    test_lcp.correct_map.update(old_cmap)

                    new_cmap = CorrectMap()
                    new_cmap.update(old_cmap)
                    npoints = 1 if correctness=='correct' else 0
                    new_cmap.set(answer_id=answer_id, npoints=npoints, correctness=correctness, msg=grader_msg, queuestate=None)

                    test_lcp.update_score(xserver_msgs[correctness], queuekey=1000 + i)
                    self.assertEquals(test_lcp.correct_map.get_dict(), new_cmap.get_dict())

                    for j, test_id in enumerate(answer_ids):
                        if j == i:
                            self.assertFalse(test_lcp.correct_map.is_queued(test_id))  # Should be dequeued, message delivered
                        else:
                            self.assertTrue(test_lcp.correct_map.is_queued(test_id))  # Should be queued, message undelivered
    

    def test_recentmost_queuetime(self):
        '''
        Test whether the LoncapaProblem knows about the time of queue requests
        '''
        problem_file = os.path.join(os.path.dirname(__file__), "test_files/coderesponse.xml")
        with open(problem_file) as input_file:
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=i4xs)

            answer_ids = sorted(test_lcp.get_question_answers())

            # CodeResponse requires internal CorrectMap state. Build it now in the unqueued state
            cmap = CorrectMap()
            for answer_id in answer_ids:
                cmap.update(CorrectMap(answer_id=answer_id, queuestate=None))
            test_lcp.correct_map.update(cmap)
            
            self.assertEquals(test_lcp.get_recentmost_queuetime(), None)

            # CodeResponse requires internal CorrectMap state. Build it now in the queued state
            cmap = CorrectMap()
            for i, answer_id in enumerate(answer_ids):
                queuekey = 1000 + i
                latest_timestamp = datetime.now()
                queuestate = CodeResponseTest.make_queuestate(1000+i, latest_timestamp)
                cmap.update(CorrectMap(answer_id=answer_id, queuestate=queuestate))
            test_lcp.correct_map.update(cmap)

            # Queue state only tracks up to second
            latest_timestamp = datetime.strptime(datetime.strftime(latest_timestamp, dateformat), dateformat)

            self.assertEquals(test_lcp.get_recentmost_queuetime(), latest_timestamp)

        def test_convert_files_to_filenames(self):
            '''
            Test whether file objects are converted to filenames without altering other structures
            '''
            problem_file = os.path.join(os.path.dirname(__file__), "test_files/coderesponse.xml")
            with open(problem_file) as fp:
                answers_with_file = {'1_2_1': 'String-based answer',
                                     '1_3_1': ['answer1', 'answer2', 'answer3'],
                                     '1_4_1': [fp, fp]}
                answers_converted = convert_files_to_filenames(answers_with_file)
                self.assertEquals(answers_converted['1_2_1'], 'String-based answer')
                self.assertEquals(answers_converted['1_3_1'], ['answer1', 'answer2', 'answer3'])
                self.assertEquals(answers_converted['1_4_1'], [fp.name, fp.name])


class ChoiceResponseTest(unittest.TestCase):

    def test_cr_rb_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/choiceresponse_radio.xml"
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'choice_2',
                           '1_3_1': ['choice_2', 'choice_3']}
        test_answers = {'1_2_1': 'choice_2',
                        '1_3_1': 'choice_2',
                        }
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_1'), 'incorrect')

    def test_cr_cb_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/choiceresponse_checkbox.xml"
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': 'choice_2',
                           '1_3_1': ['choice_2', 'choice_3'],
                           '1_4_1': ['choice_2', 'choice_3']}
        test_answers = {'1_2_1': 'choice_2',
                        '1_3_1': 'choice_2',
                        '1_4_1': ['choice_2', 'choice_3'],
                        }
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_1'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_4_1'), 'correct')

class JavascriptResponseTest(unittest.TestCase):

    def test_jr_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/javascriptresponse.xml"
        coffee_file_path = os.path.dirname(__file__) + "/test_files/js/*.coffee"
        os.system("coffee -c %s" % (coffee_file_path))
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=i4xs)
        correct_answers = {'1_2_1': json.dumps({0: 4})}
        incorrect_answers = {'1_2_1': json.dumps({0: 5})}

        self.assertEquals(test_lcp.grade_answers(incorrect_answers).get_correctness('1_2_1'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')

#-----------------------------------------------------------------------------
# Grading tests


class GradesheetTest(unittest.TestCase):

    def test_weighted_grading(self):
        scores = []
        Score.__sub__ = lambda me, other: (me.earned - other.earned) + (me.possible - other.possible)

        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=0, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, graded=True, section="summary"))

        scores.append(Score(earned=0, possible=5, graded=False, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=5, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, graded=True, section="summary"))

        scores.append(Score(earned=3, possible=5, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=3, possible=10, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=3, possible=5, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=5, possible=15, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=5, possible=10, graded=True, section="summary"))


class GraderTest(unittest.TestCase):

    empty_gradesheet = {
    }

    incomplete_gradesheet = {
        'Homework': [],
        'Lab': [],
        'Midterm': [],
    }

    test_gradesheet = {
        'Homework': [Score(earned=2, possible=20.0, graded=True, section='hw1'),
              Score(earned=16, possible=16.0, graded=True, section='hw2')],
              #The dropped scores should be from the assignments that don't exist yet

        'Lab': [Score(earned=1, possible=2.0, graded=True, section='lab1'),  # Dropped
             Score(earned=1, possible=1.0, graded=True, section='lab2'),
             Score(earned=1, possible=1.0, graded=True, section='lab3'),
             Score(earned=5, possible=25.0, graded=True, section='lab4'),  # Dropped
             Score(earned=3, possible=4.0, graded=True, section='lab5'),  # Dropped
             Score(earned=6, possible=7.0, graded=True, section='lab6'),
             Score(earned=5, possible=6.0, graded=True, section='lab7')],

        'Midterm': [Score(earned=50.5, possible=100, graded=True, section="Midterm Exam"), ],
    }

    def test_SingleSectionGrader(self):
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")
        lab4Grader = graders.SingleSectionGrader("Lab", "lab4")
        badLabGrader = graders.SingleSectionGrader("Lab", "lab42")

        for graded in [midtermGrader.grade(self.empty_gradesheet),
                        midtermGrader.grade(self.incomplete_gradesheet),
                        badLabGrader.grade(self.test_gradesheet)]:
            self.assertEqual(len(graded['section_breakdown']), 1)
            self.assertEqual(graded['percent'], 0.0)

        graded = midtermGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.505)
        self.assertEqual(len(graded['section_breakdown']), 1)

        graded = lab4Grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2)
        self.assertEqual(len(graded['section_breakdown']), 1)

    def test_AssignmentFormatGrader(self):
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        noDropGrader = graders.AssignmentFormatGrader("Homework", 12, 0)
        #Even though the minimum number is 3, this should grade correctly when 7 assignments are found
        overflowGrader = graders.AssignmentFormatGrader("Lab", 3, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)

        #Test the grading of an empty gradesheet
        for graded in [homeworkGrader.grade(self.empty_gradesheet),
                        noDropGrader.grade(self.empty_gradesheet),
                        homeworkGrader.grade(self.incomplete_gradesheet),
                        noDropGrader.grade(self.incomplete_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            #Make sure the breakdown includes 12 sections, plus one summary
            self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = homeworkGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)  # 100% + 10% / 10 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = noDropGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0916666666666666)  # 100% + 10% / 12 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = overflowGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.8880952380952382)  # 100% + 10% / 5 assignments
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

        graded = labGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.9226190476190477)
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

    def test_WeightedSubsectionsGrader(self):
        #First, a few sub graders
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")

        weightedGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.25), (labGrader, labGrader.category, 0.25),
        (midtermGrader, midtermGrader.category, 0.5)])

        overOneWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.5), (labGrader, labGrader.category, 0.5),
        (midtermGrader, midtermGrader.category, 0.5)])

        #The midterm should have all weight on this one
        zeroWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.0), (labGrader, labGrader.category, 0.0),
        (midtermGrader, midtermGrader.category, 0.5)])

        #This should always have a final percent of zero
        allZeroWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.0), (labGrader, labGrader.category, 0.0),
        (midtermGrader, midtermGrader.category, 0.0)])

        emptyGrader = graders.WeightedSubsectionsGrader([])

        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = overOneWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.7688095238095238)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = zeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2525)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = allZeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        for graded in [weightedGrader.grade(self.empty_gradesheet),
                        weightedGrader.grade(self.incomplete_gradesheet),
                        zeroWeightsGrader.grade(self.empty_gradesheet),
                        allZeroWeightsGrader.grade(self.empty_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
            self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

    def test_graderFromConf(self):

        #Confs always produce a graders.WeightedSubsectionsGrader, so we test this by repeating the test
        #in test_graders.WeightedSubsectionsGrader, but generate the graders with confs.

        weightedGrader = graders.grader_from_conf([
            {
                'type': "Homework",
                'min_count': 12,
                'drop_count': 2,
                'short_label': "HW",
                'weight': 0.25,
            },
            {
                'type': "Lab",
                'min_count': 7,
                'drop_count': 3,
                'category': "Labs",
                'weight': 0.25
            },
            {
                'type': "Midterm",
                'name': "Midterm Exam",
                'short_label': "Midterm",
                'weight': 0.5,
            },
        ])

        emptyGrader = graders.grader_from_conf([])

        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

        #Test that graders can also be used instead of lists of dictionaries
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        homeworkGrader2 = graders.grader_from_conf(homeworkGrader)

        graded = homeworkGrader2.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        #TODO: How do we test failure cases? The parser only logs an error when it can't parse something. Maybe it should throw exceptions?

# --------------------------------------------------------------------------
# Module progress tests


class ProgressTest(unittest.TestCase):
    ''' Test that basic Progress objects work.  A Progress represents a
    fraction between 0 and 1.
    '''
    not_started = Progress(0, 17)
    part_done = Progress(2, 6)
    half_done = Progress(3, 6)
    also_half_done = Progress(1, 2)
    done = Progress(7, 7)

    def test_create_object(self):
        # These should work:
        p = Progress(0, 2)
        p = Progress(1, 2)
        p = Progress(2, 2)

        p = Progress(2.5, 5.0)
        p = Progress(3.7, 12.3333)

        # These shouldn't
        self.assertRaises(ValueError, Progress, 0, 0)
        self.assertRaises(ValueError, Progress, 2, 0)
        self.assertRaises(ValueError, Progress, 1, -2)

        self.assertRaises(TypeError, Progress, 0, "all")
        # check complex numbers just for the heck of it :)
        self.assertRaises(TypeError, Progress, 2j, 3)

    def test_clamp(self):
        self.assertEqual((2, 2), Progress(3, 2).frac())
        self.assertEqual((0, 2), Progress(-2, 2).frac())

    def test_frac(self):
        p = Progress(1, 2)
        (a, b) = p.frac()
        self.assertEqual(a, 1)
        self.assertEqual(b, 2)

    def test_percent(self):
        self.assertEqual(self.not_started.percent(), 0)
        self.assertAlmostEqual(self.part_done.percent(), 33.33333333333333)
        self.assertEqual(self.half_done.percent(), 50)
        self.assertEqual(self.done.percent(), 100)

        self.assertEqual(self.half_done.percent(), self.also_half_done.percent())

    def test_started(self):
        self.assertFalse(self.not_started.started())

        self.assertTrue(self.part_done.started())
        self.assertTrue(self.half_done.started())
        self.assertTrue(self.done.started())

    def test_inprogress(self):
        # only true if working on it
        self.assertFalse(self.done.inprogress())
        self.assertFalse(self.not_started.inprogress())

        self.assertTrue(self.part_done.inprogress())
        self.assertTrue(self.half_done.inprogress())

    def test_done(self):
        self.assertTrue(self.done.done())
        self.assertFalse(self.half_done.done())
        self.assertFalse(self.not_started.done())

    def test_str(self):
        self.assertEqual(str(self.not_started), "0/17")
        self.assertEqual(str(self.part_done), "2/6")
        self.assertEqual(str(self.done), "7/7")

    def test_ternary_str(self):
        self.assertEqual(self.not_started.ternary_str(), "none")
        self.assertEqual(self.half_done.ternary_str(), "in_progress")
        self.assertEqual(self.done.ternary_str(), "done")

    def test_to_js_status(self):
        '''Test the Progress.to_js_status_str() method'''

        self.assertEqual(Progress.to_js_status_str(self.not_started), "none")
        self.assertEqual(Progress.to_js_status_str(self.half_done), "in_progress")
        self.assertEqual(Progress.to_js_status_str(self.done), "done")
        self.assertEqual(Progress.to_js_status_str(None), "NA")

    def test_to_js_detail_str(self):
        '''Test the Progress.to_js_detail_str() method'''
        f = Progress.to_js_detail_str
        for p in (self.not_started, self.half_done, self.done):
            self.assertEqual(f(p), str(p))
        # But None should be encoded as NA
        self.assertEqual(f(None), "NA")

    def test_add(self):
        '''Test the Progress.add_counts() method'''
        p = Progress(0, 2)
        p2 = Progress(1, 3)
        p3 = Progress(2, 5)
        pNone = None
        add = lambda a, b: Progress.add_counts(a, b).frac()

        self.assertEqual(add(p, p), (0, 4))
        self.assertEqual(add(p, p2), (1, 5))
        self.assertEqual(add(p2, p3), (3, 8))

        self.assertEqual(add(p2, pNone), p2.frac())
        self.assertEqual(add(pNone, p2), p2.frac())

    def test_equality(self):
        '''Test that comparing Progress objects for equality
        works correctly.'''
        p = Progress(1, 2)
        p2 = Progress(2, 4)
        p3 = Progress(1, 2)
        self.assertTrue(p == p3)
        self.assertFalse(p == p2)

        # Check != while we're at it
        self.assertTrue(p != p2)
        self.assertFalse(p != p3)


class ModuleProgressTest(unittest.TestCase):
    ''' Test that get_progress() does the right thing for the different modules
    '''
    def test_xmodule_default(self):
        '''Make sure default get_progress exists, returns None'''
        xm = x_module.XModule(i4xs, 'a://b/c/d/e', None, {})
        p = xm.get_progress()
        self.assertEqual(p, None)
