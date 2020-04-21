"""
Unit tests for edly_app context_processor
"""
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
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
        'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY': 60
    })
    def test_default_edly_app_context(self):
        request = RequestFactory().get('/')
        context = edly_app_context(request)
        self.assertEqual(context['services_notifications_cookie_expiry'], 60)
        self.assertEqual(context['edly_copyright_text'], "test@copyrights")
