"""
Tests for third_party_auth utility functions.
"""
import unittest
from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from third_party_auth.tests.testutil import TestCase
from third_party_auth.utils import user_exists, UsernameGenerator

from student.tests.factories import UserFactory


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


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@override_settings(FEATURES={"ENABLE_REGISTRATION_USERNAME_SUGGESTION": True})
class UsernameGeneratorTestCase(TestCase):
    """
    Test the utility functions.
    """
    def setUp(self):
        self.enable_saml()
        UserFactory(username='my_self_user', email='test_user@example.com')
        self.fullname = 'My Self User'

    def test_separator(self):
        """
        The first step to generate a hinted username is the separator character of the
        full name string. This test makes sure that we are generating a username replacing
        all whitespaces by a character configured in settings or in site_configurations.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'SEPARATOR': '.'}
        )
        generator = UsernameGenerator(saml.other_settings)
        username = generator.replace_separator(self.fullname)
        return self.assertEqual(username, "My.Self.User")

    def test_generate_username_in_lowercase(self):
        """
        Test if the full name that comes from insert_separator method
        it's converted in lowercase.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'LOWER': True}
        )
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.process_case('My_Self_User')
        return self.assertEqual(new_username, 'my_self_user')

    def test_generate_username_not_lowercase(self):
        """
        Test if the full name that comes from insert_separator method
        is not converted in lowercase and preserves their original lowercases and
        uppers cases.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'LOWER': False}
        )
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.process_case('My_Self_User')
        return self.assertEqual(new_username, 'My_Self_User')

    def test_generate_username_with_consecutive(self):
        """
        It should return a new user with a consecutive number.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'RANDOM': False}
        )
        for i in range(1, 6):
            User.objects.create(
                username='my_self_user_{}'.format(i)
            )
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.generate_username(self.fullname)
        # We have 6 users: Five created in the loop with a consecutive
        # number and another one that comes from initial setUp,
        # the first has not consecutive number due to is
        # not neccesary append an differentiator. We expect a new user with
        # the consecutive number 6.
        return self.assertEqual(new_username, 'my_self_user_6')

    @patch('third_party_auth.utils.UsernameGenerator.get_random')
    def test_generate_username_with_random(self, mock_random):
        """
        It should return a username with a random integer
        at the end of the username generated.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'RANDOM': True}
        )
        mock_random.return_value = 4589
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.generate_username(self.fullname)
        return self.assertEqual(new_username, 'my_self_user_4589')

    @patch('third_party_auth.utils.UsernameGenerator.get_random')
    def test_generate_username_with_repetitive_random(self, mock_random):
        """
        If a random generated number is repeated, should append
        a suffix with another random that does not exists.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'RANDOM': True}
        )
        mock_random.side_effect = [4589, 9819]
        User.objects.create(username='my_self')
        User.objects.create(username='my_self_4589')
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.generate_username('My Self')
        return self.assertEqual(new_username, 'my_self_9819')

    def test_username_without_modifications(self):
        """
        If the provided username does not exists
        in database, should return the username without
        any modifications of suffix number.
        """
        saml = self.configure_saml_provider(
            enabled=True,
            name="Saml Test",
            idp_slug="test",
            backend_name="saml_backend",
            other_settings={'RANDOM': True}
        )
        not_existing_user = 'Another Myself'
        generator = UsernameGenerator(saml.other_settings)
        new_username = generator.generate_username(not_existing_user)
        return self.assertEqual(new_username, 'another_myself')
