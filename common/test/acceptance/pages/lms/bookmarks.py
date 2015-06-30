"""
Courseware Boomarks
"""
from bok_choy.promise import EmptyPromise
from .course_page import CoursePage
from selenium.webdriver.common.keys import Keys


class BookmarksPage(CoursePage):
    """
    Courseware Bookmarks Page.
    """
    url = None
    url_path = "courseware/"
    BOOKMARKS_BUTTON_SELECTOR = '.bookmarks-list-button'
    BOOKMARKED_ITEMS_SELECTOR = '.bookmarks-results-list .bookmarks-results-list-item'
    BOOKMARKED_BREADCRUMBS = BOOKMARKED_ITEMS_SELECTOR + ' .list-item-breadcrumbtrail'
    FOOTER_BUTTONS = {
        'previous': '.paging-footer .previous-page-link',
        'next': '.paging-footer .next-page-link',
        'current': '.paging-footer span.current-page',
        'total': '.paging-footer span.total-pages',
        'page': '.paging-footer input#page-number-input',
    }

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

    @property
    def paging_header_text(self):
        """
        Returns paging header text.
        """
        return self.q(css='.paging-header span').text[0]

    def paging_footer_button_state(self, button):
        """
        Returns True if paging footers `button` is enabled else False

        Arguments:
            button (str): `previous` or `next`
        """
        return 'is-disabled' not in self.q(css=self.FOOTER_BUTTONS[button]).attrs('class')[0]

    def paging_footer_button_value(self, button):
        """
        Returns the value of paging footers `button`

        Arguments:
            button (str): `current` or `total`
        """
        return int(self.q(css=self.FOOTER_BUTTONS[button]).text[0])

    def click_paging_footer_button(self, button):
        """
        Click on paging footers `button`

        Arguments:
            button (str): `previous`, `next`
        """
        last_page_number = self.paging_footer_button_value('current')
        self.q(css=self.FOOTER_BUTTONS[button]).first.click()
        self._wait_for_page_change(last_page_number)

    def goto_page_number(self, page_number, wait_for_page_change=True):
        """
        Go to page number in bookmarks list results

        Arguments:
            page_number (int): page number
        """
        last_page_number = self.paging_footer_button_value('current')
        self.q(css=self.FOOTER_BUTTONS['page']).results[0].send_keys(page_number, Keys.ENTER)
        if wait_for_page_change:
            self._wait_for_page_change(last_page_number)

    def _wait_for_page_change(self, last_page_number):
        """
        Wait for page change.

        Arguments:
            last_page_number (int): page number before navigation to new page
        """
        EmptyPromise(
            lambda: self.paging_footer_button_value('current') != last_page_number,
            "Page changed"
        ).fulfill()
