from django.test import TestCase
from organizations.tests.factories import OrganizationFactory
from rest_framework.test import APIRequestFactory

from tahoe_sites.tests.utils import create_organization_mapping
from student.tests.factories import UserFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.appsembler.sites.permissions import AMCAdminPermission


class AMCAdminPermissionsTestCase(TestCase):
    """
    Verify permissions for AMC users.

    If the user is an admin user of an organization, they should be able to have access.
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
        create_organization_mapping(user=self.user, organization=self.organization, is_admin=False)
        self.assertFalse(AMCAdminPermission().has_permission(self.request, None))

    def test_organization_admin_user(self):
        create_organization_mapping(user=self.user, organization=self.organization, is_admin=True)
        self.assertTrue(AMCAdminPermission().has_permission(self.request, None))
