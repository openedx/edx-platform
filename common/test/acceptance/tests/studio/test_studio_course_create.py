"""
Acceptance tests for course creation.
"""
import uuid
import random
import string

from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.index import DashboardPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.tests.helpers import AcceptanceTest


class CreateCourseTest(AcceptanceTest):
    """
    Test that we can create a new course the studio home page.
    """
    shard = 19

    def setUp(self):
        """
        Load the helper for the home page (dashboard page)
        """
        super(CreateCourseTest, self).setUp()

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.course_name = "New Course Name"
        self.course_org = "orgX"
        self.course_number = str(uuid.uuid4().get_hex().upper()[0:6])
        self.course_run = "2015_T2"

    def test_create_course_with_non_existing_org(self):
        """
        Scenario: Ensure that the course creation with non existing org display proper error message.
        Given I have filled course creation form with a non existing and all required fields
        When I click 'Create' button
        Form validation should pass
        Then I see the error message explaining reason for failure to create course
        """

        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.has_course(
            org='testOrg', number=self.course_number, run=self.course_run
        ))
        self.assertTrue(self.dashboard_page.new_course_button.present)

        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            self.course_name, 'testOrg', self.course_number, self.course_run
        )
        self.assertTrue(self.dashboard_page.is_new_course_form_valid())
        self.dashboard_page.submit_new_course_form()
        self.assertTrue(self.dashboard_page.error_notification.present)
        self.assertIn(
            u'Organization you selected does not exist in the system', self.dashboard_page.error_notification_message
        )

    def test_create_course_with_existing_org(self):
        """
        Scenario: Ensure that the course creation with an existing org should be successful.
        Given I have filled course creation form with an existing org and all required fields
        When I click 'Create' button
        Form validation should pass
        Then I see the course listing page with newly created course
        """

        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.has_course(
            org=self.course_org, number=self.course_number, run=self.course_run
        ))
        self.assertTrue(self.dashboard_page.new_course_button.present)

        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            self.course_name, self.course_org, self.course_number, self.course_run
        )
        self.assertTrue(self.dashboard_page.is_new_course_form_valid())
        self.dashboard_page.submit_new_course_form()

        # Successful creation of course takes user to course outline page
        course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_org,
            self.course_number,
            self.course_run
        )
        course_outline_page.visit()
        course_outline_page.wait_for_page()

        # Go back to dashboard and verify newly created course exists there
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.has_course(
            org=self.course_org, number=self.course_number, run=self.course_run
        ))
        # Click on the course listing and verify that the Studio course outline page opens.
        self.dashboard_page.click_course_run(self.course_run)
        course_outline_page.wait_for_page()

    def test_create_course_with_existing_org_via_autocomplete(self):
        """
        Scenario: Ensure that the course creation with an existing org should be successful.
        Given I have filled course creation form with an existing org and all required fields
        And I selected `Course Organization` input via autocomplete
        When I click 'Create' button
        Form validation should pass
        Then I see the course listing page with newly created course
        """

        self.auth_page.visit()
        self.dashboard_page.visit()
        new_org = 'orgX2'
        self.assertFalse(self.dashboard_page.has_course(
            org=new_org, number=self.course_number, run=self.course_run
        ))
        self.assertTrue(self.dashboard_page.new_course_button.present)

        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            self.course_name, '', self.course_number, self.course_run
        )
        self.dashboard_page.course_org_field.fill('org')
        self.dashboard_page.select_item_in_autocomplete_widget(new_org)
        self.assertTrue(self.dashboard_page.is_new_course_form_valid())
        self.dashboard_page.submit_new_course_form()

        # Successful creation of course takes user to course outline page
        course_outline_page = CourseOutlinePage(
            self.browser,
            new_org,
            self.course_number,
            self.course_run
        )
        course_outline_page.visit()
        course_outline_page.wait_for_page()

        # Go back to dashboard and verify newly created course exists there
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.has_course(
            org=new_org, number=self.course_number, run=self.course_run
        ))

    def test_error_appears_with_long_tuple(self):
        """
        Scenario: Ensure that the course creation is not successful with 66 characters long tuple.
        Given I have filled course creation from with combined length of 66 characters for Organization, course Number
        and course Run.
        And I have a valid course name
        Then form validation should not pass
        And I see error for combined length longer than 65
        """
        course_org = "012345678901234567890123456789"
        course_number = ''.join(random.choice(string.digits) for _ in range(30))
        course_run = "0123456"
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.new_course_button.present)
        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            self.course_name, course_org, course_number, course_run
        )
        self.assertEqual(
            self.dashboard_page.course_creation_error_message,
            'The combined length of the organization, course number, and course run fields cannot be more than 65 '
            'characters.'
        )
        self.assertTrue(self.dashboard_page.is_create_button_disabled())

    def test_no_error_appears_for_long_course_name(self):
        """
        Scenario: Ensure that the course creation with 66 characters long course name is successful.
        Given I have filled course creation form with 66 characters long course name.
        And I have filled remaining form within the allowed characters length.
        When I click 'Create' button
        Form validation should pass
        Then I see the course listing page with newly created course
        """
        course_name = ''.join(random.choice(string.ascii_uppercase) for _ in range(66))
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.has_course(
            org=self.course_org, number=self.course_number, run=self.course_run
        ))
        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            course_name, self.course_org, self.course_number, self.course_run
        )
        self.dashboard_page.submit_new_course_form()
        # Successful creation of course takes user to course outline page
        course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_org,
            self.course_number,
            self.course_run
        )
        course_outline_page.visit()
        course_outline_page.wait_for_page()
        self.dashboard_page.visit()
        # Assert that course is present on dashboard
        self.assertTrue(self.dashboard_page.has_course(
            org=self.course_org, number=self.course_number, run=self.course_run
        ))
