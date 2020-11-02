"""
Tests for the Appsembler Analytics app.
"""

from django.test import TestCase
from openedx.core.djangoapps.appsembler.analytics.helpers import should_show_hubspot
from openedx.core.djangoapps.appsembler.api.tests.factories import UserOrganizationMappingFactory
from mock import patch
from django.contrib.auth.models import User


@patch.object(User, 'is_authenticated', return_value=True)
class AnalyticsHelpersTests(TestCase):
    def setUp(self):
        super(AnalyticsHelpersTests, self).setUp()
        self.mapping = UserOrganizationMappingFactory.create(is_amc_admin=True, is_active=True)
        self.user = self.mapping.user
        self.org = self.mapping.organization

    def test_happy_scenario(self, _is_authd):
        assert self.user.is_authenticated
        assert should_show_hubspot(self.user)

    def test_disable_for_non_auth(self, is_authd):
        is_authd.return_value = False
        assert not self.user.is_authenticated
        assert not should_show_hubspot(self.user)

    def test_disable_for_none(self, _is_authd):
        assert not should_show_hubspot(None)

    def test_disable_for_super_users(self, _is_authd):
        self.user.is_superuser = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_staff_users(self, _is_authd):
        self.user.is_staff = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_staff(self, _is_authd):
        self.user.is_staff = True
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_amc_admin(self, _is_authd):
        self.mapping.is_amc_admin = False
        self.mapping.save()
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_active_amc_membership(self, _is_authd):
        self.mapping.is_active = False
        self.mapping.save()
        assert not should_show_hubspot(self.user)

    def test_disable_for_non_active(self, _is_authd):
        self.user.is_active = False
        assert not should_show_hubspot(self.user)
