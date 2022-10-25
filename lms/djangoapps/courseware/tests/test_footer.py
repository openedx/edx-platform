"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""


import unittest

from django.conf import settings
from django.test import TestCase


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestFooter(TestCase):
    """
    Tests for edx and OpenEdX footer
    """

    SOCIAL_MEDIA_NAMES = [
        "facebook",
        "instagram",
        "twitter",
        "linkedin",
        "tumblr",
        "meetup",
        "reddit",
        "youtube",
    ]

    SOCIAL_MEDIA_URLS = {
        "facebook": "http://www.facebook.com/",
        "instagram": "https://instagram.com/",
        "twitter": "https://twitter.com/",
        "linkedin": "http://www.linkedin.com/",
        "tumblr": "http://www.tumblr.com/",
        "meetup": "http://www.meetup.com/",
        "reddit": "http://www.reddit.com/",
        "youtube": "https://www.youtube.com/"
    }

    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """
        resp = self.client.get('/')
        assert resp.status_code == 200
        self.assertContains(resp, 'footer-openedx')
