"""
Tests the logic of problems with a delay between attempt submissions
"""

import unittest
import textwrap
import datetime
import json
import random
import os
import textwrap
import unittest

from mock import Mock, patch
import webob
from webob.multidict import MultiDict

import xmodule
from xmodule.tests import DATA_DIR
from capa.responsetypes import (StudentInputError, LoncapaProblemError,
                                ResponseError)
from capa.xqueue_interface import XQueueInterface
from xmodule.capa_module import CapaModule, ComplexEncoder
from xmodule.modulestore import Location
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from . import get_test_system
from pytz import UTC
from capa.correctmap import CorrectMap


class CapaFactory(object):
    """
    A helper class to create problem modules with various parameters for testing.
    """

    sample_problem_xml = textwrap.dedent("""\
        <?xml version="1.0"?>
        <problem>
            <text>
                <p>What is pi, to two decimal places?</p>
            </text>
        <numericalresponse answer="3.14">
        <textline math="1" size="30"/>
        </numericalresponse>
        </problem>
    """)

    num = 0

    @classmethod
    def next_num(cls):
        cls.num += 1
        return cls.num

    @classmethod
    def input_key(cls, input_num=2):
        """
        Return the input key to use when passing GET parameters
        """
        return ("input_" + cls.answer_key(input_num))

    @classmethod
    def answer_key(cls, input_num=2):
        """
        Return the key stored in the capa problem answer dict
        """
        return (
            "%s_%d_1" % (
                "-".join(['i4x', 'edX', 'capa_test', 'problem', 'SampleProblem%d' % cls.num]),
                input_num,
            )
        )

    @classmethod
    def create(cls,
               graceperiod=None,
               due=None,
               max_attempts=None,
               showanswer=None,
               rerandomize=None,
               force_save_button=None,
               attempts=None,
               problem_state=None,
               correct=False,
               done=None,
               text_customization=None
               ):
        """
        All parameters are optional, and are added to the created problem if specified.

        Arguments:
            graceperiod:
            due:
            max_attempts:
            showanswer:
            force_save_button:
            rerandomize: all strings, as specified in the policy for the problem

            problem_state: a dict to to be serialized into the instance_state of the
                module.

            attempts: also added to instance state.  Will be converted to an int.
        """
        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(cls.next_num())])
        field_data = {'data': cls.sample_problem_xml}

        if graceperiod is not None:
            field_data['graceperiod'] = graceperiod
        if due is not None:
            field_data['due'] = due
        if max_attempts is not None:
            field_data['max_attempts'] = max_attempts
        if showanswer is not None:
            field_data['showanswer'] = showanswer
        if force_save_button is not None:
            field_data['force_save_button'] = force_save_button
        if rerandomize is not None:
            field_data['rerandomize'] = rerandomize
        if done is not None:
            field_data['done'] = done
        if text_customization is not None:
            field_data['text_customization'] = text_customization

        descriptor = Mock(weight="1")
        if problem_state is not None:
            field_data.update(problem_state)
        if attempts is not None:
            # converting to int here because I keep putting "0" and "1" in the tests
            # since everything else is a string.
            field_data['attempts'] = int(attempts)

        system = get_test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaModule(
            descriptor,
            system,
            DictFieldData(field_data),
            ScopeIds(None, None, location, location),
        )

        if correct:
            # TODO: probably better to actually set the internal state properly, but...
            module.get_score = lambda: {'score': 1, 'total': 1}
        else:
            module.get_score = lambda: {'score': 0, 'total': 1}

        return module

