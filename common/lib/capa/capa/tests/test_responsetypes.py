"""
Tests of responsetypes
"""


from datetime import datetime
import json
from nose.plugins.skip import SkipTest
import os
import unittest

from . import test_system

import capa.capa_problem as lcp
from capa.correctmap import CorrectMap
from capa.util import convert_files_to_filenames
from capa.xqueue_interface import dateformat


class MultiChoiceTest(unittest.TestCase):
    def test_MC_grade(self):
        multichoice_file = os.path.dirname(__file__) + "/test_files/multichoice.xml"
        test_lcp = lcp.LoncapaProblem(open(multichoice_file).read(), '1', system=test_system)
        correct_answers = {'1_2_1': 'choice_foil3'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        false_answers = {'1_2_1': 'choice_foil2'}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')

    def test_MC_bare_grades(self):
        multichoice_file = os.path.dirname(__file__) + "/test_files/multi_bare.xml"
        test_lcp = lcp.LoncapaProblem(open(multichoice_file).read(), '1', system=test_system)
        correct_answers = {'1_2_1': 'choice_2'}
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')
        false_answers = {'1_2_1': 'choice_1'}
        self.assertEquals(test_lcp.grade_answers(false_answers).get_correctness('1_2_1'), 'incorrect')

    def test_TF_grade(self):
        truefalse_file = os.path.dirname(__file__) + "/test_files/truefalse.xml"
        test_lcp = lcp.LoncapaProblem(open(truefalse_file).read(), '1', system=test_system)
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
        test_lcp = lcp.LoncapaProblem(open(imageresponse_file).read(), '1', system=test_system)
        # testing regions only
        correct_answers = {
           #regions
           '1_2_1': '(490,11)-(556,98)',
           '1_2_2': '(242,202)-(296,276)',
           '1_2_3': '(490,11)-(556,98);(242,202)-(296,276)',
           '1_2_4': '(490,11)-(556,98);(242,202)-(296,276)',
           '1_2_5': '(490,11)-(556,98);(242,202)-(296,276)',
           #testing regions and rectanges
           '1_3_1': 'rectangle="(490,11)-(556,98)" \
           regions="[[[10,10], [20,10], [20, 30]], [[100,100], [120,100], [120,150]]]"',
           '1_3_2': 'rectangle="(490,11)-(556,98)" \
           regions="[[[10,10], [20,10], [20, 30]], [[100,100], [120,100], [120,150]]]"',
           '1_3_3': 'regions="[[[10,10], [20,10], [20, 30]], [[100,100], [120,100], [120,150]]]"',
           '1_3_4': 'regions="[[[10,10], [20,10], [20, 30]], [[100,100], [120,100], [120,150]]]"',
           '1_3_5': 'regions="[[[10,10], [20,10], [20, 30]]]"',
           '1_3_6': 'regions="[[10,10], [30,30], [15, 15]]"',
           '1_3_7': 'regions="[[10,10], [30,30], [10, 30], [30, 10]]"',
                          }
        test_answers = {
            '1_2_1': '[500,20]',
            '1_2_2': '[250,300]',
            '1_2_3': '[500,20]',
            '1_2_4': '[250,250]',
            '1_2_5': '[10,10]',

            '1_3_1': '[500,20]',
            '1_3_2': '[15,15]',
            '1_3_3': '[500,20]',
            '1_3_4': '[115,115]',
            '1_3_5': '[15,15]',
            '1_3_6': '[20,20]',
            '1_3_7': '[20,15]',
                        }

        # regions
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_2'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_3'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_4'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_5'), 'incorrect')

        # regions and rectangles
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_2'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_3'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_4'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_5'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_6'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_7'), 'correct')


