from bok_choy.web_app_test import WebAppTest
from pages.signup import SignUpPage
from pages.termsofservice import TermsOfServicePage
from pages.login import LoginPage

class TestSignUpPage(WebAppTest):
    def setUp(self):
        super(TestSignUpPage, self).setUp()
        self.browser.maximize_window()
        self.signup_page = SignUpPage(self.browser)
        self.edx_terms_page = TermsOfServicePage(self.browser)

        SignUpPage(self.browser).visit()

    def test_already_have_studio_account_link(self):
        # Verify that user can click Already have a pages Account? Sign in link and is navigated to Sign Up page

        self.signup_page.click_alreay_have_studio_account_link()
        LoginPage(self.browser).wait_for_page()

    def test_terms_of_service_link(self):
        # Verify that user can click Terms of Service (near checkbox) link and is navigated to Terms of Service page
        """
        Authentication box which cannot be handled directly so adding 2 tests
        """

        self.signup_page.verify_terms_of_service_checkbox_url()
        self.assertEquals(self.signup_page.verify_terms_of_service_checkbox_url(), "https://stage.edx.org/edx-terms-service")
        self.signup_page.terms_of_service_page_checkbox()
        self.assertTrue(self.edx_terms_page.is_browser_on_page(), "Not on Correct Page or Link Broken")
