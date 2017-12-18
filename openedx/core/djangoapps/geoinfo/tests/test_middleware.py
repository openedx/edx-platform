# pylint: disable=no-member
"""
Tests for CountryMiddleware.
"""
from mock import patch
import pygeoip

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.geoinfo.middleware import CountryMiddleware
from student.tests.factories import UserFactory, AnonymousUserFactory


class CountryMiddlewareTests(TestCase):
    """
    Tests of CountryMiddleware.
    """
    def setUp(self):
        super(CountryMiddlewareTests, self).setUp()
        self.country_middleware = CountryMiddleware()
        self.session_middleware = SessionMiddleware()
        self.authenticated_user = UserFactory.create()
        self.anonymous_user = AnonymousUserFactory.create()
        self.request_factory = RequestFactory()
        self.patcher = patch.object(pygeoip.GeoIP, 'country_code_by_addr', self.mock_country_code_by_addr)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def mock_country_code_by_addr(self, ip_addr):
        """
        Gives us a fake set of IPs
        """
        ip_dict = {
            '117.79.83.1': 'CN',
            '117.79.83.100': 'CN',
            '4.0.0.0': 'SD',
            '2001:da8:20f:1502:edcf:550b:4a9c:207d': 'CN',
        }
        return ip_dict.get(ip_addr, 'US')

    def test_country_code_added(self):
        request = self.request_factory.get(
            '/somewhere',
            HTTP_X_FORWARDED_FOR='117.79.83.1',
        )
        request.user = self.authenticated_user
        self.session_middleware.process_request(request)
        # No country code exists before request.
        self.assertNotIn('country_code', request.session)
        self.assertNotIn('ip_address', request.session)
        self.country_middleware.process_request(request)
        # Country code added to session.
        self.assertEqual('CN', request.session.get('country_code'))
        self.assertEqual('117.79.83.1', request.session.get('ip_address'))

    def test_ip_address_changed(self):
        request = self.request_factory.get(
            '/somewhere',
            HTTP_X_FORWARDED_FOR='4.0.0.0',
        )
        request.user = self.anonymous_user
        self.session_middleware.process_request(request)
        request.session['country_code'] = 'CN'
        request.session['ip_address'] = '117.79.83.1'
        self.country_middleware.process_request(request)
        # Country code is changed.
        self.assertEqual('SD', request.session.get('country_code'))
        self.assertEqual('4.0.0.0', request.session.get('ip_address'))

    def test_ip_address_is_not_changed(self):
        request = self.request_factory.get(
            '/somewhere',
            HTTP_X_FORWARDED_FOR='117.79.83.1',
        )
        request.user = self.anonymous_user
        self.session_middleware.process_request(request)
        request.session['country_code'] = 'CN'
        request.session['ip_address'] = '117.79.83.1'
        self.country_middleware.process_request(request)
        # Country code is not changed.
        self.assertEqual('CN', request.session.get('country_code'))
        self.assertEqual('117.79.83.1', request.session.get('ip_address'))

    def test_same_country_different_ip(self):
        request = self.request_factory.get(
            '/somewhere',
            HTTP_X_FORWARDED_FOR='117.79.83.100',
        )
        request.user = self.anonymous_user
        self.session_middleware.process_request(request)
        request.session['country_code'] = 'CN'
        request.session['ip_address'] = '117.79.83.1'
        self.country_middleware.process_request(request)
        # Country code is not changed.
        self.assertEqual('CN', request.session.get('country_code'))
        self.assertEqual('117.79.83.100', request.session.get('ip_address'))

    def test_ip_address_is_none(self):
        # IP address is not defined in request.
        request = self.request_factory.get('/somewhere')
        request.user = self.anonymous_user
        # Run process_request to set up the session in the request
        # to be able to override it.
        self.session_middleware.process_request(request)
        request.session['country_code'] = 'CN'
        request.session['ip_address'] = '117.79.83.1'
        self.country_middleware.process_request(request)
        # No country code exists after request processing.
        self.assertNotIn('country_code', request.session)
        self.assertNotIn('ip_address', request.session)

    def test_ip_address_is_ipv6(self):
        request = self.request_factory.get(
            '/somewhere',
            HTTP_X_FORWARDED_FOR='2001:da8:20f:1502:edcf:550b:4a9c:207d'
        )
        request.user = self.authenticated_user
        self.session_middleware.process_request(request)
        # No country code exists before request.
        self.assertNotIn('country_code', request.session)
        self.assertNotIn('ip_address', request.session)
        self.country_middleware.process_request(request)
        # Country code added to session.
        self.assertEqual('CN', request.session.get('country_code'))
        self.assertEqual(
            '2001:da8:20f:1502:edcf:550b:4a9c:207d', request.session.get('ip_address'))