class SymbolicResponseTest(unittest.TestCase):
    def test_sr_grade(self):
        raise SkipTest()  # This test fails due to dependencies on a local copy of snuggletex-webapp. Until we have figured that out, we'll just skip this test
        symbolicresponse_file = os.path.dirname(__file__) + "/test_files/symbolicresponse.xml"
        test_lcp = lcp.LoncapaProblem(open(symbolicresponse_file).read(), '1', system=test_system)
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
        test_lcp = lcp.LoncapaProblem(open(optionresponse_file).read(), '1', system=test_system)
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
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=test_system)
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
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=test_system)
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
        """
        Simple test of whether LoncapaProblem knows when it's been queued
        """
        problem_file = os.path.join(os.path.dirname(__file__), "test_files/coderesponse.xml")
        with open(problem_file) as input_file:
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=test_system)

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
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=test_system)

            answer_ids = sorted(test_lcp.get_question_answers())

            # CodeResponse requires internal CorrectMap state. Build it now in the queued state
            old_cmap = CorrectMap()
            for i, answer_id in enumerate(answer_ids):
                queuekey = 1000 + i
                queuestate = CodeResponseTest.make_queuestate(1000 + i, datetime.now())
                old_cmap.update(CorrectMap(answer_id=answer_ids[i], queuestate=queuestate))

            # Message format common to external graders
            grader_msg = '<span>MESSAGE</span>'   # Must be valid XML
            correct_score_msg = json.dumps({'correct': True, 'score': 1, 'msg': grader_msg})
            incorrect_score_msg = json.dumps({'correct': False, 'score': 0, 'msg': grader_msg})

            xserver_msgs = {'correct': correct_score_msg,
                            'incorrect': incorrect_score_msg, }

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
                    npoints = 1 if correctness == 'correct' else 0
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
            test_lcp = lcp.LoncapaProblem(input_file.read(), '1', system=test_system)

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
                queuestate = CodeResponseTest.make_queuestate(1000 + i, latest_timestamp)
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
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=test_system)
        correct_answers = {'1_2_1': 'choice_2',
                           '1_3_1': ['choice_2', 'choice_3']}
        test_answers = {'1_2_1': 'choice_2',
                        '1_3_1': 'choice_2',
                        }
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_2_1'), 'correct')
        self.assertEquals(test_lcp.grade_answers(test_answers).get_correctness('1_3_1'), 'incorrect')

    def test_cr_cb_grade(self):
        problem_file = os.path.dirname(__file__) + "/test_files/choiceresponse_checkbox.xml"
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=test_system)
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
        test_lcp = lcp.LoncapaProblem(open(problem_file).read(), '1', system=test_system)
        correct_answers = {'1_2_1': json.dumps({0: 4})}
        incorrect_answers = {'1_2_1': json.dumps({0: 5})}

        self.assertEquals(test_lcp.grade_answers(incorrect_answers).get_correctness('1_2_1'), 'incorrect')
        self.assertEquals(test_lcp.grade_answers(correct_answers).get_correctness('1_2_1'), 'correct')

from response_xml_factory import NumericalResponseXMLFactory
class NumericalResponseTest(unittest.TestCase):

    def setUp(self):
        self.xml_factory = NumericalResponseXMLFactory()
    
    def test_grade_exact(self):
        xml = self.xml_factory.build_xml(question_text="What is 2 + 2?",
                                        explanation="The answer is 4",
                                        answer=4)
        correct_responses = ["4", "4.0", "4.00"]
        incorrect_responses = ["", "3.9", "4.1", "0"]
        self._test_grading(xml, correct_responses, incorrect_responses)
        

    def test_grade_decimal_tolerance(self):
        xml = self.xml_factory.build_xml(question_text="What is 2 + 2 approximately?",
                                        explanation="The answer is 4",
                                        answer=4,
                                        tolerance=0.1)
        correct_responses = ["4.0", "4.00", "4.09", "3.91"] 
        incorrect_responses = ["", "4.11", "3.89", "0"]
        self._test_grading(xml, correct_responses, incorrect_responses)
                        
    def test_grade_percent_tolerance(self):
        xml = self.xml_factory.build_xml(question_text="What is 2 + 2 approximately?",
                                        explanation="The answer is 4",
                                        answer=4,
                                        tolerance="10%")
        correct_responses = ["4.0", "4.3", "3.7", "4.30", "3.70"]
        incorrect_responses = ["", "4.5", "3.5", "0"]
        self._test_grading(xml, correct_responses, incorrect_responses)

    def test_grade_with_script(self):
        script_text = "computed_response = math.sqrt(4)"
        xml = self.xml_factory.build_xml(question_text="What is sqrt(4)?",
                                        explanation="The answer is 2",
                                        answer="$computed_response",
                                        script=script_text)
        correct_responses = ["2", "2.0"]
        incorrect_responses = ["", "2.01", "1.99", "0"]
        self._test_grading(xml, correct_responses, incorrect_responses)

    def test_grade_with_script_and_tolerance(self):
        script_text = "computed_response = math.sqrt(4)"
        xml = self.xml_factory.build_xml(question_text="What is sqrt(4)?",
                                        explanation="The answer is 2",
                                        answer="$computed_response",
                                        tolerance="0.1",
                                        script=script_text)
        correct_responses = ["2", "2.0", "2.05", "1.95"]
        incorrect_responses = ["", "2.11", "1.89", "0"]
        self._test_grading(xml, correct_responses, incorrect_responses)


    def _test_grading(self, xml, correct_answers, incorrect_answers):

        problem = lcp.LoncapaProblem(xml, '1', system=test_system)

        for input_str in correct_answers:
            result = problem.grade_answers({'1_2_1': input_str}).get_correctness('1_2_1')
            self.assertEqual(result, 'correct')

        for input_str in incorrect_answers:
            result = problem.grade_answers({'1_2_1': input_str}).get_correctness('1_2_1')
            self.assertEqual(result, 'incorrect')

