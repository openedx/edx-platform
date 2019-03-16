"""
Tests for logout
"""
import unittest

import ddt
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from edx_oauth2_provider.constants import AUTHORIZED_CLIENTS_SESSION_KEY
from edx_oauth2_provider.tests.factories import (
    ClientFactory,
    TrustedClientFactory
)
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class LogoutTests(TestCase):
    """ Tests for the logout functionality. """

    def setUp(self):
        """ Create a course and user, then log in. """
        super(LogoutTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='test')

    def _create_oauth_client(self):
        """ Creates a trusted OAuth client. """
        client = ClientFactory(logout_uri='https://www.example.com/logout/')
        TrustedClientFactory(client=client)
        return client

    def _assert_session_logged_out(self, oauth_client, **logout_headers):
        """ Authenticates a user via OAuth 2.0, logs out, and verifies the session is logged out. """
        self._authenticate_with_oauth(oauth_client)

        # Logging out should remove the session variables, and send a list of logout URLs to the template.
        # The template will handle loading those URLs and redirecting the user. That functionality is not tested here.
        response = self.client.get(reverse('logout'), **logout_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(AUTHORIZED_CLIENTS_SESSION_KEY, self.client.session)

        return response

    def _authenticate_with_oauth(self, oauth_client):
        """ Perform an OAuth authentication using the current web client.

        This should add an AUTHORIZED_CLIENTS_SESSION_KEY entry to the current session.
        """
        data = {
            'client_id': oauth_client.client_id,
            'client_secret': oauth_client.client_secret,
            'response_type': 'code'
        }
        # Authenticate with OAuth to set the appropriate session values
        self.client.post(reverse('oauth2:capture'), data, follow=True)
        self.assertListEqual(self.client.session[AUTHORIZED_CLIENTS_SESSION_KEY], [oauth_client.client_id])

    @ddt.data(
        ('/courses', 'testserver'),
        ('https://edx.org/courses', 'edx.org'),
        ('https://test.edx.org/courses', 'edx.org'),
    )
    @ddt.unpack
    @override_settings(LOGIN_REDIRECT_WHITELIST=['test.edx.org'])
    def test_logout_redirect_success(self, redirect_url, host):
        url = '{logout_path}?redirect_url={redirect_url}'.format(
            logout_path=reverse('logout'),
            redirect_url=redirect_url
        )
        response = self.client.get(url, HTTP_HOST=host)
        expected = {
            'target': redirect_url,
        }
        self.assertDictContainsSubset(expected, response.context_data)

    def test_no_redirect_supplied(self):
        response = self.client.get(reverse('logout'), HTTP_HOST='testserver')
        expected = {
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    @ddt.data(
        ('https://www.amazon.org', 'edx.org'),
    )
    @ddt.unpack
    def test_logout_redirect_failure(self, redirect_url, host):
        url = '{logout_path}?redirect_url={redirect_url}'.format(
            logout_path=reverse('logout'),
            redirect_url=redirect_url
        )
        response = self.client.get(url, HTTP_HOST=host)
        expected = {
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    def test_client_logout(self):
        """ Verify the context includes a list of the logout URIs of the authenticated OpenID Connect clients.

        The list should only include URIs of the clients for which the user has been authenticated.
        """
        client = self._create_oauth_client()
        response = self._assert_session_logged_out(client)
        expected = {
            'logout_uris': [client.logout_uri + '?no_redirect=1'],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    @patch(
        'django.conf.settings.IDA_LOGOUT_URI_LIST',
        ['http://fake.ida1/logout', 'http://fake.ida2/accounts/logout', ]
    )
    def test_client_logout_with_dot_idas(self):
        """
        Verify the context includes a list of the logout URIs of the authenticated OpenID Connect clients AND OAuth2/DOT
        clients.

        The list should only include URIs of the OIDC clients for which the user has been authenticated, and all the
        configured DOT clients regardless of login status..
        """
        client = self._create_oauth_client()
        response = self._assert_session_logged_out(client)
        # Add the logout endpoints for the IDAs where auth was established via OIDC.
        expected_logout_uris = [client.logout_uri + '?no_redirect=1']
        # Add the logout endpoints for the IDAs where auth was established via DOT/OAuth2.
        expected_logout_uris += [
            'http://fake.ida1/logout?no_redirect=1',
            'http://fake.ida2/accounts/logout?no_redirect=1',
        ]
        expected = {
            'logout_uris': expected_logout_uris,
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    @patch(
        'django.conf.settings.IDA_LOGOUT_URI_LIST',
        ['http://fake.ida1/logout', 'http://fake.ida2/accounts/logout', ]
    )
    def test_client_logout_with_dot_idas_and_no_oidc_idas(self):
        """
        Verify the context includes a list of the logout URIs of the OAuth2/DOT clients, even if there are no currently
        authenticated OpenID Connect clients.

        The list should include URIs of all the configured DOT clients.
        """
        response = self.client.get(reverse('logout'))
        # Add the logout endpoints for the IDAs where auth was established via DOT/OAuth2.
        expected_logout_uris = [
            'http://fake.ida1/logout?no_redirect=1',
            'http://fake.ida2/accounts/logout?no_redirect=1',
        ]
        expected = {
            'logout_uris': expected_logout_uris,
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    def test_filter_referring_service(self):
        """ Verify that, if the user is directed to the logout page from a service, that service's logout URL
        is not included in the context sent to the template.
        """
        client = self._create_oauth_client()
        response = self._assert_session_logged_out(client, HTTP_REFERER=client.logout_uri)
        expected = {
            'logout_uris': [],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)
