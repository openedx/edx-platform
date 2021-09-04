"""
Test Appsembler Auth 'oauth' module.
"""
from mock import patch

from django.conf import settings
from django.test import TestCase

from oauth2_provider.models import (get_application_model,
                                    AccessToken,
                                    RefreshToken)

from student.tests.factories import UserFactory

from openedx.core.djangoapps.oauth_dispatch.api import destroy_oauth_tokens

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


Application = get_application_model()


class TestDestroyOAuthTokensHelper(TestCase):
    def setUp(self):
        super().setUp()
        self.admin = UserFactory.create()
        self.user = UserFactory.create()
        self.application = ApplicationFactory(
            user=self.admin,
            client_id=settings.AMC_APP_OAUTH2_CLIENT_ID,
        )

        access_token = AccessTokenFactory.create(
            user=self.user,
            application=self.application,
        )
        RefreshTokenFactory.create(
            user=self.user,
            application=self.application,
            access_token=access_token,
        )

    def assert_destroy_behaviour(self, should_be_kept, message):
        """
        Helper to test the `destroy_oauth_tokens` behaviour.
        """
        assert AccessToken.objects.count()  # Sanity check
        assert RefreshToken.objects.count()  # Sanity check
        destroy_oauth_tokens(self.user)
        assert should_be_kept == AccessToken.objects.count(), message
        assert should_be_kept == RefreshToken.objects.count(), message

    @patch.dict(settings.FEATURES, {'KEEP_AMC_TOKENS_ON_PASSWORD_RESET': False})
    def test_keep_tokens_feature_disabled(self):
        """
        Tokens that have a confidential TrustedClient should be removed if the
        feature is disabled
        """
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message=('Tokens of a AMC application should be deleted if the feature is disabled'),
        )

    @patch.dict(settings.FEATURES, {'KEEP_AMC_TOKENS_ON_PASSWORD_RESET': True})
    def test_keep_tokens_feature_enabled(self):
        """
        Tokens that have a confidential TrustedClient shouldn't be removed.
        """
        self.assert_destroy_behaviour(
            should_be_kept=True,
            message='Tokens of a AMC application should be kept',
        )

    @patch.dict(settings.FEATURES, {'KEEP_AMC_TOKENS_ON_PASSWORD_RESET': True})
    def test_no_amc_application_should_raise_exception(self):
        """
        This feature depends on AMC Application to be configured.
        """
        self.application.delete()
        with self.assertRaises(Application.DoesNotExist):  # The feature expects an AMC app to be configured.
            destroy_oauth_tokens(self.user)