from response_xml_factory import CustomResponseXMLFactory
class CustomResponseTest(unittest.TestCase):

    def setUp(self):
        self.xml_factory = CustomResponseXMLFactory()

    def test_inline_code(self):

        # For inline code, we directly modify global context variables
        # 'answers' is a list of answers provided to us
        # 'correct' is a list we fill in with True/False
        # 'expect' is given to us (if provided in the XML)
        inline_script = """correct[0] = 'correct' if (answers['1_2_1'] == expect) else 'incorrect'"""

        xml = self.xml_factory.build_xml(answer=inline_script, expect="42")

        problem = lcp.LoncapaProblem(xml, '1', system=test_system)

        # Correct answer
        input_dict = {'1_2_1': '42'}
        result = problem.grade_answers(input_dict).get_correctness('1_2_1')
        self.assertEqual(result, 'correct')

        # Incorrect answer
        input_dict = {'1_2_1': '0'}
        result = problem.grade_answers(input_dict).get_correctness('1_2_1')
        self.assertEqual(result, 'incorrect')

    def test_inline_message(self):

        # Inline code can update the global messages list
        # to pass messages to the CorrectMap for a particular input
        inline_script = """messages[0] = "Test Message" """

        xml = self.xml_factory.build_xml(answer=inline_script)
        problem = lcp.LoncapaProblem(xml, '1', system=test_system)

        input_dict = {'1_2_1': '0'}
        msg = problem.grade_answers(input_dict).get_msg('1_2_1')
        self.assertEqual(msg, "Test Message")

    def test_function_code(self):

        # For function code, we pass in three arguments:
        # 
        #   'expect' is the expect attribute of the <customresponse>
        #
        #   'answer_given' is the answer the student gave (if there is just one input)
        #       or an ordered list of answers (if there are multiple inputs)
        #   
        #   'student_answers' is a dictionary of answers by input ID
        #
        #
        # The function should return a dict of the form 
        # { 'ok': BOOL, 'msg': STRING }
        #
        script = """def check_func(expect, answer_given, student_answers):
    return {'ok': answer_given == expect, 'msg': 'Message text'}"""

        xml = self.xml_factory.build_xml(script=script, cfn="check_func", expect="42")
        problem = lcp.LoncapaProblem(xml, '1', system=test_system)

        # Correct answer
        input_dict = {'1_2_1': '42'}
        correct_map = problem.grade_answers(input_dict)

        correctness = correct_map.get_correctness('1_2_1')
        msg = correct_map.get_msg('1_2_1')

        self.assertEqual(correctness, 'correct')
        self.assertEqual(msg, "Message text\n")

        # Incorrect answer
        input_dict = {'1_2_1': '0'}
        correct_map = problem.grade_answers(input_dict)

        correctness = correct_map.get_correctness('1_2_1')
        msg = correct_map.get_msg('1_2_1')

        self.assertEqual(correctness, 'incorrect')
        self.assertEqual(msg, "Message text\n")

    def test_multiple_inputs(self):
        # When given multiple inputs, the 'answer_given' argument
        # to the check_func() is a list of inputs
        # The sample script below marks the problem as correct
        # if and only if it receives answer_given=[1,2,3]
        # (or string values ['1','2','3'])
        script = """def check_func(expect, answer_given, student_answers):
    check1 = (int(answer_given[0]) == 1)
    check2 = (int(answer_given[1]) == 2)
    check3 = (int(answer_given[2]) == 3)
    return {'ok': (check1 and check2 and check3),  'msg': 'Message text'}"""

        xml = self.xml_factory.build_xml(script=script, 
                                        cfn="check_func", num_inputs=3)
        problem = lcp.LoncapaProblem(xml, '1', system=test_system)

        # Grade the inputs (one input incorrect)
        input_dict = {'1_2_1': '-999', '1_2_2': '2', '1_2_3': '3' }
        correct_map = problem.grade_answers(input_dict)

        # Everything marked incorrect
        self.assertEqual(correct_map.get_correctness('1_2_1'), 'incorrect')
        self.assertEqual(correct_map.get_correctness('1_2_2'), 'incorrect')
        self.assertEqual(correct_map.get_correctness('1_2_3'), 'incorrect')

        # Grade the inputs (everything correct)
        input_dict = {'1_2_1': '1', '1_2_2': '2', '1_2_3': '3' }
        correct_map = problem.grade_answers(input_dict)

        # Everything marked incorrect
        self.assertEqual(correct_map.get_correctness('1_2_1'), 'correct')
        self.assertEqual(correct_map.get_correctness('1_2_2'), 'correct')
        self.assertEqual(correct_map.get_correctness('1_2_3'), 'correct')
