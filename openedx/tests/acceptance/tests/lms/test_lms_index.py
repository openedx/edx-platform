# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS Index page (aka, Home page).  Note that this is different than
what students see @ edx.org because we redirect requests to a separate web application.
"""
import datetime

from bok_choy.web_app_test import WebAppTest
from openedx.tests.acceptance.pages.lms.index import IndexPage


class BaseLmsIndexTest(WebAppTest):
    """ Base test suite for the LMS Index (Home) page """

    def setUp(self):
        """
        Initializes the components (page objects, courses, users) for this test suite
        """
        # Some state is constructed by the parent setUp() routine
        super(BaseLmsIndexTest, self).setUp()

        # Load page objects for use by the tests
        self.page = IndexPage(self.browser)

        # Navigate to the index page and get testing!
        self.page.visit()


class LmsIndexPageTest(BaseLmsIndexTest):
    """ Test suite for the LMS Index (Home) page """

    def setUp(self):
        super(LmsIndexPageTest, self).setUp()

        # Useful to capture the current datetime for our tests
        self.now = datetime.datetime.now()

    def test_index_basic_request(self):
        """
        Perform a general validation of the index page, renders normally, no exceptions raised, etc.
        """
        self.assertTrue(self.page.banner_element.visible)
        expected_links = [u'About', u'Blog', u'News', u'Help Center', u'Contact', u'Careers', u'Donate']
        self.assertEqual(self.page.footer_links, expected_links)

    def test_intro_video_hidden_by_default(self):
        """
        Confirm that the intro video is not displayed when using the default configuration
        """
        # Ensure the introduction video element is not shown
        self.assertFalse(self.page.intro_video_element.visible)

        # Still need to figure out how to swap platform settings in the context of a bok choy test
        # but we can at least prevent accidental exposure with these validations going forward
        # Note: 'present' is a DOM check, whereas 'visible' is an actual browser/screen check
        self.assertFalse(self.page.video_modal_element.present)
        self.assertFalse(self.page.video_modal_element.visible)
