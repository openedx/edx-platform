"""
Tests for Edly django models.
"""
from django.test import TestCase

from organizations.tests.factories import OrganizationFactory
from openedx.features.edly.models import EdlyMultiSiteAccess, EdlyOrganization, EdlySubOrganization
from openedx.features.edly.tests.factories import (
    EdlyMultiSiteAccessFactory,
    EdlyOrganizationFactory,
    EdlySubOrganizationFactory,
    SiteFactory,
)
from student.tests.factories import UserFactory
from student.roles import GlobalCourseCreatorRole


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
        edx_org = OrganizationFactory()
        edly_sub_organization = EdlySubOrganizationFactory(
            edx_organizations=[edx_org],
            slug='test-edly-sub-organization',
            lms_site=self.lms_site
        )
        edly_sub_organization_data = EdlySubOrganization.objects.filter(lms_site=edly_sub_organization.lms_site)
        assert edly_sub_organization_data.count() == 1

        user = UserFactory.create(edly_multisite_user__sub_org=edly_sub_organization)
        GlobalCourseCreatorRole(edx_org.short_name).add_users(user)

        edx_org_2 = OrganizationFactory()
        edly_sub_organization.edx_organizations.add(edx_org_2)
        edly_sub_organization.save()

        assert GlobalCourseCreatorRole(edx_org_2.short_name).has_user(user)

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


class EdlyMultiSiteAccessTests(TestCase):
    """
    Tests for "EdlyMultiSiteAccess" Model.
    """

    @classmethod
    def setUpClass(cls):
        super(EdlyMultiSiteAccessTests, cls).setUpClass()
        cls.user = UserFactory(password='test')

    def test_edly_user_profile_post_save_receiver(self):
        """
        Test "EdlyMultiSiteAccess" model object creation.
        """
        edly_sub_org = EdlySubOrganizationFactory()
        edly_user_profile = EdlyMultiSiteAccessFactory(user=self.user, sub_org=edly_sub_org)
        edly_user_profile_data = EdlyMultiSiteAccess.objects.filter(user=edly_user_profile.user, sub_org=edly_sub_org)
        assert edly_user_profile_data.count() == 1

    def test_multiple_sub_organizations(self):
        """
        Test "EdlyMultiSiteAccess" model multiple edly sub organizations.
        """

        edly_sub_organizations = [EdlySubOrganizationFactory() for __ in range(3)]
        for edly_sub_org in edly_sub_organizations:
            EdlyMultiSiteAccessFactory(user=self.user, sub_org=edly_sub_org)

        edly_user_profile_data = EdlyMultiSiteAccess.objects.filter(user=self.user, sub_org__in=edly_sub_organizations)

        assert edly_user_profile_data.count() == 3

    def test_edly_user_profile_on_user_creation(self):
        """
        Test "EdlyMultiSiteAccess" object creation on User object creation.
        """
        edly_sub_org = EdlySubOrganizationFactory()
        edly_user = UserFactory(password='test-pass', edly_multisite_user__sub_org=edly_sub_org)
        edly_user_profile = EdlyMultiSiteAccess.objects.filter(user=edly_user, sub_org=edly_sub_org)
        assert edly_user_profile.count() == 1
        assert edly_user_profile[0].user == edly_user

    def test_edly_user_profile_is_blocked_attr(self):
        """
        Test "EdlyMultiSiteAccess" attr "is_blocked" bool.
        """

        edly_user_profile = EdlyMultiSiteAccessFactory()
        assert not edly_user_profile.is_blocked

        edly_user_profile.is_blocked = True
        assert edly_user_profile.is_blocked
