"""
Tests for Django template context processors.
"""


from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory

from lms.djangoapps.mobile_api.context_processor import is_from_mobile_app


class MobileContextProcessorTests(TestCase):
    """
    Tests for the configuration context processor.
    """

    def test_is_from_mobile_app(self):
        """
        Verify the context is from mobile app.
        """
        request = RequestFactory().get('/')
        request.META['HTTP_USER_AGENT'] = settings.MOBILE_APP_USER_AGENT_REGEXES[0]
        context = is_from_mobile_app(request)
        assert context['is_from_mobile_app'] is True

    def test_not_is_from_mobile_app(self):
        """
        Verify the context is not from the mobile app.
        """
        request = RequestFactory().get('/')
        request.META['HTTP_USER_AGENT'] = "Not from the mobile app"
        context = is_from_mobile_app(request)
        assert context['is_from_mobile_app'] is False
