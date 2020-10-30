"""
Test cases to cover Accounts change email related to APPSEMBLER_MULTI_TENANT_EMAILS.
"""

from unittest import skipUnless
import json

from rest_framework import status
from rest_framework.test import APITestCase

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import PendingEmailChange

from .test_utils import with_organization_context, create_org_user


@skip_unless_lms
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This tests multi-tenancy')
class TestAccountsAPI(APITestCase):
    """
    Unit tests for the Accounts views.

    This is similar to user_api.accounts..TestAccountsAPI but focuses on the
    limited to `APPSEMBLER_MULTI_TENANT_EMAILS` feature.
    """

    RED = 'red1'
    BLUE = 'blue2'

    AHMED_EMAIL = 'ahmedj@example.org'
    JOHN_EMAIL = 'johnb@example.org'
    PASSWORD = 'test_password'

    def send_patch_email(self, user, new_email):
        """
        Login and send PATCH request to change the email then logout.
        """
        self.client.login(username=user.username, password=self.PASSWORD)
        url = reverse('accounts_api', kwargs={'username': user.username})
        patch_body = json.dumps({'email': new_email, 'goals': 'change my email'})
        response = self.client.patch(url, patch_body, content_type='application/merge-patch+json')
        self.client.logout()
        return response

    def assert_change_email(self, user, new_email):
        """
        Assert a successful but PENDING email change.
        """
        original_email = user.email
        response = self.send_patch_email(user, new_email)
        allow_change_email = 'Email change should be allowed: {}'.format(response.content)
        assert response.status_code == status.HTTP_200_OK, allow_change_email

        pending_changes = PendingEmailChange.objects.filter(user=user)
        assert pending_changes.count() == 1, allow_change_email

        user.refresh_from_db()
        assert user.email == original_email, 'Should not change the email yet'

    def assert_confirm_change(self, user, new_email):
        # Now call the method that will be invoked with the user clicks the activation key in the received email.
        # First we must get the activation key that was sent.
        pending_change = PendingEmailChange.objects.get(user=user)
        activation_key = pending_change.activation_key
        confirm_change_url = reverse(
            'confirm_email_change', kwargs={'key': activation_key}
        )
        confirm_response = self.client.get(confirm_change_url)
        assert confirm_response.status_code == status.HTTP_200_OK, confirm_response.content
        user.refresh_from_db()
        assert user.email == new_email, 'Should change the email successfully'

    def test_change_email_success(self):
        """
        Email change request is allowed regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(site_color=self.RED) as org:
            red_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)
            new_email = 'another_email@example.com'
            self.assert_change_email(red_ahmed, new_email)
            self.assert_confirm_change(red_ahmed, new_email)

    def test_change_email_disallow_duplicate(self):
        """
        Ensure email reuse is not allowed within the organization regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(site_color=self.RED) as org:
            red_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)
            red_john = create_org_user(org, email=self.JOHN_EMAIL, password=self.PASSWORD)
            response = self.send_patch_email(red_ahmed, red_john.email)
            disallow_reuse_msg = 'Email reuse within the same organization should be disallowed'
            assert response.status_code == status.HTTP_400_BAD_REQUEST, disallow_reuse_msg
            pending_changes = PendingEmailChange.objects.filter(user=red_ahmed)
            assert not pending_changes.count(), disallow_reuse_msg

    def test_change_email_success_multi_tenant(self):
        """
        Email change allows emails in other organizations when APPSEMBLER_MULTI_TENANT_EMAILS is enabled.

        Story:
         - John registers for the Red Academy via his corporate email address.
         - John registers for the Blue University via his Gmail email address.
         - John decides to use his corporate email address on Blue University as well.
        """
        john_email = 'johnb@gmail.com'
        john_corp = 'johnb@corp.biz'

        with with_organization_context(site_color=self.RED) as org:
            # John registers for the Red Academy via his corporate email address.
            red_john = create_org_user(org, email=john_corp, password=self.PASSWORD)

        with with_organization_context(site_color=self.BLUE) as org:
            # John registers for the Blue University via his Gmail email address.
            blue_john = create_org_user(org, email=john_email, password=self.PASSWORD)
            # John decides to use his corporate email address on Blue University as well.
            self.assert_change_email(blue_john, red_john.email)  # Use corporate email in another organization
            self.assert_confirm_change(blue_john, red_john.email)  # Reuse Ahmed's email in another organization
