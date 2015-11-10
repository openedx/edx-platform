"""Tests covering utilities for working with access tokens."""
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
import jwt
from oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import AccessToken

from openedx.core.lib.token_utils import get_id_token
from student.tests.factories import UserFactory


class TestIdTokenGeneration(TestCase):
    """Tests covering ID token generation."""
    client_name = 'edx-dummy-client'

    def setUp(self):
        super(TestIdTokenGeneration, self).setUp()

        self.oauth2_client = ClientFactory(name=self.client_name, client_type=CONFIDENTIAL)
        self.user = UserFactory()

    def test_get_id_token(self):
        """Verify that ID tokens are generated as expected."""
        self.assertEqual(AccessToken.objects.all().count(), 0)

        # Verify that a user with no existing access token has one
        # created for them when an ID token is generated.
        first_token = get_id_token(self.user, self.client_name)
        self.assertEqual(AccessToken.objects.all().count(), 1)

        # Verify that the JWT was signed with the expected secret, and that
        # the audience claim is correct.
        jwt.decode(first_token, self.oauth2_client.client_secret, audience=self.oauth2_client.client_id)

        # Verify that a user with an existing, valid access token doesn't
        # have a second generated for them when requesting an ID token.
        second_token = get_id_token(self.user, self.client_name)
        self.assertEqual(AccessToken.objects.all().count(), 1)
        self.assertEqual(first_token, second_token)

    def test_get_id_token_invalid_client(self):
        """Verify that ImproperlyConfigured is raised when an invalid client name is provided."""
        with self.assertRaises(ImproperlyConfigured):
            get_id_token(self.user, 'does-not-exist')
