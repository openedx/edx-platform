# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS that utilize the
progress page.
"""
import ddt

from bok_choy.javascript import js_defined
from contextlib import contextmanager
from nose.plugins.attrib import attr

from ..helpers import (
    UniqueCourseTest, auto_auth, create_multiple_choice_problem, create_multiple_choice_xml, get_modal_alert
)
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.common.logout import LogoutPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage, StudentSpecificAdmin
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

        self.problem1 = create_multiple_choice_problem(self.PROBLEM_NAME)
        self.problem2 = create_multiple_choice_problem(self.PROBLEM_NAME_2)

        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', self.SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', self.SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT_NAME).add_children(self.problem1, self.problem2)
                )
            ),
            XBlockFixtureDesc('chapter', "Lab Section").add_children(
                XBlockFixtureDesc('sequential', "Lab Subsection").add_children(
                    XBlockFixtureDesc('vertical', "Lab Unit").add_children(
                        create_multiple_choice_problem("Lab Exercise")
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
        self._answer_problem(choice=2)

    def _answer_problem(self, choice):
        """
        Submit the given choice for the problem.
        """
        self.courseware_page.go_to_sequential_position(1)
        self.problem_page.click_choice('choice_choice_{}'.format(choice))
        self.problem_page.click_submit()

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


@ddt.ddt
@js_defined('window.jQuery')
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
        self.course_outline.visit()
        subsection = self.course_outline.section(self.SECTION_NAME).subsection(self.SUBSECTION_NAME)
        subsection.expand_subsection()
        subsection.add_unit()
        subsection.publish()

    def _set_staff_lock_on_subsection(self, locked):
        """
        Sets staff lock for a subsection, which should hide the
        subsection score from students on the progress page.
        """
        self.course_outline.visit()
        subsection = self.course_outline.section_at(0).subsection_at(0)
        subsection.set_staff_lock(locked)
        self.assertEqual(subsection.has_staff_lock_warning, locked)

    def _get_problem_in_studio(self):
        """
        Returns the editable problem component in studio,
        along with its container unit, so any changes can
        be published.
        """
        self.course_outline.visit()
        self.course_outline.section_at(0).subsection_at(0).expand_subsection()
        unit = self.course_outline.section_at(0).subsection_at(0).unit(self.UNIT_NAME).go_to()
        component = unit.xblocks[1]
        return unit, component

    def _change_weight_for_problem(self):
        """
        Changes the weight of the problem, which should not affect
        persisted grades.
        """
        unit, component = self._get_problem_in_studio()
        component.edit()
        component_editor = ComponentEditorView(self.browser, component.locator)
        component_editor.set_field_value_and_save('Problem Weight', 5)
        unit.publish()

    def _change_correct_answer_for_problem(self, new_correct_choice=1):
        """
        Changes the correct answer of the problem.
        """
        unit, component = self._get_problem_in_studio()
        modal = component.edit()

        modified_content = create_multiple_choice_xml(correct_choice=new_correct_choice)

        type_in_codemirror(self, 0, modified_content)
        modal.q(css='.action-save').click()
        unit.publish()

    def _student_admin_action_for_problem(self, action_button, has_cancellable_alert=False):
        """
        As staff, clicks the "delete student state" button,
        deleting the student user's state for the problem.
        """
        self.instructor_dashboard_page.visit()
        student_admin_section = self.instructor_dashboard_page.select_student_admin(StudentSpecificAdmin)
        student_admin_section.set_student_email_or_username(self.USERNAME)
        student_admin_section.set_problem_location(self.problem1.locator)
        getattr(student_admin_section, action_button).click()
        if has_cancellable_alert:
            alert = get_modal_alert(student_admin_section.browser)
            alert.accept()
        alert = get_modal_alert(student_admin_section.browser)
        alert.dismiss()
        return student_admin_section

    def test_progress_page_shows_scored_problems(self):
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

    @ddt.data(
        _change_correct_answer_for_problem,
        _change_subsection_structure,
        _change_weight_for_problem
    )
    def test_content_changes_do_not_change_score(self, edit):
        with self._logged_in_session():
            self.courseware_page.visit()
            self._answer_problem_correctly()

        with self._logged_in_session(staff=True):
            edit(self)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))

    def test_visibility_change_affects_score(self):
        with self._logged_in_session():
            self.courseware_page.visit()
            self._answer_problem_correctly()

        with self._logged_in_session(staff=True):
            self._set_staff_lock_on_subsection(True)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), None)
            self.assertEqual(self._get_section_score(), None)

        with self._logged_in_session(staff=True):
            self._set_staff_lock_on_subsection(False)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(1, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (1, 2))

    def test_delete_student_state_affects_score(self):
        with self._logged_in_session():
            self.courseware_page.visit()
            self._answer_problem_correctly()

        with self._logged_in_session(staff=True):
            self._student_admin_action_for_problem('delete_state_button', has_cancellable_alert=True)

        with self._logged_in_session():
            self.assertEqual(self._get_problem_scores(), [(0, 1), (0, 1)])
            self.assertEqual(self._get_section_score(), (0, 2))


class SubsectionGradingPolicyTest(ProgressPageBaseTest):
    """
    Tests changing a subsection's 'graded' field
    and the effect it has on the progress page.
    """
    def setUp(self):
        super(SubsectionGradingPolicyTest, self).setUp()
        self._set_policy_for_subsection("Homework", 0)
        self._set_policy_for_subsection("Lab", 1)

    def _set_policy_for_subsection(self, policy, section=0):
        """
        Set the grading policy for the first subsection in the specified section.
        If a section index is not provided, 0 is assumed.
        """
        with self._logged_in_session(staff=True):
            self.course_outline.visit()
            modal = self.course_outline.section_at(section).subsection_at(0).edit()
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

    def _check_tick_text(self, index, sr_text, label, label_hidden=True):
        """
        Check the label and sr text for a horizontal (X-axis) tick.
        """
        self.assertEqual(sr_text, self.progress_page.x_tick_sr_text(index))
        self.assertEqual([label, 'true' if label_hidden else None], self.progress_page.x_tick_label(index))

    def test_axis_a11y(self):
        """
        Tests that the progress chart axes have appropriate a11y (screenreader) markup.
        """
        with self._logged_in_session():
            self.courseware_page.visit()
            # Answer the first HW problem (the unit contains 2 problems, only one will be answered correctly)
            self._answer_problem_correctly()
            self.courseware_page.click_next_button_on_top()
            # Answer the first Lab problem (unit only contains a single problem)
            self._answer_problem_correctly()
            self.progress_page.visit()

            # Verify that y-Axis labels are aria-hidden
            self.assertEqual(['100%', 'true'], self.progress_page.y_tick_label(0))
            self.assertEqual(['0%', 'true'], self.progress_page.y_tick_label(1))
            self.assertEqual(['Pass 50%', 'true'], self.progress_page.y_tick_label(2))

            # Verify x-Axis labels and sr-text
            self._check_tick_text(0, [u'Homework 1 - Test Subsection 1 - 50% (1/2)'], u'HW 01')

            # Homeworks 2-10 are checked in the for loop below.

            self._check_tick_text(
                10,
                [u'Homework 11 Unreleased - 0% (?/?)', u'The lowest 2 Homework scores are dropped.'],
                u'HW 11'
            )

            self._check_tick_text(
                11,
                [u'Homework 12 Unreleased - 0% (?/?)', u'The lowest 2 Homework scores are dropped.'],
                u'HW 12'
            )

            self._check_tick_text(12, [u'Homework Average = 5%'], u'HW Avg')
            self._check_tick_text(13, [u'Lab 1 - Lab Subsection - 100% (1/1)'], u'Lab 01')

            # Labs 2-10 are checked in the for loop below.

            self._check_tick_text(
                23,
                [u'Lab 11 Unreleased - 0% (?/?)', u'The lowest 2 Lab scores are dropped.'],
                u'Lab 11'
            )
            self._check_tick_text(
                24,
                [u'Lab 12 Unreleased - 0% (?/?)', u'The lowest 2 Lab scores are dropped.'],
                u'Lab 12'
            )

            self._check_tick_text(25, [u'Lab Average = 10%'], u'Lab Avg')
            self._check_tick_text(26, [u'Midterm Exam = 0%'], u'Midterm')
            self._check_tick_text(27, [u'Final Exam = 0%'], u'Final')

            self._check_tick_text(
                28,
                [u'Homework = 0.75% of a possible 15.00%', u'Lab = 1.50% of a possible 15.00%'],
                u'Total',
                False  # The label "Total" should NOT be aria-hidden
            )

            # The grading policy has 12 Homeworks and 12 Labs. Most of them are unpublished,
            # with no additional information.
            for i in range(1, 10):
                self._check_tick_text(
                    i,
                    [u'Homework {index} Unreleased - 0% (?/?)'.format(index=i + 1)],
                    u'HW 0{index}'.format(index=i + 1) if i < 9 else u'HW {index}'.format(index=i + 1)
                )
                self._check_tick_text(
                    i + 13,
                    [u'Lab {index} Unreleased - 0% (?/?)'.format(index=i + 1)],
                    u'Lab 0{index}'.format(index=i + 1) if i < 9 else u'Lab {index}'.format(index=i + 1)
                )

            # Verify the overall score. The first element in the array is the sr-only text, and the
            # second is the total text (including the sr-only text).
            self.assertEqual(['Overall Score', 'Overall Score\n2%'], self.progress_page.graph_overall_score())

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
