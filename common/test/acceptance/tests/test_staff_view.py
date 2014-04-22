# -*- coding: utf-8 -*-
"""
E2E tests for the LMS.
"""

from .helpers import UniqueCourseTest
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.lms.courseware import CoursewarePage
from ..pages.lms.staff_view import StaffPage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc
from textwrap import dedent


class StaffDebugTest(UniqueCourseTest):
    """
    Tests that verify the staff debug info.
    """

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
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=problem_data)
                )
            )
        ).install()

        # Auto-auth register for the course.
        # Do this as global staff so that you will see the Staff View
        AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit()

    def test_staff_debug(self):
        self.courseware_page.visit()
        staff_page = StaffPage(self.browser)
        self.assertEqual(staff_page.staff_status, 'Staff view')
        staff_debug_page = staff_page.open_staff_debug_info()
        staff_debug_page.reset_attempts()

        msg = staff_debug_page.idash_msg
        self.assertEqual('foo', msg) # Not sure what is supposed to happen
