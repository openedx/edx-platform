"""
Acceptance tests for course creation.
"""
import uuid
from bok_choy.web_app_test import WebAppTest
from nose.plugins.attrib import attr

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.index import DashboardPage
from ...pages.studio.overview import CourseOutlinePage


@attr('shard_8')
class CreateCourseTest(WebAppTest):
    """
    Test that we can create a new course the studio home page.
    """

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
