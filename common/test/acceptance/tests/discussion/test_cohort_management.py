# -*- coding: utf-8 -*-
"""
End-to-end tests related to the cohort management on the LMS Instructor Dashboard
"""


import uuid

from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.tests.discussion.helpers import CohortTestMixin
from common.test.acceptance.tests.helpers import EventsTestMixin, UniqueCourseTest
from openedx.core.lib.tests import attr


@attr(shard=8)
class CohortConfigurationTest(EventsTestMixin, UniqueCourseTest, CohortTestMixin):
    """
    Tests for cohort management on the LMS Instructor Dashboard
    """

    def setUp(self):
        """
        Set up a cohorted course
        """
        super(CohortConfigurationTest, self).setUp()

        # create course with cohorts
        self.manual_cohort_name = "ManualCohort1"
        self.auto_cohort_name = "AutoCohort1"
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.setup_cohort_config(self.course_fixture, auto_cohort_groups=[self.auto_cohort_name])
        self.manual_cohort_id = self.add_manual_cohort(self.course_fixture, self.manual_cohort_name)

        # create a non-instructor who will be registered for the course and in the manual cohort.
        self.student_name, self.student_email = self._generate_unique_user_data()
        self.student_id = AutoAuthPage(
            self.browser, username=self.student_name, email=self.student_email,
            course_id=self.course_id, staff=False
        ).visit().get_user_id()
        self.add_user_to_cohort(self.course_fixture, self.student_name, self.manual_cohort_id)

        # create a second student user
        self.other_student_name, self.other_student_email = self._generate_unique_user_data()
        self.other_student_id = AutoAuthPage(
            self.browser, username=self.other_student_name, email=self.other_student_email,
            course_id=self.course_id, staff=False
        ).visit().get_user_id()

        # login as an instructor
        self.instructor_name, self.instructor_email = self._generate_unique_user_data()
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, email=self.instructor_email,
            course_id=self.course_id, staff=True
        ).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        self.cohort_management_page = self.instructor_dashboard_page.select_cohort_management()

    def _generate_unique_user_data(self):
        """
        Produce unique username and e-mail.
        """
        unique_username = 'user' + str(uuid.uuid4().hex)[:12]
        unique_email = unique_username + "@example.com"
        return unique_username, unique_email

    @attr('a11y')
    def test_cohorts_management_a11y(self):
        """
        Run accessibility audit for cohort management.
        """
        self.cohort_management_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.cohort_management_page.a11y_audit.check_for_accessibility_errors()
