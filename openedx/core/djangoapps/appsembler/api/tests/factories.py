import factory

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from student.tests.factories import UserFactory

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteFactory,
)

import organizations


class SiteConfigurationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SiteConfiguration

    site = factory.SubFactory(SiteFactory)
    enabled = True
    values = {
        'PLATFORM_NAME': factory.SelfAttribute('site.name'),
        'SITE_NAME': factory.SelfAttribute('site.domain'),
    }
    sass_variables = {}
    page_elements = {}


class OrganizationFactory(factory.DjangoModelFactory):
    """
    We define the OrganizationFactory here instead of using the one in
    edx-organizations because that one is missing the `sites` relationship and
    we can't rely on getting `organizations.tests` to simply extend
    organizations/tests/factories.py:OrganizationFactory
    """
    class Meta(object):
        model = organizations.models.Organization

    name = factory.Sequence(u'organization name {}'.format)
    short_name = factory.Sequence(u'name{}'.format)
    description = factory.Sequence(u'description{}'.format)
    logo = None
    active = True

    @factory.post_generation
    def sites(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for site in extracted:
                self.sites.add(site)


class UserOrganizationMappingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = organizations.models.UserOrganizationMapping

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    is_active = True
    is_amc_admin = False
