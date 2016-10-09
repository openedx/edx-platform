"""
Signup page for studio
"""
from bok_choy.page_object import PageObject

from openedx.tests.acceptance.pages.studio import BASE_URL
from openedx.tests.acceptance.pages.studio.utils import set_input_value, HelpMixin
from openedx.tests.acceptance.pages.common.utils import click_css


class SignupPage(PageObject, HelpMixin):
    """
    Signup page for Studio.
    """

    url = BASE_URL + "/signup"

    def is_browser_on_page(self):
        return self.q(css='body.view-signup').visible

    def sign_up_user(self, registration_dictionary):
        """
        Register the user.
        """
        for css, value in registration_dictionary.iteritems():
            set_input_value(self, css, value)

        click_css(page=self, css='#tos', require_notification=False)
        click_css(page=self, css='#submit', require_notification=False)
        self.wait_for_element_absence('#submit', 'Submit button is gone.')
