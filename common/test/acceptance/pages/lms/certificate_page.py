# -*- coding: utf-8 -*-
"""
Module for Certificates pages.
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class CertificatePage(PageObject):
    """
    Certificate web view page.
    """

    url_path = "certificates"

    def __init__(self, browser, user_id, course_id):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            user_id: id of the user whom certificate is awarded
            course_id: course key of the course where certificate is awarded
        """
        super(CertificatePage, self).__init__(browser)
        self.user_id = user_id
        self.course_id = course_id

    def is_browser_on_page(self):
        """ Checks if certificate web view page is being viewed """
        return self.q(css='section.about-accomplishments').present

    @property
    def url(self):
        """
        Construct a URL to the page
        """
        return BASE_URL + "/" + self.url_path + "/user/" + self.user_id + "/course/" + self.course_id

    @property
    def accomplishment_banner(self):
        """
        returns accomplishment banner.
        """
        return self.q(css='section.banner-user')

    @property
    def add_to_linkedin_profile_button(self):
        """
        returns add to LinkedIn profile button
        """
        return self.q(css='button.action-linkedin-profile')

    @property
    def add_to_facebook_profile_button(self):
        """
        returns Facebook share button
        """
        return self.q(css='button.action-share-facebook')
