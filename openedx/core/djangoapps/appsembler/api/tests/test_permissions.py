"""
Tests to ensure proper permission are set on the Appsembler API views

The tests in this module copied and extended from the permissions tests in
`lms.djangoapps.appsembler_api` locaed in the Appsembler's enterprise branches
of edx-platform
"""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from inspect import isclass

import ddt
import mock
from organizations.models import Organization

from tahoe_sites.tests.utils import create_organization_mapping
from student.tests.factories import UserFactory
from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory,
    SiteFactory,
)
from openedx.core.djangoapps.appsembler.api.v1 import views as api_views
from openedx.core.djangoapps.appsembler.api.permissions import IsSiteAdminUser


from .factories import OrganizationFactory


SITE_CONFIGURATION_CLASS = ('openedx.core.djangoapps.site_configuration'
                            '.models.SiteConfiguration')


def get_api_classes():
    """
    This method retrieves all classes from the views module. This means only
    view classes should be in the views module OR the API permissions tests
    need to be refactored
    """
    api_classes = []

    for member_name in dir(api_views):
        member = getattr(api_views, member_name)
        if isclass(member):
            # Exclude imported classes
            if member.__module__ == api_views.__name__:
                api_classes.append(member)

    return api_classes


@ddt.ddt
class AppsemblerAPIPermissionsTests(TestCase):
    """
    See the comments in the ``get_api_classes`` function above
    """
    def test_api_classes_are_being_found(self):
        self.assertTrue(get_api_classes())  # Ensure the API classes are filtered correctly

    @ddt.data(*get_api_classes())
    def test_auth_classes_are_tuples(self, api_class):
        """
        The commas that makes the tuple tend to be tricky! This ensures it's being set right.

        This will NOT ensure that the classes being set are secure or
        correct, we still rely on manual review for that matter.
        """
        self.assertIsInstance(api_class.authentication_classes, (tuple, list))
        self.assertIsInstance(api_class.permission_classes, (tuple, list))


@ddt.ddt
class SiteAdminPermissionsTest(TestCase):

    def setUp(self):
        patch = mock.patch(SITE_CONFIGURATION_CLASS + '.compile_microsite_sass')
        self.mock_site_config_method = patch.start()
        self.site = SiteFactory()
        self.organization = OrganizationFactory(linked_site=self.site)
        self.site_configuration = SiteConfigurationFactory(
            site=self.site,
            sass_variables={},
            page_elements={},
        )
        self.site_configuration.site_values['course_org_filter'] = self.organization.short_name
        self.callers = [
            UserFactory(username='alpha_nonadmin'),
            UserFactory(username='alpha_site_admin'),
            UserFactory(username='non_site_user'),
        ]
        # Make sure we DO NOT add the 'non_site_user' here
        create_organization_mapping(user=self.callers[0], organization=self.organization)
        create_organization_mapping(user=self.callers[1], organization=self.organization, is_admin=True)
        self.factory = RequestFactory()
        self.addCleanup(patch.stop)

    @ddt.data(('alpha_nonadmin', False),
              ('alpha_site_admin', True),

              ('non_site_user', False))
    @ddt.unpack
    def test_is_site_admin_user(self, username, has_permission):
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = self.site.domain
        request.user = get_user_model().objects.get(username=username)
        permission = IsSiteAdminUser().has_permission(request, None)
        self.assertEqual(permission, has_permission)

    @mock.patch('django.contrib.sites.shortcuts.get_current_site', mock.Mock())
    @ddt.data(Organization.DoesNotExist, Organization.MultipleObjectsReturned)
    def test_is_site_admin_user_with_handled_exceptions(self, side_effect):
        with mock.patch(
            'openedx.core.djangoapps.appsembler.api.permissions.get_organization_by_site',
            side_effect=side_effect
        ):
            self.assertEqual(IsSiteAdminUser().has_permission(mock.Mock(), None), False)
