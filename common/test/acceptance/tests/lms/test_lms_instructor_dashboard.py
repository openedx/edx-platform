# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS Instructor Dashboard.
"""

import ddt

from nose.plugins.attrib import attr
from bok_choy.promise import EmptyPromise

from ..helpers import UniqueCourseTest, get_modal_alert, EventsTestMixin
from ...pages.common.logout import LogoutPage
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.lms.create_mode import ModeCreationPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.instructor_dashboard import InstructorDashboardPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.dashboard import DashboardPage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.track_selection import TrackSelectionPage
from ...pages.lms.pay_and_verify import PaymentAndVerificationFlow, FakePaymentPage
from ...pages.lms.login_and_register import CombinedLoginAndRegisterPage
from common.test.acceptance.tests.helpers import disable_animations
from ...fixtures.certificates import CertificateConfigFixture


class BaseInstructorDashboardTest(EventsTestMixin, UniqueCourseTest):
    """
    Mixin class for testing the instructor dashboard.
    """
    def log_in_as_instructor(self):
        """
        Logs in as an instructor and returns the id.
        """
        username = "test_instructor_{uuid}".format(uuid=self.unique_id[0:6])
        auto_auth_page = AutoAuthPage(self.browser, username=username, course_id=self.course_id, staff=True)
        return username, auto_auth_page.visit().get_user_id()

    def visit_instructor_dashboard(self):
        """
        Visits the instructor dashboard.
        """
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        return instructor_dashboard_page


@attr('a11y')
class LMSInstructorDashboardA11yTest(BaseInstructorDashboardTest):
    """
    Instructor dashboard base accessibility test.
    """
    def setUp(self):
        super(LMSInstructorDashboardA11yTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()

    def test_instructor_dashboard_a11y(self):
        self.instructor_dashboard_page.a11y_audit.config.set_rules({
            "ignore": [
                'link-href',  # TODO: AC-491
                'data-table',  # TODO: AC-491
            ]
        })
        self.instructor_dashboard_page.a11y_audit.check_for_accessibility_errors()


@ddt.ddt
class BulkEmailTest(BaseInstructorDashboardTest):
    """
    End-to-end tests for bulk emailing from instructor dash.
    """
    def setUp(self):
        super(BulkEmailTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        instructor_dashboard_page = self.visit_instructor_dashboard()
        self.send_email_page = instructor_dashboard_page.select_bulk_email()

    @ddt.data(["myself"], ["staff"], ["learners"], ["myself", "staff", "learners"])
    def test_email_queued_for_sending(self, recipient):
        self.assertTrue(self.send_email_page.is_browser_on_page())
        self.send_email_page.send_message(recipient)
        self.send_email_page.verify_message_queued_successfully()

    @attr('a11y')
    def test_bulk_email_a11y(self):
        """
        Bulk email accessibility tests
        """
        self.send_email_page.a11y_audit.config.set_scope([
            '#section-send-email'
        ])
        self.send_email_page.a11y_audit.config.set_rules({
            "ignore": [
                'button-name',  # TinyMCE button is missing accessible text
                'color-contrast',  # TODO: AC-491
            ]
        })
        self.send_email_page.a11y_audit.check_for_accessibility_errors()


@attr('shard_7')
class AutoEnrollmentWithCSVTest(BaseInstructorDashboardTest):
    """
    End-to-end tests for Auto-Registration and enrollment functionality via CSV file.
    """

    def setUp(self):
        super(AutoEnrollmentWithCSVTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        instructor_dashboard_page = self.visit_instructor_dashboard()
        self.auto_enroll_section = instructor_dashboard_page.select_membership().select_auto_enroll_section()
        # Initialize the page objects
        self.register_page = CombinedLoginAndRegisterPage(self.browser, start_page="register")
        self.dashboard_page = DashboardPage(self.browser)

    def test_browse_and_upload_buttons_are_visible(self):
        """
        Scenario: On the Membership tab of the Instructor Dashboard, Auto-Enroll Browse and Upload buttons are visible.
            Given that I am on the Membership tab on the Instructor Dashboard
            Then I see the 'REGISTER/ENROLL STUDENTS' section on the page with the 'Browse' and 'Upload' buttons
        """
        self.assertTrue(self.auto_enroll_section.is_file_attachment_browse_button_visible())
        self.assertTrue(self.auto_enroll_section.is_upload_button_visible())

    def test_enroll_unregister_student(self):
        """
        Scenario: On the Membership tab of the Instructor Dashboard, Batch Enrollment div is visible.
            Given that I am on the Membership tab on the Instructor Dashboard
            Then I enter the email and enroll it.
            Logout the current page.
            And Navigate to the registration page and register the student.
            Then I see the course which enrolled the student.
        """
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        email = "{user}@example.com".format(user=username)
        self.auto_enroll_section.fill_enrollment_batch_text_box(email)
        self.assertIn(
            'Successfully sent enrollment emails to the following users. '
            'They will be enrolled once they register:',
            self.auto_enroll_section.get_notification_text()
        )
        LogoutPage(self.browser).visit()
        self.register_page.visit()
        self.register_page.register(
            email=email,
            password="123456",
            username=username,
            full_name="Test User",
            terms_of_service=True,
            country="US",
            favorite_movie="Harry Potter",
        )
        course_names = self.dashboard_page.wait_for_page().available_courses
        self.assertEquals(len(course_names), 1)
        self.assertIn(self.course_info["display_name"], course_names)

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

    @attr('a11y')
    def test_auto_enroll_csv_a11y(self):
        """
        Auto-enrollment with CSV accessibility tests
        """
        self.auto_enroll_section.a11y_audit.config.set_scope([
            '#member-list-widget-template'
        ])
        self.auto_enroll_section.a11y_audit.check_for_accessibility_errors()


@attr('shard_7')
class ProctoredExamsTest(BaseInstructorDashboardTest):
    """
    End-to-end tests for Proctoring Sections of the Instructor Dashboard.
    """

    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(ProctoredExamsTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        course_fixture = CourseFixture(**self.course_info)
        course_fixture.add_advanced_settings({
            "enable_proctored_exams": {"value": "true"}
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            )
        ).install()

        self.track_selection_page = TrackSelectionPage(self.browser, self.course_id)
        self.payment_and_verification_flow = PaymentAndVerificationFlow(self.browser, self.course_id)
        self.immediate_verification_page = PaymentAndVerificationFlow(
            self.browser, self.course_id, entry_point='verify-now'
        )
        self.upgrade_page = PaymentAndVerificationFlow(self.browser, self.course_id, entry_point='upgrade')
        self.fake_payment_page = FakePaymentPage(self.browser, self.course_id)
        self.dashboard_page = DashboardPage(self.browser)
        self.problem_page = ProblemPage(self.browser)

        # Add a verified mode to the course
        ModeCreationPage(
            self.browser, self.course_id, mode_slug=u'verified', mode_display_name=u'Verified Certificate',
            min_price=10, suggested_prices='10,20'
        ).visit()

        # Auto-auth register for the course.
        self._auto_auth(self.USERNAME, self.EMAIL, False)

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()

    def _login_as_a_verified_user(self):
        """
        login as a verififed user
        """

        self._auto_auth(self.USERNAME, self.EMAIL, False)

        # the track selection page cannot be visited. see the other tests to see if any prereq is there.
        # Navigate to the track selection page
        self.track_selection_page.visit()

        # Enter the payment and verification flow by choosing to enroll as verified
        self.track_selection_page.enroll('verified')

        # Proceed to the fake payment page
        self.payment_and_verification_flow.proceed_to_payment()

        # Submit payment
        self.fake_payment_page.submit_payment()

    def _create_a_proctored_exam_and_attempt(self):
        """
        Creates a proctored exam and makes the student attempt it so that
        the associated allowance and attempts are visible on the Instructor Dashboard.
        """
        # Visit the course outline page in studio
        LogoutPage(self.browser).visit()
        self._auto_auth("STAFF_TESTER", "staff101@example.com", True)
        self.course_outline.visit()

        # open the exam settings to make it a proctored exam.
        self.course_outline.open_subsection_settings_dialog()

        # select advanced settings tab
        self.course_outline.select_advanced_tab()

        self.course_outline.make_exam_proctored()

        # login as a verified student and visit the courseware.
        LogoutPage(self.browser).visit()
        self._login_as_a_verified_user()
        self.courseware_page.visit()

        # Start the proctored exam.
        self.courseware_page.start_proctored_exam()

    def _create_a_timed_exam_and_attempt(self):
        """
        Creates a timed exam and makes the student attempt it so that
        the associated allowance and attempts are visible on the Instructor Dashboard.
        """
        # Visit the course outline page in studio
        LogoutPage(self.browser).visit()
        self._auto_auth("STAFF_TESTER", "staff101@example.com", True)
        self.course_outline.visit()

        # open the exam settings to make it a proctored exam.
        self.course_outline.open_subsection_settings_dialog()

        # select advanced settings tab
        self.course_outline.select_advanced_tab()

        self.course_outline.make_exam_timed()

        # login as a verified student and visit the courseware.
        LogoutPage(self.browser).visit()
        self._login_as_a_verified_user()
        self.courseware_page.visit()

        # Start the timed exam.
        self.courseware_page.start_timed_exam()

        # Stop the timed exam.
        self.courseware_page.stop_timed_exam()

    def test_can_add_remove_allowance(self):
        """
        Make sure that allowances can be added and removed.
        """
        # Given that an exam has been configured to be a timed exam.
        self._create_a_timed_exam_and_attempt()

        # When I log in as an instructor,
        __, __ = self.log_in_as_instructor()

        # And visit the Allowance Section of Instructor Dashboard's Special Exams tab
        instructor_dashboard_page = self.visit_instructor_dashboard()
        allowance_section = instructor_dashboard_page.select_special_exams().select_allowance_section()

        # Then I can add Allowance to that exam for a student
        self.assertTrue(allowance_section.is_add_allowance_button_visible)

        # When I click the Add Allowance button
        allowance_section.click_add_allowance_button()

        # Then popup should be visible
        self.assertTrue(allowance_section.is_add_allowance_popup_visible)

        # When I fill and submit the allowance form
        allowance_section.submit_allowance_form('10', self.USERNAME)

        # Then, the added record should be visible
        self.assertTrue(allowance_section.is_allowance_record_visible)

    def test_can_reset_attempts(self):
        """
        Make sure that Exam attempts are visible and can be reset.
        """
        # Given that an exam has been configured to be a proctored exam.
        self._create_a_timed_exam_and_attempt()

        # When I log in as an instructor,
        __, __ = self.log_in_as_instructor()

        # And visit the Student Proctored Exam Attempts Section of Instructor Dashboard's Special Exams tab
        instructor_dashboard_page = self.visit_instructor_dashboard()
        exam_attempts_section = instructor_dashboard_page.select_special_exams().select_exam_attempts_section()

        # Then I can see the search text field
        self.assertTrue(exam_attempts_section.is_search_text_field_visible)

        # And I can see one attempt by a student.
        self.assertTrue(exam_attempts_section.is_student_attempt_visible)

        # And I can remove the attempt by clicking the "x" at the end of the row.
        exam_attempts_section.remove_student_attempt()
        self.assertFalse(exam_attempts_section.is_student_attempt_visible)


@attr('shard_7')
class EntranceExamGradeTest(BaseInstructorDashboardTest):
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

        # go to the student admin page on the instructor dashboard
        self.log_in_as_instructor()
        self.student_admin_section = self.visit_instructor_dashboard().select_student_admin()

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


@attr('shard_7')
class DataDownloadsTest(BaseInstructorDashboardTest):
    """
    Bok Choy tests for the "Data Downloads" tab.
    """
    def setUp(self):
        super(DataDownloadsTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.instructor_username, self.instructor_id = self.log_in_as_instructor()
        instructor_dashboard_page = self.visit_instructor_dashboard()
        self.data_download_section = instructor_dashboard_page.select_data_download()

    def verify_report_requested_event(self, report_type):
        """
        Verifies that the correct event is emitted when a report is requested.
        """
        self.assert_matching_events_were_emitted(
            event_filter={'name': u'edx.instructor.report.requested', 'report_type': report_type}
        )

    def verify_report_downloaded_event(self, report_url):
        """
        Verifies that the correct event is emitted when a report is downloaded.
        """
        self.assert_matching_events_were_emitted(
            event_filter={'name': u'edx.instructor.report.downloaded', 'report_url': report_url}
        )

    def verify_report_download(self, report_name):
        """
        Verifies that a report can be downloaded and an event fired.
        """
        download_links = self.data_download_section.report_download_links
        self.assertEquals(len(download_links), 1)
        download_links[0].click()
        expected_url = download_links.attrs('href')[0]
        self.assertIn(report_name, expected_url)
        self.verify_report_downloaded_event(expected_url)

    def test_student_profiles_report_download(self):
        """
        Scenario: Verify that an instructor can download a student profiles report

        Given that I am an instructor
        And I visit the instructor dashboard's "Data Downloads" tab
        And I click on the "Download profile information as a CSV" button
        Then a report should be generated
        And a report requested event should be emitted
        When I click on the report
        Then a report downloaded event should be emitted
        """
        report_name = u"student_profile_info"
        self.data_download_section.generate_student_report_button.click()
        self.data_download_section.wait_for_available_report()
        self.verify_report_requested_event(report_name)
        self.verify_report_download(report_name)

    def test_grade_report_download(self):
        """
        Scenario: Verify that an instructor can download a grade report

        Given that I am an instructor
        And I visit the instructor dashboard's "Data Downloads" tab
        And I click on the "Generate Grade Report" button
        Then a report should be generated
        And a report requested event should be emitted
        When I click on the report
        Then a report downloaded event should be emitted
        """
        report_name = u"grade_report"
        self.data_download_section.generate_grade_report_button.click()
        self.data_download_section.wait_for_available_report()
        self.verify_report_requested_event(report_name)
        self.verify_report_download(report_name)

    def test_problem_grade_report_download(self):
        """
        Scenario: Verify that an instructor can download a problem grade report

        Given that I am an instructor
        And I visit the instructor dashboard's "Data Downloads" tab
        And I click on the "Generate Problem Grade Report" button
        Then a report should be generated
        And a report requested event should be emitted
        When I click on the report
        Then a report downloaded event should be emitted
        """
        report_name = u"problem_grade_report"
        self.data_download_section.generate_problem_report_button.click()
        self.data_download_section.wait_for_available_report()
        self.verify_report_requested_event(report_name)
        self.verify_report_download(report_name)

    def test_ora2_response_report_download(self):
        """
        Scenario: Verify that an instructor can download an ORA2 grade report

        Given that I am an instructor
        And I visit the instructor dashboard's "Data Downloads" tab
        And I click on the "Download ORA2 Responses" button
        Then a report should be generated
        """
        report_name = u"ORA_data"
        self.data_download_section.generate_ora2_response_report_button.click()
        self.data_download_section.wait_for_available_report()
        self.verify_report_download(report_name)

    @attr('a11y')
    def test_data_download_a11y(self):
        """
        Data download page accessibility tests
        """
        self.data_download_section.a11y_audit.config.set_scope([
            '.data-download-container'
        ])
        self.data_download_section.a11y_audit.check_for_accessibility_errors()


@attr('shard_7')
@ddt.ddt
class CertificatesTest(BaseInstructorDashboardTest):
    """
    Tests for Certificates functionality on instructor dashboard.
    """

    def setUp(self):
        super(CertificatesTest, self).setUp()
        self.test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }
        CourseFixture(**self.course_info).install()
        self.cert_fixture = CertificateConfigFixture(self.course_id, self.test_certificate_config)
        self.cert_fixture.install()
        self.user_name, self.user_id = self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()
        disable_animations(self.certificates_section)

    def test_generate_certificates_buttons_is_disable(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Generate Certificates button is disable.
            Given that I am on the Certificates tab on the Instructor Dashboard
            The instructor-generation and cert_html_view_enabled feature flags have been enabled
            But the certificate is not active in settings.
            Then I see a 'Generate Certificates' button disabled
        """
        self.test_certificate_config['is_active'] = False
        self.cert_fixture.update_certificate(1)
        self.browser.refresh()
        self.assertFalse(self.certificates_section.generate_certificates_button.visible)
        self.assertTrue(self.certificates_section.generate_certificates_disabled_button.visible)

    def test_generate_certificates_buttons_is_visible(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Generate Certificates button is visible.
            Given that I am on the Certificates tab on the Instructor Dashboard
            And the instructor-generation feature flag has been enabled
            Then I see a 'Generate Certificates' button
            And when I click on the 'Generate Certificates' button
            Then I should see a status message and 'Generate Certificates' button should be disabled.
        """
        self.assertTrue(self.certificates_section.generate_certificates_button.visible)
        self.certificates_section.generate_certificates_button.click()
        alert = get_modal_alert(self.certificates_section.browser)
        alert.accept()

        self.certificates_section.wait_for_ajax()
        EmptyPromise(
            lambda: self.certificates_section.certificate_generation_status.visible,
            'Certificate generation status shown'
        ).fulfill()
        disabled = self.certificates_section.generate_certificates_button.attrs('disabled')
        self.assertEqual(disabled[0], 'true')

    def test_pending_tasks_section_is_visible(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Pending Instructor Tasks section is visible.
            Given that I am on the Certificates tab on the Instructor Dashboard
            Then I see 'Pending Instructor Tasks' section
        """
        self.assertTrue(self.certificates_section.pending_tasks_section.visible)

    def test_certificate_exceptions_section_is_visible(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Certificate Exceptions section is visible.
            Given that I am on the Certificates tab on the Instructor Dashboard
            Then I see 'CERTIFICATE EXCEPTIONS' section
        """
        self.assertTrue(self.certificates_section.certificate_exceptions_section.visible)

    def test_instructor_can_add_certificate_exception(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can add new certificate
        exception to list.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username and notes fields and click 'Add Exception' button
            Then new certificate exception should be visible in certificate exceptions list
        """
        notes = 'Test Notes'
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, notes)
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(notes, self.certificates_section.last_certificate_exception.text)

        # Verify that added exceptions are also synced with backend
        # Revisit Page
        self.certificates_section.refresh()

        # wait for the certificate exception section to render
        self.certificates_section.wait_for_certificate_exceptions_section()

        # validate certificate exception synced with server is visible in certificate exceptions list
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(notes, self.certificates_section.last_certificate_exception.text)

    def test_remove_certificate_exception_on_page_reload(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can remove added certificate
        exceptions from the list.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username and notes fields and click 'Add Exception' button
            Then new certificate exception should be visible in certificate exceptions list

            Revisit the page to make sure exceptions are synced.

            Remove the user from the exception list should remove the user from the list.
        """
        notes = 'Test Notes'
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, notes)
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(notes, self.certificates_section.last_certificate_exception.text)

        # Verify that added exceptions are also synced with backend
        # Revisit Page
        self.certificates_section.refresh()

        # Remove Certificate Exception
        self.certificates_section.remove_first_certificate_exception()
        self.assertNotIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertNotIn(notes, self.certificates_section.last_certificate_exception.text)

    def test_instructor_can_remove_certificate_exception(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can remove  added certificate
        exceptions from the list.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username and notes fields and click 'Add Exception' button
            Then new certificate exception should be visible in certificate exceptions list
        """
        notes = 'Test Notes'
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, notes)
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(notes, self.certificates_section.last_certificate_exception.text)

        # Remove Certificate Exception
        self.certificates_section.remove_first_certificate_exception()
        self.assertNotIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertNotIn(notes, self.certificates_section.last_certificate_exception.text)

        # Verify that added exceptions are also synced with backend
        # Revisit Page
        self.certificates_section.refresh()

        # wait for the certificate exception section to render
        self.certificates_section.wait_for_certificate_exceptions_section()

        # validate certificate exception synced with server is visible in certificate exceptions list
        self.assertNotIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertNotIn(notes, self.certificates_section.last_certificate_exception.text)

    def test_error_on_duplicate_certificate_exception(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard,
        Error message appears if student being added already exists in certificate exceptions list

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username that already is in the list and click 'Add Exception' button
            Then Error Message should say 'User (username/email={user}) already in exception list.'
        """
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, '')

        # Add duplicate student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, '')

        self.assertIn(
            '{user} already in exception list.'.format(user=self.user_name),
            self.certificates_section.message.text
        )

    def test_error_on_empty_user_name(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard,
        Error message appears if no username/email is entered while clicking "Add Exception" button

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I click on 'Add Exception' button
            AND student username/email field is empty
            Then Error Message should say
                'Student username/email field is required and can not be empty. '
                'Kindly fill in username/email and then press "Add Exception" button.'
        """
        # Click 'Add Exception' button without filling username/email field
        self.certificates_section.wait_for_certificate_exceptions_section()
        self.certificates_section.click_add_exception_button()

        self.assertIn(
            'Student username/email field is required and can not be empty. '
            'Kindly fill in username/email and then press "Add to Exception List" button.',
            self.certificates_section.message.text
        )

    def test_error_on_non_existing_user(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard,
        Error message appears if username/email does not exists in the system while clicking "Add Exception" button

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I click on 'Add Exception' button
            AND student username/email does not exists
            Then Error Message should say
                'Student username/email field is required and can not be empty. '
                'Kindly fill in username/email and then press "Add Exception" button.
        """
        invalid_user = 'test_user_non_existent'
        # Click 'Add Exception' button with invalid username/email field
        self.certificates_section.wait_for_certificate_exceptions_section()

        self.certificates_section.fill_user_name_field(invalid_user)
        self.certificates_section.click_add_exception_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            "{user} does not exist in the LMS. Please check your spelling and retry.".format(user=invalid_user),
            self.certificates_section.message.text
        )

    def test_user_not_enrolled_error(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard,
        Error message appears if user is not enrolled in the course while trying to add a new exception.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I click on 'Add Exception' button
            AND student is not enrolled in the course
            Then Error Message should say
                "The user (username/email={user}) you have entered is not enrolled in this course.
                Make sure the username or email address is correct, then try again."
        """
        new_user = 'test_user_{uuid}'.format(uuid=self.unique_id[6:12])
        new_email = 'test_user_{uuid}@example.com'.format(uuid=self.unique_id[6:12])
        # Create a new user who is not enrolled in the course
        AutoAuthPage(self.browser, username=new_user, email=new_email).visit()
        # Login as instructor and visit Certificate Section of Instructor Dashboard
        self.user_name, self.user_id = self.log_in_as_instructor()
        self.instructor_dashboard_page.visit()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()

        # Click 'Add Exception' button with invalid username/email field
        self.certificates_section.wait_for_certificate_exceptions_section()

        self.certificates_section.fill_user_name_field(new_user)
        self.certificates_section.click_add_exception_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            "{user} is not enrolled in this course. Please check your spelling and retry.".format(user=new_user),
            self.certificates_section.message.text
        )

    def test_generate_certificate_exception(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, when user clicks
        'Generate Exception Certificates' newly added certificate exceptions should be synced on server

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I click 'Generate Exception Certificates'
            Then newly added certificate exceptions should be synced on server
        """
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, '')

        # Click 'Generate Exception Certificates' button
        self.certificates_section.click_generate_certificate_exceptions_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            self.user_name + ' has been successfully added to the exception list. Click Generate Exception Certificate'
                             ' below to send the certificate.',
            self.certificates_section.message.text
        )

    @ddt.data(
        ('Test \nNotes', 'Test Notes'),
        ('<Test>Notes</Test>', '<Test>Notes</Test>'),
    )
    @ddt.unpack
    def test_notes_escaped_in_add_certificate_exception(self, notes, expected_notes):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can add new certificate
        exception to list.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username and notes (which contains character which are needed to be escaped)
            and click 'Add Exception' button, then new certificate exception should be visible in
            certificate exceptions list.
        """
        # Add a student to Certificate exception list
        self.certificates_section.add_certificate_exception(self.user_name, notes)
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(expected_notes, self.certificates_section.last_certificate_exception.text)

        # Revisit Page & verify that added exceptions are also synced with backend
        self.certificates_section.refresh()

        # Wait for the certificate exception section to render
        self.certificates_section.wait_for_certificate_exceptions_section()

        # Validate certificate exception synced with server is visible in certificate exceptions list
        self.assertIn(self.user_name, self.certificates_section.last_certificate_exception.text)
        self.assertIn(expected_notes, self.certificates_section.last_certificate_exception.text)

    @attr('a11y')
    def test_certificates_a11y(self):
        """
        Certificates page accessibility tests
        """
        self.certificates_section.a11y_audit.config.set_scope([
            '.certificates-wrapper'
        ])
        self.certificates_section.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr-value',  # TODO: AC-491
                'checkboxgroup',  # TODO: AC-491
                'color-contrast',  # TODO: AC-491
                'duplicate-id',  # TODO: AC-491
                'label',  # TODO: AC-491
                'radiogroup',  # TODO: AC-491
            ]
        })
        self.certificates_section.a11y_audit.check_for_accessibility_errors()


