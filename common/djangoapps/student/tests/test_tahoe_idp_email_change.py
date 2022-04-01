"""
Tests the email change when ENABLE_TAHOE_AUTH0 is enabled.
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
class EmailChangeWithAuth0Tests(TestCase):
    """
    Test that confirmation of email change updates the email on auth0 as well.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.pending_change_request = PendingEmailChangeFactory.create(user=self.user)
        self.new_email = self.pending_change_request.new_email
        self.key = self.pending_change_request.activation_key

    @patch('student.views.management.tahoe_auth0_api', create=True)
    def test_successful_email_change_without_auth0(self, mock_tahoe_auth0_api):
        """
        Test `confirm_email_change` with ENABLE_TAHOE_AUTH0 = False.
        """
        with patch.dict(settings.FEATURES, {'ENABLE_TAHOE_AUTH0': False}):
            response = self.client.get(reverse('confirm_email_change', args=[self.key]))
        assert response.status_code == 200, 'Should succeed: {}'.format(response.content.decode('utf-8'))
        assert not mock_tahoe_auth0_api.update_user_email.called, (
            'Should not use auth0 unless explicitly enabled via ENABLE_TAHOE_AUTH0'
        )

    @patch('student.views.management.tahoe_auth0_api', create=True)
    def test_successful_email_change_with_auth0(self, mock_tahoe_auth0_api):
        """
        Test `confirm_email_change` with ENABLE_TAHOE_AUTH0 = True.
        """
        with patch.dict(settings.FEATURES, {'ENABLE_TAHOE_AUTH0': True}):
            response = self.client.get(reverse('confirm_email_change', args=[self.key]))

        assert response.status_code == 200, 'Should succeed: {}'.format(response.content.decode('utf-8'))
        assert len(mail.outbox) == 2, 'Must have two items in outbox: one for old email, another for new email'

        assert mock_tahoe_auth0_api.update_user_email.called, 'Should update auth0 email when ENABLE_TAHOE_AUTH0=True'
        mock_tahoe_auth0_api.update_user_email.assert_called_once_with(
            self.user,
            self.new_email,
            set_email_as_verified=True,
        )

        assert not PendingEmailChange.objects.count(), 'Should delete the PendingEmailChange after using it'
