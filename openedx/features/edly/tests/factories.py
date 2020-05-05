"""
Model factories for unit testing views or models.
"""

from django.contrib.sites.models import Site
from factory import SelfAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory

from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization


class EdlyOrganizationFactory(DjangoModelFactory):
    """
    Factory class for EdlyOrganization model.
    """

    class Meta(object):
        model = EdlyOrganization
        django_get_or_create = ('name', 'slug')

    name = Sequence('Edly Organization {}'.format)
    slug = Sequence('edly-organization-{}'.format)


class SiteFactory(DjangoModelFactory):
    """
    Factory class for Site model.
    """

    class Meta(object):
        model = Site
        django_get_or_create = ('domain',)

    domain = Sequence('{}.testserver.fake'.format)
    name = SelfAttribute('domain')


class EdlySubOrganizationFactory(DjangoModelFactory):
    """
    Factory class for EdlySubOrganization model.
    """

    class Meta(object):
        model = EdlySubOrganization
        django_get_or_create = ('name', 'slug')

    name = Sequence('Edly SubOrganization {}'.format)
    slug = Sequence('edly-sub-organization-{}'.format)
    edly_organization = SubFactory(EdlyOrganizationFactory)
    edx_organization = SubFactory(OrganizationFactory)
    lms_site = SubFactory(SiteFactory)
    studio_site = SubFactory(SiteFactory)
