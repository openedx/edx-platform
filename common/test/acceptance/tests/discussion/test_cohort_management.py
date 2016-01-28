# -*- coding: utf-8 -*-
"""
End-to-end tests related to the cohort management on the LMS Instructor Dashboard
"""

from datetime import datetime

from pytz import UTC, utc
from bok_choy.promise import EmptyPromise
from nose.plugins.attrib import attr
from .helpers import CohortTestMixin
from ..helpers import UniqueCourseTest, EventsTestMixin, create_user_partition_json
from xmodule.partitions.partitions import Group
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage, DataDownloadPage
from ...pages.studio.settings_group_configurations import GroupConfigurationsPage

import os
import unicodecsv
import uuid


@attr('shard_8')
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
            'Learners are added to this cohort only when you provide '
            'their email addresses or usernames on this page',
        )
        self.verify_cohort_description(
            self.auto_cohort_name,
            'Learners are added to this cohort automatically',
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

    def _create_csv_file(self, filename, csv_text_as_lists):
        """
        Create a csv file with the provided list of lists.

        :param filename: this is the name that will be used for the csv file. Its location will
         be under the test upload data directory
        :param csv_text_as_lists: provide the contents of the csv file int he form of a list of lists
        """
        filename = self.instructor_dashboard_page.get_asset_path(filename)
        with open(filename, 'w+') as csv_file:
            writer = unicodecsv.writer(csv_file)
            for line in csv_text_as_lists:
                writer.writerow(line)
        self.addCleanup(os.remove, filename)

    def _generate_unique_user_data(self):
        """
        Produce unique username and e-mail.
        """
        unique_username = 'user' + str(uuid.uuid4().hex)[:12]
        unique_email = unique_username + "@example.com"
        return unique_username, unique_email

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

        message = "There must be one cohort to which students can automatically be assigned."
        self.assertEqual(message, self.cohort_management_page.assignment_settings_message)

    def test_cohort_enable_disable(self):
        """
        Scenario: Cohort Enable/Disable checkbox related functionality is working as intended.

        Given I have a cohorted course with a user.
        And I can see the `Enable Cohorts` checkbox is checked.
        And cohort management controls are visible.
        When I uncheck the `Enable Cohorts` checkbox.
        Then cohort management controls are not visible.
        And When I reload the page.
        Then I can see the `Enable Cohorts` checkbox is unchecked.
        And cohort management controls are not visible.
        """
        self.assertTrue(self.cohort_management_page.is_cohorted)
        self.assertTrue(self.cohort_management_page.cohort_management_controls_visible())
        self.cohort_management_page.is_cohorted = False
        self.assertFalse(self.cohort_management_page.cohort_management_controls_visible())
        self.browser.refresh()
        self.cohort_management_page.wait_for_page()
        self.assertFalse(self.cohort_management_page.is_cohorted)
        self.assertFalse(self.cohort_management_page.cohort_management_controls_visible())

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
        csv_contents = [
            ['username', 'email', 'ignored_column', 'cohort'],
            [self.instructor_name, '', 'June', 'ManualCohort1'],
            ['', self.student_email, 'Spring', 'AutoCohort1'],
            [self.other_student_name, '', 'Fall', 'ManualCohort1'],
        ]
        filename = "cohort_csv_both_columns_1.csv"
        self._create_csv_file(filename, csv_contents)
        self._verify_csv_upload_acceptable_file(filename)

    def test_cohort_by_csv_only_email(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using only emails.

        Given I have a course with two cohorts defined
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to cohorts via only emails
        Then I can download a file with results
        And appropriate events have been emitted
        """
        csv_contents = [
            ['email', 'cohort'],
            [self.instructor_email, 'ManualCohort1'],
            [self.student_email, 'AutoCohort1'],
            [self.other_student_email, 'ManualCohort1'],
        ]
        filename = "cohort_csv_emails_only.csv"
        self._create_csv_file(filename, csv_contents)
        self._verify_csv_upload_acceptable_file(filename)

    def test_cohort_by_csv_only_username(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using only usernames.

        Given I have a course with two cohorts defined
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to cohorts via only usernames
        Then I can download a file with results
        And appropriate events have been emitted
        """
        csv_contents = [
            ['username', 'cohort'],
            [self.instructor_name, 'ManualCohort1'],
            [self.student_name, 'AutoCohort1'],
            [self.other_student_name, 'ManualCohort1'],
        ]
        filename = "cohort_users_only_username1.csv"
        self._create_csv_file(filename, csv_contents)
        self._verify_csv_upload_acceptable_file(filename)

    # TODO: Change unicode_hello_in_korean = u'ßßßßßß' to u'안녕하세요', after up gradation of Chrome driver. See TNL-3944
    def test_cohort_by_csv_unicode(self):
        """
        Scenario: the instructor can upload a file with user and cohort assignments, using both emails and usernames.

        Given I have a course with two cohorts defined
        And I add another cohort with a unicode name
        When I go to the cohort management section of the instructor dashboard
        I can upload a CSV file with assignments of users to the unicode cohort via both usernames and emails
        Then I can download a file with results

        TODO: refactor events verification to handle this scenario. Events verification assumes movements
        between other cohorts (manual and auto).
        """
        unicode_hello_in_korean = u'ßßßßßß'
        self._verify_cohort_settings(cohort_name=unicode_hello_in_korean, assignment_type=None)
        csv_contents = [
            ['username', 'email', 'cohort'],
            [self.instructor_name, '', unicode_hello_in_korean],
            ['', self.student_email, unicode_hello_in_korean],
            [self.other_student_name, '', unicode_hello_in_korean]
        ]
        filename = "cohort_unicode_name.csv"
        self._create_csv_file(filename, csv_contents)
        self._verify_csv_upload_acceptable_file(filename, skip_events=True)

    def _verify_csv_upload_acceptable_file(self, filename, skip_events=None):
        """
        Helper method to verify cohort assignments after a successful CSV upload.

        When skip_events is specified, no assertions are made on events.
        """
        start_time = datetime.now(UTC)
        self.cohort_management_page.upload_cohort_file(filename)
        self._verify_cohort_by_csv_notification(
            "Your file '{}' has been uploaded. Allow a few minutes for processing.".format(filename)
        )

        if not skip_events:
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
            # other_student_user (previously unassigned) is added to manual cohort
            self.assertEqual(
                self.event_collection.find({
                    "name": "edx.cohort.user_added",
                    "time": {"$gt": start_time},
                    "event.user_id": {"$in": [int(self.other_student_id)]},
                    "event.cohort_name": self.manual_cohort_name,
                }).count(),
                1
            )

        # Verify the results can be downloaded.
        data_download = self.instructor_dashboard_page.select_data_download()
        data_download.wait_for_available_report()
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


@attr('shard_6')
class CohortDiscussionTopicsTest(UniqueCourseTest, CohortTestMixin):
    """
    Tests for cohorting the inline and course-wide discussion topics.
    """
    def setUp(self):
        """
        Set up a discussion topics
        """
        super(CohortDiscussionTopicsTest, self).setUp()

        self.discussion_id = "test_discussion_{}".format(uuid.uuid4().hex)
        self.course_fixture = CourseFixture(**self.course_info).add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                            metadata={"discussion_id": self.discussion_id}
                        )
                    )
                )
            )
        ).install()

        # create course with single cohort and two content groups (user_partition of type "cohort")
        self.cohort_name = "OnlyCohort"
        self.setup_cohort_config(self.course_fixture)
        self.cohort_id = self.add_manual_cohort(self.course_fixture, self.cohort_name)

        # login as an instructor
        self.instructor_name = "instructor_user"
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, email="instructor_user@example.com",
            course_id=self.course_id, staff=True
        ).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        self.cohort_management_page = self.instructor_dashboard_page.select_cohort_management()
        self.cohort_management_page.wait_for_page()

        self.course_wide_key = 'course-wide'
        self.inline_key = 'inline'

    def cohort_discussion_topics_are_visible(self):
        """
        Assert that discussion topics are visible with appropriate content.
        """
        self.cohort_management_page.toggles_showing_of_discussion_topics()
        self.assertTrue(self.cohort_management_page.discussion_topics_visible())

        self.assertEqual(
            "Course-Wide Discussion Topics",
            self.cohort_management_page.cohort_discussion_heading_is_visible(self.course_wide_key)
        )
        self.assertTrue(self.cohort_management_page.is_save_button_disabled(self.course_wide_key))

        self.assertEqual(
            "Content-Specific Discussion Topics",
            self.cohort_management_page.cohort_discussion_heading_is_visible(self.inline_key)
        )
        self.assertTrue(self.cohort_management_page.is_save_button_disabled(self.inline_key))

    def save_and_verify_discussion_topics(self, key):
        """
        Saves the discussion topics and the verify the changes.
        """
        # click on the inline save button.
        self.cohort_management_page.save_discussion_topics(key)

        # verifies that changes saved successfully.
        confirmation_message = self.cohort_management_page.get_cohort_discussions_message(key=key)
        self.assertEqual("Your changes have been saved.", confirmation_message)

        # save button disabled again.
        self.assertTrue(self.cohort_management_page.is_save_button_disabled(key))

    def reload_page(self):
        """
        Refresh the page.
        """
        self.browser.refresh()
        self.cohort_management_page.wait_for_page()

        self.instructor_dashboard_page.select_cohort_management()
        self.cohort_management_page.wait_for_page()

        self.cohort_discussion_topics_are_visible()

    def verify_discussion_topics_after_reload(self, key, cohorted_topics):
        """
        Verifies the changed topics.
        """
        self.reload_page()
        self.assertEqual(self.cohort_management_page.get_cohorted_topics_count(key), cohorted_topics)

    def test_cohort_course_wide_discussion_topic(self):
        """
        Scenario: cohort a course-wide discussion topic.

        Given I have a course with a cohort defined,
        And a course-wide discussion with disabled Save button.
        When I click on the course-wide discussion topic
        Then I see the enabled save button
        When I click on save button
        Then I see success message
        When I reload the page
        Then I see the discussion topic selected
        """
        self.cohort_discussion_topics_are_visible()

        cohorted_topics_before = self.cohort_management_page.get_cohorted_topics_count(self.course_wide_key)
        self.cohort_management_page.select_discussion_topic(self.course_wide_key)

        self.assertFalse(self.cohort_management_page.is_save_button_disabled(self.course_wide_key))

        self.save_and_verify_discussion_topics(key=self.course_wide_key)
        cohorted_topics_after = self.cohort_management_page.get_cohorted_topics_count(self.course_wide_key)

        self.assertNotEqual(cohorted_topics_before, cohorted_topics_after)

        self.verify_discussion_topics_after_reload(self.course_wide_key, cohorted_topics_after)

    def test_always_cohort_inline_topic_enabled(self):
        """
        Scenario: Select the always_cohort_inline_topics radio button

        Given I have a course with a cohort defined,
        And a inline discussion topic with disabled Save button.
        When I click on always_cohort_inline_topics
        Then I see enabled save button
        And I see disabled inline discussion topics
        When I reload the page
        Then I see the option enabled
        """
        self.cohort_discussion_topics_are_visible()

        # enable always inline discussion topics.
        self.cohort_management_page.select_always_inline_discussion()

        self.assertTrue(self.cohort_management_page.inline_discussion_topics_disabled())

        self.reload_page()
        self.assertIsNotNone(self.cohort_management_page.always_inline_discussion_selected())

    def test_cohort_some_inline_topics_enabled(self):
        """
        Scenario: Select the cohort_some_inline_topics radio button

        Given I have a course with a cohort defined,
        And a inline discussion topic with disabled Save button.
        When I click on cohort_some_inline_topics
        Then I see enabled save button
        And I see enabled inline discussion topics
        When I reload the page
        Then I see the option enabled
        """
        self.cohort_discussion_topics_are_visible()

        # enable some inline discussion topic radio button.
        self.cohort_management_page.select_cohort_some_inline_discussion()
        # I see that save button is enabled
        self.assertFalse(self.cohort_management_page.is_save_button_disabled(self.inline_key))
        # I see that inline discussion topics are enabled
        self.assertFalse(self.cohort_management_page.inline_discussion_topics_disabled())

        self.reload_page()
        self.assertIsNotNone(self.cohort_management_page.cohort_some_inline_discussion_selected())

    def test_cohort_inline_discussion_topic(self):
        """
        Scenario: cohort inline discussion topic.

        Given I have a course with a cohort defined,
        And a inline discussion topic with disabled Save button.
        When I click on cohort_some_inline_discussion_topics
        Then I see enabled saved button
        And When I click on inline discussion topic
        And I see enabled save button
        And When i click save button
        Then I see success message
        When I reload the page
        Then I see the discussion topic selected
        """
        self.cohort_discussion_topics_are_visible()

        # select some inline discussion topics radio button.
        self.cohort_management_page.select_cohort_some_inline_discussion()

        cohorted_topics_before = self.cohort_management_page.get_cohorted_topics_count(self.inline_key)
        # check the discussion topic.
        self.cohort_management_page.select_discussion_topic(self.inline_key)

        # Save button enabled.
        self.assertFalse(self.cohort_management_page.is_save_button_disabled(self.inline_key))

        # verifies that changes saved successfully.
        self.save_and_verify_discussion_topics(key=self.inline_key)

        cohorted_topics_after = self.cohort_management_page.get_cohorted_topics_count(self.inline_key)
        self.assertNotEqual(cohorted_topics_before, cohorted_topics_after)

        self.verify_discussion_topics_after_reload(self.inline_key, cohorted_topics_after)

    def test_verify_that_selecting_the_final_child_selects_category(self):
        """
        Scenario: Category should be selected on selecting final child.

        Given I have a course with a cohort defined,
        And a inline discussion with disabled Save button.
        When I click on child topics
        Then I see enabled saved button
        Then I see parent category to be checked.
        """
        self.cohort_discussion_topics_are_visible()

        # enable some inline discussion topics.
        self.cohort_management_page.select_cohort_some_inline_discussion()

        # category should not be selected.
        self.assertFalse(self.cohort_management_page.is_category_selected())

        # check the discussion topic.
        self.cohort_management_page.select_discussion_topic(self.inline_key)

        # verify that category is selected.
        self.assertTrue(self.cohort_management_page.is_category_selected())

    def test_verify_that_deselecting_the_final_child_deselects_category(self):
        """
        Scenario: Category should be deselected on deselecting final child.

        Given I have a course with a cohort defined,
        And a inline discussion with disabled Save button.
        When I click on final child topics
        Then I see enabled saved button
        Then I see parent category to be deselected.
        """
        self.cohort_discussion_topics_are_visible()

        # enable some inline discussion topics.
        self.cohort_management_page.select_cohort_some_inline_discussion()

        # category should not be selected.
        self.assertFalse(self.cohort_management_page.is_category_selected())

        # check the discussion topic.
        self.cohort_management_page.select_discussion_topic(self.inline_key)

        # verify that category is selected.
        self.assertTrue(self.cohort_management_page.is_category_selected())

        # un-check the discussion topic.
        self.cohort_management_page.select_discussion_topic(self.inline_key)

        # category should not be selected.
        self.assertFalse(self.cohort_management_page.is_category_selected())

    def test_verify_that_correct_subset_of_category_being_selected_after_save(self):
        """
        Scenario: Category should be selected on selecting final child.

        Given I have a course with a cohort defined,
        And a inline discussion with disabled Save button.
        When I click on child topics
        Then I see enabled saved button
        When I select subset of category
        And I click on save button
        Then I see success message with
        same sub-category being selected
        """
        self.cohort_discussion_topics_are_visible()

        # enable some inline discussion topics.
        self.cohort_management_page.select_cohort_some_inline_discussion()

        # category should not be selected.
        self.assertFalse(self.cohort_management_page.is_category_selected())

        cohorted_topics_after = self.cohort_management_page.get_cohorted_topics_count(self.inline_key)

        # verifies that changes saved successfully.
        self.save_and_verify_discussion_topics(key=self.inline_key)

        # verify changes after reload.
        self.verify_discussion_topics_after_reload(self.inline_key, cohorted_topics_after)


@attr('shard_6')
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
        self.cohort_management_page = self.instructor_dashboard_page.select_cohort_management()

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
