import factory

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteFactory,
)
from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain


class AlternativeDomainFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlternativeDomain
    site = factory.SubFactory(SiteFactory)
    domain = factory.Sequence(lambda n: 'domain{}'.format(n))
