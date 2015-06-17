from bok_choy.web_app_test import WebAppTest

from Tests.LMS.pages.lms_login import LMSLoginPage
from Tests.LMS.pages.dashboard import Dashboard
from Tests.Settings.config import GlobalVariables


class TestLMSLoginSuccess(WebAppTest):
    def setUp(self):
        super(TestLMSLoginSuccess, self).setUp()
        self.browser.maximize_window()
        self.lms_login_page = LMSLoginPage(self.browser)
        self.lms_dashboard = Dashboard(self.browser)

        LMSLoginPage(self.browser).visit()

    def test_successful_LMS_login(self):
        # Verify that user can log in to pages and is navigated to Dashboard Page

        self.lms_login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.lms_login_page.login_success_validation()
        self.assertTrue(self.lms_dashboard.is_browser_on_page(), "Successful pages login failed")

