"""Test the Appsembler Analytics app helpers module
"""

from mock import patch, PropertyMock
from django.contrib.auth.models import User
from django.test import TestCase
from tahoe_sites.api import update_admin_role_in_organization
from tahoe_sites.tests.utils import create_organization_mapping

from student.tests.factories import UserFactory
from openedx.core.djangoapps.appsembler.analytics.helpers import should_show_hubspot
from openedx.core.djangoapps.appsembler.api.tests.factories import OrganizationFactory


@patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
class AnalyticsHelpersTests(TestCase):
    def setUp(self):
        super(AnalyticsHelpersTests, self).setUp()
        self.user = UserFactory()
        self.org = OrganizationFactory()
        create_organization_mapping(user=self.user, organization=self.org, is_admin=True)

    def test_happy_scenario(self):
        assert self.user.is_authenticated
        assert should_show_hubspot(self.user)

    def test_disable_for_non_auth(self):
        with patch.object(User, 'is_authenticated', PropertyMock(return_value=False)):
            assert not self.user.is_authenticated
            assert not should_show_hubspot(self.user)

    def test_disable_for_none(self):
        assert not should_show_hubspot(None)

    def test_disable_for_super_users(self):
        self.user.is_superuser = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_staff_users(self):
        self.user.is_staff = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_staff(self):
        self.user.is_staff = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_amc_admin(self):
        update_admin_role_in_organization(user=self.user, organization=self.org, set_as_admin=False)
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_active(self):
        self.user.is_active = False
        assert not should_show_hubspot(self.user)
