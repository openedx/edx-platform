"""
Tests for the Account Deletion (Retirement) view.
"""

from mock import patch, Mock
import pytest

from django.urls import reverse
from django.core import mail
from rest_framework.test import APITestCase
from rest_framework import status

from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.user_api.accounts.views import DeactivateLogoutView

from .test_utils import with_organization_context, lms_multi_tenant_test

from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (
    # Importing this module to allow using `usefixtures("setup_retirement_states")`
    setup_retirement_states,  # pylint: disable=unused-import
)


@lms_multi_tenant_test
@patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': True})
@pytest.mark.usefixtures("setup_retirement_states")
@patch(
    'openedx.core.djangoapps.ace_common.templatetags.ace._get_google_analytics_tracking_url',
    Mock(return_value='http://url.com/')
)
class MultiTenantDeactivateLogoutViewTest(APITestCase):
    """
    Tests to ensure the DeactivateLogoutView works well with multi-tenant emails.
    """

    RED = 'red1'
    BLUE = 'blue2'
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

    def assert_re_register_fails(self, color, email, username=None):
        """
        Assert that email re-use is disallowed.
        """
        username = username or 'ali2_{}'.format(color)
        res = self.register_user(self.RED, username=username)
        assert res.status_code == status.HTTP_409_CONFLICT, res.content

        error_response = {
            'email': [
                {
                    'user_message': ('It looks like {} belongs to an existing account. '
                                     'Try again with a different email address.').format(email)
                }
            ]
        }
        assert res.json() == error_response, '{}: {}'.format(
            'Should complain of retired email',
            res.content,
        )

    def test_disallow_email_reuse_after_deactivate(self):
        """
        Happy case scenario regardless of the `APPSEMBLER_MULTI_TENANT_EMAILS` feature.
        """
        with with_organization_context(site_color=self.RED):
            register_res = self.register_user(self.RED)
            assert register_res.status_code == status.HTTP_200_OK, register_res.content
            deactivate_res = self.deactivate_user(self.RED)
            assert deactivate_res.status_code == status.HTTP_204_NO_CONTENT, deactivate_res.content
            assert UserRetirementStatus.objects.exists()
            self.assert_re_register_fails(self.RED, self.EMAIL)

    def test_email_suffix_hacks(self):
        """
        Tests for the email suffix hack.

        Ensure the email suffix is done properly and the original organization and email
        are stored in the profile meta for retirement cancellation purposes.

        This fixes email collision issues when the APPSEMBLER_MULTI_TENANT_EMAILS feature
        is enabled.

        See the related decision document: https://appsembler.atlassian.net/l/c/QBcq0Mhu
        """
        username = 'some_learner'

        with with_organization_context(site_color=self.RED):
            register_res = self.register_user(self.RED, username=username)
            assert register_res.status_code == status.HTTP_200_OK, register_res.content
            self.deactivate_user(self.RED, username=username)
            retirement_status = UserRetirementStatus.objects.get(original_username=username)

        learner = retirement_status.user
        assert learner.email.endswith('retired.invalid')

        retired_email = 'ali@example.com..red1'  # See: generate_retired_email_address
        assert retirement_status.original_email == retired_email

        profile_meta = learner.profile.get_meta()
        assert profile_meta[DeactivateLogoutView.APPSEMBLER_RETIREMENT_EMAIL_META_KEY] == self.EMAIL

    def test_email_retirement_email_without_suffix(self):
        """
        Ensure that the DeletionNotificationMessage email is sent to the unsuffixed email.

        Fixes RED-1212
        """
        username = 'some_learner'

        with with_organization_context(site_color=self.RED):
            self.register_user(self.RED, username=username)
            assert not len(mail.outbox), 'No emails should be sent yet.'
            deactivate_res = self.deactivate_user(self.RED, username=username)

        assert deactivate_res.status_code == status.HTTP_204_NO_CONTENT, deactivate_res.content
        assert len(mail.outbox), 'Retirement email should be sent.'
        deletion_notification_message = mail.outbox[0]
        assert deletion_notification_message.to == [self.EMAIL], 'Un-suffixed email should be used'

    def test_allow_email_reuse_in_other_organization(self):
        """
        Ensure deactivated emails can be used in other organizations.

        This case tests DeactivateLogoutView with `APPSEMBLER_MULTI_TENANT_EMAILS`.
        """
        with with_organization_context(site_color=self.RED):
            red_register_res = self.register_user(self.RED)
            assert red_register_res.status_code == status.HTTP_200_OK, red_register_res.content
            red_deactivate_res = self.deactivate_user(self.RED)
            assert red_deactivate_res.status_code == status.HTTP_204_NO_CONTENT, red_deactivate_res.content
            assert UserRetirementStatus.objects.count() == 1

        with with_organization_context(site_color=self.BLUE):
            blue_register_res = self.register_user(self.BLUE)
            assert blue_register_res.status_code == status.HTTP_200_OK, blue_register_res.content
            blue_deactivate_res = self.deactivate_user(self.BLUE)
            assert blue_deactivate_res.status_code == status.HTTP_204_NO_CONTENT, blue_deactivate_res.content
            assert UserRetirementStatus.objects.count() == 2