class XModuleQuizAttemptsDelayTest(unittest.TestCase):
    '''
    Testing class
    '''

    def setUp(self):
        now = datetime.datetime.now(UTC)
        day_delta = datetime.timedelta(days=1)
        self.yesterday_str = str(now - day_delta)
        self.today_str = str(now)
        self.tomorrow_str = str(now + day_delta)

        # in the capa grace period format, not in time delta format
        self.two_day_delta_str = "2 days"

    def test_check_problem_resubmitted_with_randomize(self):
        rerandomize_values = ['always', 'true']

        for rerandomize in rerandomize_values:
            # Randomize turned on
            module = CapaFactory.create(rerandomize=rerandomize, attempts=0)

            # Simulate that the problem is completed
            module.done = True

            # Expect that we cannot submit
            with self.assertRaises(xmodule.exceptions.NotFoundError):
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                module.check_problem(get_request_dict)

            # Expect that number of attempts NOT incremented
            self.assertEqual(module.attempts, 0)

    # def test_reset_problem(self):
    #     module = CapaFactory.create(done=True)
    #     module.new_lcp = Mock(wraps=module.new_lcp)
    #     module.choose_new_seed = Mock(wraps=module.choose_new_seed)

    #     # Stub out HTML rendering
    #     with patch('xmodule.capa_module.CapaModule.get_problem_html') as mock_html:
    #         mock_html.return_value = "<div>Test HTML</div>"

    #         # Reset the problem
    #         get_request_dict = {}
    #         result = module.reset_problem(get_request_dict)

    #     # Expect that the request was successful
    #     self.assertTrue('success' in result and result['success'])

    #     # Expect that the problem HTML is retrieved
    #     self.assertTrue('html' in result)
    #     self.assertEqual(result['html'], "<div>Test HTML</div>")

    #     # Expect that the problem was reset
    #     module.new_lcp.assert_called_once_with(None)

    # def test_targeted_feedback_not_finished(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solution explanation-id="feedbackC">
    #         <div class="detailed-solution">
    #             <p>Explanation</p>
    #             <p>This is the solution explanation</p>
    #             <p>Not much to explain here, sorry!</p>
    #         </div>
    #         </solution>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<div>.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback2|feedback3|feedbackC")

    # def test_targeted_feedback_student_answer1(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solution explanation-id="feedbackC">
    #         <div class="detailed-solution">
    #             <p>Explanation</p>
    #             <p>This is the solution explanation</p>
    #             <p>Not much to explain here, sorry!</p>
    #         </div>
    #         </solution>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_3'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback3\">.*3rd WRONG solution")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback2|feedbackC")

    # def test_targeted_feedback_student_answer2(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solution explanation-id="feedbackC">
    #         <div class="detailed-solution">
    #             <p>Explanation</p>
    #             <p>This is the solution explanation</p>
    #             <p>Not much to explain here, sorry!</p>
    #         </div>
    #         </solution>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_0'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\">.*1st WRONG solution")
    #     self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3|feedbackC")

    # def test_targeted_feedback_show_solution_explanation(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solution explanation-id="feedbackC">
    #         <div class="detailed-solution">
    #             <p>Explanation</p>
    #             <p>This is the solution explanation</p>
    #             <p>Not much to explain here, sorry!</p>
    #         </div>
    #         </solution>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_0'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\">.*1st WRONG solution")
    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
    #     self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3")

    # def test_targeted_feedback_no_show_solution_explanation(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solution explanation-id="feedbackC">
    #         <div class="detailed-solution">
    #             <p>Explanation</p>
    #             <p>This is the solution explanation</p>
    #             <p>Not much to explain here, sorry!</p>
    #         </div>
    #         </solution>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_0'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\">.*1st WRONG solution")
    #     self.assertNotRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
    #     self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3|feedbackC")

    # def test_targeted_feedback_with_solutionset_explanation(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #             <choice correct="true" explanation-id="feedbackC2">correct-2</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback2">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 2nd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC2">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on the other solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solutionset>
    #             <solution explanation-id="feedbackC2">
    #             <div class="detailed-solution">
    #                 <p>Explanation</p>
    #                 <p>This is the other solution explanation</p>
    #                 <p>Not much to explain here, sorry!</p>
    #             </div>
    #             </solution>
    #         </solutionset>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_0'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\">.*1st WRONG solution")
    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC2\".*other solution explanation")
    #     self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3")

    # def test_targeted_feedback_no_feedback_for_selected_choice1(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solutionset>
    #             <solution explanation-id="feedbackC">
    #             <div class="detailed-solution">
    #                 <p>Explanation</p>
    #                 <p>This is the solution explanation</p>
    #                 <p>Not much to explain here, sorry!</p>
    #             </div>
    #             </solution>
    #         </solutionset>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_1'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
    #     self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback3")

    # def test_targeted_feedback_no_feedback_for_selected_choice2(self):
    #     xml_str = textwrap.dedent("""
    #         <problem>
    #         <p>What is the correct answer?</p>
    #         <multiplechoiceresponse targeted-feedback="">
    #           <choicegroup type="MultipleChoice">
    #             <choice correct="false" explanation-id="feedback1">wrong-1</choice>
    #             <choice correct="false" explanation-id="feedback2">wrong-2</choice>
    #             <choice correct="true" explanation-id="feedbackC">correct-1</choice>
    #             <choice correct="false" explanation-id="feedback3">wrong-3</choice>
    #           </choicegroup>
    #         </multiplechoiceresponse>

    #         <targetedfeedbackset>
    #             <targetedfeedback explanation-id="feedback1">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 1st WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedback3">
    #             <div class="detailed-targeted-feedback">
    #                 <p>Targeted Feedback</p>
    #                 <p>This is the 3rd WRONG solution</p>
    #             </div>
    #             </targetedfeedback>

    #             <targetedfeedback explanation-id="feedbackC">
    #             <div class="detailed-targeted-feedback-correct">
    #                 <p>Targeted Feedback</p>
    #                 <p>Feedback on your correct solution...</p>
    #             </div>
    #             </targetedfeedback>

    #         </targetedfeedbackset>

    #         <solutionset>
    #             <solution explanation-id="feedbackC">
    #             <div class="detailed-solution">
    #                 <p>Explanation</p>
    #                 <p>This is the solution explanation</p>
    #                 <p>Not much to explain here, sorry!</p>
    #             </div>
    #             </solution>
    #         </solutionset>
    #     </problem>

    #     """)

    #     problem = new_loncapa_problem(xml_str)
    #     problem.done = True
    #     problem.student_answers = {'1_2_1': 'choice_1'}

    #     the_html = problem.get_html()
    #     without_new_lines = the_html.replace("\n", "")

    #     self.assertNotRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
    #     self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
    #     self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback3|feedbackC")