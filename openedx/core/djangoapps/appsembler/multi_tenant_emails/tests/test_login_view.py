"""
Tests for multi-tentant login view.
"""

from unittest import skipUnless

from django.conf import settings
from django.core.cache import cache
from django.test.client import Client
from django.test.utils import override_settings
from django.urls import reverse

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangolib.testing.utils import skip_unless_lms

from .test_utils import with_organization_context, create_org_user
from ...settings.helpers import get_tahoe_multitenant_auth_backends


@skip_unless_lms
@override_settings(AUTHENTICATION_BACKENDS=get_tahoe_multitenant_auth_backends(settings))
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This only tests multi-tenancy')
class MultiTenantLoginTest(CacheIsolationTestCase):
    """
    Test user_authn's login_user() view.

    This is similar to user_authn's LoginTest focuses on our multi-tenant tests including but not
    limited to `APPSEMBLER_MULTI_TENANT_EMAILS` i.e. these tests test
    the `organizations.backends.OrganizationMemberBackend` backend we rely on for Tahoe security.
    """

    ENABLED_CACHES = ['default']
    EMAIL = 'test@edx.org'
    PASSWORD = 'test_password'

    RED = 'red1'
    BLUE = 'blue2'

    def setUp(self):
        super(MultiTenantLoginTest, self).setUp()
        # Create the test client
        self.client = Client()
        cache.clear()
        # Store the login url
        self.url = reverse('login_api')

    def create_user(self, org, email=EMAIL, password=PASSWORD):
        """
        Create one user and save it to the database.
        """
        return create_org_user(org, first_name='noderabbit', email=email, password=password)

    def test_login_success(self):
        """
        Happy scenario for Tahoe sites regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(self.RED) as org:
            self.create_user(org)
            response = self.client.post(self.url, {'email': self.EMAIL, 'password': self.PASSWORD})
            assert response.json()['success'], response.content

    def test_login_site_separation(self):
        """
        Ensure site separation via our OrganizationMemberBackend regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(self.RED) as org:
            self.create_user(org)

        with with_organization_context(self.BLUE):
            response = self.client.post(self.url, {'email': self.EMAIL, 'password': self.PASSWORD})
            assert not response.json()['success'], response.content
            assert response.json()['value'], 'Email or password is incorrect'

    def test_login_reuse_email_two_sites(self):
        """
        Testing two emails with the `APPSEMBLER_MULTI_TENANT_EMAILS` enabled.
        """
        with with_organization_context(self.RED) as org:
            self.create_user(org)
            response = self.client.post(self.url, {'email': self.EMAIL, 'password': self.PASSWORD})
            assert response.json()['success'], response.content

        with with_organization_context(self.BLUE) as org:
            self.create_user(org)
            response = self.client.post(self.url, {'email': self.EMAIL, 'password': self.PASSWORD})
            assert response.json()['success'], response.content

    def test_login_fail_no_user_exists(self):
        """
        Sanity check for user not found regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(self.RED) as org:
            self.create_user(org)
            nonexistent_email = 'not_a_user@edx.org'
            response = self.client.post(self.url, {'email': nonexistent_email, 'password': self.PASSWORD})
            assert not response.json()['success'], response.content
            assert response.json()['value'], 'Email or password is incorrect'

    def test_login_fail_wrong_password(self):
        """
        Sanity check for incorrect password regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(self.RED) as org:
            self.create_user(org)
            response = self.client.post(self.url, {'email': self.EMAIL, 'password': 'wrong_password'})
            assert not response.json()['success'], response.content
            assert response.json()['value'], 'Email or password is incorrect'
