"""
Tests for Edly django models.
"""
from django.test import TestCase

from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization, EdlyUserProfile
from openedx.features.edly.tests.factories import (
    EdlyOrganizationFactory,
    EdlySubOrganizationFactory,
    EdlyUserFactory,
    EdlyUserProfileFactory,
    SiteFactory,
)


class EdlyOrganizationTests(TestCase):
    """
    Tests for EdlyOrganization Model.
    """

    @classmethod
    def setUpClass(cls):
        super(EdlyOrganizationTests, cls).setUpClass()

    def test_edly_organization_post_save_receiver(self):
        """
        Test EdlyOrganization model object creation.
        """
        edly_organization = EdlyOrganizationFactory(
            name='Test Edly Organization Name',
            slug='test-edly-organization-name'
        )
        edly_organizations = EdlyOrganization.objects.filter(name=edly_organization.name)
        assert edly_organizations.count() == 1
        assert edly_organizations[0].name == edly_organization.name

    def test_slug_alphanumerice_validation(self):
        """
        Test EdlyOrganization slug alphanumeric validation.
        """
        edly_organization = EdlyOrganizationFactory(slug='test-invalid-slug+')
        expected_exception_message = 'Only small case alphanumeric and hyphen characters are allowed.'

        with self.assertRaises(Exception) as validation_exception:
            edly_organization.full_clean()

        assert expected_exception_message in str(validation_exception.exception)


class EdlySubOrganizationTests(TestCase):
    """
    Tests for EdlySubOrganization Model.
    """

    @classmethod
    def setUpClass(cls):
        super(EdlySubOrganizationTests, cls).setUpClass()
        cls.lms_site = SiteFactory()
        cls.studio_site = SiteFactory()

    def test_edly_sub_organization_post_save_receiver(self):
        """
        Test EdlySubOrganization model object creation.
        """
        edly_sub_organization = EdlySubOrganizationFactory(slug='test-edly-sub-organization', lms_site=self.lms_site)
        edly_sub_organization_data = EdlySubOrganization.objects.filter(lms_site=edly_sub_organization.lms_site)
        assert edly_sub_organization_data.count() == 1

    def test_edly_sub_organization_post_update_receiver(self):
        """
        Test EdlySubOrganization model object update.
        """
        edly_organization = EdlyOrganizationFactory(name='Test Edly Organization Name')
        edly_sub_organization = EdlySubOrganizationFactory(
            name='Test Edly Sub Organization Name',
            slug='test-edly-sub-organization-name',
            studio_site=self.studio_site,
            edly_organization=edly_organization
        )
        edly_sub_organization_data = EdlySubOrganization.objects.filter(studio_site=edly_sub_organization.studio_site)

        assert edly_sub_organization_data.count() == 1
        assert edly_sub_organization_data[0].edly_organization.name == edly_organization.name


class EdlyUserProfileTests(TestCase):
    """
    Tests for "EdlyUserProfile" Model.
    """

    @classmethod
    def setUpClass(cls):
        super(EdlyUserProfileTests, cls).setUpClass()
        cls.user = EdlyUserFactory(password='test')

    def test_edly_user_profile_post_save_receiver(self):
        """
        Test "EdlyUserProfile" model object creation.
        """

        edly_user_profile = EdlyUserProfileFactory(user=self.user)
        edly_user_profile_data = EdlyUserProfile.objects.filter(user=edly_user_profile.user)
        assert edly_user_profile_data.count() == 1

    def test_multiple_sub_organizations(self):
        """
        Test "EdlyUserProfile" model multiple edly sub organizations.
        """

        edly_sub_organizations = [EdlySubOrganizationFactory() for __ in range(3)]
        edly_user_profile = EdlyUserProfileFactory(user=self.user)
        edly_user_profile.edly_sub_organizations.add(*edly_sub_organizations)

        edly_user_profile_data = EdlyUserProfile.objects.filter(user=edly_user_profile.user)

        assert edly_user_profile_data.count() == 1
        assert list(edly_user_profile_data[0].edly_sub_organizations.all()) == edly_sub_organizations

    def test_edly_user_profile_on_user_creation(self):
        """
        Test "EdlyUserProfile" object creation on User object creation.
        """

        edly_user = EdlyUserFactory(password='test-pass')
        edly_user_profile = EdlyUserProfile.objects.filter(user=edly_user)
        assert edly_user_profile.count() == 1
        assert edly_user_profile[0].user == edly_user
