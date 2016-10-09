"""
Courseware search
"""

from openedx.tests.acceptance.pages.lms.course_page import CoursePage


class CoursewareSearchPage(CoursePage):
    """
    Coursware page featuring a search form
    """

    url_path = "courseware/"
    search_bar_selector = '#courseware-search-bar'
    search_results_selector = '.courseware-results'

    @property
    def search_results(self):
        """ search results list showing """
        return self.q(css=self.search_results_selector)

    def is_browser_on_page(self):
        """ did we find the search bar in the UI """
        return self.q(css=self.search_bar_selector).present

    def enter_search_term(self, text):
        """ enter the search term into the box """
        self.q(css=self.search_bar_selector + ' input[type="text"]').fill(text)

    def search(self):
        """ execute the search """
        self.q(css=self.search_bar_selector + ' [type="submit"]').click()
        self.wait_for_ajax()
        self.wait_for_element_visibility(self.search_results_selector, 'Search results are visible')

    def search_for_term(self, text):
        """
        Fill input and do search
        """
        self.enter_search_term(text)
        self.search()

    def clear_search(self):
        """
        Clear search bar after search.
        """
        self.q(css=self.search_bar_selector + ' .cancel-button').click()
        self.wait_for_element_visibility('#course-content', 'Search bar is cleared')
