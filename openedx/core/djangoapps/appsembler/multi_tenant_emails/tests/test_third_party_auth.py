"""
Tests for third_party_auth app MTE related changes.
"""
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from unittest import skipUnless
from mock import patch
from openedx.core.djangolib.testing.utils import skip_unless_lms

from .test_utils import with_organization_context, create_org_user
from third_party_auth.utils import user_exists
from organizations.models import Organization


@skip_unless_lms
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This only tests multi-tenancy')
class TestMultiTenantEmailsUtils(TestCase):
    """
    Test the third_party_auth utils module.
    """
    RED = 'red1'
    BLUE = 'blue2'

    def create_users(self):
        """
        Create two users in two different organizations.
        """
        with with_organization_context(site_color=self.RED) as red_org:
            red_user = create_org_user(red_org, email='red_user@example.com', username='red_user')

        with with_organization_context(site_color=self.BLUE) as blue_org:
            blue_user = create_org_user(blue_org, email='blue_user@example.com', username='blue_user')

    def test_users_exists(self):
        """
        Test that recent created users are found by email, username and both combined.
        """
        self.create_users()
        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.RED).first()
        ):
            assert user_exists({'email': 'red_user@example.com'})
            assert user_exists({'username': 'red_user'})
            assert user_exists({'username': 'red_user', 'email': 'red_user@example.com'})

        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.BLUE).first()
        ):
            assert user_exists({'email': 'blue_user@example.com'})
            assert user_exists({'username': 'blue_user'})
            assert user_exists({'username': 'blue_user', 'email': 'blue_user@example.com'})

    def test_user_does_not_exists_by_email(self):
        """
        Test that the users does not exists in the other organization, where they
        don't belong by email. It also test with an email that doesn't exists in
        any org.
        """
        self.create_users()
        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.RED).first()
        ):
            assert not user_exists({'email': 'blue_user@example.com'})
            assert not user_exists({'email': 'another_user@example.com'})

        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.BLUE).first()
        ):
            assert not user_exists({'email': 'red_user@example.com'})
            assert not user_exists({'email': 'another_user@example.com'})

    def test_user_does_not_exists_by_username(self):
        """
        Test that the users does not exists in the other organization, where they
        don't belong by username. It also test with a username that doesn't
        exists in any org.
        """
        self.create_users()
        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.RED).first()
        ):
            assert not user_exists({'username': 'another_user'})

        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.BLUE).first()
        ):
            assert not user_exists({'username': 'another_user'})

    def test_user_does_not_exists_by_username_and_email(self):
        """
        Test that the users does not exists in the other organization, where they
        don't belong by username and email.
        """
        self.create_users()
        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.RED).first()
        ):
            assert not user_exists({'username': 'blue_user', 'email': 'blue_user@example.com'})

        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.BLUE).first()
        ):
            assert not user_exists({'username': 'red_user', 'email': 'red_user@example.com'})

    def test_username_exists_in_another_org(self):
        """
        Test with a username that exists but outside the organization.
        """
        self.create_users()
        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.RED).first()
        ):
            assert user_exists({'username': 'blue_user'})

        with patch(
            'third_party_auth.utils.get_current_organization',
            return_value=Organization.objects.filter(name=self.BLUE).first()
        ):
            assert user_exists({'username': 'red_user'})
