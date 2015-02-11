# -*- coding: utf-8 -*-
"""
End-to-end tests related to the cohort management on the LMS Instructor Dashboard
"""

from datetime import datetime

from pymongo import MongoClient

from pytz import UTC, utc
from bok_choy.promise import EmptyPromise
from nose.plugins.attrib import attr
from .helpers import CohortTestMixin
from ..helpers import UniqueCourseTest, create_user_partition_json
from xmodule.partitions.partitions import Group
from ...fixtures.course import CourseFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage, DataDownloadPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage
from ...pages.studio.settings_group_configurations import GroupConfigurationsPage

import uuid


@attr('shard_3')
class CohortConfigurationTest(UniqueCourseTest, CohortTestMixin):
    """
    Tests for cohort management on the LMS Instructor Dashboard
    """

    def setUp(self):
        """
        Set up a cohorted course
        """
        super(CohortConfigurationTest, self).setUp()

        self.event_collection = MongoClient()["test"]["events"]

        # create course with cohorts
        self.manual_cohort_name = "ManualCohort1"
        self.auto_cohort_name = "AutoCohort1"
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.setup_cohort_config(self.course_fixture, auto_cohort_groups=[self.auto_cohort_name])
        self.manual_cohort_id = self.add_manual_cohort(self.course_fixture, self.manual_cohort_name)

        # create a non-instructor who will be registered for the course and in the manual cohort.
        self.student_name = "student_user"
        self.student_id = AutoAuthPage(
            self.browser, username=self.student_name, email="student_user@example.com",
            course_id=self.course_id, staff=False
        ).visit().get_user_id()
        self.add_user_to_cohort(self.course_fixture, self.student_name, self.manual_cohort_id)

        # create a user with unicode characters in their username
        self.unicode_student_id = AutoAuthPage(
            self.browser, username="Ωπ", email="unicode_student_user@example.com",
            course_id=self.course_id, staff=False
        ).visit().get_user_id()

        # login as an instructor
        self.instructor_name = "instructor_user"
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, email="instructor_user@example.com",
            course_id=self.course_id, staff=True
        ).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        membership_page = self.instructor_dashboard_page.select_membership()
        self.cohort_management_page = membership_page.select_cohort_management_section()

    def verify_cohort_description(self, cohort_name, expected_description):
        """
        Selects the cohort with the given name and verifies the expected description is presented.
        """
        self.cohort_management_page.select_cohort(cohort_name)
        self.assertEquals(self.cohort_management_page.get_selected_cohort(), cohort_name)
        self.assertIn(expected_description, self.cohort_management_page.get_cohort_group_setup())

    def test_cohort_description(self):
        """
        Scenario: the cohort configuration management in the instructor dashboard specifies whether
        students are automatically or manually assigned to specific cohorts.

        Given I have a course with a manual cohort and an automatic cohort defined
        When I view the manual cohort in the instructor dashboard
        There is text specifying that students are only added to the cohort manually
        And when I view the automatic cohort in the instructor dashboard
        There is text specifying that students are automatically added to the cohort
        """
        self.verify_cohort_description(
            self.manual_cohort_name,
            'Students are added to this cohort only when you provide '
            'their email addresses or usernames on this page',
        )
        self.verify_cohort_description(
            self.auto_cohort_name,
            'Students are added to this cohort automatically',
        )

    def test_no_content_groups(self):
        """
        Scenario: if the course has no content groups defined (user_partitions of type cohort),
        the settings in the cohort management tab reflect this

        Given I have a course with a cohort defined but no content groups
        When I view the cohort in the instructor dashboard and select settings
        Then the cohort is not linked to a content group
        And there is text stating that no content groups are defined
        And I cannot select the radio button to enable content group association
        And there is a link I can select to open Group settings in Studio
        """
        self.cohort_management_page.select_cohort(self.manual_cohort_name)
        self.assertIsNone(self.cohort_management_page.get_cohort_associated_content_group())
        self.assertEqual(
            "Warning:\nNo content groups exist. Create a content group",
            self.cohort_management_page.get_cohort_related_content_group_message()
        )
        self.assertFalse(self.cohort_management_page.select_content_group_radio_button())
        self.cohort_management_page.select_studio_group_settings()
        group_settings_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        group_settings_page.wait_for_page()

    def test_link_to_studio(self):
        """
        Scenario: a link is present from the cohort configuration in the instructor dashboard
        to the Studio Advanced Settings.

        Given I have a course with a cohort defined
        When I view the cohort in the LMS instructor dashboard
        There is a link to take me to the Studio Advanced Settings for the course
        """
        self.cohort_management_page.select_cohort(self.manual_cohort_name)
        self.cohort_management_page.select_edit_settings()
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
        And appropriate events have been emitted
        """
        start_time = datetime.now(UTC)
        self.cohort_management_page.select_cohort(self.auto_cohort_name)
        self.assertEqual(0, self.cohort_management_page.get_selected_cohort_count())
        self.cohort_management_page.add_students_to_selected_cohort([self.student_name, self.instructor_name])
        # Wait for the number of users in the cohort to change, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 2 == self.cohort_management_page.get_selected_cohort_count(), 'Waiting for added students'
        ).fulfill()
        confirmation_messages = self.cohort_management_page.get_cohort_confirmation_messages()
        self.assertEqual(
            [
                "2 students have been added to this cohort",
                "1 student was removed from " + self.manual_cohort_name
            ],
            confirmation_messages
        )
        self.assertEqual("", self.cohort_management_page.get_cohort_student_input_field_value())
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_added",
                "time": {"$gt": start_time},
                "event.user_id": {"$in": [int(self.instructor_id), int(self.student_id)]},
                "event.cohort_name": self.auto_cohort_name,
            }).count(),
            2
        )
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_removed",
                "time": {"$gt": start_time},
                "event.user_id": int(self.student_id),
                "event.cohort_name": self.manual_cohort_name,
            }).count(),
            1
        )
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_add_requested",
                "time": {"$gt": start_time},
                "event.user_id": int(self.instructor_id),
                "event.cohort_name": self.auto_cohort_name,
                "event.previous_cohort_name": None,
            }).count(),
            1
        )
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_add_requested",
                "time": {"$gt": start_time},
                "event.user_id": int(self.student_id),
                "event.cohort_name": self.auto_cohort_name,
                "event.previous_cohort_name": self.manual_cohort_name,
            }).count(),
            1
        )

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
        self.cohort_management_page.select_cohort(self.manual_cohort_name)
        self.assertEqual(1, self.cohort_management_page.get_selected_cohort_count())
        self.cohort_management_page.add_students_to_selected_cohort([self.student_name, "unknown_user"])
        # Wait for notification messages to appear, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 2 == len(self.cohort_management_page.get_cohort_confirmation_messages()), 'Waiting for notification'
        ).fulfill()
        self.assertEqual(1, self.cohort_management_page.get_selected_cohort_count())

        self.assertEqual(
            [
                "0 students have been added to this cohort",
                "1 student was already in the cohort"
            ],
            self.cohort_management_page.get_cohort_confirmation_messages()
        )

        self.assertEqual(
            [
                "There was an error when trying to add students:",
                "Unknown user: unknown_user"
            ],
            self.cohort_management_page.get_cohort_error_messages()
        )
        self.assertEqual(
            self.student_name + ",unknown_user,",
            self.cohort_management_page.get_cohort_student_input_field_value()
        )

    def _verify_cohort_settings(
            self,
            cohort_name,
            assignment_type=None,
            new_cohort_name=None,
            new_assignment_type=None,
            verify_updated=False
    ):

        """
        Create a new cohort and verify the new and existing settings.
        """
        start_time = datetime.now(UTC)
        self.assertFalse(cohort_name in self.cohort_management_page.get_cohorts())
        self.cohort_management_page.add_cohort(cohort_name, assignment_type=assignment_type)
        # After adding the cohort, it should automatically be selected
        EmptyPromise(
            lambda: cohort_name == self.cohort_management_page.get_selected_cohort(), "Waiting for new cohort to appear"
        ).fulfill()
        self.assertEqual(0, self.cohort_management_page.get_selected_cohort_count())
        # After adding the cohort, it should automatically be selected and its
        # assignment_type should be "manual" as this is the default assignment type
        _assignment_type = assignment_type or 'manual'
        msg = "Waiting for currently selected cohort assignment type"
        EmptyPromise(
            lambda: _assignment_type == self.cohort_management_page.get_cohort_associated_assignment_type(), msg
        ).fulfill()
        # Go back to Manage Students Tab
        self.cohort_management_page.select_manage_settings()
        self.cohort_management_page.add_students_to_selected_cohort([self.instructor_name])
        # Wait for the number of users in the cohort to change, indicating that the add operation is complete.
        EmptyPromise(
            lambda: 1 == self.cohort_management_page.get_selected_cohort_count(), 'Waiting for student to be added'
        ).fulfill()
        self.assertFalse(self.cohort_management_page.is_assignment_settings_disabled)
        self.assertEqual('', self.cohort_management_page.assignment_settings_message)
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.created",
                "time": {"$gt": start_time},
                "event.cohort_name": cohort_name,
            }).count(),
            1
        )
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.creation_requested",
                "time": {"$gt": start_time},
                "event.cohort_name": cohort_name,
            }).count(),
            1
        )

        if verify_updated:
            self.cohort_management_page.select_cohort(cohort_name)
            self.cohort_management_page.select_cohort_settings()
            self.cohort_management_page.set_cohort_name(new_cohort_name)
            self.cohort_management_page.set_assignment_type(new_assignment_type)
            self.cohort_management_page.save_cohort_settings()

            # If cohort name is empty, then we should get/see an error message.
            if not new_cohort_name:
                confirmation_messages = self.cohort_management_page.get_cohort_settings_messages(type='error')
                self.assertEqual(
                    ["The cohort cannot be saved", "You must specify a name for the cohort"],
                    confirmation_messages
                )
            else:
                confirmation_messages = self.cohort_management_page.get_cohort_settings_messages()
                self.assertEqual(["Saved cohort"], confirmation_messages)
                self.assertEqual(new_cohort_name, self.cohort_management_page.cohort_name_in_header)
                self.assertTrue(new_cohort_name in self.cohort_management_page.get_cohorts())
                self.assertEqual(1, self.cohort_management_page.get_selected_cohort_count())
                self.assertEqual(
                    new_assignment_type,
                    self.cohort_management_page.get_cohort_associated_assignment_type()
                )

    def test_add_new_cohort(self):
        """
        Scenario: A new manual cohort can be created, and a student assigned to it.

        Given I have a course with a user in the course
        When I add a new manual cohort to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And assignment type of displayed cohort to "manual" because this is the default
        And when I add the user to the new cohort
        Then the cohort has 1 user
        And appropriate events have been emitted
        """
        cohort_name = str(uuid.uuid4().get_hex()[0:20])
        self._verify_cohort_settings(cohort_name=cohort_name, assignment_type=None)

    def test_add_new_cohort_with_manual_assignment_type(self):
        """
        Scenario: A new cohort with manual assignment type can be created, and a student assigned to it.

        Given I have a course with a user in the course
        When I add a new manual cohort with manual assignment type to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And assignment type of displayed cohort is "manual"
        And when I add the user to the new cohort
        Then the cohort has 1 user
        And appropriate events have been emitted
        """
        cohort_name = str(uuid.uuid4().get_hex()[0:20])
        self._verify_cohort_settings(cohort_name=cohort_name, assignment_type='manual')

    def test_add_new_cohort_with_random_assignment_type(self):
        """
        Scenario: A new cohort with random assignment type can be created, and a student assigned to it.

        Given I have a course with a user in the course
        When I add a new manual cohort with random assignment type to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And assignment type of displayed cohort is "random"
        And when I add the user to the new cohort
        Then the cohort has 1 user
        And appropriate events have been emitted
        """
        cohort_name = str(uuid.uuid4().get_hex()[0:20])
        self._verify_cohort_settings(cohort_name=cohort_name, assignment_type='random')

    def test_update_existing_cohort_settings(self):
        """
        Scenario: Update existing cohort settings(cohort name, assignment type)

        Given I have a course with a user in the course
        When I add a new cohort with random assignment type to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And assignment type of displayed cohort is "random"
        And when I add the user to the new cohort
        Then the cohort has 1 user
        And appropriate events have been emitted
        Then I select the cohort (that you just created) from existing cohorts
        Then I change its name and assignment type set to "manual"
        Then I Save the settings
        And cohort with new name is present in cohorts dropdown list
        And cohort assignment type should be "manual"
        """
        cohort_name = str(uuid.uuid4().get_hex()[0:20])
        new_cohort_name = '{old}__NEW'.format(old=cohort_name)
        self._verify_cohort_settings(
            cohort_name=cohort_name,
            assignment_type='random',
            new_cohort_name=new_cohort_name,
            new_assignment_type='manual',
            verify_updated=True
        )

    def test_update_existing_cohort_settings_with_empty_cohort_name(self):
        """
        Scenario: Update existing cohort settings(cohort name, assignment type).

        Given I have a course with a user in the course
        When I add a new cohort with random assignment type to the course via the LMS instructor dashboard
        Then the new cohort is displayed and has no users in it
        And assignment type of displayed cohort is "random"
        And when I add the user to the new cohort
        Then the cohort has 1 user
        And appropriate events have been emitted
        Then I select a cohort from existing cohorts
        Then I set its name as empty string and assignment type set to "manual"
        And I click on Save button
        Then I should see an error message
        """
        cohort_name = str(uuid.uuid4().get_hex()[0:20])
        new_cohort_name = ''
        self._verify_cohort_settings(
            cohort_name=cohort_name,
            assignment_type='random',
            new_cohort_name=new_cohort_name,
            new_assignment_type='manual',
            verify_updated=True
        )

    def test_default_cohort_assignment_settings(self):
        """
        Scenario: Cohort assignment settings are disabled for default cohort.

        Given I have a course with a user in the course
        And I have added a manual cohort
        And I have added a random cohort
        When I select the random cohort
        Then cohort assignment settings are disabled
        """
        self.cohort_management_page.select_cohort("AutoCohort1")
        self.cohort_management_page.select_cohort_settings()

        self.assertTrue(self.cohort_management_page.is_assignment_settings_disabled)

        message = "There must be one cohort to which students can be randomly assigned."
        self.assertEqual(message, self.cohort_management_page.assignment_settings_message)

    def test_link_to_data_download(self):
        """
        Scenario: a link is present from the cohort configuration in
        the instructor dashboard to the Data Download section.

        Given I have a course with a cohort defined
        When I view the cohort in the LMS instructor dashboard
        There is a link to take me to the Data Download section of the Instructor Dashboard.
        """
        self.cohort_management_page.select_data_download()
        data_download_page = DataDownloadPage(self.browser)
        data_download_page.wait_for_page()

    def test_cohort_by_csv_both_columns(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using both emails and usernames.

        Given I have a course with two cohorts defined
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to cohorts via both usernames and emails
        Then I can download a file with results
        And appropriate events have been emitted
        """
        # cohort_users_both_columns.csv adds instructor_user to ManualCohort1 via username and
        # student_user to AutoCohort1 via email
        self._verify_csv_upload_acceptable_file("cohort_users_both_columns.csv")

    def test_cohort_by_csv_only_email(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using only emails.

        Given I have a course with two cohorts defined
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to cohorts via only emails
        Then I can download a file with results
        And appropriate events have been emitted
        """
        # cohort_users_only_email.csv adds instructor_user to ManualCohort1 and student_user to AutoCohort1 via email
        self._verify_csv_upload_acceptable_file("cohort_users_only_email.csv")

    def test_cohort_by_csv_only_username(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using only usernames.

        Given I have a course with two cohorts defined
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to cohorts via only usernames
        Then I can download a file with results
        And appropriate events have been emitted
        """
        # cohort_users_only_username.csv adds instructor_user to ManualCohort1 and
        # student_user to AutoCohort1 via username
        self._verify_csv_upload_acceptable_file("cohort_users_only_username.csv")

    def _verify_csv_upload_acceptable_file(self, filename):
        """
        Helper method to verify cohort assignments after a successful CSV upload.
        """
        start_time = datetime.now(UTC)
        self.cohort_management_page.upload_cohort_file(filename)
        self._verify_cohort_by_csv_notification(
            "Your file '{}' has been uploaded. Allow a few minutes for processing.".format(filename)
        )

        # student_user is moved from manual cohort to auto cohort
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_added",
                "time": {"$gt": start_time},
                "event.user_id": {"$in": [int(self.student_id)]},
                "event.cohort_name": self.auto_cohort_name,
            }).count(),
            1
        )
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_removed",
                "time": {"$gt": start_time},
                "event.user_id": int(self.student_id),
                "event.cohort_name": self.manual_cohort_name,
            }).count(),
            1
        )
        # instructor_user (previously unassigned) is added to manual cohort
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_added",
                "time": {"$gt": start_time},
                "event.user_id": {"$in": [int(self.instructor_id)]},
                "event.cohort_name": self.manual_cohort_name,
            }).count(),
            1
        )
        # unicode_student_user (previously unassigned) is added to manual cohort
        self.assertEqual(
            self.event_collection.find({
                "name": "edx.cohort.user_added",
                "time": {"$gt": start_time},
                "event.user_id": {"$in": [int(self.unicode_student_id)]},
                "event.cohort_name": self.manual_cohort_name,
            }).count(),
            1
        )

        # Verify the results can be downloaded.
        data_download = self.instructor_dashboard_page.select_data_download()
        EmptyPromise(
            lambda: 1 == len(data_download.get_available_reports_for_download()), 'Waiting for downloadable report'
        ).fulfill()
        report = data_download.get_available_reports_for_download()[0]
        base_file_name = "cohort_results_"
        self.assertIn("{}_{}".format(
            '_'.join([self.course_info['org'], self.course_info['number'], self.course_info['run']]), base_file_name
        ), report)
        report_datetime = datetime.strptime(
            report[report.index(base_file_name) + len(base_file_name):-len(".csv")],
            "%Y-%m-%d-%H%M"
        )
        self.assertLessEqual(start_time.replace(second=0, microsecond=0), utc.localize(report_datetime))

    def test_cohort_by_csv_wrong_file_type(self):
        """
        Scenario: if the instructor uploads a non-csv file, an error message is presented.

        Given I have a course with cohorting enabled
        When I go to the cohort management section of the instructor dashboard
        And I upload a file without the CSV extension
        Then I get an error message stating that the file must have a CSV extension
        """
        self.cohort_management_page.upload_cohort_file("image.jpg")
        self._verify_cohort_by_csv_notification("The file must end with the extension '.csv'.")

    def test_cohort_by_csv_missing_cohort(self):
        """
        Scenario: if the instructor uploads a csv file with no cohort column, an error message is presented.

        Given I have a course with cohorting enabled
        When I go to the cohort management section of the instructor dashboard
        And I upload a CSV file that is missing the cohort column
        Then I get an error message stating that the file must have a cohort column
        """
        self.cohort_management_page.upload_cohort_file("cohort_users_missing_cohort_column.csv")
        self._verify_cohort_by_csv_notification("The file must contain a 'cohort' column containing cohort names.")

    def test_cohort_by_csv_missing_user(self):
        """
        Scenario: if the instructor uploads a csv file with no username or email column, an error message is presented.

        Given I have a course with cohorting enabled
        When I go to the cohort management section of the instructor dashboard
        And I upload a CSV file that is missing both the username and email columns
        Then I get an error message stating that the file must have either a username or email column
        """
        self.cohort_management_page.upload_cohort_file("cohort_users_missing_user_columns.csv")
        self._verify_cohort_by_csv_notification(
            "The file must contain a 'username' column, an 'email' column, or both."
        )

    def _verify_cohort_by_csv_notification(self, expected_message):
        """
        Helper method to check the CSV file upload notification message.
        """
        # Wait for notification message to appear, indicating file has been uploaded.
        EmptyPromise(
            lambda: 1 == len(self.cohort_management_page.get_csv_messages()), 'Waiting for notification'
        ).fulfill()
        messages = self.cohort_management_page.get_csv_messages()
        self.assertEquals(expected_message, messages[0])


