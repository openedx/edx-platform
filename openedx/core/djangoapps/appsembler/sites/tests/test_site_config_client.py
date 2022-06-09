"""
Tests for site_config_client_helpers and SiteConfigAdapter.
"""
from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import RequestFactory
from mock import Mock
from organizations.tests.factories import OrganizationFactory

from lms.djangoapps.courseware.access_utils import in_preview_mode
from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)

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
        adapter = client_helpers.get_configuration_adapter(site)
    assert adapter, 'Should return if client package is installed'
    assert adapter.site_uuid == org.edx_uuid, 'Should set the correct ID'
    assert adapter.status == 'draft', 'can be set to draft based on current request parameters'


@pytest.mark.django_db
def test_get_configuration_adapter(site_with_org):
    site, org = site_with_org

    adapter = client_helpers.get_configuration_adapter(site)
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
