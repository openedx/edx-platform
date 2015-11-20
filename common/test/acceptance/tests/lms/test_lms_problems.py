# -*- coding: utf-8 -*-
"""
Bok choy acceptance tests for problems in the LMS

See also old lettuce tests in lms/djangoapps/courseware/features/problems.feature
"""
from textwrap import dedent

from ..helpers import UniqueCourseTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.login_and_register import CombinedLoginAndRegisterPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ..helpers import EventsTestMixin


class ProblemsTest(UniqueCourseTest):
    """
    Base class for tests of problems in the LMS.
    """
    USERNAME = "joe_student"
    EMAIL = "joe@example.com"
    PASSWORD = "keep it secret; keep it safe."

    def setUp(self):
        super(ProblemsTest, self).setUp()

        self.xqueue_grade_response = None

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with a hierarchy and problems
        course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        problem = self.get_problem()
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(problem)
            )
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(
            self.browser,
            username=self.USERNAME,
            email=self.EMAIL,
            password=self.PASSWORD,
            course_id=self.course_id,
            staff=False
        ).visit()

    def get_problem(self):
        """ Subclasses should override this to complete the fixture """
        raise NotImplementedError()


class ProblemClarificationTest(ProblemsTest):
    """
    Tests the <clarification> element that can be used in problem XML.
    """

    def get_problem(self):
        """
        Create a problem with a <clarification>
        """
        xml = dedent("""
            <problem markdown="null">
                <text>
                    <p>
                        Given the data in Table 7 <clarification>Table 7: "Example PV Installation Costs",
                        Page 171 of Roberts textbook</clarification>, compute the ROI
                        <clarification>Return on Investment <strong>(per year)</strong></clarification> over 20 years.
                    </p>
                    <numericalresponse answer="6.5">
                        <textline label="Enter the annual ROI" trailing_text="%" />
                    </numericalresponse>
                </text>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'TOOLTIP TEST PROBLEM', data=xml)

    def test_clarification(self):
        """
        Test that we can see the <clarification> tooltips.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name, 'TOOLTIP TEST PROBLEM')
        problem_page.click_clarification(0)
        self.assertIn('"Example PV Installation Costs"', problem_page.visible_tooltip_text)
        problem_page.click_clarification(1)
        tooltip_text = problem_page.visible_tooltip_text
        self.assertIn('Return on Investment', tooltip_text)
        self.assertIn('per year', tooltip_text)
        self.assertNotIn('strong', tooltip_text)


