"""
Studio Signup Page
"""

from bok_choy.page_object import PageObject

from Tests.Studio.pages.termsofservice import TermsOfServicePage
from . import BASE_URL


class SignUpPage(PageObject):

    url = BASE_URL + '/signup'

    def is_browser_on_page(self):
        return self.q(css='body.view-signup').present

    def click_alreay_have_studio_account_link(self):
        # Click on Already have a pages Account? Sign in link

        self.q(css='.content header a.action.action-signin').first.click()

    def terms_of_service_page_checkbox(self):
        # Terms of Service page is displaying

        TermsOfServicePage(self.browser).visit().wait_for_page()

    def verify_terms_of_service_checkbox_url(self):
        # Verify terms of service checkbox url

        return self.q(css='.required label a').attrs('href')[0]
