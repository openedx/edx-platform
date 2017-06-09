"""
Courseware Boomarks
"""
from bok_choy.promise import EmptyPromise
from common.test.acceptance.pages.lms.course_page import CoursePage
from common.test.acceptance.pages.common.paging import PaginatedUIMixin


class BookmarksPage(CoursePage, PaginatedUIMixin):
    """
    Courseware Bookmarks Page.
    """
    url = None
    url_path = "courseware/"
    BOOKMARKS_BUTTON_SELECTOR = '.bookmarks-list-button'
    BOOKMARKED_ITEMS_SELECTOR = '.bookmarks-results-list .bookmarks-results-list-item'
    BOOKMARKED_BREADCRUMBS = BOOKMARKED_ITEMS_SELECTOR + ' .list-item-breadcrumbtrail'

    def is_browser_on_page(self):
        """ Verify if we are on correct page """
        return self.q(css=self.BOOKMARKS_BUTTON_SELECTOR).visible

    def bookmarks_button_visible(self):
        """ Check if bookmarks button is visible """
        return self.q(css=self.BOOKMARKS_BUTTON_SELECTOR).visible

    def click_bookmarks_button(self, wait_for_results=True):
        """ Click on Bookmarks button """
        self.q(css=self.BOOKMARKS_BUTTON_SELECTOR).first.click()
        if wait_for_results:
            EmptyPromise(self.results_present, "Bookmarks results present").fulfill()

    def results_present(self):
        """ Check if bookmarks results are present """
        return self.q(css='#my-bookmarks').present

    def results_header_text(self):
        """ Returns the bookmarks results header text """
        return self.q(css='.bookmarks-results-header').text[0]

    def empty_header_text(self):
        """ Returns the bookmarks empty header text """
        return self.q(css='.bookmarks-empty-header').text[0]

    def empty_list_text(self):
        """ Returns the bookmarks empty list text """
        return self.q(css='.bookmarks-empty-detail-title').text[0]

    def count(self):
        """ Returns the total number of bookmarks in the list """
        return len(self.q(css=self.BOOKMARKED_ITEMS_SELECTOR).results)

    def breadcrumbs(self):
        """ Return list of breadcrumbs for all bookmarks """
        breadcrumbs = self.q(css=self.BOOKMARKED_BREADCRUMBS).text
        return [breadcrumb.replace('\n', '').split('-') for breadcrumb in breadcrumbs]

    def click_bookmarked_block(self, index):
        """
        Click on bookmarked block at index `index`

        Arguments:
            index (int): bookmark index in the list
        """
        self.q(css=self.BOOKMARKED_ITEMS_SELECTOR).nth(index).click()
