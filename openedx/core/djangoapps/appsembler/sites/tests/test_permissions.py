from django.test import TestCase
from organizations.models import UserOrganizationMapping, UserSiteMapping
from organizations.tests.factories import UserFactory, OrganizationFactory
from rest_framework.test import APIRequestFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

from ..permissions import AMCAdminPermission


class AMCAdminPermissionsTestCase(TestCase):
    """
    Verify permissions for AMC users.

    If the user is an admin user and either a part of an organization or a site, they should
    be able to have access.
    """

    def setUp(self):
        super(AMCAdminPermissionsTestCase, self).setUp()
        self.user = UserFactory.create()
        self.site = SiteFactory.create(
            domain='foo.dev',
            name='foo.dev'
        )
        factory = APIRequestFactory()
        self.request = factory.get('/test/')
        self.request.user = self.user
        self.organization = OrganizationFactory()

    def test_random_user(self):
        self.assertFalse(AMCAdminPermission().has_permission(self.request, None))

    def test_organization_nonadmin_user(self):
        UserOrganizationMapping.objects.create(user=self.user, organization=self.organization, is_amc_admin=False)
        self.assertFalse(AMCAdminPermission().has_permission(self.request, None))

    def test_organization_admin_user(self):
        UserOrganizationMapping.objects.create(user=self.user, organization=self.organization, is_amc_admin=True)
        self.assertTrue(AMCAdminPermission().has_permission(self.request, None))

    def test_site_nonadmin_user(self):
        UserSiteMapping.objects.create(user=self.user, site=self.site, is_amc_admin=False)
        self.assertFalse(AMCAdminPermission().has_permission(self.request, None))

    def test_site_admin_user(self):
        UserSiteMapping.objects.create(user=self.user, site=self.site, is_amc_admin=True)
        self.assertTrue(AMCAdminPermission().has_permission(self.request, None))
