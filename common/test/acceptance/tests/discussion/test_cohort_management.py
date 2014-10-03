# -*- coding: utf-8 -*-
"""
End-to-end tests related to the cohort management on the LMS Instructor Dashboard
"""

from bok_choy.promise import EmptyPromise
from .helpers import CohortTestMixin
from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage

import uuid


class CohortConfigurationTest(UniqueCourseTest, CohortTestMixin):
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
        self.student_name = "student_user"
        self.student_id = AutoAuthPage(
            self.browser, username=self.student_name, course_id=self.course_id, staff=False
        ).visit().get_user_id()
        self.add_user_to_cohort(self.course_fixture, self.student_name, self.manual_cohort_id)

        # login as an instructor
        self.instructor_name = "instructor_user"
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, course_id=self.course_id, staff=True
        ).visit().get_user_id()

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
        Scenario: the cohort configuration management in the instructor dashboard specifies whether
        students are automatically or manually assigned to specific cohorts.

        Given I have a course with a manual cohort and an automatic cohort defined
        When I view the manual cohort in the instructor dashboard
        There is text specifying that students are only added to the cohort manually
        And when I vew the automatic cohort in the instructor dashboard
        There is text specifying that students are automatically added to the cohort
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
        Scenario: a link is present from the cohort configuration in the instructor dashboard
        to the Studio Advanced Settings.

        Given I have a course with a cohort defined
        When I view the cohort in the LMS instructor dashboard
        There is a link to take me to the Studio Advanced Settings for the course
        """
        self.membership_page.select_cohort(self.manual_cohort_name)
        self.membership_page.select_edit_settings()
        advanced_settings_page = AdvancedSettingsPage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        advanced_settings_page.wait_for_page()

    def test_add_students_to_cohort_success(self):
        """
        Scenario: When students are added to a cohort, the appropriate notification is shown.

        Given I have a course with two cohorts
        And there is a user in one cohort
        And there is a user in neither cohort
        When I add the two users to the cohort that initially had no users
        Then there are 2 users in total in the cohort
        And I get a notification that 2 users have been added to the cohort
        And I get a notification that 1 user was moved from the other cohort
        And the user input field is empty
        """
        self.membership_page.select_cohort(self.auto_cohort_name)
        self.assertEqual(0, self.membership_page.get_selected_cohort_count())
        self.membership_page.add_students_to_selected_cohort([self.student_name, self.instructor_name])
        # Wait for the number of users in the cohort to change, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 2 == self.membership_page.get_selected_cohort_count(), 'Waiting for added students'
        ).fulfill()
        confirmation_messages = self.membership_page.get_cohort_confirmation_messages()
        self.assertEqual(2, len(confirmation_messages))
        self.assertEqual("2 students have been added to this cohort group", confirmation_messages[0])
        self.assertEqual("1 student was removed from " + self.manual_cohort_name, confirmation_messages[1])
        self.assertEqual("", self.membership_page.get_cohort_student_input_field_value())

    def test_add_students_to_cohort_failure(self):
        """
        Scenario: When errors occur when adding students to a cohort, the appropriate notification is shown.

        Given I have a course with a cohort and a user already in it
        When I add the user already in a cohort to that same cohort
        And I add a non-existing user to that cohort
        Then there is no change in the number of students in the cohort
        And I get a notification that one user was already in the cohort
        And I get a notification that one user is unknown
        And the user input field still contains the incorrect email addresses
        """
        self.membership_page.select_cohort(self.manual_cohort_name)
        self.assertEqual(1, self.membership_page.get_selected_cohort_count())
        self.membership_page.add_students_to_selected_cohort([self.student_name, "unknown_user"])
        # Wait for notification messages to appear, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 2 == len(self.membership_page.get_cohort_confirmation_messages()), 'Waiting for notification'
        ).fulfill()
        self.assertEqual(1, self.membership_page.get_selected_cohort_count())

        confirmation_messages = self.membership_page.get_cohort_confirmation_messages()
        self.assertEqual(2, len(confirmation_messages))
        self.assertEqual("0 students have been added to this cohort group", confirmation_messages[0])
        self.assertEqual("1 student was already in the cohort group", confirmation_messages[1])

        error_messages = self.membership_page.get_cohort_error_messages()
        self.assertEqual(2, len(error_messages))
        self.assertEqual("There was an error when trying to add students:", error_messages[0])
        self.assertEqual("Unknown user: unknown_user", error_messages[1])
        self.assertEqual(
            self.student_name + ",unknown_user,",
            self.membership_page.get_cohort_student_input_field_value()
        )

    def test_add_new_cohort(self):
        """
        Scenario: A new manual cohort can be created, and a student assigned to it.

        Given I have a course with a user in the course
        When I add a new manual cohort to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And when I add the user to the new cohort
        Then the cohort has 1 user
        """
        new_cohort = str(uuid.uuid4().get_hex()[0:20])
        self.assertFalse(new_cohort in self.membership_page.get_cohorts())
        self.membership_page.add_cohort(new_cohort)
        # After adding the cohort, it should automatically be selected
        EmptyPromise(
            lambda: new_cohort == self.membership_page.get_selected_cohort(), "Waiting for new cohort to appear"
        ).fulfill()
        self.assertEqual(0, self.membership_page.get_selected_cohort_count())
        self.membership_page.add_students_to_selected_cohort([self.instructor_name])
        # Wait for the number of users in the cohort to change, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 1 == self.membership_page.get_selected_cohort_count(), 'Waiting for student to be added'
        ).fulfill()
