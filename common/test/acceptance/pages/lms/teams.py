# -*- coding: utf-8 -*-
"""
Teams page.
"""

from .course_page import CoursePage


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
        return self.q(css='.teams-text').text[0]
