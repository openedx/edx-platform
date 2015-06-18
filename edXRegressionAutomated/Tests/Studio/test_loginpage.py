from bok_choy.web_app_test import WebAppTest
from pages.edgehelp import EdgeHelpPage
from pages.login import LoginPage
from pages.mycoursespage import MyCoursesPage
from ..Settings.config import GlobalVariables

class TestLoginSuccess(WebAppTest):
    def setUp(self):
        super(TestLoginSuccess, self).setUp()
        self.browser.maximize_window()
        self.login_page = LoginPage(self.browser)
        self.edge_help_page = EdgeHelpPage(self.browser)
        self.mycourses_page = MyCoursesPage(self.browser)

        LoginPage(self.browser).visit()

    def test_dont_have_studio_account_link(self):
        # Verify that user can click Don't have a pages Account? Sign up! link and is navigated to Sign Up page

        self.login_page.click_dont_have_studio_account_link()

    def test_our_support_center_link(self):
        # Verify that user can click our support center link and is navigated to Edge Help page

        self.login_page.click_our_support_center_link()

    def test_successful_login(self):
        # Verify that user can login successfully inputting correct user name and password

        self.login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.login_page.login_success_validation()

class TestLoginFailure(WebAppTest):
    def setUp(self):
        super(TestLoginFailure, self).setUp()
        self.browser.maximize_window()
        self.login_page = LoginPage(self.browser)

        LoginPage(self.browser).visit()

    def test_invalid_username(self):
        # Verify that user cannot login inputting incorrect user name and correct password

        self.login_page.login('a@a.com', GlobalVariables.password)
        self.login_page.login_error_validation()

    def test_invalid_password(self):
        # Verify that user cannot login inputting correct user name and incorrect password

        self.login_page.login(GlobalVariables.user_name, 'abc123')
        self.login_page.login_error_validation()

    def test_invalid_username_and_password(self):
        # Verify that user cannot login inputting incorrect user name and incorrect password

        self.login_page.login('a@a.com', 'abc123')
        self.login_page.login_error_validation()
