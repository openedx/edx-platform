""" Tests for OAuth 2.0 client credentials support. """
from __future__ import unicode_literals

import json
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from edx_oauth2_provider.tests.factories import ClientFactory
from oauth2_provider.models import Application
from provider.oauth2.models import AccessToken
from student.tests.factories import UserFactory

from . import mixins
from .constants import DUMMY_REDIRECT_URL
from ..adapters import DOTAdapter


@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class ClientCredentialsTest(mixins.AccessTokenMixin, TestCase):
    """ Tests validating the client credentials grant behavior. """

    def setUp(self):
        super(ClientCredentialsTest, self).setUp()
        self.user = UserFactory()

    def test_access_token(self):
        """ Verify the client credentials grant can be used to obtain an access token whose default scopes allow access
        to the user info endpoint.
        """
        oauth_client = ClientFactory(user=self.user)
        data = {
            'grant_type': 'client_credentials',
            'client_id': oauth_client.client_id,
            'client_secret': oauth_client.client_secret
        }
        response = self.client.post(reverse('oauth2:access_token'), data)
        self.assertEqual(response.status_code, 200)

        access_token = json.loads(response.content)['access_token']
        expected = AccessToken.objects.filter(client=oauth_client, user=self.user).first().token
        self.assertEqual(access_token, expected)

        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }
        response = self.client.get(reverse('oauth2:user_info'), **headers)
        self.assertEqual(response.status_code, 200)

    def test_jwt_access_token(self):
        """ Verify the client credentials grant can be used to obtain a JWT access token. """
        application = DOTAdapter().create_confidential_client(
            name='test dot application',
            user=self.user,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dot-app-client-id',
        )
        scopes = ['read', 'write', 'email']
        data = {
            'grant_type': 'client_credentials',
            'client_id': application.client_id,
            'client_secret': application.client_secret,
            'scope': ' '.join(scopes),
            'token_type': 'jwt'
        }

        response = self.client.post(reverse('access_token'), data)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        access_token = content['access_token']
        self.assertEqual(content['scope'], data['scope'])
        self.assert_valid_jwt_access_token(access_token, self.user, scopes)
