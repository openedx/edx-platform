"""
Test Help links in LMS
"""

from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.tests.discussion.helpers import CohortTestMixin
from common.test.acceptance.tests.lms.test_lms_instructor_dashboard import BaseInstructorDashboardTest
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase
from common.test.acceptance.tests.helpers import (
    assert_opened_help_link_is_correct,
    url_for_help,
    click_and_wait_for_window
)
from openedx.core.release import skip_unless_master

# @skip_unless_master is used throughout this file because on named release
# branches, most work happens leading up to the first release on the branch, and
# that is before the docs have been published.  Tests that check readthedocs for
# the right doc page will fail during this time, and it's just a big
# distraction.  Also, if we bork the docs, it's not the end of the world, and we
# can fix it easily, so this is a good tradeoff.


@skip_unless_master         # See note at the top of the file.
class TestCohortHelp(ContainerBase, CohortTestMixin):
    """
    Tests help links in Cohort page
    """
    def setUp(self, is_staff=True):
        super(TestCohortHelp, self).setUp(is_staff=is_staff)
        self.enable_cohorting(self.course_fixture)
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        self.cohort_management = self.instructor_dashboard_page.select_cohort_management()

    def verify_help_link(self, href):
        """
        Verifies that help link is correct
        Arguments:
            href (str): Help url
        """
        help_element = self.cohort_management.get_cohort_help_element()
        self.assertEqual(help_element.text, "What does this mean?")
        click_and_wait_for_window(self, help_element)
        assert_opened_help_link_is_correct(self, href)

    def test_manual_cohort_help(self):
        """
        Scenario: Help in 'What does it mean?' is correct when we create cohort manually.
        Given that I am at 'Cohort' tab of LMS instructor dashboard
        And I check 'Enable Cohorts'
        And I add cohort name it, choose Manual for Cohort Assignment Method and
        No content group for Associated Content Group and save the cohort
        Then you see the UI text "Learners are added to this cohort only when..."
        followed by "What does this mean" link.
        And I click "What does this mean" link then help link should end with
        course_features/cohorts/cohort_config.html#assign-learners-to-cohorts-manually
        """
        self.cohort_management.add_cohort('cohort_name')

        href = url_for_help(
            'course_author',
            '/course_features/cohorts/cohort_config.html#assign-learners-to-cohorts-manually',
        )
        self.verify_help_link(href)

    def test_automatic_cohort_help(self):
        """
        Scenario: Help in 'What does it mean?' is correct when we create cohort automatically.
        Given that I am at 'Cohort' tab of LMS instructor dashboard
        And I check 'Enable Cohorts'
        And I add cohort name it, choose Automatic for Cohort Assignment Method and
        No content group for Associated Content Group and save the cohort
        Then you see the UI text "Learners are added to this cohort automatically"
        followed by "What does this mean" link.
        And I click "What does this mean" link then help link should end with
        course_features/cohorts/cohorts_overview.html#all-automated-assignment
        """

        self.cohort_management.add_cohort('cohort_name', assignment_type='random')

        href = url_for_help(
            'course_author',
            '/course_features/cohorts/cohorts_overview.html#all-automated-assignment',
        )
        self.verify_help_link(href)


@skip_unless_master         # See note at the top of the file.
class InstructorDashboardHelp(BaseInstructorDashboardTest):
    """
    Tests opening help from the general Help button in the instructor dashboard.
    """

    def setUp(self):
        super(InstructorDashboardHelp, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()

    def test_instructor_dashboard_help(self):
        """
        Scenario: Help button opens staff help
        Given that I am viewing the Instructor Dashboard
        When I click "Help"
        Then I see help about the instructor dashboard in a new tab
        """
        href = url_for_help('course_author', '/CA_instructor_dash_help.html')
        help_element = self.instructor_dashboard_page.get_help_element()
        click_and_wait_for_window(self, help_element)
        assert_opened_help_link_is_correct(self, href)
