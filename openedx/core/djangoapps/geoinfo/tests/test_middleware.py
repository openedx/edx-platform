"""
Tests for CountryMiddleware.
"""


import geoip2
import maxminddb
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from mock import MagicMock, PropertyMock, patch

from openedx.core.djangoapps.geoinfo.middleware import CountryMiddleware
from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory


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
        patcher = patch.object(maxminddb, 'open_database')
        patcher.start()
        country_patcher = patch.object(geoip2.database.Reader, 'country', self.mock_country)
        country_patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(country_patcher.stop)

    def mock_country(self, ip_address):
        """
        :param ip_address:
        :return:
        """
        ip_dict = {
            '117.79.83.1': 'CN',
            '117.79.83.100': 'CN',
            '4.0.0.0': 'SD',
            '2001:da8:20f:1502:edcf:550b:4a9c:207d': 'CN',
        }

        magic_mock = MagicMock()
        magic_mock.country = MagicMock()
        type(magic_mock.country).iso_code = PropertyMock(return_value=ip_dict.get(ip_address))

        return magic_mock

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
