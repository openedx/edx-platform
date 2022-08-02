"""
Tests for to ensure the REGISTER_USER signal is sent with User that is linked to an organization

This is needed for Open edX plugins that uses this signal.
"""

from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from tahoe_sites.api import get_organization_for_user

from openedx.core.djangolib.testing.utils import skip_unless_lms

from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER

from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import with_organization_context


@skip_unless_lms
class MultiTenantRegistrationViewTest(APITestCase):
    """
    Tests to ensure the registration end-point allow multi-tenant emails.
    """

    def setUp(self):
        super(MultiTenantRegistrationViewTest, self).setUp()
        self.url = reverse('user_api_registration')

    @patch.object(REGISTER_USER, 'send')
    def test_register_user_signal_order(self, signal_send):
        site_color = 'blue_academy'

        def assert_active_user_sent_with_signal(sender, user, registration):
            """
            Mock REGISTER_USER receiver to ensure user is linked to an organization

            In Juniper the function which adds the link is `create_account_with_params` in the
            `openedx.core.djangoapps.user_authn.views.register` package.
            """
            assert get_organization_for_user(user=user), 'REGISTER_USER sent for a user without an organization!'

        signal_send.side_effect = assert_active_user_sent_with_signal

        with with_organization_context(site_color=site_color):
            # Register a user user
            response = self.client.post(self.url, {
                'email': 'ali_register@example.com',
                'name': 'Ali',
                'username': 'ali_blue_academy',
                'password': 'zzz',
                'honor_code': 'true',
            })

        assert response.status_code == status.HTTP_200_OK, 'Should register learner ({}): {}'.format(
            site_color,
            response.content
        )

        assert signal_send.call_count == 1, 'The REGISTER_USER should be sent when creating a new user.'
