# -*- coding: utf-8 -*-
"""
Teams page.
"""

from .course_page import CoursePage
from ..common.paging import PaginatedUIMixin


TOPIC_CARD_CSS = 'div.wrapper-card-core'
BROWSE_BUTTON_CSS = 'a.nav-item[data-index="1"]'


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


class BrowseTopicsPage(CoursePage, PaginatedUIMixin):
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

    @property
    def topic_cards(self):
        """Return a list of the topic cards present on the page."""
        return self.q(css=TOPIC_CARD_CSS).results
