# -*- coding: utf-8 -*-
"""
End-to-end tests for the Student Account Settings.
"""
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.account_settings import AccountSettingsPage
from ...pages.lms.dashboard import DashboardPage

from bok_choy.web_app_test import WebAppTest


class AccountSettingsTest(WebAppTest):
    """
    Tests that verify Student Account Settings Page.
    """

    USERNAME = 'test_user'
    EMAIL = 'test_user@edx.org'

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(AccountSettingsTest, self).setUp()

        self.account_settings_page = AccountSettingsPage(self.browser)
        self.dashboard_page = DashboardPage(self.browser)

        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL).visit()

    def test_dashboard_account_settings_link(self):
        """
        Scenario: Verify that account settings link is present on dashboard page and we can navigate to it.

        Given that I am a registered user.
        When I go to Dashboard page.
        And I click on username dropdown.
        Then I see Account Settings link in the dropdown menu.
        When I click on Account Settings link.
        Then I will be navigated to Account Settings page.
        """
        self.dashboard_page.visit()
        self.dashboard_page.click_username_dropdown()
        self.assertTrue('Account Settings' in self.dashboard_page.username_dropdown_links)
        self.dashboard_page.click_account_settings_link()

    def test_dashboard_account_settings(self):
        """
        Scenario: Verify that account settings works as expected.

        Given that I am a registered user.
        When I go to Account Settings page.
        Then I see correct Account Settings Sections.
        And I see correct user information.
        """
        self.account_settings_page.visit()

        sections = ['Basic Account Information', 'Demographics and Additional Details', 'Connected Accounts']
        self.assertEqual(sections, self.account_settings_page.sections)

        expected_user_info = {
            'username': self.USERNAME,
            'fullname': self.USERNAME,
            'email': self.EMAIL,
            'language': 'English',
        }
        displayed_user_info = {
            'username': self.account_settings_page.get_field_value('username'),
            'fullname': self.account_settings_page.get_field_value('name'),
            'email': self.account_settings_page.get_field_value('email'),
            'language': self.account_settings_page.get_field_value('language'),
        }
        self.assertEqual(expected_user_info, displayed_user_info)
