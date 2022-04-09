"""
Tests the email change when ENABLE_TAHOE_IDP is enabled.
"""

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import PendingEmailChange
from student.tests.factories import PendingEmailChangeFactory, UserFactory


@skip_unless_lms
class EmailChangeWithIdpTests(TestCase):
    """
    Test that confirmation of email change updates the email on idp as well.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.pending_change_request = PendingEmailChangeFactory.create(user=self.user)
        self.new_email = self.pending_change_request.new_email
        self.key = self.pending_change_request.activation_key

    @patch('student.views.management.tahoe_idp_api', create=True)
    def test_successful_email_change_without_idp(self, mock_tahoe_idp_api):
        """
        Test `confirm_email_change` with ENABLE_TAHOE_IDP = False.
        """
        with patch.dict(settings.FEATURES, {'ENABLE_TAHOE_IDP': False}):
            response = self.client.get(reverse('confirm_email_change', args=[self.key]))
        assert response.status_code == 200, 'Should succeed: {}'.format(response.content.decode('utf-8'))
        assert not mock_tahoe_idp_api.update_user_email.called, (
            'Should not use idp unless explicitly enabled via ENABLE_TAHOE_IDP'
        )

    @patch('student.views.management.tahoe_idp_api', create=True)
    def test_successful_email_change_with_idp(self, mock_tahoe_idp_api):
        """
        Test `confirm_email_change` with ENABLE_TAHOE_IDP = True.
        """
        with patch.dict(settings.FEATURES, {'ENABLE_TAHOE_IDP': True}):
            response = self.client.get(reverse('confirm_email_change', args=[self.key]))

        assert response.status_code == 200, 'Should succeed: {}'.format(response.content.decode('utf-8'))
        assert len(mail.outbox) == 2, 'Must have two items in outbox: one for old email, another for new email'

        assert mock_tahoe_idp_api.update_user_email.called, 'Should update idp email when ENABLE_TAHOE_IDP=True'
        mock_tahoe_idp_api.update_user_email.assert_called_once_with(
            self.user,
            self.new_email,
            set_email_as_verified=True,
        )

        assert not PendingEmailChange.objects.count(), 'Should delete the PendingEmailChange after using it'