@attr('shard_3')
class CohortContentGroupAssociationTest(UniqueCourseTest, CohortTestMixin):
    """
    Tests for linking between content groups and cohort in the instructor dashboard.
    """

    def setUp(self):
        """
        Set up a cohorted course with a user_partition of scheme "cohort".
        """
        super(CohortContentGroupAssociationTest, self).setUp()

        # create course with single cohort and two content groups (user_partition of type "cohort")
        self.cohort_name = "OnlyCohort"
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.setup_cohort_config(self.course_fixture)
        self.cohort_id = self.add_manual_cohort(self.course_fixture, self.cohort_name)

        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Apples, Bananas',
                        'Content Group Partition',
                        [Group("0", 'Apples'), Group("1", 'Bananas')],
                        scheme="cohort"
                    )
                ],
            },
        })

        # login as an instructor
        self.instructor_name = "instructor_user"
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, email="instructor_user@example.com",
            course_id=self.course_id, staff=True
        ).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        membership_page = self.instructor_dashboard_page.select_membership()
        self.cohort_management_page = membership_page.select_cohort_management_section()

    def test_no_content_group_linked(self):
        """
        Scenario: In a course with content groups, cohorts are initially not linked to a content group

        Given I have a course with a cohort defined and content groups defined
        When I view the cohort in the instructor dashboard and select settings
        Then the cohort is not linked to a content group
        And there is no text stating that content groups are undefined
        And the content groups are listed in the selector
        """
        self.cohort_management_page.select_cohort(self.cohort_name)
        self.assertIsNone(self.cohort_management_page.get_cohort_associated_content_group())
        self.assertIsNone(self.cohort_management_page.get_cohort_related_content_group_message())
        self.assertEquals(["Apples", "Bananas"], self.cohort_management_page.get_all_content_groups())

    def test_link_to_content_group(self):
        """
        Scenario: In a course with content groups, cohorts can be linked to content groups

        Given I have a course with a cohort defined and content groups defined
        When I view the cohort in the instructor dashboard and select settings
        And I link the cohort to one of the content groups and save
        Then there is a notification that my cohort has been saved
        And when I reload the page
        And I view the cohort in the instructor dashboard and select settings
        Then the cohort is still linked to the content group
        """
        self._link_cohort_to_content_group(self.cohort_name, "Bananas")
        self.assertEqual("Bananas", self.cohort_management_page.get_cohort_associated_content_group())

    def test_unlink_from_content_group(self):
        """
        Scenario: In a course with content groups, cohorts can be unlinked from content groups

        Given I have a course with a cohort defined and content groups defined
        When I view the cohort in the instructor dashboard and select settings
        And I link the cohort to one of the content groups and save
        Then there is a notification that my cohort has been saved
        And I reload the page
        And I view the cohort in the instructor dashboard and select settings
        And I unlink the cohort from any content group and save
        Then there is a notification that my cohort has been saved
        And when I reload the page
        And I view the cohort in the instructor dashboard and select settings
        Then the cohort is not linked to any content group
        """
        self._link_cohort_to_content_group(self.cohort_name, "Bananas")
        self.cohort_management_page.set_cohort_associated_content_group(None)
        self._verify_settings_saved_and_reload(self.cohort_name)
        self.assertEqual(None, self.cohort_management_page.get_cohort_associated_content_group())

    def test_create_new_cohort_linked_to_content_group(self):
        """
        Scenario: In a course with content groups, a new cohort can be linked to a content group
            at time of creation.

        Given I have a course with a cohort defined and content groups defined
        When I create a new cohort and link it to a content group
        Then when I select settings I see that the cohort is linked to the content group
        And when I reload the page
        And I view the cohort in the instructor dashboard and select settings
        Then the cohort is still linked to the content group
        """
        new_cohort = "correctly linked cohort"
        self._create_new_cohort_linked_to_content_group(new_cohort, "Apples")
        self.browser.refresh()
        self.cohort_management_page.wait_for_page()
        self.cohort_management_page.select_cohort(new_cohort)
        self.assertEqual("Apples", self.cohort_management_page.get_cohort_associated_content_group())

    def test_missing_content_group(self):
        """
        Scenario: In a course with content groups, if a cohort is associated with a content group that no longer
            exists, a warning message is shown

        Given I have a course with a cohort defined and content groups defined
        When I create a new cohort and link it to a content group
        And I delete that content group from the course
        And I reload the page
        And I view the cohort in the instructor dashboard and select settings
        Then the settings display a message that the content group no longer exists
        And when I select a different content group and save
        Then the error message goes away
        """
        new_cohort = "linked to missing content group"
        self._create_new_cohort_linked_to_content_group(new_cohort, "Apples")
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Apples, Bananas',
                        'Content Group Partition',
                        [Group("2", 'Pears'), Group("1", 'Bananas')],
                        scheme="cohort"
                    )
                ],
            },
        })
        self.browser.refresh()
        self.cohort_management_page.wait_for_page()
        self.cohort_management_page.select_cohort(new_cohort)
        self.assertEqual("Deleted Content Group", self.cohort_management_page.get_cohort_associated_content_group())
        self.assertEquals(
            ["Bananas", "Pears", "Deleted Content Group"],
            self.cohort_management_page.get_all_content_groups()
        )
        self.assertEqual(
            "Warning:\nThe previously selected content group was deleted. Select another content group.",
            self.cohort_management_page.get_cohort_related_content_group_message()
        )
        self.cohort_management_page.set_cohort_associated_content_group("Pears")
        confirmation_messages = self.cohort_management_page.get_cohort_settings_messages()
        self.assertEqual(["Saved cohort"], confirmation_messages)
        self.assertIsNone(self.cohort_management_page.get_cohort_related_content_group_message())
        self.assertEquals(["Bananas", "Pears"], self.cohort_management_page.get_all_content_groups())

    def _create_new_cohort_linked_to_content_group(self, new_cohort, cohort_group):
        """
        Creates a new cohort linked to a content group.
        """
        self.cohort_management_page.add_cohort(new_cohort, content_group=cohort_group)
        # After adding the cohort, it should automatically be selected
        EmptyPromise(
            lambda: new_cohort == self.cohort_management_page.get_selected_cohort(), "Waiting for new cohort to appear"
        ).fulfill()
        self.assertEqual(cohort_group, self.cohort_management_page.get_cohort_associated_content_group())

    def _link_cohort_to_content_group(self, cohort_name, content_group):
        """
        Links a cohort to a content group. Saves the changes and verifies the cohort updated properly.
        Then refreshes the page and selects the cohort.
        """
        self.cohort_management_page.select_cohort(cohort_name)
        self.cohort_management_page.set_cohort_associated_content_group(content_group)
        self._verify_settings_saved_and_reload(cohort_name)

    def _verify_settings_saved_and_reload(self, cohort_name):
        """
        Verifies the confirmation message indicating that a cohort's settings have been updated.
        Then refreshes the page and selects the cohort.
        """
        confirmation_messages = self.cohort_management_page.get_cohort_settings_messages()
        self.assertEqual(["Saved cohort"], confirmation_messages)
        self.browser.refresh()
        self.cohort_management_page.wait_for_page()
        self.cohort_management_page.select_cohort(cohort_name)
