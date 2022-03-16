"""
Tests for site_config_client_helpers and SiteConfigAdapter.
"""

import pytest
from django.contrib.sites.models import Site
from mock import Mock
from organizations.tests.factories import OrganizationFactory

from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)


@pytest.fixture
def site_with_org():
    org = OrganizationFactory.create()
    assert org.edx_uuid, 'Should have valid uuid'
    site = Site.objects.create(domain='fake-site')
    site.organizations.add(org)
    return site, org


@pytest.mark.django_db
def test_is_enabled_for_site(monkeypatch, site_with_org):
    site, org = site_with_org

    helper = Mock()
    monkeypatch.setattr(client_helpers, 'is_feature_enabled_for_site', helper)

    is_enabled = client_helpers.is_enabled_for_site(site)
    assert is_enabled, 'Enabled if client is installed'
    helper.assert_called_with(org.edx_uuid)


@pytest.mark.django_db
def test_is_disabled_for_non_existent_organizations():
    """
    Ensures a sane result on incorrect or incomplete data.

    This is mostly useful for tests which adds no organization for a site.
    """
    site_without_organization = Site.objects.create(domain='fake-site')
    is_enabled = client_helpers.is_enabled_for_site(site_without_organization)
    assert not is_enabled, 'Should be disabled if a site has no organization'


@pytest.mark.django_db
def test_is_disabled_for_main_site(settings, site_with_org):
    site, org = site_with_org
    settings.SITE_ID = site.id
    is_enabled = client_helpers.is_enabled_for_site(site)
    assert not is_enabled, 'Should be disabled for main site like `tahoe.appsembler.com/admin`'


@pytest.mark.django_db
def test_get_configuration_adapter(site_with_org):
    site, org = site_with_org

    adapter = client_helpers.get_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'


@pytest.mark.django_db
def test_get_configuration_adapter(site_with_org):
    site, org = site_with_org

    adapter = client_helpers.get_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'
