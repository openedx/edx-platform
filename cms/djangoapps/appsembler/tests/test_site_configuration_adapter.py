"""
Test the initialization of SiteConfig API adapter in CMS in SiteConfiguration.
"""
from unittest.mock import patch

import pytest

from tahoe_sites.api import create_tahoe_site_by_link
from organizations.tests.factories import OrganizationFactory

from openedx.core.djangoapps.appsembler.sites.site_config_client_helpers import enable_for_site
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory


@pytest.mark.django_db
def test_api_adapter_not_enabled(settings):
    settings.DEFAULT_SITE_THEME = 'edx-theme-codebase'

    organization = OrganizationFactory.create()
    site = SiteFactory.create()

    config = SiteConfigurationFactory.create(site=site, sass_variables={}, page_elements={})
    assert config.api_adapter is None, 'Should _not_ have site api adapter because it is disabled.'


@pytest.mark.django_db
def test_api_adapter_enabled(settings):
    settings.DEFAULT_SITE_THEME = 'edx-theme-codebase'

    organization = OrganizationFactory.create()
    site = SiteFactory.create()
    create_tahoe_site_by_link(site=site, organization=organization)

    enable_for_site(site)

    with patch('site_config_client.openedx.adapter.SiteConfigAdapter.get_backend_configs') as mock_get:
        mock_get.return_value = {'configuration': {'setting': {}}}
        config = SiteConfigurationFactory.create(site=site, sass_variables={}, page_elements={})
        assert config.api_adapter, 'Should have site api adapter'
