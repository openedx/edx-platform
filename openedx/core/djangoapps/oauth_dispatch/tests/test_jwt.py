""" Tests for OAuth Dispatch's jwt module. """


import itertools
from datetime import timedelta

import ddt
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from openedx.core.djangoapps.oauth_dispatch import jwt as jwt_api
from openedx.core.djangoapps.oauth_dispatch.adapters import DOTAdapter
from openedx.core.djangoapps.oauth_dispatch.models import RestrictedApplication
from openedx.core.djangoapps.oauth_dispatch.tests.mixins import AccessTokenMixin
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class TestCreateJWTs(AccessTokenMixin, TestCase):
    """ Tests for oauth_dispatch's jwt creation functionality. """
    def setUp(self):
        super(TestCreateJWTs, self).setUp()
        self.user = UserFactory()
        self.default_scopes = ['email', 'profile']

    def _create_client(self, oauth_adapter, client_restricted):
        """
        Creates and returns an OAuth client using the given oauth_adapter.
        Configures the client as a RestrictedApplication if client_restricted is
        True.
        """
        client = oauth_adapter.create_public_client(
            name='public app',
            user=self.user,
            redirect_uri='',
            client_id='public-client-id',
        )
        if client_restricted:
            RestrictedApplication.objects.create(application=client)
        return client

    def _create_jwt_for_token(
        self, oauth_adapter, use_asymmetric_key, client_restricted=False,
    ):
        """ Creates and returns the jwt returned by jwt_api.create_jwt_from_token. """
        client = self._create_client(oauth_adapter, client_restricted)
        expires_in = 60 * 60
        expires = now() + timedelta(seconds=expires_in)
        token_dict = dict(
            access_token=oauth_adapter.create_access_token_for_test('token', client, self.user, expires),
            expires_in=expires_in,
            scope=' '.join(self.default_scopes)
        )
        return jwt_api.create_jwt_from_token(token_dict, oauth_adapter, use_asymmetric_key=use_asymmetric_key)

    def _assert_jwt_is_valid(self, jwt_token, should_be_asymmetric_key):
        """ Asserts the given jwt_token is valid and meets expectations. """
        self.assert_valid_jwt_access_token(
            jwt_token, self.user, self.default_scopes, should_be_asymmetric_key=should_be_asymmetric_key,
        )

    def test_create_jwt_for_token(self):
        oauth_adapter = DOTAdapter()
        jwt_token = self._create_jwt_for_token(oauth_adapter, use_asymmetric_key=False)
        self._assert_jwt_is_valid(jwt_token, should_be_asymmetric_key=False)

    def test_dot_create_jwt_for_token_with_asymmetric(self):
        jwt_token = self._create_jwt_for_token(DOTAdapter(), use_asymmetric_key=True)
        self._assert_jwt_is_valid(jwt_token, should_be_asymmetric_key=True)

    @ddt.data((True, False))
    def test_dot_create_jwt_for_token(self, client_restricted):
        jwt_token = self._create_jwt_for_token(
            DOTAdapter(),
            use_asymmetric_key=None,
            client_restricted=client_restricted,
        )
        self._assert_jwt_is_valid(jwt_token, should_be_asymmetric_key=client_restricted)

    @patch('openedx.core.djangoapps.oauth_dispatch.jwt.create_role_auth_claim_for_user')
    @ddt.data(True, False)
    def test_create_jwt_for_user(self, user_email_verified, mock_create_roles):
        mock_create_roles.return_value = ['superuser', 'enterprise-admin']
        self.user.is_active = user_email_verified
        self.user.save()

        aud = 'test_aud'
        secret = 'test_secret'
        additional_claims = {'claim1_key': 'claim1_val'}
        jwt_token = jwt_api.create_jwt_for_user(self.user, secret=secret, aud=aud, additional_claims=additional_claims)
        token_payload = self.assert_valid_jwt_access_token(
            jwt_token, self.user, self.default_scopes, aud=aud, secret=secret,
        )
        self.assertDictContainsSubset(additional_claims, token_payload)
        self.assertEqual(user_email_verified, token_payload['email_verified'])
        self.assertEqual(token_payload['roles'], mock_create_roles.return_value)

    def test_scopes(self):
        """
        Ensure the requested scopes are used.
        """
        scopes = [
            'user_id',
        ]
        aud = 'test_aud'
        secret = 'test_secret'

        jwt = jwt_api.create_jwt_for_user(self.user, secret=secret, aud=aud)
        jwt_scopes = jwt_api.create_jwt_for_user(self.user, secret=secret, aud=aud, scopes=scopes)

        jwt_payload = self.assert_valid_jwt_access_token(
            jwt, self.user, self.default_scopes, aud=aud, secret=secret,
        )
        jwt_scopes_payload = self.assert_valid_jwt_access_token(
            jwt_scopes, self.user, scopes, aud=aud, secret=secret,
        )
        self.assertEqual(jwt_payload['scopes'], self.default_scopes)
        self.assertEqual(jwt_scopes_payload['scopes'], scopes)
        self.assertEqual(jwt_scopes_payload['user_id'], self.user.id)
