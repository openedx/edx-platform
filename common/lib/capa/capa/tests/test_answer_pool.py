"""
Tests the logic of the "answer-pool" attribute, e.g.
  <choicegroup answer-pool="4"
"""

import unittest
import textwrap
from . import test_capa_system, new_loncapa_problem
from capa.responsetypes import LoncapaProblemError


class CapaAnswerPoolTest(unittest.TestCase):
    '''
    Testing class
    '''

    def setUp(self):
        super(CapaAnswerPoolTest, self).setUp()
        self.system = test_capa_system()

    def test_answer_pool_4_choices_1_multiplechoiceresponse_seed1(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=723)
        the_html = problem.get_html()
        # [('choice_3', u'wrong-3'), ('choice_5', u'correct-2'), ('choice_1', u'wrong-2'), ('choice_4', u'wrong-4')]
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-3'.*'correct-2'.*'wrong-2'.*'wrong-4'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_2'.*\}</div>")
        self.assertEqual(the_html, problem.get_html(), 'should be able to call get_html() twice')
        self.assertIsNotNone(problem.tree.xpath('//choicegroup[@answer-pool-done="done"]'))
        # Check about masking
        response = problem.responders.values()[0]
        self.assertTrue(hasattr(response, 'is_masked'))
        self.assertEqual(response.unmask_order(), ['choice_3', 'choice_5', 'choice_1', 'choice_4'])

    def test_answer_pool_4_choices_1_multiplechoiceresponse_seed2(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=9)
        the_html = problem.get_html()
        # [('choice_0', u'wrong-1'), ('choice_4', u'wrong-4'), ('choice_3', u'wrong-3'), ('choice_2', u'correct-1')]
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-1'.*'wrong-4'.*'wrong-3'.*'correct-1'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertIsNotNone(problem.tree.xpath('//choicegroup[@answer-pool-done="done"]'))
        # Check about masking
        response = problem.responders.values()[0]
        self.assertTrue(hasattr(response, 'is_masked'))
        self.assertEqual(response.unmask_order(), ['choice_0', 'choice_4', 'choice_3', 'choice_2'])

    def test_no_answer_pool_4_choices_1_multiplechoiceresponse(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str)
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*'wrong-4'.*'correct-2'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_1'.*'1_solution_2'.*\}</div>")
        self.assertEqual(the_html, problem.get_html(), 'should be able to call get_html() twice')
        self.assertEquals(problem.tree.xpath('//choicegroup[@answer-pool-done="done"]'), [])
        # Check about masking
        response = problem.responders.values()[0]
        self.assertFalse(hasattr(response, 'is_masked'))

    def test_0_answer_pool_4_choices_1_multiplechoiceresponse(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="0">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str)
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*'wrong-4'.*'correct-2'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_1'.*'1_solution_2'.*\}</div>")
        self.assertEquals(problem.tree.xpath('//choicegroup[@answer-pool-done="done"]'), [])
        response = problem.responders.values()[0]
        self.assertFalse(hasattr(response, 'is_masked'))

    def test_invalid_answer_pool(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="2.3">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        with self.assertRaises(LoncapaProblemError):
            problem = new_loncapa_problem(xml_str)
            problem.get_html()

    def test_answer_pool_5_choices_1_multiplechoiceresponse_seed1(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="5">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=723)
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'correct-2'.*'wrong-1'.*'wrong-2'.*.*'wrong-3'.*'wrong-4'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_2'.*\}</div>")
        response = problem.responders.values()[0]
        self.assertTrue(hasattr(response, 'is_masked'))
        self.assertEqual(response.unmask_order(), ['choice_5', 'choice_0', 'choice_1', 'choice_3', 'choice_4'])

    def test_answer_pool_2_multiplechoiceresponses_seed1(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="3">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=723)
        the_html = problem.get_html()

        str1 = r"<div>.*\[.*'wrong-3'.*'correct-2'.*'wrong-2'.*'wrong-4'.*\].*</div>"
        str2 = r"<div>.*\[.*'wrong-2'.*'wrong-1'.*'correct-2'.*\].*</div>"
        str3 = r"<div>\{.*'1_solution_2'.*\}</div>"
        str4 = r"<div>\{.*'1_solution_4'.*\}</div>"

        self.assertRegexpMatches(the_html, str1)
        self.assertRegexpMatches(the_html, str2)
        self.assertRegexpMatches(the_html, str3)
        self.assertRegexpMatches(the_html, str4)

        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, str1 + r".*" + str2)
        self.assertRegexpMatches(without_new_lines, str3 + r".*" + str4)

    def test_answer_pool_2_multiplechoiceresponses_seed2(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="3">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=9)
        the_html = problem.get_html()

        str1 = r"<div>.*\[.*'wrong-4'.*'wrong-3'.*'correct-1'.*\].*</div>"
        str2 = r"<div>.*\[.*'wrong-2'.*'wrong-3'.*'wrong-4'.*'correct-2'.*\].*</div>"
        str3 = r"<div>\{.*'1_solution_1'.*\}</div>"
        str4 = r"<div>\{.*'1_solution_4'.*\}</div>"

        self.assertRegexpMatches(the_html, str1)
        self.assertRegexpMatches(the_html, str2)
        self.assertRegexpMatches(the_html, str3)
        self.assertRegexpMatches(the_html, str4)

        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, str1 + r".*" + str2)
        self.assertRegexpMatches(without_new_lines, str3 + r".*" + str4)

    def test_answer_pool_and_no_answer_pool(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solution>
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true" explanation-id="solution1">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true" explanation-id="solution2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solutionset>
                <solution explanation-id="solution1">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 1st solution</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>

                <solution explanation-id="solution2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the 2nd solution</p>
                </div>
                </solution>
            </solutionset>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=723)
        the_html = problem.get_html()

        str1 = r"<div>.*\[.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*'wrong-4'.*\].*</div>"
        str2 = r"<div>.*\[.*'wrong-3'.*'correct-2'.*'wrong-2'.*'wrong-4'.*\].*</div>"
        str3 = r"<div>\{.*'1_solution_1'.*\}</div>"
        str4 = r"<div>\{.*'1_solution_3'.*\}</div>"

        self.assertRegexpMatches(the_html, str1)
        self.assertRegexpMatches(the_html, str2)
        self.assertRegexpMatches(the_html, str3)
        self.assertRegexpMatches(the_html, str4)

        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, str1 + r".*" + str2)
        self.assertRegexpMatches(without_new_lines, str3 + r".*" + str4)

    def test_answer_pool_without_solutionset(self):
        xml_str = textwrap.dedent("""
            <problem>

            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true">correct-1</choice>
                <choice correct="false">wrong-3</choice>
                <choice correct="false">wrong-4</choice>
                <choice correct="true">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solution>
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>

        </problem>

        """)

        problem = new_loncapa_problem(xml_str, seed=723)
        the_html = problem.get_html()

        self.assertRegexpMatches(the_html, r"<div>.*\[.*'wrong-3'.*'correct-2'.*'wrong-2'.*'wrong-4'.*\].*</div>")
        self.assertRegexpMatches(the_html, r"<div>\{.*'1_solution_1'.*\}</div>")
