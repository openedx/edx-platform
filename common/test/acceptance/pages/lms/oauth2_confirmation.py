"""Pages relevant for OAuth2 confirmation."""
from common.test.acceptance.pages.lms import BASE_URL

from bok_choy.page_object import PageObject


class OAuth2Confirmation(PageObject):
    """Page for OAuth2 confirmation view."""
    def __init__(self, browser, client_id="test-id", scopes=("email",)):
        super(OAuth2Confirmation, self).__init__(browser)
        self.client_id = client_id
        self.scopes = scopes

    @property
    def url(self):
        return "{}/oauth2/authorize?client_id={}&response_type=code&scope={}".format(
            BASE_URL, self.client_id, ' '.join(self.scopes))

    def is_browser_on_page(self):
        return self.q(css="body.oauth2").visible

    def cancel(self):
        """
        Cancel the request.

        This redirects to an invalid URI, because we don't want actual network
        connections being made.
        """
        self.q(css="input[name=cancel]").click()

    def confirm(self):
        """
        Confirm OAuth access

        This redirects to an invalid URI, because we don't want actual network
        connections being made.
        """
        self.q(css="input[name=authorize]").click()

    @property
    def has_error(self):
        """Boolean for if the page has an error or not."""
        return self.q(css=".error").present

    @property
    def error_message(self):
        """Text of the page's error message."""
        return self.q(css='.error').text[0]
