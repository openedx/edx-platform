# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS Instructor Dashboard.
"""

from ..helpers import UniqueCourseTest, get_modal_alert
from ...pages.common.logout import LogoutPage
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
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        self.auto_enroll_section = instructor_dashboard_page.select_membership().select_auto_enroll_section()

    def test_browse_and_upload_buttons_are_visible(self):
        """
        Scenario: On the Membership tab of the Instructor Dashboard, Auto-Enroll Browse and Upload buttons are visible.
            Given that I am on the Membership tab on the Instructor Dashboard
            Then I see the 'REGISTER/ENROLL STUDENTS' section on the page with the 'Browse' and 'Upload' buttons
        """
        self.assertTrue(self.auto_enroll_section.is_file_attachment_browse_button_visible())
        self.assertTrue(self.auto_enroll_section.is_upload_button_visible())

    def test_clicking_file_upload_button_without_file_shows_error(self):
        """
        Scenario: Clicking on the upload button without specifying a CSV file results in error.
            Given that I am on the Membership tab on the Instructor Dashboard
            When I click the Upload Button without specifying a CSV file
            Then I should be shown an Error Notification
            And The Notification message should read 'File is not attached.'
        """
        self.auto_enroll_section.click_upload_file_button()
        self.assertTrue(self.auto_enroll_section.is_notification_displayed(section_type=self.auto_enroll_section.NOTIFICATION_ERROR))
        self.assertEqual(self.auto_enroll_section.first_notification_message(section_type=self.auto_enroll_section.NOTIFICATION_ERROR), "File is not attached.")

    def test_uploading_correct_csv_file_results_in_success(self):
        """
        Scenario: Uploading a CSV with correct data results in Success.
            Given that I am on the Membership tab on the Instructor Dashboard
            When I select a csv file with correct data and click the Upload Button
            Then I should be shown a Success Notification.
        """
        self.auto_enroll_section.upload_correct_csv_file()
        self.assertTrue(self.auto_enroll_section.is_notification_displayed(section_type=self.auto_enroll_section.NOTIFICATION_SUCCESS))

    def test_uploading_csv_file_with_bad_data_results_in_errors_and_warnings(self):
        """
        Scenario: Uploading a CSV with incorrect data results in error and warnings.
            Given that I am on the Membership tab on the Instructor Dashboard
            When I select a csv file with incorrect data and click the Upload Button
            Then I should be shown an Error Notification
            And a corresponding Error Message.
            And I should be shown a Warning Notification
            And a corresponding Warning Message.
        """
        self.auto_enroll_section.upload_csv_file_with_errors_warnings()
        self.assertTrue(self.auto_enroll_section.is_notification_displayed(section_type=self.auto_enroll_section.NOTIFICATION_ERROR))
        self.assertEqual(self.auto_enroll_section.first_notification_message(section_type=self.auto_enroll_section.NOTIFICATION_ERROR), "Data in row #2 must have exactly four columns: email, username, full name, and country")
        self.assertTrue(self.auto_enroll_section.is_notification_displayed(section_type=self.auto_enroll_section.NOTIFICATION_WARNING))
        self.assertEqual(self.auto_enroll_section.first_notification_message(section_type=self.auto_enroll_section.NOTIFICATION_WARNING), "ename (d@a.com): (An account with email d@a.com exists but the provided username ename is different. Enrolling anyway with d@a.com.)")

    def test_uploading_non_csv_file_results_in_error(self):
        """
        Scenario: Uploading an image file for auto-enrollment results in error.
            Given that I am on the Membership tab on the Instructor Dashboard
            When I select an image file (a non-csv file) and click the Upload Button
            Then I should be shown an Error Notification
            And The Notification message should read 'Make sure that the file you upload is in CSV..'
        """
        self.auto_enroll_section.upload_non_csv_file()
        self.assertTrue(self.auto_enroll_section.is_notification_displayed(section_type=self.auto_enroll_section.NOTIFICATION_ERROR))
        self.assertEqual(self.auto_enroll_section.first_notification_message(section_type=self.auto_enroll_section.NOTIFICATION_ERROR), "Make sure that the file you upload is in CSV format with no extraneous characters or rows.")


class EntranceExamGradeTest(UniqueCourseTest):
    """
    Tests for Entrance exam specific student grading tasks.
    """

    def setUp(self):
        super(EntranceExamGradeTest, self).setUp()
        self.course_info.update({"settings": {"entrance_exam_enabled": "true"}})
        CourseFixture(**self.course_info).install()
        self.student_identifier = "johndoe_saee@example.com"
        # Create the user (automatically logs us in)
        AutoAuthPage(
            self.browser,
            username="johndoe_saee",
            email=self.student_identifier,
            course_id=self.course_id,
            staff=False
        ).visit()

        LogoutPage(self.browser).visit()

        # login as an instructor
        AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit()

        # go to the student admin page on the instructor dashboard
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        self.student_admin_section = instructor_dashboard_page.select_student_admin()

    def test_input_text_and_buttons_are_visible(self):
        """
        Scenario: On the Student admin tab of the Instructor Dashboard, Student Email input box,
        Reset Student Attempt, Rescore Student Submission, Delete Student State for entrance exam
            and Show Background Task History for Student buttons are visible
            Given that I am on the Student Admin tab on the Instructor Dashboard
            Then I see Student Email input box, Reset Student Attempt, Rescore Student Submission,
            Delete Student State for entrance exam and Show Background Task History for Student buttons
        """
        self.assertTrue(self.student_admin_section.is_student_email_input_visible())
        self.assertTrue(self.student_admin_section.is_reset_attempts_button_visible())
        self.assertTrue(self.student_admin_section.is_rescore_submission_button_visible())
        self.assertTrue(self.student_admin_section.is_delete_student_state_button_visible())
        self.assertTrue(self.student_admin_section.is_background_task_history_button_visible())

    def test_clicking_reset_student_attempts_button_without_email_shows_error(self):
        """
        Scenario: Clicking on the Reset Student Attempts button without entering student email
        address or username results in error.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Reset Student Attempts Button  under Entrance Exam Grade
            Adjustment without enter an email address
            Then I should be shown an Error Notification
            And The Notification message should read 'Please enter a student email address or username.'
        """
        self.student_admin_section.click_reset_attempts_button()
        self.assertEqual(
            'Please enter a student email address or username.',
            self.student_admin_section.top_notification.text[0]
        )

    def test_clicking_reset_student_attempts_button_with_success(self):
        """
        Scenario: Clicking on the Reset Student Attempts button with valid student email
        address or username should result in success prompt.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Reset Student Attempts Button under Entrance Exam Grade
            Adjustment after entering a valid student
            email address or username
            Then I should be shown an alert with success message
        """
        self.student_admin_section.set_student_email(self.student_identifier)
        self.student_admin_section.click_reset_attempts_button()
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.dismiss()

    def test_clicking_reset_student_attempts_button_with_error(self):
        """
        Scenario: Clicking on the Reset Student Attempts button with email address or username
        of a non existing student should result in error message.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Reset Student Attempts Button  under Entrance Exam Grade
            Adjustment after non existing student email address or username
            Then I should be shown an error message
        """
        self.student_admin_section.set_student_email('non_existing@example.com')
        self.student_admin_section.click_reset_attempts_button()
        self.student_admin_section.wait_for_ajax()
        self.assertGreater(len(self.student_admin_section.top_notification.text[0]), 0)

    def test_clicking_rescore_submission_button_with_success(self):
        """
        Scenario: Clicking on the Rescore Student Submission button with valid student email
        address or username should result in success prompt.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Rescore Student Submission Button  under Entrance Exam Grade
            Adjustment after entering a valid student email address or username
            Then I should be shown an alert with success message
        """
        self.student_admin_section.set_student_email(self.student_identifier)
        self.student_admin_section.click_rescore_submissions_button()
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.dismiss()

    def test_clicking_rescore_submission_button_with_error(self):
        """
        Scenario: Clicking on the Rescore Student Submission button with email address or username
        of a non existing student should result in error message.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Rescore Student Submission Button under Entrance Exam Grade
            Adjustment after non existing student email address or username
            Then I should be shown an error message
        """
        self.student_admin_section.set_student_email('non_existing@example.com')
        self.student_admin_section.click_rescore_submissions_button()
        self.student_admin_section.wait_for_ajax()
        self.assertGreater(len(self.student_admin_section.top_notification.text[0]), 0)

    def test_clicking_skip_entrance_exam_button_with_success(self):
        """
        Scenario: Clicking on the  Let Student Skip Entrance Exam button with
        valid student email address or username should result in success prompt.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the  Let Student Skip Entrance Exam Button under
            Entrance Exam Grade Adjustment after entering a valid student
            email address or username
            Then I should be shown an alert with success message
        """
        self.student_admin_section.set_student_email(self.student_identifier)
        self.student_admin_section.click_skip_entrance_exam_button()
        #first we have window.confirm
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.accept()

        # then we have alert confirming action
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.dismiss()

    def test_clicking_skip_entrance_exam_button_with_error(self):
        """
        Scenario: Clicking on the Let Student Skip Entrance Exam button with
        email address or username of a non existing student should result in error message.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Let Student Skip Entrance Exam Button under
            Entrance Exam Grade Adjustment after entering non existing
            student email address or username
            Then I should be shown an error message
        """
        self.student_admin_section.set_student_email('non_existing@example.com')
        self.student_admin_section.click_skip_entrance_exam_button()
        #first we have window.confirm
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.accept()

        self.student_admin_section.wait_for_ajax()
        self.assertGreater(len(self.student_admin_section.top_notification.text[0]), 0)

    def test_clicking_delete_student_attempts_button_with_success(self):
        """
        Scenario: Clicking on the Delete Student State for entrance exam button
        with valid student email address or username should result in success prompt.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Delete Student State for entrance exam Button
            under Entrance Exam Grade Adjustment after entering a valid student
            email address or username
            Then I should be shown an alert with success message
        """
        self.student_admin_section.set_student_email(self.student_identifier)
        self.student_admin_section.click_delete_student_state_button()
        alert = get_modal_alert(self.student_admin_section.browser)
        alert.dismiss()

    def test_clicking_delete_student_attempts_button_with_error(self):
        """
        Scenario: Clicking on the Delete Student State for entrance exam button
        with email address or username of a non existing student should result
        in error message.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Delete Student State for entrance exam Button
            under Entrance Exam Grade Adjustment after non existing student
            email address or username
            Then I should be shown an error message
        """
        self.student_admin_section.set_student_email('non_existing@example.com')
        self.student_admin_section.click_delete_student_state_button()
        self.student_admin_section.wait_for_ajax()
        self.assertGreater(len(self.student_admin_section.top_notification.text[0]), 0)

    def test_clicking_task_history_button_with_success(self):
        """
        Scenario: Clicking on the Show Background Task History for Student
        with valid student email address or username should result in table of tasks.
            Given that I am on the Student Admin tab on the Instructor Dashboard
            When I click the Show Background Task History for Student Button
            under Entrance Exam Grade Adjustment after entering a valid student
            email address or username
            Then I should be shown an table listing all background tasks
        """
        self.student_admin_section.set_student_email(self.student_identifier)
        self.student_admin_section.click_task_history_button()
        self.assertTrue(self.student_admin_section.is_background_task_history_table_visible())
