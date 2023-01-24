""" Tests for OAuth 2.0 client credentials support. """


import json
import unittest

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from oauth2_provider.models import Application

from common.djangoapps.student.tests.factories import UserFactory

from ..adapters import DOTAdapter
from . import mixins
from .constants import DUMMY_REDIRECT_URL


@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class ClientCredentialsTest(mixins.AccessTokenMixin, TestCase):
    """ Tests validating the client credentials grant behavior. """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

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
        assert response.status_code == 200

        content = json.loads(response.content.decode('utf-8'))
        access_token = content['access_token']
        assert content['scope'] == data['scope']
        self.assert_valid_jwt_access_token(access_token, self.user, scopes, grant_type='client-credentials')
