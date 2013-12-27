from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class AutoAuthPage(PageObject):
    """
    The automatic authorization page.
    When allowed via the django settings file, visiting
    this url will create a user and log them in.
    """

    @property
    def name(self):
        return "studio.auto_auth"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        return "{0}/auto_auth".format(
            BASE_URL
        )

    def is_browser_on_page(self):
        return True
