# -*- coding: utf-8 -*-
"""
End-to-end tests for the Account Settings page.
"""


from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.tests.helpers import AcceptanceTest, EventsTestMixin


class AccountSettingsTestMixin(EventsTestMixin, AcceptanceTest):
    """
    Mixin with helper methods to test the account settings page.
    """

    CHANGE_INITIATED_EVENT_NAME = u"edx.user.settings.change_initiated"
    USER_SETTINGS_CHANGED_EVENT_NAME = 'edx.user.settings.changed'
    ACCOUNT_SETTINGS_REFERER = u"/account/settings"

    shard = 23

    def visit_account_settings_page(self, gdpr=False):
        """
        Visit the account settings page for the current user, and store the page instance
        as self.account_settings_page.
        """
        self.account_settings_page = AccountSettingsPage(self.browser)
        self.account_settings_page.visit()
        self.account_settings_page.wait_for_ajax()
        # TODO: LEARNER-4422 - delete when we clean up flags
        if gdpr:
            self.account_settings_page.browser.get(self.browser.current_url + "?course_experience.gdpr=1")
            self.account_settings_page.wait_for_page()

    def log_in_as_unique_user(self, email=None, full_name=None, password=None):
        """
        Create a unique user and return the account's username and id.
        """
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        auto_auth_page = AutoAuthPage(
            self.browser,
            username=username,
            email=email,
            full_name=full_name,
            password=password
        ).visit()
        user_id = auto_auth_page.get_user_id()
        return username, user_id


class AccountSettingsA11yTest(AccountSettingsTestMixin, AcceptanceTest):
    """
    Class to test account settings accessibility.
    """
    a11y = True

    def test_account_settings_a11y(self):
        """
        Test the accessibility of the account settings page.
        """
        self.log_in_as_unique_user()
        self.visit_account_settings_page()
        self.account_settings_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.account_settings_page.a11y_audit.check_for_accessibility_errors()
