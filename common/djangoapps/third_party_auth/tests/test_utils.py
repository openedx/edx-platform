"""
Tests for third_party_auth utility functions.
"""


import unittest

from django.conf import settings

from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.tests.testutil import TestCase
from common.djangoapps.third_party_auth.utils import (
    get_user_from_email,
    is_enterprise_customer_user,
    user_exists,
    convert_saml_slug_provider_id,
)
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCustomerIdentityProviderFactory,
    EnterpriseCustomerUserFactory,
)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestUtils(TestCase):
    """
    Test the utility functions.
    """
    def test_user_exists(self):
        """
        Verify that user_exists function returns correct response.
        """
        # Create users from factory
        UserFactory(username='test_user', email='test_user@example.com')
        assert user_exists({'username': 'test_user', 'email': 'test_user@example.com'})
        assert user_exists({'username': 'test_user'})
        assert user_exists({'email': 'test_user@example.com'})
        assert not user_exists({'username': 'invalid_user'})
        assert user_exists({'username': 'TesT_User'})

    def test_convert_saml_slug_provider_id(self):
        """
        Verify saml provider id/slug map to each other correctly.
        """
        provider_names = {'saml-samltest': 'samltest', 'saml-example': 'example'}
        for provider_id in provider_names:
            # provider_id -> slug
            assert convert_saml_slug_provider_id(provider_id) == provider_names[provider_id]
            # slug -> provider_id
            assert convert_saml_slug_provider_id(provider_names[provider_id]) == provider_id

    def test_get_user(self):
        """
        Match the email and return user if exists.
        """
        # Create users from factory
        UserFactory(username='test_user', email='test_user@example.com')
        assert get_user_from_email({'email': 'test_user@example.com'})
        assert not get_user_from_email({'email': 'invalid@example.com'})

    def test_is_enterprise_customer_user(self):
        """
        Verify that if user is an enterprise learner.
        """
        # Create users from factory

        user = UserFactory(username='test_user', email='test_user@example.com')
        other_user = UserFactory(username='other_user', email='other_user@example.com')
        customer_idp = EnterpriseCustomerIdentityProviderFactory.create(
            provider_id='the-provider',
        )
        customer = customer_idp.enterprise_customer
        EnterpriseCustomerUserFactory.create(
            enterprise_customer=customer,
            user_id=user.id,
        )

        assert is_enterprise_customer_user('the-provider', user)
        assert not is_enterprise_customer_user('the-provider', other_user)
