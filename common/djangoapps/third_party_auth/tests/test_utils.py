"""
Tests for third_party_auth utility functions.
"""


import unittest

from django.conf import settings

from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.tests.testutil import TestCase
from common.djangoapps.third_party_auth.utils import user_exists, convert_saml_slug_provider_id


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestUtils(TestCase):
    """
    Test the utility functions.
    """
    def test_user_exists(self):
        """
        Verify that user_exists function returns correct response.
        """
        # Create users from factory
        UserFactory(username='test_user', email='test_user@example.com')
        self.assertTrue(
            user_exists({'username': 'test_user', 'email': 'test_user@example.com'}),
        )
        self.assertTrue(
            user_exists({'username': 'test_user'}),
        )
        self.assertTrue(
            user_exists({'email': 'test_user@example.com'}),
        )
        self.assertFalse(
            user_exists({'username': 'invalid_user'}),
        )
        self.assertTrue(
            user_exists({'username': 'TesT_User'})
        )

    def test_convert_saml_slug_provider_id(self):
        """
        Verify saml provider id/slug map to each other correctly.
        """
        provider_names = {'saml-samltest': 'samltest', 'saml-example': 'example'}
        for provider_id in provider_names:
            # provider_id -> slug
            self.assertEqual(
                convert_saml_slug_provider_id(provider_id), provider_names[provider_id]
            )
            # slug -> provider_id
            self.assertEqual(
                convert_saml_slug_provider_id(provider_names[provider_id]), provider_id
            )
