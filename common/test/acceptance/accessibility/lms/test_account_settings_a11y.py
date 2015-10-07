"""
Accessibility tests for LMS account settings page.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t lms/test_account_settings_a11y.py
"""
from ...tests.lms.test_account_settings import AccountSettingsTestMixin
from bok_choy.web_app_test import WebAppTest


class AccountSettingsAxsTest(AccountSettingsTestMixin, WebAppTest):
    """
    Class to test account settings accessibility.
    """

    def test_account_settings_axs(self):
        """
        Test the accessibility of the account settings page.
        """
        self.log_in_as_unique_user()
        self.visit_account_settings_page()
        self.account_settings_page.a11y_audit.check_for_accessibility_errors()
