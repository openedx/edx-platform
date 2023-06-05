"""
Library edit page in Studio
"""


import six

from bok_choy.page_object import PageObject

from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.pagination import PaginatedMixin
from common.test.acceptance.pages.studio.users import UsersPageMixin
from common.test.acceptance.pages.studio.utils import HelpMixin


class LibraryPage(PageObject, HelpMixin):
    """
    Base page for Library pages. Defaults URL to the edit page.
    """
    def __init__(self, browser, locator):
        super(LibraryPage, self).__init__(browser)
        self.locator = locator

    @property
    def url(self):
        """
        URL to the library edit page for the given library.
        """
        return "{}/library/{}".format(BASE_URL, six.text_type(self.locator))

    def is_browser_on_page(self):
        """
        Returns True iff the browser has loaded the library edit page.
        """
        return self.q(css='body.view-library').present


class LibraryEditPage(LibraryPage, PaginatedMixin, UsersPageMixin):
    """
    Library edit page in Studio
    """

    def wait_until_ready(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to
        finish.

        Always call this before using the page. It also disables animations
        for improved test reliability.
        """
        self.wait_for_ajax()
        super(LibraryEditPage, self).wait_until_ready()
