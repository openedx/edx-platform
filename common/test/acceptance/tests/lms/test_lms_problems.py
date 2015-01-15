# -*- coding: utf-8 -*-
"""
Bok choy acceptance tests for problems in the LMS

See also old lettuce tests in lms/djangoapps/courseware/features/problems.feature
"""
from ..helpers import UniqueCourseTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.problem import ProblemPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from textwrap import dedent


class ProblemsTest(UniqueCourseTest):
    """
    Base class for tests of problems in the LMS.
    """
    USERNAME = "joe_student"
    EMAIL = "joe@example.com"

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
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()

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
