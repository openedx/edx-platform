"""
Tests for DOP Adapter
"""

from datetime import timedelta

import ddt
from django.test import TestCase
from django.utils.timezone import now
from provider.oauth2 import models
from provider import constants

from student.tests.factories import UserFactory

from ..adapters import DOPAdapter
from .constants import DUMMY_REDIRECT_URL


@ddt.ddt
class DOPAdapterTestCase(TestCase):
    """
    Test class for DOPAdapter.
    """

    adapter = DOPAdapter()

    def setUp(self):
        super(DOPAdapterTestCase, self).setUp()
        self.user = UserFactory()
        self.public_client = self.adapter.create_public_client(
            name='public client',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='public-client-id',
        )
        self.confidential_client = self.adapter.create_confidential_client(
            name='confidential client',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='confidential-client-id',
        )

    @ddt.data(
        ('confidential', constants.CONFIDENTIAL),
        ('public', constants.PUBLIC),
    )
    @ddt.unpack
    def test_create_client(self, client_name, client_type):
        client = getattr(self, '{}_client'.format(client_name))
        self.assertIsInstance(client, models.Client)
        self.assertEqual(client.client_id, '{}-client-id'.format(client_name))
        self.assertEqual(client.client_type, client_type)

    def test_get_client(self):
        client = self.adapter.get_client(client_type=constants.CONFIDENTIAL)
        self.assertIsInstance(client, models.Client)
        self.assertEqual(client.client_type, constants.CONFIDENTIAL)

    def test_get_client_not_found(self):
        with self.assertRaises(models.Client.DoesNotExist):
            self.adapter.get_client(client_id='not-found')

    def test_get_client_for_token(self):
        token = models.AccessToken(
            user=self.user,
            client=self.public_client,
        )
        self.assertEqual(self.adapter.get_client_for_token(token), self.public_client)

    def test_get_access_token(self):
        token = models.AccessToken.objects.create(
            token='token-id',
            client=self.public_client,
            user=self.user,
            expires=now() + timedelta(days=30),
        )
        self.assertEqual(self.adapter.get_access_token(token_string='token-id'), token)
