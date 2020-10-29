"""
Provides factories for third_party_auth models.
"""


from factory import SubFactory
from factory.django import DjangoModelFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from common.djangoapps.third_party_auth.models import SAMLConfiguration, SAMLProviderConfig


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
        django_get_or_create = ('slug', 'metadata_source', "entity_id")

    site = SubFactory(SiteFactory)

    enabled = True
    slug = "test-shib"
    name = "TestShib College"

    entity_id = "https://idp.testshib.org/idp/shibboleth"
    metadata_source = "https://www.testshib.org/metadata/testshib-providers.xml"
