# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS that test the completion aggregates as the learner progresses in the course
"""
from contextlib import contextmanager

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.lms.completion_aggregate import CompletionAggregatePage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage as StudioCourseOutlinePage
from common.test.acceptance.pages.studio.utils import drag
from common.test.acceptance.tests.helpers import UniqueCourseTest, auto_auth, create_multiple_choice_problem


class CompletionAggregatorTest(UniqueCourseTest):
    """
    Class for Completion Aggregator tests.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"
    SECTION_NAME = 'Test Section 1'
    SUBSECTION_NAME = 'Test Subsection 1'
    UNIT1_NAME = 'Test Unit 1'
    UNIT2_NAME = 'Test Unit 2'
    UNIT3_NAME = 'Test Unit 3'
    UNIT4_NAME = 'Test Unit 4'
    UNIT5_NAME = 'Test Unit 5'
    UNIT6_NAME = 'Test Unit 6'
    UNIT7_NAME = 'Test Unit 7'
    UNIT8_NAME = 'Test Unit 8'
    PROBLEM1_NAME = 'Test Problem 1'
    PROBLEM2_NAME = 'Test Problem 2'
    PROBLEM3_NAME = 'Test Problem 3'
    PROBLEM4_NAME = 'Test Problem 4'
    PROBLEM5_NAME = 'Test Problem 5'
    PROBLEM6_NAME = 'Test Problem 6'
    PROBLEM7_NAME = 'Test Problem 7'
    PROBLEM8_NAME = 'Test Problem 8'

    def setUp(self):
        super(CompletionAggregatorTest, self).setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.problem_page = ProblemPage(self.browser)
        self.logout_page = LogoutPage(self.browser)
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.completion_aggregation_list_page = CompletionAggregatePage(self.browser)
        self.completion_aggregation_detail_page = CompletionAggregatePage(self.browser, course_id=self.course_id)
        self.completion_aggregation_student_detail_page = CompletionAggregatePage(self.browser,
                                                                                  course_id=self.course_id,
                                                                                  username=self.USERNAME)

        self.studio_course_outline = StudioCourseOutlinePage(
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

        self.problem1 = create_multiple_choice_problem(self.PROBLEM1_NAME)
        self.problem2 = create_multiple_choice_problem(self.PROBLEM2_NAME)
        self.problem3 = create_multiple_choice_problem(self.PROBLEM3_NAME)
        self.problem4 = create_multiple_choice_problem(self.PROBLEM4_NAME)
        self.problem5 = create_multiple_choice_problem(self.PROBLEM5_NAME)
        self.problem6 = create_multiple_choice_problem(self.PROBLEM6_NAME)
        self.problem7 = create_multiple_choice_problem(self.PROBLEM7_NAME)
        self.problem8 = create_multiple_choice_problem(self.PROBLEM8_NAME)

        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', self.SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', self.SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT1_NAME).add_children(self.problem1),
                    XBlockFixtureDesc('vertical', self.UNIT2_NAME).add_children(self.problem2),
                    XBlockFixtureDesc('vertical', self.UNIT3_NAME).add_children(self.problem3),
                    XBlockFixtureDesc('vertical', self.UNIT4_NAME).add_children(self.problem4)
                ),
                XBlockFixtureDesc('sequential', self.SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT5_NAME).add_children(self.problem5),
                    XBlockFixtureDesc('vertical', self.UNIT6_NAME).add_children(self.problem6),
                    XBlockFixtureDesc('vertical', self.UNIT7_NAME).add_children(self.problem7),
                    XBlockFixtureDesc('vertical', self.UNIT8_NAME).add_children(self.problem8)
                )
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _answer_problem(self, problem_number, choice):
        """
        Submit the given choice for the problem.
        """
        self.courseware_page.go_to_sequential_position(problem_number)
        self.problem_page.click_choice('choice_choice_{}'.format(choice))
        self.problem_page.click_submit()

    def _get_completion_aggregate_detail(self):
        """
        Return the completion aggregate data
        """
        self.completion_aggregation_student_detail_page.visit()
        return self.completion_aggregation_student_detail_page.get_completion_data()

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

    def _delete_unit(self):
        """
        Deletes the first unit of the first subsection of the first section.
        """
        self.studio_course_outline.visit()
        self.studio_course_outline.section_at(0).subsection_at(0).expand_subsection()
        self.studio_course_outline.section_at(0).subsection_at(0).unit_at(0).delete()

    def _drag_unit_to_other_subsection(self):
        """
        Moves Unit 7 from subsection 2 to subsection 1.
        """
        self.studio_course_outline.visit()
        self.studio_course_outline.expand_all_subsections()
        drag(self.studio_course_outline, 4, 6)
        self.studio_course_outline.section(self.SECTION_NAME).publish()

    def test_aggregate_increases_with_attempts(self):
        """
        Tests that attempting the problems increments the completion.

        Scenario: Check that completion aggregates change when problems are attempted.
            Given that I am enrolled in a course with 2 subsections with 4 units+problems each.
            When I answer the second problem
            Then my completion aggregate should show 8 possible, 1 earned and 1/8 percent.
            When I answer the second problem
            Then my completion aggregate should show 8 possible, 2 earned and 2/8 percent.
        """
        with self._logged_in_session(staff=False):
            self.courseware_page.visit()
            self._answer_problem(problem_number=1, choice=2)

        with self._logged_in_session(staff=True):
            completion_data = self._get_completion_aggregate_detail()
            self.assertAlmostEqual(completion_data['possible'], 8.0)
            self.assertAlmostEqual(completion_data['earned'], 1.0)
            self.assertAlmostEqual(completion_data['percent'], 1.0 / 8.0)

        with self._logged_in_session(staff=False):
            self.courseware_page.visit()
            self._answer_problem(problem_number=2, choice=2)

        with self._logged_in_session(staff=True):
            completion_data = self._get_completion_aggregate_detail()
            self.assertAlmostEqual(completion_data['possible'], 8.0)
            self.assertAlmostEqual(completion_data['earned'], 2.0)
            self.assertAlmostEqual(completion_data['percent'], 2.0 / 8.0)

    def test_completion_aggregates_delete_unit(self):
        """
        Tests that deleting a unit changes the totals and aggregates.

        Scenario: Check that completion aggregates change when problems are attempted.
            Given that I am enrolled in a course with 2 subsections with 4 units+problems each.
            When I answer the second problem
            Then my completion aggregate should show 8 possible, 1 earned and 1/8 percent.
            When the staff changes the course and deletes the first problem
            And that leaves a total of 7 problems and changes the indexes of the problems
            When I answer the second problem (which was previously the third problem)
            Then my completion aggregate should show 7 possible, 2 earned and 2/7 percent.
        """
        with self._logged_in_session(staff=False):
            self.courseware_page.visit()
            self._answer_problem(problem_number=2, choice=2)

        with self._logged_in_session(staff=True):
            completion_data = self._get_completion_aggregate_detail()
            self.assertAlmostEqual(completion_data['possible'], 8.0)
            self.assertAlmostEqual(completion_data['earned'], 1.0)
            self.assertAlmostEqual(completion_data['percent'], 1.0 / 8.0)

        with self._logged_in_session(staff=True):
            self._delete_unit()

        with self._logged_in_session(staff=False):
            self.courseware_page.visit()
            self._answer_problem(problem_number=2, choice=2)

        with self._logged_in_session(staff=True):
            completion_data = self._get_completion_aggregate_detail()
            self.assertAlmostEqual(completion_data['possible'], 7.0)
            self.assertAlmostEqual(completion_data['earned'], 2.0)
            self.assertAlmostEqual(completion_data['percent'], 2.0 / 7.0)
