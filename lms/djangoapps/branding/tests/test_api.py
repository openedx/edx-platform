# encoding: utf-8
"""Tests of Branding API """
from __future__ import unicode_literals

from django.test import TestCase

import mock
from branding.api import get_logo_url, get_footer
from django.test.utils import override_settings


class TestHeader(TestCase):
    """Test API end-point for retrieving the header. """

    def test_cdn_urls_for_logo(self):
        # Ordinarily, we'd use `override_settings()` to override STATIC_URL,
        # which is what the staticfiles storage backend is using to construct the URL.
        # Unfortunately, other parts of the system are caching this value on module
        # load, which can cause other tests to fail.  To ensure that this change
        # doesn't affect other tests, we patch the `url()` method directly instead.
        cdn_url = "http://cdn.example.com/static/image.png"
        with mock.patch('branding.api.staticfiles_storage.url', return_value=cdn_url):
            logo_url = get_logo_url()

        self.assertEqual(logo_url, cdn_url)


class TestFooter(TestCase):
    """Test retrieving the footer. """
    @mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True})
    @mock.patch.dict('django.conf.settings.MKTG_URLS', {
        "ROOT": "https://edx.org",
        "ABOUT": "/about-us",
        "NEWS": "/news-announcements",
        "CONTACT": "/contact",
        "FAQ": "/student-faq",
        "BLOG": "/edx-blog",
        "DONATE": "/donate",
        "JOBS": "/jobs",
        "SITE_MAP": "/sitemap",
        "TOS_AND_HONOR": "/edx-terms-service",
        "PRIVACY": "/edx-privacy-policy",
        "ACCESSIBILITY": "/accessibility",
        "MEDIA_KIT": "/media-kit",
        "ENTERPRISE": "/enterprise"
    })
    @override_settings(PLATFORM_NAME='\xe9dX')
    def test_get_footer(self):
        actual_footer = get_footer(is_secure=True)
        expected_footer = {
            'copyright': '\xa9 \xe9dX.  All rights reserved except where noted.  EdX, Open edX and the edX and Open'
                         ' EdX logos are registered trademarks or trademarks of edX Inc.',
            'navigation_links': [
                {'url': 'https://edx.org/about-us', 'name': 'about', 'title': 'About'},
                {'url': 'https://edx.org/enterprise', 'name': 'enterprise', 'title': '\xe9dX for Business'},
                {'url': 'https://edx.org/edx-blog', 'name': 'blog', 'title': 'Blog'},
                {'url': 'https://edx.org/news-announcements', 'name': 'news', 'title': 'News'},
                {'url': 'https://support.example.com', 'name': 'help-center', 'title': 'Help Center'},
                {'url': 'https://edx.org/contact', 'name': 'contact', 'title': 'Contact'},
                {'url': 'https://edx.org/donate', 'name': 'donate', 'title': 'Donate'}
            ],
            'legal_links': [
                {'url': 'https://edx.org/edx-terms-service',
                 'name': 'terms_of_service_and_honor_code',
                 'title': 'Terms of Service & Honor Code'},
                {'url': 'https://edx.org/edx-privacy-policy', 'name': 'privacy_policy', 'title': 'Privacy Policy'},
                {'url': 'https://edx.org/accessibility',
                 'name': 'accessibility_policy',
                 'title': 'Accessibility Policy'},
                {'url': 'https://edx.org/sitemap', 'name': 'sitemap', 'title': 'Sitemap'},
                {'url': 'https://edx.org/media-kit', 'name': 'media_kit', 'title': 'Media Kit'}
            ],
            'social_links': [
                {'url': '#', 'action': 'Like \xe9dX on Facebook', 'name': 'facebook',
                 'icon-class': 'fa-facebook-square', 'title': 'Facebook'},
                {'url': '#', 'action': 'Follow \xe9dX on Twitter', 'name': 'twitter',
                 'icon-class': 'fa-twitter', 'title': 'Twitter'},
                {'url': '#', 'action': 'Subscribe to the \xe9dX YouTube channel',
                 'name': 'youtube', 'icon-class': 'fa-youtube', 'title': 'Youtube'},
                {'url': '#', 'action': 'Follow \xe9dX on LinkedIn', 'name': 'linkedin',
                 'icon-class': 'fa-linkedin-square', 'title': 'LinkedIn'},
                {'url': '#', 'action': 'Follow \xe9dX on Google+', 'name': 'google_plus',
                 'icon-class': 'fa-google-plus-square', 'title': 'Google+'},
                {'url': '#', 'action': 'Subscribe to the \xe9dX subreddit',
                 'name': 'reddit', 'icon-class': 'fa-reddit', 'title': 'Reddit'}
            ],
            'mobile_links': [],
            'logo_image': 'https://edx.org/static/images/logo.png',
            'openedx_link': {
                'url': 'http://open.edx.org',
                'image': 'https://files.edx.org/openedx-logos/edx-openedx-logo-tag.png',
                'title': 'Powered by Open edX'
            }
        }
        self.assertEqual(actual_footer, expected_footer)