class ProblemExtendedHintTest(ProblemsTest, EventsTestMixin):
    """
    Test that extended hint features plumb through to the page html and tracking log.
    """

    def get_problem(self):
        """
        Problem with extended hint features.
        """
        xml = dedent("""
            <problem>
            <p>question text</p>
            <stringresponse answer="A">
                <stringequalhint answer="B">hint</stringequalhint>
                <textline size="20"/>
            </stringresponse>
            <demandhint>
              <hint>demand-hint1</hint>
              <hint>demand-hint2</hint>
            </demandhint>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'TITLE', data=xml)

    def test_check_hint(self):
        """
        Test clicking Check shows the extended hint in the problem message.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_text[0], u'question text')
        problem_page.fill_answer('B')
        problem_page.click_check()
        self.assertEqual(problem_page.message_text, u'Incorrect: hint')
        # Check for corresponding tracking event
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.problem.hint.feedback_displayed'},
            number_of_matches=1
        )
        self.assert_events_match(
            [{'event': {'hint_label': u'Incorrect',
                        'trigger_type': 'single',
                        'student_answer': [u'B'],
                        'correctness': False,
                        'question_type': 'stringresponse',
                        'hints': [{'text': 'hint'}]}}],
            actual_events)

    def test_demand_hint(self):
        """
        Test clicking hint button shows the demand hint in its div.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        # The hint button rotates through multiple hints
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (1 of 2): demand-hint1')
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (2 of 2): demand-hint2')
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (1 of 2): demand-hint1')
        # Check corresponding tracking events
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.problem.hint.demandhint_displayed'},
            number_of_matches=3
        )
        self.assert_events_match(
            [
                {'event': {u'hint_index': 0, u'hint_len': 2, u'hint_text': u'demand-hint1'}},
                {'event': {u'hint_index': 1, u'hint_len': 2, u'hint_text': u'demand-hint2'}},
                {'event': {u'hint_index': 0, u'hint_len': 2, u'hint_text': u'demand-hint1'}}
            ],
            actual_events)


class ProblemHintWithHtmlTest(ProblemsTest, EventsTestMixin):
    """
    Tests that hints containing html get rendered properly
    """

    def get_problem(self):
        """
        Problem with extended hint features.
        """
        xml = dedent("""
            <problem>
            <p>question text</p>
            <stringresponse answer="A">
                <stringequalhint answer="C"><a href="#">aa bb</a> cc</stringequalhint>
                <textline size="20"/>
            </stringresponse>
            <demandhint>
              <hint>aa <a href="#">bb</a> cc</hint>
              <hint><a href="#">dd  ee</a> ff</hint>
            </demandhint>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'PROBLEM HTML HINT TEST', data=xml)

    def test_check_hint(self):
        """
        Test clicking Check shows the extended hint in the problem message.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_text[0], u'question text')
        problem_page.fill_answer('C')
        problem_page.click_check()
        self.assertEqual(problem_page.message_text, u'Incorrect: aa bb cc')
        # Check for corresponding tracking event
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.problem.hint.feedback_displayed'},
            number_of_matches=1
        )
        self.assert_events_match(
            [{'event': {'hint_label': u'Incorrect',
                        'trigger_type': 'single',
                        'student_answer': [u'C'],
                        'correctness': False,
                        'question_type': 'stringresponse',
                        'hints': [{'text': '<a href="#">aa bb</a> cc'}]}}],
            actual_events)

    def test_demand_hint(self):
        """
        Test clicking hint button shows the demand hint in its div.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        # The hint button rotates through multiple hints
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (1 of 2): aa bb cc')
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (2 of 2): dd ee ff')
        problem_page.click_hint()
        self.assertEqual(problem_page.hint_text, u'Hint (1 of 2): aa bb cc')
        # Check corresponding tracking events
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.problem.hint.demandhint_displayed'},
            number_of_matches=3
        )
        self.assert_events_match(
            [
                {'event': {u'hint_index': 0, u'hint_len': 2, u'hint_text': u'aa <a href="#">bb</a> cc'}},
                {'event': {u'hint_index': 1, u'hint_len': 2, u'hint_text': u'<a href="#">dd  ee</a> ff'}},
                {'event': {u'hint_index': 0, u'hint_len': 2, u'hint_text': u'aa <a href="#">bb</a> cc'}}
            ],
            actual_events)


class ProblemWithMathjax(ProblemsTest):
    """
    Tests the <MathJax> used in problem
    """

    def get_problem(self):
        """
        Create a problem with a <MathJax> in body and hint
        """
        xml = dedent(r"""
            <problem>
                <p>Check mathjax has rendered [mathjax]E=mc^2[/mathjax]</p>
                <multiplechoiceresponse>
                  <choicegroup label="Answer this?" type="MultipleChoice">
                    <choice correct="true">Choice1 <choicehint>Correct choice message</choicehint></choice>
                    <choice correct="false">Choice2<choicehint>Wrong choice message</choicehint></choice>
                  </choicegroup>
                </multiplechoiceresponse>
                <demandhint>
                        <hint>mathjax should work1 \(E=mc^2\) </hint>
                        <hint>mathjax should work2 [mathjax]E=mc^2[/mathjax]</hint>
                </demandhint>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'MATHJAX TEST PROBLEM', data=xml)

    def test_mathjax_in_hint(self):
        """
        Test that MathJax have successfully rendered in problem hint
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name, "MATHJAX TEST PROBLEM")

        problem_page.verify_mathjax_rendered_in_problem()

        # The hint button rotates through multiple hints
        problem_page.click_hint()
        self.assertIn("Hint (1 of 2): mathjax should work1", problem_page.hint_text)
        problem_page.verify_mathjax_rendered_in_hint()

        # Rotate the hint and check the problem hint
        problem_page.click_hint()

        self.assertIn("Hint (2 of 2): mathjax should work2", problem_page.hint_text)
        problem_page.verify_mathjax_rendered_in_hint()


