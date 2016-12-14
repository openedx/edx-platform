"""
Common mixin for paginated UIs.
"""


from selenium.webdriver.common.keys import Keys


class PaginatedUIMixin(object):
    """Common methods used for paginated UI."""

    PAGINATION_FOOTER_CSS = 'nav.bottom'
    PAGE_NUMBER_INPUT_CSS = 'input#page-number-input'
    NEXT_PAGE_BUTTON_CSS = 'button.next-page-link'
    PREVIOUS_PAGE_BUTTON_CSS = 'button.previous-page-link'
    PAGINATION_HEADER_TEXT_CSS = 'div.search-tools'
    CURRENT_PAGE_NUMBER_CSS = 'span.current-page'
    TOTAL_PAGES_CSS = 'span.total-pages'

    def get_pagination_header_text(self):
        """Return the text showing which items the user is currently viewing."""
        return self.q(css=self.PAGINATION_HEADER_TEXT_CSS).text[0]

    def pagination_controls_visible(self):
        """Return true if the pagination controls in the footer are visible."""
        footer_nav = self.q(css=self.PAGINATION_FOOTER_CSS).results[0]
        # The footer element itself is non-generic, so check above it
        footer_el = footer_nav.find_element_by_xpath('..')
        return 'hidden' not in footer_el.get_attribute('class').split()

    def get_current_page_number(self):
        """Return the the current page number."""
        return int(self.q(css=self.CURRENT_PAGE_NUMBER_CSS).text[0])

    @property
    def get_total_pages(self):
        """Returns the total page value"""
        return int(self.q(css=self.TOTAL_PAGES_CSS).text[0])

    def go_to_page(self, page_number):
        """Go to the given page_number in the paginated list results."""
        self.q(css=self.PAGE_NUMBER_INPUT_CSS).results[0].send_keys(unicode(page_number), Keys.ENTER)
        self.wait_for_ajax()

    def press_next_page_button(self):
        """Press the next page button in the paginated list results."""
        self.q(css=self.NEXT_PAGE_BUTTON_CSS).click()
        self.wait_for_ajax()

    def press_previous_page_button(self):
        """Press the previous page button in the paginated list results."""
        self.q(css=self.PREVIOUS_PAGE_BUTTON_CSS).click()
        self.wait_for_ajax()

    def is_next_page_button_enabled(self):
        """Return whether the 'next page' button can be clicked."""
        return self.is_enabled(self.NEXT_PAGE_BUTTON_CSS)

    def is_previous_page_button_enabled(self):
        """Return whether the 'previous page' button can be clicked."""
        return self.is_enabled(self.PREVIOUS_PAGE_BUTTON_CSS)

    def is_enabled(self, css):
        """Return whether the given element is not disabled."""
        return 'is-disabled' not in self.q(css=css).attrs('class')[0]
