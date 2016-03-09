"""
Tests for Blocks Views
"""

from datetime import timedelta
from unittest import skip

import ddt
from django.test import TestCase
from django.utils.timezone import now
from oauth2_provider import models

from student.tests.factories import UserFactory

from ..adapters import dot


@ddt.ddt
class TestAccessTokenView(TestCase):
    """
    Test class for AccessTokenView
    """

    adapter = dot.DOTAdapter()

    def setUp(self):
        super(TestAccessTokenView, self).setUp()
        self.user = UserFactory()
        self.public_client = self.adapter.create_public_client(user=self.user, client_id='public-client-id')
        self.confidential_client = self.adapter.create_confidential_client(
            user=self.user,
            client_id='confidential-client-id'
        )

    def test_create_confidential_client(self):
        self.assertIsInstance(self.confidential_client, models.Application)
        self.assertEqual(self.confidential_client.client_id, 'confidential-client-id')
        self.assertEqual(self.confidential_client.client_type, 'confidential')

    def test_create_public_client(self):
        self.assertIsInstance(self.public_client, models.Application)
        self.assertEqual(self.public_client.client_id, 'public-client-id')
        self.assertEqual(self.public_client.client_type, 'public')

    def test_get_client(self):
        client = self.adapter.get_client(client_type='confidential')
        self.assertIsInstance(client, models.Application)
        self.assertEqual(client.client_type, 'confidential')

    def test_get_client_not_found(self):
        with self.assertRaises(models.Application.DoesNotExist):
            self.adapter.get_client(client_id='not-found')

    def test_get_client_for_token(self):
        token = models.AccessToken(
            user=self.user,
            application=self.public_client,
        )
        self.assertEqual(self.adapter.get_client_for_token(token), self.public_client)

    def test_get_access_token(self):
        token = models.AccessToken.objects.create(
            token='token-id',
            application=self.public_client,
            user=self.user,
            expires=now() + timedelta(days=30),
        )
        self.assertEqual(
            self.adapter.get_access_token(token_string='token-id'),
            token
        )

    def test_refresh_token_in_token_response_keys(self):
        self.assertIn('refresh_token', self.adapter.get_token_response_keys())

    @skip("Scopes not yet supported for django-oauth-toolkit (MA-2123)")
    def test_normalize_scopes(self):
        self.fail()

    @skip("Scopes not yet supported for django-oauth-toolkit (MA-2123)")
    def test_get_token_scope_names(self):
        self.fail()
