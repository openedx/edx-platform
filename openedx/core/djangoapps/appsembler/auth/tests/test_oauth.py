"""Test Appsembler Auth 'oauth' module

"""
from mock import patch

from django.conf import settings
from django.test import TestCase

from oauth2_provider.models import (get_application_model,
                                    AccessToken,
                                    RefreshToken)

from student.tests.factories import UserFactory

from openedx.core.djangoapps.appsembler.auth.models import TrustedApplication
from openedx.core.djangoapps.appsembler.auth.oauth import destroy_oauth_tokens

# there is also the following ApplicationFactory:
# openeedx.core.djangoapps.api_admin.tests.factories.ApplicationFactory
#
# This ApplicationFactory automatically creates a user and performs more
# explicit field assignments
from openedx.core.djangoapps.oauth_dispatch.tests.factories import (
    ApplicationFactory,
    AccessTokenFactory,
    RefreshTokenFactory,
)

from .factories import TrustedApplicationFactory


Application = get_application_model()


class TestDestroyOAuthTokensHelper(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.application = ApplicationFactory(
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL)
        access_token = AccessTokenFactory.create(user=self.user,
                                                 application=self.application)
        RefreshTokenFactory.create(user=self.user,
                                   application=self.application,
                                   access_token=access_token)

    def assert_destroy_behaviour(self, should_be_kept, message):
        """
        Helper to test the `destroy_oauth_tokens` behaviour.
        """
        assert AccessToken.objects.count()  # Sanity check
        assert RefreshToken.objects.count()  # Sanity check
        destroy_oauth_tokens(self.user)
        assert should_be_kept == AccessToken.objects.count(), message
        assert should_be_kept == RefreshToken.objects.count(), message

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': False})
    def test_confidential_trusted_client_feature_disabled(self):
        """
        Tokens that have a confidential TrustedClient should be removed if the
        feature is disabled
        """
        TrustedApplicationFactory.create(application=self.application)
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message=('Tokens of a trusted confidential client should be '
                     'deleted if the feature is disabled'),
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_confidential_trusted_client(self):
        """
        Tokens that have a confidential TrustedClient shouldn't be removed.
        """
        TrustedApplicationFactory.create(application=self.application)
        self.assert_destroy_behaviour(
            should_be_kept=True,
            message='Tokens of a trusted confidential client should be kept',
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_no_trusted_application(self):
        """
        Only tokens that don't have a TrustedClient should be removed.
        """
        # Sanity check, there should not be a client
        assert not TrustedApplication.objects.count()
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message='Tokens of an untrusted client should be deleted',
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_public_trusted_client(self):
        """
        Tokens for public clients are removed, even if they're trusted.
        """
        self.application.client_type = Application.CLIENT_PUBLIC
        self.application.save()
        TrustedApplicationFactory.create(application=self.application)
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message='Tokens of a public trusted client should be deleted',
        )
