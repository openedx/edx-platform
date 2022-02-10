"""
Tests for the Apppsembler API views.
"""
import pytest

from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework import status

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory

from openedx.core.djangoapps.appsembler.sites import (
    site_config_client_helpers as client_helpers,
)

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
    site_configuration = SiteConfigurationFactory.build(site=site)
    site_configuration.save()

    url = reverse('tahoe_compile_sass')
    data = {'site_uuid': org.edx_uuid}
    response = client.post(url, data=data,
                           HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
    content = response.content.decode('utf-8')
    assert response.status_code == status.HTTP_200_OK, content
