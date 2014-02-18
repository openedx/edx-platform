from bok_choy.page_object import PageObject
from . import BASE_URL


class LogoutPage(PageObject):
    """
    Logout from the LMS by directly going to the logout URL.
    """
    def is_browser_on_page(self):
        return True

    @property
    def url(self):
        return BASE_URL + "/logout"
