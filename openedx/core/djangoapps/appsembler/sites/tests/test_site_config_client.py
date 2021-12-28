"""
Tests for site_config_client_helpers and SiteConfigAdapter.
"""

import pytest
from django.contrib.sites.models import Site
from mock import Mock
from organizations.models import Organization
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
def test_is_enabled_for_site_with_client(monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    site, org = site_with_org

    helper = Mock()
    monkeypatch.setattr(client_helpers, 'is_feature_enabled_for_site', helper)

    is_enabled = client_helpers.is_enabled_for_site(site)
    assert is_enabled, 'Enabled if client is installed'
    helper.assert_called_with(org.edx_uuid)


@pytest.mark.django_db
def test_is_disabled_for_main_site_with_client(settings, monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    site, org = site_with_org
    settings.SITE_ID = site.id
    is_enabled = client_helpers.is_enabled_for_site(site)
    assert not is_enabled, 'Should be disabled for main site like `tahoe.appsembler.com/admin`'


@pytest.mark.django_db
def test_get_single_org_for_site_multiple_orgs(settings, monkeypatch, site_with_org):
    site, org = site_with_org
    site.organizations.add(OrganizationFactory.create())

    with pytest.raises(Organization.MultipleObjectsReturned):
        client_helpers.get_single_org_for_site(site)


@pytest.mark.django_db
def test_is_enabled_for_site_without_client(monkeypatch, site_with_org):
    site, _ = site_with_org
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', False)
    assert not client_helpers.is_enabled_for_site(site), 'Disable if no client is installed'


@pytest.mark.django_db
def test_get_configuration_adapter_with_client(monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    site, org = site_with_org

    adapter = client_helpers.get_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'


@pytest.mark.django_db
def test_get_configuration_adapter_with_client(monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    site, org = site_with_org

    adapter = client_helpers.get_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'


@pytest.mark.django_db
def test_get_configuration_adapter_without_client(monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', False)
    site, _ = site_with_org
    assert not client_helpers.get_configuration_adapter(site), 'Do not return if no client is installed'
