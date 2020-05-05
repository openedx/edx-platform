"""
Tests for Edly django models.
"""
from django.test import TestCase

from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization
from openedx.features.edly.tests.factories import EdlyOrganizationFactory, EdlySubOrganizationFactory, SiteFactory


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
        assert len(edly_organizations) == 1
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
        assert len(edly_sub_organization_data) == 1

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

        assert len(edly_sub_organization_data) == 1
        assert edly_sub_organization_data[0].edly_organization.name == edly_organization.name