@attr('shard_7')
class CertificateInvalidationTest(BaseInstructorDashboardTest):
    """
    Tests for Certificates functionality on instructor dashboard.
    """

    @classmethod
    def setUpClass(cls):
        super(CertificateInvalidationTest, cls).setUpClass()

        # Create course fixture once each test run
        CourseFixture(
            org='test_org',
            number='335535897951379478207964576572017930000',
            run='test_run',
            display_name='Test Course 335535897951379478207964576572017930000',
        ).install()

    def setUp(self):
        super(CertificateInvalidationTest, self).setUp()
        # set same course number as we have in fixture json
        self.course_info['number'] = "335535897951379478207964576572017930000"

        # we have created a user with this id in fixture, and created a generated certificate for it.
        self.student_id = "99"
        self.student_name = "testcert"
        self.student_email = "cert@example.com"

        # Enroll above test user in the course
        AutoAuthPage(
            self.browser,
            username=self.student_name,
            email=self.student_email,
            course_id=self.course_id,
        ).visit()

        self.test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }

        self.cert_fixture = CertificateConfigFixture(self.course_id, self.test_certificate_config)
        self.cert_fixture.install()
        self.user_name, self.user_id = self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()

        disable_animations(self.certificates_section)

    def test_instructor_can_invalidate_certificate(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can add a certificate
        invalidation to invalidation list.

            Given that I am on the Certificates tab on the Instructor Dashboard
            When I fill in student username and notes fields and click 'Add Exception' button
            Then new certificate exception should be visible in certificate exceptions list
        """
        notes = 'Test Notes'
        # Add a student to certificate invalidation list
        self.certificates_section.add_certificate_invalidation(self.student_name, notes)
        self.assertIn(self.student_name, self.certificates_section.last_certificate_invalidation.text)
        self.assertIn(notes, self.certificates_section.last_certificate_invalidation.text)

        # Validate success message
        self.assertIn(
            "Certificate has been successfully invalidated for {user}.".format(user=self.student_name),
            self.certificates_section.certificate_invalidation_message.text
        )

        # Verify that added invalidations are also synced with backend
        # Revisit Page
        self.certificates_section.refresh()

        # wait for the certificate invalidations section to render
        self.certificates_section.wait_for_certificate_invalidations_section()

        # validate certificate invalidation is visible in certificate invalidation list
        self.assertIn(self.student_name, self.certificates_section.last_certificate_invalidation.text)
        self.assertIn(notes, self.certificates_section.last_certificate_invalidation.text)

    def test_instructor_can_re_validate_certificate(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor can re-validate certificate.

            Given that I am on the certificates tab on the Instructor Dashboard
            AND there is a certificate invalidation in certificate invalidation table
            When I click "Remove from Invalidation Table" button
            Then certificate is re-validated and removed from certificate invalidation table.
        """
        notes = 'Test Notes'
        # Add a student to certificate invalidation list
        self.certificates_section.add_certificate_invalidation(self.student_name, notes)
        self.assertIn(self.student_name, self.certificates_section.last_certificate_invalidation.text)
        self.assertIn(notes, self.certificates_section.last_certificate_invalidation.text)

        # Verify that added invalidations are also synced with backend
        # Revisit Page
        self.certificates_section.refresh()

        # wait for the certificate invalidations section to render
        self.certificates_section.wait_for_certificate_invalidations_section()

        # click "Remove from Invalidation Table" button next to certificate invalidation
        self.certificates_section.remove_first_certificate_invalidation()

        # validate certificate invalidation is removed from the list
        self.assertNotIn(self.student_name, self.certificates_section.last_certificate_invalidation.text)
        self.assertNotIn(notes, self.certificates_section.last_certificate_invalidation.text)

        self.assertIn(
            "The certificate for this learner has been re-validated and the system is "
            "re-running the grade for this learner.",
            self.certificates_section.certificate_invalidation_message.text
        )

    def test_error_on_empty_user_name_or_email(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor should see error message if he clicks
            "Invalidate Certificate" button without entering student username or email.

            Given that I am on the certificates tab on the Instructor Dashboard
            When I click "Invalidate Certificate" button without entering student username/email.
            Then I see following error message
                "Student username/email field is required and can not be empty."
                "Kindly fill in username/email and then press "Invalidate Certificate" button."
        """
        # Click "Invalidate Certificate" with empty student username/email field
        self.certificates_section.fill_certificate_invalidation_user_name_field("")
        self.certificates_section.click_invalidate_certificate_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            u'Student username/email field is required and can not be empty. '
            u'Kindly fill in username/email and then press "Invalidate Certificate" button.',
            self.certificates_section.certificate_invalidation_message.text
        )

    def test_error_on_invalid_user(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor should see error message if
            the student entered for certificate invalidation does not exist.

            Given that I am on the certificates tab on the Instructor Dashboard
            When I click "Invalidate Certificate"
            AND the username entered does not exist in the system
            Then I see following error message
                "Student username/email field is required and can not be empty."
                "Kindly fill in username/email and then press "Invalidate Certificate" button."
        """
        invalid_user = "invalid_test_user"
        # Click "Invalidate Certificate" with invalid student username/email
        self.certificates_section.fill_certificate_invalidation_user_name_field(invalid_user)
        self.certificates_section.click_invalidate_certificate_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            u"{user} does not exist in the LMS. Please check your spelling and retry.".format(user=invalid_user),
            self.certificates_section.certificate_invalidation_message.text
        )

    def test_user_not_enrolled_error(self):
        """
        Scenario: On the Certificates tab of the Instructor Dashboard, Instructor should see error message if
            the student entered for certificate invalidation is not enrolled in the course.

            Given that I am on the certificates tab on the Instructor Dashboard
            When I click "Invalidate Certificate"
            AND the username entered is not enrolled in the current course
            Then I see following error message
                "{user} is not enrolled in this course. Please check your spelling and retry."
        """
        new_user = 'test_user_{uuid}'.format(uuid=self.unique_id[6:12])
        new_email = 'test_user_{uuid}@example.com'.format(uuid=self.unique_id[6:12])
        # Create a new user who is not enrolled in the course
        AutoAuthPage(self.browser, username=new_user, email=new_email).visit()
        # Login as instructor and visit Certificate Section of Instructor Dashboard
        self.user_name, self.user_id = self.log_in_as_instructor()
        self.instructor_dashboard_page.visit()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()

        # Click 'Invalidate Certificate' button with not enrolled student
        self.certificates_section.wait_for_certificate_invalidations_section()

        self.certificates_section.fill_certificate_invalidation_user_name_field(new_user)
        self.certificates_section.click_invalidate_certificate_button()
        self.certificates_section.wait_for_ajax()

        self.assertIn(
            u"{user} is not enrolled in this course. Please check your spelling and retry.".format(user=new_user),
            self.certificates_section.certificate_invalidation_message.text
        )

    @attr('a11y')
    def test_invalidate_certificates_a11y(self):
        """
        Certificate invalidation accessibility tests
        """
        self.certificates_section.a11y_audit.config.set_scope([
            '.certificates-wrapper'
        ])
        self.certificates_section.a11y_audit.config.set_rules({
            "ignore": [
                'data-table',  # TODO: AC-491
                'aria-valid-attr-value',  # TODO: AC-491
                'checkboxgroup',  # TODO: AC-491
                'color-contrast',  # TODO: AC-491
                'duplicate-id',  # TODO: AC-491
                'label',  # TODO: AC-491
                'radiogroup',  # TODO: AC-491
            ]
        })
        self.certificates_section.a11y_audit.check_for_accessibility_errors()
