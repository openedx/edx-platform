# -*- coding: utf-8 -*-
"""
LMS index (home) page.
"""
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms import BASE_URL

BANNER_SELECTOR = 'section.home header div.outer-wrapper div.title .heading-group h1'
INTRO_VIDEO_SELECTOR = 'div.play-intro'
VIDEO_MODAL_SELECTOR = 'section#video-modal.modal.home-page-video-modal.video-modal'


class IndexPage(PageObject):
    """
    LMS index (home) page, the default landing page for Open edX users when they are not logged in
    """
    def __init__(self, browser):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
        """
        super(IndexPage, self).__init__(browser)

    url = "{base}/".format(base=BASE_URL)

    def is_browser_on_page(self):
        """
        Returns a browser query object representing the video modal element
        """
        element = self.q(css=BANNER_SELECTOR)
        return element.visible and element.text[0].startswith("Welcome to the Open edX")

    @property
    def banner_element(self):
        """
        Returns a browser query object representing the video modal element
        """
        return self.q(css=BANNER_SELECTOR)

    @property
    def intro_video_element(self):
        """
        Returns a browser query object representing the video modal element
        """
        return self.q(css=INTRO_VIDEO_SELECTOR)

    @property
    def video_modal_element(self):
        """
        Returns a browser query object representing the video modal element
        """
        return self.q(css=VIDEO_MODAL_SELECTOR)

    @property
    def footer_links(self):
        """Return a list of the text of the links in the page footer."""
        return self.q(css='.nav-colophon a').attrs('text')
