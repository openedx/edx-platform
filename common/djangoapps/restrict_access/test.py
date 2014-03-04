"""Test for restrict access"""

from django.http import HttpResponseRedirect

from django.utils import unittest
from django.test.utils import override_settings
from mock import Mock

from restrict_access.middleware import RestrictAccessMiddleware

class RestrictAccessTest(unittest.TestCase):
    """
    Test the restrict access middleware
    """

    def setUp(self):
        """
        Create a django test request
        """
        self.middleware = RestrictAccessMiddleware()
        self.request = Mock(
            META={'REMOTE_ADDR': '10.0.2.2'},
        )

        # probably not the best way to create an anon request
        del self.request.user

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.0/24',))
    @override_settings(RESTRICT_ACCESS_DENY=('10.0.2.2',))
    def test_restrict_access_authenticated(self):
        """
        Test restrict access with a auth user (automatically allowed).
        """

        # create a request with an authenticated user
        request = Mock(
            META={'REMOTE_ADDR': '10.0.2.2'},
        )

        self.assertIsNone(self.middleware.process_request(request))

    def test_restrict_access_disabled(self):
        """
        Test restrict access disabled
        """

        self.assertIsNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('',))
    def test_restrict_access_invalid_allow(self):
        """
        Test restrict access with an invalid allow settings
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.2',))
    def test_restrict_access_with_request_ip_allow(self):
        """
        Test restrict access with a our request ip address in allow settings
        """

        self.assertIsNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.2',))
    def test_restrict_access_with_request_ip_proxy_allow(self):
        """
        Test restrict access with a our request ip address in allow settings,
        when behing a proxy.
        """

        # create a request to simulate a deployment behing a proxy
        request = Mock(
            META={'REMOTE_ADDR': '10.0.1.1', 'HTTP_X_FORWARDED_FOR': '10.0.2.2'},
        )
        del request.user

        self.assertIsNone(self.middleware.process_request(request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('192.168.4.4',))
    def test_restrict_access_with_unknown_ip_allow(self):
        """
        Test restrict access with a an unknown ip address in allow settings
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_DENY=('10.0.2.2',))
    def test_restrict_access_disabled_with_deny(self):
        """
        Test restrict access disabled, but with deny settings
        """

        self.assertIsNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.2',))
    @override_settings(RESTRICT_ACCESS_DENY=('10.0.2.2',))
    def test_restrict_access_with_request_ip_allow_and_deny(self):
        """
        Test restrict access with a our request ip address in allow and deny
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.2',))
    @override_settings(RESTRICT_ACCESS_DENY=('',))
    def test_restrict_access_with_request_ip_allow_and_invalid_deny(self):
        """
        Test restrict access with a our request ip address in allow and an invalid deny
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.0/32',))
    def test_restrict_access_with_network_32(self):
        """
        Test restrict access with a our request ip address not in the allow network
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.0/24',))
    def test_restrict_access_with_network_24(self):
        """
        Test restrict access with a our request ip address in the allow network
        """

        self.assertIsNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.0/24',))
    @override_settings(RESTRICT_ACCESS_DENY=('10.0.2.2/32',))
    def test_restrict_access_with_network_24_with_deny(self):
        """
        Test restrict access with a our request ip address include in the allow network, but also in deny.
        """

        self.assertIsNotNone(self.middleware.process_request(self.request))

    @override_settings(RESTRICT_ACCESS_REDIRECT_URL='http://code.edx.org/')
    @override_settings(RESTRICT_ACCESS_ALLOW=('10.0.2.0/24',))
    @override_settings(RESTRICT_ACCESS_DENY=('10.0.2.2/32',))
    def test_restrict_access_with_network_24_with_deny_and_redirect(self):
        """
        Test restrict access with a our request ip address include in the allow network, but also in deny... with a redirect url.
        """

        self.assertIsInstance(
            self.middleware.process_request(self.request),
            HttpResponseRedirect)
