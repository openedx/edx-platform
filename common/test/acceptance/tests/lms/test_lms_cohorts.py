# -*- coding: utf-8 -*-
"""
End-to-end tests related to the cohort management on the LMS Instructor Dashboard
"""

from .helpers import CohortTestMixin
from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage


class CohortTest(UniqueCourseTest, CohortTestMixin):
    """
    Tests for cohort management on the LMS Instructor Dashboard
    """

    def setUp(self):
        """
        Set up a cohorted course
        """
        super(CohortTest, self).setUp()

        # create course with cohorts
        self.manual_cohort_name = "ManualCohort1"
        self.auto_cohort_name = "AutoCohort1"
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.setup_cohort_config(self.course_fixture, auto_cohort_groups=[self.auto_cohort_name])
        self.add_manual_cohort(self.course_fixture, self.manual_cohort_name)

        # login as an instructor
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        self.membership_page = instructor_dashboard_page.select_membership()

    def verify_cohort_description(self, cohort_name, expected_description):
        """
        Selects the cohort with the given name and verifies the expected description is presented.
        """
        self.membership_page.select_cohort(cohort_name)
        self.assertEquals(self.membership_page.get_selected_cohort(), cohort_name)
        self.assertIn(expected_description, self.membership_page.get_cohort_group_setup())

    def test_cohort_description(self):
        """
        Tests the description presented for manual and auto cohort types.
        """
        self.verify_cohort_description(
            self.manual_cohort_name,
            'Students are added to this group only when you provide their email addresses or usernames on this page',
        )
        self.verify_cohort_description(
            self.auto_cohort_name,
            'Students are added to this group automatically',
        )

    def test_link_to_studio(self):
        """
        Tests the link to the Advanced Settings page in Studio.
        """
        self.membership_page.select_cohort(self.manual_cohort_name)
        self.membership_page.select_edit_settings()
        advanced_settings_page = AdvancedSettingsPage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        advanced_settings_page.wait_for_page()
