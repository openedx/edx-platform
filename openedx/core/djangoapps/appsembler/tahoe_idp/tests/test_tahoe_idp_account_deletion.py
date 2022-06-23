"""
Tests for the Account Deletion (Retirement) view.
"""

from mock import patch, Mock
import pytest
from social_django.models import UserSocialAuth

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from ...multi_tenant_emails.tests.test_utils import with_organization_context

from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (
    # Importing this module to allow using `usefixtures("setup_retirement_states")`
    setup_retirement_states,  # pylint: disable=unused-import
)


@patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': True})
@pytest.mark.usefixtures("setup_retirement_states")
@patch(
    'openedx.core.djangoapps.ace_common.templatetags.ace._get_google_analytics_tracking_url',
    Mock(return_value='http://url.com/')
)
class MultiTenantDeactivateLogoutViewTest(APITestCase):
    """
    Tests to ensure the DeactivateLogoutView deactivates the Tahoe IdP as well.
    """

    RED = 'red1'
    EMAIL = 'ali@example.com'
    PASSWORD = 'zzz'

    def setUp(self):
        super(MultiTenantDeactivateLogoutViewTest, self).setUp()
        self.registration_url = reverse('user_api_registration')
        self.deactivate_url = reverse('deactivate_logout')

    def register_user(self, color, username=None):
        """
        Register a user.
        """
        response = self.client.post(self.registration_url, {
            'email': self.EMAIL,
            'name': 'Ali',
            'username': username or 'ali_{}'.format(color),
            'password': self.PASSWORD,
            'honor_code': 'true',
        })
        return response

    def deactivate_user(self, color, username=None):
        """
        Post a deactivate_logout request (a.k.a GDPR forget me).
        """
        client = self.client_class()
        username = username or 'ali_{}'.format(color)
        assert client.login(username=username, password=self.PASSWORD)
        response = client.post(self.deactivate_url, {
            'password': self.PASSWORD,
        })
        return response

    @patch('openedx.core.djangoapps.user_api.accounts.views.tahoe_idp_api', create=True)
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': True})
    def test_disallow_email_reuse_after_deactivate(self, mock_tahoe_idp_api):
        """
        Test the account deletion with Tahoe IdP support.
        """
        social_auth_uid = 'e1ede4d8-f6f6-11ec-9eb7-f778f1c67e22'
        mock_tahoe_idp_api.get_tahoe_idp_id_by_user.return_value = social_auth_uid

        with with_organization_context(site_color=self.RED):
            register_res = self.register_user(self.RED)
            assert register_res.status_code == status.HTTP_200_OK, register_res.content.decode('utf-8')
            deactivate_res = self.deactivate_user(self.RED)
            assert deactivate_res.status_code == status.HTTP_204_NO_CONTENT, deactivate_res.content.decode('utf-8')

        mock_tahoe_idp_api.deactivate_user.assert_called_once_with(social_auth_uid)
