"""
Tests for DOT Adapter
"""

from datetime import timedelta

import ddt
from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now
from oauth2_provider import models
import unittest

from student.tests.factories import UserFactory

from ..adapters import DOTAdapter
from .constants import DUMMY_REDIRECT_URL, DUMMY_REDIRECT_URL2
from ..models import RestrictedApplication


@ddt.ddt
@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class DOTAdapterTestCase(TestCase):
    """
    Test class for DOTAdapter.
    """

    adapter = DOTAdapter()

    def setUp(self):
        super(DOTAdapterTestCase, self).setUp()
        self.user = UserFactory()
        self.public_client = self.adapter.create_public_client(
            name='public app',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='public-client-id',
        )
        self.confidential_client = self.adapter.create_confidential_client(
            name='confidential app',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='confidential-client-id',
        )
        self.restricted_client = self.adapter.create_confidential_client(
            name='restricted app',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL2,
            client_id='restricted-client-id',
        )
        self.restricted_app = RestrictedApplication.objects.create(application=self.restricted_client)

    def test_restricted_app_unicode(self):
        """
        Make sure unicode representation of RestrictedApplication is correct
        """
        self.assertEqual(unicode(self.restricted_app), u"<RestrictedApplication '{name}'>".format(
            name=self.restricted_client.name
        ))

    @ddt.data(
        ('confidential', models.Application.CLIENT_CONFIDENTIAL),
        ('public', models.Application.CLIENT_PUBLIC),
    )
    @ddt.unpack
    def test_create_client(self, client_name, client_type):
        client = getattr(self, '{}_client'.format(client_name))
        self.assertIsInstance(client, models.Application)
        self.assertEqual(client.client_id, '{}-client-id'.format(client_name))
        self.assertEqual(client.client_type, client_type)

    def test_get_client(self):
        """
        Read back one of the confidential clients (there are two)
        and verify that we get back what we expected
        """
        client = self.adapter.get_client(
            redirect_uris=DUMMY_REDIRECT_URL,
            client_type=models.Application.CLIENT_CONFIDENTIAL
        )
        self.assertIsInstance(client, models.Application)
        self.assertEqual(client.client_type, models.Application.CLIENT_CONFIDENTIAL)

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
        self.assertEqual(self.adapter.get_access_token(token_string='token-id'), token)

    def test_get_restricted_access_token(self):
        """
        Make sure when generating an access_token for a restricted client
        that the token is immediately expired
        """
        models.AccessToken.objects.create(
            token='expired-token-id',
            application=self.restricted_client,
            user=self.user,
            expires=now() + timedelta(days=30),
        )

        readback_token = self.adapter.get_access_token(token_string='expired-token-id')
        self.assertTrue(RestrictedApplication.verify_access_token_as_expired(readback_token))
