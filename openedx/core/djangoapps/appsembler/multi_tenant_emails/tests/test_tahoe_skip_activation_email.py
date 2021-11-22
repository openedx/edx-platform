"""
Tests for Tahoe-specific skip activation email logic.
"""


from unittest.mock import patch
from django.test import TestCase


from openedx.core.djangoapps.user_authn.views.register import _skip_activation_email
from student.tests.factories import UserFactory


class TestSkipActivationEmail(TestCase):
    """
    Tests for _skip_activation_email.
    """

    @patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': True})
    def test_feature_enabled(self):
        """
        Test for Open edX vanilla behaviour regardless of Tahoe customization.
        """
        user = UserFactory.create()
        assert _skip_activation_email(user, {}, None, {}), 'Feature enabled: email should be skipped'

    @patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': False})
    def test_feature_disabled(self):
        """
        Test for Open edX vanilla behaviour regardless of Tahoe customization.
        """
        user = UserFactory.create()
        assert not _skip_activation_email(user, {}, None, {}), 'Feature disabled: email should be sent'

    @patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': False})
    def test_skip_for_amc_admin(self):
        """
        Email should not be sent for AMC customers when registered via APIs.
        """
        user = UserFactory.create()

        is_amc_admin_path = 'openedx.core.djangoapps.user_authn.views.register.is_request_for_amc_admin'
        with patch(is_amc_admin_path, return_value=True):
            assert _skip_activation_email(user, {}, None, {}), 'AMC admin: email should be skipped'
