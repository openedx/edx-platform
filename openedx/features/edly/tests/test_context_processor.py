"""
Unit tests for edly_app context_processor
"""
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.site_configuration.tests.test_util import (
    with_site_configuration,
)
from openedx.features.edly.context_processor import edly_app_context

PLATFORM_NAME = 'Test Platform'


@override_settings(PLATFORM_NAME=PLATFORM_NAME)
class EdlyAppContextProcessorTests(TestCase):
    """
    Unit tests for Edly Context processor.
    """

    @with_site_configuration(configuration={
        'EDLY_COPYRIGHT_TEXT': 'test@copyrights',
        'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY': 60,
        'nav_menu_url': marketing_link('NAV_MENU'),
        'zendesk_widget_url': marketing_link('ZENDESK-WIDGET'),
        'footer_url': marketing_link('FOOTER'),
        'GTM_ID': 'GTM-XXXXXX',
        'GA_ID': 'G-XXXXXX'
    })
    def test_default_edly_app_context(self):
        request = RequestFactory().get('/')
        context = edly_app_context(request)
        self.assertEqual(context['services_notifications_cookie_expiry'], 60)
        self.assertEqual(context['edly_copyright_text'], "test@copyrights")
        self.assertEqual(context['nav_menu_url'], marketing_link('NAV_MENU'))
        self.assertEqual(context['zendesk_widget_url'], marketing_link('ZENDESK-WIDGET'))
        self.assertEqual(context['footer_url'], marketing_link('FOOTER'))
        self.assertEqual(context['gtm_id'], 'GTM-XXXXXX')
        self.assertEqual(context['ga_id'], 'G-XXXXXX')
        self.assertEqual(context['is_mobile_app'], False)
