""" Tests for Django template context processors. """
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from microsite_configuration.context_processors import microsite_context

PLATFORM_NAME = 'Test Platform'


@override_settings(PLATFORM_NAME=PLATFORM_NAME)
class MicrositeContextProcessorTests(TestCase):
    """ Tests for the microsite context processor. """

    def setUp(self):
        super(MicrositeContextProcessorTests, self).setUp()
        request = RequestFactory().get('/')
        self.context = microsite_context(request)

    def test_platform_name(self):
        """ Verify the context includes the platform name. """
        self.assertEqual(self.context['platform_name'], PLATFORM_NAME)
