"""Test the Appsembler Analytics app helpers module
"""

from mock import patch, PropertyMock
from django.contrib.auth.models import User
from django.test import TestCase

from openedx.core.djangoapps.appsembler.analytics.helpers import should_show_hubspot
from openedx.core.djangoapps.appsembler.api.tests.factories import UserOrganizationMappingFactory


@patch.object(User, 'is_authenticated', PropertyMock(return_value=True))
class AnalyticsHelpersTests(TestCase):
    def setUp(self):
        super(AnalyticsHelpersTests, self).setUp()
        self.mapping = UserOrganizationMappingFactory.create(is_amc_admin=True, is_active=True)
        self.user = self.mapping.user
        self.org = self.mapping.organization

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
        self.mapping.is_amc_admin = False
        self.mapping.save()
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_active_amc_membership(self):
        self.mapping.is_active = False
        self.mapping.save()
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_active(self):
        self.user.is_active = False
        assert not should_show_hubspot(self.user)
