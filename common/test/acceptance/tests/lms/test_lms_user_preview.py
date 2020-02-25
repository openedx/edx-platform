# -*- coding: utf-8 -*-
"""
Tests the "preview" selector in the LMS that allows changing between Staff, Learner, and Content Groups.
"""


from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.pages.lms.staff_view import StaffCoursewarePage
from common.test.acceptance.tests.helpers import UniqueCourseTest, create_user_partition_json
from openedx.core.lib.tests import attr
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID, MINIMUM_STATIC_PARTITION_ID, Group


@attr(shard=20)
class StaffViewTest(UniqueCourseTest):
    """
    Tests that verify the staff view.
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    def setUp(self):
        super(StaffViewTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections/problems, tabs, updates, and handouts
        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.populate_course_fixture(self.course_fixture)

        self.course_fixture.install()

        # Auto-auth register for the course.
        # Do this as global staff so that you will see the Staff View
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=True).visit()

    def _goto_staff_page(self):
        """
        Open staff page with assertion
        """
        self.courseware_page.visit()
        staff_page = StaffCoursewarePage(self.browser, self.course_id)
        self.assertEqual(staff_page.staff_view_mode, 'Staff')
        return staff_page


@attr(shard=20)
class CourseWithoutContentGroupsTest(StaffViewTest):
    """
    Setup for tests that have no content restricted to specific content groups.
    """

    def populate_course_fixture(self, course_fixture):
        """
        Populates test course with chapter, sequential, and 2 problems.
        """
        problem_data = dedent("""
            <problem markdown="Simple Problem" max_attempts="" weight="">
              <p>Choose Yes.</p>
              <choiceresponse>
                <checkboxgroup>
                  <choice correct="true">Yes</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
        """)

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=problem_data),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=problem_data)
                )
            )
        )


@attr(shard=20)
class StaffViewToggleTest(CourseWithoutContentGroupsTest):
    """
    Tests for the staff view toggle button.
    """
    def test_instructor_tab_visibility(self):
        """
        Test that the instructor tab is hidden when viewing as a student.
        """

        course_page = self._goto_staff_page()
        self.assertTrue(course_page.has_tab('Instructor'))
        course_page.set_staff_view_mode('Learner')
        self.assertEqual(course_page.staff_view_mode, 'Learner')
        self.assertFalse(course_page.has_tab('Instructor'))


class CourseWithContentGroupsTest(StaffViewTest):
    """
    Verifies that changing the "View this course as" selector works properly for content groups.
    """

    def setUp(self):
        super(CourseWithContentGroupsTest, self).setUp()
        # pylint: disable=protected-access
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        MINIMUM_STATIC_PARTITION_ID,
                        'Configuration alpha,beta',
                        'Content Group Partition',
                        [
                            Group(MINIMUM_STATIC_PARTITION_ID + 1, 'alpha'),
                            Group(MINIMUM_STATIC_PARTITION_ID + 2, 'beta')
                        ],
                        scheme="cohort"
                    )
                ],
            },
        })

    def populate_course_fixture(self, course_fixture):
        """
        Populates test course with chapter, sequential, and 3 problems.
        One problem is visible to all, one problem is visible only to Group "alpha", and
        one problem is visible only to Group "beta".
        """
        problem_data = dedent("""
            <problem markdown="Simple Problem" max_attempts="" weight="">
              <choiceresponse>
              <label>Choose Yes.</label>
                <checkboxgroup>
                  <choice correct="true">Yes</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
        """)

        self.alpha_text = "VISIBLE TO ALPHA"
        self.beta_text = "VISIBLE TO BETA"
        self.audit_text = "VISIBLE TO AUDIT"
        self.everyone_text = "VISIBLE TO EVERYONE"

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc(
                            'problem',
                            self.alpha_text,
                            data=problem_data,
                            metadata={"group_access": {MINIMUM_STATIC_PARTITION_ID: [MINIMUM_STATIC_PARTITION_ID + 1]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.beta_text,
                            data=problem_data,
                            metadata={"group_access": {MINIMUM_STATIC_PARTITION_ID: [MINIMUM_STATIC_PARTITION_ID + 2]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.audit_text,
                            data=problem_data,
                            # Below 1 is the hardcoded group ID for "Audit"
                            metadata={"group_access": {ENROLLMENT_TRACK_PARTITION_ID: [1]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.everyone_text,
                            data=problem_data
                        )
                    )
                )
            )
        )

    @attr(shard=20)
    def test_staff_sees_all_problems(self):
        """
        Scenario: Staff see all problems
        Given I have a course with a cohort user partition
        And problems that are associated with specific groups in the user partition
        When I view the courseware in the LMS with staff access
        Then I see all the problems, regardless of their group_access property
        """
        course_page = self._goto_staff_page()
        verify_expected_problem_visibility(
            self,
            course_page,
            [self.alpha_text, self.beta_text, self.audit_text, self.everyone_text]
        )

    @attr(shard=3)
    def test_student_not_in_content_group(self):
        """
        Scenario: When previewing as a learner, only content visible to all is shown
        Given I have a course with a cohort user partition
        And problems that are associated with specific groups in the user partition
        When I view the courseware in the LMS with staff access
        And I change to previewing as a Learner
        Then I see only problems visible to all users
        """
        course_page = self._goto_staff_page()
        course_page.set_staff_view_mode('Learner')
        verify_expected_problem_visibility(self, course_page, [self.everyone_text])

    @attr(shard=3)
    def test_as_student_in_alpha(self):
        """
        Scenario: When previewing as a learner in group alpha, only content visible to alpha is shown
        Given I have a course with a cohort user partition
        And problems that are associated with specific groups in the user partition
        When I view the courseware in the LMS with staff access
        And I change to previewing as a Learner in group alpha
        Then I see only problems visible to group alpha
        """
        course_page = self._goto_staff_page()
        course_page.set_staff_view_mode('Learner in alpha')
        verify_expected_problem_visibility(self, course_page, [self.alpha_text, self.everyone_text])

    @attr(shard=3)
    def test_as_student_in_beta(self):
        """
        Scenario: When previewing as a learner in group beta, only content visible to beta is shown
        Given I have a course with a cohort user partition
        And problems that are associated with specific groups in the user partition
        When I view the courseware in the LMS with staff access
        And I change to previewing as a Learner in group beta
        Then I see only problems visible to group beta
        """
        course_page = self._goto_staff_page()
        course_page.set_staff_view_mode('Learner in beta')
        verify_expected_problem_visibility(self, course_page, [self.beta_text, self.everyone_text])

    @attr(shard=3)
    def test_as_student_in_audit(self):
        """
        Scenario: When previewing as a learner in the audit enrollment track, only content visible to audit is shown
        Given I have a course with an enrollment_track user partition
        And problems that are associated with specific groups in the user partition
        When I view the courseware in the LMS with staff access
        And I change to previewing as a Learner in audit enrollment track
        Then I see only problems visible to audit enrollment track
        """
        course_page = self._goto_staff_page()
        course_page.set_staff_view_mode('Learner in Audit')
        verify_expected_problem_visibility(self, course_page, [self.audit_text, self.everyone_text])

    def create_cohorts_and_assign_students(self, student_a_username, student_b_username):
        """
        Adds 2 manual cohorts, linked to content groups, to the course.
        Each cohort is assigned one learner.
        """
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        cohort_management_page = instructor_dashboard_page.select_cohort_management()
        cohort_management_page.is_cohorted = True

        def add_cohort_with_student(cohort_name, content_group, student):
            """ Create cohort and assign learner to it. """
            cohort_management_page.add_cohort(cohort_name, content_group=content_group)
            cohort_management_page.add_students_to_selected_cohort([student])
        add_cohort_with_student("Cohort Alpha", "alpha", student_a_username)
        add_cohort_with_student("Cohort Beta", "beta", student_b_username)
        cohort_management_page.wait_for_ajax()

    @attr('a11y')
    def test_course_page(self):
        """
        Run accessibility audit for course staff pages.
        """
        course_page = self._goto_staff_page()
        course_page.a11y_audit.config.set_rules({
            'ignore': [
                'aria-allowed-attr',  # TODO: AC-559
                'aria-roles',  # TODO: AC-559,
                'aria-valid-attr',  # TODO: AC-559
                'color-contrast',  # TODO: AC-559
                'link-href',  # TODO: AC-559
                'section',  # TODO: AC-559
                'region',  # TODO: AC-932
            ]
        })
        course_page.a11y_audit.check_for_accessibility_errors()


def verify_expected_problem_visibility(test, courseware_page, expected_problems):
    """
    Helper method that checks that the expected problems are visible on the current page.
    """
    courseware_page.wait_for(
        lambda: courseware_page.num_xblock_components == len(expected_problems), "Expected number of problems visible"
    )
    for index, expected_problem in enumerate(expected_problems):
        test.assertIn(expected_problem, courseware_page.xblock_components[index].text)
