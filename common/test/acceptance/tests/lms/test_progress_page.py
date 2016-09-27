# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS that utilize the
progress page.
"""

from contextlib import contextmanager

import ddt

from ..helpers import UniqueCourseTest, auto_auth, create_multiple_choice_problem
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from lettuce import world
from nose.plugins.attrib import attr
from ...pages.common.logout import LogoutPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.progress import ProgressPage
from ...pages.studio.component_editor import ComponentEditorView
from ...pages.studio.utils import type_in_codemirror
from ...pages.studio.overview import CourseOutlinePage


class ProgressPageBaseTest(UniqueCourseTest):
    """
    Provides utility methods for tests retrieving
    scores from the progress page.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"
    SECTION_NAME = 'Test Section 1'
    SUBSECTION_NAME = 'Test Subsection 1'
    UNIT_NAME = 'Test Unit 1'
    PROBLEM_NAME = 'Test Problem 1'
    PROBLEM_NAME_2 = 'Test Problem 2'

    def setUp(self):
        super(ProgressPageBaseTest, self).setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.problem_page = ProblemPage(self.browser)  # pylint: disable=attribute-defined-outside-init
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.logout_page = LogoutPage(self.browser)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with problems
        self.course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', self.SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', self.SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT_NAME).add_children(
                        create_multiple_choice_problem(self.PROBLEM_NAME),
                        create_multiple_choice_problem(self.PROBLEM_NAME_2)
                    )
                )
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _answer_problem_correctly(self):
        """
        Submit a correct answer to the problem.
        """
        self.courseware_page.go_to_sequential_position(1)
        self.problem_page.click_choice('choice_choice_2')
        self.problem_page.click_check()

    def _get_section_score(self):
        """
        Return a list of scores from the progress page.
        """
        self.progress_page.visit()
        return self.progress_page.section_score(self.SECTION_NAME, self.SUBSECTION_NAME)

    def _get_problem_scores(self):
        """
        Return a list of scores from the progress page.
        """
        self.progress_page.visit()
        return self.progress_page.scores(self.SECTION_NAME, self.SUBSECTION_NAME)

    def _check_progress_page_with_scored_problem(self):
        """
        Checks the progress page before and after answering
        the course's first problem correctly.
        """
        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(0, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (0, 2))
            self.courseware_page.visit()
            self._answer_problem_correctly()
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))

    @contextmanager
    def _logged_in_session(self, staff=False):
        """
        Ensure that the user is logged in and out appropriately at the beginning
        and end of the current test.
        """
        self.logout_page.visit()
        try:
            if staff:
                auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
            else:
                auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
            yield
        finally:
            self.logout_page.visit()


class ProgressPageTest(ProgressPageBaseTest):
    """
    Test that the progress page reports scores from completed assessments.
    """
    def test_progress_page_shows_scored_problems(self):
        self._check_progress_page_with_scored_problem()


