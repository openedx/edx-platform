"""
Test the various password reset flows
"""
import re

from unittest import skipUnless, skipIf

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings
from openedx.core.djangolib.testing.utils import skip_unless_lms
from rest_framework.test import APITestCase

from .test_utils import with_organization_context, create_org_user


@skip_unless_lms
@skipIf(settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS, 'fix in Juniper')
@override_settings(DEFAULT_SITE_THEME='edx-theme-codebase')
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This only tests multi-tenancy')
class ResetPasswordMultiTenantTests(APITestCase):
    """
    Tests to ensure that password reset works with multi-tenant emails
    """

    RED = 'red1'
    BLUE = 'blue2'
    AHMED_EMAIL = 'ahmed@gmail.com'
    PASSWORD = 'test_password'
    BAD_EMAIL = 'doesnotexist@gmail.com'

    def test_password_reset_simple(self):
        """
        Ensures the basic functionality works within a site. Ahmed registers
        for the Red Academy via his personal email address and then resets
        the password.
        """
        with with_organization_context(site_color=self.RED) as org:
            red_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)
            response = self.client.post('/password_reset/', {'email': red_ahmed.email})
            assert response.status_code == 200, response.content
            assert response.json()['success'], response.content
            assert mail.outbox[0]

    def test_email_not_found(self):
        """
        Ensures if an email doesn't exists the email isn't sent.
        """
        with with_organization_context(site_color=self.BLUE) as org:
            response = self.client.post('/password_reset/', {'email': self.BAD_EMAIL})
            assert response.status_code == 200, response.content
            assert response.json()['success'], response.content
            assert len(mail.outbox) == 0

    def test_multi_tenant_password_reset(self):
        """
        Ensures two different user objects registered in two different sites
        with the same email address are not affected then one request password
        reset.
        """
        with with_organization_context(site_color=self.RED) as org:
            red_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)

        with with_organization_context(site_color=self.BLUE) as org:
            blue_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)

        with with_organization_context(site_color=self.RED) as org:
            response = self.client.post('/password_reset/', {'email': red_ahmed.email})
            assert response.status_code == 200, response.content
            assert response.json()['success']
            assert mail.outbox[0]
            assert len(mail.outbox) == 1
            sent_message = mail.outbox[0]
            assert "Password reset" in sent_message.subject
            assert len(sent_message.to) == 1
            assert sent_message.to[0] == self.AHMED_EMAIL
            reset_pwr_url = r'{}/password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/'.format(org.sites.first().domain)
            re.search(reset_pwr_url, sent_message.body).groupdict()

        with with_organization_context(site_color=self.BLUE) as org:
            response = self.client.post('/password_reset/', {'email': blue_ahmed.email})
            assert response.status_code == 200, response.content
            assert response.json()['success']
            assert mail.outbox[1]
            assert len(mail.outbox) == 2
            sent_message = mail.outbox[1]
            assert "Password reset" in sent_message.subject
            assert len(sent_message.to) == 1
            assert sent_message.to[0] == self.AHMED_EMAIL
            reset_pwr_url = r'{}/password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/'.format(org.sites.first().domain)
            re.search(reset_pwr_url, sent_message.body).groupdict()

    def test_user_in_another_site(self):
        """
        Ensures that if an user (based on email) doesn't exists in a site, a
        password reset email will not be generated and sent despite the fact a
        user with the same email exists in another site.
        """
        with with_organization_context(site_color=self.BLUE) as org:
            _blue_ahmed = create_org_user(org, email=self.AHMED_EMAIL, password=self.PASSWORD)

        with with_organization_context(site_color=self.RED):
            response = self.client.post('/password_reset/', {'email': self.AHMED_EMAIL})
            assert response.status_code == 200, response.content
            assert response.json()['success'], response.content
            assert len(mail.outbox) == 0
