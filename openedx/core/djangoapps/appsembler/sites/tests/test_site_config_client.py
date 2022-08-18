"""
Tests for site_config_client_helpers and SiteConfigAdapter.
"""
from unittest.mock import patch, Mock
from uuid import UUID
import pytest
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import RequestFactory
from django.utils import timezone
from mock import Mock

from organizations.tests.factories import OrganizationFactory
from site_config_client.exceptions import SiteConfigurationError

from lms.djangoapps.courseware.access_utils import in_preview_mode
from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)
from openedx.core.djangoapps.appsembler.sites.site_config_client_helpers import (
    get_active_site_uuids_from_site_config_service,
    get_current_configuration_adapter,
    get_current_site_config_tier_info,
)
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context

User = get_user_model()


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
    request = RequestFactory().get('/', data={'preview': 'true'})
    with patch('crum.get_current_request', return_value=request):
        adapter = client_helpers.init_site_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'
    assert adapter.status == 'draft', 'can be set to draft based on current request parameters'


@pytest.mark.django_db
def test_get_configuration_adapter(site_with_org):
    site, org = site_with_org

    adapter = client_helpers.init_site_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'
    assert adapter.status == 'live', 'by default should be live status'


def test_get_configuration_adapter_status_default():
    """Ensure status is `live` by default."""
    status = client_helpers.get_configuration_adapter_status(current_request=None)
    assert status == 'live'


def test_get_configuration_adapter_status_draft():
    """Ensure status can be set to `draft`."""
    request = RequestFactory().get('/', data={'preview': 'true'})
    request.user = User()
    status = client_helpers.get_configuration_adapter_status(request)
    assert status == 'draft'


def test_courseware_in_preview_mode(settings):
    """
    Support the Tahoe preview in `lms.djangoapps.courseware.access_utils.in_preview_mode`.
    """
    settings.FEATURES = {
        'PREVIEW_LMS_BASE': 'preview.example.com',
    }
    with patch(
        'lms.djangoapps.courseware.access_utils.get_current_request_hostname'
    ) as mock_get_hostname:
        mock_get_hostname.return_value = 'preview.example.com'
        assert in_preview_mode(), 'Sanity check: preview.example.com is the preview domain'

        mock_get_hostname.return_value = 'example.com'
        assert not in_preview_mode(), 'Sanity check: example.com is not the preview domain'

        request = RequestFactory().get('/', data={'preview': 'true'})
        request.user = User()

        with patch('crum.get_current_request', return_value=request):
            assert in_preview_mode(), (
                'New feature: example.com/?preview=true should be considered as a preview request'
            )


def test_get_active_site_uuids_from_site_config_service_without_client(settings):
    """
    Ensure `get_active_site_uuids_from_site_config_service` won't break if SITE_CONFIG_CLIENT isn't available.
    """
    del settings.SITE_CONFIG_CLIENT
    assert get_active_site_uuids_from_site_config_service() == []


def test_get_active_site_uuids_from_site_config_service(settings):
    """
    Ensure `get_active_site_uuids_from_site_config_service` returns UUIDs.
    """
    client = Mock()
    client.list_active_sites.return_value = {"results": [{
        "name": "site1",
        "uuid": "198d3826-e8ce-11ec-bf0b-1f28a583771a",
    }]}
    settings.SITE_CONFIG_CLIENT = client

    assert get_active_site_uuids_from_site_config_service() == [
        UUID("198d3826-e8ce-11ec-bf0b-1f28a583771a"),
    ]


def test_get_active_site_uuids_from_site_config_service_error(settings, caplog):
    """
    Ensure `get_active_site_uuids_from_site_config_service` handles errors gracefully.
    """
    client = Mock()
    client.list_active_sites.side_effect = SiteConfigurationError('my exception message')
    settings.SITE_CONFIG_CLIENT = client

    assert get_active_site_uuids_from_site_config_service() == [], 'Should return sane results'
    assert 'my exception message' in caplog.text
    assert 'An error occurred while fetching site config active sites' in caplog.text


def test_get_current_configuration_adapter_no_site_config():
    """
    Ensure it works while get_current_site_configuration returning `None`.
    """
    with patch('openedx.core.djangoapps.appsembler.sites.site_config_client_helpers') as helpers:
        helpers.get_current_site_configuration.return_value = None
        assert get_current_configuration_adapter() is None


@pytest.mark.django_db
def test_get_current_configuration_adapter_with_site_config():
    """
    Needs get_current_site_configuration to return an instance.
    """
    with with_site_configuration_context() as site:
        mock_api_adapter = Mock()
        site.configuration._api_adapter = mock_api_adapter
        site.configuration._api_adapter_initialization_attempted = True
        assert get_current_configuration_adapter() == mock_api_adapter, "Return current site\'s api adapter"


def test_get_current_site_config_tier_info_non_request():
    """
    Ensure `get_current_site_config_tier_info` works in non-request contexts.
    """
    assert not get_current_site_config_tier_info(), 'No tier info without a current site'


@pytest.mark.django_db
def test_get_current_site_config_tier_info():
    """
    Ensure `get_current_site_config_tier_info` works in the basic form.
    """
    mock_api_adapter = Mock()
    mock_api_adapter.get_site_info.return_value = {
        'always_active': True,
        'subscription_ends': timezone.now(),  # The date doesn't matter because `always_active=True`
        'tier': 'trial',
    }
    with with_site_configuration_context() as site:
        site.configuration._api_adapter = mock_api_adapter
        site.configuration._api_adapter_initialization_attempted = True
        tier_info = get_current_site_config_tier_info()

    assert not tier_info.has_subscription_ended(), 'Should return valid TierInfo object'
