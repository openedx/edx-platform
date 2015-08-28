from bok_choy.page_object import PageObject
from . import BASE_URL
from signup import SignUpPage
from login import LoginPage
from studiohelp import StudioHelpPage
from termsofservice import TermsOfServicePage
from privacypolicy import PrivacyPolicyPage
from ...LMS.pages.homepage import LMSHomePage

class HomePage(PageObject):

    #pages Home Page

    url = BASE_URL

    def is_browser_on_page(self):
        return 'welcome' in self.browser.title.lower()

    def click_edx_image(self):
        # Clicks on the EDX image

        self.q(css='img[alt=\"edX pages\"]').first.click()
        HomePage(self.browser).wait_for_page()

    def click_signup_button(self):
        # Clicks on Sign up button

        self.q(css='.action-signup').first.click()
        SignUpPage(self.browser).wait_for_page()

    def click_login_button(self):
        # Clicks on Sign in button

        self.q(css='.action-signin').first.click()
        LoginPage(self.browser).wait_for_page()

    def click_studio_help_link(self):
        # Clicks on pages Help link

        self.q(css='.nav-not-signedin-help > a').first.click()
        self.browser.switch_to_window(self.browser.window_handles[-1])
        StudioHelpPage(self.browser).wait_for_page()

    def click_signup_and_start_making_button(self):
        # Clicks on Sign up & Start Making An Edx Course button

        self.q(css='.action-primary').first.click()
        SignUpPage(self.browser).wait_for_page()

    def click_already_have_studio_account_link(self):
        # Clicks on Already have a pages Account? Sign in

        self.q(css='.action-secondary').first.click()
        LoginPage(self.browser).wait_for_page()

    def verify_terms_of_service_url(self):
        # Verify terms and service url

        return self.q(css='li.nav-item.nav-peripheral-tos a').attrs('href')[0]

    def terms_of_service_page(self):
        # Terms of Service page is displaying

        TermsOfServicePage(self.browser).visit().wait_for_page()

    def verify_privacy_policy_url(self):
        # Verify privacy policy url

        return self.q(css='li.nav-item.nav-peripheral-pp a').attrs('href')[0]

    def privacy_policy_page(self):
        # Privacy Policy page is displaying

        PrivacyPolicyPage(self.browser).visit().wait_for_page()

    def verify_edx_link_url(self):
        # Verify edX link URL

        return self.q(css='.colophon>p>a').attrs('href')[0]

    def verify_lms_home_page(self):
        # Verify edX pages Home Page

        LMSHomePage(self.browser).visit().wait_for_page()
