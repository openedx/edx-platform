from django.test.client import RequestFactory
from django.conf import settings
from util.request import safe_get_host
from django.core.exceptions import SuspiciousOperation
import unittest


class ResponseTestCase(unittest.TestCase):
    """ Tests for response-related utility functions """
    def setUp(self):
        self.old_site_name = settings.SITE_NAME
        self.old_allowed_hosts = settings.ALLOWED_HOSTS

    def tearDown(self):
        settings.SITE_NAME = self.old_site_name
        settings.ALLOWED_HOSTS = self.old_allowed_hosts

    def test_safe_get_host(self):
        """ Tests that the safe_get_host function returns the desired host """
        settings.SITE_NAME = 'siteName.com'
        factory = RequestFactory()
        request = factory.request()
        request.META['HTTP_HOST'] = 'www.userProvidedHost.com'
        # If ALLOWED_HOSTS is not set properly, safe_get_host should return SITE_NAME
        settings.ALLOWED_HOSTS = None
        self.assertEqual(safe_get_host(request), "siteName.com")
        settings.ALLOWED_HOSTS = ["*"]
        self.assertEqual(safe_get_host(request), "siteName.com")
        settings.ALLOWED_HOSTS = ["foo.com", "*"]
        self.assertEqual(safe_get_host(request), "siteName.com")

        # If ALLOWED_HOSTS is set properly, and the host is valid, we just return the user-provided host
        settings.ALLOWED_HOSTS = [request.META['HTTP_HOST']]
        self.assertEqual(safe_get_host(request), request.META['HTTP_HOST'])

        # If ALLOWED_HOSTS is set properly but the host is invalid, we should get a SuspiciousOperation
        settings.ALLOWED_HOSTS = ["the_valid_website.com"]
        with self.assertRaises(SuspiciousOperation):
            safe_get_host(request)
