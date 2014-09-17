# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""

from ..helpers import UniqueCourseTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.staff_view import StaffPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from textwrap import dedent


class StaffDebugTest(UniqueCourseTest):
    """
    Tests that verify the staff debug info.
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    def setUp(self):
        super(StaffDebugTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        problem_data = dedent("""
            <problem markdown="Simple Problem" max_attempts="" weight="">
              <p>Choose Yes.</p>
              <choiceresponse>
                <checkboxgroup direction="vertical">
                  <choice correct="true">Yes</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
        """)

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=problem_data),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=problem_data)
                )
            )
        ).install()

        # Auto-auth register for the course.
        # Do this as global staff so that you will see the Staff View
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=True).visit()

    def _goto_staff_page(self):
        """
        Open staff page with assertion
        """
        self.courseware_page.visit()
        staff_page = StaffPage(self.browser)
        self.assertEqual(staff_page.staff_status, 'Staff view')
        return staff_page

    def test_reset_attempts_empty(self):
        """
        Test that we reset even when there is no student state
        """

        staff_debug_page = self._goto_staff_page().open_staff_debug_info()
        staff_debug_page.reset_attempts()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully reset the attempts '
                         'for user {}'.format(self.USERNAME), msg)

    def test_delete_state_empty(self):
        """
        Test that we delete properly even when there isn't state to delete.
        """
        staff_debug_page = self._goto_staff_page().open_staff_debug_info()
        staff_debug_page.delete_state()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully deleted student state '
                         'for user {}'.format(self.USERNAME), msg)

    def test_reset_attempts_state(self):
        """
        Successfully reset the student attempts
        """
        staff_page = self._goto_staff_page()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.reset_attempts()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully reset the attempts '
                         'for user {}'.format(self.USERNAME), msg)

    def test_rescore_state(self):
        """
        Rescore the student
        """
        staff_page = self._goto_staff_page()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.rescore()
        msg = staff_debug_page.idash_msg[0]
        # Since we aren't running celery stuff, this will fail badly
        # for now, but is worth excercising that bad of a response
        self.assertEqual(u'Failed to rescore problem. '
                         'Unknown Error Occurred.', msg)

    def test_student_state_delete(self):
        """
        Successfully delete the student state with an answer
        """
        staff_page = self._goto_staff_page()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.delete_state()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully deleted student state '
                         'for user {}'.format(self.USERNAME), msg)

    def test_student_by_email(self):
        """
        Successfully reset the student attempts using their email address
        """
        staff_page = self._goto_staff_page()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.reset_attempts(self.EMAIL)
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully reset the attempts '
                         'for user {}'.format(self.EMAIL), msg)

    def test_bad_student(self):
        """
        Test negative response with invalid user
        """
        staff_page = self._goto_staff_page()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.delete_state('INVALIDUSER')
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Failed to delete student state. '
                         'User does not exist.', msg)

    def test_reset_attempts_for_problem_loaded_via_ajax(self):
        """
        Successfully reset the student attempts for problem loaded via ajax.
        """
        staff_page = self._goto_staff_page()
        staff_page.load_problem_via_ajax()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.reset_attempts()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully reset the attempts '
                         'for user {}'.format(self.USERNAME), msg)

    def test_rescore_state_for_problem_loaded_via_ajax(self):
        """
        Rescore the student for problem loaded via ajax.
        """
        staff_page = self._goto_staff_page()
        staff_page.load_problem_via_ajax()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.rescore()
        msg = staff_debug_page.idash_msg[0]
        # Since we aren't running celery stuff, this will fail badly
        # for now, but is worth excercising that bad of a response
        self.assertEqual(u'Failed to rescore problem. '
                         'Unknown Error Occurred.', msg)

    def test_student_state_delete_for_problem_loaded_via_ajax(self):
        """
        Successfully delete the student state for problem loaded via ajax.
        """
        staff_page = self._goto_staff_page()
        staff_page.load_problem_via_ajax()
        staff_page.answer_problem()

        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.delete_state()
        msg = staff_debug_page.idash_msg[0]
        self.assertEqual(u'Successfully deleted student state '
                         'for user {}'.format(self.USERNAME), msg)
