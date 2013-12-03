import unittest
from lxml import etree
import os
import textwrap

import mock
# from random import Random
from .response_xml_factory import StringResponseXMLFactory, CustomResponseXMLFactory
from . import test_system, new_loncapa_problem

import ipdb

class CapaShuffleTest(unittest.TestCase):

    def setUp(self):
        super(CapaShuffleTest, self).setUp()
        self.system = test_system()

    # def test_no_answer_pool_4_choices(self):

    def test_answer_pool_4_choices_1_multiplechoiceresponse(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse answer-pool="4" targeted-feedback="alwaysShowCorrectChoiceExplanation">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="solution1w">wrong-1</choice>
                <choice correct="false" explanation-id="solution2w">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false" explanation-id="solution3w">wrong-3</choice>
                <choice correct="false" explanation-id="solution4w">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="solution1w">
                <div class="detailed-targeted-feedback" >
                    <p>Targeted Feedback</p>
                    <p>xThis is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="solution2w">
                <div class="detailed-targeted-feedback" >
                    <p>Targeted Feedback</p>
                    <p>xThis is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="solution3w">
                <div class="detailed-targeted-feedback" >
                    <p>Targeted Feedback</p>
                    <p>xThis is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="solution4w">
                <div class="detailed-targeted-feedback" >
                    <p>Targeted Feedback</p>
                    <p>xThis is the 4th WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="solution1">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution" >
                    <p>Explanation</p>
                    <p>xThis is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution" >
                    <p>Explanation</p>
                    <p>xThis is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        # problem = new_loncapa_problem(xml_str, seed=56)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 56
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_3'}

        the_html = problem.get_html()

        # print "\n\n"
        # print the_html
        # print "\n\n"

        # ipdb.set_trace()

        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-4'.*'wrong-3'.*'wrong-2'.*'correct-2'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"3rd WRONG")
        self.assertRegexpMatches(the_html, r"2nd solution")
        self.assertNotRegexpMatches(the_html, r"1st solution")

        # problem = new_loncapa_problem(xml_str)
        # rnd = Random()
        # ix = rnd.randint(0, 20)
        # problem.seed = ix
        # the_html = problem.get_html()

        # print the_html
        # self.assertEqual(1, 2)
        # self.assertRegexpMatches(the_html, r"<div>.*\[.*'A'.*'B'.*'C'.*\].*</div>.*")

# <problem>
            
#             <p>What is the correct answer?</p>
#             <multiplechoiceresponse answer-pool="4" targeted-feedback="alwaysShowCorrectChoiceExplanation">
#               <choicegroup type="MultipleChoice">
#                 <choice correct="false" explanation-id="solution1w">wrong-1</choice>
#                 <choice correct="false" explanation-id="solution2w">wrong-2</choice>
#                 <choice correct="true" explanation-id="solution1">correct-1</choice>
#                 <choice correct="false" explanation-id="solution3w">wrong-3</choice>
#                 <choice correct="false" explanation-id="solution4w">wrong-4</choice>
#                 <choice correct="true" explanation-id="solution2">correct-2</choice>
#               </choicegroup>
#             </multiplechoiceresponse>

#             <targetedfeedbackset>
#                 <targetedfeedback explanation-id="solution1w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>xThis is the 1st WRRRRRONG solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution2w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>xThis is the 2nd WRRRRRONG solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution3w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>xThis is the 3rd bad solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution4w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>xThis is the 4th bad solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution1">
#                 <div class="detailed-targeted-feedback-correct">
#                     <p>Targeted Feedback</p>
#                     <p>Feedback on your correct solution...</p>
#                 </div>
#                 </targetedfeedback>

#             </targetedfeedbackset>

#             <solutionset>
#                 <solution explanation-id="solution1">
#                 <div class="detailed-solution" >
#                     <p>Explanation</p>
#                     <p>xThis is the 1st solution</p>
#                     <p>Not much to explain here, sorry!</p>
#                 </div>
#                 </solution>

#                 <solution explanation-id="solution2">
#                 <div class="detailed-solution" >
#                     <p>Explanation</p>
#                     <p>xThis is the 2nd solution</p>
#                 </div>
#                 </solution>
#             </solutionset>

#             <p>What is the wrong answer?</p>
#             <multiplechoiceresponse answer-pool="4" targeted-feedback="alwaysShowCorrectChoiceExplanation">
#               <choicegroup type="MultipleChoice">
#                 <choice correct="false" explanation-id="solution1w">wrong-1</choice>
#                 <choice correct="false" explanation-id="solution2w">wrong-2</choice>
#                 <choice correct="true" explanation-id="solution1">correct-1</choice>
#                 <choice correct="false" explanation-id="solution3w">wrong-3</choice>
#                 <choice correct="false" explanation-id="solution4w">wrong-4</choice>
#                 <choice correct="true" explanation-id="solution2">correct-2</choice>
#               </choicegroup>
#             </multiplechoiceresponse>

#             <targetedfeedbackset>
#                 <targetedfeedback explanation-id="solution1w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>yThis is the 1st WRRRRRONG solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution2w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>yThis is the 2nd WRRRRRONG solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution3w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>yThis is the 3rd bad solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution4w">
#                 <div class="detailed-targeted-feedback" >
#                     <p>Targeted Feedback</p>
#                     <p>yThis is the 4th bad solution</p>
#                 </div>
#                 </targetedfeedback>

#                 <targetedfeedback explanation-id="solution1">
#                 <div class="detailed-targeted-feedback-correct">
#                     <p>Targeted Feedback</p>
#                     <p>Feedback on your correct solution...</p>
#                 </div>
#                 </targetedfeedback>    

#             </targetedfeedbackset>

#             <solutionset>
#                 <solution explanation-id="solution1">
#                 <div class="detailed-solution" >
#                     <p>Explanation</p>
#                     <p>This is the 1st solution</p>
#                     <p>yNot much to explain here, sorry!</p>
#                 </div>
#                 </solution>

#                 <solution explanation-id="solution2">
#                 <div class="detailed-solution" >
#                     <p>Explanation</p>
#                     <p>yThis is the 2nd solution</p>
#                 </div>
#                 </solution>
#             </solutionset>
#         </problem>