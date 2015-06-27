# -*- coding: utf-8 -*-
"""
Teams page.
"""

from selenium.webdriver.common.keys import Keys
from .course_page import CoursePage


BROWSE_BUTTON_CSS = 'a.nav-item[data-index="1"]'
TOPIC_CARD_CSS = 'div.card-core-wrapper'
PAGINATION_FOOTER_CSS = '.topics-paging-footer'
PAGE_NUMBER_INPUT_CSS = 'input#page-number-input'
NEXT_PAGE_BUTTON_CSS = 'button.next-page-link'
PREVIOUS_PAGE_BUTTON_CSS = 'button.previous-page-link'
PAGINATION_HEADER_TEXT_CSS = 'div.search-tools'
CURRENT_PAGE_NUMBER_CSS = 'span.current-page'


class TeamsPage(CoursePage):
    """
    Teams page/tab.
    """
    url_path = "teams"

    def is_browser_on_page(self):
        """ Checks if teams page is being viewed """
        return self.q(css='body.view-teams').present

    def get_body_text(self):
        """ Returns the current dummy text. This will be changed once there is more content on the page. """
        main_page_content_css = '.page-content-main'
        self.wait_for(
            lambda: len(self.q(css=main_page_content_css).text) == 1,
            description="Body text is present"
        )
        return self.q(css=main_page_content_css).text[0]

    def browse_topics(self):
        """ View the Browse tab of the Teams page. """
        self.q(css=BROWSE_BUTTON_CSS).click()


class BrowseTopicsPage(CoursePage):
    """
    The 'Browse' tab of the Teams page.
    """

    url_path = "teams/#browse"

    def is_browser_on_page(self):
        """Check if the Browse tab is being viewed."""
        button_classes = self.q(css=BROWSE_BUTTON_CSS).attrs('class')
        if len(button_classes) == 0:
            return False
        return 'is-active' in button_classes[0]

    def get_topic_cards(self):
        """Return a list of the topic cards present on the page."""
        return self.q(css=TOPIC_CARD_CSS).results

    def get_pagination_header_text(self):
        """Return the text showing which topics the user is currently viewing."""
        return self.q(css=PAGINATION_HEADER_TEXT_CSS).text[0]

    def pagination_controls_visible(self):
        """Return true if the pagination controls in the footer are visible"""
        return 'hidden' not in self.q(css=PAGINATION_FOOTER_CSS).attrs('class')[0].split()

    def get_current_page_number(self):
        """Return the the current page number."""
        return int(self.q(css=CURRENT_PAGE_NUMBER_CSS).text[0])

    def go_to_page(self, page_number):
        """Go to the given page_number in the topics list results."""
        self.q(css=PAGE_NUMBER_INPUT_CSS).results[0].send_keys(unicode(page_number), Keys.ENTER)
        self.wait_for_ajax()

    def press_next_page_button(self):
        """Press the next page button in the topics list results."""
        self.q(css=NEXT_PAGE_BUTTON_CSS).click()
        self.wait_for_ajax()

    def press_previous_page_button(self):
        """Press the previous page button in the topics list results."""
        self.q(css=PREVIOUS_PAGE_BUTTON_CSS).click()
        self.wait_for_ajax()

    def is_next_page_button_enabled(self):
        """Return whether the 'next page' button can be click"""
        return self.is_enabled(NEXT_PAGE_BUTTON_CSS)

    def is_previous_page_button_enabled(self):
        """Return whether the 'previous page' button can be click"""
        return self.is_enabled(PREVIOUS_PAGE_BUTTON_CSS)

    def is_enabled(self, css):
        """Return whether the given element is not disabled."""
        return 'is-disabled' not in self.q(css=css).attrs('class')[0]
