"""
Tests for third_party_auth decorators.
"""
import ddt
import unittest
import datetime

from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory

from third_party_auth.decorators import xframe_allow_whitelisted, allow_frame_from_whitelisted_url
from third_party_auth.tests.testutil import TestCase

SCORM_CLOUD_URL = 'https://cloud.scorm.com'


def mock_view(_request):
    """ A test view for testing purposes. """
    return HttpResponse()


# remove this decorator once third_party_auth is enabled in CMS
@unittest.skipIf(
    'third_party_auth' not in settings.INSTALLED_APPS,
    'third_party_auth is not currently installed in CMS'
)
@ddt.ddt
class TestXFrameWhitelistDecorator(TestCase):
    """ Test the xframe_allow_whitelisted decorator. """

    def setUp(self):
        super(TestXFrameWhitelistDecorator, self).setUp()
        self.configure_lti_provider(name='Test', lti_hostname='localhost', lti_consumer_key='test_key', enabled=True)
        self.factory = RequestFactory()

    def construct_request(self, referer):
        """ Add the given referer to a request and then return it. """
        request = self.factory.get('/login')
        request.META['HTTP_REFERER'] = referer
        return request

    @ddt.unpack
    @ddt.data(
        ('http://localhost:8000/login', 'ALLOW'),
        ('http://not-a-real-domain.com/login', 'DENY'),
        (None, 'DENY')
    )
    def test_x_frame_options(self, url, expected_result):
        request = self.construct_request(url)

        response = xframe_allow_whitelisted(mock_view)(request)

        self.assertEqual(response['X-Frame-Options'], expected_result)

    @ddt.data('http://localhost/login', 'http://not-a-real-domain.com', None)
    def test_feature_flag_off(self, url):
        with self.settings(FEATURES={'ENABLE_THIRD_PARTY_AUTH': False}):
            request = self.construct_request(url)
            response = xframe_allow_whitelisted(mock_view)(request)
            self.assertEqual(response['X-Frame-Options'], 'DENY')


# remove this decorator once third_party_auth is enabled in CMS
@unittest.skipIf(
    'third_party_auth' not in settings.INSTALLED_APPS,
    'third_party_auth is not currently installed in CMS'
)
@ddt.ddt
class TestXFrameWhitelistDecoratorForSAML(TestCase):
    """ Test the allow_frame_from_whitelisted_url decorator. """

    def setUp(self):
        super(TestXFrameWhitelistDecoratorForSAML, self).setUp()
        self.configure_saml_provider_data(
            entity_id='https://idp.testshib.org/idp/shibboleth',
            sso_url='https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO',
            public_key='testkey',
            fetched_at=datetime.datetime.now()
        )
        self.factory = RequestFactory()

    def construct_request(self, referer):
        """ Add the given referer to a request and then return it. """
        request = self.factory.get('/auth/custom_auth_entry')
        request.META['HTTP_REFERER'] = referer
        return request

    @ddt.unpack
    @ddt.data(
        (
            'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO?param1=1&param2=',
            {
                'X-Frame-Options': 'ALLOW-FROM %s' % SCORM_CLOUD_URL,
                'Content-Security-Policy': "frame-ancestors %s" % SCORM_CLOUD_URL,

            }
        ),
        (
            'http://not-a-real-domain.com/SSO',
            {
                'X-Frame-Options': 'DENY',
                'Content-Security-Policy': "frame-ancestors 'none'",

            }
        ),
        (
            None,
            {
                'X-Frame-Options': 'DENY',
                'Content-Security-Policy': "frame-ancestors 'none'",

            }
        )
    )
    def test_x_frame_options(self, url, expected_headers):
        with self.settings(THIRD_PARTY_AUTH_FRAME_ALLOWED_FROM_URL=[SCORM_CLOUD_URL]):
            request = self.construct_request(url)
            response = allow_frame_from_whitelisted_url(mock_view)(request)
            for header, value in expected_headers.items():
                self.assertEqual(response[header], value)

    @ddt.data('https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO', 'http://not-a-real-domain.com/SSO', None)
    def test_feature_flag_off(self, url):
        with self.settings(FEATURES={'ENABLE_THIRD_PARTY_AUTH': False}):
            request = self.construct_request(url)
            response = allow_frame_from_whitelisted_url(mock_view)(request)
            self.assertEqual(response['X-Frame-Options'], 'DENY')
            self.assertEqual(response['Content-Security-Policy'], "frame-ancestors 'none'")
