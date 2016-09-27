"""
Tests the logic of the "targeted-feedback" attribute for MultipleChoice questions,
i.e. those with the <multiplechoiceresponse> element
"""

import unittest
import textwrap
from . import test_capa_system, new_loncapa_problem, load_fixture


class CapaTargetedFeedbackTest(unittest.TestCase):
    '''
    Testing class
    '''

    def setUp(self):
        super(CapaTargetedFeedbackTest, self).setUp()
        self.system = test_capa_system()

    def test_no_targeted_feedback(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback2">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solution explanation-id="feedbackC">
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution explanation</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>
        </problem>

        """)

        problem = new_loncapa_problem(xml_str)

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, r"<div>.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*</div>")
        self.assertRegexpMatches(without_new_lines, r"feedback1|feedback2|feedback3|feedbackC")

    def test_targeted_feedback_not_finished(self):
        problem = new_loncapa_problem(load_fixture('targeted_feedback.xml'))
        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, r"<div>.*'wrong-1'.*'wrong-2'.*'correct-1'.*'wrong-3'.*</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback2|feedback3|feedbackC")
        self.assertEquals(the_html, problem.get_html(), "Should be able to call get_html() twice")

    def test_targeted_feedback_student_answer1(self):
        problem = new_loncapa_problem(load_fixture('targeted_feedback.xml'))
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_3'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback3\" role=\"group\" aria-describedby=\"1_2_1-legend\">\s*<span class=\"sr\">Incorrect</span>.*3rd WRONG solution")
        self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback2|feedbackC")
        # Check that calling it multiple times yields the same thing
        the_html2 = problem.get_html()
        self.assertEquals(the_html, the_html2)

    def test_targeted_feedback_student_answer2(self):
        problem = new_loncapa_problem(load_fixture('targeted_feedback.xml'))
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\" role=\"group\" aria-describedby=\"1_2_1-legend\">\s*<span class=\"sr\">Incorrect</span>.*1st WRONG solution")
        self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3|feedbackC")

    def test_targeted_feedback_correct_answer(self):
        """ Test the case of targeted feedback for a correct answer. """
        problem = new_loncapa_problem(load_fixture('targeted_feedback.xml'))
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_2'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines,
                                 r"<targetedfeedback explanation-id=\"feedbackC\" role=\"group\" aria-describedby=\"1_2_1-legend\">\s*<span class=\"sr\">Correct</span>.*Feedback on your correct solution...")
        self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback2|feedback3")

    def test_targeted_feedback_id_typos(self):
        """Cases where the explanation-id's don't match anything."""
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1TYPO">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackCTYPO">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback2">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solution explanation-id="feedbackC">
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution explanation</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>
        </problem>
        """)

        # explanation-id does not match anything: fall back to empty targetedfeedbackset
        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<targetedfeedbackset>\s*</targetedfeedbackset>")

        # New problem with same XML -- try the correct choice.
        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_2'}  # correct
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<targetedfeedbackset>\s*</targetedfeedbackset>")

    def test_targeted_feedback_no_solution_element(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="">
              <choicegroup type="MultipleChoice">
                <choice correct="false">wrong-1</choice>
                <choice correct="false">wrong-2</choice>
                <choice correct="true"  explanation-id="feedbackC">correct-1</choice>
                <choice correct="false">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                </div>
                </targetedfeedback>
            </targetedfeedbackset>
            </problem>
        """)

        # Solution element not found
        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_2'}
        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # </div> right after </targetedfeedbackset>
        self.assertRegexpMatches(
            without_new_lines,
            r"<div>.*<targetedfeedbackset>.*</targetedfeedbackset>\s*</div>"
        )

    def test_targeted_feedback_show_solution_explanation(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback2">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solution explanation-id="feedbackC">
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution explanation</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>
        </problem>

        """)

        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\" role=\"group\" aria-describedby=\"1_2_1-legend\">.*1st WRONG solution")
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
        self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3")
        # Check that calling it multiple times yields the same thing
        the_html2 = problem.get_html()
        self.assertEquals(the_html, the_html2)

    def test_targeted_feedback_no_show_solution_explanation(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback2">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solution explanation-id="feedbackC">
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>This is the solution explanation</p>
                <p>Not much to explain here, sorry!</p>
            </div>
            </solution>
        </problem>

        """)

        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\" role=\"group\" aria-describedby=\"1_2_1-legend\">.*1st WRONG solution")
        self.assertNotRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
        self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3|feedbackC")

    def test_targeted_feedback_with_solutionset_explanation(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
                <choice correct="true" explanation-id="feedbackC2">correct-2</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback2">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 2nd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC2">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on the other solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solutionset>
                <solution explanation-id="feedbackC2">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the other solution explanation</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>
            </solutionset>
        </problem>

        """)

        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # pylint: disable=line-too-long
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedback1\" role=\"group\" aria-describedby=\"1_2_1-legend\">.*1st WRONG solution")
        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC2\".*other solution explanation")
        self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback2|feedback3")

    def test_targeted_feedback_no_feedback_for_selected_choice1(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="alwaysShowCorrectChoiceExplanation">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solutionset>
                <solution explanation-id="feedbackC">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the solution explanation</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>
            </solutionset>
        </problem>

        """)

        # The student choses one with no feedback, but alwaysShowCorrectChoiceExplanation
        # is in force, so we should see the correct solution feedback.
        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_1'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")

        self.assertRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
        self.assertNotRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback3")

    def test_targeted_feedback_no_feedback_for_selected_choice2(self):
        xml_str = textwrap.dedent("""
            <problem>
            <p>What is the correct answer?</p>
            <multiplechoiceresponse targeted-feedback="">
              <choicegroup type="MultipleChoice">
                <choice correct="false" explanation-id="feedback1">wrong-1</choice>
                <choice correct="false" explanation-id="feedback2">wrong-2</choice>
                <choice correct="true" explanation-id="feedbackC">correct-1</choice>
                <choice correct="false" explanation-id="feedback3">wrong-3</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <targetedfeedbackset>
                <targetedfeedback explanation-id="feedback1">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 1st WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedback3">
                <div class="detailed-targeted-feedback">
                    <p>Targeted Feedback</p>
                    <p>This is the 3rd WRONG solution</p>
                </div>
                </targetedfeedback>

                <targetedfeedback explanation-id="feedbackC">
                <div class="detailed-targeted-feedback-correct">
                    <p>Targeted Feedback</p>
                    <p>Feedback on your correct solution...</p>
                </div>
                </targetedfeedback>

            </targetedfeedbackset>

            <solutionset>
                <solution explanation-id="feedbackC">
                <div class="detailed-solution">
                    <p>Explanation</p>
                    <p>This is the solution explanation</p>
                    <p>Not much to explain here, sorry!</p>
                </div>
                </solution>
            </solutionset>
        </problem>

        """)

        # The student chooses one with no feedback set, so we check that there's no feedback.
        problem = new_loncapa_problem(xml_str)
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_1'}

        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")

        self.assertNotRegexpMatches(without_new_lines, r"<targetedfeedback explanation-id=\"feedbackC\".*solution explanation")
        self.assertRegexpMatches(without_new_lines, r"<div>\{.*'1_solution_1'.*\}</div>")
        self.assertNotRegexpMatches(without_new_lines, r"feedback1|feedback3|feedbackC")

    def test_targeted_feedback_multiple_not_answered(self):
        # Not answered -> empty targeted feedback
        problem = new_loncapa_problem(load_fixture('targeted_feedback_multiple.xml'))
        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # Q1 and Q2 have no feedback
        self.assertRegexpMatches(
            without_new_lines,
            r'<targetedfeedbackset.*?>\s*</targetedfeedbackset>.*' +
            r'<targetedfeedbackset.*?>\s*</targetedfeedbackset>'
        )

    def test_targeted_feedback_multiple_answer_1(self):
        problem = new_loncapa_problem(load_fixture('targeted_feedback_multiple.xml'))
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0'}  # feedback1
        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # Q1 has feedback1 and Q2 has nothing
        self.assertRegexpMatches(
            without_new_lines,
            r'<targetedfeedbackset.*?>.*?explanation-id="feedback1".*?</targetedfeedbackset>.*' +
            r'<targetedfeedbackset.*?>\s*</targetedfeedbackset>'
        )

    def test_targeted_feedback_multiple_answer_2(self):
        problem = new_loncapa_problem(load_fixture('targeted_feedback_multiple.xml'))
        problem.done = True
        problem.student_answers = {'1_2_1': 'choice_0', '1_3_1': 'choice_2'}  # Q1 wrong, Q2 correct
        the_html = problem.get_html()
        without_new_lines = the_html.replace("\n", "")
        # Q1 has feedback1 and Q2 has feedbackC
        self.assertRegexpMatches(
            without_new_lines,
            r'<targetedfeedbackset.*?>.*?explanation-id="feedback1".*?</targetedfeedbackset>.*' +
            r'<targetedfeedbackset.*?>.*explanation-id="feedbackC".*?</targetedfeedbackset>'
        )
