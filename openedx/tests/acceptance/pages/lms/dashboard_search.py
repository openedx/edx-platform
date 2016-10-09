"""
Dashboard search
"""

from bok_choy.page_object import PageObject
from openedx.tests.acceptance.pages.lms import BASE_URL


class DashboardSearchPage(PageObject):
    """
    Dashboard page featuring a search form
    """

    search_bar_selector = '#dashboard-search-bar'
    url = "{base}/dashboard".format(base=BASE_URL)

    @property
    def search_results(self):
        """ search results list showing """
        return self.q(css='#dashboard-search-results')

    def is_browser_on_page(self):
        """ did we find the search bar in the UI """
        return self.q(css=self.search_bar_selector).present

    def enter_search_term(self, text):
        """ enter the search term into the box """
        self.q(css=self.search_bar_selector + ' input[type="text"]').fill(text)

    def search(self):
        """ execute the search """
        self.q(css=self.search_bar_selector + ' [type="submit"]').click()
        self.wait_for_element_visibility('.search-info', 'Search results are shown')

    def search_for_term(self, text):
        """
        Search and return results
        """
        self.enter_search_term(text)
        self.search()
