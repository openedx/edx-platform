"""
Course catalog page
"""


import re

from bok_choy.page_object import PageObject

from common.test.acceptance.pages.lms import BASE_URL


class CacheProgramsPage(PageObject):
    """
    Visit this page to call the cache_programs management command.

    This page makes a GET request to a view which is only meant to be enabled in
    testing contexts where the LMS can only be reached over HTTP. Stub the
    discovery service before visiting this page.
    """
    url = BASE_URL + '/catalog/management/cache_programs/'

    def is_browser_on_page(self):
        body = self.q(css='body').text[0]
        match = re.search(r'programs cached', body, flags=re.IGNORECASE)

        return True if match else False
