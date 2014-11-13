# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS Instructor Dashboard.
"""

from ..helpers import UniqueCourseTest
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage
from ...fixtures.course import CourseFixture


class AutoEnrollmentWithCSVTest(UniqueCourseTest):
    """
    End-to-end tests for Auto-Registration and enrollment functionality via CSV file.
    """

    def setUp(self):
        super(AutoEnrollmentWithCSVTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()

        # login as an instructor
        AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        self.membership_page = self.instructor_dashboard_page.select_membership()

    def test_browse_and_upload_buttons_are_visible(self):
        # Given that I am on the Membership tab on the Instructor Dashboard
        # I see the 'REGISTER/ENROLL STUDENTS' section on the page with the 'Browse' and 'Upload' buttons
        self.assertTrue(self.instructor_dashboard_page.file_attachment_browse_button_is_visible())
        self.assertTrue(self.instructor_dashboard_page.is_upload_button_visible())

    def test_clicking_file_upload_button_without_file_shows_error(self):
        # Given that I am on the Membership tab on the Instructor Dashboard

        # When I click the Upload Button without specifying a CSV file
        self.instructor_dashboard_page.click_upload_file_button()

        # Then I should be shown an Error Notification
        self.assertTrue(self.instructor_dashboard_page.is_notification_displayed(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR))

        # And The Notification message should read 'File is not attached.'
        self.assertEqual(self.instructor_dashboard_page.first_notification_message(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR), "File is not attached.")

    def test_uploading_correct_csv_file_results_in_success(self):
        # Given that I am on the Membership tab on the Instructor Dashboard

        # When I select a csv file with correct data and click the Upload Button
        self.instructor_dashboard_page.upload_correct_csv_file()

        # Then I should be shown a Success Notification.
        self.assertTrue(self.instructor_dashboard_page.is_notification_displayed(section_type=self.instructor_dashboard_page.NOTIFICATION_SUCCESS))

    def test_uploading_csv_file_with_bad_data_results_in_errors_and_warnings(self):
        # Given that I am on the Membership tab on the Instructor Dashboard

        # When I select a csv file with incorrect data and click the Upload Button
        self.instructor_dashboard_page.upload_csv_file_with_errors_warnings()

        # Then I should be shown an Error Notification
        self.assertTrue(self.instructor_dashboard_page.is_notification_displayed(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR))

        # And a corresponding Error Message.
        self.assertEqual(self.instructor_dashboard_page.first_notification_message(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR), "Data in row #2 must have exactly four columns: email, username, full name, and country")

        # And I should be shown a Warning Notification
        self.assertTrue(self.instructor_dashboard_page.is_notification_displayed(section_type=self.instructor_dashboard_page.NOTIFICATION_WARNING))

        # And a corresponding Warning Message.
        self.assertEqual(self.instructor_dashboard_page.first_notification_message(section_type=self.instructor_dashboard_page.NOTIFICATION_WARNING), "ename (d@a.com): (An account with email d@a.com exists but the provided username ename is different. Enrolling anyway with d@a.com.)")

    def test_uploading_non_csv_file_results_in_error(self):
        # Given that I am on the Membership tab on the Instructor Dashboard

        # When I select an image file (a non-csv file) and click the Upload Button
        self.instructor_dashboard_page.upload_non_csv_file()

        # Then I should be shown an Error Notification
        self.assertTrue(self.instructor_dashboard_page.is_notification_displayed(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR))

        # And The Notification message should read 'Make sure that the file you upload is in CSV format.....'
        self.assertEqual(self.instructor_dashboard_page.first_notification_message(section_type=self.instructor_dashboard_page.NOTIFICATION_ERROR), "Make sure that the file you upload is in CSV format with no extraneous characters or rows.")
