"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""


import unittest

import six
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme


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

    @with_comprehensive_theme("edx.org")
    def test_edx_footer(self):
        """
        Verify that the homepage, when accessed at edx.org, has the edX footer
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'footer-edx-v3')

    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'footer-openedx')

    @with_comprehensive_theme("edx.org")
    @override_settings(
        SOCIAL_MEDIA_FOOTER_NAMES=SOCIAL_MEDIA_NAMES,
        SOCIAL_MEDIA_FOOTER_URLS=SOCIAL_MEDIA_URLS
    )
    def test_edx_footer_social_links(self):
        resp = self.client.get('/')
        for name, url in six.iteritems(self.SOCIAL_MEDIA_URLS):
            self.assertContains(resp, url)
            self.assertContains(resp, settings.SOCIAL_MEDIA_FOOTER_DISPLAY[name]['title'])
            self.assertContains(resp, settings.SOCIAL_MEDIA_FOOTER_DISPLAY[name]['icon'])
