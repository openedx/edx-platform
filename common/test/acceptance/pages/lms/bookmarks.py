"""
Courseware Boomarks
"""


from common.test.acceptance.pages.common.paging import PaginatedUIMixin
from common.test.acceptance.pages.lms.course_page import CoursePage


class BookmarksPage(CoursePage, PaginatedUIMixin):
    """
    Courseware Bookmarks Page.
    """
    url_path = "bookmarks"
    BOOKMARKS_BUTTON_SELECTOR = '.bookmarks-list-button'
    BOOKMARKS_ELEMENT_SELECTOR = '#my-bookmarks'
    BOOKMARKED_ITEMS_SELECTOR = '.bookmarks-results-list .bookmarks-results-list-item'
    BOOKMARKED_BREADCRUMBS = BOOKMARKED_ITEMS_SELECTOR + ' .list-item-breadcrumbtrail'

    def is_browser_on_page(self):
        """ Verify if we are on correct page """
        return self.q(css=self.BOOKMARKS_ELEMENT_SELECTOR).present

    def bookmarks_button_visible(self):
        """ Check if bookmarks button is visible """
        return self.q(css=self.BOOKMARKS_BUTTON_SELECTOR).visible

    def results_present(self):
        """ Check if bookmarks results are present """
        return self.q(css=self.BOOKMARKS_ELEMENT_SELECTOR).present

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
