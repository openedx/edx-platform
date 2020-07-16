# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS that utilize the course home page and course outline.
"""

from openedx.core.lib.tests import attr

from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.course_home import CourseHomePage
from ...pages.lms.courseware import CoursewarePage
from ..helpers import UniqueCourseTest, auto_auth, load_data_str


class CourseHomeBaseTest(UniqueCourseTest):
    """
    Provides base setup for course home tests.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(CourseHomeBaseTest, self).setUp()

        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections and problems
        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab', data=r"static tab data with mathjax \(E=mc^2\)"),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2'),
                XBlockFixtureDesc('sequential', 'Test Subsection 3').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem A', data=load_data_str('multiple_choice.xml'))
                ),
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)


@attr('a11y')
class CourseHomeA11yTest(CourseHomeBaseTest):
    """
    Tests the accessibility of the course home page
    """

    def test_course_home_a11y(self):
        """
        Test the accessibility of the course home page with course outline.
        """
        course_home_page = CourseHomePage(self.browser, self.course_id)
        course_home_page.visit()
        course_home_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
                'landmark-no-duplicate-banner',  # TODO: AC-934
            ]
        })
        course_home_page.a11y_audit.check_for_accessibility_errors()
