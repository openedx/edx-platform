"""
Tests for the Apppsembler Platform 2.0 API views.
"""
import logging
import pytest
import uuid
from unittest.mock import patch, Mock

from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework import status

from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from organizations.tests.factories import OrganizationFactory


@pytest.fixture
def site_with_org(scope='function'):
    org = OrganizationFactory.create()
    assert org.edx_uuid, 'Should have valid uuid'
    site = Site.objects.create(domain='fake-site')
    site.organizations.add(org)
    return site, org


@pytest.mark.django_db
def test_compile_sass_view(client, monkeypatch, site_with_org):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    site, org = site_with_org
    site_configuration = SiteConfigurationFactory.build(
        site=site,
        site_values={'css_overrides_file': 'site.css'}
    )
    site_configuration.save()

    url = reverse('tahoe_compile_sass')
    data = {'site_uuid': org.edx_uuid}
    response = client.post(url, data=data,
                           HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
    content = response.content.decode('utf-8')
    assert response.status_code == status.HTTP_200_OK, content
    response_json = response.json()
    assert response_json.get('successful_sass_compile'), 'Should compile CSS successfully'
    assert 'sass_compile_message' in response_json


@pytest.mark.django_db
def test_compile_sass_view_site_not_found(client, monkeypatch):
    monkeypatch.setattr(client_helpers, 'CONFIG_CLIENT_INSTALLED', True)
    url = reverse('tahoe_compile_sass')
    data = {'site_uuid': 'ee9894a6-898e-11ec-ab4d-9779d2628f5b'}
    response = client.post(url, data=data, HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
    content = response.content.decode('utf-8')
    assert response.status_code == status.HTTP_404_NOT_FOUND, content
    response_json = response.json()
    assert not response_json.get('successful_sass_compile'), 'Should compile CSS successfully'
    assert response_json.get('sass_compile_message') == 'Requested site was not found'


@pytest.mark.django_db
@pytest.mark.parametrize('site_params', [
    {},
    {'site_uuid': 'ee9894a6-898e-11ec-ab4d-9779d2628f5b'},
])
def test_tahoe_site_create_view(client, site_params):
    """
    Tests for Platform 2.0 Site Creation view.
    """
    res = client.post(
        reverse('tahoe_site_creation_v2'),
        data={
            'domain': 'blue-site.localhost',
            'short_name': 'blue-site',
            **site_params,
        },
        HTTP_X_EDX_API_KEY=settings.EDX_API_KEY,
    )

    assert res.status_code == status.HTTP_201_CREATED, 'Should succeed: {res}'.format(
        res=res.content.decode('utf-8'),
    )
    site_data = res.json()

    assert 'successful_sass_compile' in site_data
    assert 'sass_compile_message' in site_data

    assert uuid.UUID(site_data['site_uuid']), 'Should return a correct uuid'

    if 'site_uuid' in site_params:
        assert site_data['site_uuid'] == site_params['site_uuid'], 'Should use the explicit UUID if provided.'


@pytest.mark.django_db
@patch('openedx.core.djangoapps.appsembler.sites.utils.compile_sass', Mock(return_value='I am working CSS'))
def test_compile_sass_file(caplog, site_with_org):
    """
    Test that _main-v2.scss file used when `THEME_VERSION` == tahoe-v2
    """
    site, org = site_with_org
    site_config = SiteConfigurationFactory.build(
        site=site,
        site_values={'css_overrides_file': 'site.css',
                     'THEME_VERSION': 'tahoe-v2'},
    )
    site_config.save()

    caplog.set_level(logging.INFO)
    assert site_config.get_value("THEME_VERSION") == 'tahoe-v2'
    sass_status = site_config.compile_microsite_sass()
    assert sass_status['successful_sass_compile']
    assert 'Sass compile finished successfully' in sass_status['sass_compile_message']
    assert '_main-v2.scss' in sass_status['scss_file_used'], 'Use `_main-v2.scss` due to THEME_VERSION`'
    assert 'main.scss' not in sass_status['scss_file_used']
