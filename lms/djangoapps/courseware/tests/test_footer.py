"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""

from mock import patch
from nose.plugins.attrib import attr

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings


@attr('shard_1')
class TestFooter(TestCase):

    SOCIAL_MEDIA_NAMES = [
        "facebook",
        "google_plus",
        "twitter",
        "linkedin",
        "tumblr",
        "meetup",
        "reddit",
        "youtube",
    ]

    SOCIAL_MEDIA_URLS = {
        "facebook": "http://www.facebook.com/",
        "google_plus": "https://plus.google.com/",
        "twitter": "https://twitter.com/",
        "linkedin": "http://www.linkedin.com/",
        "tumblr": "http://www.tumblr.com/",
        "meetup": "http://www.meetup.com/",
        "reddit": "http://www.reddit.com/",
        "youtube": "https://www.youtube.com/"
    }

    def test_edx_footer(self):
        """
        Verify that the homepage, when accessed at edx.org, has the edX footer
        """
        with patch.dict('django.conf.settings.FEATURES', {"IS_EDX_DOMAIN": True}):
            resp = self.client.get('/')
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, 'footer-edx-v3')

    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """
        with patch.dict('django.conf.settings.FEATURES', {"IS_EDX_DOMAIN": False}):
            resp = self.client.get('/')
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, 'footer-openedx')

    @patch.dict(settings.FEATURES, {'IS_EDX_DOMAIN': True})
    @override_settings(
        SOCIAL_MEDIA_FOOTER_NAMES=SOCIAL_MEDIA_NAMES,
        SOCIAL_MEDIA_FOOTER_URLS=SOCIAL_MEDIA_URLS
    )
    def test_edx_footer_social_links(self):
        resp = self.client.get('/')
        for name, url in self.SOCIAL_MEDIA_URLS.iteritems():
            self.assertContains(resp, url)
            self.assertContains(resp, settings.SOCIAL_MEDIA_FOOTER_DISPLAY[name]['title'])
            self.assertContains(resp, settings.SOCIAL_MEDIA_FOOTER_DISPLAY[name]['icon'])
