"""
Provides factories for third_party_auth models.
"""
from factory import SubFactory
from factory.django import DjangoModelFactory

from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory


class SAMLConfigurationFactory(DjangoModelFactory):
    """
    Factory or SAMLConfiguration model in third_party_auth app.
    """
    class Meta(object):
        model = SAMLConfiguration

    site = SubFactory(SiteFactory)
    enabled = True


class SAMLProviderConfigFactory(DjangoModelFactory):
    """
    Factory or SAMLProviderConfig model in third_party_auth app.
    """
    class Meta(object):
        model = SAMLProviderConfig
        django_get_or_create = ('idp_slug', 'metadata_source', "entity_id")

    site = SubFactory(SiteFactory)

    enabled = True
    idp_slug = "test-shib"
    name = "TestShib College"

    entity_id = "https://idp.testshib.org/idp/shibboleth"
    metadata_source = "https://www.testshib.org/metadata/testshib-providers.xml"
