# -*- coding: utf-8 -*-
"""
Teams page.
"""

from selenium.webdriver.common.keys import Keys
from .course_page import CoursePage


BROWSE_BUTTON_CSS = 'a.nav-item[data-index="1"]'
TOPIC_CARD_CSS = 'div.card-core-wrapper'
PAGE_NUMBER_INPUT_CSS = 'input#page-number-input'
NEXT_PAGE_BUTTON_CSS = 'a.next-page-link'
PAGINATION_TEXT_CSS = 'div.search-tools'
CURRENT_PAGE_TEXT_CSS = 'span.current-page'


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

    def get_topic_cards(self):
        """Return a list of the topic cards present on the page."""
        return self.q(css=TOPIC_CARD_CSS).results

    def get_pagination_text(self):
        """Return the text showing which topics the user is currently viewing."""
        return self.q(css=PAGINATION_TEXT_CSS).text[0]

    def get_current_page_text(self):
        """Return the text showing the current page."""
        return self.q(css=CURRENT_PAGE_TEXT_CSS).text[0]

    def go_to_topics_list_page(self, page_number):
        """Go to the given page_number in the topics list results."""
        self.q(css=PAGE_NUMBER_INPUT_CSS).results[0].send_keys(unicode(page_number), Keys.ENTER)

    def press_next_page_button(self):
        """Press the next page button in the topics list results."""
        self.q(css=NEXT_PAGE_BUTTON_CSS).click()