class ProblemPartialCredit(ProblemsTest):
    """
    Makes sure that the partial credit is appearing properly.
    """
    def get_problem(self):
        """
        Create a problem with partial credit.
        """
        xml = dedent("""
            <problem>
                <p>The answer is 1. Partial credit for -1.</p>
                <numericalresponse answer="1" partial_credit="list">
                    <formulaequationinput label="How many miles away from Earth is the sun? Use scientific notation to answer." />
                    <responseparam type="tolerance" default="0.01" />
                    <responseparam partial_answers="-1" />
                </numericalresponse>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'PARTIAL CREDIT TEST PROBLEM', data=xml)

    def test_partial_credit(self):
        """
        Test that we can see the partial credit value and feedback.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        problem_page.wait_for_element_visibility(problem_page.CSS_PROBLEM_HEADER, 'wait for problem header')
        self.assertEqual(problem_page.problem_name, 'PARTIAL CREDIT TEST PROBLEM')
        problem_page.fill_answer_numerical('-1')
        problem_page.click_check()
        problem_page.wait_for_status_icon()
        self.assertTrue(problem_page.simpleprob_is_partially_correct())


class LogoutDuringAnswering(ProblemsTest):
    """
    Tests for the scenario where a user is logged out (their session expires
    or is revoked) just before they click "check" on a problem.
    """
    def get_problem(self):
        """
        Create a problem.
        """
        xml = dedent("""
            <problem>
                <p>The answer is 1</p>
                <numericalresponse answer="1">
                    <formulaequationinput label="where are the songs of spring?" />
                    <responseparam type="tolerance" default="0.01" />
                </numericalresponse>
            </problem>
        """)
        return XBlockFixtureDesc('problem', 'TEST PROBLEM', data=xml)

    def log_user_out(self):
        """
        Log the user out by deleting their session cookie.
        """
        self.browser.delete_cookie('sessionid')

    def test_logout_after_click_redirect(self):
        """
        1) User goes to a problem page.
        2) User fills out an answer to the problem.
        3) User is logged out because their session id is invalidated or removed.
        4) User clicks "check", and sees a confirmation modal asking them to
           re-authenticate, since they've just been logged out.
        5) User clicks "ok".
        6) User is redirected to the login page.
        7) User logs in.
        8) User is redirected back to the problem page they started out on.
        9) User is able to submit an answer
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name, 'TEST PROBLEM')
        problem_page.fill_answer_numerical('1')

        self.log_user_out()
        with problem_page.handle_alert(confirm=True):
            problem_page.click_check()

        login_page = CombinedLoginAndRegisterPage(self.browser)
        login_page.wait_for_page()

        login_page.login(self.EMAIL, self.PASSWORD)

        problem_page.wait_for_page()
        self.assertEqual(problem_page.problem_name, 'TEST PROBLEM')

        problem_page.fill_answer_numerical('1')
        problem_page.click_check()
        self.assertTrue(problem_page.simpleprob_is_correct())

    def test_logout_cancel_no_redirect(self):
        """
        1) User goes to a problem page.
        2) User fills out an answer to the problem.
        3) User is logged out because their session id is invalidated or removed.
        4) User clicks "check", and sees a confirmation modal asking them to
           re-authenticate, since they've just been logged out.
        5) User clicks "cancel".
        6) User is not redirected to the login page.
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name, 'TEST PROBLEM')
        problem_page.fill_answer_numerical('1')
        self.log_user_out()
        with problem_page.handle_alert(confirm=False):
            problem_page.click_check()

        self.assertTrue(problem_page.is_browser_on_page())
        self.assertEqual(problem_page.problem_name, 'TEST PROBLEM')
