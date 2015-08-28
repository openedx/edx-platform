from bok_choy.web_app_test import WebAppTest
from pages.homepage import HomePage
from pages.signup import SignUpPage
from pages.howstudioworks import HowStudioWorksPage
from pages.studiohelp import StudioHelpPage
from pages.termsofservice import TermsOfServicePage
from pages.privacypolicy import PrivacyPolicyPage
from pages.login import LoginPage
from ..LMS.pages.homepage import LMSHomePage

class TestHomePage(WebAppTest):
    def setUp(self):
        super(TestHomePage, self).setUp()
        self.browser.maximize_window()
        self.home_page = HomePage(self.browser)
        self.signup_page = SignUpPage(self.browser)
        self.how_studio_works_page = HowStudioWorksPage(self.browser)
        self.studio_help_page = StudioHelpPage(self.browser)
        self.lms_home_page = LMSHomePage(self.browser)
        self.edx_terms_page = TermsOfServicePage(self.browser)
        self.edx_privacy_policy_page = PrivacyPolicyPage(self.browser)
        self.login_page = LoginPage(self.browser)
        HomePage(self.browser).visit()

    def test_click_edx_image(self):
        # Verify that user can click edX pages Image and is navigated to Home Page again

        self.home_page.click_edx_image()

    def test_signup_button(self):
        # Verify that user can click Sign Up button and is navigated to the Sign up page

        self.home_page.click_signup_button()

    def test_login_button(self):
        # Verify that user can click Login button and is navigated to the Login page

        self.home_page.click_login_button()

    def test_studio_help_link(self):
        # Verify that user can click pages Help link and is navigated to Help page

        self.home_page.click_studio_help_link()

    def test_signup_start_making_edx_course_button(self):
        # Verify that user can click Sign up & Start Making An Edx Course button and is navigated to the Sign up page

        self.home_page.click_signup_and_start_making_button()

    def test_already_have_studio_account_link(self):
        # Verify that user can click Already have a pages Account? Sign in link and is navigated to the Log in page

        self.home_page.click_already_have_studio_account_link()

    def test_edx_live_link(self):
        # Verify that user can click edx link and is navigated to edx live website
        """
        Authentication box which cannot be handled directly so adding 2 tests
        """

        self.home_page.verify_edx_link_url()
        self.assertEquals(self.home_page.verify_edx_link_url(), "https://stage.edx.org/")
        #self.home_page.verify_lms_home_page()
        #self.assertTrue(self.lms_home_page.is_browser_on_page(), "Not on the correct page or link broken")

    def test_terms_of_service_link(self):
        # Verify that user can click Terms of Service link and is navigated to Terms of Service page
        """
        Authentication box which cannot be handled directly so adding 2 tests
        """

        self.home_page.verify_terms_of_service_url()
        self.assertEquals(self.home_page.verify_terms_of_service_url(), "https://stage.edx.org/edx-terms-service")
        self.home_page.terms_of_service_page()
        self.assertTrue(self.edx_terms_page.is_browser_on_page(), "Not on Correct Page or Link Broken")

    def test_privacy_policy_link(self):
        # Verify that user can click Privacy Policy link and is navigated to Privacy Policy page
        """
        Authentication box which cannot be handled directly so adding 2 tests
        """

        self.home_page.verify_privacy_policy_url()
        self.assertEquals(self.home_page.verify_privacy_policy_url(), "https://stage.edx.org/edx-privacy-policy")
        self.home_page.privacy_policy_page()
        self.assertTrue(self.edx_privacy_policy_page.is_browser_on_page(), "Not on Correct Page or Link Broken")
