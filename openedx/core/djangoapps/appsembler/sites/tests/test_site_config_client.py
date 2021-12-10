"""
Tests for site_config_client_helpers and SiteConfigAdapter.
"""

import pytest
from mock import Mock
from organizations.models import Organization

from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)
from openedx.core.djangoapps.appsembler.sites import (
    utils as site_utils,
)


@pytest.mark.django_db
def test_is_enabled_for_current_organization_with_client(monkeypatch):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    fake_uuid = 'fake-uuid'
    org = Organization(edx_uuid=fake_uuid)
    monkeypatch.setattr(site_utils, 'get_current_organization', Mock(return_value=org))

    helper = Mock()
    monkeypatch.setattr(client_helpers, 'is_feature_enabled_for_site', helper)

    is_enabled = client_helpers.is_enabled_for_current_organization()
    assert is_enabled, 'Enabled if client is installed'
    helper.assert_called_with(fake_uuid)


def test_is_enabled_for_current_organization_without_client(monkeypatch):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', False)
    assert not client_helpers.is_enabled_for_current_organization(), 'Disable if no client is installed'


@pytest.mark.django_db
def test_get_current_configuration_adapter_with_client(monkeypatch):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    fake_uuid = 'fake-uuid'
    org = Organization(edx_uuid=fake_uuid)
    monkeypatch.setattr(site_utils, 'get_current_organization', Mock(return_value=org))

    adapter = client_helpers.get_current_configuration_adapter()
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == fake_uuid, 'Should set the correct ID'


def test_get_current_configuration_adapter_without_client(monkeypatch):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', False)
    assert not client_helpers.get_current_configuration_adapter(), 'Do not return if no client is installed'
