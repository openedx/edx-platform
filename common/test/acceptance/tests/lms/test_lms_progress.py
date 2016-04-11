# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""
from textwrap import dedent
from ..helpers import UniqueCourseTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.progress import ProgressPage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.course_nav import CourseNavPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...fixtures.grading import GradingConfigFixture


class ProgressTest(UniqueCourseTest):
    """
    Test progress page.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(ProgressTest, self).setUp()

        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.courseware = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)

        problem = dedent("""
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

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc(
                    'sequential', 'Test Subsection 1', metadata={'graded': True, 'format': 'Homework'}
                ).add_children(
                    XBlockFixtureDesc(
                        'vertical', 'Test Vertical 1'
                    ).add_children(XBlockFixtureDesc('problem', 'Test Problem 1', data=problem)),
                ),
                XBlockFixtureDesc(
                    'sequential', 'Test Subsection 2', metadata={'graded': True, 'format': 'Homework'}
                ).add_children(
                    XBlockFixtureDesc(
                        'vertical', 'Test Vertical 2'
                    ).add_children(XBlockFixtureDesc('problem', 'Test Problem 3', data=problem)),
                ),
                XBlockFixtureDesc('sequential', 'Test Subsection 3').add_children(
                    XBlockFixtureDesc(
                        'vertical', 'Test Vertical 3'
                    ).add_children(XBlockFixtureDesc('problem', 'Test Problem 3', data=problem)),
                ),
            ),
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(
            self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id, staff=False
        ).visit()

    def check_problem(self, section, subsection, answer):
        """
        Opens the courseware page with a problem and passes it.
        """
        self.courseware.visit()
        self.course_nav.go_to_section(section, subsection)
        problem_page = ProblemPage(self.browser)
        problem_page.fill_answer(answer)
        problem_page.click_check()
        self.assertTrue(problem_page.is_correct())

    def set_assignments(self, assignments):
        """
        Configures assignment types for the course.
        """
        GradingConfigFixture(self.course_id, {'graders': assignments}).install()

    def test_passing_info_table_is_hidden_when_all_assignments_has_passing_grade_disabled(self):
        """
        Ensures that the passing information table is hidden when all Assignments has
        passing grade disabled.
        """
        self.set_assignments([
            {
                'type': 'Homework', 'weight': 50,
                'min_count': 2, 'drop_count': 0, 'short_label': 'HW',
                'passing_grade_enabled': False
            },
            {
                'type': 'Exam', 'weight': 50,
                'min_count': 1, 'drop_count': 0, 'short_label': 'EX',
                'passing_grade_enabled': False
            },
        ])

        self.progress_page.visit()
        self.assertFalse(self.progress_page.has_passing_information_table)

    def test_passing_info_table_is_visible(self):
        """
        Ensures that the passing information table is visible when at least one Assignment has
        passing grade enabled and it does not dispaly Assignments with passing grade disabled.
        """
        self.set_assignments([
            {
                'type': 'Homework', 'passing_grade': 70, 'weight': 50,
                'min_count': 2, 'drop_count': 0, 'short_label': 'HW',
                'passing_grade_enabled': True
            },
            {
                'type': 'Exam', 'weight': 50,
                'min_count': 1, 'drop_count': 0, 'short_label': 'EX',
                'passing_grade_enabled': False
            },
        ])

        self.progress_page.visit()
        self.assertTrue(self.progress_page.has_passing_information_table)
        self.assertEqual(
            self.progress_page.passing_information_table.status,
            [('Homework', '70', '0', 'Not pass')]
        )

    def test_passing_info_table_has_correct_values(self):
        """
        Scenario: Ensures that the passing information table has correct values
        Given I have a course with 2 categories ("Homework", "Exam")
        And "Homework" has passing grade "70" and contains 2 problems
        And "Exam" has passing grade disabled and contains 1 problem
        When I pass the 1st Homework's problem (current grade for the category is 50)
        And I go to the Progress page
        Then I see that "Homework" category is not passed in the passing information table
        When I pass the 2nd Homework's problem (current grade for the category is 100)
        And I go to the Progress page
        Then I see that "Homework" category is passed in the passing information table
        """
        self.set_assignments([
            {
                'type': 'Homework', 'passing_grade': 70, 'weight': 50,
                'min_count': 2, 'drop_count': 0, 'short_label': 'HW',
                'passing_grade_enabled': True
            },
            {
                'type': 'Exam', 'weight': 50,
                'min_count': 1, 'drop_count': 0, 'short_label': 'EX',
                'passing_grade_enabled': False
            },
        ])

        self.check_problem('Test Section 1', 'Test Subsection 1', answer='6.5')
        self.progress_page.visit()
        self.assertTrue(self.progress_page.has_passing_information_table)
        self.assertEqual(
            self.progress_page.passing_information_table.status,
            [('Homework', '70', '50', 'Not pass')]
        )

        self.check_problem('Test Section 1', 'Test Subsection 2', answer='6.5')
        self.progress_page.visit()
        self.assertTrue(self.progress_page.has_passing_information_table)
        self.assertEqual(
            self.progress_page.passing_information_table.status,
            [('Homework', '70', '100', 'Pass')]
        )
