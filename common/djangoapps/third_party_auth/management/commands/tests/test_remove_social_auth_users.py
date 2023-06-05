"""
Tests for `remove_social_auth_users` management command
"""


import sys
import unittest
from contextlib import contextmanager
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from six import StringIO
from social_django.models import UserSocialAuth

from common.djangoapps.student.models import User
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.management.commands import remove_social_auth_users
from common.djangoapps.third_party_auth.tests.factories import SAMLProviderConfigFactory

FEATURES_WITH_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_ENABLED['ENABLE_ENROLLMENT_RESET'] = True


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestRemoveSocialAuthUsersCommand(TestCase):
    """
    Test django management command
    """
    @classmethod
    def setUpClass(cls):
        super(TestRemoveSocialAuthUsersCommand, cls).setUpClass()
        cls.command = remove_social_auth_users.Command()

    def setUp(self):
        super(TestRemoveSocialAuthUsersCommand, self).setUp()
        self.provider_hogwarts = SAMLProviderConfigFactory.create(slug='hogwarts')
        self.provider_durmstrang = SAMLProviderConfigFactory.create(slug='durmstrang')

        self.user_fleur = UserFactory(username='fleur')      # no social auth
        self.user_harry = UserFactory(username='harry')      # social auth for Hogwarts
        self.user_viktor = UserFactory(username='viktor')    # social auth for Durmstrang

        self.create_social_auth_entry(self.user_harry, self.provider_hogwarts)
        self.create_social_auth_entry(self.user_viktor, self.provider_durmstrang)

    @contextmanager
    def _replace_stdin(self, text):
        orig = sys.stdin
        sys.stdin = StringIO(text)
        yield
        sys.stdin = orig

    def create_social_auth_entry(self, user, provider):
        external_id = uuid4()
        UserSocialAuth.objects.create(
            user=user,
            uid='{0}:{1}'.format(provider.slug, external_id),
            provider=provider.slug,
        )

    def find_user_social_auth_entry(self, username):
        UserSocialAuth.objects.get(user__username=username)

    @override_settings(FEATURES=FEATURES_WITH_ENABLED)
    def test_remove_users(self):
        call_command(self.command, self.provider_hogwarts.slug, force=True)

        # user with input idp is removed, along with social auth entries
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='harry')
        with self.assertRaises(UserSocialAuth.DoesNotExist):
            self.find_user_social_auth_entry('harry')

        # other users intact
        self.user_fleur.refresh_from_db()
        self.user_viktor.refresh_from_db()
        self.assertIsNotNone(self.user_fleur)
        self.assertIsNotNone(self.user_viktor)

        # other social auth intact
        self.find_user_social_auth_entry(self.user_viktor.username)

    @override_settings(FEATURES=FEATURES_WITH_ENABLED)
    def test_invalid_idp(self):
        invalid_slug = 'jedi-academy'
        err_string = u'No SAML provider found for slug {}'.format(invalid_slug)
        with self.assertRaisesRegex(CommandError, err_string):
            call_command(self.command, invalid_slug)

    @override_settings(FEATURES=FEATURES_WITH_ENABLED)
    def test_confirmation_required(self):
        """ By default this command will require user input to confirm """
        with self._replace_stdin('confirm'):
            call_command(self.command, self.provider_hogwarts.slug)

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='harry')
        with self.assertRaises(UserSocialAuth.DoesNotExist):
            self.find_user_social_auth_entry('harry')

    @override_settings(FEATURES=FEATURES_WITH_ENABLED)
    def test_confirmation_failure(self):
        err_string = 'User confirmation required.  No records have been modified'
        with self.assertRaisesRegex(CommandError, err_string):
            with self._replace_stdin('no'):
                call_command(self.command, self.provider_hogwarts.slug)

        # no users should be removed
        self.assertEqual(len(User.objects.all()), 3)
        self.assertEqual(len(UserSocialAuth.objects.all()), 2)

    def test_feature_default_disabled(self):
        """ By default this command should not be enabled """
        err_string = 'ENABLE_ENROLLMENT_RESET feature not enabled on this enviroment'
        with self.assertRaisesRegex(CommandError, err_string):
            call_command(self.command, self.provider_hogwarts.slug, force=True)
