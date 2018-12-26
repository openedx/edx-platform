"""
Signup page for studio
"""
from bok_choy.page_object import PageObject

from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio import LMS_URL
from common.test.acceptance.pages.studio.utils import HelpMixin, set_input_value


class SignupPage(PageObject, HelpMixin):
    """
    Signup page for Studio.
    """

    url = LMS_URL + "/register"

    def is_browser_on_page(self):
        return (
            self.q(css="#register-anchor").is_present() and
            self.q(css=".register-button").visible
        )

    def input_password(self, password):
        """Inputs a password and then returns the password input"""
        return set_input_value(self, "#register-password", password)

    def sign_up_user(self, email, name, username, password, country="US", favorite_movie="Alf"):
        """
        Register the user.
        """
        self.q(css="#register-email").fill(email)
        self.q(css="#register-name").fill(name)
        self.q(css="#register-username").fill(username)
        self.q(css="#register-password").fill(password)
        self.q(css="#register-country").results[0].send_keys(country)
        self.q(css="#register-favorite_movie").fill(favorite_movie)

        # Submit it
        self.q(css=".register-button").click()
        self.wait_for_element_absence('.register-button', 'Register button is gone.')
