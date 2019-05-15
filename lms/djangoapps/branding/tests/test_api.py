# encoding: utf-8
"""Tests of Branding API """
from __future__ import unicode_literals

import mock
from django.conf import settings
from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings

from branding.api import get_footer, get_home_url, get_logo_url
from edxmako.shortcuts import marketing_link


class TestHeader(TestCase):
    """Test API end-point for retrieving the header. """
    shard = 4

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

    def test_home_url_with_mktg_disabled(self):
        expected_url = get_home_url()
        self.assertEqual(reverse('dashboard'), expected_url)

    @mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True})
    @mock.patch.dict('django.conf.settings.MKTG_URLS', {
        "ROOT": "https://edx.org",
    })
    def test_home_url_with_mktg_enabled(self):
        expected_url = get_home_url()
        self.assertEqual(marketing_link('ROOT'), expected_url)


class TestFooter(TestCase):
    shard = 4
    maxDiff = None
    """Test retrieving the footer. """
    @mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True})
    @mock.patch.dict('django.conf.settings.MKTG_URLS', {
        "ROOT": "https://edx.org",
        "ABOUT": "/about-us",
        "NEWS": "/news-announcements",
        "CONTACT": "/contact",
        "CAREERS": '/careers',
        "FAQ": "/student-faq",
        "BLOG": "/edx-blog",
        "DONATE": "/donate",
        "JOBS": "/jobs",
        "SITE_MAP": "/sitemap",
        "TRADEMARKS": "/trademarks",
        "TOS_AND_HONOR": "/edx-terms-service",
        "PRIVACY": "/edx-privacy-policy",
        "ACCESSIBILITY": "/accessibility",
        "AFFILIATES": '/affiliate-program',
        "MEDIA_KIT": "/media-kit",
        "ENTERPRISE": "/enterprise"
    })
    @override_settings(PLATFORM_NAME='\xe9dX')
    def test_get_footer(self):
        actual_footer = get_footer(is_secure=True)
        expected_footer = {
            'copyright': '\xa9 \xe9dX.  All rights reserved except where noted. '
                         ' edX, Open edX and their respective logos are '
                         'registered trademarks of edX Inc.',
            'navigation_links': [
                {'url': 'https://edx.org/about-us', 'name': 'about', 'title': 'About'},
                {'url': 'https://edx.org/enterprise', 'name': 'enterprise', 'title': '\xe9dX for Business'},
                {'url': 'https://edx.org/edx-blog', 'name': 'blog', 'title': 'Blog'},
                {'url': 'https://edx.org/news-announcements', 'name': 'news', 'title': 'News'},
                {'url': 'https://support.example.com', 'name': 'help-center', 'title': 'Help Center'},
                {'url': '/support/contact_us', 'name': 'contact', 'title': 'Contact'},
                {'url': 'https://edx.org/careers', 'name': 'careers', 'title': 'Careers'},
                {'url': 'https://edx.org/donate', 'name': 'donate', 'title': 'Donate'}
            ],
            'business_links': [
                {'url': 'https://edx.org/about-us', 'name': 'about', 'title': 'About'},
                {'url': 'https://edx.org/enterprise', 'name': 'enterprise', 'title': '\xe9dX for Business'},
                {'url': 'https://edx.org/affiliate-program', 'name': 'affiliates', 'title': 'Affiliates'},
                {'url': 'http://open.edx.org', 'name': 'openedx', 'title': 'Open edX'},
                {'url': 'https://edx.org/careers', 'name': 'careers', 'title': 'Careers'},
                {'url': 'https://edx.org/news-announcements', 'name': 'news', 'title': 'News'},

            ],
            'more_info_links': [
                {'url': 'https://edx.org/edx-terms-service',
                 'name': 'terms_of_service_and_honor_code',
                 'title': 'Terms of Service & Honor Code'},
                {'url': 'https://edx.org/edx-privacy-policy', 'name': 'privacy_policy', 'title': 'Privacy Policy'},
                {'url': 'https://edx.org/accessibility',
                 'name': 'accessibility_policy',
                 'title': 'Accessibility Policy'},
                {'url': 'https://edx.org/trademarks', 'name': 'trademarks', 'title': 'Trademark Policy'},
                {'url': 'https://edx.org/sitemap', 'name': 'sitemap', 'title': 'Sitemap'},

            ],
            'connect_links': [
                {'url': 'https://edx.org/edx-blog', 'name': 'blog', 'title': 'Blog'},
                # pylint: disable=line-too-long
                {'url': '{base_url}/support/contact_us'.format(base_url=settings.LMS_ROOT_URL), 'name': 'contact', 'title': 'Contact Us'},
                {'url': 'https://support.example.com', 'name': 'help-center', 'title': 'Help Center'},
                {'url': 'https://edx.org/media-kit', 'name': 'media_kit', 'title': 'Media Kit'},
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
                {'name': 'media_kit',
                 'title': u'Media Kit',
                 'url': u'https://edx.org/media-kit'}
            ],
            'social_links': [
                {'url': '#', 'action': 'Like \xe9dX on Facebook', 'name': 'facebook',
                 'icon-class': 'fa-facebook-square', 'title': 'Facebook'},
                {'url': '#', 'action': 'Follow \xe9dX on Twitter', 'name': 'twitter',
                 'icon-class': 'fa-twitter-square', 'title': 'Twitter'},
                {'url': '#', 'action': 'Subscribe to the \xe9dX YouTube channel',
                 'name': 'youtube', 'icon-class': 'fa-youtube-square', 'title': 'Youtube'},
                {'url': '#', 'action': 'Follow \xe9dX on LinkedIn', 'name': 'linkedin',
                 'icon-class': 'fa-linkedin-square', 'title': 'LinkedIn'},
                {'url': '#', 'action': 'Follow \xe9dX on Google+', 'name': 'google_plus',
                 'icon-class': 'fa-google-plus-square', 'title': 'Google+'},
                {'url': '#', 'action': 'Subscribe to the \xe9dX subreddit',
                 'name': 'reddit', 'icon-class': 'fa-reddit-square', 'title': 'Reddit'}
            ],
            'mobile_links': [],
            'logo_image': 'https://edx.org/static/images/logo.png',
            'openedx_link': {
                'url': 'http://open.edx.org',
                'image': 'https://files.edx.org/openedx-logos/edx-openedx-logo-tag.png',
                'title': 'Powered by Open edX'
            },
            'edx_org_link': {
                'url': 'https://www.edx.org/?utm_medium=affiliate_partner&utm_source=opensource-partner&utm_content=open-edx-partner-footer-link&utm_campaign=open-edx-footer',
                'text': 'Take free online courses at edX.org',
            },
        }
        self.assertEqual(actual_footer, expected_footer)