@ddt.ddt
class PersistentGradesTest(ProgressPageBaseTest):
    """
    Test that grades for completed assessments are persisted
    when various edits are made.
    """
    def setUp(self):
        super(PersistentGradesTest, self).setUp()
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)

    def _change_subsection_structure(self):
        """
        Adds a unit to the subsection, which
        should not affect a persisted subsection grade.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            subsection = self.course_outline.section(self.SECTION_NAME).subsection(self.SUBSECTION_NAME)
            subsection.expand_subsection()
            subsection.add_unit()

    def _set_staff_lock_on_subsection(self, locked):
        """
        Sets staff lock for a subsection, which should hide the
        subsection score from students on the progress page.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            subsection = self.course_outline.section_at(0).subsection_at(0)
            subsection.set_staff_lock(locked)
            self.assertEqual(subsection.has_staff_lock_warning, locked)

    def _change_weight_for_problem(self):
        """
        Changes the weight of the problem, which should not affect
        persisted grades.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            self.course_outline.section_at(0).subsection_at(0).expand_subsection()
            unit = self.course_outline.section_at(0).subsection_at(0).unit(self.UNIT_NAME).go_to()
            component = unit.xblocks[1]
            component.edit()
            component_editor = ComponentEditorView(self.browser, component.locator)
            component_editor.set_field_value_and_save('Problem Weight', 5)

    def _edit_problem_content(self):
        """
        Replaces the content of a problem with other html.
        Should not affect persisted grades.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            self.course_outline.section_at(0).subsection_at(0).expand_subsection()
            unit = self.course_outline.section_at(0).subsection_at(0).unit(self.UNIT_NAME).go_to()
            component = unit.xblocks[1]
            modal = component.edit()

            # Set content in the CodeMirror editor.
            modified_content = "<p>modified content</p>"
            type_in_codemirror(self, 0, modified_content)
            modal.q(css='.action-save').click()

    @ddt.data(
        _edit_problem_content,
        _change_subsection_structure,
        _change_weight_for_problem
    )
    def test_content_changes_do_not_change_score(self, edit):
        with self._logged_in_session():
            self._check_progress_page_with_scored_problem()

        edit(self)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))

    def test_visibility_change_does_affect_score(self):
        with self._logged_in_session():
            self._check_progress_page_with_scored_problem()

        self._set_staff_lock_on_subsection(True)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), None)
            self.assertEqual(self._get_section_score(), None)

        self._set_staff_lock_on_subsection(False)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))


class SubsectionGradingPolicyTest(ProgressPageBaseTest):
    """
    Tests changing a subsection's 'graded' field
    and the effect it has on the progress page.
    """
    def setUp(self):
        super(SubsectionGradingPolicyTest, self).setUp()
        self._set_policy_for_subsection("Homework")

    def _set_policy_for_subsection(self, policy):
        """
        Set the grading policy for the
        subsection in the test.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            modal = self.course_outline.section_at(0).subsection_at(0).edit()
            modal.policy = policy
            modal.save()

    def _check_scores_and_page_text(self, problem_scores, section_score, text):
        """
        Asserts that the given problem and section scores, and text,
        appear on the progress page.
        """
        self.assertEqual(self._get_problem_scores(), problem_scores)
        self.assertEqual(self._get_section_score(), section_score)
        self.assertTrue(self.progress_page.text_on_page(text))

    def _check_for_sr_text_in_chart(self):
        """
        Ensures we have at least one .sr text in the graph.
        We can assume if there's one, the JS is working correctly.
        """
        selector = 'grade-detail-graph'
        graph_container = self.progress_page.q(css='#' + selector)[0]
        self.assertTrue("Necessary screenreader element not found!", graph_container.find_element_by_class_name('sr'))

    def test_subsection_grading_policy_on_progress_page(self):
        with self._logged_in_session():
            self._check_scores_and_page_text([(0, 1), (0, 1)], (0, 2), "Homework 1 - Test Subsection 1 - 0% (0/2)")
            self.courseware_page.visit()
            self._answer_problem_correctly()
            self._check_scores_and_page_text([(1, 1), (0, 1)], (1, 2), "Homework 1 - Test Subsection 1 - 50% (1/2)")

        self._set_policy_for_subsection("Not Graded")

        with self._logged_in_session():
            self.progress_page.visit()
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))
            self.assertFalse(self.progress_page.text_on_page("Homework 1 - Test Subsection 1"))
            self._check_for_sr_text_in_chart()

        self._set_policy_for_subsection("Homework")

        with self._logged_in_session():
            self._check_scores_and_page_text([(1, 1), (0, 1)], (1, 2), "Homework 1 - Test Subsection 1 - 50% (1/2)")


@attr('a11y')
class ProgressPageA11yTest(ProgressPageBaseTest):
    """
    Class to test the accessibility of the progress page.
    """

    def test_progress_page_a11y(self):
        """
        Test the accessibility of the progress page.
        """
        self.progress_page.visit()
        self.progress_page.a11y_audit.check_for_accessibility_errors()
