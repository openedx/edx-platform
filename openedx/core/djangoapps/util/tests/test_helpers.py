"""
Tests for the helper methods.
"""

import jwt
from oauth2_provider.tests.factories import ClientFactory
from provider.oauth2.models import AccessToken, Client
from unittest import skipUnless

from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.util.helpers import get_id_token
from student.tests.factories import UserFactory


@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetIdTokenTest(TestCase):
    """
    Tests for then helper method 'get_id_token'.
    """
    def setUp(self):
        self.client_name = "edx-dummy-client"
        ClientFactory(name=self.client_name)
        super(GetIdTokenTest, self).setUp()
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

    def test_get_id_token(self):
        """
        Test generation of ID Token.
        """
        # test that a user with no ID Token gets a valid token on calling the
        # method 'get_id_token' against a client
        self.assertEqual(AccessToken.objects.all().count(), 0)
        client = Client.objects.get(name=self.client_name)
        first_token = get_id_token(self.user, self.client_name)
        self.assertEqual(AccessToken.objects.all().count(), 1)
        jwt.decode(first_token, client.client_secret, audience=client.client_id)

        # test that a user with existing ID Token gets the same token instead
        # of a new generated token
        second_token = get_id_token(self.user, self.client_name)
        self.assertEqual(AccessToken.objects.all().count(), 1)
        self.assertEqual(first_token, second_token)
