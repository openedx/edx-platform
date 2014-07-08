# -*- coding: utf-8 -*-
"""
E2E tests for the LMS.
"""
import time

from .helpers import UniqueCourseTest
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.studio.overview import CourseOutlinePage
from ..pages.lms.courseware import CoursewarePage
from ..pages.lms.problem import ProblemPage
from ..pages.common.logout import LogoutPage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc


class CoursewareTest(UniqueCourseTest):
    """
    Test courseware.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(CoursewareTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 2')
                )
            )
        ).install()

        # Auto-auth register for the course.
        self._auto_auth(self.USERNAME, self.EMAIL, False)

    def _goto_problem_page(self):
        """
        Open problem page with assertion.
        """
        self.courseware_page.visit()
        self.problem_page = ProblemPage(self.browser)
        self.assertEqual(self.problem_page.problem_name, 'TEST PROBLEM 1')

    def _change_problem_release_date_in_studio(self):
        """

        """
        self.course_outline.q(css=".subsection-header-actions .configure-button").first.click()
        self.course_outline.q(css="#start_date").fill("01/01/2015")
        self.course_outline.q(css=".action-save").first.click()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()


    def test_courseware(self):
        """
        Test courseware if recent visited subsection become unpublished.
        """

        # Visit problem page as a student.
        self._goto_problem_page()

        # Logout and login as a staff user.
        LogoutPage(self.browser).visit()
        self._auto_auth("STAFF_TESTER", "staff101@example.com", True)

        # Visit course outline page in studio.
        self.course_outline.visit()

        # Set release date for subsection in future.
        self._change_problem_release_date_in_studio()

        # Wait for 2 seconds to save new date.
        time.sleep(2)

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        self._auto_auth(self.USERNAME, self.EMAIL, False)

        # Visit courseware as a student.
        self.courseware_page.visit()

        # Problem name should be "TEST PROBLEM 2".
        self.assertEqual(self.problem_page.problem_name, 'TEST PROBLEM 2')
